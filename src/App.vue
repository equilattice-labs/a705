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
  { id: "top", label: "Overview", icon: FileText },
  { id: "cockpit", label: "Research desk", icon: FileText },
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
    <div class="edition-line page-container">
      <span>INDEPENDENT RESEARCH, CONSIDERED.</span
      ><span>THE RESEARCH EDITION / 001</span>
    </div>
    <header class="site-header">
      <div class="header-inner page-container">
        <a
          href="#top"
          class="brand-lockup"
          :aria-label="`${brand.name} home`"
          @click="closeMenu"
          ><img
            :src="`/${brand.slug}-mark.svg`"
            width="38"
            height="38"
            alt=""
          /><span>{{ brand.name }}</span></a
        >
        <nav class="desktop-navigation" aria-label="Main navigation">
          <a
            href="#cockpit"
            :aria-current="activeSection === 'cockpit' ? 'location' : undefined"
            >Research desk</a
          >
          <a
            href="#method"
            :aria-current="activeSection === 'method' ? 'location' : undefined"
            >Our method</a
          >
          <button @click="openJournal">
            Your journal <ArrowUpRight :size="14" />
          </button>
        </nav>
        <div class="header-actions">
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
          >{{ item.label }}<ArrowUpRight :size="17"
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
            <span class="small-rule"></span> A FIELD GUIDE TO YOUR NEXT DECISION
          </p>
          <h1 id="hero-title">Conviction,<br />with <em>context.</em></h1>
          <p class="hero-lede">
            Good decisions begin with a better question.<br
              class="desktop-break"
            />
            Explore the evidence, test your assumptions,<br
              class="desktop-break"
            />
            and give your thinking a place to grow.
          </p>
          <div class="hero-actions">
            <button class="button primary" @click="openResearch('Brief')">
              Open the research desk <ArrowUpRight :size="18" /></button
            ><span>No wallet needed.<br />Just a curious mind.</span>
          </div>
        </div>
        <div
          class="hero-art"
          role="img"
          aria-label="An open research folio with overlapping lenses, a reminder to examine a decision from several perspectives"
        >
          <span class="art-annotation annotation-top"
            >FIG. 01 / A CHANGE OF PERSPECTIVE</span
          >
          <div class="folio-shadow"></div>
          <div class="folio-sheet folio-back"></div>
          <div class="folio-sheet folio-front">
            <div class="folio-top">
              <span>THE OPEN QUESTION</span><span>01 / 03</span>
            </div>
            <div class="lens-composition">
              <div class="lens lens-one"></div>
              <div class="lens lens-two"></div>
              <div class="lens lens-three"></div>
              <span class="lens-cross cross-one">+</span
              ><span class="lens-cross cross-two">+</span>
            </div>
            <p>What would<br /><em>change your mind?</em></p>
            <div class="folio-baseline">
              <span>EVIDENCE</span><span>ASSUMPTION</span><span>JUDGMENT</span>
            </div>
          </div>
          <span class="art-annotation annotation-bottom"
            >A LITTLE DISTANCE. A CLEARER VIEW.</span
          ><span class="art-seal" aria-hidden="true"
            >KEEP<br />ASKING<br /><ArrowUpRight :size="23"
          /></span>
        </div>
      </section>
      <div class="reading-strip page-container">
        <span class="eyebrow">A PRACTICE IN THREE PARTS</span
        ><button @click="openResearch('Sources')">
          <span>01</span> Read the evidence <ArrowRight :size="16" /></button
        ><button @click="openResearch('Scenario')">
          <span>02</span> Test the possibilities
          <ArrowRight :size="16" /></button
        ><button @click="openJournal">
          <span>03</span> Keep the reasoning <ArrowRight :size="16" />
        </button>
      </div>
      <section
        id="cockpit"
        class="workspace-section page-container"
        aria-labelledby="workspace-title"
      >
        <div class="section-intro">
          <div>
            <p class="eyebrow">01 / THE RESEARCH DESK</p>
            <h2 id="workspace-title">Make room for <em>another view.</em></h2>
          </div>
          <p class="section-aside">
            <span class="status-dot"></span> Interactive research preview<br /><span
              >Four sample assets. Your own perspective.</span
            >
          </p>
        </div>
        <MarketCockpit ref="workbench" />
        <div class="workspace-caption">
          <span>Sample research and hypothetical scenarios.</span
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
            <p class="eyebrow">02 / THE METHOD</p>
            <h2 id="method-title">
              A question before<br />every <em>conclusion.</em>
            </h2>
          </div>
          <p class="method-intro">
            A useful research process leaves space for doubt. Move between the
            evidence, the possibilities, and the reasoning you want to remember.
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
              <span>0{{ index + 1 }}</span
              ><strong>{{ item.label }}</strong
              ><ArrowUpRight :size="19" />
            </button>
          </div>
          <article class="method-detail" aria-live="polite">
            <p class="eyebrow">{{ layer.note }}</p>
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
        class="journal-section"
        aria-labelledby="journal-title"
      >
        <div class="journal-layout page-container">
          <div class="journal-copy">
            <p class="eyebrow">03 / THE DECISION JOURNAL</p>
            <h2 id="journal-title">
              Your future self<br />will ask <em>why.</em>
            </h2>
            <p>
              Leave a thoughtful answer. Save the view, the assumptions, and the
              moment behind a decision. Come back when the story changes.
            </p>
            <button class="button light-button" @click="openJournal">
              Open your decision journal <ArrowUpRight :size="18" /></button
            ><small>Saved on your device. Ready to revisit or export.</small>
          </div>
          <article class="example-note">
            <div class="note-heading">
              <BookOpen :size="19" /><span>A NOTE TO RETURN TO</span
              ><span>EXAMPLE</span>
            </div>
            <div class="note-asset">
              <strong>AAPL</strong><span>Apple Inc. / Base case</span>
            </div>
            <h3>What is already priced<br />into the story?</h3>
            <div class="note-row">
              <span>THE WORKING VIEW</span>
              <p>Services resilience supports the thesis.</p>
            </div>
            <div class="note-row">
              <span>THE OPEN QUESTION</span>
              <p>How much optimism does the current price assume?</p>
            </div>
            <div class="note-footer">
              A snapshot of your thinking. Not a fixed conclusion.
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
            <p class="eyebrow">THE NEXT CHAPTER</p>
            <h2 id="roadmap-title">
              Useful now.<br /><em>Considered next.</em>
            </h2>
          </div>
          <p class="method-intro">
            A working preview, with clear boundaries.<br />Each next step needs
            evidence of its own.
          </p>
        </div>
        <div class="roadmap-list">
          <article>
            <span class="roadmap-number">01</span>
            <h3>Research &amp; reflection</h3>
            <p>
              Sample briefs, adjustable scenarios, and your local decision
              journal.
            </p>
            <a href="#cockpit" class="roadmap-status"
              >EXPLORE NOW <ArrowUpRight :size="16"
            /></a>
          </article>
          <article>
            <span class="roadmap-number">02</span>
            <h3>Connected context</h3>
            <p>
              Verified data and wallet context, after data and privacy review.
            </p>
            <span class="roadmap-status">IN PLANNING</span>
          </article>
          <article>
            <span class="roadmap-number">03</span>
            <h3>Verifiable intent</h3>
            <p>Testnet proof records, subject to security review.</p>
            <span class="roadmap-status">RESEARCH STAGE</span>
          </article>
          <article>
            <span class="roadmap-number">04</span>
            <h3>Scoped execution</h3>
            <p>Limited mainnet routing, gated by audit and legal approval.</p>
            <span class="roadmap-status">GATED</span>
          </article>
        </div>
      </section>
      <section
        id="beta"
        class="interest-section page-container"
        aria-labelledby="interest-title"
      >
        <div>
          <p class="eyebrow">A PLACE ON YOUR READING LIST</p>
          <h2 id="interest-title">Come back <em>curious.</em></h2>
          <p>Keep a reminder on this device while you explore.</p>
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
            Saved only in this browser. No email is sent and no mailing list is
            joined.
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
            width="36"
            height="36"
          /><span>{{ brand.name }}</span></a
        >
        <p>{{ brand.tagline }}</p>
        <div class="footer-links">
          <a
            :href="`https://x.com/${brand.handle.slice(1)}`"
            target="_blank"
            rel="noopener noreferrer"
            >X / {{ brand.handle }} <ArrowUpRight :size="14" /></a
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
          Markets, Inc. This preview uses sample data and browser-local records.
          Research is not investment advice. Tokenized stocks and onchain
          services are subject to eligibility, jurisdictional, and market risks.
        </p>
        <span
          >&copy; 2026 {{ brand.name }}<br />An open mind is a good
          beginning.</span
        >
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
