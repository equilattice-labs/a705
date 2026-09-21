<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import {
  ArrowRight,
  BookOpen,
  Route,
  ArrowUpRight,
  Check,
  FileText,
  Menu,
  SlidersHorizontal,
  Wallet,
  X,
  Layers3,
  LayoutDashboard,
  FlaskConical,
  Activity,
  ShieldCheck,
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
  { id: "cockpit", label: "Research lab", icon: Activity },
  { id: "method", label: "Method", icon: FlaskConical },
  { id: "journal", label: "Journal", icon: BookOpen },
  { id: "roadmap", label: "Roadmap", icon: Route },
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
    <aside class="app-sidebar" aria-label="Application sidebar">
      <a
        href="#top"
        class="brand-lockup"
        :aria-label="`${brand.name} home`"
        @click="closeMenu"
      >
        <img :src="`/${brand.slug}-mark.svg`" width="38" height="38" alt="" />
        <span>{{ brand.name }}<small>RESEARCH LAB</small></span>
      </a>
      <div class="sidebar-label">WORKSPACE <span>01</span></div>
      <nav class="side-navigation" aria-label="Main navigation">
        <a
          v-for="item in navItems"
          :key="item.id"
          :href="`#${item.id}`"
          :aria-current="activeSection === item.id ? 'location' : undefined"
          :title="item.label"
        >
          <component :is="item.icon" :size="18" /><span>{{ item.label }}</span
          ><span v-if="item.id === 'cockpit'" class="nav-count">4</span>
        </a>
      </nav>
      <div class="sidebar-bottom">
        <div class="local-mode">
          <span class="status-dot"></span
          ><span
            >Local-first preview<small>Your thinking stays yours.</small></span
          >
        </div>
        <a href="#beta" class="sidebar-interest"
          >Keep me in the loop <ArrowUpRight :size="16"
        /></a>
        <span class="sidebar-version">RESEARCH / v0.1</span>
      </div>
    </aside>
    <div class="app-main">
      <header class="app-header">
        <div class="mobile-brand">
          <a href="#top" class="brand-lockup" :aria-label="`${brand.name} home`"
            ><img
              :src="`/${brand.slug}-mark.svg`"
              width="32"
              height="32"
              alt=""
            /><span>{{ brand.name }}</span></a
          >
        </div>
        <div class="header-path">
          <span>Workspace</span><span class="path-divider">/</span
          ><strong>{{
            navItems.find((item) => item.id === activeSection)?.label ||
            "Overview"
          }}</strong>
        </div>
        <div class="header-actions">
          <span class="preview-badge"
            ><span class="status-dot"></span> Interactive preview</span
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
          aria-label="Mobile navigation"
        >
          <a
            v-for="item in navItems"
            :key="item.id"
            :href="`#${item.id}`"
            @click="closeMenu"
            ><component :is="item.icon" :size="18" />{{ item.label
            }}<ArrowUpRight :size="17"
          /></a>
        </nav>
      </header>
      <main>
        <section
          id="top"
          class="hero-section page-container"
          aria-labelledby="hero-title"
        >
          <div class="hero-copy">
            <p class="eyebrow">
              <span class="eyebrow-square"></span> INDEPENDENT THINKING. IN
              FOCUS.
            </p>
            <h1 id="hero-title">
              Conviction is<br />a <span>hypothesis.</span>
            </h1>
            <p class="hero-lede">
              Give it a proper test. Explore the evidence, map the downside, and
              keep a record of why you decided.
            </p>
            <div class="hero-actions">
              <button class="button primary" @click="openResearch('Brief')">
                Start researching <ArrowUpRight :size="18" /></button
              ><button class="hero-secondary" @click="openResearch('Scenario')">
                Test a scenario <ArrowRight :size="16" />
              </button>
            </div>
            <div class="hero-proof">
              <ShieldCheck :size="14" /><span>No wallet required</span
              ><span class="proof-divider"></span
              ><span>Saved on your device</span>
            </div>
          </div>
          <div
            class="scenario-visual"
            role="img"
            aria-label="Illustrative research map: one starting hypothesis branches into upside, base, and downside cases. Scenarios are assumptions, not forecasts."
          >
            <div class="visual-heading">
              <span><Layers3 :size="14" /> THE POSSIBILITY SPACE</span
              ><span class="visual-code">MODEL / 001</span>
            </div>
            <svg class="branch-map" viewBox="0 0 560 330" aria-hidden="true">
              <defs>
                <pattern
                  id="research-grid"
                  width="28"
                  height="28"
                  patternUnits="userSpaceOnUse"
                >
                  <path
                    d="M 28 0 L 0 0 0 28"
                    fill="none"
                    stroke="#283549"
                    stroke-width="0.7"
                  />
                </pattern>
                <linearGradient id="scenario-fill" x1="0" x2="1">
                  <stop offset="0" stop-color="#c4f06a" stop-opacity=".02" />
                  <stop offset="1" stop-color="#c4f06a" stop-opacity=".1" />
                </linearGradient>
              </defs>
              <rect
                x="14"
                y="10"
                width="532"
                height="306"
                fill="url(#research-grid)"
              />
              <path
                d="M73 187 C156 186 172 187 219 164 C286 132 286 64 449 48 L449 278 C314 277 287 242 219 207 C181 188 159 187 73 187Z"
                fill="url(#scenario-fill)"
              />
              <path
                d="M73 187H475"
                stroke="#526179"
                stroke-width="1"
                stroke-dasharray="3 7"
              />
              <path
                d="M73 187 C151 187 164 198 215 177 S288 66 449 48"
                stroke="#c4f06a"
                stroke-width="2.5"
                fill="none"
              />
              <path
                d="M73 187 C164 187 192 186 226 173 S327 148 449 148"
                stroke="#8fb9ff"
                stroke-width="2.5"
                fill="none"
              />
              <path
                d="M73 187 C151 187 172 183 219 206 S314 277 449 278"
                stroke="#71879e"
                stroke-width="2"
                fill="none"
              />
              <path
                d="M219 30V294"
                stroke="#34445b"
                stroke-width="1"
                stroke-dasharray="3 6"
              />
              <circle cx="73" cy="187" r="21" fill="#c4f06a" opacity=".07" />
              <circle
                cx="73"
                cy="187"
                r="11"
                fill="#121c2b"
                stroke="#c4f06a"
                stroke-width="1"
              />
              <circle cx="73" cy="187" r="4" fill="#c4f06a" />
              <circle cx="449" cy="48" r="5" fill="#c4f06a" />
              <circle cx="449" cy="148" r="5" fill="#8fb9ff" />
              <circle cx="449" cy="278" r="5" fill="#71879e" />
              <text
                x="70"
                y="230"
                fill="#a5b1c2"
                font-size="9"
                font-family="Consolas,monospace"
              >
                YOUR THESIS
              </text>
              <text
                x="228"
                y="30"
                fill="#70839a"
                font-size="8"
                font-family="Consolas,monospace"
              >
                TEST THE ASSUMPTIONS
              </text>
              <text
                x="466"
                y="46"
                fill="#c4f06a"
                font-size="10"
                font-family="Consolas,monospace"
              >
                UPSIDE
              </text>
              <text
                x="466"
                y="60"
                fill="#70839a"
                font-size="8"
                font-family="Consolas,monospace"
              >
                CASE 03
              </text>
              <text
                x="466"
                y="146"
                fill="#8fb9ff"
                font-size="10"
                font-family="Consolas,monospace"
              >
                BASE
              </text>
              <text
                x="466"
                y="160"
                fill="#70839a"
                font-size="8"
                font-family="Consolas,monospace"
              >
                CASE 02
              </text>
              <text
                x="466"
                y="276"
                fill="#a5b1c2"
                font-size="10"
                font-family="Consolas,monospace"
              >
                DOWNSIDE
              </text>
              <text
                x="466"
                y="290"
                fill="#70839a"
                font-size="8"
                font-family="Consolas,monospace"
              >
                CASE 01
              </text>
            </svg>
            <div class="visual-footer">
              <span
                ><span class="status-dot"></span> One thesis. Multiple
                futures.</span
              ><span>ILLUSTRATIVE MODEL</span>
            </div>
          </div>
        </section>
        <div
          class="launch-strip page-container"
          aria-label="Research shortcuts"
        >
          <button @click="openResearch('Sources')">
            <span class="launch-number">01</span
            ><span
              ><strong>Explore the evidence</strong
              ><small>Read the thesis. Challenge the story.</small></span
            ><ArrowUpRight :size="18" />
          </button>
          <button @click="openResearch('Scenario')">
            <span class="launch-number">02</span
            ><span
              ><strong>Test the possibilities</strong
              ><small>Bear, base, bull. Make it measurable.</small></span
            ><ArrowUpRight :size="18" />
          </button>
          <button @click="openJournal">
            <span class="launch-number">03</span
            ><span
              ><strong>Keep the reasoning</strong
              ><small>A decision you can come back to.</small></span
            ><ArrowUpRight :size="18" />
          </button>
        </div>
        <section
          id="cockpit"
          class="workspace-section page-container"
          aria-labelledby="workspace-title"
        >
          <div class="section-intro workspace-intro">
            <div>
              <p class="eyebrow">YOUR WORKSPACE</p>
              <h2 id="workspace-title">Research, with the controls on.</h2>
            </div>
            <div class="section-aside">
              <span class="sample-badge">SAMPLE DATA</span
              ><span>4 assets · 3 scenarios · Your perspective</span>
            </div>
          </div>
          <MarketCockpit ref="workbench" />
          <div class="workspace-caption">
            <span
              ><ShieldCheck :size="12" /> Sample research and hypothetical
              scenarios.</span
            ><span>For exploration. Not investment advice.</span>
          </div>
        </section>
        <section
          id="method"
          class="method-section page-container"
          aria-labelledby="method-title"
        >
          <div class="section-intro">
            <div>
              <p class="eyebrow">THE RESEARCH LOOP</p>
              <h2 id="method-title">A process that makes room for doubt.</h2>
            </div>
            <p class="section-description">
              Better questions lead to better decisions. Move from evidence to
              assumptions to a record you can revisit.
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
                <component :is="item.icon" :size="21" /><span
                  ><small
                    >0{{ index + 1 }} / {{ item.label.toUpperCase() }}</small
                  ><strong>{{ item.title }}</strong></span
                ><ArrowUpRight :size="18" />
              </button>
            </div>
            <article class="method-detail" aria-live="polite">
              <div class="method-detail-main">
                <p class="eyebrow">{{ layer.tag }}</p>
                <h3>{{ layer.headline }}</h3>
                <p>{{ layer.detail }}</p>
                <button class="text-link" @click="launchLayer">
                  {{ layer.action }} <ArrowRight :size="18" />
                </button>
              </div>
              <div class="method-glyph" aria-hidden="true">
                <span class="glyph-ring ring-outer"></span
                ><span class="glyph-ring ring-middle"></span
                ><span class="glyph-ring ring-inner"></span
                ><component :is="layer.icon" :size="36" /><span
                  class="glyph-coordinate"
                  >0{{ activeLayer + 1 }} / 03</span
                >
              </div>
            </article>
          </div>
        </section>
        <section
          id="journal"
          class="journal-section page-container"
          aria-labelledby="journal-title"
        >
          <div class="journal-panel">
            <div class="journal-copy">
              <p class="eyebrow">
                <BookOpen :size="15" /> YOUR DECISION JOURNAL
              </p>
              <h2 id="journal-title">Don't lose the <span>why.</span></h2>
              <p>
                Markets move. Memory edits. Keep the thesis, the assumptions,
                and your reasoning together — exactly as you saw them.
              </p>
              <button class="button primary" @click="openJournal">
                Open your journal <ArrowUpRight :size="18" /></button
              ><small
                ><ShieldCheck :size="13" /> Local to your device. Yours to
                export.</small
              >
            </div>
            <article class="example-note">
              <div class="note-heading">
                <span><span class="status-dot"></span> DECISION RECORD</span
                ><span>EXAMPLE / 001</span>
              </div>
              <div class="note-asset">
                <span class="note-symbol">A</span>
                <div><strong>AAPL</strong><small>Apple Inc.</small></div>
                <span class="note-case">BASE CASE</span>
              </div>
              <div class="note-row">
                <span>01 / THESIS</span>
                <p>Services resilience supports the working view.</p>
              </div>
              <div class="note-row">
                <span>02 / OPEN QUESTION</span>
                <p>How much optimism does the current price assume?</p>
              </div>
              <div class="note-footer">
                <Check :size="14" /> A snapshot of thinking. Ready to revisit.
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
              <p class="eyebrow">BUILDING IN THE OPEN</p>
              <h2 id="roadmap-title">
                Useful today. Deliberate about tomorrow.
              </h2>
            </div>
            <p class="section-description">
              A working preview with clear boundaries. Every next step needs
              evidence of its own.
            </p>
          </div>
          <div class="roadmap-grid">
            <article class="roadmap-active">
              <div class="roadmap-top">
                <span>01 / AVAILABLE</span><span class="status-dot"></span>
              </div>
              <h3>Research &amp;<br />reflection</h3>
              <p>
                Sample briefs, adjustable scenarios, and your local decision
                journal.
              </p>
              <a href="#cockpit">Explore the lab <ArrowUpRight :size="16" /></a>
            </article>
            <article>
              <div class="roadmap-top">
                <span>02 / IN PLANNING</span><Route :size="15" />
              </div>
              <h3>Connected<br />context</h3>
              <p>
                Verified data and wallet context, after data and privacy review.
              </p>
              <span class="roadmap-stage">DATA &amp; PRIVACY REVIEW</span>
            </article>
            <article>
              <div class="roadmap-top">
                <span>03 / RESEARCH</span><Layers3 :size="15" />
              </div>
              <h3>Verifiable<br />intent</h3>
              <p>Testnet proof records, subject to security review.</p>
              <span class="roadmap-stage">SECURITY REVIEW REQUIRED</span>
            </article>
            <article>
              <div class="roadmap-top">
                <span>04 / GATED</span><ShieldCheck :size="15" />
              </div>
              <h3>Scoped<br />execution</h3>
              <p>Limited mainnet routing, gated by audit and legal approval.</p>
              <span class="roadmap-stage">AUDIT &amp; LEGAL APPROVAL</span>
            </article>
          </div>
        </section>
        <section
          id="beta"
          class="interest-section page-container"
          aria-labelledby="interest-title"
        >
          <div>
            <p class="eyebrow">KEEP THE THREAD</p>
            <h2 id="interest-title">A reminder to stay curious.</h2>
            <p>Save your interest on this device while you explore.</p>
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
              Saved only in this browser. No email is sent and no mailing list
              is joined.
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
              >{{ brand.handle }} <ArrowUpRight :size="14" /></a
            ><a
              href="https://docs.robinhood.com/chain/"
              target="_blank"
              rel="noopener noreferrer"
              >Network docs <ArrowUpRight :size="14"
            /></a>
          </div>
        </div>
        <div class="footer-bottom">
          <p>
            {{ brand.name }} is independent and is not affiliated with Robinhood
            Markets, Inc. This preview uses sample data and browser-local
            records. Research is not investment advice. Tokenized stocks and
            onchain services are subject to eligibility, jurisdictional, and
            market risks.
          </p>
          <span
            >&copy; 2026 {{ brand.name }}<br />Question. Test. Revisit.</span
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
