<script setup>
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from "vue";
import {
  ArrowRight,
  BarChart3,
  Check,
  ChevronRight,
  ExternalLink,
  Menu,
  ShieldAlert,
  TrendingUp,
  X,
  Zap,
} from "lucide-vue-next";
import { brand, storageKeys } from "./brand.js";
import {
  SNAPSHOT,
  validateScenarioInputs,
  calculateScenario,
  createJournalRecord,
  validateJournalRecord,
} from "./scenario.js";

const normalizePath = (value) =>
  ["/pass", "/pulse"].includes(value.replace(/\/$/, ""))
    ? "/signal"
    : value.replace(/\/$/, "") || "/";
const path = ref(normalizePath(location.pathname));
const menuOpen = ref(false);
const step = ref("form");
const amount = ref("1000");
const movePct = ref("-15");
const note = ref("");
const record = ref(null);
const errors = ref({});
const storageNotice = ref("");
const feedback = ref("");
const heading = ref(null);
const menuButton = ref(null);
const captureLabel = "22 Sep 2026 · 02:27 UTC";
const peers = [
  { symbol: "DOGE", price: 0.099869125, change: 12.85 },
  { symbol: "SHIB", price: 0.00000599755, change: 7.97 },
  { symbol: "SOL", price: 117.66583068, change: 5.5 },
  { symbol: "BTC", price: 85727.03917655, change: 5.29 },
  { symbol: "ETH", price: 2746.32311175, change: 3.04 },
];
const sections = [
  { id: "overview", title: "Overview" },
  { id: "sources", title: "Data source" },
  { id: "scenario", title: "Scenario math" },
  { id: "storage", title: "Local journal" },
  { id: "limits", title: "Limits" },
];
const stages = [
  [
    "Snapshot recorded",
    "The original reference price and source travel with this note.",
  ],
  [
    "Assumption reviewed",
    "Your selected price change is an assumption, not a forecast.",
  ],
  [
    "Context reviewed",
    "DOGE can move sharply. This model excludes fees and execution.",
  ],
  ["Review complete", "Export your note or return to an earlier check."],
];
const currency = (value, digits = 2) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
const percent = (value) =>
  (Number(value) > 0 ? "+" : "") + Number(value).toFixed(2) + "%";
const quantity = (value) =>
  new Intl.NumberFormat("en-US", { maximumFractionDigits: 8 }).format(
    Number(value),
  );
const referencePrice = computed(() => currency(SNAPSHOT.price, 5));
const activeSnapshot = computed(() => record.value?.snapshot ?? SNAPSHOT);
const decimalInput = (value) => Number(value).toFixed(8).replace(/\.?0+$/, "");
const input = computed(() => ({
  amount: amount.value,
  movePct: movePct.value,
  note: note.value,
}));
const result = computed(() =>
  record.value ? calculateScenario(record.value, record.value.snapshot) : null,
);
const selectedMove = computed(() => Number(movePct.value));
const remaining = computed(() => 1000 - note.value.length);
const pageTitles = {
  "/": "DOGE snapshot",
  "/signal": "Scenario sandbox",
  "/docs": "Method",
  "/stats": "Market board",
  "/whitepaper": "Field note",
};

