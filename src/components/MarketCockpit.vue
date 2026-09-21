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
  <div class="research-desk" role="region" :aria-label="`${brand.name} interactive research preview`">
    <header class="desk-header">
      <div class="desk-title"><span class="desk-indicator" aria-hidden="true"></span><h3>Research workspace</h3><span class="sample-tag">SAMPLE DATA</span></div>
      <button ref="journalToggle" class="quiet-button journal-toggle" :aria-expanded="journalOpen" aria-controls="local-journal" @click="toggleJournal"><BookOpen :size="16" /> My journal <span class="count">{{ journal.length }}</span></button>
    </header>

    <div class="workspace-grid">
      <aside class="asset-index" aria-label="Asset watchlist">
        <div class="index-label"><span class="small-heading">WATCHLIST</span><span class="asset-count">04</span></div>
        <div class="asset-search"><Search :size="15" aria-hidden="true" /><input ref="searchInput" v-model="query" type="search" aria-label="Search assets" placeholder="Find asset" /><button v-if="query" aria-label="Clear asset search" @click="clearSearch"><X :size="14" /></button></div>
        <div class="asset-list">
          <button v-for="asset in filteredAssets" :key="asset.symbol" class="asset-row" :class="{ selected: active === asset.symbol }" :aria-pressed="active === asset.symbol" @click="selectAsset(asset.symbol)">
            <span class="asset-name"><strong>{{ asset.symbol }}</strong><small>{{ asset.name }}</small></span>
            <span class="asset-quote"><strong>{{ asset.price.toFixed(2) }}</strong><small :class="asset.change > 0 ? 'positive' : 'negative'"><ArrowUpRight v-if="asset.change > 0" :size="12" /><ArrowDownRight v-else :size="12" />{{ Math.abs(asset.change).toFixed(2) }}%</small></span>
          </button>
          <div v-if="!filteredAssets.length" class="search-empty" role="status"><p>No matching assets.</p><button class="inline-button" @click="clearSearch">Clear search</button></div>
        </div>
        <p class="watchlist-caption">Illustrative prices · USD</p>
        <div class="workspace-guide"><span class="small-heading">YOUR RESEARCH LOOP</span><ol><li><span>01</span> Inspect the thesis</li><li><span>02</span> Test your assumptions</li><li><span>03</span> Save your reasoning</li></ol><p>Different asset, different draft.<br />Your work stays in place while you explore.</p></div>
      </aside>

      <section class="research-main" aria-label="Selected asset research">
        <div class="asset-heading">
          <div class="asset-title-group"><p class="small-heading">{{ current.name }} <span>/ EQUITY SAMPLE</span></p><h3 id="selected-asset-title" tabindex="-1">{{ current.symbol }}<span :class="['signal-status', current.status.toLowerCase()]">{{ current.status }}</span></h3></div>
          <div class="main-price"><strong>${{ current.price.toFixed(2) }}</strong><small :class="current.change > 0 ? 'positive' : 'negative'">{{ current.change > 0 ? '+' : '' }}{{ current.change.toFixed(2) }}% <span>sample move</span></small></div>
        </div>

        <div v-if="revisitedEntry" class="revisit-banner" role="status"><RotateCcw :size="17" /><div><strong>Reviewing {{ formatDate(revisitedEntry.savedAt) }}</strong><p>Changes create a new snapshot; your original is preserved.</p></div><button v-if="previousDraft" class="inline-button" @click="restorePreviousDraft">Restore previous draft</button></div>

        <figure class="projection-map" aria-labelledby="projection-title" aria-describedby="projection-description">
          <figcaption class="chart-topline"><div id="projection-title"><span class="small-heading">30-DAY SCENARIO MAP</span><span>Explore the range of assumptions</span></div><span class="chart-period">D0 → D30</span></figcaption>
          <svg class="projection-svg" viewBox="0 0 580 238" aria-hidden="true">
            <defs><linearGradient id="scenario-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#c4f06a" stop-opacity="0.12" /><stop offset="100%" stop-color="#c4f06a" stop-opacity="0.01" /></linearGradient></defs>
            <g class="chart-grid"><line v-for="y in [35, 85, 135, 185]" :key="y" x1="24" :y1="y" x2="505" :y2="y" /><line v-for="x in [24, 184, 344, 505]" :key="x" :x1="x" y1="20" :x2="x" y2="205" /></g>
            <line class="chart-baseline" x1="24" y1="125" x2="505" y2="125" />
            <path :d="`M24 125 L505 ${125 - scenario.move * 5} L505 125 Z`" fill="url(#scenario-fill)" />
            <g v-for="item in scenarios" :key="item.id" :class="['projection-line', item.id, { active: activeScenario === item.id }]">
              <line x1="24" y1="125" x2="505" :y2="125 - item.move * 5" />
              <circle cx="505" :cy="125 - item.move * 5" :r="activeScenario === item.id ? 5 : 3" />
              <text x="520" :y="129 - item.move * 5">{{ item.move > 0 ? '+' : '' }}{{ item.move }}%</text>
            </g>
            <circle class="chart-origin" cx="24" cy="125" r="4" />
            <text class="chart-label" x="24" y="226">SAMPLE PRICE</text><text class="chart-label" x="505" y="226" text-anchor="end">HYPOTHETICAL OUTCOME</text>
          </svg>
          <div class="chart-legend" role="group" aria-label="Chart scenario selection"><button v-for="item in scenarios" :key="item.id" :class="[item.id, { selected: activeScenario === item.id }]" :aria-pressed="activeScenario === item.id" @click="activeScenario = item.id"><span class="legend-dot" aria-hidden="true"></span>{{ item.label }}<strong>${{ (current.price * (1 + item.move / 100)).toFixed(2) }}</strong><Check v-if="activeScenario === item.id" :size="13" /></button></div>
          <p id="projection-description" class="chart-disclosure">Straight lines connect sample price to assumed outcomes. No historical prices, forecasts, or probabilities.</p>
        </figure>

        <div class="research-tabs" role="tablist" aria-label="Research sections" @keydown="navigateTabs"><button v-for="(tab, index) in tabs" :id="`research-tab-${tab.toLowerCase()}`" :key="tab" role="tab" :aria-label="tab" :aria-selected="activeTab === tab" :aria-controls="`research-panel-${tab.toLowerCase()}`" :tabindex="activeTab === tab ? 0 : -1" :class="{ selected: activeTab === tab }" @click="activeTab = tab"><FileText v-if="index === 0" :size="15" /><BookOpen v-else-if="index === 1" :size="15" /><SlidersHorizontal v-else :size="15" />{{ tab }}</button></div>

        <div v-if="activeTab === 'Brief'" id="research-panel-brief" class="research-panel brief-panel" role="tabpanel" aria-labelledby="research-tab-brief" tabindex="0">
          <div class="thesis-card"><div class="card-heading"><span class="small-heading">WORKING THESIS</span><span class="sample-tag">SAMPLE</span></div><p class="thesis-copy">{{ current.thesis }}</p></div>
          <div class="counter-case"><span class="counter-icon" aria-hidden="true">↳</span><div><h4>The counter-case</h4><p>{{ current.counter }}</p></div></div>
          <div class="evidence-summary"><div class="signal-score"><strong>{{ current.signal }}<small>/100</small></strong><div><span>Illustrative signal score</span><div class="signal-track" aria-hidden="true"><i :style="{ width: `${current.signal}%` }"></i></div></div></div><button class="evidence-button" :aria-expanded="evidenceOpen" aria-controls="evidence-detail" @click="evidenceOpen = !evidenceOpen">Data context <ChevronDown :size="15" :class="{ rotated: evidenceOpen }" /></button></div>
          <div v-if="evidenceOpen" id="evidence-detail" class="evidence-detail"><strong>Demonstration data only</strong><p>Prices, scores, and theses are fixed samples. No issuer filings, market feed, or model output are connected. Network references do not substantiate the investment thesis.</p><button class="inline-button" @click="goToTab('Sources')">Inspect source context <ArrowRight :size="14" /></button></div>
          <button class="next-step" @click="goToTab('Sources')">Inspect the sources <ArrowRight :size="15" /></button>
        </div>

        <div v-if="activeTab === 'Sources'" id="research-panel-sources" class="research-panel source-panel" role="tabpanel" aria-labelledby="research-tab-sources" tabindex="0">
          <div class="panel-introduction"><h4>Know what supports the view.</h4><p>This preview has no live research sources. The sample thesis has not been verified against issuer disclosures.</p></div>
          <div class="source-ledger"><div class="source-record"><span class="source-icon"><FileText :size="18" /></span><div><strong>{{ brand.name }} product sample</strong><p>Fixed prices, illustrative scores, and scenario assumptions. No collection timestamp.</p><small>DEMONSTRATION</small></div></div><a class="source-record source-link" href="https://docs.robinhood.com/chain/" target="_blank" rel="noreferrer"><span class="source-icon"><BookOpen :size="18" /></span><div><strong>Robinhood Chain documentation <ExternalLink :size="13" /></strong><p>Network reference for the wallet connection.</p><small>NETWORK REFERENCE ONLY</small></div></a><a class="source-record source-link" href="https://robinhoodchain.blockscout.com" target="_blank" rel="noreferrer"><span class="source-icon"><ExternalLink :size="18" /></span><div><strong>Robinhood Chain explorer <ExternalLink :size="13" /></strong><p>Inspect onchain activity independently.</p><small>NETWORK REFERENCE ONLY</small></div></a></div>
          <button class="next-step" @click="goToTab('Scenario')">Test an assumption <ArrowRight :size="15" /></button>
        </div>

        <div v-if="activeTab === 'Scenario'" id="research-panel-scenario" class="research-panel scenario-panel" role="tabpanel" aria-labelledby="research-tab-scenario" tabindex="0">
          <div class="panel-introduction"><h4>Change the case. See the impact.</h4><p>Each 30-day case includes an assumed price move and a separate stress drawdown for position sizing.</p></div>
          <div class="scenario-choices" role="group" aria-label="Market scenarios"><button v-for="item in scenarios" :key="item.id" :class="[item.id, { selected: activeScenario === item.id }]" :aria-pressed="activeScenario === item.id" @click="activeScenario = item.id"><span>{{ item.label }} <Check v-if="activeScenario === item.id" :size="14" /></span><strong>{{ item.move > 0 ? '+' : '' }}{{ item.move }}%</strong><small>{{ item.description }}</small><span class="case-price">${{ (current.price * (1 + item.move / 100)).toFixed(2) }}</span></button></div>
          <div class="scenario-result" aria-live="polite"><div><span class="small-heading">{{ scenario.label.toUpperCase() }} CASE / {{ current.symbol }}</span><p>Hypothetical price</p></div><strong>${{ projectedPrice }}</strong></div>
          <div class="scenario-metrics"><div><span>Assumed move</span><strong>{{ scenario.move > 0 ? '+' : '' }}{{ scenario.move }}%</strong></div><div><span>Stress drawdown</span><strong>−{{ scenario.drawdown }}%</strong></div><div><span>Portfolio stress</span><strong>−{{ portfolioImpact }}%</strong></div></div>
          <p class="assumption-note">Sample price × (1 + assumed move). Scenarios are neither forecasts nor probability estimates.</p>
          <button class="next-step" @click="focusDecisionNote">Record your assumptions <ArrowRight :size="15" /></button>
        </div>
      </section>

      <aside class="decision-sidebar">
        <section class="risk-sidebar" aria-label="Risk simulator"><div class="card-heading"><h4><SlidersHorizontal :size="16" /> Position lab</h4><span class="sample-tag">SIMULATION</span></div><p class="risk-intro">Test {{ current.symbol }} exposure before you commit to a view.</p><fieldset class="compact-scenarios"><legend>Scenario</legend><div><button v-for="item in scenarios" :key="item.id" :class="{ selected: activeScenario === item.id }" :aria-pressed="activeScenario === item.id" @click="activeScenario = item.id">{{ item.label }}</button></div></fieldset><div class="weight-label"><label for="position-weight">Position weight</label><output for="position-weight">{{ weight }}%</output></div><input id="position-weight" v-model.number="weight" type="range" min="1" max="50" step="1" :aria-valuetext="`${weight} percent of portfolio`" /><div class="range-ends"><span>1% of portfolio</span><span>50%</span></div><div class="stress-result"><span>Portfolio stress impact</span><strong>−{{ portfolioImpact }}<small>%</small></strong><p>{{ weight }}% position × {{ scenario.drawdown }}% assumed drawdown</p></div><div class="stress-gauge" aria-hidden="true"><i :style="{ width: `${(Number(portfolioImpact) / 12) * 100}%` }"></i></div><div class="stress-scale"><span>0%</span><span>12% stress</span></div><p class="risk-footnote">Illustrative sizing. No leverage, fees, or slippage. No loss limit enforced. No trade submitted.</p></section>
        <section class="save-area" aria-label="Decision note"><div class="card-heading"><h4><Bookmark :size="16" /> Decision note</h4><span class="draft-status">DRAFT</span></div><label for="thesis-note">What would change your mind? <span>Optional</span></label><textarea id="thesis-note" v-model="note" rows="4" maxlength="500" aria-describedby="draft-note" placeholder="Record a trigger, an open question, or a reason to wait…"></textarea><p id="draft-note" class="draft-note"><span>{{ current.symbol }} · {{ note.length }}/500</span><span>Until you leave this page</span></p><div class="save-context"><span>{{ scenario.label }} case</span><span>{{ weight }}% position</span></div><button class="save-button" :disabled="isSaved || !!journalError" @click="saveThesis"><Check v-if="isSaved" :size="16" /><Bookmark v-else :size="16" />{{ isSaved ? 'Saved to journal' : revisitedEntry ? 'Save revised thesis' : 'Save thesis' }}<ArrowRight v-if="!isSaved" :size="15" /></button><button v-if="isSaved" id="saved-journal-link" class="saved-journal-link inline-button" @click="openSavedJournal">View saved entry <ArrowRight :size="15" /></button><p class="local-storage-note"><ShieldCheck :size="13" /> On this device · Unencrypted</p></section>
      </aside>
    </div>

    <div v-if="notice || journalError" class="desk-feedback"><p v-if="notice" role="status"><Check :size="16" />{{ notice }}</p><div v-if="journalError" class="storage-error" role="alert"><span>{{ journalError }}</span><button class="inline-button" @click="loadJournal">Retry storage <RotateCcw :size="14" /></button></div></div>

    <section v-if="journalOpen" id="local-journal" class="local-journal" aria-labelledby="local-journal-title" @keydown.esc.stop.prevent="toggleJournal">
      <div class="journal-heading"><div><p class="small-heading">DECISION HISTORY</p><h4 id="local-journal-title" ref="journalHeading" tabindex="-1">My journal <span>{{ journal.length }}</span></h4></div><div class="journal-actions"><button class="quiet-button" :disabled="!journal.length" @click="exportJournal"><Download :size="15" /> Export JSON</button><button class="journal-close" aria-label="Close journal" @click="toggleJournal"><X :size="18" /></button></div></div>
      <p class="journal-disclosure">Saved locally in this browser, unencrypted. No cloud sync or onchain proof. Avoid sensitive information and export a copy before clearing browser data.</p>
      <div v-if="journal.length" class="journal-filters"><label class="journal-search" for="journal-search"><Search :size="16" aria-hidden="true" /><input id="journal-search" v-model="journalQuery" type="search" placeholder="Search decisions" aria-label="Search journal" /></label><label class="journal-asset-filter">Asset<select v-model="journalAsset" aria-label="Filter journal by asset"><option value="all">All assets</option><option v-for="asset in assets" :key="asset.symbol" :value="asset.symbol">{{ asset.symbol }}</option></select></label><span class="journal-filter-count" role="status">{{ filteredJournal.length }} of {{ journal.length }} entries</span></div>
      <div v-if="lastDeleted" class="undo-row"><span>Last journal entry removed.</span><button id="journal-undo" class="inline-button" :disabled="!!journalError" @click="undoDelete"><Undo2 :size="14" /> Undo deletion</button></div>
      <div v-if="journalError && !journal.length" class="journal-empty"><BookOpen :size="27" /><h5>Your saved journal is unavailable.</h5><p>Retry storage to recover your entries. Existing data has not been changed.</p><button class="inline-button" @click="loadJournal">Retry storage <RotateCcw :size="14" /></button></div>
      <div v-else-if="!journal.length" class="journal-empty"><span class="empty-icon"><BookOpen :size="27" /></span><h5>Your next decision starts here.</h5><p>Choose an asset, explore a scenario, and save your reasoning.</p><button class="inline-button" @click="focusDecisionNote">Write your first note <ArrowRight :size="16" /></button></div>
      <div v-else-if="!filteredJournal.length" class="journal-empty"><Search :size="27" /><h5>No matching decisions.</h5><p>Try another asset or a word from your notes.</p><button class="inline-button" @click="clearJournalFilters">Clear journal filters</button></div>
      <ol v-else class="journal-entries"><li v-for="entry in filteredJournal" :key="entry.id"><div class="entry-heading"><div><strong>{{ entry.symbol }}</strong><span>{{ entry.scenario }} case · {{ entry.weight }}% position</span></div><time :datetime="new Date(entry.savedAt).toISOString()">{{ formatDate(entry.savedAt) }}</time></div><p>{{ entry.thesis }}</p><p v-if="entry.note" class="entry-note"><strong>Your note</strong>{{ entry.note }}</p><div class="entry-footer"><button class="revisit-entry quiet-button" :aria-label="`Revisit ${entry.symbol} decision from ${formatDate(entry.savedAt)}`" @click="revisitDecision(entry)"><RotateCcw :size="14" /> Revisit decision</button><button class="delete-entry" :aria-label="`Delete ${entry.symbol} journal entry from ${formatDate(entry.savedAt)}`" :disabled="!!journalError" @click="deleteEntry(entry)"><Trash2 :size="14" /> Delete</button></div><p class="entry-disclosure">SAVED SNAPSHOT · SAMPLE DATA · LOCAL COPY</p></li></ol>
    </section>
    <footer class="desk-footer"><span><span class="preview-dot" aria-hidden="true"></span>PRODUCT PREVIEW · SAMPLE DATA</span><span>Research, scenario testing, and a record of your reasoning.</span></footer>
  </div>
