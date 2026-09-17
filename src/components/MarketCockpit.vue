<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { brand, storageKeys, migrateBrandStorage } from "../brand.js";
import {
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  Bookmark,
  BookOpen,
  Check,
  ChevronDown,
  Download,
  ExternalLink,
  FileText,
  RotateCcw,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Trash2,
  Undo2,
  X,
} from "lucide-vue-next";

const assets = [
  {
    symbol: "AAPL",
    name: "Apple",
    price: 234.42,
    change: 1.84,
    signal: 78,
    status: "Build",
    thesis:
      "Services resilience and improving device mix support the base case. Valuation expansion is the key constraint; size only inside the defined risk band.",
    counter:
      "Multiple compression could outweigh stronger services revenue. Revisit the thesis if services growth slows or device mix deteriorates.",
  },
  {
    symbol: "NVDA",
    name: "NVIDIA",
    price: 188.61,
    change: 3.12,
    signal: 72,
    status: "Watch",
    thesis:
      "Demand signals remain constructive, while concentration and elevated expectations increase downside sensitivity around guidance.",
    counter:
      "Customer concentration and ambitious growth expectations leave little room for a guidance miss.",
  },
  {
    symbol: "TSLA",
    name: "Tesla",
    price: 354.18,
    change: -1.26,
    signal: 43,
    status: "Caution",
    thesis:
      "Momentum is mixed against a high-volatility backdrop. Delivery evidence and margin trend do not yet clear the action threshold.",
    counter:
      "Delivery weakness or further margin compression could amplify an already volatile setup.",
  },
  {
    symbol: "AMZN",
    name: "Amazon",
    price: 251.05,
    change: 0.73,
    signal: 66,
    status: "Watch",
    thesis:
      "Cloud acceleration supports the thesis, with retail margins and regulatory exposure defining the primary counter-case.",
    counter:
      "Slower cloud growth, weaker retail margins, or regulatory action would challenge the base case.",
  },
];
const scenarios = [
  {
    id: "bear",
    label: "Bear",
    move: -12,
    drawdown: 24,
    description: "Expectations reset and valuation contracts.",
  },
  {
    id: "base",
    label: "Base",
    move: 6,
    drawdown: 12,
    description: "The thesis develops without a major rerating.",
  },
  {
    id: "bull",
    label: "Bull",
    move: 18,
    drawdown: 17,
    description: "Growth surprises; valuation sensitivity remains.",
  },
];
const tabs = ["Brief", "Sources", "Scenario"];
const active = ref("AAPL");
const activeTab = ref("Brief");
const activeScenario = ref("base");
const query = ref("");
const weight = ref(10);
const note = ref("");
const evidenceOpen = ref(false);
const journalOpen = ref(false);
const journal = ref([]);
const journalQuery = ref("");
const journalAsset = ref("all");
const revisitedEntry = ref(null);
const previousDraft = ref(null);
const journalError = ref("");
const notice = ref("");
const lastDeleted = ref(null);
const journalHeading = ref(null);
const journalToggle = ref(null);
const searchInput = ref(null);
const journalReturnTarget = ref(null);
const drafts = new Map();
const journalKey = storageKeys.journal;
const current = computed(() =>
  assets.find((asset) => asset.symbol === active.value),
);
const scenario = computed(() =>
  scenarios.find((item) => item.id === activeScenario.value),
);
const filteredAssets = computed(() => {
  const term = query.value.trim().toLowerCase();
  return assets.filter((asset) =>
    `${asset.symbol} ${asset.name}`.toLowerCase().includes(term),
  );
});
const portfolioImpact = computed(() =>
  ((Number(weight.value) * scenario.value.drawdown) / 100).toFixed(2),
);
const projectedPrice = computed(() =>
  (current.value.price * (1 + scenario.value.move / 100)).toFixed(2),
);
const scenarioPrices = computed(() =>
  scenarios.map((item) => ({
    ...item,
    price: (current.value.price * (1 + item.move / 100)).toFixed(2),
  })),
);
const filteredJournal = computed(() => {
  const term = journalQuery.value.trim().toLowerCase();
  return journal.value.filter(
    (entry) =>
      (journalAsset.value === "all" || entry.symbol === journalAsset.value) &&
      `${entry.symbol} ${entry.note} ${entry.thesis} ${entry.scenario}`
        .toLowerCase()
        .includes(term),
  );
});
const isSaved = computed(() =>
  journal.value.some(
    (entry) =>
      entry.symbol === active.value &&
      entry.scenario === activeScenario.value &&
      entry.weight === Number(weight.value) &&
      entry.note === note.value.trim(),
  ),
);

