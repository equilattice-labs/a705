<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import {
  ArrowRight,
  ArrowDown,
  LayoutDashboard,
  BookOpen,
  Route,
  FlaskConical,
  ArrowUpRight,
  Check,
  FileText,
  Menu,
  SlidersHorizontal,
  Wallet,
  X,
} from "lucide-vue-next";
import MarketCockpit from "./components/MarketCockpit.vue";
import WalletModal from "./components/WalletModal.vue";
import { brand, migrateBrandStorage, storageKeys } from "./brand";

const walletOpen = ref(false);
const menuOpen = ref(false);
const connectedAccount = ref("");
const email = ref("");
const subscribed = ref(false);
const emailError = ref("");
const emailNotice = ref("");
const workbench = ref(null);
const menuButton = ref(null);
const activeLayer = ref(0);
const shortAccount = computed(() =>
  connectedAccount.value
    ? `${connectedAccount.value.slice(0, 6)}…${connectedAccount.value.slice(-4)}`
    : "",
);
const layers = [
  {
    label: "Understand",
    icon: FileText,
    title: "Build a view from both sides.",
    tag: "01 / RESEARCH",
    headline: "A convincing thesis needs a convincing counter-case.",
    detail:
      "Read the working thesis, then challenge it. Source context makes it clear which inputs are samples and where independent evidence is still needed.",
    action: "Inspect source context",
    target: "Sources",
    note: "OBSERVATION BEFORE INTERPRETATION",
  },
  {
    label: "Test",
    icon: SlidersHorizontal,
    title: "Give the downside a number.",
    tag: "02 / SCENARIO",
    headline: "Change the assumptions. See what changes.",
    detail:
      "Explore bear, base, and bull cases. Adjust your position weight and see the portfolio stress impact before recording a decision.",
    action: "Open scenario lab",
    target: "Scenario",
    note: "ASSUMPTIONS, NEVER PREDICTIONS",
  },
  {
    label: "Remember",
    icon: BookOpen,
    title: "Leave a trail for your future self.",
    tag: "03 / DECISION",
    headline: "Your reasoning deserves more than a memory.",
    detail:
      "Save the asset, thesis, scenario, and your own note together. Revisit a saved decision to explore new assumptions without rewriting the original.",
    action: "Open decision journal",
    target: "Journal",
    note: "RECORD. REVISIT. REFINE.",
  },
];
const layer = computed(() => layers[activeLayer.value]);
const navItems = [
  { id: "top", label: "Overview", icon: LayoutDashboard },
  { id: "cockpit", label: "Research", icon: FlaskConical },
  { id: "method", label: "Process", icon: Route },
  { id: "journal", label: "Journal", icon: BookOpen },
  { id: "roadmap", label: "Next", icon: ArrowUpRight },
];
const activeSection = ref("top");
let sectionObserver;
onMounted(() => {
  sectionObserver = new IntersectionObserver(
    (entries) => {
      const visible = entries.filter((entry) => entry.isIntersecting);
      if (visible.length) activeSection.value = visible[0].target.id;
    },
    { rootMargin: "-90px 0px -60% 0px" },
  );
  for (const item of navItems) {
    const el = document.getElementById(item.id);
    if (el) sectionObserver.observe(el);
  }
});
onBeforeUnmount(() => sectionObserver?.disconnect());
async function openResearch(tab = "Brief") {
  closeMenu();
  window.location.hash = "cockpit";
  await nextTick();
  await workbench.value?.goToTab(tab);
}
function launchLayer() {
  if (layer.value.target === "Journal") return openJournal();
  return openResearch(layer.value.target);
}
let provider;
let sessionRevision = 0;
function invalidateSession() {
  sessionRevision += 1;
  connectedAccount.value = "";
  try {
    sessionStorage.removeItem(storageKeys.session);
  } catch {
    /* In-memory session cleared. */
  }
}
function onAccountsChanged(accounts) {
  if (
    !accounts?.[0] ||
    accounts[0].toLowerCase() !== connectedAccount.value.toLowerCase()
  )
    invalidateSession();
}
function onChainChanged(chain) {
  if (Number(chain) !== 4663) invalidateSession();
}
function attachProvider(nextProvider) {
  if (provider === nextProvider) return;
  provider?.removeListener?.("accountsChanged", onAccountsChanged);
  provider?.removeListener?.("chainChanged", onChainChanged);
  provider?.removeListener?.("disconnect", invalidateSession);
  provider = nextProvider;
  provider?.on?.("accountsChanged", onAccountsChanged);
  provider?.on?.("chainChanged", onChainChanged);
  provider?.on?.("disconnect", invalidateSession);
}
onMounted(async () => {
  migrateBrandStorage();
  try {
    const saved = localStorage.getItem(storageKeys.email);
    if (saved && /^\S+@\S+\.\S+$/.test(saved)) {
      email.value = saved;
      subscribed.value = true;
    }
  } catch {
    /* Saving reports storage errors explicitly. */
  }
  attachProvider(window.ethereum);
  const revision = sessionRevision;
  try {
    const session = JSON.parse(
      sessionStorage.getItem(storageKeys.session) || "null",
    );
    if (session?.account && provider) {
      const [accounts, chain] = await Promise.all([
        provider.request({ method: "eth_accounts" }),
        provider.request({ method: "eth_chainId" }),
      ]);
      if (revision !== sessionRevision) return;
      if (
        Number(chain) === 4663 &&
        accounts?.[0]?.toLowerCase() === session.account.toLowerCase()
      )
        connectedAccount.value = session.account;
      else invalidateSession();
    } else if (session) invalidateSession();
  } catch {
    if (revision === sessionRevision) invalidateSession();
  }
});
onBeforeUnmount(() => {
  provider?.removeListener?.("accountsChanged", onAccountsChanged);
  provider?.removeListener?.("chainChanged", onChainChanged);
  provider?.removeListener?.("disconnect", invalidateSession);
});
function handleConnected(account) {
  attachProvider(window.ethereum);
  sessionRevision += 1;
  connectedAccount.value = account;
  walletOpen.value = false;
}
function closeMenu() {
  menuOpen.value = false;
}
function escapeMenu() {
  if (menuOpen.value) {
    closeMenu();
    menuButton.value?.focus();
  }
}
async function openJournal() {
  await workbench.value?.openJournal();
}
function subscribe() {
  emailError.value = "";
  emailNotice.value = "";
  const value = email.value.trim();
  if (!/^\S+@\S+\.\S+$/.test(value)) {
    emailError.value = "Enter a valid email address to save your interest.";
    return;
  }
  try {
    localStorage.setItem(storageKeys.email, value);
    email.value = value;
    subscribed.value = true;
    emailNotice.value =
      "Interest saved on this device. You have not joined a mailing list.";
  } catch {
    emailError.value =
      "Your browser could not save this. Allow site storage and try again.";
  }
}
function forgetEmail() {
  try {
    localStorage.removeItem(storageKeys.email);
    email.value = "";
    subscribed.value = false;
    emailError.value = "";
    emailNotice.value = "Your saved email has been removed from this device.";
  } catch {
    emailError.value =
      "Your browser could not remove the saved email. Check site storage settings.";
  }
}
</script>

