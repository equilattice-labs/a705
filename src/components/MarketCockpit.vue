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
defineExpose({ openJournal, goToTab });
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
        <span class="desk-icon" aria-hidden="true"
          ><SlidersHorizontal :size="23"
        /></span>
        <span
          >Decision workspace
          <small>{{ brand.name }} / RESEARCH PREVIEW</small></span
        >
      </div>
      <p class="desk-session">
        <span class="preview-dot"></span> Sample data <span>Local session</span>
      </p>
      <button
        ref="journalToggle"
        class="quiet-button journal-toggle"
        :aria-expanded="journalOpen"
        aria-controls="local-journal"
        @click="toggleJournal"
      >
        <BookOpen :size="16" /> My journal
        <span class="count">{{ journal.length }}</span>
      </button>
    </header>
    <div class="desk-grid">
      <aside class="watchlist" aria-label="Asset watchlist">
        <div class="small-heading">
          <span>ASSETS</span><span>{{ filteredAssets.length }} of 4</span>
        </div>
        <div class="asset-search">
          <Search :size="15" aria-hidden="true" /><input
            ref="searchInput"
            v-model="query"
            type="search"
            aria-label="Search assets"
            placeholder="Find an asset"
          /><button
            v-if="query"
            aria-label="Clear asset search"
            @click="clearSearch"
          >
            <X :size="14" />
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
            ><span class="asset-quote"
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
        </div>
        <div v-if="!filteredAssets.length" class="search-empty" role="status">
          <Search :size="20" />
          <p>No matching assets.</p>
          <button class="inline-button" @click="clearSearch">
            Clear search
          </button>
        </div>
        <p class="watchlist-note">
          Fixed sample prices in USD. Select an asset to examine its thesis.
        </p>
        <div class="desk-process">
          <span>YOUR WORKFLOW</span>
          <ol>
            <li><span>01</span> Build a view</li>
            <li><span>02</span> Challenge it</li>
            <li><span>03</span> Record the why</li>
          </ol>
          <p>Drafts stay with each asset while this page is open.</p>
        </div>
      </aside>
      <section class="research-main" aria-label="Selected asset research">
        <div class="asset-heading">
          <div>
            <p class="small-heading">{{ current.name }} / STOCK TOKEN</p>
            <h3 id="selected-asset-title" tabindex="-1">
              {{ current.symbol }}
              <span :class="['signal-status', current.status.toLowerCase()]">{{
                current.status
              }}</span>
            </h3>
          </div>
          <div class="main-price">
            ${{ current.price.toFixed(2)
            }}<small :class="current.change > 0 ? 'positive' : 'negative'"
              >{{ current.change > 0 ? "+" : ""
              }}{{ current.change.toFixed(2) }}% <span>sample</span></small
            >
          </div>
        </div>
        <div v-if="revisitedEntry" class="revisit-banner" role="status">
          <RotateCcw :size="16" />
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
            :aria-selected="activeTab === tab"
            :aria-controls="`research-panel-${tab.toLowerCase()}`"
            :tabindex="activeTab === tab ? 0 : -1"
            :class="{ selected: activeTab === tab }"
            @click="activeTab = tab"
          >
            <span class="tab-number" aria-hidden="true">{{ index + 1 }}</span
            >{{ tab }}
          </button>
        </div>
        <p class="research-guide">
          Read the thesis, inspect its sources, then test a scenario.
        </p>
        <div
          v-if="activeTab === 'Brief'"
          id="research-panel-brief"
          class="research-panel"
          role="tabpanel"
          aria-labelledby="research-tab-brief"
          tabindex="0"
        >
          <div class="brief-label">
            <FileText :size="16" /><span>THE WORKING THESIS</span
            ><span class="sample-tag">SAMPLE</span>
          </div>
          <p class="thesis-copy">{{ current.thesis }}</p>
          <div class="counter-case">
            <span>What could change the view</span>
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
          <button class="next-step" @click="goToTab('Sources')">
            Next: inspect sources <ArrowRight :size="16" />
          </button>
        </div>
        <div
          v-if="activeTab === 'Sources'"
          id="research-panel-sources"
          class="research-panel source-panel"
          role="tabpanel"
          aria-labelledby="research-tab-sources"
          tabindex="0"
        >
          <div class="brief-label">
            <BookOpen :size="16" /><span>SOURCE CONTEXT</span
            ><span class="sample-tag">PREVIEW</span>
          </div>
          <h4>Evidence should be inspectable.</h4>
          <p class="panel-copy">
            This demo contains no live research sources. The working thesis is
            sample copy; it has not been verified against issuer disclosures.
          </p>
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
                >Robinhood Chain documentation <ExternalLink :size="13"
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
                >Robinhood Chain explorer <ExternalLink :size="13"
              /></strong>
              <p>Inspect onchain activity independently.</p>
              <small>REFERENCE / NETWORK ONLY</small>
            </div></a
          >
          <button class="next-step" @click="goToTab('Scenario')">
            Next: test a scenario <ArrowRight :size="16" />
          </button>
        </div>
        <div
          v-if="activeTab === 'Scenario'"
          id="research-panel-scenario"
          class="research-panel"
          role="tabpanel"
          aria-labelledby="research-tab-scenario"
          tabindex="0"
        >
          <div class="brief-label">
            <SlidersHorizontal :size="16" /><span>SCENARIO LAB</span
            ><span class="sample-tag">30 DAYS</span>
          </div>
          <h4>Make the assumptions visible.</h4>
          <p class="panel-copy">
            Explore a hypothetical price move. Each case also carries a separate
            stress drawdown for sizing.
          </p>
          <div
            class="scenario-choices"
            role="group"
            aria-label="Market scenarios"
          >
            <button
              v-for="item in scenarios"
              :key="item.id"
              :class="{ selected: activeScenario === item.id }"
              :aria-pressed="activeScenario === item.id"
              @click="activeScenario = item.id"
            >
              <span>{{ item.label }} case</span
              ><strong>{{ item.move > 0 ? "+" : "" }}{{ item.move }}%</strong>
            </button>
          </div>
          <div class="scenario-result">
            <span>Hypothetical {{ current.symbol }} price</span
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
          <p class="assumption-note">
            Sample price × (1 + assumed move). These scenarios are neither
            forecasts nor probability estimates.
          </p>
        </div>
      </section>
      <aside class="risk-sidebar" aria-label="Risk simulator">
        <div class="small-heading">
          <span>RISK PARAMETERS</span><ShieldCheck :size="18" />
        </div>
        <h4>What is the downside?</h4>
        <p class="risk-intro">
          Explore how your {{ current.symbol }} position would affect the whole
          portfolio.
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
              {{ item.label }}
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
          <span>Portfolio stress impact</span
          ><strong>−{{ portfolioImpact }}<small>%</small></strong>
          <p>
            {{ weight }}% position × {{ scenario.drawdown }}% assumed drawdown
          </p>
          <div class="stress-gauge" aria-hidden="true">
            <i
              :style="{ width: `${(Number(portfolioImpact) / 12) * 100}%` }"
            ></i>
          </div>
          <div class="stress-scale">
            <span>0% portfolio stress</span><span>12%</span>
          </div>
        </div>
        <ul class="risk-checklist">
          <li><Check :size="14" />{{ scenario.label }} case selected</li>
          <li><Check :size="14" />Downside made explicit</li>
          <li><span class="hollow-dot"></span>No trade is submitted</li>
        </ul>
        <p class="risk-footnote">
          Illustrative sizing only. No leverage; excludes fees and slippage.
          This estimate does not enforce a loss limit.
        </p>
      </aside>
      <div class="save-area">
        <p class="save-heading">
          DECISION NOTE <span>03 / RECORD THE WHY</span>
        </p>
        <label for="thesis-note">Your decision note <span>optional</span></label
        ><textarea
          id="thesis-note"
          v-model="note"
          rows="2"
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
            >{{ scenario.label }} case · {{ weight }}% position<br />
            Saved on this device. Unencrypted.</small
          ><button
            class="save-button"
            :disabled="isSaved || !!journalError"
            @click="saveThesis"
          >
            <Check v-if="isSaved" :size="15" /><Bookmark v-else :size="15" />{{
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
      </div>
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
      <span><span class="preview-dot"></span> PRODUCT PREVIEW</span
      ><span>Research is a process. The decision is yours.</span>
    </footer>
  </div>
</template>

<style scoped>
.research-desk {
  --desk-positive: #bce69b;
  --desk-negative: #f3a593;
  color: var(--ink, #eef2ed);
  background: var(--surface, #191e22);
  border: 1px solid var(--line, #344039);
  border-radius: 14px;
  overflow: hidden;
  font: 14px/1.65 var(--sans, "Segoe UI", sans-serif);
  text-align: left;
  color-scheme: dark;
}
.research-desk *,
.research-desk *::before,
.research-desk *::after {
  box-sizing: border-box;
}
.research-desk button,
.research-desk input,
.research-desk textarea,
.research-desk select {
  font: inherit;
}
.research-desk button {
  cursor: pointer;
}
.research-desk button:focus-visible,
.research-desk input:focus-visible,
.research-desk textarea:focus-visible,
.research-desk select:focus-visible,
.research-desk a:focus-visible,
.research-desk [tabindex]:focus-visible {
  outline: 2px solid var(--accent, #cef576);
  outline-offset: 4px;
}
.research-desk button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}
.research-desk p,
.research-desk h3,
.research-desk h4,
.research-desk h5,
.research-desk figure {
  margin: 0;
}
.research-desk svg {
  flex-shrink: 0;
}
.desk-header {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 21px 24px;
  border-bottom: 1px solid var(--line, #344039);
}
.desk-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 600;
  letter-spacing: -0.4px;
}
.desk-icon {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  background: var(--sage, #273222);
  border: 1px solid #465c33;
  border-radius: 10px;
  color: var(--accent, #cef576);
}
.desk-title small {
  display: block;
  margin-top: 3px;
  color: var(--muted, #a7b2ab);
  font: 10px/1.6 var(--mono, Consolas, monospace);
  letter-spacing: 1px;
  text-transform: uppercase;
}
.desk-session {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto !important;
  color: var(--muted, #a7b2ab);
  font-size: 11px;
}
.desk-session > span:last-child {
  border-left: 1px solid var(--line, #344039);
  padding-left: 10px;
  margin-left: 3px;
}
.preview-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  background: var(--accent, #cef576);
  border-radius: 50%;
}
.quiet-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 44px;
  padding: 10px 13px;
  border: 1px solid #52604f;
  border-radius: 7px;
  color: var(--ink, #eef2ed);
  background: transparent;
  font-size: 12px !important;
  font-weight: 550 !important;
}
.quiet-button:hover:not(:disabled) {
  background: var(--sage, #273222);
  border-color: #859971;
}
.count {
  display: inline-grid;
  place-items: center;
  min-width: 23px;
  height: 23px;
  background: #303b2b;
  color: var(--accent, #cef576);
  border-radius: 5px;
  font: 11px var(--mono, Consolas, monospace);
}
.desk-grid {
  display: grid;
  grid-template-columns: 205px minmax(0, 1fr) 285px;
}
.watchlist {
  grid-column: 1;
  grid-row: 1 / 3;
  background: #151a1d;
  border-right: 1px solid var(--line, #344039);
  padding: 24px 14px;
  min-width: 0;
}
.small-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: var(--muted, #a7b2ab);
  font: 10px/1.7 var(--mono, Consolas, monospace);
  letter-spacing: 0.8px;
}
.watchlist > .small-heading {
  padding: 0 4px;
}
.watchlist > .small-heading > span:last-child {
  letter-spacing: 0;
}
.asset-search {
  display: flex;
  align-items: center;
  gap: 7px;
  min-height: 44px;
  padding: 0 10px;
  margin: 18px 0 15px;
  border: 1px solid #4a584f;
  border-radius: 6px;
  background: #101517;
  color: var(--muted, #a7b2ab);
}
.asset-search:focus-within {
  border-color: var(--accent, #cef576);
}
.asset-search input {
  min-width: 0;
  width: 100%;
  min-height: 44px;
  padding: 0;
  color: var(--ink, #eef2ed);
  background: transparent;
  border: 0;
  font-size: 12px;
}
.asset-search input::-webkit-search-cancel-button {
  display: none;
}
.asset-search input:focus-visible {
  outline-offset: 0;
}
.asset-search button {
  display: grid;
  place-items: center;
  flex: 0 0 44px;
  min-width: 44px;
  min-height: 44px;
  padding: 0;
  color: var(--muted, #a7b2ab);
  background: transparent;
  border: 0;
}
.asset-list {
  display: grid;
  gap: 7px;
}
.asset-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-width: 0;
  padding: 14px 10px;
  border: 1px solid transparent;
  border-radius: 6px;
  color: var(--ink, #eef2ed);
  background: transparent;
  text-align: left;
  transition:
    border-color 0.16s,
    background 0.16s;
}
.asset-row:hover {
  background: #222a27;
  border-color: #4c5b44;
}
.asset-row.selected {
  background: #273222;
  border-color: #52673a;
  box-shadow: inset 3px 0 var(--accent, #cef576);
}
.asset-name strong {
  display: block;
  font-size: 14px;
  letter-spacing: 0.1px;
}
.asset-name small {
  display: block;
  color: var(--muted, #a7b2ab);
  font-size: 11px;
  margin-top: 3px;
}
.asset-quote {
  text-align: right;
}
.asset-quote strong {
  display: block;
  font: 12px/1.6 var(--mono, Consolas, monospace);
}
.asset-quote small {
  display: flex;
  align-items: center;
  justify-content: end;
  gap: 2px;
  font: 10px/1.5 var(--mono, Consolas, monospace);
  margin-top: 5px;
}
.positive {
  color: var(--desk-positive);
}
.negative {
  color: var(--desk-negative);
}
.watchlist-note {
  color: var(--muted, #a7b2ab);
  font-size: 11px;
  line-height: 1.9;
  padding: 20px 4px;
}
.desk-process {
  margin-top: 34px;
  padding: 24px 4px 0;
  border-top: 1px solid var(--line, #344039);
}
.desk-process > span {
  font: 10px var(--mono, Consolas, monospace);
  letter-spacing: 0.8px;
  color: var(--muted, #a7b2ab);
}
.desk-process ol {
  list-style: none;
  padding: 0;
  margin: 19px 0;
  display: grid;
  gap: 17px;
}
.desk-process li {
  display: flex;
  gap: 10px;
  align-items: center;
  font-size: 12px;
}
.desk-process li span {
  color: var(--accent, #cef576);
  font: 10px var(--mono, Consolas, monospace);
}
.desk-process p {
  color: var(--muted, #a7b2ab);
  font-size: 11px;
  line-height: 1.9;
}
.search-empty {
  padding: 24px 6px;
  text-align: center;
  color: var(--muted, #a7b2ab);
  font-size: 12px;
}
.search-empty p {
  margin-top: 10px;
}
.research-main {
  grid-column: 2;
  grid-row: 1;
  min-width: 0;
  padding: 27px 28px 24px;
}
.asset-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding-bottom: 23px;
}
.asset-heading .small-heading {
  font-size: 10px;
  letter-spacing: 0.6px;
}
.asset-heading h3 {
  display: flex;
  align-items: center;
  gap: 12px;
  font: 600 34px/1.2 var(--sans, "Segoe UI", sans-serif);
  letter-spacing: -1px;
  margin-top: 7px;
  scroll-margin-top: 120px;
}
.signal-status {
  display: inline-flex;
  align-items: center;
  padding: 4px 7px;
  font-size: 10px;
  font-weight: 500;
  line-height: 1.6;
  letter-spacing: 0.2px;
  border: 1px solid #546647;
  border-radius: 4px;
  color: #d0e3b1;
  background: #2d3b28;
}
.signal-status.watch {
  color: #dce3cd;
  border-color: #566051;
  background: #30372b;
}
.signal-status.caution {
  color: #f3be98;
  border-color: #765641;
  background: #392c25;
}
.main-price {
  text-align: right;
  font: 23px/1.3 var(--mono, Consolas, monospace);
  letter-spacing: -0.8px;
}
.main-price small {
  display: block;
  margin-top: 7px;
  font: 11px/1.6 var(--mono, Consolas, monospace);
  letter-spacing: 0;
}
.main-price small span {
  color: var(--muted, #a7b2ab);
  padding-left: 3px;
}
.revisit-banner {
  display: flex;
  align-items: start;
  flex-wrap: wrap;
  gap: 10px;
  padding: 13px 15px;
  margin-bottom: 20px;
  background: #273222;
  border: 1px solid #52673a;
  border-radius: 6px;
  color: var(--accent, #cef576);
  font-size: 12px;
}
.revisit-banner p {
  flex: 1;
  min-width: 180px;
}
.revisit-banner button {
  padding-block: 7px;
  text-align: left;
}
.revisit-banner svg {
  margin-top: 2px;
}
.revisit-banner span {
  display: block;
  margin-top: 3px;
  color: #b9c8ad;
  font-size: 11px;
}
.research-tabs {
  display: flex;
  gap: 25px;
  border-bottom: 1px solid var(--line, #344039);
}
.research-tabs button {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-width: 44px;
  min-height: 48px;
  padding: 11px 0;
  border: 0;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--muted, #a7b2ab);
  font-size: 13px;
  scroll-margin-top: 120px;
}
.research-tabs button.selected {
  border-bottom-color: var(--accent, #cef576);
  color: var(--accent, #cef576);
}
.tab-number {
  font: 10px var(--mono, Consolas, monospace);
  color: #94a28f;
}
.selected .tab-number {
  color: var(--accent, #cef576);
}
.research-guide {
  color: var(--muted, #a7b2ab);
  font-size: 11px;
  line-height: 1.8;
  padding: 14px 0 24px;
}
.research-panel {
  min-height: 410px;
}
.brief-label {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--muted, #a7b2ab);
  font: 10px/1.7 var(--mono, Consolas, monospace);
  letter-spacing: 0.8px;
}
.research-desk .sample-tag {
  margin-left: auto;
  padding: 3px 6px;
  border: 1px solid #495743;
  border-radius: 3px;
  background: #2b3427;
  color: #b5c5aa;
  font: 9px/1.5 var(--mono, Consolas, monospace);
  white-space: nowrap;
}
.thesis-copy {
  font-size: 16px;
  line-height: 1.9;
  margin: 17px 0 22px !important;
}
.counter-case {
  background: #242a27;
  border: 1px solid #404b40;
  border-left: 3px solid #748561;
  border-radius: 3px;
  padding: 16px 17px;
}
.counter-case > span {
  color: #e5eadf;
  font-size: 12px;
  font-weight: 600;
}
.counter-case p {
  margin-top: 7px;
  color: #bac3b9;
  font-size: 13px;
  line-height: 1.85;
}
.evidence-summary {
  display: flex;
  align-items: center;
  gap: 20px;
  margin: 24px 0 15px;
}
.evidence-summary > div:first-child {
  display: flex;
  align-items: center;
  gap: 10px;
}
.evidence-summary strong {
  white-space: nowrap;
  font: 23px var(--mono, Consolas, monospace);
}
.evidence-summary strong small {
  font-size: 11px;
  color: var(--muted, #a7b2ab);
}
.evidence-summary span {
  font-size: 11px;
  line-height: 1.6;
  color: var(--muted, #a7b2ab);
  max-width: 105px;
}
.signal-track {
  height: 5px;
  flex: 1;
  border-radius: 4px;
  background: #3b4635;
  overflow: hidden;
}
.signal-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--accent, #cef576);
}
.evidence-button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  min-height: 48px;
  padding: 10px 0;
  border: 0;
  border-top: 1px solid var(--line, #344039);
  background: transparent;
  color: #ccd6c7;
  font-size: 12px;
  text-align: left;
}
.evidence-button svg {
  transition: transform 0.2s;
}
.evidence-button .rotated {
  transform: rotate(180deg);
}
.evidence-detail {
  padding: 17px;
  background: #252e23;
  border: 1px solid #4a5d3f;
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.9;
}
.evidence-detail p {
  margin-top: 9px;
  color: var(--muted, #a7b2ab);
}
.inline-button,
.next-step {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 44px;
  padding: 10px 0;
  border: 0;
  background: transparent;
  color: var(--accent, #cef576);
  font-size: 12px !important;
  font-weight: 550 !important;
  text-decoration: underline;
  text-underline-offset: 4px;
}
.next-step {
  width: 100%;
  justify-content: space-between;
  padding: 13px 16px;
  margin-top: 16px;
  border: 1px solid #50603f;
  border-radius: 5px;
  background: #252e22;
  text-decoration: none;
}
.next-step:hover {
  background: #303d27;
  border-color: #91aa67;
}
.research-panel h4 {
  font: 550 24px/1.4 var(--sans, "Segoe UI", sans-serif);
  letter-spacing: -0.6px;
  margin-top: 17px;
}
.panel-copy {
  color: var(--muted, #a7b2ab);
  font-size: 13px;
  line-height: 1.9;
  margin: 10px 0 20px !important;
}
.source-record {
  display: flex;
  gap: 14px;
  padding: 17px 0;
  border-top: 1px solid var(--line, #344039);
  color: inherit;
  text-decoration: none;
}
.source-number {
  color: #b7c7a8;
  font: 11px/1.7 var(--mono, Consolas, monospace);
  padding-top: 2px;
}
.source-record strong {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
  font-weight: 550;
}
.source-record p {
  font-size: 12px;
  color: var(--muted, #a7b2ab);
  line-height: 1.8;
  margin: 6px 0 8px;
}
.source-record small {
  color: #a2b196;
  font: 9px/1.6 var(--mono, Consolas, monospace);
  letter-spacing: 0.4px;
}
.source-link:hover strong {
  color: var(--accent, #cef576);
  text-decoration: underline;
  text-underline-offset: 4px;
}
.scenario-choices {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin: 22px 0;
}
.scenario-choices button {
  padding: 15px 12px;
  border: 1px solid #4b5945;
  border-radius: 6px;
  color: var(--muted, #a7b2ab);
  background: #171d1a;
  text-align: left;
}
.scenario-choices button.selected {
  color: var(--accent, #cef576);
  border-color: var(--accent, #cef576);
  background: #283522;
}
.scenario-choices span {
  display: block;
  font-size: 12px;
}
.scenario-choices strong {
  display: block;
  margin-top: 10px;
  font: 25px/1.2 var(--mono, Consolas, monospace);
  letter-spacing: -0.8px;
}
.scenario-result {
  padding: 20px;
  background: #232c20;
  border: 1px solid #4b6140;
  border-radius: 6px;
}
.scenario-result > span {
  font-size: 12px;
  color: #b9c8af;
}
.scenario-result strong {
  display: block;
  font: 35px/1.2 var(--mono, Consolas, monospace);
  letter-spacing: -1px;
  margin: 11px 0;
  color: var(--accent, #cef576);
}
.scenario-result p,
.assumption-note {
  color: var(--muted, #a7b2ab);
  font-size: 12px;
  line-height: 1.9;
}
.scenario-chart {
  padding: 22px 0 0;
}
.scenario-chart figcaption {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 16px;
  font: 9px/1.7 var(--mono, Consolas, monospace);
  letter-spacing: 0.5px;
  color: #b3c1a9;
}
.scenario-chart figcaption span:last-child {
  letter-spacing: 0;
  color: var(--muted, #a7b2ab);
}
.scenario-chart-row {
  display: grid;
  grid-template-columns: 40px minmax(0, 1fr) 81px;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  font-size: 11px;
  color: var(--muted, #a7b2ab);
}
.scenario-chart-row.selected {
  color: var(--accent, #cef576);
}
.scenario-bar-track {
  position: relative;
  height: 22px;
  background: repeating-linear-gradient(
    90deg,
    transparent,
    transparent calc(20% - 1px),
    #344039 calc(20% - 1px),
    #344039 20%
  );
  border-bottom: 1px solid #344039;
}
.scenario-bar-track::after {
  content: "";
  position: absolute;
  height: 100%;
  width: 1px;
  left: 40%;
  top: 0;
  background: #bdcab3;
}
.scenario-bar-track i {
  position: absolute;
  height: 11px;
  top: 5px;
  border-radius: 2px;
  background: #6f8658;
}
.scenario-bar-track i.downside {
  background: #cb8c78;
}
.selected .scenario-bar-track i {
  background: var(--accent, #cef576);
}
.selected .scenario-bar-track i.downside {
  background: var(--desk-negative);
}
.scenario-chart-row strong {
  font: 11px var(--mono, Consolas, monospace);
  text-align: right;
}
.scenario-chart-row small {
  display: block;
  margin-top: 4px;
  font-size: 9px;
}
.scenario-chart > p {
  margin-top: 13px;
  color: var(--muted, #a7b2ab);
  font-size: 11px;
  line-height: 1.8;
}
.assumption-note {
  margin-top: 19px !important;
}
.risk-sidebar {
  grid-column: 3;
  grid-row: 1 / 3;
  background: #202720;
  padding: 27px 23px;
  border-left: 1px solid #3d4c35;
  min-width: 0;
}
.risk-sidebar > .small-heading {
  color: #b5c7a7;
  font-size: 10px;
  letter-spacing: 0.6px;
}
.risk-sidebar h4 {
  font: 500 28px/1.25 var(--sans, "Segoe UI", sans-serif);
  letter-spacing: -0.8px;
  margin-top: 25px;
}
.risk-intro {
  color: #b4c1ac;
  font-size: 13px;
  line-height: 1.85;
  margin-top: 14px !important;
}
.compact-scenarios {
  border: 0;
  padding: 0;
  margin: 28px 0 25px;
  min-width: 0;
}
.compact-scenarios legend {
  font-size: 12px;
  padding: 0;
  margin-bottom: 11px;
  color: #d8e2ce;
}
.compact-scenarios > div {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 3px;
  padding: 4px;
  border: 1px solid #5b694f;
  border-radius: 6px;
  background: #141b12;
}
.compact-scenarios button {
  min-height: 44px;
  padding: 8px 3px;
  border: 0;
  border-radius: 3px;
  background: transparent;
  color: #b5c1ac;
  font-size: 12px;
}
.compact-scenarios button.selected {
  background: var(--accent, #cef576);
  color: #101315;
  font-weight: 650;
}
.weight-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font-size: 12px;
  color: #d7e0cf;
}
.weight-label output {
  font: 21px var(--mono, Consolas, monospace);
  color: var(--accent, #cef576);
}
.risk-sidebar input[type="range"] {
  width: 100%;
  min-height: 44px;
  margin: 8px 0 0;
  accent-color: var(--accent, #cef576);
  cursor: pointer;
}
.range-ends {
  display: flex;
  justify-content: space-between;
  color: #acbba2;
  font: 10px/1.7 var(--mono, Consolas, monospace);
}
.stress-result {
  border-top: 1px solid #4d5b43;
  margin-top: 28px;
  padding-top: 24px;
}
.stress-result > span {
  font-size: 12px;
  color: #c3cfb9;
}
.stress-result > strong {
  display: block;
  margin: 13px 0;
  color: var(--accent, #cef576);
  font: 45px/1.2 var(--mono, Consolas, monospace);
  letter-spacing: -2px;
}
.stress-result strong small {
  font-size: 25px;
  letter-spacing: -1px;
}
.stress-result p {
  color: #b3c2a8;
  font-size: 11px;
  line-height: 1.8;
}
.stress-gauge {
  height: 6px;
  border-radius: 4px;
  background: #47563b;
  margin-top: 20px;
  overflow: hidden;
}
.stress-gauge i {
  display: block;
  height: 100%;
  background: var(--accent, #cef576);
  border-radius: inherit;
}
.stress-scale {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-top: 8px;
  font: 9px/1.7 var(--mono, Consolas, monospace);
  color: #aebe9f;
}
.risk-checklist {
  display: grid;
  gap: 14px;
  padding: 0;
  margin: 29px 0 0;
  list-style: none;
}
.risk-checklist li {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: #c4d1b9;
}
.risk-checklist svg {
  color: var(--accent, #cef576);
}
.hollow-dot {
  width: 10px;
  height: 10px;
  margin: 2px;
  border: 1px solid #aebe9f;
  border-radius: 50%;
}
.risk-footnote {
  padding-top: 22px;
  margin-top: 28px !important;
  border-top: 1px solid #4d5b43;
  color: #aebfa1;
  font-size: 11px;
  line-height: 1.9;
}
.save-area {
  grid-column: 2;
  grid-row: 2;
  min-width: 0;
  padding: 25px 28px;
  border-top: 1px solid var(--line, #344039);
  background: #151b1a;
}
.save-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding-bottom: 17px;
  font: 10px/1.6 var(--mono, Consolas, monospace);
  color: #d7e1cc;
  letter-spacing: 0.6px;
}
.save-heading span {
  font-size: 9px;
  color: var(--muted, #a7b2ab);
  letter-spacing: 0.3px;
}
.save-area label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  font-weight: 550;
}
.save-area label span {
  color: var(--muted, #a7b2ab);
  font-size: 11px;
  font-weight: 400;
}
.save-area textarea {
  display: block;
  width: 100%;
  min-height: 96px;
  max-height: 260px;
  padding: 12px 14px;
  margin: 10px 0 8px;
  resize: vertical;
  border: 1px solid #53614b;
  border-radius: 5px;
  color: var(--ink, #eef2ed);
  background: #101612;
  font-size: 13px;
  line-height: 1.8;
}
.save-area textarea::placeholder,
.research-desk input::placeholder {
  color: #9eaf96;
  opacity: 1;
}
.draft-note {
  color: var(--muted, #a7b2ab);
  font-size: 10px;
  line-height: 1.8;
}
.save-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  margin-top: 18px;
}
.save-row small {
  color: var(--muted, #a7b2ab);
  font-size: 10px;
  line-height: 1.8;
}
.save-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 46px;
  padding: 12px 16px;
  border: 1px solid var(--accent, #cef576);
  border-radius: 5px;
  color: #101315;
  background: var(--accent, #cef576);
  font-size: 12px !important;
  font-weight: 650 !important;
  flex-shrink: 0;
}
.save-button:hover:not(:disabled) {
  background: #dbff91;
}
.save-button:disabled {
  color: #c0d6a0;
  background: #2a3623;
  border-color: #5e744a;
  opacity: 1;
}
.saved-journal-link {
  margin-top: 10px;
}
.desk-feedback {
  padding: 17px 24px;
  border-top: 1px solid #4b613b;
  background: #263220;
  color: #d7e6c3;
  font-size: 13px;
  line-height: 1.9;
}
.storage-error {
  display: flex;
  align-items: center;
  gap: 20px;
  color: #f2b3a2;
}
.storage-error span {
  flex: 1;
}
.storage-error button {
  flex-shrink: 0;
}
.local-journal {
  padding: 28px;
  border-top: 1px solid var(--line, #344039);
  background: #141a18;
  scroll-margin-top: 110px;
}
.journal-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}
.journal-heading h4 {
  font: 550 28px/1.3 var(--sans, "Segoe UI", sans-serif);
  letter-spacing: -0.8px;
  margin-top: 7px;
  scroll-margin-top: 110px;
}
.journal-heading h4 span {
  margin-left: 10px;
  color: var(--muted, #a7b2ab);
  font: 13px var(--mono, Consolas, monospace);
  vertical-align: middle;
}
.journal-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.journal-close {
  display: grid;
  place-items: center;
  min-width: 44px;
  min-height: 44px;
  padding: 10px;
  color: var(--ink, #eef2ed);
  background: transparent;
  border: 1px solid #52604f;
  border-radius: 6px;
}
.journal-close:hover {
  background: #273222;
}
.journal-disclosure {
  max-width: 780px;
  margin-top: 15px !important;
  color: var(--muted, #a7b2ab);
  font-size: 12px;
  line-height: 1.9;
}
.journal-filters {
  display: flex;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
  margin-top: 23px;
  padding: 16px;
  border: 1px solid var(--line, #344039);
  background: #1c241c;
  border-radius: 6px;
}
.journal-search {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 200px;
  color: #adbea0;
}
.journal-search input {
  min-width: 0;
  width: 100%;
  min-height: 44px;
  padding: 9px 12px;
  border: 1px solid #59694f;
  border-radius: 5px;
  color: var(--ink, #eef2ed);
  background: #111810;
  font-size: 12px;
}
.journal-asset-filter {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: #b9c8af;
}
.journal-asset-filter select {
  min-height: 44px;
  padding: 9px 30px 9px 12px;
  color: var(--ink, #eef2ed);
  background: #111810;
  border: 1px solid #59694f;
  border-radius: 5px;
  font-size: 12px;
}
.journal-filter-count {
  color: var(--muted, #a7b2ab);
  font: 10px var(--mono, Consolas, monospace);
  white-space: nowrap;
}
.undo-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  margin-top: 19px;
  padding: 8px 16px;
  border: 1px solid #526a3f;
  border-radius: 6px;
  color: #ceddbf;
  background: #273222;
  font-size: 12px;
}
.journal-empty {
  padding: 45px 20px;
  text-align: center;
  color: var(--muted, #a7b2ab);
}
.journal-empty h5 {
  color: var(--ink, #eef2ed);
  font: 500 23px/1.4 var(--sans, "Segoe UI", sans-serif);
  margin: 16px 0 10px;
}
.journal-empty p {
  font-size: 13px;
  line-height: 1.9;
}
.journal-entries {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 17px;
  padding: 0;
  margin: 23px 0 0;
  list-style: none;
}
.journal-entries li {
  padding: 23px;
  border: 1px solid #3b4935;
  border-radius: 7px;
  background: #1e261d;
  overflow-wrap: anywhere;
}
.entry-heading {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 12px;
}
.entry-heading strong {
  font-size: 18px;
  letter-spacing: 0.2px;
}
.entry-heading span {
  display: block;
  margin-top: 5px;
  font-size: 11px;
  color: #aebfa1;
  text-transform: capitalize;
}
.entry-heading time {
  color: #aebfa1;
  font: 10px/1.8 var(--mono, Consolas, monospace);
  text-align: right;
}
.journal-entries li > p {
  margin-top: 18px;
  font-size: 13px;
  line-height: 1.9;
}
.entry-note {
  border-left: 2px solid #718953;
  padding-left: 13px;
  white-space: pre-wrap;
}
.entry-note strong {
  display: block;
  color: #b0c09f;
  font-size: 10px;
  margin-bottom: 5px;
}
.entry-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #3d4d35;
}
.revisit-entry {
  font-size: 11px !important;
}
.delete-entry {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 44px;
  padding: 9px 7px;
  border: 0;
  border-radius: 5px;
  color: var(--desk-negative);
  background: transparent;
  font-size: 11px !important;
}
.delete-entry:hover {
  background: #392b26;
}
.journal-entries li > .entry-disclosure {
  margin-top: 13px;
  font: 9px/1.7 var(--mono, Consolas, monospace);
  color: #a4b694;
}
.desk-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 15px 24px;
  background: #121815;
  border-top: 1px solid var(--line, #344039);
  color: var(--muted, #a7b2ab);
  font: 9px/1.8 var(--mono, Consolas, monospace);
  letter-spacing: 0.6px;
}
.desk-footer > span:first-child {
  display: flex;
  align-items: center;
  gap: 7px;
}
.desk-footer > span:last-child {
  font: 11px/1.8 var(--sans, "Segoe UI", sans-serif);
  letter-spacing: 0;
}
@media (max-width: 1180px) {
  .desk-grid {
    grid-template-columns: 180px minmax(0, 1fr) 254px;
  }
  .watchlist {
    padding-inline: 10px;
  }
  .asset-row {
    padding-inline: 8px;
  }
  .asset-name strong {
    font-size: 13px;
  }
  .asset-quote strong {
    font-size: 11px;
  }
  .research-main {
    padding: 25px 21px;
  }
  .save-area {
    padding: 24px 21px;
  }
  .risk-sidebar {
    padding: 26px 20px;
  }
  .desk-session > span:last-child {
    display: none;
  }
  .research-tabs {
    gap: 18px;
  }
  .research-tabs button {
    gap: 6px;
    font-size: 12px;
  }
  .save-row {
    flex-direction: column;
    align-items: stretch;
    gap: 13px;
  }
  .save-row small br {
    display: none;
  }
  .risk-sidebar h4 {
    font-size: 25px;
  }
}
@media (max-width: 960px) {
  .desk-grid {
    grid-template-columns: 185px minmax(0, 1fr);
  }
  .watchlist {
    grid-column: 1;
    grid-row: 1 / 4;
  }
  .research-main {
    grid-column: 2;
    grid-row: 1;
  }
  .risk-sidebar {
    grid-column: 2;
    grid-row: 2;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0 26px;
    padding: 25px;
    border-left: 0;
    border-top: 1px solid #3d4c35;
  }
  .risk-sidebar > .small-heading {
    grid-column: 1 / -1;
    margin-bottom: 20px;
  }
  .risk-sidebar h4 {
    grid-column: 1;
    margin: 0;
  }
  .risk-intro,
  .compact-scenarios,
  .weight-label,
  .risk-sidebar input,
  .range-ends {
    grid-column: 1;
  }
  .stress-result {
    grid-column: 2;
    grid-row: 2 / 5;
    margin: 0;
    padding: 0;
    border: 0;
  }
  .stress-result > strong {
    font-size: 37px;
  }
  .stress-result strong small {
    font-size: 22px;
  }
  .stress-scale {
    font-size: 8px;
  }
  .risk-checklist {
    grid-column: 2;
    grid-row: 5 / 7;
    margin: 0;
  }
  .risk-footnote {
    grid-column: 2;
    grid-row: 7 / 10;
    align-self: start;
    margin-top: 20px !important;
    padding-top: 15px;
  }
  .save-area {
    grid-column: 2;
    grid-row: 3;
  }
  .save-row {
    flex-direction: row;
    align-items: center;
  }
  .save-row small br {
    display: block;
  }
  .desk-session {
    display: none;
  }
  .journal-toggle {
    margin-left: auto;
  }
}
@media (max-width: 700px) {
  .desk-grid {
    display: block;
  }
  .desk-header {
    padding: 18px;
    gap: 13px;
    flex-wrap: wrap;
  }
  .desk-title {
    font-size: 17px;
    gap: 10px;
  }
  .desk-title small {
    font-size: 9px;
    letter-spacing: 0.7px;
  }
  .desk-icon {
    width: 36px;
    height: 36px;
    border-radius: 7px;
  }
  .watchlist {
    padding: 20px 18px;
    border-right: 0;
    border-bottom: 1px solid var(--line, #344039);
  }
  .watchlist > .small-heading {
    padding: 0;
  }
  .asset-search {
    margin: 13px 0;
  }
  .asset-search input {
    font-size: 16px;
  }
  .asset-search button {
    min-width: 44px;
  }
  .asset-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 7px;
  }
  .asset-row {
    border-color: #344039;
    padding: 13px 11px;
  }
  .asset-name strong {
    font-size: 15px;
  }
  .asset-quote strong {
    font-size: 12px;
  }
  .watchlist-note {
    padding: 14px 0 0;
    font-size: 11px;
  }
  .desk-process {
    display: none;
  }
  .research-main {
    padding: 25px 23px;
  }
  .research-panel {
    min-height: 0;
  }
  .research-tabs {
    justify-content: space-between;
    gap: 15px;
  }
  .research-tabs button {
    font-size: 13px;
    padding: 11px 6px;
  }
  .save-area {
    padding: 25px 23px;
  }
  .risk-sidebar {
    padding: 25px 23px;
  }
  .journal-entries {
    grid-template-columns: 1fr;
  }
  .journal-heading {
    flex-wrap: wrap;
    gap: 17px;
  }
  .journal-filters {
    gap: 13px;
    padding: 14px;
  }
  .journal-search {
    flex-basis: 100%;
  }
  .journal-search input,
  .journal-asset-filter select {
    font-size: 16px;
  }
  .journal-filter-count {
    margin-left: auto;
  }
  .local-journal {
    padding: 24px 20px;
  }
  .journal-disclosure {
    font-size: 12px;
  }
}
@media (max-width: 450px) {
  .research-desk {
    border-radius: 8px;
  }
  .desk-header {
    padding: 17px 15px;
  }
  .desk-title {
    font-size: 17px;
  }
  .journal-toggle {
    width: 100%;
    margin: 0;
    justify-content: space-between;
    padding-inline: 12px;
  }
  .journal-toggle svg {
    margin-right: auto;
  }
  .watchlist {
    padding: 18px 15px;
  }
  .asset-row {
    padding: 12px 9px;
    gap: 6px;
  }
  .asset-name strong {
    font-size: 13px;
  }
  .asset-name small {
    font-size: 10px;
  }
  .asset-quote strong {
    font-size: 11px;
  }
  .asset-quote small {
    font-size: 9px;
  }
  .research-main {
    padding: 24px 18px;
  }
  .asset-heading {
    gap: 10px;
  }
  .asset-heading .small-heading {
    font-size: 9px;
  }
  .asset-heading h3 {
    font-size: 29px;
    gap: 8px;
  }
  .signal-status {
    font-size: 9px;
    padding-inline: 5px;
  }
  .main-price {
    font-size: 20px;
  }
  .main-price small {
    font-size: 10px;
  }
  .research-tabs {
    gap: 8px;
  }
  .research-tabs button {
    font-size: 12px;
    gap: 7px;
    padding-inline: 3px;
  }
  .research-guide {
    font-size: 11px;
    padding-bottom: 22px;
  }
  .thesis-copy {
    font-size: 15px;
  }
  .counter-case {
    padding: 14px;
  }
  .counter-case p {
    font-size: 12px;
  }
  .evidence-summary {
    gap: 12px;
  }
  .evidence-summary > div:first-child {
    gap: 8px;
  }
  .evidence-summary span {
    font-size: 10px;
    max-width: 98px;
  }
  .brief-label {
    font-size: 9px;
    letter-spacing: 0.4px;
    gap: 7px;
  }
  .research-panel h4 {
    font-size: 22px;
  }
  .scenario-choices {
    gap: 7px;
  }
  .scenario-choices button {
    padding: 13px 10px;
  }
  .scenario-choices span {
    font-size: 11px;
  }
  .scenario-choices strong {
    font-size: 23px;
  }
  .scenario-chart-row {
    grid-template-columns: 32px minmax(0, 1fr) 74px;
    gap: 8px;
  }
  .scenario-result {
    padding: 18px;
  }
  .risk-sidebar {
    display: block;
    padding: 25px 21px;
  }
  .risk-sidebar > .small-heading {
    margin: 0;
  }
  .risk-sidebar h4 {
    margin-top: 22px;
    font-size: 28px;
  }
  .risk-intro {
    margin-top: 12px !important;
  }
  .compact-scenarios {
    margin: 24px 0;
  }
  .stress-result {
    margin-top: 25px;
    padding-top: 24px;
    border-top: 1px solid #4d5b43;
  }
  .stress-result > strong {
    font-size: 46px;
  }
  .stress-scale {
    font-size: 9px;
  }
  .risk-checklist {
    margin-top: 25px;
  }
  .risk-footnote {
    margin-top: 25px !important;
    padding-top: 20px;
  }
  .save-area {
    padding: 25px 18px;
  }
  .save-heading {
    flex-wrap: wrap;
  }
  .save-area textarea {
    font-size: 16px;
  }
  .save-row {
    align-items: stretch;
    flex-direction: column;
    gap: 14px;
  }
  .save-row small br {
    display: none;
  }
  .save-button {
    width: 100%;
  }
  .saved-journal-link {
    width: 100%;
  }
  .desk-feedback {
    padding: 16px 18px;
    font-size: 12px;
  }
  .storage-error {
    display: block;
  }
  .local-journal {
    padding: 23px 18px;
  }
  .journal-heading h4 {
    font-size: 27px;
  }
  .journal-actions {
    gap: 8px;
  }
  .journal-entries li {
    padding: 18px;
  }
  .entry-heading time {
    max-width: 88px;
    font-size: 9px;
  }
  .entry-footer {
    gap: 8px;
  }
  .revisit-entry {
    font-size: 10px !important;
    padding: 9px 10px;
  }
  .undo-row {
    flex-wrap: wrap;
    gap: 0 10px;
    padding: 11px 14px;
  }
  .desk-footer {
    padding: 15px 18px;
    align-items: start;
    flex-direction: column;
    gap: 9px;
  }
  .desk-footer > span:last-child {
    font-size: 10px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .research-desk *,
  .research-desk *::before,
  .research-desk *::after {
    transition: none !important;
    animation: none !important;
    scroll-behavior: auto !important;
  }
}
</style>