async function focusHeading() {
  await nextTick();
  heading.value?.focus({ preventScroll: true });
}
async function navigate(to) {
  menuOpen.value = false;
  const [targetPath, targetHash = ""] = to.split("#", 2);
  const normalizedTarget = normalizePath(targetPath || "/");
  if (normalizedTarget === path.value && !targetHash) return;
  history.pushState({}, "", to);
  path.value = normalizedTarget;
  await focusHeading();
  const behavior = matchMedia("(prefers-reduced-motion: reduce)").matches
    ? "instant"
    : "smooth";
  if (targetHash) {
    await nextTick();
    document.getElementById(targetHash)?.scrollIntoView({ behavior });
  } else window.scrollTo({ top: 0, behavior });
}
function onPop() {
  path.value = normalizePath(location.pathname);
  menuOpen.value = false;
}
function onKey(event) {
  if (event.key === "Escape" && menuOpen.value) {
    menuOpen.value = false;
    nextTick(() => menuButton.value?.focus());
  }
}
async function review() {
  const validation = validateScenarioInputs(input.value);
  errors.value = validation.errors;
  feedback.value = "";
  if (!validation.valid) {
    await nextTick();
    document.querySelector('[aria-invalid="true"]')?.focus();
    return;
  }
  record.value = createJournalRecord(validation.value, {
    id: "DP-" + crypto.randomUUID(),
    createdAt: new Date().toISOString(),
    snapshot: activeSnapshot.value,
  });
  step.value = "review";
  await focusHeading();
}
function persist() {
  try {
    localStorage.setItem(storageKeys.journal, JSON.stringify(record.value));
    storageNotice.value = "";
    feedback.value = "Saved in this browser.";
    return true;
  } catch {
    storageNotice.value =
      "Browser storage is unavailable. Your note remains open; download it to keep a copy.";
    feedback.value = "";
    return false;
  }
}
async function save() {
  persist();
  step.value = "journal";
  await focusHeading();
}
function changeStage(delta) {
  record.value = {
    ...record.value,
    stage: Math.max(0, Math.min(3, record.value.stage + delta)),
  };
  persist();
}
function edit() {
  if (record.value) {
    amount.value = decimalInput(record.value.amount);
    movePct.value = String(record.value.movePct);
    note.value = record.value.note;
  }
  errors.value = {};
  feedback.value = "";
  step.value = "form";
  focusHeading();
}
function newScenario() {
  step.value = "form";
  record.value = null;
  amount.value = "1000";
  movePct.value = "-15";
  note.value = "";
  errors.value = {};
  feedback.value = "";
  focusHeading();
}
function removeJournal() {
  try {
    localStorage.removeItem(storageKeys.journal);
    storageNotice.value = "";
    newScenario();
    feedback.value = "Saved journal removed from this browser.";
  } catch {
    storageNotice.value =
      "This browser blocked deletion. You can remove site data in browser settings.";
  }
}
function downloadJournal() {
  if (!record.value) return;
  const value = {
    ...record.value,
    calculations: result.value,
    disclaimer:
      "User-defined scenario, not a forecast. Excludes fees, spread, tax and execution. Independent of Robinhood and Dogecoin.",
  };
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(value, null, 2) + "\n"], {
      type: "application/json",
    }),
  );
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "dogepulse-" + record.value.id.toLowerCase() + ".json";
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  feedback.value = "Journal download prepared.";
}
watch(
  path,
  () => {
    document.title =
      (pageTitles[path.value] || "Page not found") + " · " + brand.name;
  },
  { immediate: true },
);
onMounted(() => {
  addEventListener("popstate", onPop);
  addEventListener("keydown", onKey);
  if (location.pathname !== path.value)
    history.replaceState({}, "", path.value);
  try {
    const raw = localStorage.getItem(storageKeys.journal);
    if (raw) {
      const restored = validateJournalRecord(JSON.parse(raw));
      if (restored.valid) {
        record.value = restored.value;
        amount.value = decimalInput(restored.value.amount);
        movePct.value = String(restored.value.movePct);
        note.value = restored.value.note;
        step.value = "journal";
      } else
        storageNotice.value =
          "A saved record could not be read. Create a new scenario to replace it.";
    }
  } catch {
    storageNotice.value =
      "Saved data is unavailable or unreadable. You can still build and download a scenario.";
  }
});
onBeforeUnmount(() => {
  removeEventListener("popstate", onPop);
  removeEventListener("keydown", onKey);
});
</script>