function selectAsset(symbol) {
  if (symbol === active.value) return;
  drafts.set(active.value, {
    note: note.value,
    scenario: activeScenario.value,
    weight: weight.value,
    revisitedEntry: revisitedEntry.value,
    previousDraft: previousDraft.value,
  });
  active.value = symbol;
  const draft = drafts.get(symbol);
  note.value = draft?.note ?? "";
  activeScenario.value = draft?.scenario ?? "base";
  weight.value = draft?.weight ?? 10;
  revisitedEntry.value = draft?.revisitedEntry ?? null;
  previousDraft.value = draft?.previousDraft ?? null;
  notice.value = "";
  evidenceOpen.value = false;
}
async function goToTab(tab) {
  activeTab.value = tab;
  await nextTick();
  document.getElementById(`research-tab-${tab.toLowerCase()}`)?.focus();
}
async function focusDecisionNote() {
  await nextTick();
  document.getElementById("thesis-note")?.focus();
}
async function clearSearch() {
  query.value = "";
  await nextTick();
  searchInput.value?.focus();
}
function navigateTabs(event) {
  let index = tabs.indexOf(activeTab.value);
  if (event.key === "ArrowRight") index = (index + 1) % tabs.length;
  else if (event.key === "ArrowLeft")
    index = (index + tabs.length - 1) % tabs.length;
  else if (event.key === "Home") index = 0;
  else if (event.key === "End") index = tabs.length - 1;
  else return;
  event.preventDefault();
  activeTab.value = tabs[index];
  nextTick(() =>
    document
      .getElementById(`research-tab-${tabs[index].toLowerCase()}`)
      ?.focus(),
  );
}
function loadJournal() {
  try {
    const migration = migrateBrandStorage();
    if (migration?.journalError) {
      journalError.value = migration.journalError;
      return;
    }
    const saved = JSON.parse(localStorage.getItem(journalKey) || "[]");
    if (
      !Array.isArray(saved) ||
      !saved.every(
        (entry) =>
          entry &&
          typeof entry.id === "string" &&
          assets.some((asset) => asset.symbol === entry.symbol) &&
          scenarios.some((item) => item.id === entry.scenario) &&
          Number.isFinite(entry.weight) &&
          entry.weight >= 1 &&
          entry.weight <= 50 &&
          Number.isFinite(entry.savedAt) &&
          !Number.isNaN(new Date(entry.savedAt).getTime()) &&
          typeof entry.thesis === "string" &&
          typeof entry.note === "string",
      )
    )
      throw new Error("Invalid journal data");
    journal.value = saved;
    journalError.value = "";
  } catch {
    journalError.value =
      "Your saved journal could not be read. Allow local storage and retry. Existing data has not been changed.";
  }
}
async function revisitDecision(entry) {
  selectAsset(entry.symbol);
  previousDraft.value = {
    note: note.value,
    scenario: activeScenario.value,
    weight: weight.value,
    revisitedEntry: revisitedEntry.value,
    previousDraft: previousDraft.value,
  };
  query.value = "";
  note.value = entry.note;
  activeScenario.value = entry.scenario;
  weight.value = entry.weight;
  revisitedEntry.value = { id: entry.id, savedAt: entry.savedAt };
  activeTab.value = "Brief";
  journalOpen.value = false;
  notice.value = `${entry.symbol} decision loaded for review. The saved snapshot stays unchanged.`;
  await nextTick();
  document.getElementById("selected-asset-title")?.focus();
}
async function restorePreviousDraft() {
  if (!previousDraft.value) return;
  const draft = previousDraft.value;
  note.value = draft.note;
  activeScenario.value = draft.scenario;
  weight.value = draft.weight;
  revisitedEntry.value = draft.revisitedEntry;
  previousDraft.value = draft.previousDraft;
  notice.value = `${active.value} previous draft restored. Saved snapshots are unchanged.`;
  await nextTick();
  document.getElementById("thesis-note")?.focus();
}
async function clearJournalFilters() {
  journalQuery.value = "";
  journalAsset.value = "all";
  await nextTick();
  document.getElementById("journal-search")?.focus();
}
function persistJournal(entries) {
  try {
    localStorage.setItem(journalKey, JSON.stringify(entries));
    journal.value = entries;
    journalError.value = "";
    return true;
  } catch {
    journalError.value =
      "This browser could not save the change. Check available storage or privacy settings, then retry.";
    return false;
  }
}
function saveThesis() {
  if (isSaved.value || journalError.value) return;
  const entry = {
    id: crypto.randomUUID(),
    savedAt: Date.now(),
    symbol: active.value,
    price: current.value.price,
    thesis: current.value.thesis,
    counter: current.value.counter,
    scenario: activeScenario.value,
    move: scenario.value.move,
    assumedDrawdown: scenario.value.drawdown,
    weight: Number(weight.value),
    portfolioStress: Number(portfolioImpact.value),
    note: note.value.trim(),
    dataType: "illustrative-preview",
    modelVersion: "preview-1",
  };
  if (persistJournal([entry, ...journal.value]))
    notice.value = `${active.value} thesis saved on this device.`;
}
async function openJournal() {
  if (!journalOpen.value && document.activeElement instanceof HTMLElement)
    journalReturnTarget.value = document.activeElement;
  journalOpen.value = true;
  await nextTick();
  journalHeading.value?.focus();
}
async function openSavedJournal() {
  journalQuery.value = "";
  journalAsset.value = active.value;
  return openJournal();
}
async function toggleJournal() {
  if (!journalOpen.value) return openJournal();
  journalOpen.value = false;
  await nextTick();
  const returnTarget = journalReturnTarget.value;
  if (returnTarget?.isConnected && !returnTarget.disabled) returnTarget.focus();
  else if (returnTarget?.id && document.getElementById(returnTarget.id))
    document.getElementById(returnTarget.id)?.focus();
  else journalToggle.value?.focus();
}
defineExpose({ openJournal, goToTab, selectAsset });
function deleteEntry(entry) {
  if (journalError.value) return;
  const index = journal.value.findIndex((item) => item.id === entry.id);
  if (persistJournal(journal.value.filter((item) => item.id !== entry.id))) {
    lastDeleted.value = { entry, index };
    notice.value = `${entry.symbol} entry removed. You can undo this deletion.`;
    nextTick(() =>
      document.getElementById("journal-undo")?.focus({ preventScroll: true }),
    );
  }
}
function undoDelete() {
  if (!lastDeleted.value || journalError.value) return;
  const restored = [...journal.value];
  restored.splice(
    Math.min(lastDeleted.value.index, restored.length),
    0,
    lastDeleted.value.entry,
  );
  if (persistJournal(restored)) {
    lastDeleted.value = null;
    notice.value = "Journal entry restored.";
    nextTick(() => journalHeading.value?.focus({ preventScroll: true }));
  }
}
function exportJournal() {
  const file = new Blob(
    [
      JSON.stringify(
        {
          brand: brand.name,
          exportedAt: new Date().toISOString(),
          storage: "local, unencrypted",
          entries: journal.value,
        },
        null,
        2,
      ),
    ],
    { type: "application/json" },
  );
  const url = URL.createObjectURL(file);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${brand.slug}-journal-${new Date().toISOString().slice(0, 10)}.json`;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  notice.value = "Journal exported as a JSON file.";
}
function formatDate(timestamp) {
  return new Date(timestamp).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
function syncJournal(event) {
  if (event.key === journalKey || event.key === null) {
    loadJournal();
    lastDeleted.value = null;
  }
}
onMounted(() => {
  loadJournal();
  window.addEventListener("storage", syncJournal);
});
onBeforeUnmount(() => window.removeEventListener("storage", syncJournal));
</script>

<template>
  <div
    class="research-desk"
    role="region"
    :aria-label="`${brand.name} interactive research preview`"
  >
    <header class="desk-header">
      <div class="desk-title">
        <span class="folio-mark" aria-hidden="true">R.</span>
        <div>
          <small>{{ brand.name }} / RESEARCH FOLIO</small>
          <h3>A place to form your view.</h3>
        </div>
      </div>
      <button
        ref="journalToggle"
        class="quiet-button journal-toggle"
        :aria-expanded="journalOpen"
        aria-controls="local-journal"
        @click="toggleJournal"
      >
        <BookOpen :size="17" /> My journal
        <span class="count">{{ journal.length }}</span>
      </button>
    </header>

    <section class="asset-index" aria-label="Asset watchlist">
      <div class="index-label">
        <span class="small-heading">01 / CHOOSE A SUBJECT</span
        ><span class="sample-note">Illustrative prices · USD</span>
      </div>
      <div class="index-controls">
        <div class="asset-search">
          <Search :size="17" aria-hidden="true" />
          <input
            ref="searchInput"
            v-model="query"
            type="search"
            aria-label="Search assets"
            placeholder="Find an asset"
          />
          <button
            v-if="query"
            aria-label="Clear asset search"
            @click="clearSearch"
          >
            <X :size="16" />
          </button>
        </div>
        <div class="asset-list">
          <button
            v-for="asset in filteredAssets"
            :key="asset.symbol"
            class="asset-row"
            :class="{ selected: active === asset.symbol }"
            :aria-pressed="active === asset.symbol"
            @click="selectAsset(asset.symbol)"
          >
            <span class="asset-name"
              ><strong>{{ asset.symbol }}</strong
              ><small>{{ asset.name }}</small></span
            >
            <span class="asset-quote"
              ><strong>{{ asset.price.toFixed(2) }}</strong
              ><small :class="asset.change > 0 ? 'positive' : 'negative'"
                ><ArrowUpRight
                  v-if="asset.change > 0"
                  :size="12"
                /><ArrowDownRight v-else :size="12" />{{
                  Math.abs(asset.change).toFixed(2)
                }}%</small
              ></span
            >
          </button>
          <div v-if="!filteredAssets.length" class="search-empty" role="status">
            <p>No matching assets.</p>
            <button class="inline-button" @click="clearSearch">
              Clear search
            </button>
          </div>
        </div>
      </div>
    </section>

    <section class="research-main" aria-label="Selected asset research">
      <div class="asset-heading">
        <div class="asset-title-group">
          <p class="small-heading">RESEARCH SUBJECT / {{ current.name }}</p>
          <h3 id="selected-asset-title" tabindex="-1">
            {{ current.symbol
            }}<span :class="['signal-status', current.status.toLowerCase()]">{{
              current.status
            }}</span>
          </h3>
        </div>
        <div class="asset-title-note">
          <span class="small-heading">THE QUESTION TO KEEP ASKING</span>
          <p>What would change<br />your mind?</p>
        </div>
        <div class="main-price">
          <span class="small-heading">SAMPLE PRICE</span
          ><strong>${{ current.price.toFixed(2) }}</strong
          ><small :class="current.change > 0 ? 'positive' : 'negative'"
            >{{ current.change > 0 ? "+" : "" }}{{ current.change.toFixed(2) }}%
            <span>illustrative move</span></small
          >
        </div>
      </div>
      <div v-if="revisitedEntry" class="revisit-banner" role="status">
        <RotateCcw :size="18" />
        <p>
          Revisiting {{ formatDate(revisitedEntry.savedAt)
          }}<span
            >Change an assumption to save a new snapshot. Your original is
            unchanged.</span
          >
        </p>
        <button
          v-if="previousDraft"
          class="inline-button"
          @click="restorePreviousDraft"
        >
          Restore previous draft
        </button>
      </div>
      <div
        class="research-tabs"
        role="tablist"
        aria-label="Research sections"
        @keydown="navigateTabs"
      >
        <button
          v-for="(tab, index) in tabs"
          :id="`research-tab-${tab.toLowerCase()}`"
          :key="tab"
          role="tab"
          :aria-label="tab"
          :aria-selected="activeTab === tab"
          :aria-controls="`research-panel-${tab.toLowerCase()}`"
          :tabindex="activeTab === tab ? 0 : -1"
          :class="{ selected: activeTab === tab }"
          @click="activeTab = tab"
        >
          <span class="tab-number" aria-hidden="true">0{{ index + 1 }}</span
          ><span class="tab-title"
            >{{ tab
            }}<small>{{
              [
                "Read the working thesis",
                "Inspect the evidence",
                "Explore the assumptions",
              ][index]
            }}</small></span
          ><ArrowRight :size="17" aria-hidden="true" />
        </button>
      </div>

      <div
        v-if="activeTab === 'Brief'"
        id="research-panel-brief"
        class="research-panel brief-panel"
        role="tabpanel"
        aria-labelledby="research-tab-brief"
        tabindex="0"
      >
        <div class="thesis-column">
          <p class="brief-label">
            <FileText :size="16" /><span>THE WORKING THESIS</span
            ><span class="sample-tag">SAMPLE</span>
          </p>
          <p class="thesis-copy">{{ current.thesis }}</p>
          <button class="next-step" @click="goToTab('Sources')">
            Next: inspect sources <ArrowRight :size="17" />
          </button>
        </div>
        <div class="context-column">
          <div class="counter-case">
            <span class="small-heading">A REASON TO RECONSIDER</span>
            <h4>What could change the view.</h4>
            <p>{{ current.counter }}</p>
          </div>
          <div class="evidence-summary">
            <div>
              <strong>{{ current.signal }}<small>/100</small></strong
              ><span>Illustrative signal score</span>
            </div>
            <div class="signal-track" aria-hidden="true">
              <i :style="{ width: `${current.signal}%` }"></i>
            </div>
          </div>
          <button
            class="evidence-button"
            :aria-expanded="evidenceOpen"
            aria-controls="evidence-detail"
            @click="evidenceOpen = !evidenceOpen"
          >
            <span>Inspect the evidence context</span
            ><ChevronDown :size="16" :class="{ rotated: evidenceOpen }" />
          </button>
          <div v-if="evidenceOpen" id="evidence-detail" class="evidence-detail">
            <strong>Know what this preview contains.</strong>
            <p>
              The prices, scores, and thesis above are fixed demonstration data.
              No issuer filings, market feed, or model output are connected to
              this workspace.
            </p>
            <p>
              Use Sources to inspect the available network references. They do
              not substantiate the investment thesis.
            </p>
            <button class="inline-button" @click="goToTab('Sources')">
              Open source context <ArrowUpRight :size="14" />
            </button>
          </div>
        </div>
      </div>

      <div
        v-if="activeTab === 'Sources'"
        id="research-panel-sources"
        class="research-panel source-panel"
        role="tabpanel"
        aria-labelledby="research-tab-sources"
        tabindex="0"
      >
        <div class="section-introduction">
          <p class="brief-label">
            <BookOpen :size="16" /><span>SOURCE CONTEXT</span
            ><span class="sample-tag">PREVIEW</span>
          </p>
          <h4>A thesis deserves<br />a paper trail.</h4>
          <p class="panel-copy">
            This demo contains no live research sources. The working thesis is
            sample copy; it has not been verified against issuer disclosures.
          </p>
          <button class="next-step" @click="goToTab('Scenario')">
            Next: test a scenario <ArrowRight :size="17" />
          </button>
        </div>
        <div class="source-ledger">
          <div class="source-record">
            <span class="source-number">01</span>
            <div>
              <strong>{{ brand.name }} product sample</strong>
              <p>
                Fixed prices, illustrative signal scores, and scenario
                assumptions. No collection timestamp.
              </p>
              <small>DATA TYPE / DEMONSTRATION</small>
            </div>
          </div>
          <a
            class="source-record source-link"
            href="https://docs.robinhood.com/chain/"
            target="_blank"
            rel="noreferrer"
            ><span class="source-number">02</span>
            <div>
              <strong
                >Robinhood Chain documentation <ExternalLink :size="14"
              /></strong>
              <p>Network reference for the wallet connection.</p>
              <small>REFERENCE / NETWORK ONLY</small>
            </div></a
          >
          <a
            class="source-record source-link"
            href="https://robinhoodchain.blockscout.com"
            target="_blank"
            rel="noreferrer"
            ><span class="source-number">03</span>
            <div>
              <strong
                >Robinhood Chain explorer <ExternalLink :size="14"
              /></strong>
              <p>Inspect onchain activity independently.</p>
              <small>REFERENCE / NETWORK ONLY</small>
            </div></a
          >
        </div>
      </div>

      <div
        v-if="activeTab === 'Scenario'"
        id="research-panel-scenario"
        class="research-panel scenario-panel"
        role="tabpanel"
        aria-labelledby="research-tab-scenario"
        tabindex="0"
      >
        <div class="scenario-introduction">
          <div>
            <p class="brief-label">
              <SlidersHorizontal :size="16" /><span>SCENARIO STUDY</span
              ><span class="sample-tag">30 DAYS</span>
            </p>
            <h4>One thesis. Three possible paths.</h4>
          </div>
          <p class="panel-copy">
            Explore a hypothetical price move. Each case also carries a separate
            stress drawdown for sizing.
          </p>
        </div>
        <div
          class="scenario-choices"
          role="group"
          aria-label="Market scenarios"
        >
          <button
            v-for="item in scenarios"
            :key="item.id"
            :class="[item.id, { selected: activeScenario === item.id }]"
            :aria-pressed="activeScenario === item.id"
            @click="activeScenario = item.id"
          >
            <span
              >{{ item.label }} case
              <Check v-if="activeScenario === item.id" :size="16" /></span
            ><strong>{{ item.move > 0 ? "+" : "" }}{{ item.move }}%</strong
            ><small>{{ item.description }}</small
            ><span class="case-price"
              >${{ (current.price * (1 + item.move / 100)).toFixed(2) }}
              <ArrowUpRight :size="16"
            /></span>
          </button>
        </div>
        <div class="scenario-comparison">
          <div class="scenario-result" aria-live="polite">
            <span class="small-heading"
              >SELECTED / {{ scenario.label.toUpperCase() }} CASE</span
            ><span>Hypothetical {{ current.symbol }} price</span
            ><strong>${{ projectedPrice }}</strong>
            <p>{{ scenario.description }}</p>
          </div>
          <figure
            class="scenario-chart"
            aria-labelledby="scenario-chart-caption"
          >
            <figcaption id="scenario-chart-caption">
              <span>ASSUMED OUTCOMES</span><span>30-day cases · USD</span>
            </figcaption>
            <div
              v-for="item in scenarioPrices"
              :key="item.id"
              class="scenario-chart-row"
              :class="{ selected: item.id === activeScenario }"
            >
              <span>{{ item.label }}</span>
              <div class="scenario-bar-track" aria-hidden="true">
                <i
                  :class="{ downside: item.move < 0 }"
                  :style="{
                    left: `${Math.min(40, 40 + item.move * 2)}%`,
                    width: `${Math.abs(item.move) * 2}%`,
                  }"
                ></i>
              </div>
              <strong
                >${{ item.price
                }}<small
                  >{{ item.move > 0 ? "+" : "" }}{{ item.move }}%</small
                ></strong
              >
            </div>
            <p>
              Bars show assumed change from the ${{
                current.price.toFixed(2)
              }}
              sample price. No historical prices or probabilities are shown.
            </p>
          </figure>
        </div>
        <p class="assumption-note">
          Sample price × (1 + assumed move). These scenarios are neither
          forecasts nor probability estimates.
        </p>
      </div>
    </section>

    <div class="decision-spread">
      <section class="risk-sidebar" aria-label="Risk simulator">
        <p class="small-heading">
          <ShieldCheck :size="16" />02 / PUT THE DOWNSIDE ON PAPER
        </p>
        <h4>Size the uncertainty.</h4>
        <p class="risk-intro">
          How would your {{ current.symbol }} position affect the whole
          portfolio?
        </p>
        <fieldset class="compact-scenarios">
          <legend>Scenario</legend>
          <div>
            <button
              v-for="item in scenarios"
              :key="item.id"
              :class="{ selected: activeScenario === item.id }"
              :aria-pressed="activeScenario === item.id"
              @click="activeScenario = item.id"
            >
              {{ item.label
              }}<Check v-if="activeScenario === item.id" :size="13" />
            </button>
          </div>
        </fieldset>
        <div class="weight-label">
          <label for="position-weight">Position weight</label
          ><output for="position-weight">{{ weight }}%</output>
        </div>
        <input
          id="position-weight"
          v-model.number="weight"
          type="range"
          min="1"
          max="50"
          step="1"
          :aria-valuetext="`${weight} percent of portfolio`"
        />
        <div class="range-ends">
          <span>1% of portfolio</span><span>50%</span>
        </div>
        <div class="stress-result">
          <div>
            <span>Portfolio stress impact</span
            ><strong>−{{ portfolioImpact }}<small>%</small></strong>
          </div>
          <p>
            {{ weight }}% position ×<br />{{ scenario.drawdown }}% assumed
            drawdown
          </p>
        </div>
        <div class="stress-gauge" aria-hidden="true">
          <i :style="{ width: `${(Number(portfolioImpact) / 12) * 100}%` }"></i>
        </div>
        <div class="stress-scale">
          <span>0% portfolio stress</span><span>12%</span>
        </div>
        <p class="risk-footnote">
          Illustrative sizing only. No leverage; excludes fees and slippage.
          This estimate does not enforce a loss limit. No trade is submitted.
        </p>
        <button class="inline-button risk-note-link" @click="focusDecisionNote">
          Record this scenario <ArrowRight :size="16" />
        </button>
      </section>
      <section class="save-area" aria-label="Decision note">
        <p class="small-heading">03 / RECORD THE WHY</p>
        <h4>Make a note.<br />Keep your perspective.</h4>
        <p class="note-intro">
          A useful decision starts with a reason you can revisit.
        </p>
        <label for="thesis-note">Your decision note <span>optional</span></label
        ><textarea
          id="thesis-note"
          v-model="note"
          rows="4"
          maxlength="500"
          aria-describedby="draft-note"
          placeholder="What would you need to see before acting?"
        ></textarea>
        <p id="draft-note" class="draft-note">
          {{ current.symbol }} draft · {{ note.length }}/500 characters · kept
          until you leave this page
        </p>
        <div class="save-row">
          <small
            >{{ scenario.label }} case · {{ weight }}% position<br />Saved on
            this device. Unencrypted.</small
          ><button
            class="save-button"
            :disabled="isSaved || !!journalError"
            @click="saveThesis"
          >
            <Check v-if="isSaved" :size="16" /><Bookmark v-else :size="16" />{{
              isSaved
                ? "Saved to journal"
                : revisitedEntry
                  ? "Save revised thesis"
                  : "Save thesis"
            }}
          </button>
        </div>
        <button
          v-if="isSaved"
          id="saved-journal-link"
          class="saved-journal-link inline-button"
          @click="openSavedJournal"
        >
          View saved entry in My journal <ArrowRight :size="16" />
        </button>
      </section>
    </div>
    <div v-if="notice || journalError" class="desk-feedback">
      <p v-if="notice" role="status">{{ notice }}</p>
      <div v-if="journalError" class="storage-error" role="alert">
        <span>{{ journalError }}</span
        ><button class="inline-button" @click="loadJournal">
          Retry storage
        </button>
      </div>
    </div>
    <section
      v-if="journalOpen"
      id="local-journal"
      class="local-journal"
      aria-labelledby="local-journal-title"
      @keydown.esc.stop.prevent="toggleJournal"
    >
      <div class="journal-heading">
        <div>
          <p class="small-heading">YOUR DECISION RECORD</p>
          <h4 id="local-journal-title" ref="journalHeading" tabindex="-1">
            My journal <span>{{ journal.length }}</span>
          </h4>
        </div>
        <div class="journal-actions">
          <button
            class="quiet-button"
            :disabled="!journal.length"
            @click="exportJournal"
          >
            <Download :size="15" /> Export JSON</button
          ><button
            class="journal-close"
            aria-label="Close journal"
            @click="toggleJournal"
          >
            <X :size="18" />
          </button>
        </div>
      </div>
      <p class="journal-disclosure">
        Local, unencrypted storage in this browser. No cloud sync or onchain
        proof. Avoid sensitive information; export a copy before clearing
        browser data.
      </p>
      <div v-if="journal.length" class="journal-filters">
        <label class="journal-search" for="journal-search"
          ><Search :size="17" aria-hidden="true" /><input
            id="journal-search"
            v-model="journalQuery"
            type="search"
            placeholder="Search notes, assets, or assumptions"
            aria-label="Search journal"
        /></label>
        <label class="journal-asset-filter"
          >Asset<select
            v-model="journalAsset"
            aria-label="Filter journal by asset"
          >
            <option value="all">All assets</option>
            <option
              v-for="asset in assets"
              :key="asset.symbol"
              :value="asset.symbol"
            >
              {{ asset.symbol }}
            </option>
          </select></label
        >
        <span class="journal-filter-count" role="status"
          >{{ filteredJournal.length }} of {{ journal.length }} entries</span
        >
      </div>
      <div v-if="lastDeleted" class="undo-row">
        <span>Last journal entry removed.</span
        ><button
          id="journal-undo"
          class="inline-button"
          :disabled="!!journalError"
          @click="undoDelete"
        >
          <Undo2 :size="14" /> Undo deletion
        </button>
      </div>
      <div v-if="journalError && !journal.length" class="journal-empty">
        <BookOpen :size="26" />
        <h5>Your saved journal is unavailable.</h5>
        <p>
          Use Retry storage above to recover your entries. Existing data has not
          been changed.
        </p>
      </div>
      <div v-else-if="!journal.length" class="journal-empty">
        <BookOpen :size="26" />
        <h5>A little context for your next decision.</h5>
        <p>Select an asset, adjust its scenario, and save your first thesis.</p>
        <button class="inline-button" @click="focusDecisionNote">
          Write your first note <ArrowRight :size="16" />
        </button>
      </div>
      <div v-else-if="!filteredJournal.length" class="journal-empty">
        <Search :size="26" />
        <h5>No decisions match these filters.</h5>
        <p>Try a different asset or a word from your notes.</p>
        <button class="inline-button" @click="clearJournalFilters">
          Clear journal filters
        </button>
      </div>
      <ol v-else class="journal-entries">
        <li v-for="entry in filteredJournal" :key="entry.id">
          <div class="entry-heading">
            <div>
              <strong>{{ entry.symbol }}</strong
              ><span
                >{{ entry.scenario }} case · {{ entry.weight }}% position</span
              >
            </div>
            <time :datetime="new Date(entry.savedAt).toISOString()">{{
              formatDate(entry.savedAt)
            }}</time>
          </div>
          <p>{{ entry.thesis }}</p>
          <p v-if="entry.note" class="entry-note">
            <strong>Your note</strong>{{ entry.note }}
          </p>
          <div class="entry-footer">
            <button
              class="revisit-entry quiet-button"
              :aria-label="`Revisit ${entry.symbol} decision from ${formatDate(entry.savedAt)}`"
              @click="revisitDecision(entry)"
            >
              <RotateCcw :size="15" /> Revisit decision
            </button>
            <button
              class="delete-entry"
              :aria-label="`Delete ${entry.symbol} journal entry from ${formatDate(entry.savedAt)}`"
              :disabled="!!journalError"
              @click="deleteEntry(entry)"
            >
              <Trash2 :size="14" /> Delete
            </button>
          </div>
          <p class="entry-disclosure">
            Saved snapshot · Sample data · Local copy
          </p>
        </li>
      </ol>
    </section>
    <footer class="desk-footer">
      <span
        ><span class="preview-dot" aria-hidden="true"></span> PRODUCT PREVIEW /
        SAMPLE DATA</span
      ><span>Research is a process. The decision is yours.</span>
    </footer>
  </div>
</template>

<style scoped>
.research-desk {
  --desk-positive: #376156;
  --desk-negative: var(--red, #a93827);
  --desk-wine: #462c34;
  --desk-peach: #eedacc;
  --desk-sage: #dfe9e5;
  width: 100%;
  min-width: 0;
  color: var(--ink);
  background: var(--surface);
  border: 1px solid var(--line);
  font: 14px/1.6 var(--sans);
  text-align: left;
  color-scheme: light;
}
.research-desk *,
.research-desk *::before,
.research-desk *::after {
  box-sizing: border-box;
}
.research-desk :is(p, h3, h4, h5, figure) {
  margin: 0;
}
.research-desk :is(button, input, textarea, select) {
  font: inherit;
}
.research-desk button {
  cursor: pointer;
  transition:
    background-color 0.18s,
    color 0.18s;
}
.research-desk
  :is(button, input, textarea, select, a, [tabindex]):focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 4px;
}
.research-desk :is(button, a, input, textarea, select) {
  -webkit-tap-highlight-color: transparent;
}
.research-desk button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}
.research-desk svg {
  flex-shrink: 0;
}
.research-desk .small-heading {
  display: flex;
  align-items: center;
  gap: 8px;
  font: 10px/1.7 var(--mono);
  letter-spacing: 1.2px;
  color: var(--muted);
  text-transform: uppercase;
}
.desk-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 28px 34px;
  background: var(--desk-wine);
  color: var(--paper);
}
.desk-title {
  display: flex;
  align-items: center;
  gap: 21px;
}
.folio-mark {
  font: italic 50px/0.8 var(--serif);
  padding-right: 23px;
  border-right: 1px solid #866f73;
}
.desk-title small {
  display: block;
  font: 9px/1.8 var(--mono);
  letter-spacing: 1.8px;
  color: #e3c7bd;
}
.desk-title h3 {
  margin-top: 5px;
  font: normal 25px/1.2 var(--serif);
  letter-spacing: -0.3px;
}
.quiet-button,
.inline-button,
.next-step,
.save-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  min-height: 44px;
  padding: 10px 16px;
  border: 1px solid var(--line);
  border-radius: 0;
  background: transparent;
  color: var(--ink);
  font: 600 12px/1.5 var(--sans) !important;
  text-decoration: none;
}
.quiet-button:hover:not(:disabled) {
  background: var(--surface-2);
}
.journal-toggle {
  flex-shrink: 0;
  color: var(--paper);
  border-color: #89777a;
}
.journal-toggle:hover:not(:disabled) {
  background: #61434b;
  color: var(--paper);
}
.count {
  display: grid;
  place-items: center;
  width: 23px;
  height: 23px;
  background: var(--paper);
  color: var(--desk-wine);
  font: 11px var(--mono);
}
.asset-index {
  padding: 22px 34px;
  border-bottom: 1px solid var(--line);
  background: var(--paper);
}
.index-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 15px;
}
.sample-note {
  font: 10px var(--mono);
  color: var(--muted);
}
.index-controls {
  display: grid;
  grid-template-columns: 180px minmax(0, 1fr);
  gap: 18px;
  align-items: center;
}
.asset-search {
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid var(--ink);
  color: var(--muted);
}
.asset-search input {
  width: 100%;
  min-width: 0;
  height: 49px;
  padding: 8px 0;
  border: 0;
  background: transparent;
  color: var(--ink);
  font-size: 12px;
}
.asset-search input::-webkit-search-cancel-button {
  display: none;
}
.asset-search button {
  display: grid;
  place-items: center;
  min-width: 44px;
  min-height: 44px;
  border: 0;
  color: var(--ink);
  background: transparent;
}
.asset-list {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 7px;
}
.asset-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  min-width: 0;
  min-height: 69px;
  padding: 11px;
  border: 1px solid transparent;
  border-bottom-color: var(--line);
  background: transparent;
  color: var(--ink);
  text-align: left;
}
.asset-row:hover {
  border-color: var(--line);
  background: var(--surface);
}
.asset-row.selected {
  border-color: var(--desk-wine);
  background: var(--desk-wine);
  color: var(--paper);
}
.asset-name,
.asset-quote {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}
.asset-name strong {
  font: 600 13px var(--sans);
}
.asset-name small {
  font-size: 10px;
  color: var(--muted);
}
.asset-row.selected .asset-name small {
  color: #e4d4ce;
}
.asset-quote {
  text-align: right;
}
.asset-quote strong {
  font: 11px var(--mono);
}
.asset-quote small {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  font: 10px var(--mono);
}
.positive {
  color: var(--desk-positive);
}
.negative {
  color: var(--desk-negative);
}
.asset-row.selected .positive,
.asset-row.selected .negative {
  color: #f2c8b7;
}
.search-empty {
  display: flex;
  align-items: center;
  gap: 18px;
  grid-column: 1/-1;
  font-size: 12px;
  min-height: 69px;
}
.inline-button {
  padding: 7px 0;
  border: 0;
  color: var(--accent);
  text-align: left;
  justify-content: flex-start;
}
.inline-button:hover {
  text-decoration: underline;
  text-underline-offset: 4px;
}
.asset-heading {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  align-items: center;
  gap: 28px;
  padding: 38px 34px 33px;
}
.asset-title-group h3 {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-top: 7px;
  font: normal 60px/1.15 var(--serif);
  letter-spacing: -2px;
  scroll-margin-top: 100px;
}
.signal-status {
  padding: 4px 8px;
  border: 1px solid #c6d4cd;
  color: var(--desk-positive);
  font: 10px/1.5 var(--mono);
  letter-spacing: 0.5px;
  text-transform: uppercase;
}
.signal-status.watch {
  color: #6c5440;
  border-color: #d8c7af;
}
.signal-status.caution {
  color: var(--accent);
  border-color: #d9b9ac;
}
.asset-title-note {
  padding-left: 30px;
  border-left: 1px solid var(--line);
}
.asset-title-note p {
  margin-top: 8px;
  font: italic 25px/1.2 var(--serif);
  color: var(--muted);
}
.asset-title-note .small-heading {
  font-size: 9px;
}
.main-price {
  text-align: right;
}
.main-price .small-heading {
  justify-content: flex-end;
}
.main-price > strong {
  display: block;
  margin-top: 7px;
  font: normal 37px/1.2 var(--serif);
  letter-spacing: -1px;
}
.main-price > small {
  display: block;
  margin-top: 7px;
  font: 11px var(--mono);
}
.main-price small span {
  color: var(--muted);
  font-size: 9px;
}
.revisit-banner {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 17px 34px;
  border-top: 1px solid var(--line);
  background: var(--desk-sage);
  font-size: 13px;
}
.revisit-banner p {
  flex: 1;
}
.revisit-banner p span {
  display: block;
  color: var(--muted);
  font-size: 11px;
}
.revisit-banner button {
  flex-shrink: 0;
}
.research-tabs {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin: 0 34px;
  border-block: 1px solid var(--line);
}
.research-tabs button {
  display: flex;
  align-items: center;
  gap: 17px;
  min-height: 84px;
  padding: 16px 22px;
  border: 0;
  border-right: 1px solid var(--line);
  background: transparent;
  color: var(--muted);
  text-align: left;
}
.research-tabs button:last-child {
  border-right: 0;
}
.research-tabs button.selected {
  background: var(--desk-peach);
  color: var(--desk-wine);
}
.research-tabs button:hover:not(.selected) {
  background: var(--paper);
}
.tab-number {
  font: italic 22px var(--serif);
  color: var(--accent);
}
.tab-title {
  flex: 1;
  font: normal 23px/1.2 var(--serif);
}
.tab-title small {
  display: block;
  margin-top: 5px;
  font: 11px/1.5 var(--sans);
  color: var(--muted);
}
.research-panel {
  padding: 34px;
  scroll-margin-top: 100px;
}
.brief-panel {
  display: grid;
  grid-template-columns: 1.18fr 1fr;
  gap: 46px;
  min-height: 370px;
}
.brief-label {
  display: flex;
  align-items: center;
  gap: 10px;
  font: 10px/1.6 var(--mono);
  letter-spacing: 1.2px;
  color: var(--accent);
}
.sample-tag {
  margin-left: auto;
  border: 1px solid var(--line);
  padding: 2px 6px;
  color: var(--muted);
  font-size: 8px;
  letter-spacing: 0.7px;
}
.thesis-copy {
  margin-top: 24px !important;
  max-width: 640px;
  font: normal clamp(24px, 2.6vw, 34px)/1.4 var(--serif);
  letter-spacing: -0.55px;
}
.next-step {
  min-height: 47px;
  margin-top: 25px;
  padding: 10px 0;
  border: 0;
  border-bottom: 1px solid var(--accent);
  color: var(--accent);
  justify-content: space-between;
  gap: 28px;
}
.next-step:hover {
  gap: 36px;
  background: transparent;
}
.context-column {
  padding-left: 35px;
  border-left: 1px solid var(--line);
}
.counter-case h4 {
  margin-top: 11px;
  font: normal 25px/1.25 var(--serif);
}
.counter-case > p {
  margin-top: 14px;
  font-size: 13px;
  line-height: 1.9;
  color: var(--muted);
}
.evidence-summary {
  display: flex;
  align-items: center;
  gap: 25px;
  margin-top: 23px;
  padding: 18px 0;
  border-block: 1px solid var(--line);
}
.evidence-summary > div:first-child {
  display: flex;
  align-items: center;
  gap: 13px;
}
.evidence-summary strong {
  white-space: nowrap;
  font: 28px var(--serif);
}
.evidence-summary strong small {
  font: 11px var(--mono);
  color: var(--muted);
}
.evidence-summary span {
  max-width: 85px;
  font-size: 10px;
  line-height: 1.6;
  color: var(--muted);
}
.signal-track {
  flex: 1;
  height: 5px;
  background: var(--line);
}
.signal-track i {
  display: block;
  height: 100%;
  background: var(--desk-wine);
}
.evidence-button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  width: 100%;
  min-height: 48px;
  padding: 12px 0;
  border: 0;
  background: transparent;
  color: var(--ink);
  font-size: 11px !important;
}
.evidence-button:hover {
  color: var(--accent);
}
.evidence-button .rotated {
  transform: rotate(180deg);
}
.evidence-detail {
  padding: 18px;
  background: var(--paper);
  font-size: 12px;
  line-height: 1.8;
}
.evidence-detail p {
  margin-top: 10px;
  color: var(--muted);
}
.source-panel {
  display: grid;
  grid-template-columns: 0.8fr 1.2fr;
  gap: 60px;
}
.section-introduction h4 {
  margin-top: 22px;
  font: normal 37px/1.14 var(--serif);
  letter-spacing: -0.8px;
}
.panel-copy {
  font-size: 13px;
  line-height: 1.9;
  color: var(--muted);
}
.section-introduction > .panel-copy {
  margin-top: 20px;
}
.source-ledger {
  border-top: 1px solid var(--line);
}
.source-record {
  display: flex;
  align-items: flex-start;
  gap: 22px;
  padding: 23px 0;
  border-bottom: 1px solid var(--line);
  color: var(--ink);
  text-decoration: none;
}
.source-number {
  font: italic 23px var(--serif);
  color: var(--accent);
}
.source-record > div {
  flex: 1;
}
.source-record strong {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
}
.source-record p {
  margin-top: 8px;
  font-size: 12px;
  line-height: 1.8;
  color: var(--muted);
}
.source-record small {
  display: block;
  margin-top: 11px;
  font: 9px/1.7 var(--mono);
  color: var(--muted);
  letter-spacing: 0.6px;
}
.source-link:hover strong {
  color: var(--accent);
  text-decoration: underline;
  text-underline-offset: 4px;
}
.scenario-introduction {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 40px;
}
.scenario-introduction h4 {
  margin-top: 17px;
  font: normal 34px/1.2 var(--serif);
  letter-spacing: -0.6px;
}
.scenario-introduction > .panel-copy {
  max-width: 320px;
}
.scenario-choices {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-top: 28px;
}
.scenario-choices button {
  display: flex;
  flex-direction: column;
  min-width: 0;
  padding: 21px;
  border: 1px solid var(--line);
  background: var(--paper);
  color: var(--ink);
  text-align: left;
}
.scenario-choices button.selected {
  outline: 1px solid var(--desk-wine);
  border-color: var(--desk-wine);
  background: var(--desk-peach);
}
.scenario-choices button.bull {
  background: var(--desk-sage);
}
.scenario-choices button.bear {
  background: #f4e4de;
}
.scenario-choices button:hover {
  border-color: var(--ink);
}
.scenario-choices button > span:first-child {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  font: 10px/1.5 var(--mono);
  text-transform: uppercase;
  letter-spacing: 0.7px;
}
.scenario-choices strong {
  margin-top: 15px;
  font: normal 43px/1.15 var(--serif);
  letter-spacing: -1.5px;
}
.scenario-choices small {
  max-width: 210px;
  min-height: 43px;
  margin-top: 10px;
  font-size: 12px;
  line-height: 1.8;
  color: var(--muted);
}
.case-price {
  display: flex;
  align-items: center;
  justify-content: space-between;
  align-self: stretch;
  margin-top: 22px;
  padding-top: 12px;
  border-top: 1px solid #c9baad;
  font: 12px var(--mono);
}
.scenario-comparison {
  display: grid;
  grid-template-columns: 0.8fr 1.2fr;
  gap: 40px;
  margin-top: 30px;
  padding-top: 25px;
  border-top: 1px solid var(--line);
}
.scenario-result > span {
  display: block;
  font-size: 12px;
  color: var(--muted);
}
.scenario-result > .small-heading {
  margin-bottom: 17px;
  font-size: 9px;
}
.scenario-result strong {
  display: block;
  margin: 6px 0 12px;
  font: normal 40px/1.2 var(--serif);
  letter-spacing: -1px;
}
.scenario-result p {
  font-size: 12px;
  color: var(--muted);
}
.scenario-chart figcaption {
  display: flex;
  justify-content: space-between;
  gap: 15px;
  margin-bottom: 12px;
  font: 9px var(--mono);
  color: var(--muted);
  letter-spacing: 0.5px;
}
.scenario-chart-row {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr) 80px;
  align-items: center;
  gap: 12px;
  padding: 6px 0;
  font-size: 11px;
  color: var(--muted);
}
.scenario-chart-row.selected {
  color: var(--accent);
}
.scenario-bar-track {
  position: relative;
  height: 23px;
  border-bottom: 1px solid var(--line);
  background: repeating-linear-gradient(
    90deg,
    transparent,
    transparent calc(20% - 1px),
    var(--line) calc(20% - 1px),
    var(--line) 20%
  );
}
.scenario-bar-track::after {
  content: "";
  position: absolute;
  height: 100%;
  width: 1px;
  left: 40%;
  top: 0;
  background: var(--muted);
}
.scenario-bar-track i {
  position: absolute;
  height: 9px;
  top: 6px;
  background: #77938a;
}
.scenario-bar-track i.downside {
  background: #c18570;
}
.selected .scenario-bar-track i {
  background: var(--desk-wine);
}
.selected .scenario-bar-track i.downside {
  background: var(--accent);
}
.scenario-chart-row strong {
  text-align: right;
  font: 11px var(--mono);
}
.scenario-chart-row strong small {
  display: block;
  margin-top: 4px;
  font-size: 9px;
}
.scenario-chart > p {
  margin-top: 15px;
  font-size: 10px;
  line-height: 1.8;
  color: var(--muted);
}
.assumption-note {
  margin-top: 25px !important;
  padding-top: 15px;
  border-top: 1px solid var(--line);
  font-size: 10px;
  color: var(--muted);
}
.decision-spread {
  display: grid;
  grid-template-columns: 0.82fr 1.18fr;
  border-top: 1px solid var(--line);
}
.risk-sidebar {
  padding: 32px 34px;
  background: var(--desk-sage);
}
.risk-sidebar h4 {
  margin-top: 16px;
  font: normal 32px/1.2 var(--serif);
  letter-spacing: -0.6px;
}
.risk-intro {
  max-width: 360px;
  margin-top: 12px !important;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.8;
}
.compact-scenarios {
  min-width: 0;
  padding: 0;
  border: 0;
  margin: 23px 0;
}
.compact-scenarios legend {
  margin-bottom: 9px;
  padding: 0;
  font-size: 12px;
}
.compact-scenarios > div {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  border: 1px solid #aebdb4;
}
.compact-scenarios button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  min-height: 44px;
  padding: 9px 3px;
  border: 0;
  border-right: 1px solid #aebdb4;
  background: transparent;
  color: var(--ink);
  font-size: 12px;
}
.compact-scenarios button:last-child {
  border-right: 0;
}
.compact-scenarios button.selected {
  background: var(--desk-wine);
  color: var(--paper);
}
.compact-scenarios button:hover:not(.selected) {
  background: #f0f4ee;
}
.weight-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  font-size: 12px;
}
.weight-label output {
  font: 25px var(--serif);
}
.risk-sidebar input[type="range"] {
  width: 100%;
  min-height: 44px;
  margin: 0;
  accent-color: var(--desk-wine);
  cursor: pointer;
}
.range-ends,
.stress-scale {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: var(--muted);
  font: 9px var(--mono);
}
.stress-result {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 22px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #bfc9c0;
}
.stress-result > div > span {
  font-size: 11px;
  color: var(--muted);
}
.stress-result strong {
  display: block;
  margin-top: 5px;
  font: normal 42px/1.2 var(--serif);
  letter-spacing: -1.5px;
  color: var(--accent);
}
.stress-result strong small {
  font-size: 25px;
}
.stress-result p {
  max-width: 140px;
  font-size: 10px;
  line-height: 1.8;
  color: var(--muted);
}
.stress-gauge {
  height: 4px;
  margin-top: 17px;
  overflow: hidden;
  background: #c1cec4;
}
.stress-gauge i {
  display: block;
  height: 100%;
  background: var(--accent);
}
.stress-scale {
  margin-top: 8px;
  font-size: 8px;
}
.risk-footnote {
  margin-top: 23px !important;
  max-width: 400px;
  font-size: 10px;
  line-height: 1.8;
  color: var(--muted);
}
.risk-note-link {
  margin-top: 7px;
}
.save-area {
  min-width: 0;
  padding: 32px 38px;
  background: var(--paper);
  border-left: 1px solid var(--line);
}
.save-area h4 {
  margin-top: 16px;
  font: normal 36px/1.17 var(--serif);
  letter-spacing: -0.8px;
}
.note-intro {
  margin-top: 12px !important;
  color: var(--muted);
  font-size: 12px;
}
.save-area label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 26px;
  font-size: 12px;
}
.save-area label span {
  font-size: 10px;
  color: var(--muted);
}
.save-area textarea {
  display: block;
  width: 100%;
  min-height: 142px;
  max-height: 320px;
  margin: 10px 0 9px;
  padding: 14px 0;
  border: 0;
  border-block: 1px solid var(--line);
  border-radius: 0;
  resize: vertical;
  scroll-margin-top: 120px;
  background: repeating-linear-gradient(
    transparent,
    transparent 27px,
    #d8cec166 28px,
    transparent 29px
  );
  color: var(--ink);
  font-size: 13px;
  line-height: 29px;
}
.save-area textarea::placeholder,
.research-desk input::placeholder {
  color: var(--muted);
  opacity: 1;
}
.draft-note {
  font: 9px/1.8 var(--mono);
  color: var(--muted);
}
.save-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  margin-top: 20px;
}
.save-row small {
  font-size: 10px;
  line-height: 1.8;
  color: var(--muted);
}
.save-button {
  min-height: 48px;
  flex-shrink: 0;
  padding: 12px 23px;
  border-color: var(--accent);
  background: var(--accent);
  color: var(--surface);
}
.save-button:hover:not(:disabled) {
  background: var(--desk-wine);
  border-color: var(--desk-wine);
}
.save-button:disabled {
  opacity: 1;
  color: var(--muted);
  border-color: var(--line);
  background: var(--surface-2);
}
.saved-journal-link {
  margin-top: 8px;
  font-size: 11px !important;
}
.desk-feedback {
  padding: 17px 34px;
  border-top: 1px solid var(--line);
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 12px;
  line-height: 1.8;
}
.storage-error {
  display: flex;
  align-items: center;
  gap: 20px;
}
.storage-error span {
  flex: 1;
}
.storage-error button {
  flex-shrink: 0;
}
.local-journal {
  padding: 34px;
  background: var(--surface);
  border-top: 1px solid var(--line);
  scroll-margin-top: 100px;
}
.journal-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}
.journal-heading h4 {
  margin-top: 8px;
  font: normal 40px/1.2 var(--serif);
  letter-spacing: -1px;
  scroll-margin-top: 110px;
}
.journal-heading h4 span {
  margin-left: 10px;
  vertical-align: middle;
  font: 12px var(--mono);
  color: var(--muted);
}
.journal-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.journal-close {
  display: grid;
  place-items: center;
  min-height: 44px;
  min-width: 44px;
  padding: 10px;
  border: 1px solid var(--line);
  color: var(--ink);
  background: transparent;
}
.journal-close:hover {
  background: var(--paper);
}
.journal-disclosure {
  max-width: 700px;
  margin-top: 18px !important;
  font-size: 11px;
  line-height: 1.9;
  color: var(--muted);
}
.journal-filters {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 18px;
  margin-top: 24px;
  padding: 14px 0;
  border-block: 1px solid var(--line);
}
.journal-search {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 200px;
  color: var(--muted);
}
.journal-search input {
  width: 100%;
  min-width: 0;
  min-height: 44px;
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: 0;
  background: var(--paper);
  color: var(--ink);
  font-size: 12px;
}
.journal-asset-filter {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: var(--muted);
}
.journal-asset-filter select {
  min-height: 44px;
  padding: 9px 28px 9px 12px;
  border: 1px solid var(--line);
  border-radius: 0;
  background: var(--paper);
  color: var(--ink);
  font-size: 12px;
}
.journal-filter-count {
  font: 10px var(--mono);
  color: var(--muted);
  white-space: nowrap;
}
.undo-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 10px 18px;
  margin-top: 20px;
  background: var(--accent-soft);
  font-size: 12px;
  color: var(--accent);
}
.journal-empty {
  padding: 50px 20px;
  text-align: center;
  color: var(--muted);
}
.journal-empty h5 {
  margin: 16px 0 10px;
  color: var(--ink);
  font: normal 30px/1.3 var(--serif);
}
.journal-empty p {
  font-size: 13px;
  line-height: 1.8;
}
.journal-entries {
  counter-reset: entry;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 30px;
  list-style: none;
  padding: 0;
  margin: 12px 0 0;
}
.journal-entries li {
  counter-increment: entry;
  position: relative;
  min-width: 0;
  padding: 27px 0 23px 43px;
  border-bottom: 1px solid var(--line);
  overflow-wrap: anywhere;
}
.journal-entries li::before {
  content: counter(entry, decimal-leading-zero);
  position: absolute;
  left: 0;
  top: 28px;
  font: italic 24px var(--serif);
  color: var(--accent);
}
.entry-heading {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 15px;
}
.entry-heading strong {
  font: normal 24px var(--serif);
}
.entry-heading span {
  display: block;
  margin-top: 4px;
  font-size: 10px;
  color: var(--muted);
  text-transform: capitalize;
}
.entry-heading time {
  font: 9px/1.8 var(--mono);
  text-align: right;
  color: var(--muted);
}
.journal-entries li > p {
  margin-top: 18px;
  font-size: 12px;
  line-height: 1.9;
}
.entry-note {
  padding: 12px 15px;
  background: var(--paper);
  white-space: pre-wrap;
}
.entry-note strong {
  display: block;
  margin-bottom: 5px;
  font: 9px var(--mono);
  color: var(--muted);
}
.entry-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 20px;
}
.revisit-entry {
  font-size: 10px !important;
  padding: 8px 12px;
}
.delete-entry {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 44px;
  padding: 9px 7px;
  border: 0;
  background: transparent;
  color: var(--accent);
  font-size: 10px !important;
}
.delete-entry:hover {
  background: var(--accent-soft);
}
.journal-entries li > .entry-disclosure {
  margin-top: 13px;
  color: var(--muted);
  font: 9px/1.7 var(--mono);
}
.desk-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 18px 34px;
  border-top: 1px solid var(--line);
  background: var(--paper);
  color: var(--muted);
  font: 9px/1.8 var(--mono);
  letter-spacing: 0.5px;
}
.desk-footer > span:first-child {
  display: flex;
  align-items: center;
  gap: 8px;
}
.desk-footer > span:last-child {
  font: italic 16px/1.4 var(--serif);
  letter-spacing: 0;
}
.preview-dot {
  width: 6px;
  height: 6px;
  background: var(--accent);
  border-radius: 50%;
}
@media (min-width: 1400px) {
  .brief-panel {
    gap: 70px;
  }
  .context-column {
    padding-left: 50px;
  }
}
@media (max-width: 1100px) {
  .index-controls {
    grid-template-columns: 1fr;
  }
  .asset-search {
    max-width: 280px;
  }
  .asset-list {
    gap: 12px;
  }
  .asset-row {
    padding: 12px 15px;
  }
  .asset-title-note {
    display: none;
  }
  .asset-heading {
    grid-template-columns: 1fr auto;
  }
  .brief-panel {
    gap: 30px;
  }
  .context-column {
    padding-left: 25px;
  }
  .scenario-introduction {
    display: block;
  }
  .scenario-introduction > .panel-copy {
    max-width: 600px;
    margin-top: 16px;
  }
  .decision-spread {
    grid-template-columns: 1fr 1.15fr;
  }
  .save-area {
    padding: 30px;
  }
  .stress-result {
    gap: 10px;
  }
  .stress-result strong {
    font-size: 36px;
  }
  .source-panel {
    gap: 35px;
  }
}
@media (max-width: 780px) {
  .desk-header {
    padding: 24px;
  }
  .desk-title h3 {
    font-size: 23px;
  }
  .desk-title {
    gap: 16px;
  }
  .folio-mark {
    font-size: 44px;
    padding-right: 16px;
  }
  .asset-index {
    padding: 22px 24px;
  }
  .asset-heading {
    padding: 30px 24px;
  }
  .research-tabs {
    margin-inline: 24px;
  }
  .research-tabs button {
    padding: 15px;
    gap: 11px;
  }
  .tab-title {
    font-size: 21px;
  }
  .tab-title small {
    font-size: 10px;
  }
  .research-tabs button > svg {
    display: none;
  }
  .research-panel {
    padding: 30px 24px;
  }
  .brief-panel {
    grid-template-columns: 1fr;
    gap: 30px;
  }
  .thesis-copy {
    font-size: 31px;
    max-width: none;
  }
  .context-column {
    padding: 25px 0 0;
    border-left: 0;
    border-top: 1px solid var(--line);
  }
  .counter-case > p {
    max-width: 600px;
  }
  .evidence-summary {
    max-width: 500px;
  }
  .source-panel {
    grid-template-columns: 1fr;
    gap: 30px;
  }
  .section-introduction h4 br {
    display: none;
  }
  .source-record {
    padding: 20px 0;
  }
  .scenario-choices {
    gap: 10px;
  }
  .scenario-choices button {
    padding: 16px;
  }
  .scenario-choices strong {
    font-size: 38px;
  }
  .scenario-comparison {
    gap: 28px;
  }
  .decision-spread {
    grid-template-columns: 1fr;
  }
  .risk-sidebar {
    padding: 30px 24px;
  }
  .risk-intro {
    max-width: none;
  }
  .compact-scenarios {
    max-width: 500px;
  }
  .stress-result strong {
    font-size: 42px;
  }
  .risk-footnote {
    max-width: none;
  }
  .save-area {
    padding: 30px 24px;
    border-left: 0;
    border-top: 1px solid var(--line);
  }
  .save-area textarea {
    min-height: 148px;
  }
  .save-area h4 br {
    display: none;
  }
  .save-row {
    max-width: 620px;
  }
  .journal-entries {
    grid-template-columns: 1fr;
  }
  .local-journal {
    padding: 30px 24px;
  }
  .revisit-banner {
    padding: 18px 24px;
    flex-wrap: wrap;
  }
  .revisit-banner p {
    flex-basis: 80%;
  }
  .revisit-banner button {
    margin-left: 32px;
  }
  .desk-feedback,
  .desk-footer {
    padding: 17px 24px;
  }
}
@media (max-width: 540px) {
  .desk-header {
    padding: 22px 18px;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 21px;
  }
  .desk-title {
    gap: 14px;
  }
  .desk-title h3 {
    font-size: 24px;
  }
  .desk-title small {
    font-size: 8px;
    letter-spacing: 1px;
  }
  .folio-mark {
    font-size: 43px;
  }
  .journal-toggle {
    margin-left: auto;
    min-height: 44px;
    padding: 8px 12px;
    font-size: 11px !important;
  }
  .asset-index {
    padding: 20px 18px;
  }
  .index-label {
    align-items: flex-start;
    gap: 10px;
  }
  .index-label .small-heading {
    font-size: 9px;
    letter-spacing: 0.6px;
  }
  .sample-note {
    max-width: 110px;
    text-align: right;
    font-size: 9px;
    line-height: 1.7;
  }
  .index-controls {
    gap: 12px;
  }
  .asset-search {
    max-width: none;
  }
  .asset-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }
  .asset-row {
    padding: 11px 12px;
    min-height: 70px;
  }
  .asset-name small {
    font-size: 10px;
  }
  .asset-heading {
    gap: 15px;
    padding: 27px 18px;
  }
  .asset-title-group > .small-heading {
    font-size: 8px;
    letter-spacing: 0.6px;
  }
  .asset-title-group h3 {
    flex-wrap: wrap;
    gap: 8px;
    font-size: 43px;
    letter-spacing: -1px;
  }
  .signal-status {
    padding: 3px 6px;
    font-size: 8px;
  }
  .main-price .small-heading {
    font-size: 8px;
  }
  .main-price > strong {
    font-size: 28px;
    letter-spacing: -0.5px;
  }
  .main-price > small {
    font-size: 10px;
  }
  .main-price small span {
    display: block;
    margin-top: 4px;
    font-size: 8px;
  }
  .research-tabs {
    margin-inline: 18px;
  }
  .research-tabs button {
    display: block;
    min-height: 92px;
    padding: 12px 10px;
  }
  .tab-number {
    display: block;
    margin-bottom: 5px;
    font-size: 17px;
  }
  .tab-title {
    font-size: 20px;
  }
  .tab-title small {
    display: none;
  }
  .research-panel {
    padding: 27px 18px;
  }
  .brief-label {
    font-size: 9px;
    letter-spacing: 0.8px;
    gap: 8px;
  }
  .thesis-copy {
    margin-top: 19px !important;
    font-size: 28px;
    line-height: 1.4;
  }
  .counter-case h4 {
    font-size: 26px;
  }
  .source-panel .section-introduction h4 {
    font-size: 33px;
  }
  .scenario-introduction h4 {
    font-size: 31px;
  }
  .scenario-choices {
    grid-template-columns: 1fr;
    gap: 10px;
    margin-top: 23px;
  }
  .scenario-choices button {
    display: grid;
    grid-template-columns: 1fr auto;
    column-gap: 20px;
    padding: 16px 19px;
  }
  .scenario-choices button > span:first-child {
    grid-column: 1;
    align-self: end;
  }
  .scenario-choices strong {
    grid-column: 2;
    grid-row: 1/3;
    margin-top: 0;
    align-self: center;
    font-size: 39px;
  }
  .scenario-choices small {
    grid-column: 1;
    min-height: 0;
    max-width: none;
    margin-top: 7px;
    font-size: 11px;
  }
  .case-price {
    grid-column: 1/-1;
    margin-top: 13px;
    padding-top: 9px;
    font-size: 11px;
  }
  .scenario-comparison {
    grid-template-columns: 1fr;
    gap: 23px;
  }
  .scenario-result {
    padding-bottom: 23px;
    border-bottom: 1px solid var(--line);
  }
  .scenario-result strong {
    font-size: 37px;
  }
  .scenario-chart-row {
    grid-template-columns: 33px minmax(0, 1fr) 72px;
    gap: 8px;
  }
  .risk-sidebar,
  .save-area {
    padding: 28px 18px;
  }
  .risk-sidebar h4 {
    font-size: 31px;
  }
  .save-area h4 {
    font-size: 33px;
  }
  .save-area h4 br {
    display: initial;
  }
  .save-row {
    align-items: stretch;
    flex-direction: column;
    gap: 16px;
  }
  .save-row small br {
    display: none;
  }
  .save-button {
    min-height: 49px;
  }
  .saved-journal-link {
    font-size: 10px !important;
    gap: 6px;
  }
  .draft-note {
    font-size: 8px;
  }
  .revisit-banner {
    padding: 17px 18px;
    gap: 10px;
  }
  .revisit-banner p {
    font-size: 12px;
  }
  .revisit-banner p span {
    font-size: 10px;
  }
  .revisit-banner button {
    margin-left: 28px;
    font-size: 11px !important;
  }
  .desk-feedback {
    padding: 16px 18px;
  }
  .storage-error {
    align-items: flex-start;
    flex-direction: column;
    gap: 3px;
  }
  .local-journal {
    padding: 28px 18px;
  }
  .journal-heading {
    flex-wrap: wrap;
    gap: 20px;
  }
  .journal-heading h4 {
    font-size: 34px;
  }
  .journal-actions {
    margin-left: auto;
  }
  .journal-actions .quiet-button {
    font-size: 11px !important;
  }
  .journal-filters {
    gap: 12px;
  }
  .journal-search {
    flex-basis: 100%;
    min-width: 0;
  }
  .journal-filter-count {
    margin-left: auto;
    font-size: 9px;
  }
  .journal-empty {
    padding: 40px 8px;
  }
  .journal-empty h5 {
    font-size: 27px;
  }
  .journal-entries li {
    padding-left: 32px;
  }
  .journal-entries li::before {
    font-size: 21px;
  }
  .entry-heading {
    gap: 10px;
  }
  .entry-heading strong {
    font-size: 23px;
  }
  .entry-heading span {
    font-size: 9px;
  }
  .entry-heading time {
    font-size: 8px;
  }
  .entry-footer {
    flex-wrap: wrap;
    gap: 5px;
  }
  .undo-row {
    padding: 10px 12px;
    flex-wrap: wrap;
    gap: 2px;
  }
  .desk-footer {
    padding: 17px 18px;
    flex-wrap: wrap;
    gap: 7px;
    font-size: 8px;
  }
  .desk-footer > span:last-child {
    font-size: 15px;
  }
}
@media (max-width: 360px) {
  .asset-title-group h3 {
    font-size: 38px;
  }
  .main-price > strong {
    font-size: 24px;
  }
  .research-tabs button {
    padding-inline: 8px;
  }
  .tab-title {
    font-size: 18px;
  }
  .asset-row {
    padding: 10px 8px;
  }
  .asset-name strong {
    font-size: 12px;
  }
  .asset-quote strong {
    font-size: 10px;
  }
  .asset-quote small {
    font-size: 9px;
  }
  .desk-title h3 {
    font-size: 21px;
  }
  .journal-filter-count {
    margin-left: 0;
  }
}
@media (prefers-reduced-motion: reduce) {
  .research-desk *,
  .research-desk *::before,
  .research-desk *::after {
    animation: none !important;
    transition: none !important;
  }
}
</style>
