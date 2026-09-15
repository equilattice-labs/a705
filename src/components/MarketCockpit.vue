<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { ArrowDownRight, ArrowUpRight, Bookmark, BookOpen, Check, ChevronDown, Download, ExternalLink, FileText, Search, ShieldCheck, SlidersHorizontal, Trash2, Undo2, X } from 'lucide-vue-next'

const assets = [
  { symbol: 'AAPL', name: 'Apple', price: 234.42, change: 1.84, signal: 78, status: 'Build', thesis: 'Services resilience and improving device mix support the base case. Valuation expansion is the key constraint; size only inside the defined risk band.', counter: 'Multiple compression could outweigh stronger services revenue. Revisit the thesis if services growth slows or device mix deteriorates.' },
  { symbol: 'NVDA', name: 'NVIDIA', price: 188.61, change: 3.12, signal: 72, status: 'Watch', thesis: 'Demand signals remain constructive, while concentration and elevated expectations increase downside sensitivity around guidance.', counter: 'Customer concentration and ambitious growth expectations leave little room for a guidance miss.' },
  { symbol: 'TSLA', name: 'Tesla', price: 354.18, change: -1.26, signal: 43, status: 'Caution', thesis: 'Momentum is mixed against a high-volatility backdrop. Delivery evidence and margin trend do not yet clear the action threshold.', counter: 'Delivery weakness or further margin compression could amplify an already volatile setup.' },
  { symbol: 'AMZN', name: 'Amazon', price: 251.05, change: 0.73, signal: 66, status: 'Watch', thesis: 'Cloud acceleration supports the thesis, with retail margins and regulatory exposure defining the primary counter-case.', counter: 'Slower cloud growth, weaker retail margins, or regulatory action would challenge the base case.' },
]
const scenarios = [
  { id: 'bear', label: 'Bear', move: -12, drawdown: 24, description: 'Expectations reset and valuation contracts.' },
  { id: 'base', label: 'Base', move: 6, drawdown: 12, description: 'The thesis develops without a major rerating.' },
  { id: 'bull', label: 'Bull', move: 18, drawdown: 17, description: 'Growth surprises; valuation sensitivity remains.' },
]
const tabs = ['Brief', 'Sources', 'Scenario']
const active = ref('AAPL')
const activeTab = ref('Brief')
const activeScenario = ref('base')
const query = ref('')
const weight = ref(10)
const note = ref('')
const evidenceOpen = ref(false)
const journalOpen = ref(false)
const journal = ref([])
const journalError = ref('')
const notice = ref('')
const lastDeleted = ref(null)
const journalHeading = ref(null)
const journalToggle = ref(null)
const searchInput = ref(null)
const journalKey = 'decisift:journal'
const current = computed(() => assets.find((asset) => asset.symbol === active.value))
const scenario = computed(() => scenarios.find((item) => item.id === activeScenario.value))
const filteredAssets = computed(() => {
  const term = query.value.trim().toLowerCase()
  return assets.filter((asset) => `${asset.symbol} ${asset.name}`.toLowerCase().includes(term))
})
const portfolioImpact = computed(() => (Number(weight.value) * scenario.value.drawdown / 100).toFixed(2))
const projectedPrice = computed(() => (current.value.price * (1 + scenario.value.move / 100)).toFixed(2))
const isSaved = computed(() => journal.value.some((entry) => entry.symbol === active.value && entry.scenario === activeScenario.value && entry.weight === Number(weight.value) && entry.note === note.value.trim()))