<template>
  <div class="pulse-app">
    <a href="#main-content" class="skip-link">Skip to content</a>
    <header class="topbar">
      <div class="topbar-inner">
        <a
          class="brand"
          href="/"
          aria-label="DogePulse home"
          @click.prevent="navigate('/')"
          ><img
            class="brand-icon"
            src="/icon.svg"
            alt=""
            width="35"
            height="35"
          /><span class="brand-name">Doge<span>Pulse</span></span></a
        >
        <nav class="desktop-nav" aria-label="Primary navigation">
          <a
            v-for="item in [
              ['/', 'Pulse'],
              ['/signal', 'Scenario'],
              ['/docs', 'Method'],
              ['/stats', 'Board'],
            ]"
            :key="item[0]"
            :href="item[0]"
            :class="{ active: path === item[0] }"
            :aria-current="path === item[0] ? 'page' : undefined"
            @click.prevent="navigate(item[0])"
            >{{ item[1] }}</a
          >
        </nav>
        <div class="top-actions">
          <a
            href="/signal"
            class="btn btn-coral btn-sm"
            @click.prevent="navigate('/signal')"
            >Test a scenario <ArrowRight :size="15" /></a
          ><button
            ref="menuButton"
            class="menu-toggle"
            :aria-label="menuOpen ? 'Close navigation' : 'Open navigation'"
            :aria-expanded="menuOpen"
            aria-controls="mobile-menu"
            @click="menuOpen = !menuOpen"
          >
            <X v-if="menuOpen" :size="20" /><Menu v-else :size="20" />
          </button>
        </div>
      </div>
      <div class="market-tape" aria-label="Archived quote snapshot">
        <span class="tape-label"
          ><span class="live-dot"></span> SAVED SNAPSHOT</span
        ><span
          v-for="peer in peers.slice(0, 4)"
          :key="peer.symbol"
          class="tape-item"
          ><b>{{ peer.symbol }}</b
          ><strong>{{
            currency(
              peer.price,
              peer.price < 0.001 ? 8 : peer.price < 1 ? 5 : 2,
            )
          }}</strong
          ><em>{{ percent(peer.change) }}</em></span
        ><span class="tape-source">{{ captureLabel }}</span>
      </div>
      <nav
        v-if="menuOpen"
        id="mobile-menu"
        class="mobile-nav"
        aria-label="Mobile navigation"
      >
        <a
          v-for="item in [
            ['/', 'Pulse'],
            ['/signal', 'Scenario'],
            ['/docs', 'Method'],
            ['/stats', 'Board'],
          ]"
          :key="item[0]"
          :href="item[0]"
          @click.prevent="navigate(item[0])"
          >{{ item[1] }}</a
        >
      </nav>
    </header>
    <main id="main-content">
      <template v-if="path === '/'">
        <section class="hero">
          <div class="hero-copy">
            <div class="eyebrow">
              <span class="live-dot"></span> DOGE / A MARKET RESEARCH NOTEBOOK
            </div>
            <h1 ref="heading" tabindex="-1">
              Read the <em>DOGE</em> pulse<br />before you move.
            </h1>
            <p class="hero-lede">
              See the move. Test your assumptions. A focused workspace for
              Dogecoin snapshots, price scenarios and your own reasoning.
            </p>
            <div class="hero-actions">
              <a
                href="/signal"
                class="btn btn-ink"
                @click.prevent="navigate('/signal')"
                >Build a scenario <ArrowRight :size="16" /></a
              ><a
                href="/docs"
                class="btn btn-outline"
                @click.prevent="navigate('/docs#storage')"
                >Explore the method <ChevronRight :size="16"
              /></a>
            </div>
            <div class="hero-foot">
              <span
                ><strong>+12.85%</strong><small>mark / open change</small></span
              ><span
                ><strong>5 coins</strong
                ><small>research comparison</small></span
              ><span
                ><strong>Your call</strong><small>your assumptions</small></span
              >
            </div>
            <p class="snapshot-caption">
              Archived Robinhood quote pages · {{ captureLabel }}. Not live.
            </p>
          </div>
          <div class="hero-visual">
            <div class="orbital" aria-hidden="true">
              <span class="orbit orbit-a"></span
              ><span class="orbit orbit-b"></span><span class="pulse-dot"></span
              ><span class="orbit-label top">DOGE / USD</span
              ><span class="orbit-label right">+12.85%</span
              ><span class="orbit-label bottom">READ → TEST → RECORD</span>
            </div>
            <div class="visual-note">
              <span class="mono">01</span
              ><strong>Attention starts the question.</strong
              ><small>Your research writes the answer.</small>
            </div>
          </div>
        </section>
        <section class="section">
          <div class="section-head">
            <div>
              <span class="eyebrow">THE RESEARCH DESK</span>
              <h2>One coin. Three useful views.</h2>
            </div>
            <a
              class="source-link"
              :href="SNAPSHOT.source"
              target="_blank"
              rel="noreferrer"
              >Check the current source <ExternalLink :size="14"
            /></a>
          </div>
          <div class="market-grid">
            <article class="market-card highlight">
              <div class="card-top">
                <span>01 / OBSERVE</span><TrendingUp :size="17" />
              </div>
              <strong class="big-number">{{ referencePrice }}</strong
              ><span class="change-pill">+12.85% vs open</span>
              <p>
                Saved DOGE mark price. The observed change led our five-coin
                comparison, not an official popularity ranking.
              </p>
              <span class="card-source">{{ captureLabel }}</span>
            </article>
            <article class="market-card">
              <div class="card-top">
                <span>02 / QUESTION</span><BarChart3 :size="17" />
              </div>
              <strong class="mid-number">What if it moves −15%?</strong>
              <div class="scenario-preview">
                <span>1,000 DOGE</span><ArrowRight :size="15" /><strong>{{
                  currency(SNAPSHOT.price * 1000 * 0.85)
                }}</strong>
              </div>
              <p>
                A price move you choose. See the arithmetic before writing the
                story.
              </p>
              <a
                href="/signal"
                class="text-link"
                @click.prevent="navigate('/signal')"
                >Test your assumption <ArrowRight :size="14"
              /></a>
            </article>
            <article class="market-card dark-card">
              <div class="card-top">
                <span>03 / REMEMBER</span><Zap :size="17" />
              </div>
              <strong class="mid-number">Keep the reasoning.</strong>
              <ul>
                <li><span>01</span>Capture the source</li>
                <li><span>02</span>Write your assumption</li>
                <li><span>03</span>Save a local journal</li>
              </ul>
              <a
                class="text-link"
                href="/docs#storage"
                @click.prevent="navigate('/docs')"
                >Read the method <ArrowRight :size="14"
              /></a>
            </article>
          </div>
        </section>
        <section class="section story-section">
          <div>
            <span class="eyebrow">WHY THIS COIN</span>
            <h2>A familiar community.<br />A move worth examining.</h2>
            <p>
              Robinhood names DOGE among its popular cryptocurrencies. In our
              saved comparison, DOGE's mark/open change was stronger than BTC,
              ETH, SOL and SHIB. That makes it a useful subject for research.
            </p>
            <a
              class="source-link"
              href="/stats"
              @click.prevent="navigate('/stats')"
              >See the five-coin comparison <ArrowRight :size="14"
            /></a>
          </div>
          <div class="story-facts">
            <div>
              <strong>Observe</strong
              ><span
                >Public prices with the original source and timestamp.</span
              >
            </div>
            <div>
              <strong>Test</strong
              ><span
                >A user-defined price move, without a prediction score.</span
              >
            </div>
            <div>
              <strong>Record</strong
              ><span>A browser journal you can export or remove.</span>
            </div>
          </div>
        </section>
      </template>

      <template v-else-if="path === '/signal'">
        <section class="page-shell">
          <div class="eyebrow">
            <span class="live-dot"></span> DOGE / SCENARIO SANDBOX
          </div>
          <h1 ref="heading" tabindex="-1">
            Turn a market moment<br /><em>into a question.</em>
          </h1>
          <p class="page-lede">
            What would your scenario be worth if the price moved? Choose your
            assumptions. The math stays visible.
          </p>
          <p v-if="storageNotice" role="alert" class="notice">
            {{ storageNotice }}
          </p>
          <p v-if="feedback" role="status" class="feedback">{{ feedback }}</p>
          <div v-if="step === 'form'" class="signal-layout">
            <form class="panel signal-form" novalidate @submit.prevent="review">
              <div class="panel-head">
                <div>
                  <span class="step">01 / FRAME</span>
                  <h2>Set your assumption.</h2>
                </div>
                <span class="mono">NO WALLET NEEDED</span>
              </div>
              <label for="amount"
                >Scenario amount <span class="unit">DOGE</span></label
              ><input
                id="amount"
                v-model="amount"
                class="field"
                inputmode="decimal"
                autocomplete="off"
                :aria-invalid="Boolean(errors.amount)"
                aria-describedby="amount-error"
                placeholder="1000"
              />
              <p v-if="errors.amount" id="amount-error" class="input-error">
                {{ errors.amount }}
              </p>
              <label for="move"
                >Assumed price change <span class="unit">%</span></label
              >
              <div
                class="segmented"
                role="group"
                aria-label="Example price changes"
              >
                <button
                  v-for="value in [-5, -15, -30, 10]"
                  :key="value"
                  type="button"
                  :class="{ selected: selectedMove === value }"
                  :aria-pressed="selectedMove === value"
                  @click="movePct = String(value)"
                >
                  {{ value > 0 ? "+" : "" }}{{ value }}%
                </button>
              </div>
              <input
                id="move"
                v-model="movePct"
                class="field"
                inputmode="decimal"
                :aria-invalid="Boolean(errors.movePct)"
                aria-describedby="move-hint move-error"
              /><small id="move-hint" class="input-hint"
                >Choose −90% to +100%. This is an assumption, not a
                forecast.</small
              >
              <p v-if="errors.movePct" id="move-error" class="input-error">
                {{ errors.movePct }}
              </p>
              <label for="note"
                >Your reasoning <span class="unit">OPTIONAL</span></label
              ><textarea
                id="note"
                v-model="note"
                class="field note-input"
                maxlength="1000"
                :aria-invalid="Boolean(errors.note)"
                aria-describedby="note-counter note-error"
                placeholder="What would make you reconsider this assumption?"
              ></textarea
              ><small id="note-counter" class="input-hint"
                >{{ remaining }} characters remaining · saved on this
                device</small
              >
              <p v-if="errors.note" id="note-error" class="input-error">
                {{ errors.note }}
              </p>
              <button class="btn btn-ink btn-wide" type="submit">
                Review scenario <ArrowRight :size="16" />
              </button>
              <p class="form-note">
                <ShieldAlert :size="15" /> No order is placed. Values exclude
                fees, spread, tax and execution.
              </p>
            </form>
            <aside class="signal-aside">
              <div class="aside-chart">
                <span class="eyebrow">YOUR STARTING POINT</span
                ><strong class="baseline-price">{{ currency(activeSnapshot.price, 5) }}</strong
                ><span class="mono">USD / DOGE</span>
                <div class="side-divider"></div>
                <p>
                  This archived quote is the starting point. Editing a saved
                  journal preserves its original price and source.
                </p>
                <a
                  class="source-link"
                  :href="activeSnapshot.source"
                  target="_blank"
                  rel="noreferrer"
                  >Robinhood DOGE quote <ExternalLink :size="14"
                /></a>
                <p class="snapshot-caption">Source updated {{ activeSnapshot.observedAt }} · not live</p>
              </div>
              <p class="aside-copy">
                Separate the data you can see from the story you want to tell.
              </p>
            </aside>
          </div>
          <div v-else-if="step === 'review'" class="review-layout">
            <div class="panel review-card">
              <div class="panel-head">
                <div>
                  <span class="step">02 / REVIEW</span>
                  <h2>If the price moves…</h2>
                </div>
                <span class="score-badge">YOUR ASSUMPTION</span>
              </div>
              <div class="score-row">
                <div class="scenario-dial">
                  <strong>{{ percent(record.movePct) }}</strong
                  ><small>hypothetical move</small>
                </div>
                <div>
                  <span class="eyebrow">SCENARIO VALUE</span>
                  <h3>{{ currency(result.scenarioValue) }}</h3>
                  <p>
                    {{ quantity(record.amount) }} DOGE ·
                    {{ currency(result.scenarioPrice, 8) }} each
                  </p>
                </div>
              </div>
              <div class="review-rows">
                <div>
                  <span>Value at saved mark</span
                  ><strong>{{ currency(result.baselineValue) }}</strong>
                </div>
                <div>
                  <span>Hypothetical difference</span
                  ><strong
                    >{{ result.deltaUsd > 0 ? "+" : ""
                    }}{{ currency(result.deltaUsd) }}</strong
                  >
                </div>
                <div>
                  <span>Price used</span
                  ><strong
                    >{{ currency(record.snapshot.price, 9) }} / DOGE</strong
                  >
                </div>
              </div>
              <p class="saved-note" v-if="record.note">{{ record.note }}</p>
              <div class="review-actions">
                <button class="btn btn-coral" @click="save">
                  Save local journal <ArrowRight :size="16" /></button
                ><button class="btn btn-outline" @click="edit">
                  Edit assumptions
                </button>
              </div>
              <p class="form-note">
                <ShieldAlert :size="15" /> This is arithmetic using your assumed
                move. It does not estimate likelihood or returns.
              </p>
            </div>
            <aside class="panel context-card">
              <span class="eyebrow">THE MATH, IN THE OPEN</span>
              <p>
                <b>Starting value</b><br />DOGE amount × recorded mark price
              </p>
              <p>
                <b>Scenario price</b><br />Recorded mark × (1 + assumed change ÷
                100)
              </p>
              <p><b>Scenario value</b><br />DOGE amount × scenario price</p>
              <p>
                Source updated:
                {{ new Date(record.snapshot.observedAt).toISOString() }}
              </p>
            </aside>
          </div>
          <div v-else class="tracking-layout">
            <div class="panel tracking-card">
              <div class="panel-head">
                <div>
                  <span class="step">03 / JOURNAL</span>
                  <h2>
                    {{
                      record.stage === 3
                        ? "Review complete."
                        : "Keep the reasoning."
                    }}
                  </h2>
                </div>
                <span class="mono">LOCAL NOTE</span>
              </div>
              <p class="page-lede">
                Review each checkpoint. You can go back, edit your assumption or
                download the full record.
              </p>
              <ol class="stations">
                <li
                  v-for="(stage, i) in stages"
                  :key="stage[0]"
                  class="station"
                  :class="{
                    done: i < record.stage,
                    current: i === record.stage,
                  }"
                  :aria-current="i === record.stage ? 'step' : undefined"
                >
                  <span class="station-dot"
                    ><Check v-if="i < record.stage" :size="12" /><span v-else>{{
                      i + 1
                    }}</span></span
                  >
                  <div>
                    <strong>{{ stage[0] }}</strong
                    ><small>{{ stage[1] }}</small>
                  </div>
                </li>
              </ol>
              <div class="review-actions">
                <button
                  class="btn btn-coral"
                  :disabled="record.stage === 3"
                  @click="changeStage(1)"
                >
                  {{
                    record.stage === 3 ? "All checks complete" : "Mark reviewed"
                  }}
                  <Check v-if="record.stage === 3" :size="16" /><ArrowRight
                    v-else
                    :size="16"
                  /></button
                ><button
                  class="btn btn-outline"
                  :disabled="record.stage === 0"
                  @click="changeStage(-1)"
                >
                  Previous check</button
                ><button class="btn btn-outline" @click="downloadJournal">
                  <ExternalLink :size="15" /> Download JSON
                </button>
              </div>
              <div class="journal-actions">
                <button @click="edit">Edit this note</button
                ><button @click="newScenario">New scenario</button
                ><button @click="removeJournal">Remove saved journal</button>
              </div>
              <p class="form-note">
                One saved journal per browser. Saving another replaces it;
                download a copy to keep more.
              </p>
            </div>
            <aside class="panel journal-side">
              <span class="eyebrow">YOUR RECORDED ASSUMPTION</span
              ><strong>{{ quantity(record.amount) }} DOGE</strong
              ><span>{{ percent(record.movePct) }} price move</span>
              <div class="side-divider"></div>
              <p>
                Hypothetical value
                <strong>{{ currency(result.scenarioValue) }}</strong>
              </p>
              <p v-if="record.note" class="saved-note">{{ record.note }}</p>
              <p class="snapshot-caption">
                Price source updated
                {{ new Date(record.snapshot.observedAt).toISOString() }}
              </p>
            </aside>
          </div>
        </section>
      </template>

      <template v-else-if="path === '/docs'">
        <section class="page-shell docs-page">
          <div class="eyebrow">METHOD / SOURCES / LIMITS</div>
          <h1 ref="heading" tabindex="-1">
            A notebook you can<br /><em>audit yourself.</em>
          </h1>
          <p class="page-lede">
            Visible inputs, simple calculations and room for your own reasoning.
          </p>
          <div class="docs-grid">
            <aside class="docs-index panel">
              <span class="eyebrow">ON THIS PAGE</span
              ><a v-for="item in sections" :key="item.id" :href="'#' + item.id"
                >{{ item.title }} <ChevronRight :size="14"
              /></a>
            </aside>
            <article class="docs-content">
              <section id="overview">
                <span class="eyebrow">01 / OVERVIEW</span>
                <h2>What is DogePulse?</h2>
                <p>
                  An independent DOGE research workspace. Read a recorded market
                  snapshot, test a hypothetical price move and save your
                  reasoning in a local journal.
                </p>
              </section>
              <section id="sources">
                <span class="eyebrow">02 / DATA SOURCE</span>
                <h2>Why DOGE?</h2>
                <p>
                  Robinhood's public crypto page names DOGE among popular coins.
                  Our {{ captureLabel }} capture compared DOGE, SHIB, SOL, BTC
                  and ETH. DOGE had the largest mark/open change in that group.
                </p>
                <p>
                  The displayed percentage is (mark price ÷ open price − 1) ×
                  100. It is a quote comparison, not an official popularity
                  ranking. Quote timestamps and saved inputs remain fixed; this
                  website has no live price feed.
                </p>
                <a
                  class="source-link"
                  :href="SNAPSHOT.source"
                  target="_blank"
                  rel="noreferrer"
                  >Inspect the current DOGE page <ExternalLink :size="14"
                /></a>
                <p>
                  <a href="/market-snapshot.json" class="source-link" download
                    >Download this site's recorded inputs
                    <ExternalLink :size="14"
                  /></a>
                </p>
              </section>
              <section id="scenario">
                <span class="eyebrow">03 / SCENARIO MATH</span>
                <h2>Assumptions, with the math shown.</h2>
                <p>
                  The scenario price equals the recorded DOGE mark multiplied by
                  (1 + your assumed percentage ÷ 100). Multiplying by the DOGE
                  amount gives the hypothetical value. The difference compares
                  that value with the recorded starting value.
                </p>
                <p>
                  Amounts accept up to 8 decimal places; assumed changes accept
                  2. Displayed dollars round to cents, while the export retains
                  the calculation values. The model excludes spread, fees, tax
                  and execution. There are no price forecasts or sentiment
                  scores.
                </p>
              </section>
              <section id="storage">
                <span class="eyebrow">04 / LOCAL JOURNAL</span>
                <h2>Your note stays with you.</h2>
                <p>
                  Your browser stores one record: amount, assumed change, note,
                  source price, timestamps and review progress. Reloading
                  restores the complete record. Download JSON to keep it
                  elsewhere, or remove the saved journal from the scenario page.
                </p>
                <p>
                  When browser storage is blocked, the scenario remains usable
                  and can still be downloaded. No wallet, private key or account
                  is required.
                </p>
              </section>
              <section id="limits">
                <span class="eyebrow">05 / LIMITS</span>
                <h2>Attention is not certainty.</h2>
                <p>
                  DOGE is volatile and has continuing issuance. A short-term
                  rise can reverse. Scenario values are not investment advice or
                  projected returns. DogePulse has no affiliation or integration
                  with Robinhood or the Dogecoin project, and it does not issue
                  a project token.
                </p>
              </section>
            </article>
          </div>
        </section>
      </template>

      <template v-else-if="path === '/whitepaper'">
        <section class="page-shell paper-page">
          <div class="paper-card">
            <div class="paper-top">
              <span class="eyebrow">DOGEPULSE / FIELD NOTE 01</span
              ><img src="/icon.svg" alt="" width="48" height="48" />
            </div>
            <h1 ref="heading" tabindex="-1">
              When a meme coin<br /><em>moves the room.</em>
            </h1>
            <p class="paper-intro">
              A framework for reading DOGE momentum without confusing attention
              with certainty.
            </p>
            <div class="paper-meta">
              <span>September 2026</span
              ><span>Independent research preview</span>
            </div>
          </div>
          <article class="paper-body">
            <span class="eyebrow">THE THESIS</span>
            <h2>Make the moment legible.</h2>
            <p>
              DOGE's community and market presence make it a familiar subject.
              Our Robinhood quote comparison makes it timely: the saved DOGE
              mark/open change was +12.85%, the largest in a five-coin group.
              That observation starts a question. It cannot answer what the
              price will do next.
            </p>
            <div class="paper-grid">
              <div>
                <span class="eyebrow">01 / OBSERVE</span>
                <h3>Start with the source.</h3>
                <p>
                  Record the price and timestamp before writing the narrative.
                </p>
              </div>
              <div>
                <span class="eyebrow">02 / QUESTION</span>
                <h3>Change an assumption.</h3>
                <p>
                  Compare different hypothetical price moves without a
                  prediction.
                </p>
              </div>
              <div>
                <span class="eyebrow">03 / JOURNAL</span>
                <h3>Keep the reasoning.</h3>
                <p>A dated note lets you revisit what you believed, and why.</p>
              </div>
            </div>
            <a
              class="btn btn-ink"
              href="/signal"
              @click.prevent="navigate('/signal')"
              >Write your first scenario <ArrowRight :size="16"
            /></a>
          </article>
        </section>
      </template>

      <template v-else-if="path === '/stats'">
        <section class="page-shell board-page">
          <div class="eyebrow">BOARD / ARCHIVED QUOTES</div>
          <h1 ref="heading" tabindex="-1">
            The DOGE moment,<br /><em>in context.</em>
          </h1>
          <p class="page-lede">
            Five public Robinhood asset pages, captured within seconds of each
            other. {{ captureLabel }} · not live.
          </p>
          <div class="board-grid">
            <article class="board-card coral">
              <span>DOGE MARK / OPEN</span><strong>+12.85%</strong
              ><small>calculated change</small>
            </article>
            <article class="board-card">
              <span>RECORDED MARK</span><strong>{{ referencePrice }}</strong
              ><small>USD per DOGE</small>
            </article>
            <article class="board-card">
              <span>COINS COMPARED</span><strong>5</strong
              ><small>selected major assets</small>
            </article>
            <article class="board-card blue">
              <span>SOURCE UPDATED</span><strong>02:27</strong
              ><small>UTC · 22 Sep 2026</small>
            </article>
          </div>
          <div class="board-lower">
            <article class="panel comparison">
              <div class="panel-head">
                <h2>The five-coin comparison</h2>
                <span class="mono">MARK / OPEN CHANGE</span>
              </div>
              <div
                v-for="peer in peers"
                :key="peer.symbol"
                class="comparison-row"
              >
                <a
                  :href="
                    'https://robinhood.com/us/en/crypto/' + peer.symbol + '/'
                  "
                  target="_blank"
                  rel="noreferrer"
                  >{{ peer.symbol }}</a
                >
                <div class="compare-bar" aria-hidden="true">
                  <i :style="{ width: (peer.change / 12.85) * 100 + '%' }"></i>
                </div>
                <strong>{{ percent(peer.change) }}</strong>
              </div>
              <p class="table-note">
                Computed from each saved mark and open price. These figures do
                not measure trading volume, users or popularity.
              </p>
            </article>
            <article class="panel source-card">
              <span class="eyebrow">READ THE EVIDENCE</span>
              <h2>A research choice.<br />A dated observation.</h2>
              <p>
                Combined with Robinhood's popular-coin copy, this snapshot
                supports a DOGE focus. It does not establish that DOGE is the
                platform's most traded or most held asset.
              </p>
              <a class="source-link" href="/market-snapshot.json" download
                >Download recorded inputs <ExternalLink :size="14"
              /></a>
            </article>
          </div>
        </section>
      </template>
      <section v-else class="page-shell">
        <span class="eyebrow">404 / PAGE NOT FOUND</span>
        <h1 ref="heading" tabindex="-1">Back to the pulse.</h1>
        <p class="page-lede">This page is not part of the notebook.</p>
        <a href="/" class="btn btn-ink" @click.prevent="navigate('/')"
          >Return home <ArrowRight :size="16"
        /></a>
      </section>
    </main>
    <footer class="footer">
      <div class="footer-main">
        <a
          href="/"
          class="brand"
          aria-label="DogePulse home"
          @click.prevent="navigate('/')"
          ><img src="/icon.svg" alt="" width="35" height="35" /><span
            class="brand-name"
            >Doge<span>Pulse</span></span
          ></a
        >
        <p>{{ brand.supportingLine }}</p>
        <nav aria-label="Footer">
          <a href="/docs" @click.prevent="navigate('/docs')">Method</a
          ><a href="/whitepaper" @click.prevent="navigate('/whitepaper')"
            >Field note</a
          ><a href="/stats" @click.prevent="navigate('/stats')">Board</a>
        </nav>
      </div>
      <div class="footer-bottom">
        <span>INDEPENDENT RESEARCH PREVIEW · NO TRADES</span
        ><span>Archived data. Your assumptions.</span>
      </div>
    </footer>
  </div>
</template>