<template>
  <div
    class="site-shell"
    :inert="walletOpen || undefined"
    @keydown.esc="escapeMenu"
  >
    <a class="skip-link" href="#cockpit">Skip to research workspace</a>
    <aside class="navigation-rail" aria-label="Quick navigation">
      <a class="rail-brand" href="#top" :aria-label="`${brand.name} home`"
        ><img src="/folivect-mark.svg" alt="" width="40" height="40"
      /></a>
      <nav aria-label="Section navigation">
        <a
          v-for="item in navItems"
          :key="item.id"
          :href="`#${item.id}`"
          :aria-current="activeSection === item.id ? 'location' : undefined"
          :class="{ active: activeSection === item.id }"
          ><component :is="item.icon" :size="21" stroke-width="1.6" /><span>{{
            item.label
          }}</span></a
        >
      </nav>
      <div class="rail-bottom">
        <span class="status-dot"></span><span>LOCAL<br />PREVIEW</span>
      </div>
    </aside>
    <div class="page-shell">
      <header class="site-header">
        <a
          href="#top"
          class="brand-lockup"
          :aria-label="`${brand.name} home`"
          @click="closeMenu"
          ><img
            src="/folivect-mark.svg"
            width="32"
            height="32"
            alt=""
          /><span>{{ brand.name }}</span
          ><span class="brand-divider"></span><small>THE RESEARCH LAB</small></a
        >
        <div class="header-actions">
          <button class="header-journal" @click="openJournal">
            <BookOpen :size="16" /><span>My journal</span></button
          ><button
            v-if="connectedAccount"
            class="button wallet-button"
            @click="invalidateSession"
            :aria-label="`End local session for ${shortAccount}`"
          >
            <Check :size="16" /><span>{{ shortAccount }}</span
            ><span class="session-end">End session</span></button
          ><button
            v-else
            class="button wallet-button"
            @click="walletOpen = true"
          >
            <Wallet :size="16" /><span>Connect wallet</span></button
          ><button
            ref="menuButton"
            class="mobile-menu"
            :aria-label="menuOpen ? 'Close navigation' : 'Open navigation'"
            :aria-expanded="menuOpen"
            aria-controls="mobile-navigation"
            @click="menuOpen = !menuOpen"
          >
            <X v-if="menuOpen" :size="22" /><Menu v-else :size="22" />
          </button>
        </div>
        <nav
          v-if="menuOpen"
          id="mobile-navigation"
          class="mobile-navigation"
          aria-label="Main navigation"
        >
          <a
            v-for="item in navItems"
            :key="item.id"
            :href="`#${item.id}`"
            @click="closeMenu"
            ><component :is="item.icon" :size="18" />{{ item.label
            }}<ArrowUpRight :size="16"
          /></a>
        </nav>
      </header>
      <main>
        <section
          id="top"
          class="hero-section page-container"
          aria-labelledby="hero-title"
        >
          <div class="hero-topline">
            <p class="eyebrow">
              <span class="status-dot"></span> INDEPENDENT THINKING. ONCHAIN
              EQUITIES.
            </p>
            <span class="edition-tag">RESEARCH PREVIEW / 01</span>
          </div>
          <div class="hero-grid">
            <div class="hero-copy">
              <h1 id="hero-title">
                See the case.<br /><span>Own the decision.</span>
              </h1>
              <p class="hero-lede">
                The market has enough opinions.<br />Build your own perspective
                with evidence, risk scenarios, and a record of your reasoning.
              </p>
              <div class="hero-actions">
                <a href="#cockpit" class="button primary"
                  >Start researching <ArrowUpRight :size="19" /></a
                ><span
                  >No wallet required.<br />A clearer process starts here.</span
                >
              </div>
            </div>
            <div class="decision-map">
              <div class="map-heading">
                <span>FROM QUESTION TO CONVICTION</span
                ><span class="map-index">01 / 03</span>
              </div>
              <div class="map-graphic" aria-hidden="true">
                <svg viewBox="0 0 440 175">
                  <defs>
                    <pattern
                      id="map-grid"
                      width="22"
                      height="22"
                      patternUnits="userSpaceOnUse"
                    >
                      <circle cx="1" cy="1" r="1" fill="#3d4841" />
                    </pattern>
                  </defs>
                  <rect width="440" height="175" fill="url(#map-grid)" />
                  <path
                    d="M30 88H113L185 28H290M113 88L185 146H290M113 88H294"
                    stroke="#5a685a"
                    stroke-width="1.5"
                    fill="none"
                  />
                  <path
                    d="M30 88H113L185 146H290L370 88H419"
                    stroke="#cef576"
                    stroke-width="2"
                    fill="none"
                  />
                  <g fill="#101315" stroke="#889488">
                    <circle cx="30" cy="88" r="9" />
                    <circle cx="113" cy="88" r="6" />
                    <rect x="281" y="19" width="18" height="18" rx="3" />
                    <rect x="285" y="79" width="18" height="18" rx="3" />
                  </g>
                  <rect
                    x="281"
                    y="137"
                    width="18"
                    height="18"
                    rx="3"
                    fill="#cef576"
                  />
                  <circle cx="409" cy="88" r="16" fill="#cef576" />
                  <path
                    d="m402 88 5 5 9-11"
                    stroke="#101315"
                    stroke-width="2"
                    fill="none"
                  /></svg
                ><span class="map-question">THE QUESTION</span
                ><span class="map-choice">YOUR CHOICE</span>
              </div>
              <div class="map-step">
                <span>01</span><strong>Examine the evidence</strong
                ><FileText :size="18" />
              </div>
              <div class="map-step">
                <span>02</span><strong>Explore the possible</strong
                ><SlidersHorizontal :size="18" />
              </div>
              <div class="map-step">
                <span>03</span><strong>Keep the reasoning</strong
                ><BookOpen :size="18" />
              </div>
              <p class="map-note">
                A process you can inspect. A decision that stays yours.
              </p>
            </div>
          </div>
          <div class="hero-bottom">
            <div>
              <strong>04</strong
              ><span>Sample assets<br />One place to investigate</span>
            </div>
            <div>
              <strong>03</strong
              ><span>Scenario paths<br />Assumptions you control</span>
            </div>
            <div>
              <strong>01</strong
              ><span>Personal journal<br />Keep the why close</span>
            </div>
            <a href="#cockpit" aria-label="Go to research workspace"
              ><ArrowDown :size="22"
            /></a>
          </div>
        </section>
        <section
          id="cockpit"
          class="workspace-section page-container"
          aria-labelledby="workspace-title"
        >
          <div class="section-intro">
            <div>
              <p class="eyebrow">01 / EXPLORE THE RESEARCH LAB</p>
              <h2 id="workspace-title">
                Build a view. <span>Pressure-test it.</span>
              </h2>
            </div>
            <span class="sample-badge"
              ><span class="status-dot"></span> Sample data. Real
              interactions.</span
            >
          </div>
          <MarketCockpit ref="workbench" />
          <div class="workspace-caption">
            <span>All prices and research are illustrative.</span
            ><span>Research is not investment advice.</span>
          </div>
        </section>
        <section
          id="method"
          class="method-section page-container"
          aria-labelledby="method-title"
        >
          <div class="section-intro">
            <div>
              <p class="eyebrow">02 / THE WAY YOU WORK</p>
              <h2 id="method-title">
                A good question<br /><span>changes the whole picture.</span>
              </h2>
            </div>
            <p>
              Your process should help you think. Every step has somewhere to
              go.
            </p>
          </div>
          <div class="method-layout">
            <div
              class="method-tabs"
              role="group"
              :aria-label="`Explore the ${brand.name} process`"
            >
              <button
                v-for="(item, index) in layers"
                :key="item.label"
                :aria-pressed="activeLayer === index"
                @click="activeLayer = index"
              >
                <span class="layer-number">0{{ index + 1 }}</span
                ><component :is="item.icon" :size="21" /><span>{{
                  item.label
                }}</span
                ><ArrowUpRight :size="18" />
              </button>
            </div>
            <article class="method-detail" aria-live="polite">
              <div class="method-kicker">
                <span>{{ layer.tag }}</span
                ><span>{{ layer.note }}</span>
              </div>
              <h3>{{ layer.headline }}</h3>
              <p>{{ layer.detail }}</p>
              <button class="text-link" @click="launchLayer">
                {{ layer.action }} <ArrowRight :size="18" />
              </button>
            </article>
          </div>
        </section>
        <section
          id="journal"
          class="journal-section page-container"
          aria-labelledby="journal-title"
        >
          <div class="journal-copy">
            <p class="eyebrow">03 / DECISIONS WITH A MEMORY</p>
            <h2 id="journal-title">
              Your future self<br />has a few questions.
            </h2>
            <p>
              What did you see? What could go wrong? What would change your
              mind? Save the context, then return with a fresh perspective.
            </p>
            <button class="button primary" @click="openJournal">
              Open your decision journal <ArrowUpRight :size="18" /></button
            ><small
              >Local to this browser. Yours to export, revisit, or
              delete.</small
            >
          </div>
          <div class="note-stack">
            <div class="note-back" aria-hidden="true"></div>
            <article class="example-note">
              <div class="note-heading">
                <span><BookOpen :size="16" /> RESEARCH RECORD</span
                ><span>EXAMPLE / 001</span>
              </div>
              <div class="note-asset">
                <strong>AAPL</strong><span>Apple Inc.</span
                ><span class="note-label">WORKING THESIS</span>
              </div>
              <h3>Strong services.<br />A demanding valuation.</h3>
              <div class="note-row">
                <span>THE CASE</span>
                <p>Services resilience supports the thesis.</p>
              </div>
              <div class="note-row">
                <span>THE QUESTION</span>
                <p>How much growth is already priced in?</p>
              </div>
              <div class="note-footer">
                <span class="status-dot"></span> A record of thinking. Not a
                forecast.
              </div>
            </article>
          </div>
        </section>
        <section
          id="roadmap"
          class="roadmap-section page-container"
          aria-labelledby="roadmap-title"
        >
          <div class="section-intro">
            <div>
              <p class="eyebrow">04 / WHAT WE ARE BUILDING</p>
              <h2 id="roadmap-title">A considered path forward.</h2>
            </div>
            <p>Useful research first. Every next step has a release gate.</p>
          </div>
          <div class="roadmap-grid">
            <article class="roadmap-card current">
              <div>
                <span>01</span><span class="roadmap-status">AVAILABLE NOW</span>
              </div>
              <FlaskConical :size="29" stroke-width="1.4" />
              <h3>The research lab</h3>
              <p>
                Sample briefs, adjustable scenarios, and a local decision
                journal.
              </p>
              <a href="#cockpit"
                >Explore the preview <ArrowUpRight :size="16"
              /></a>
            </article>
            <article class="roadmap-card">
              <div>
                <span>02</span><span class="roadmap-status">IN PLANNING</span>
              </div>
              <Route :size="29" stroke-width="1.4" />
              <h3>Connected context</h3>
              <p>
                Verified data sources and wallet context, after privacy review.
              </p>
              <span class="roadmap-note">DATA &amp; PRIVACY GATE</span>
            </article>
            <article class="roadmap-card">
              <div>
                <span>03</span
                ><span class="roadmap-status">RESEARCH STAGE</span>
              </div>
              <FileText :size="29" stroke-width="1.4" />
              <h3>Verifiable intent</h3>
              <p>
                Testnet intent and proof records, subject to security review.
              </p>
              <span class="roadmap-note">SECURITY GATE</span>
            </article>
            <article class="roadmap-card">
              <div>
                <span>04</span><span class="roadmap-status">GATED</span>
              </div>
              <ArrowUpRight :size="29" stroke-width="1.4" />
              <h3>Scoped execution</h3>
              <p>Limited mainnet routing, gated by audit and legal approval.</p>
              <span class="roadmap-note">AUDIT &amp; LEGAL GATE</span>
            </article>
          </div>
        </section>
        <section
          id="beta"
          class="interest-section page-container"
          aria-labelledby="interest-title"
        >
          <div>
            <p class="eyebrow">KEEP EXPLORING</p>
            <h2 id="interest-title">Stay close to the next chapter.</h2>
            <p>
              Save an email reminder on this device while you explore the
              preview.
            </p>
          </div>
          <form class="interest-form" @submit.prevent="subscribe">
            <label for="email">Your email address</label>
            <div class="email-controls">
              <input
                id="email"
                v-model="email"
                type="email"
                required
                autocomplete="email"
                inputmode="email"
                maxlength="254"
                placeholder="you@example.com"
                :aria-invalid="!!emailError"
                aria-describedby="email-help email-feedback"
                @input="
                  subscribed = false;
                  emailError = '';
                  emailNotice = '';
                "
              /><button class="button primary" type="submit">
                <Check v-if="subscribed" :size="16" />{{
                  subscribed ? "Saved locally" : "Save my interest"
                }}<ArrowRight v-if="!subscribed" :size="16" />
              </button>
            </div>
            <p id="email-help">
              Browser-only reminder. No email is sent or mailing list
              subscription created.
            </p>
            <p
              v-if="emailError"
              id="email-feedback"
              class="form-error"
              role="alert"
            >
              {{ emailError }}
            </p>
            <p v-else id="email-feedback" class="form-success" role="status">
              {{ emailNotice }}
            </p>
            <button
              v-if="subscribed"
              type="button"
              class="text-link"
              @click="forgetEmail"
            >
              Remove saved email <X :size="14" />
            </button>
          </form>
        </section>
      </main>
      <footer class="site-footer page-container">
        <div class="footer-top">
          <a href="#top" class="brand-lockup" :aria-label="`${brand.name} home`"
            ><img
              src="/folivect-mark.svg"
              alt=""
              width="32"
              height="32"
            /><span>{{ brand.name }}</span></a
          >
          <p>{{ brand.tagline }}</p>
          <a
            href="https://docs.robinhood.com/chain/"
            target="_blank"
            rel="noopener noreferrer"
            >Robinhood Chain docs <ArrowUpRight :size="15"
          /></a>
        </div>
        <div class="footer-bottom">
          <p>
            {{ brand.name }} is independent and is not affiliated with Robinhood
            Markets, Inc. Tokenized stocks and onchain services are subject to
            eligibility, jurisdictional, and market risks. Research is not
            investment advice.
          </p>
          <span
            >&copy; 2026 {{ brand.name }}<br />Research with intention.</span
          >
        </div>
      </footer>
    </div>
  </div>
  <WalletModal
    :open="walletOpen"
    @close="walletOpen = false"
    @connected="handleConnected"
    @session-invalidated="invalidateSession"
  />
</template>