function selectAsset(symbol) {
  active.value = symbol
  note.value = ''
  notice.value = ''
  evidenceOpen.value = false
}
async function clearSearch() {
  query.value = ''
  await nextTick()
  searchInput.value?.focus()
}
function navigateTabs(event) {
  let index = tabs.indexOf(activeTab.value)
  if (event.key === 'ArrowRight') index = (index + 1) % tabs.length
  else if (event.key === 'ArrowLeft') index = (index + tabs.length - 1) % tabs.length
  else if (event.key === 'Home') index = 0
  else if (event.key === 'End') index = tabs.length - 1
  else return
  event.preventDefault()
  activeTab.value = tabs[index]
  nextTick(() => document.getElementById(`research-tab-${tabs[index].toLowerCase()}`)?.focus())
}
function loadJournal() {
  try {
    const saved = JSON.parse(localStorage.getItem(journalKey) || '[]')
    if (!Array.isArray(saved) || !saved.every((entry) => entry && typeof entry.id === 'string' && assets.some((asset) => asset.symbol === entry.symbol) && scenarios.some((item) => item.id === entry.scenario) && Number.isFinite(entry.weight) && entry.weight >= 1 && entry.weight <= 50 && Number.isFinite(entry.savedAt) && !Number.isNaN(new Date(entry.savedAt).getTime()) && typeof entry.thesis === 'string' && typeof entry.note === 'string')) throw new Error('Invalid journal data')
    journal.value = saved
    journalError.value = ''
  } catch {
    journalError.value = 'Your saved journal could not be read. Allow local storage and retry. Existing data has not been changed.'
  }
}
function persistJournal(entries) {
  try {
    localStorage.setItem(journalKey, JSON.stringify(entries))
    journal.value = entries
    journalError.value = ''
    return true
  } catch {
    journalError.value = 'This browser could not save the change. Check available storage or privacy settings, then retry.'
    return false
  }
}
function saveThesis() {
  if (isSaved.value || journalError.value) return
  const entry = {
    id: crypto.randomUUID(), savedAt: Date.now(), symbol: active.value,
    price: current.value.price, thesis: current.value.thesis, counter: current.value.counter,
    scenario: activeScenario.value, move: scenario.value.move, assumedDrawdown: scenario.value.drawdown,
    weight: Number(weight.value), portfolioStress: Number(portfolioImpact.value),
    note: note.value.trim(), dataType: 'illustrative-preview', modelVersion: 'preview-1',
  }
  if (persistJournal([entry, ...journal.value])) notice.value = `${active.value} thesis saved on this device.`
}
async function openJournal() {
  journalOpen.value = true
  await nextTick()
  journalHeading.value?.focus({ preventScroll: true })
}
async function toggleJournal() {
  if (!journalOpen.value) return openJournal()
  journalOpen.value = false
  await nextTick()
  journalToggle.value?.focus({ preventScroll: true })
}
defineExpose({ openJournal })
function deleteEntry(entry) {
  if (journalError.value) return
  const index = journal.value.findIndex((item) => item.id === entry.id)
  if (persistJournal(journal.value.filter((item) => item.id !== entry.id))) {
    lastDeleted.value = { entry, index }
    notice.value = `${entry.symbol} entry removed. You can undo this deletion.`
    nextTick(() => document.getElementById('journal-undo')?.focus({ preventScroll: true }))
  }
}
function undoDelete() {
  if (!lastDeleted.value || journalError.value) return
  const restored = [...journal.value]
  restored.splice(Math.min(lastDeleted.value.index, restored.length), 0, lastDeleted.value.entry)
  if (persistJournal(restored)) {
    lastDeleted.value = null
    notice.value = 'Journal entry restored.'
    nextTick(() => journalHeading.value?.focus({ preventScroll: true }))
  }
}
function exportJournal() {
  const file = new Blob([JSON.stringify({ brand: 'Decisift', exportedAt: new Date().toISOString(), storage: 'local, unencrypted', entries: journal.value }, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(file)
  const link = document.createElement('a')
  link.href = url
  link.download = `decisift-journal-${new Date().toISOString().slice(0, 10)}.json`
  link.click()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  notice.value = 'Journal exported as a JSON file.'
}
function formatDate(timestamp) {
  return new Date(timestamp).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
function syncJournal(event) {
  if (event.key === journalKey || event.key === null) { loadJournal(); lastDeleted.value = null }
}
onMounted(() => { loadJournal(); window.addEventListener('storage', syncJournal) })
onBeforeUnmount(() => window.removeEventListener('storage', syncJournal))
</script>

<template>
  <div class="research-desk" aria-label="Decisift interactive research preview">
    <header class="desk-header">
      <div class="desk-title"><span class="desk-mark" aria-hidden="true">d.</span><span>Research workspace <small>ILLUSTRATIVE PREVIEW</small></span></div>
      <button ref="journalToggle" class="quiet-button journal-toggle" :aria-expanded="journalOpen" aria-controls="local-journal" @click="toggleJournal"><BookOpen :size="16" /> My journal <span class="count">{{ journal.length }}</span></button>
    </header>
    <div class="desk-grid">
      <aside class="watchlist" aria-label="Asset watchlist">
        <div class="small-heading"><span>YOUR WATCHLIST</span><span>04</span></div>
        <div class="asset-search"><Search :size="15" aria-hidden="true" /><input ref="searchInput" v-model="query" type="search" aria-label="Search assets" placeholder="Find an asset" /><button v-if="query" aria-label="Clear asset search" @click="clearSearch"><X :size="14" /></button></div>
        <div class="asset-list"><button v-for="asset in filteredAssets" :key="asset.symbol" class="asset-row" :class="{ selected: active === asset.symbol }" :aria-pressed="active === asset.symbol" @click="selectAsset(asset.symbol)"><span class="asset-name"><strong>{{ asset.symbol }}</strong><small>{{ asset.name }}</small></span><span class="asset-quote"><strong>{{ asset.price.toFixed(2) }}</strong><small :class="asset.change > 0 ? 'positive' : 'negative'"><ArrowUpRight v-if="asset.change > 0" :size="12" /><ArrowDownRight v-else :size="12" />{{ Math.abs(asset.change).toFixed(2) }}%</small></span></button></div>
        <div v-if="!filteredAssets.length" class="search-empty" role="status"><Search :size="20" /><p>No matching assets.</p><button class="inline-button" @click="clearSearch">Clear search</button></div>
        <p class="watchlist-note">Four sample assets.<br />Prices are illustrative USD values.</p>
      </aside>
      <section class="research-main" aria-label="Selected asset research">
        <div class="asset-heading"><div><p class="small-heading">{{ current.name }} / STOCK TOKEN</p><h3>{{ current.symbol }} <span :class="['signal-status', current.status.toLowerCase()]">{{ current.status }}</span></h3></div><div class="main-price">${{ current.price.toFixed(2) }}<small :class="current.change > 0 ? 'positive' : 'negative'">{{ current.change > 0 ? '+' : '' }}{{ current.change.toFixed(2) }}% <span>sample</span></small></div></div>
        <div class="research-tabs" role="tablist" aria-label="Research sections" @keydown="navigateTabs"><button v-for="tab in tabs" :id="`research-tab-${tab.toLowerCase()}`" :key="tab" role="tab" :aria-selected="activeTab === tab" :aria-controls="`research-panel-${tab.toLowerCase()}`" :tabindex="activeTab === tab ? 0 : -1" :class="{ selected: activeTab === tab }" @click="activeTab = tab">{{ tab }}<span v-if="tab === 'Sources'" class="tab-dot" aria-hidden="true"></span></button></div>
        <div v-if="activeTab === 'Brief'" id="research-panel-brief" class="research-panel" role="tabpanel" aria-labelledby="research-tab-brief" tabindex="0">
          <div class="brief-label"><FileText :size="16" /><span>THE WORKING THESIS</span><span class="sample-tag">SAMPLE</span></div>
          <p class="thesis-copy">{{ current.thesis }}</p>
          <div class="counter-case"><span>What could change the view</span><p>{{ current.counter }}</p></div>
          <div class="evidence-summary"><div><strong>{{ current.signal }}<small>/100</small></strong><span>Illustrative signal score</span></div><div class="signal-track" aria-hidden="true"><i :style="{ width: `${current.signal}%` }"></i></div></div>
          <button class="evidence-button" :aria-expanded="evidenceOpen" aria-controls="evidence-detail" @click="evidenceOpen = !evidenceOpen"><span>Inspect the evidence context</span><ChevronDown :size="16" :class="{ rotated: evidenceOpen }" /></button>
          <div v-if="evidenceOpen" id="evidence-detail" class="evidence-detail"><strong>Know what this preview contains.</strong><p>The prices, scores, and thesis above are fixed demonstration data. No issuer filings, market feed, or model output are connected to this workspace.</p><p>Use Sources to inspect the available network references. They do not substantiate the investment thesis.</p><button class="inline-button" @click="activeTab = 'Sources'">Open source context <ArrowUpRight :size="14" /></button></div>
        </div>
        <div v-if="activeTab === 'Sources'" id="research-panel-sources" class="research-panel source-panel" role="tabpanel" aria-labelledby="research-tab-sources" tabindex="0">
          <div class="brief-label"><BookOpen :size="16" /><span>SOURCE CONTEXT</span><span class="sample-tag">PREVIEW</span></div>
          <h4>Evidence should be inspectable.</h4><p class="panel-copy">This demo contains no live research sources. The working thesis is sample copy; it has not been verified against issuer disclosures.</p>
          <div class="source-record"><span class="source-number">01</span><div><strong>Decisift product sample</strong><p>Fixed prices, illustrative signal scores, and scenario assumptions. No collection timestamp.</p><small>DATA TYPE / DEMONSTRATION</small></div></div>
          <a class="source-record source-link" href="https://docs.robinhood.com/chain/" target="_blank" rel="noreferrer"><span class="source-number">02</span><div><strong>Robinhood Chain documentation <ExternalLink :size="13" /></strong><p>Network reference for the wallet connection.</p><small>REFERENCE / NETWORK ONLY</small></div></a>
          <a class="source-record source-link" href="https://robinhoodchain.blockscout.com" target="_blank" rel="noreferrer"><span class="source-number">03</span><div><strong>Robinhood Chain explorer <ExternalLink :size="13" /></strong><p>Inspect onchain activity independently.</p><small>REFERENCE / NETWORK ONLY</small></div></a>
        </div>
        <div v-if="activeTab === 'Scenario'" id="research-panel-scenario" class="research-panel" role="tabpanel" aria-labelledby="research-tab-scenario" tabindex="0">
          <div class="brief-label"><SlidersHorizontal :size="16" /><span>SCENARIO LAB</span><span class="sample-tag">30 DAYS</span></div>
          <h4>Make the assumptions visible.</h4><p class="panel-copy">Explore a hypothetical price move. Each case also carries a separate stress drawdown for sizing.</p>
          <div class="scenario-choices" role="group" aria-label="Market scenarios"><button v-for="item in scenarios" :key="item.id" :class="{ selected: activeScenario === item.id }" :aria-pressed="activeScenario === item.id" @click="activeScenario = item.id"><span>{{ item.label }} case</span><strong>{{ item.move > 0 ? '+' : '' }}{{ item.move }}%</strong></button></div>
          <div class="scenario-result"><span>Hypothetical {{ current.symbol }} price</span><strong>${{ projectedPrice }}</strong><p>{{ scenario.description }}</p></div>
          <p class="assumption-note">Sample price × (1 + assumed move). These scenarios are neither forecasts nor probability estimates.</p>
        </div>
        <div class="save-area"><label for="thesis-note">Your decision note <span>optional</span></label><textarea id="thesis-note" v-model="note" rows="2" maxlength="500" placeholder="What would you need to see before acting?"></textarea><div class="save-row"><small>Saved on this device. Unencrypted.</small><button class="save-button" :disabled="isSaved || !!journalError" @click="saveThesis"><Check v-if="isSaved" :size="15" /><Bookmark v-else :size="15" />{{ isSaved ? 'Saved to journal' : 'Save thesis' }}</button></div></div>
      </section>
      <aside class="risk-sidebar" aria-label="Risk simulator">
        <div class="small-heading"><span>BEFORE YOU DECIDE</span><ShieldCheck :size="16" /></div><h4>Give your conviction<br />a boundary.</h4><p class="risk-intro">A clear thesis still needs a clear downside.</p>
        <fieldset class="compact-scenarios"><legend>Scenario</legend><div><button v-for="item in scenarios" :key="item.id" :class="{ selected: activeScenario === item.id }" :aria-pressed="activeScenario === item.id" @click="activeScenario = item.id">{{ item.label }}</button></div></fieldset>
        <div class="weight-label"><label for="position-weight">Position weight</label><output for="position-weight">{{ weight }}%</output></div><input id="position-weight" v-model.number="weight" type="range" min="1" max="50" step="1" :aria-valuetext="`${weight} percent of portfolio`" /><div class="range-ends"><span>1% of portfolio</span><span>50%</span></div>
        <div class="stress-result"><span>Portfolio stress impact</span><strong>−{{ portfolioImpact }}<small>%</small></strong><p>{{ weight }}% position × {{ scenario.drawdown }}% assumed drawdown</p></div>
        <ul class="risk-checklist"><li><Check :size="14" />{{ scenario.label }} case selected</li><li><Check :size="14" />Downside made explicit</li><li><span class="hollow-dot"></span>No trade is submitted</li></ul><p class="risk-footnote">Illustrative sizing only. No leverage; excludes fees and slippage. This estimate does not enforce a loss limit.</p>
      </aside>
    </div>
    <div v-if="notice || journalError" class="desk-feedback"><p v-if="notice" role="status">{{ notice }}</p><div v-if="journalError" class="storage-error" role="alert"><span>{{ journalError }}</span><button class="inline-button" @click="loadJournal">Retry storage</button></div></div>
    <section v-if="journalOpen" id="local-journal" class="local-journal" aria-labelledby="local-journal-title">
      <div class="journal-heading"><div><p class="small-heading">YOUR DECISION RECORD</p><h4 id="local-journal-title" ref="journalHeading" tabindex="-1">My journal <span>{{ journal.length }}</span></h4></div><div class="journal-actions"><button class="quiet-button" :disabled="!journal.length" @click="exportJournal"><Download :size="15" /> Export JSON</button><button class="journal-close" aria-label="Close journal" @click="toggleJournal"><X :size="18" /></button></div></div>
      <p class="journal-disclosure">Local, unencrypted storage in this browser. No cloud sync or onchain proof. Avoid sensitive information; export a copy before clearing browser data.</p>
      <div v-if="lastDeleted" class="undo-row"><span>Last journal entry removed.</span><button id="journal-undo" class="inline-button" :disabled="!!journalError" @click="undoDelete"><Undo2 :size="14" /> Undo deletion</button></div>
      <div v-if="!journal.length" class="journal-empty"><BookOpen :size="26" /><h5>A little context for your next decision.</h5><p>Select an asset, adjust its scenario, and save your first thesis.</p></div>
      <ol v-else class="journal-entries"><li v-for="entry in journal" :key="entry.id"><div class="entry-heading"><div><strong>{{ entry.symbol }}</strong><span>{{ entry.scenario }} case · {{ entry.weight }}% position</span></div><time :datetime="new Date(entry.savedAt).toISOString()">{{ formatDate(entry.savedAt) }}</time></div><p>{{ entry.thesis }}</p><p v-if="entry.note" class="entry-note"><strong>Your note</strong>{{ entry.note }}</p><div class="entry-footer"><span>ILLUSTRATIVE PREVIEW · LOCAL COPY</span><button class="delete-entry" :aria-label="`Delete ${entry.symbol} journal entry from ${formatDate(entry.savedAt)}`" :disabled="!!journalError" @click="deleteEntry(entry)"><Trash2 :size="14" /> Delete</button></div></li></ol>
    </section>
    <footer class="desk-footer"><span><span class="preview-dot"></span> PRODUCT PREVIEW</span><span>Research is a process. The decision is yours.</span></footer>
  </div>
</template>

<style scoped>
.research-desk{color:var(--ink,#20332e);background:#fffefa;border:1px solid var(--line,#dce2d8);border-radius:16px;box-shadow:0 18px 50px #20332e0b;overflow:hidden;font-family:var(--sans,'Segoe UI',sans-serif);text-align:left}
.research-desk *,.research-desk *::before,.research-desk *::after{box-sizing:border-box}.research-desk button,.research-desk input,.research-desk textarea{font:inherit}.research-desk button{cursor:pointer}.research-desk button:focus-visible,.research-desk input:focus-visible,.research-desk textarea:focus-visible,.research-desk a:focus-visible,.research-desk [tabindex]:focus-visible{outline:3px solid #a74222;outline-offset:3px}.research-desk button:disabled{cursor:not-allowed;opacity:.55}.research-desk p,.research-desk h3,.research-desk h4,.research-desk h5{margin:0}
.desk-header{padding:18px 24px;display:flex;align-items:center;justify-content:space-between;gap:18px;border-bottom:1px solid var(--line,#dce2d8)}.desk-title{display:flex;align-items:center;gap:12px;font-size:14px;font-weight:600}.desk-mark{background:var(--forest,#183b35);color:#fffefa;border-radius:8px;width:34px;height:34px;display:grid;place-content:center;font:italic 26px Georgia,serif}.desk-title small{display:block;font:9px var(--mono,Consolas,monospace);letter-spacing:1.3px;color:var(--muted,#66756d);margin-top:4px}.quiet-button{display:inline-flex;align-items:center;justify-content:center;gap:8px;color:var(--ink,#20332e);background:none;border:1px solid var(--line,#dce2d8);border-radius:6px;padding:10px 12px;min-height:42px;font-size:12px!important;font-weight:600!important}.quiet-button:hover:not(:disabled){background:var(--sage,#e7ede6)}.count{font:10px var(--mono,Consolas,monospace);border-radius:4px;padding:2px 5px;background:var(--sage,#e7ede6)}
.desk-grid{display:grid;grid-template-columns:204px minmax(0,1fr) 252px;align-items:stretch}.watchlist{padding:24px 12px;border-right:1px solid var(--line,#dce2d8);background:#f9f9f4}.small-heading{display:flex;align-items:center;justify-content:space-between;gap:8px;color:var(--muted,#66756d);font:9px/1.5 var(--mono,Consolas,monospace);letter-spacing:1.1px}.watchlist>.small-heading{padding:0 8px}.asset-search{margin:20px 0 12px;display:flex;align-items:center;gap:7px;border:1px solid var(--line,#dce2d8);border-radius:6px;padding-left:9px;color:var(--muted,#66756d);min-height:42px;background:#fffefa}.asset-search input{width:100%;min-width:0;color:var(--ink,#20332e);font-size:11px;padding:12px 0;background:transparent;border:0}.asset-search input::-webkit-search-cancel-button{display:none}.asset-search button{min-width:30px;min-height:38px;border:0;background:transparent;color:var(--muted,#66756d);display:grid;place-items:center}.asset-row{display:flex;justify-content:space-between;align-items:center;width:100%;gap:8px;border:1px solid transparent;background:transparent;color:inherit;padding:15px 10px;text-align:left;border-radius:7px;margin:3px 0}.asset-row:hover{background:#edf0e9}.asset-row.selected{background:var(--sage,#e7ede6);border-color:#d1dace}.asset-name strong{font:600 13px var(--sans,'Segoe UI',sans-serif)}.asset-name small{display:block;font-size:10px;color:var(--muted,#66756d);margin-top:5px}.asset-quote{text-align:right}.asset-quote strong{font:11px var(--mono,Consolas,monospace)}.asset-quote small{display:flex;align-items:center;justify-content:flex-end;font:9px var(--mono,Consolas,monospace);margin-top:6px}.positive{color:#326447}.negative{color:#a74222}.watchlist-note{color:var(--muted,#66756d);padding:24px 8px 0;font-size:10px;line-height:1.7}.search-empty{text-align:center;padding:26px 8px;color:var(--muted,#66756d);font-size:12px}.search-empty p{margin:9px 0}
.research-main{min-width:0}.asset-heading{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:28px 28px 22px}.asset-heading h3{font-size:29px;font-weight:600;letter-spacing:-.8px;display:flex;align-items:center;gap:10px;margin-top:6px}.signal-status{font:500 10px var(--sans,'Segoe UI',sans-serif);letter-spacing:0;color:#42604b;background:var(--sage,#e7ede6);padding:4px 7px;border-radius:4px}.signal-status.caution{color:#a74222;background:#f4e2d8}.main-price{font:20px var(--mono,Consolas,monospace);text-align:right;white-space:nowrap}.main-price small{display:block;font-size:10px;margin-top:8px}.main-price small span{font:9px var(--sans,'Segoe UI',sans-serif);color:var(--muted,#66756d);margin-left:3px}.research-tabs{display:flex;gap:28px;margin:0 28px;border-bottom:1px solid var(--line,#dce2d8)}.research-tabs button{display:flex;gap:6px;align-items:center;padding:12px 0 13px;min-height:44px;font-size:12px;border:0;border-bottom:2px solid transparent;color:var(--muted,#66756d);background:transparent}.research-tabs button.selected{color:var(--forest,#183b35);border-bottom-color:var(--forest,#183b35);font-weight:600}.tab-dot{width:4px;height:4px;border-radius:50%;background:#acb3a7}.research-panel{padding:24px 28px 0;min-height:360px}.brief-label{display:flex;align-items:center;gap:8px;font:9px var(--mono,Consolas,monospace);letter-spacing:1px;color:var(--muted,#66756d)}.sample-tag{margin-left:auto;font-size:8px;letter-spacing:.8px;border:1px solid var(--line,#dce2d8);padding:4px 6px;border-radius:3px;white-space:nowrap}.thesis-copy{font-size:15px;line-height:1.85;margin:16px 0 19px!important}.counter-case{background:#f5f2e9;border-left:2px solid #c7ae85;border-radius:0 5px 5px 0;padding:13px 15px}.counter-case>span{font-size:10px;font-weight:600}.counter-case p{color:#697063;font-size:11px;line-height:1.8;margin-top:6px}.evidence-summary{margin:19px 0 15px;display:flex;gap:16px;align-items:center}.evidence-summary>div:first-child{display:flex;align-items:center;gap:9px;flex-shrink:0}.evidence-summary strong{font:17px var(--mono,Consolas,monospace)}.evidence-summary strong small{font-size:9px;color:var(--muted,#66756d)}.evidence-summary span{color:var(--muted,#66756d);font-size:9px}.signal-track{height:4px;background:var(--sage,#e7ede6);border-radius:4px;overflow:hidden;flex:1}.signal-track i{height:100%;background:#63826c;display:block;border-radius:4px}.evidence-button{width:100%;display:flex;justify-content:space-between;gap:8px;align-items:center;color:var(--forest,#183b35);background:transparent;border:0;border-top:1px solid var(--line,#dce2d8);font-size:11px;text-align:left;min-height:46px;padding:10px 0}.evidence-button svg{transition:transform .2s;flex-shrink:0}.evidence-button .rotated{transform:rotate(180deg)}.evidence-detail{background:var(--sage,#e7ede6);padding:15px;border-radius:6px;font-size:11px;line-height:1.8}.evidence-detail p{margin:7px 0;color:#59695e}.inline-button{color:var(--forest,#183b35);border:0;background:transparent;font-size:11px!important;font-weight:600!important;display:inline-flex;align-items:center;gap:6px;min-height:36px;padding:5px 0;text-decoration:underline;text-underline-offset:4px}.research-panel h4{font:500 22px/1.3 Georgia,serif;letter-spacing:-.2px;margin-top:17px}.panel-copy{color:var(--muted,#66756d);font-size:11px;line-height:1.8;margin:9px 0 16px!important}.source-record{display:flex;gap:12px;padding:14px 0;border-top:1px solid var(--line,#dce2d8);color:inherit;text-decoration:none}.source-number{font:10px var(--mono,Consolas,monospace);color:var(--muted,#66756d);padding-top:3px}.source-record strong{display:flex;gap:6px;align-items:center;font-size:11px;font-weight:600}.source-record p{font-size:10px;color:var(--muted,#66756d);line-height:1.7;margin:4px 0 6px}.source-record small{font:8px var(--mono,Consolas,monospace);letter-spacing:.7px;color:var(--muted,#66756d)}.source-link:hover strong{text-decoration:underline;text-underline-offset:3px}.scenario-choices{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:20px 0}.scenario-choices button{border:1px solid var(--line,#dce2d8);border-radius:6px;background:transparent;padding:13px 8px;text-align:left;color:var(--muted,#66756d)}.scenario-choices button.selected{background:var(--sage,#e7ede6);border-color:#748a74;color:var(--forest,#183b35)}.scenario-choices span{display:block;font-size:10px}.scenario-choices strong{display:block;margin-top:8px;font:20px var(--mono,Consolas,monospace)}.scenario-result{padding:18px;background:#f6f6ef;border-radius:6px}.scenario-result>span{font-size:10px;color:var(--muted,#66756d)}.scenario-result strong{font:26px var(--mono,Consolas,monospace);display:block;margin:8px 0}.scenario-result p,.assumption-note{font-size:10px;line-height:1.8;color:var(--muted,#66756d)}.assumption-note{margin-top:12px!important}
.save-area{padding:19px 28px 25px}.save-area label{font-size:10px;font-weight:600;display:flex;justify-content:space-between}.save-area label span{color:var(--muted,#66756d);font-weight:400}.save-area textarea{width:100%;resize:vertical;min-height:62px;max-height:180px;border:1px solid var(--line,#dce2d8);background:#fffefa;border-radius:5px;margin:8px 0 12px;padding:10px 12px;font-size:11px;line-height:1.6;color:var(--ink,#20332e);display:block}.save-area textarea::placeholder{color:#778075}.save-row{display:flex;align-items:center;justify-content:space-between;gap:10px}.save-row small{font-size:9px;color:var(--muted,#66756d);line-height:1.6}.save-button{min-height:40px;display:flex;align-items:center;justify-content:center;gap:7px;font-size:11px!important;font-weight:600!important;background:var(--forest,#183b35);color:#fffefa;border:1px solid var(--forest,#183b35);border-radius:5px;padding:10px 12px;flex-shrink:0}.save-button:hover:not(:disabled){background:#2b5247}
.risk-sidebar{background:#f0f2e9;padding:27px 23px;border-left:1px solid var(--line,#dce2d8)}.risk-sidebar h4{font:25px/1.25 Georgia,serif;letter-spacing:-.5px;margin-top:23px}.risk-intro{font-size:11px;line-height:1.8;color:var(--muted,#66756d);margin-top:12px!important}.compact-scenarios{border:0;padding:0;margin:27px 0 23px}.compact-scenarios legend{font-size:10px;padding:0;margin-bottom:10px}.compact-scenarios>div{display:grid;grid-template-columns:repeat(3,1fr);padding:3px;background:#e3e8dc;border-radius:6px;gap:3px}.compact-scenarios button{min-height:35px;border:0;border-radius:4px;background:transparent;color:#59695e;font-size:11px}.compact-scenarios button.selected{background:#fffefa;color:var(--forest,#183b35);box-shadow:0 1px 4px #20332e14;font-weight:600}.weight-label{display:flex;justify-content:space-between;align-items:center;font-size:10px}.weight-label output{font:15px var(--mono,Consolas,monospace)}.risk-sidebar input[type='range']{width:100%;margin:13px 0 2px;accent-color:var(--forest,#183b35);cursor:pointer;min-height:25px}.range-ends{display:flex;justify-content:space-between;font:8px var(--mono,Consolas,monospace);color:var(--muted,#66756d)}.stress-result{margin-top:29px;border-top:1px solid #d4dccb;padding-top:22px}.stress-result>span{font-size:10px;color:var(--muted,#66756d)}.stress-result strong{display:block;font:42px var(--mono,Consolas,monospace);letter-spacing:-2px;margin:8px 0 9px;color:#a74222}.stress-result strong small{font-size:24px;letter-spacing:-1px}.stress-result p{font-size:9px;line-height:1.8;color:var(--muted,#66756d)}.risk-checklist{list-style:none;padding:0;margin:25px 0 0;display:grid;gap:13px}.risk-checklist li{display:flex;align-items:center;gap:8px;font-size:10px;color:#50654f}.hollow-dot{width:10px;height:10px;border:1px solid #99a690;border-radius:50%;margin:2px}.risk-footnote{font-size:9px;line-height:1.9;color:var(--muted,#66756d);margin-top:23px!important}
.desk-feedback{padding:14px 24px;border-top:1px solid var(--line,#dce2d8);background:#f2f5ec;font-size:11px;line-height:1.7}.storage-error{color:#a74222;display:flex;align-items:center;gap:16px}.storage-error span{flex:1}.storage-error button{flex-shrink:0}.local-journal{padding:28px;border-top:1px solid var(--line,#dce2d8);background:#f9f9f4}.journal-heading{display:flex;justify-content:space-between;gap:16px;align-items:center}.journal-heading h4{font:26px Georgia,serif;margin-top:7px}.journal-heading h4 span{font:12px var(--mono,Consolas,monospace);color:var(--muted,#66756d);vertical-align:middle;margin-left:7px}.journal-actions{display:flex;align-items:center;gap:10px}.journal-close{width:40px;min-height:40px;display:grid;place-items:center;color:var(--ink,#20332e);border:0;border-radius:5px;background:transparent}.journal-close:hover{background:var(--sage,#e7ede6)}.journal-disclosure{font-size:11px;color:var(--muted,#66756d);line-height:1.8;margin-top:14px!important;max-width:680px}.undo-row{display:flex;justify-content:space-between;align-items:center;gap:12px;font-size:11px;background:var(--sage,#e7ede6);border-radius:5px;padding:7px 14px;margin-top:15px}.journal-empty{padding:38px 15px;text-align:center;color:var(--muted,#66756d)}.journal-empty h5{color:var(--ink,#20332e);font:20px Georgia,serif;margin:13px 0 8px}.journal-empty p{font-size:11px;line-height:1.8}.journal-entries{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;padding:0;list-style:none;margin:22px 0 0}.journal-entries li{background:#fffefa;border:1px solid var(--line,#dce2d8);border-radius:7px;padding:18px;overflow-wrap:anywhere}.entry-heading{display:flex;gap:10px;justify-content:space-between;align-items:start}.entry-heading strong{font-size:13px}.entry-heading span{display:block;margin-top:6px;color:var(--muted,#66756d);font-size:10px;text-transform:capitalize}.entry-heading time{font:8px/1.7 var(--mono,Consolas,monospace);color:var(--muted,#66756d);white-space:nowrap}.journal-entries li>p{font-size:11px;line-height:1.8;margin-top:16px}.entry-note{border-left:2px solid #c7ae85;padding-left:11px;white-space:pre-wrap}.entry-note strong{display:block;font-size:9px;color:var(--muted,#66756d)}.entry-footer{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-top:12px;border-top:1px solid var(--line,#dce2d8);padding-top:8px}.entry-footer>span{font:8px/1.6 var(--mono,Consolas,monospace);color:var(--muted,#66756d);letter-spacing:.4px}.delete-entry{display:inline-flex;align-items:center;gap:5px;background:transparent;border:0;color:#a74222;padding:9px 5px;min-height:38px;font-size:10px!important}.desk-footer{border-top:1px solid var(--line,#dce2d8);background:#fbfbf6;padding:15px 24px;display:flex;align-items:center;justify-content:space-between;gap:15px;color:var(--muted,#66756d);font:8px var(--mono,Consolas,monospace);letter-spacing:.8px}.desk-footer>span:first-child{display:flex;align-items:center;gap:6px;white-space:nowrap}.desk-footer>span:last-child{font:10px var(--sans,'Segoe UI',sans-serif);letter-spacing:0}.preview-dot{height:5px;width:5px;border-radius:50%;background:#d48b58}
@media(max-width:1100px){.desk-grid{grid-template-columns:176px minmax(0,1fr) 220px}.asset-heading{padding:24px 20px 20px}.research-tabs{margin:0 20px}.research-panel{padding:22px 20px 0}.save-area{padding:18px 20px 23px}.risk-sidebar{padding:25px 18px}.risk-sidebar h4{font-size:23px}.evidence-summary{gap:10px}.evidence-summary>div:first-child{gap:7px}.evidence-summary span{font-size:8px}}
@media(max-width:900px){.desk-grid{grid-template-columns:170px minmax(0,1fr)}.risk-sidebar{grid-column:1/-1;border-top:1px solid var(--line,#dce2d8);border-left:0;display:grid;grid-template-columns:1fr 1fr;column-gap:36px;padding:25px 28px}.risk-sidebar>.small-heading{grid-column:1/-1;margin-bottom:15px}.risk-sidebar h4{margin:0;grid-column:1}.risk-intro{grid-column:1}.compact-scenarios{grid-column:1;margin:20px 0}.weight-label,.risk-sidebar input,.range-ends{grid-column:1}.stress-result{grid-column:2;grid-row:2/5;margin:0;padding:0;border:0}.stress-result strong{font-size:45px}.risk-checklist{grid-column:2;grid-row:5/7;margin:0}.risk-footnote{grid-column:2;grid-row:7/9;margin:15px 0 0!important}}
@media(max-width:620px){.research-desk{border-radius:10px}.desk-header{padding:15px;gap:8px}.desk-title{gap:8px;font-size:12px}.desk-title small{font-size:7px;letter-spacing:.9px}.desk-mark{width:30px;height:30px;font-size:24px}.journal-toggle{padding:8px;font-size:10px!important;gap:5px}.desk-grid{display:block}.watchlist{border-right:0;border-bottom:1px solid var(--line,#dce2d8);padding:17px 14px 12px}.watchlist>.small-heading{padding:0 2px;font-size:8px}.asset-search{margin:12px 0 9px}.asset-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:5px}.asset-row{margin:0;padding:12px 10px}.asset-name strong{font-size:12px}.asset-name small{font-size:9px}.watchlist-note{padding:10px 2px 0;font-size:9px}.watchlist-note br{display:none}.search-empty{padding:14px}.asset-heading{padding:23px 20px 17px}.asset-heading h3{font-size:27px}.main-price{font-size:19px}.research-panel{min-height:0;padding-top:22px;padding-bottom:5px}.thesis-copy{font-size:14px}.counter-case p{font-size:11px}.evidence-summary span{font-size:9px}.save-area{padding-top:18px}.save-row small{max-width:116px}.save-button{min-height:44px}.risk-sidebar{display:block;padding:24px 20px}.risk-sidebar h4{margin-top:17px;font-size:28px}.risk-sidebar h4 br{display:none}.risk-intro{margin-top:10px!important}.compact-scenarios{margin:21px 0}.compact-scenarios button{min-height:42px}.weight-label{font-size:11px}.risk-sidebar input[type='range']{min-height:34px}.stress-result{margin-top:24px;padding-top:21px;border-top:1px solid #d4dccb}.stress-result>span,.stress-result p,.risk-checklist li{font-size:11px}.risk-checklist{margin-top:20px}.risk-footnote{margin-top:18px!important;font-size:10px}.desk-feedback{padding:14px 20px}.storage-error{display:block}.local-journal{padding:22px 18px}.journal-heading{align-items:start}.journal-heading h4{font-size:24px}.journal-actions{gap:3px}.journal-actions .quiet-button{font-size:10px!important;padding:8px}.journal-entries{grid-template-columns:1fr}.journal-empty{padding:30px 0 15px}.undo-row{padding:8px 10px}.desk-footer{align-items:start;padding:14px 18px}.desk-footer>span:last-child{max-width:160px;line-height:1.6;text-align:right;font-size:9px}}
@media(prefers-reduced-motion:reduce){.research-desk *,.research-desk *::before,.research-desk *::after{transition:none!important;animation:none!important;scroll-behavior:auto!important}}
</style>