</template>

<style scoped>
.research-desk { --desk-bg: var(--paper, #0b111b); --desk-panel: var(--surface, #121c2b); --desk-panel-raised: var(--surface-2, #192639); --desk-line: var(--line, #263247); --desk-ink: var(--ink, #edf3f8); --desk-muted: var(--muted, #a5b1c2); --desk-lime: var(--accent, #c4f06a); --desk-blue: var(--blue, #8fb9ff); --desk-red: #f39a9f; --desk-mono: var(--mono, Consolas, "Courier New", monospace); color: var(--desk-ink); background: var(--desk-bg); border: 1px solid var(--desk-line); border-radius: 12px; container: research / inline-size; font-family: var(--sans, "Segoe UI", Arial, sans-serif); font-size: 13px; text-align: left; }
.research-desk *, .research-desk *::before, .research-desk *::after { box-sizing: border-box; }
.research-desk h3, .research-desk h4, .research-desk h5, .research-desk p, .research-desk figure { margin: 0; }
.research-desk button, .research-desk input, .research-desk textarea, .research-desk select { font: inherit; }
.research-desk button { cursor: pointer; }
.research-desk button:disabled { cursor: not-allowed; opacity: .55; }
.research-desk button, .research-desk a, .research-desk input, .research-desk textarea, .research-desk select { -webkit-tap-highlight-color: transparent; }
.research-desk :focus-visible { outline: 2px solid var(--desk-blue); outline-offset: 4px; }
.research-desk button, .research-desk a { transition: background .16s, color .16s, border-color .16s; }
.research-desk svg { flex-shrink: 0; }
.desk-header { display: flex; justify-content: space-between; align-items: center; gap: 16px; padding: 16px 20px; background: var(--desk-panel); border-bottom: 1px solid var(--desk-line); border-radius: 12px 12px 0 0; }
.desk-title { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.desk-title h3 { font-size: 14px; font-weight: 600; letter-spacing: -.15px; }
.desk-indicator { width: 8px; height: 8px; background: var(--desk-lime); box-shadow: 0 0 0 4px #c4f06a0a; border-radius: 2px; }
.small-heading { display: inline-flex; align-items: center; gap: 7px; color: var(--desk-muted); font: 10px/1.5 var(--desk-mono); letter-spacing: .75px; }
.sample-tag { display: inline-block; padding: 3px 5px; border: 1px solid var(--desk-line); border-radius: 3px; color: var(--desk-muted); font: 8px/1.3 var(--desk-mono); letter-spacing: .5px; white-space: nowrap; }
.quiet-button, .save-button, .inline-button, .next-step { display: inline-flex; align-items: center; justify-content: center; gap: 8px; min-height: 40px; border: 1px solid var(--desk-line); border-radius: 5px; padding: 9px 12px; background: transparent; color: var(--desk-ink); font-size: 11px !important; font-weight: 500 !important; }
.quiet-button:hover:not(:disabled) { background: var(--desk-panel-raised); border-color: #44516a; }
.count { display: inline-flex; align-items: center; justify-content: center; min-width: 21px; height: 20px; padding: 0 4px; background: var(--desk-panel-raised); color: var(--desk-lime); border-radius: 3px; font: 10px var(--desk-mono); }
.workspace-grid { display: grid; grid-template-columns: 172px minmax(0, 1fr) 270px; align-items: stretch; }
.asset-index { padding: 22px 12px; background: #0e1724; border-right: 1px solid var(--desk-line); min-width: 0; }
.index-label { display: flex; align-items: center; justify-content: space-between; padding: 0 5px; }
.asset-count { color: #728399; font: 10px var(--desk-mono); }
.asset-search { display: flex; align-items: center; gap: 6px; padding: 0 9px; min-height: 38px; border: 1px solid var(--desk-line); border-radius: 5px; color: var(--desk-muted); margin-top: 16px; background: var(--desk-bg); }
.asset-search input { width: 100%; min-width: 0; height: 36px; padding: 0; border: 0; background: transparent; color: var(--desk-ink); font-size: 11px; }
.asset-search input:focus { outline: none; }
.asset-search:focus-within { outline: 2px solid var(--desk-blue); outline-offset: 2px; }
.asset-search button { display: grid; place-items: center; width: 24px; min-width: 24px; height: 30px; padding: 0; border: 0; background: transparent; color: var(--desk-muted); }
.asset-list { display: flex; flex-direction: column; gap: 7px; margin-top: 15px; }
.asset-row { display: flex; align-items: center; justify-content: space-between; gap: 8px; width: 100%; min-height: 72px; padding: 12px 9px; border: 1px solid transparent; border-radius: 5px; color: var(--desk-ink); background: transparent; text-align: left; }
.asset-row:hover { background: var(--desk-panel-raised); }
.asset-row.selected { border-color: #c4f06a40; background: #c4f06a0a; box-shadow: inset 2px 0 var(--desk-lime); }
.asset-name, .asset-quote { display: flex; flex-direction: column; gap: 7px; }
.asset-name strong { font-size: 12px; font-weight: 600; letter-spacing: .2px; }
.asset-name small { font-size: 10px; color: var(--desk-muted); }
.asset-quote { align-items: flex-end; font-family: var(--desk-mono); }
.asset-quote strong { font-size: 11px; font-weight: 400; }
.asset-quote small { display: flex; align-items: center; gap: 2px; font-size: 9px; }
.positive { color: var(--desk-lime); }
.negative { color: var(--desk-red); }
.watchlist-caption { margin: 14px 5px 0 !important; color: #8795a7; font-size: 9px; }
.workspace-guide { border-top: 1px solid var(--desk-line); margin-top: 30px; padding: 22px 5px 0; }
.workspace-guide .small-heading { font-size: 8px; letter-spacing: .4px; }
.workspace-guide ol { list-style: none; padding: 0; margin: 16px 0; display: grid; gap: 17px; }
.workspace-guide li { display: flex; align-items: center; gap: 10px; color: var(--desk-muted); font-size: 10px; }
.workspace-guide li span { color: var(--desk-lime); font: 9px var(--desk-mono); }
.workspace-guide p { color: #8795a7; font-size: 10px; line-height: 1.8; }
.search-empty { padding: 18px 4px; color: var(--desk-muted); font-size: 11px; }
.search-empty .inline-button { padding-left: 0; }
.research-main { min-width: 0; }
.asset-heading { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 25px 24px 20px; }
.asset-title-group .small-heading { font-family: inherit; font-size: 11px; letter-spacing: 0; }
.asset-title-group .small-heading span { color: #7e8fa4; font: 8px var(--desk-mono); letter-spacing: .3px; }
.asset-title-group h3 { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; margin-top: 9px; font-size: 31px; font-weight: 600; letter-spacing: -1px; scroll-margin-top: 100px; }
.signal-status { padding: 4px 7px; background: #c4f06a10; border: 1px solid #c4f06a30; border-radius: 3px; color: var(--desk-lime); font: 9px var(--desk-mono); letter-spacing: 0; }
.signal-status.watch { color: var(--desk-blue); border-color: #8fb9ff30; background: #8fb9ff10; }
.signal-status.caution { color: #e9be78; border-color: #e9be7830; background: #e9be7810; }
.main-price { text-align: right; flex-shrink: 0; }
.main-price > strong { display: block; font: 24px var(--desk-mono); letter-spacing: -1px; }
.main-price > small { display: block; margin-top: 8px; font: 10px var(--desk-mono); }
.main-price small span { color: var(--desk-muted); font: 9px "Segoe UI", Arial, sans-serif; margin-left: 3px; }
.projection-map { padding: 4px 24px 17px; }
.chart-topline { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.chart-topline > div > span:last-child { display: block; margin-top: 5px; font-size: 10px; color: #8291a5; }
.chart-topline .small-heading { color: var(--desk-ink); font-size: 9px; }
.chart-period { padding: 5px 8px; border: 1px solid var(--desk-line); border-radius: 3px; color: var(--desk-muted); font: 9px var(--desk-mono); white-space: nowrap; }
.projection-svg { display: block; width: 100%; height: auto; margin: 13px 0 5px; overflow: visible; }
.chart-grid line { stroke: var(--desk-line); stroke-width: .7; stroke-dasharray: 2 5; }
.chart-baseline { stroke: #5b6b80; stroke-width: 1; stroke-dasharray: 4 5; }
.projection-line line { stroke-width: 1.6; stroke-dasharray: 5 5; opacity: .48; }
.projection-line.active line { stroke-width: 2.5; stroke-dasharray: none; opacity: 1; }
.projection-line.bear { stroke: var(--desk-red); fill: var(--desk-red); }
.projection-line.base { stroke: var(--desk-blue); fill: var(--desk-blue); }
.projection-line.bull { stroke: var(--desk-lime); fill: var(--desk-lime); }
.projection-line text { font: 10px var(--desk-mono); stroke: none; }
.projection-line circle { stroke-width: 5; stroke-opacity: .12; }
.chart-origin { fill: var(--desk-ink); stroke: var(--desk-bg); stroke-width: 2; }
.chart-label { fill: #8c9bae; font: 8px var(--desk-mono); letter-spacing: .5px; }
.chart-legend { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 7px; }
.chart-legend button { display: flex; align-items: center; justify-content: center; gap: 5px; min-height: 36px; padding: 7px 4px; border: 1px solid var(--desk-line); border-radius: 4px; color: var(--desk-muted); background: #101a28; font-size: 10px; white-space: nowrap; }
.chart-legend button:hover { border-color: #687c94; }
.chart-legend button.selected { background: #1b293b; border-color: #758ca5; color: var(--desk-ink); }
.chart-legend strong { margin-left: 2px; font: 10px var(--desk-mono); }
.legend-dot { width: 5px; height: 5px; border-radius: 50%; background: var(--desk-blue); }
.bear .legend-dot { background: var(--desk-red); }
.bull .legend-dot { background: var(--desk-lime); }
.chart-disclosure { margin-top: 10px !important; color: #8e9bae; font-size: 9px; line-height: 1.7; }
.research-tabs { display: flex; padding: 0 24px; gap: 22px; border-block: 1px solid var(--desk-line); background: #0e1723; }
.research-tabs button { display: flex; align-items: center; gap: 7px; position: relative; min-height: 47px; padding: 10px 2px; border: 0; background: transparent; color: var(--desk-muted); font-size: 12px; }
.research-tabs button.selected { color: var(--desk-lime); }
.research-tabs button.selected::after { content: ""; position: absolute; bottom: -1px; left: 0; right: 0; height: 2px; background: var(--desk-lime); }
.research-tabs button:hover { color: var(--desk-ink); }
.research-panel { padding: 23px 24px; outline-offset: -4px !important; min-height: 362px; }
.card-heading { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.card-heading h4 { display: flex; align-items: center; gap: 7px; font-size: 13px; font-weight: 600; }
.thesis-copy { margin-top: 13px !important; font-size: 14px; line-height: 1.85; color: #dde6f1; }
.counter-case { display: flex; align-items: start; gap: 11px; padding: 15px; margin-top: 19px; border-left: 2px solid #8fb9ff; background: #8fb9ff08; border-radius: 0 5px 5px 0; }
.counter-icon { color: var(--desk-blue); font: 19px var(--desk-mono); }
.counter-case h4 { color: var(--desk-blue); font-size: 11px; font-weight: 500; }
.counter-case p { margin-top: 6px; color: var(--desk-muted); font-size: 11px; line-height: 1.8; }
.evidence-summary { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-top: 20px; }
.signal-score { display: flex; align-items: center; gap: 11px; flex: 1; }
.signal-score > strong { color: var(--desk-lime); font: 23px var(--desk-mono); white-space: nowrap; }
.signal-score > strong small { color: var(--desk-muted); font-size: 10px; }
.signal-score > div { width: 160px; }
.signal-score > div > span { font-size: 9px; color: var(--desk-muted); }
.signal-track { width: 100%; height: 3px; margin-top: 8px; background: var(--desk-line); border-radius: 2px; }
.signal-track i { display: block; height: 100%; background: var(--desk-lime); border-radius: 2px; }
.evidence-button { display: flex; align-items: center; justify-content: center; gap: 6px; min-height: 36px; padding: 4px 0 4px 5px; color: var(--desk-muted); background: transparent; border: 0; font-size: 10px !important; white-space: nowrap; }
.rotated { transform: rotate(180deg); }
.evidence-detail { border: 1px solid var(--desk-line); border-radius: 5px; padding: 15px; margin-top: 14px; font-size: 11px; background: var(--desk-panel); }
.evidence-detail strong { font-weight: 600; }
.evidence-detail p { line-height: 1.8; color: var(--desk-muted); margin-top: 7px; }
.inline-button, .next-step { padding-inline: 0; border-color: transparent; color: var(--desk-lime); }
.inline-button:hover:not(:disabled), .next-step:hover { color: #e3ffae; text-decoration: underline; text-underline-offset: 4px; }
.next-step { margin-top: 13px; gap: 12px; font-size: 11px !important; }
.panel-introduction h4 { font-size: 17px; font-weight: 500; letter-spacing: -.3px; }
.panel-introduction p { margin-top: 9px; color: var(--desk-muted); font-size: 11px; line-height: 1.8; }
.source-ledger { margin-top: 16px; }
.source-record { display: flex; gap: 12px; padding: 16px 0; border-bottom: 1px solid var(--desk-line); color: var(--desk-ink); text-decoration: none; }
.source-icon { display: grid; place-items: center; width: 34px; height: 34px; border: 1px solid var(--desk-line); border-radius: 4px; color: var(--desk-blue); flex-shrink: 0; }
.source-record > div { min-width: 0; }
.source-record strong { display: flex; align-items: center; gap: 7px; font-weight: 500; font-size: 11px; line-height: 1.6; }
.source-record p { margin-top: 4px; color: var(--desk-muted); font-size: 10px; line-height: 1.7; }
.source-record small { display: block; color: #8090a7; font: 8px/1.5 var(--desk-mono); letter-spacing: .5px; margin-top: 6px; }
.source-link:hover { background: #8fb9ff08; }
.source-link:hover strong { color: var(--desk-blue); }
.scenario-choices { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 9px; margin-top: 20px; }
.scenario-choices button { display: flex; flex-direction: column; min-width: 0; padding: 13px 10px; border: 1px solid var(--desk-line); border-radius: 5px; background: var(--desk-panel); color: var(--desk-ink); text-align: left; }
.scenario-choices button:hover { border-color: #65758c; }
.scenario-choices button.selected { border-color: var(--desk-lime); background: #c4f06a08; }
.scenario-choices button > span:first-child { display: flex; width: 100%; align-items: center; justify-content: space-between; gap: 5px; color: var(--desk-muted); font-size: 11px; }
.scenario-choices button.selected > span:first-child { color: var(--desk-lime); }
.scenario-choices strong { display: block; margin-top: 14px; font: 24px var(--desk-mono); letter-spacing: -1px; }
.scenario-choices small { display: block; margin-top: 8px; color: var(--desk-muted); font-size: 10px; line-height: 1.7; flex: 1; }
.case-price { display: block; margin-top: 13px; padding-top: 10px; border-top: 1px solid var(--desk-line); width: 100%; color: var(--desk-muted); font: 11px var(--desk-mono); }
.scenario-result { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-top: 22px; }
.scenario-result .small-heading { font-size: 8px; }
.scenario-result p { margin-top: 6px; color: var(--desk-muted); font-size: 11px; }
.scenario-result > strong { font: 28px var(--desk-mono); letter-spacing: -1px; color: var(--desk-lime); }
.scenario-metrics { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; margin-top: 18px; padding-top: 16px; border-top: 1px solid var(--desk-line); }
.scenario-metrics span { display: block; color: var(--desk-muted); font-size: 9px; }
.scenario-metrics strong { display: block; margin-top: 7px; font: 14px var(--desk-mono); }
.assumption-note { margin-top: 18px !important; color: #8e9bae; font-size: 9px; line-height: 1.8; }
.decision-sidebar { min-width: 0; border-left: 1px solid var(--desk-line); background: #101927; }
.risk-sidebar { padding: 23px 18px 20px; }
.risk-sidebar .card-heading { flex-wrap: wrap; }
.risk-intro { margin-top: 11px !important; color: var(--desk-muted); font-size: 11px; line-height: 1.8; }
.compact-scenarios { border: 0; margin: 19px 0; padding: 0; min-width: 0; }
.compact-scenarios legend { padding: 0; margin-bottom: 9px; color: var(--desk-muted); font-size: 11px; }
.compact-scenarios > div { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); padding: 3px; gap: 3px; border: 1px solid var(--desk-line); border-radius: 5px; background: var(--desk-bg); }
.compact-scenarios button { border: 1px solid transparent; border-radius: 3px; padding: 7px 5px; min-height: 34px; color: var(--desk-muted); background: transparent; font-size: 10px; }
.compact-scenarios button.selected { border-color: #c4f06a35; background: #c4f06a12; color: var(--desk-lime); }
.compact-scenarios button:hover:not(.selected) { background: var(--desk-panel-raised); }
.weight-label { display: flex; align-items: center; justify-content: space-between; gap: 12px; color: var(--desk-muted); font-size: 11px; }
.weight-label output { color: var(--desk-ink); font: 16px var(--desk-mono); }
.risk-sidebar input[type="range"] { display: block; width: 100%; height: 35px; margin: 3px 0 0; accent-color: var(--desk-lime); cursor: pointer; }
.range-ends, .stress-scale { display: flex; align-items: center; justify-content: space-between; gap: 10px; color: #8e9bae; font: 8px var(--desk-mono); }
.stress-result { padding-top: 18px; border-top: 1px solid var(--desk-line); margin-top: 23px; }
.stress-result > span { color: var(--desk-muted); font-size: 11px; }
.stress-result strong { display: block; margin-top: 8px; font: 35px var(--desk-mono); letter-spacing: -1.5px; color: var(--desk-red); }
.stress-result strong small { font-size: 21px; margin-left: 3px; }
.stress-result p { margin-top: 8px; font-size: 9px; color: var(--desk-muted); }
.stress-gauge { margin-top: 13px; height: 4px; background: var(--desk-line); border-radius: 2px; overflow: hidden; }
.stress-gauge i { display: block; height: 100%; background: var(--desk-red); }
.stress-scale { margin-top: 7px; }
.risk-footnote { margin-top: 14px !important; color: #8e9bae; font-size: 9px; line-height: 1.8; }
.save-area { padding: 22px 18px; border-top: 1px solid var(--desk-line); }
.draft-status { font: 8px var(--desk-mono); color: #8fa2b9; }
.save-area label { display: block; margin-top: 17px; color: var(--desk-muted); font-size: 10px; line-height: 1.8; }
.save-area label > span { display: block; color: #8290a4; font-size: 9px; }
.save-area textarea { display: block; width: 100%; min-height: 127px; max-height: 350px; padding: 12px; border: 1px solid #344259; border-radius: 5px; margin: 9px 0; resize: vertical; background: var(--desk-bg); color: var(--desk-ink); font-size: 11px; line-height: 1.8; scroll-margin-top: 110px; }
.research-desk input::placeholder, .research-desk textarea::placeholder { color: #91a0b3; opacity: 1; }
.draft-note { display: flex; align-items: center; justify-content: space-between; gap: 8px; font: 8px/1.6 var(--desk-mono); color: #8b9bb0; }
.draft-note span:last-child { font-family: "Segoe UI", Arial, sans-serif; font-size: 8px; text-align: right; }
.save-context { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin: 20px 0 10px; font: 9px var(--desk-mono); color: var(--desk-muted); }
.save-button { width: 100%; min-height: 42px; border-color: var(--desk-lime); background: var(--desk-lime); color: #14210a; font-weight: 600 !important; }
.save-button > svg:last-child:not(:first-child) { margin-left: auto; }
.save-button:hover:not(:disabled) { background: #d5ff83; border-color: #d5ff83; }
.save-button:disabled { opacity: 1; color: var(--desk-muted); background: var(--desk-panel-raised); border-color: #34445d; }
.saved-journal-link { display: flex; width: 100%; margin-top: 5px; }
.local-storage-note { display: flex; align-items: center; justify-content: center; gap: 6px; margin-top: 12px !important; font-size: 9px; color: #8c9bb0; }
.revisit-banner { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding: 13px 24px; border-block: 1px solid #8fb9ff30; background: #8fb9ff09; color: var(--desk-blue); }
.revisit-banner > div { flex: 1; min-width: 180px; }
.revisit-banner strong { font-weight: 500; font-size: 11px; }
.revisit-banner p { color: var(--desk-muted); margin-top: 4px; font-size: 10px; line-height: 1.6; }
.revisit-banner .inline-button { color: var(--desk-blue); font-size: 10px !important; }
.desk-feedback { padding: 14px 22px; border-top: 1px solid var(--desk-line); background: #c4f06a09; color: var(--desk-lime); font-size: 12px; line-height: 1.8; }
.desk-feedback > p { display: flex; align-items: center; gap: 9px; }
.storage-error { display: flex; align-items: center; justify-content: space-between; gap: 18px; color: var(--desk-red); }
.storage-error > span { flex: 1; }
.storage-error .inline-button { color: var(--desk-red); white-space: nowrap; }
.local-journal { padding: 27px 24px; border-top: 1px solid var(--desk-line); background: #101926; scroll-margin-top: 90px; }
.journal-heading { display: flex; align-items: center; justify-content: space-between; gap: 18px; }
.journal-heading h4 { display: flex; align-items: center; gap: 10px; margin-top: 6px; font-size: 24px; font-weight: 500; letter-spacing: -.6px; scroll-margin-top: 100px; }
.journal-heading h4 span { display: grid; place-items: center; min-width: 25px; height: 23px; padding: 0 5px; border: 1px solid var(--desk-line); border-radius: 4px; color: var(--desk-muted); font: 11px var(--desk-mono); }
.journal-actions { display: flex; align-items: center; gap: 8px; }
.journal-close { display: grid; place-items: center; min-width: 40px; min-height: 40px; border: 1px solid var(--desk-line); border-radius: 5px; background: transparent; color: var(--desk-muted); }
.journal-close:hover { color: var(--desk-ink); background: var(--desk-panel-raised); }
.journal-disclosure { margin-top: 13px !important; max-width: 790px; color: var(--desk-muted); font-size: 11px; line-height: 1.8; }
.journal-filters { display: flex; align-items: center; flex-wrap: wrap; gap: 14px; margin-top: 21px; padding: 16px 0; border-block: 1px solid var(--desk-line); }
.journal-search { display: flex; align-items: center; gap: 9px; flex: 1; min-width: 200px; padding: 0 12px; background: var(--desk-bg); border: 1px solid #344259; border-radius: 5px; color: var(--desk-muted); }
.journal-search input { width: 100%; min-width: 0; min-height: 40px; padding: 10px 0; border: 0; background: transparent; color: var(--desk-ink); font-size: 11px; }
.journal-search:focus-within { outline: 2px solid var(--desk-blue); outline-offset: 2px; }
.journal-search input:focus { outline: none; }
.journal-asset-filter { display: flex; align-items: center; gap: 8px; color: var(--desk-muted); font-size: 11px; }
.journal-asset-filter select { min-height: 40px; padding: 7px 25px 7px 10px; color: var(--desk-ink); background: var(--desk-bg); border: 1px solid #344259; border-radius: 5px; font-size: 11px; }
.journal-filter-count { margin-left: auto; color: var(--desk-muted); font: 9px var(--desk-mono); }
.undo-row { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; padding: 8px 14px; border: 1px solid #c4f06a35; border-radius: 5px; background: #c4f06a08; margin-top: 16px; color: var(--desk-lime); font-size: 11px; }
.journal-empty { display: flex; flex-direction: column; align-items: center; padding: 45px 10px 28px; color: var(--desk-muted); text-align: center; }
.empty-icon { display: grid; place-items: center; width: 58px; height: 58px; border: 1px solid var(--desk-line); border-radius: 10px; color: var(--desk-lime); background: var(--desk-bg); }
.journal-empty h5 { margin-top: 19px; color: var(--desk-ink); font-size: 20px; font-weight: 500; letter-spacing: -.3px; }
.journal-empty p { margin-top: 10px; font-size: 12px; line-height: 1.8; }
.journal-empty .inline-button { margin-top: 12px; }
.journal-entries { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 15px; list-style: none; padding: 0; margin: 21px 0 0; }
.journal-entries li { min-width: 0; padding: 19px; border: 1px solid var(--desk-line); border-radius: 7px; background: var(--desk-bg); overflow-wrap: anywhere; }
.entry-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; }
.entry-heading strong { font-size: 16px; font-weight: 600; letter-spacing: .2px; }
.entry-heading span { display: block; margin-top: 6px; color: var(--desk-muted); font-size: 10px; text-transform: capitalize; }
.entry-heading time { color: #8f9eb1; font: 9px/1.8 var(--desk-mono); text-align: right; }
.journal-entries li > p { margin-top: 16px; color: var(--desk-muted); font-size: 11px; line-height: 1.8; }
.journal-entries li > p.entry-note { padding: 12px; border-left: 2px solid var(--desk-blue); border-radius: 0 4px 4px 0; color: var(--desk-ink); background: #8fb9ff09; white-space: pre-wrap; }
.entry-note strong { display: block; margin-bottom: 5px; color: var(--desk-blue); font: 8px var(--desk-mono); text-transform: uppercase; letter-spacing: .5px; }
.entry-footer { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: 17px; }
.revisit-entry { min-height: 36px; padding: 8px 10px; font-size: 10px !important; }
.delete-entry { display: inline-flex; align-items: center; gap: 5px; padding: 8px 5px; min-height: 36px; border: 1px solid transparent; border-radius: 4px; color: var(--desk-red); background: transparent; font-size: 10px !important; }
.delete-entry:hover:not(:disabled) { background: #f39a9f10; }
.journal-entries li > .entry-disclosure { margin-top: 12px; color: #8595aa; font: 8px/1.8 var(--desk-mono); letter-spacing: .3px; }
.desk-footer { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; padding: 14px 20px; border-top: 1px solid var(--desk-line); border-radius: 0 0 12px 12px; background: var(--desk-panel); color: #8c9bb0; font: 8px/1.8 var(--desk-mono); }
.desk-footer > span:first-child { display: inline-flex; align-items: center; gap: 7px; }
.desk-footer > span:last-child { font-family: "Segoe UI", Arial, sans-serif; font-size: 10px; }
.preview-dot { width: 5px; height: 5px; border-radius: 50%; background: var(--desk-muted); }
@container research (max-width: 1050px) {
  .workspace-grid { grid-template-columns: 155px minmax(0, 1fr) 250px; }
  .asset-index { padding-inline: 10px; }
  .asset-heading, .projection-map, .research-panel { padding-inline: 20px; }
  .research-tabs { padding-inline: 20px; }
  .risk-sidebar, .save-area { padding-inline: 15px; }
  .chart-legend button { flex-wrap: wrap; column-gap: 4px; }
  .chart-legend strong { font-size: 9px; }
  .evidence-summary { flex-wrap: wrap; gap: 8px; }
  .signal-score { min-width: 150px; }
}
@container research (max-width: 940px) {
  .workspace-grid { grid-template-columns: 165px minmax(0, 1fr); }
  .decision-sidebar { grid-column: 1 / -1; border-top: 1px solid var(--desk-line); border-left: 0; display: grid; grid-template-columns: 1fr 1fr; }
  .risk-sidebar, .save-area { padding: 24px; }
  .save-area { border-top: 0; border-left: 1px solid var(--desk-line); }
  .research-panel { min-height: 0; }
  .risk-sidebar .card-heading { flex-wrap: nowrap; }
  .compact-scenarios { margin-block: 15px; }
  .stress-result { margin-top: 18px; padding-top: 15px; }
  .risk-footnote { max-width: 390px; }
  .save-area label { margin-top: 21px; }
  .save-area textarea { min-height: 149px; }
  .chart-legend button { flex-wrap: nowrap; }
  .chart-legend strong { font-size: 10px; }
}
@container research (max-width: 700px) {
  .workspace-grid { grid-template-columns: minmax(0, 1fr); }
  .asset-index { padding: 15px 20px; border-right: 0; border-bottom: 1px solid var(--desk-line); display: grid; grid-template-columns: 1fr 170px; gap: 12px; }
  .index-label { justify-content: flex-start; gap: 10px; padding: 0; }
  .asset-search { margin-top: 0; min-height: 34px; }
  .asset-search input { height: 32px; }
  .asset-list { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; grid-column: 1 / -1; margin-top: 0; }
  .asset-row { min-height: 65px; padding: 10px; gap: 6px; }
  .asset-name strong { font-size: 11px; }
  .asset-name small { font-size: 9px; }
  .asset-quote strong { font-size: 10px; }
  .asset-quote small { font-size: 8px; }
  .watchlist-caption { display: none; }
  .workspace-guide { display: none; }
  .search-empty { grid-column: 1 / -1; padding: 5px 0; display: flex; align-items: center; gap: 12px; }
  .asset-heading { padding-top: 24px; }
  .projection-svg { max-height: 255px; }
  .asset-heading, .projection-map, .research-panel { padding-inline: 24px; }
  .research-tabs { padding-inline: 24px; }
}
@container research (max-width: 540px) {

  .desk-header { padding: 14px 15px; gap: 9px; }
  .desk-title { gap: 8px; }
  .desk-title h3 { font-size: 12px; }
  .desk-title > .sample-tag { margin-left: 16px; font-size: 7px; }
  .journal-toggle { flex-shrink: 0; padding: 8px; font-size: 10px !important; gap: 6px; min-height: 44px; }
  .journal-toggle > svg { width: 14px; }
  .desk-title { max-width: 190px; }
  .asset-index { padding: 14px 15px; gap: 10px; grid-template-columns: 1fr 150px; }
  .asset-search { min-height: 46px; }
  .asset-search input { min-height: 44px; }
  .asset-search button { min-width: 44px; min-height: 44px; }
  .asset-list { display: flex; flex-direction: row; overflow-x: auto; padding: 2px 2px 8px; margin-inline: -2px; scrollbar-width: thin; scrollbar-color: #46556c transparent; }
  .asset-row { min-width: 134px; width: 134px; min-height: 66px; flex-shrink: 0; padding: 10px; border-color: var(--desk-line); }
  .asset-name strong { font-size: 12px; }
  .asset-quote strong { font-size: 11px; }
  .asset-quote small { font-size: 9px; }
  .search-empty { min-width: 100%; }
  .asset-heading { padding: 22px 17px 19px; gap: 12px; }
  .asset-title-group .small-heading { font-size: 10px; }
  .asset-title-group .small-heading span { display: none; }
  .asset-title-group h3 { font-size: 29px; gap: 8px; }
  .main-price > strong { font-size: 23px; }
  .main-price > small { font-size: 9px; }
  .main-price small span { display: block; margin-top: 5px; }
  .signal-status { padding: 4px 5px; font-size: 8px; }
  .projection-map { padding: 0 17px 16px; }
  .chart-topline .small-heading { font-size: 8px; }
  .chart-topline > div > span:last-child { font-size: 9px; }
  .chart-period { font-size: 8px; padding: 5px; }
  .projection-svg { margin-top: 15px; min-height: 138px; }
  .chart-legend { gap: 5px; }
  .chart-legend button { min-height: 44px; flex-wrap: wrap; padding: 7px 4px; font-size: 9px; gap: 3px; }
  .chart-legend button > svg { display: none; }
  .chart-legend strong { font-size: 9px; }
  .chart-disclosure { font-size: 9px; }
  .research-tabs { padding-inline: 17px; gap: 0; justify-content: space-between; }
  .research-tabs button { min-height: 48px; padding-inline: 7px; font-size: 12px; }
  .research-panel { padding: 22px 17px; }
  .thesis-copy { font-size: 13px; line-height: 1.9; }
  .counter-case { padding: 13px; }
  .evidence-summary { gap: 8px; }
  .signal-score { gap: 8px; }
  .signal-score > div { width: 110px; }
  .signal-score > div > span { font-size: 8px; }
  .evidence-button { font-size: 9px !important; min-height: 44px; }
  .next-step, .inline-button { min-height: 44px; }
  .panel-introduction h4 { font-size: 17px; }
  .scenario-choices { gap: 7px; }
  .scenario-choices button { padding: 12px 8px; }
  .scenario-choices strong { font-size: 23px; }
  .scenario-choices small { font-size: 9px; }
  .case-price { font-size: 10px; }
  .scenario-result > strong { font-size: 27px; }
  .decision-sidebar { grid-template-columns: 1fr; }
  .risk-sidebar, .save-area { padding: 24px 18px; }
  .save-area { border-left: 0; border-top: 1px solid var(--desk-line); }
  .risk-sidebar .card-heading h4, .save-area .card-heading h4 { font-size: 14px; }
  .compact-scenarios button { min-height: 44px; font-size: 12px; }
  .risk-sidebar input[type="range"] { min-height: 44px; }
  .weight-label, .risk-intro { font-size: 12px; }
  .weight-label output { font-size: 18px; }
  .stress-result { position: relative; padding-right: 80px; }
  .stress-result strong { position: absolute; top: 12px; right: 0; font-size: 32px; }
  .stress-result strong small { font-size: 17px; }
  .stress-result > span { font-size: 11px; }
  .stress-result p { font-size: 8px; }
  .risk-footnote { font-size: 10px; }
  .save-area label { font-size: 12px; display: flex; justify-content: space-between; align-items: center; gap: 10px; }
  .save-area label > span { font-size: 9px; }
  .save-area textarea { min-height: 135px; font-size: 12px; }
  .draft-note { font-size: 9px; }
  .draft-note span:last-child { font-size: 9px; }
  .save-button { min-height: 46px; font-size: 12px !important; }
  .save-context { font-size: 10px; }
  .local-storage-note { font-size: 10px; }
  .revisit-banner { padding: 14px 17px; }
  .revisit-banner .inline-button { margin-left: 27px; }
  .desk-feedback { padding: 14px 17px; font-size: 11px; }
  .storage-error { flex-wrap: wrap; gap: 2px; }
  .storage-error > span { flex-basis: 100%; }
  .local-journal { padding: 23px 17px; }
  .journal-heading { flex-wrap: wrap; gap: 15px; }
  .journal-heading h4 { font-size: 23px; }
  .journal-actions { margin-left: auto; }
  .journal-actions .quiet-button { min-height: 44px; padding: 9px; font-size: 10px !important; }
  .journal-close { min-height: 44px; min-width: 44px; }
  .journal-filters { gap: 12px; }
  .journal-search { min-width: 0; flex-basis: 100%; }
  .journal-search input { min-height: 44px; font-size: 12px; }
  .journal-asset-filter select { min-height: 44px; }
  .journal-filter-count { font-size: 8px; }
  .journal-entries { grid-template-columns: 1fr; gap: 12px; }
  .journal-entries li { padding: 15px; }
  .entry-heading time { font-size: 8px; }
  .entry-heading span { font-size: 9px; }
  .entry-footer { gap: 7px; flex-wrap: wrap; }
  .revisit-entry, .delete-entry { min-height: 44px; }
  .journal-empty h5 { font-size: 18px; }
  .journal-empty p { font-size: 11px; }
  .desk-footer { padding: 13px 17px; gap: 5px; }
  .desk-footer > span:last-child { font-size: 9px; }
}
@container research (max-width: 310px) {
  .desk-header { flex-wrap: wrap; }
  .desk-title { max-width: none; }
  .desk-title > .sample-tag { margin-left: 0; }
  .journal-toggle { margin-left: auto; }
  .asset-index { grid-template-columns: 1fr 137px; }
  .main-price > strong { font-size: 21px; }
  .asset-title-group h3 { font-size: 25px; }
  .scenario-choices { grid-template-columns: 1fr; }
  .scenario-choices button { display: grid; grid-template-columns: 1fr auto; column-gap: 12px; }
  .scenario-choices button > span:first-child { grid-column: 1; justify-content: flex-start; }
  .scenario-choices strong { grid-column: 2; grid-row: 1 / 3; margin-top: 0; align-self: center; }
  .scenario-choices small { grid-column: 1; margin-top: 5px; }
  .case-price { grid-column: 1 / -1; }
  .chart-legend button { flex-direction: column; }
  .chart-legend .legend-dot { display: none; }
  .stress-result { padding-right: 0; }
  .stress-result strong { position: static; margin-top: 9px; }
}
@media (prefers-reduced-motion: reduce) {
  .research-desk *, .research-desk *::before, .research-desk *::after { animation: none !important; transition: none !important; scroll-behavior: auto !important; }
}
</style>
