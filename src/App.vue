<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import {
  ArrowRight,
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
  closeMenu();
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
    <aside class="navigation-rail" aria-label="Workspace navigation">
      <a class="rail-brand" href="#top" :aria-label="`${brand.name} home`"
        ><img :src="`/${brand.slug}-mark.svg`" width="42" height="42" alt=""
      /></a>
      <nav>
        <a
          v-for="item in navItems"
          :key="item.id"
          :href="`#${item.id}`"
          :class="{ active: activeSection === item.id }"
          :aria-current="activeSection === item.id ? 'location' : undefined"
          ><component :is="item.icon" :size="21" /><span>{{
            item.label
          }}</span></a
        >
      </nav>
      <div class="rail-bottom">
        <span class="status-dot"></span><span>LOCAL<br />PREVIEW</span>
      </div>
    </aside>
    <header class="site-header">
      <a
        href="#top"
        class="brand-lockup"
        :aria-label="`${brand.name} home`"
        @click="closeMenu"
        ><img
          :src="`/${brand.slug}-mark.svg`"
          width="32"
          height="32"
          alt=""
        /><span>{{ brand.name }}</span></a
      >
      <div class="header-context"><span>/</span> The decision workspace</div>
      <div class="header-actions">
        <span class="preview-label"
          ><span class="status-dot"></span> Research preview</span
        >
        <button
          v-if="connectedAccount"
          class="button wallet-button"
          @click="invalidateSession"
          :aria-label="`End local session for ${shortAccount}`"
        >
          <Check :size="16" /><span>{{ shortAccount }}</span
          ><span class="session-end">End session</span>
        </button>
        <button
          v-else
          class="button wallet-button"
          aria-label="Connect wallet"
          @click="walletOpen = true"
        >
          <Wallet :size="16" /><span>Connect wallet</span>
        </button>
        <button
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
        <div class="page-topline">
          <span>INDEPENDENT THINKING. STRUCTURED.</span
          ><span>WORKSPACE / 001</span>
        </div>
        <div class="hero-grid">
          <div class="hero-copy">
            <p class="eyebrow">
              <span class="status-dot"></span> A CLEARER WAY TO MAKE A CALL
            </p>
            <h1 id="hero-title">Less noise.<br /><em>More perspective.</em></h1>
            <p class="hero-lede">
              Build your thesis. Put it under pressure.<br />Keep the reasoning
              behind every decision.
            </p>
            <div class="hero-actions">
              <button class="button primary" @click="openResearch('Brief')">
                Start researching <ArrowUpRight :size="19" /></button
              ><span>Open to explore.<br />No wallet required.</span>
            </div>
          </div>
          <div
            class="perspective-map"
            role="group"
            aria-label="Research process: one thesis branches into bear, base and bull scenarios before a decision is recorded"
          >
            <div class="map-topline">
              <span>THE PERSPECTIVE ENGINE</span
              ><span class="map-live">ILLUSTRATIVE</span>
            </div>
            <svg
              class="path-diagram"
              viewBox="0 0 510 285"
              fill="none"
              aria-hidden="true"
            >
              <defs>
                <pattern
                  id="map-grid"
                  width="30"
                  height="30"
                  patternUnits="userSpaceOnUse"
                >
                  <circle cx="1" cy="1" r="1" fill="#41505D" />
                </pattern>
              </defs>
              <rect width="510" height="285" fill="url(#map-grid)" />
              <circle
                cx="256"
                cy="143"
                r="104"
                stroke="#33404A"
                stroke-dasharray="3 6"
              />
              <circle cx="256" cy="143" r="62" stroke="#33404A" />
              <path
                d="M20 143H182C224 143 219 62 264 62H478M182 143H478M182 143C224 143 219 224 264 224H478"
                stroke="#536270"
                stroke-width="2"
              />
              <path
                d="M20 143H182C224 143 219 62 264 62H478"
                stroke="#D5FA5B"
                stroke-width="3"
              />
              <rect
                x="53"
                y="114"
                width="115"
                height="58"
                rx="6"
                fill="#D5FA5B"
              />
              <text
                x="110"
                y="139"
                text-anchor="middle"
                fill="#111923"
                font-size="11"
                font-family="Arial"
                font-weight="700"
              >
                YOUR THESIS
              </text>
              <text
                x="110"
                y="156"
                text-anchor="middle"
                fill="#314D1A"
                font-size="10"
                font-family="Arial"
              >
                Start with a question
              </text>
              <circle cx="264" cy="62" r="6" fill="#D5FA5B" />
              <circle cx="264" cy="143" r="5" fill="#A9B6C1" />
              <circle cx="264" cy="224" r="5" fill="#A9B6C1" />
              <text
                x="318"
                y="49"
                fill="#D5FA5B"
                font-size="12"
                font-family="Arial"
                font-weight="700"
              >
                BULL CASE
              </text>
              <text
                x="318"
                y="130"
                fill="#D7DEE5"
                font-size="12"
                font-family="Arial"
                font-weight="700"
              >
                BASE CASE
              </text>
              <text
                x="318"
                y="211"
                fill="#D7DEE5"
                font-size="12"
                font-family="Arial"
                font-weight="700"
              >
                BEAR CASE
              </text>
              <circle cx="478" cy="62" r="4" fill="#D5FA5B" />
              <circle cx="478" cy="143" r="4" fill="#A9B6C1" />
              <circle cx="478" cy="224" r="4" fill="#A9B6C1" />
            </svg>
            <div class="map-bottom">
              <span>One view. Multiple possibilities.</span
              ><button
                @click="openResearch('Scenario')"
                aria-label="Explore scenario possibilities"
              >
                <ArrowUpRight :size="20" />
              </button>
            </div>
          </div>
        </div>
        <div
          class="hero-index"
          role="group"
          aria-label="Choose a research step"
        >
          <button @click="openResearch('Sources')">
            <span class="index-icon"><FileText :size="22" /></span>
            <div>
              <span class="index-number">01 / INVESTIGATE</span
              ><strong>Find the other side.</strong
              ><small>Evidence, context &amp; counter-cases</small>
            </div>
            <ArrowUpRight :size="19" />
          </button>
          <button @click="openResearch('Scenario')">
            <span class="index-icon"><SlidersHorizontal :size="22" /></span>
            <div>
              <span class="index-number">02 / PRESSURE-TEST</span
              ><strong>Make uncertainty visible.</strong
              ><small>Three scenarios. Your assumptions.</small>
            </div>
            <ArrowUpRight :size="19" />
          </button>
          <button @click="openJournal">
            <span class="index-icon"><BookOpen :size="22" /></span>
            <div>
              <span class="index-number">03 / REFLECT</span
              ><strong>Remember your reasoning.</strong
              ><small>A decision trail you can revisit</small>
            </div>
            <ArrowUpRight :size="19" />
          </button>
        </div>
      </section>
      <section
        id="cockpit"
        class="workspace-section page-container"
        aria-labelledby="workspace-title"
      >
        <div class="section-intro">
          <div>
            <p class="eyebrow">YOUR WORKSPACE</p>
            <h2 id="workspace-title">
              From a view to a decision<span>.</span>
            </h2>
          </div>
          <span class="sample-badge"
            ><span class="status-dot"></span> 4 sample assets / Working
            tools</span
          >
        </div>
        <MarketCockpit ref="workbench" />
        <div class="workspace-caption">
          <span
            >Sample research. Hypothetical scenarios. Real room to think.</span
          ><span>Not investment advice.</span>
        </div>
      </section>
      <section
        id="method"
        class="method-section page-container"
        aria-labelledby="method-title"
      >
        <div class="section-intro">
          <div>
            <p class="eyebrow">THE OPERATING PRINCIPLE</p>
            <h2 id="method-title">A process, not a prediction.</h2>
          </div>
          <p>Better questions at every step.</p>
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
              ><component :is="item.icon" :size="22" /><span>{{
                item.label
              }}</span
              ><ArrowRight :size="18" />
            </button>
          </div>
          <article class="method-detail" aria-live="polite">
            <div class="method-kicker">
              <span>{{ layer.tag }}</span
              ><span>{{ layer.note }}</span>
            </div>
            <div class="method-body">
              <h3>{{ layer.headline }}</h3>
              <div>
                <p>{{ layer.detail }}</p>
                <button class="text-link" @click="launchLayer">
                  {{ layer.action }} <ArrowRight :size="18" />
                </button>
              </div>
            </div>
          </article>
        </div>
      </section>
      <section
        id="journal"
        class="journal-section page-container"
        aria-labelledby="journal-title"
      >
        <div class="journal-copy">
          <p class="eyebrow">THE DECISION TRAIL</p>
          <h2 id="journal-title">
            Your thinking.<br />Saved for the next you.
          </h2>
          <p>
            The view. The assumptions. The why. Keep them together, then revisit
            with a fresh perspective.
          </p>
          <button class="button primary" @click="openJournal">
            Open your decision journal <ArrowUpRight :size="18" /></button
          ><small>On this device. Exportable. Always yours to delete.</small>
        </div>
        <article class="example-note">
          <div class="note-heading">
            <span><BookOpen :size="18" /> DECISION SNAPSHOT</span
            ><span>EXAMPLE</span>
          </div>
          <div class="note-asset">
            <strong>AAPL</strong><span>Apple Inc.</span
            ><span class="note-label">BASE CASE</span>
          </div>
          <h3>What is already priced<br />into the story?</h3>
          <div class="note-row">
            <span>WORKING VIEW</span>
            <p>Services resilience supports the thesis.</p>
          </div>
          <div class="note-row">
            <span>WATCH NEXT</span>
            <p>Growth expectations and the price of optimism.</p>
          </div>
          <div class="note-footer">
            <span class="status-dot"></span> A snapshot to revisit. A view that
            can evolve.
          </div>
        </article>
      </section>
      <section
        id="roadmap"
        class="roadmap-section page-container"
        aria-labelledby="roadmap-title"
      >
        <div class="section-intro">
          <div>
            <p class="eyebrow">WHAT COMES NEXT</p>
            <h2 id="roadmap-title">Built one useful step at a time.</h2>
          </div>
          <p>Current capabilities. Clear release gates.</p>
        </div>
        <div class="roadmap-grid">
          <article class="roadmap-card current">
            <div>
              <span>01</span><span class="roadmap-status">AVAILABLE NOW</span>
            </div>
            <h3>Research workspace</h3>
            <p>
              Sample briefs, adjustable scenarios, and a local decision journal.
            </p>
            <a href="#cockpit"
              >Explore the preview <ArrowUpRight :size="16"
            /></a>
          </article>
          <article class="roadmap-card">
            <div>
              <span>02</span><span class="roadmap-status">IN PLANNING</span>
            </div>
            <h3>Connected context</h3>
            <p>
              Verified data sources and wallet context, after privacy review.
            </p>
            <span class="roadmap-note">DATA &amp; PRIVACY REVIEW</span>
          </article>
          <article class="roadmap-card">
            <div>
              <span>03</span><span class="roadmap-status">RESEARCH STAGE</span>
            </div>
            <h3>Verifiable intent</h3>
            <p>Testnet intent and proof records, subject to security review.</p>
            <span class="roadmap-note">SECURITY REVIEW</span>
          </article>
          <article class="roadmap-card">
            <div><span>04</span><span class="roadmap-status">GATED</span></div>
            <h3>Scoped execution</h3>
            <p>Limited mainnet routing, gated by audit and legal approval.</p>
            <span class="roadmap-note">AUDIT &amp; LEGAL REVIEW</span>
          </article>
        </div>
      </section>
      <section
        id="beta"
        class="interest-section page-container"
        aria-labelledby="interest-title"
      >
        <div>
          <p class="eyebrow">KEEP IT ON YOUR RADAR</p>
          <h2 id="interest-title">A reminder to return.</h2>
          <p>Save your email on this device while you explore.</p>
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
            A local reminder. No email is sent or mailing list subscription
            created.
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
            :src="`/${brand.slug}-mark.svg`"
            alt=""
            width="32"
            height="32"
          /><span>{{ brand.name }}</span></a
        >
        <p>{{ brand.tagline }}</p>
        <div class="footer-links">
          <a
            :href="`https://x.com/${brand.handle.slice(1)}`"
            target="_blank"
            rel="noopener noreferrer"
            >X / {{ brand.handle }} <ArrowUpRight :size="15" /></a
          ><a
            href="https://docs.robinhood.com/chain/"
            target="_blank"
            rel="noopener noreferrer"
            >Network docs <ArrowUpRight :size="15"
          /></a>
        </div>
      </div>
      <div class="footer-bottom">
        <p>
          {{ brand.name }} is independent and is not affiliated with Robinhood
          Markets, Inc. Tokenized stocks and onchain services are subject to
          eligibility, jurisdictional, and market risks. Research is not
          investment advice.
        </p>
        <span>&copy; 2026 {{ brand.name }}<br />Think it through.</span>
      </div>
    </footer>
  </div>
  <WalletModal
    :open="walletOpen"
    @close="walletOpen = false"
    @connected="handleConnected"
    @session-invalidated="invalidateSession"
  />
</template>
