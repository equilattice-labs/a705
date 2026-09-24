<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ArrowUpRight, BarChart3, Check, Coins, Copy, ExternalLink, Menu, ShieldCheck, X } from 'lucide-vue-next'
import { brand, storageKeys } from './brand.js'
import { DEFAULT_BASE_PRICE, calculateScenario, createJournalRecord, restoreJournalRecord, validateScenarioInputs } from './scenario.js'
import { solanaConfig, solanaExplorerToken } from './solana.js'
import SolanaWalletButton from './components/SolanaWalletButton.vue'

const normalizePath = value => ['/', '/signal', '/docs', '/stats'].includes(value.replace(/\/$/, '')) ? value.replace(/\/$/, '') || '/' : '/'
const path = ref(normalizePath(location.pathname))
const menuOpen = ref(false)
const wallet = ref(null)
const walletMessage = ref('')
const amount = ref('1000')
const basePrice = ref('1.00')
const movePct = ref('-15')
const note = ref('')
const step = ref('form')
const record = ref(null)
const errors = ref({})
const feedback = ref('')
const storageNotice = ref('')
const heading = ref(null)
const peers = Object.freeze([
  { symbol: 'SOL', status: 'No feed', tone: 'neutral' },
  { symbol: 'JUP', status: 'No feed', tone: 'neutral' },
  { symbol: 'BONK', status: 'No feed', tone: 'neutral' },
  { symbol: 'WIF', status: 'No feed', tone: 'neutral' },
])
const sections = [
  { id: 'overview', title: 'Overview' },
  { id: 'scenario', title: 'Scenario math' },
  { id: 'journal', title: 'Local journal' },
  { id: 'limits', title: 'Limits' },
]
const stages = ['Inputs recorded', 'Assumption reviewed', 'Limits reviewed', 'Review complete']
const currency = (value, digits = 2) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value)
const percent = value => `${Number(value) > 0 ? '+' : ''}${Number(value).toFixed(2)}%`
const input = computed(() => ({ amount: amount.value, basePrice: basePrice.value, movePct: movePct.value, note: note.value }))
const result = computed(() => record.value ? calculateScenario(record.value) : null)
const remaining = computed(() => 1000 - note.value.length)
const activeTitle = computed(() => ({ '/': 'Market overview', '/signal': 'Scenario lab', '/docs': 'Protocol notes', '/stats': 'Market board' }[path.value] || 'Lumquira'))

async function focusHeading() { heading.value?.focus({ preventScroll: true }) }
async function navigate(to) {
  menuOpen.value = false
  const [target, hash] = to.split('#')
  const next = normalizePath(target || '/')
  history.pushState({}, '', to)
  path.value = next
  await focusHeading()
  if (hash) document.getElementById(hash)?.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' })
  else scrollTo({ top: 0, behavior: 'smooth' })
}
function onPop() { path.value = normalizePath(location.pathname); menuOpen.value = false }
function onKey(event) { if (event.key === 'Escape') menuOpen.value = false }
function onWalletConnected(address, name) {
  wallet.value = address
  walletMessage.value = `${name || 'Solana wallet'} linked. Only its public address is displayed; transactions are off.`
}
function onWalletDisconnected() { wallet.value = null; walletMessage.value = 'Wallet disconnected.' }
async function review() {
  const validation = validateScenarioInputs(input.value)
  errors.value = validation.errors; feedback.value = ''
  if (!validation.valid) { document.querySelector('[aria-invalid="true"]')?.focus(); return }
  record.value = createJournalRecord(validation.value, { id: `LM-${crypto.randomUUID()}`, createdAt: new Date().toISOString() })
  step.value = 'review'; await focusHeading()
}
function persist() {
  try { localStorage.setItem(storageKeys.journal, JSON.stringify(record.value)); feedback.value = 'Saved locally on this device.'; return true }
  catch { storageNotice.value = 'Browser storage is unavailable. Download your journal to keep a copy.'; return false }
}
async function save() { persist(); step.value = 'journal'; await focusHeading() }
function edit() { if (record.value) { amount.value = String(record.value.amount); basePrice.value = String(record.value.basePrice); movePct.value = String(record.value.movePct); note.value = record.value.note }; errors.value = {}; step.value = 'form'; focusHeading() }
function newScenario() { record.value = null; step.value = 'form'; amount.value = '1000'; basePrice.value = DEFAULT_BASE_PRICE; movePct.value = '-15'; note.value = ''; errors.value = {}; feedback.value = ''; focusHeading() }
function changeStage(delta) { record.value = { ...record.value, stage: Math.max(0, Math.min(3, record.value.stage + delta)) }; persist() }
function removeJournal() { localStorage.removeItem(storageKeys.journal); newScenario(); feedback.value = 'Local journal removed.' }
function copyMint() { if (solanaConfig.tokenMint) navigator.clipboard?.writeText(solanaConfig.tokenMint); feedback.value = solanaConfig.tokenMint ? 'Mint address copied.' : `Mint address will appear after ${solanaConfig.cluster} deployment.` }
function downloadJournal() {
  if (!record.value) return
  const data = { ...record.value, calculations: result.value, disclaimer: 'User-entered price and move. Not a quote or forecast. This interface does not enable wallet transactions.' }
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })); const a = document.createElement('a'); a.href = url; a.download = `lumquira-${record.value.id.toLowerCase()}.json`; a.click(); URL.revokeObjectURL(url); feedback.value = 'Journal export prepared.'
}
watch(path, () => { document.title = `${activeTitle.value} / ${brand.name}` }, { immediate: true })
onMounted(() => {
  addEventListener('popstate', onPop); addEventListener('keydown', onKey)
  try { const activeRaw = localStorage.getItem(storageKeys.journal); const legacyBrandRaw = activeRaw ? null : localStorage.getItem('kinovra:journal:v1'); const raw = activeRaw || legacyBrandRaw; if (raw) { const restored = restoreJournalRecord(JSON.parse(raw)); if (restored.valid) { record.value = restored.value; amount.value = String(restored.value.amount); basePrice.value = String(restored.value.basePrice); movePct.value = String(restored.value.movePct); note.value = restored.value.note; step.value = 'journal'; if (restored.migrated || legacyBrandRaw) { localStorage.setItem(storageKeys.journal, JSON.stringify(restored.value)); feedback.value = restored.migrated ? 'Legacy price retained as your assumption in the new Lumquira format.' : 'Local journal moved to the Lumquira namespace.' } } } } catch { storageNotice.value = 'Saved journal could not be restored.' }
})
onBeforeUnmount(() => { removeEventListener('popstate', onPop); removeEventListener('keydown', onKey) })
</script>

<template>
  <div class="terminal-app">
    <a href="#main-content" class="skip-link">Skip to content</a>
    <header class="topbar">
      <div class="topbar-inner">
      <a href="/" class="brand" aria-label="Lumquira home" @click.prevent="navigate('/')"><span class="brand-mark"><Coins :size="17" /></span><span><b>LUMQUIRA</b><small>SOLANA / RESEARCH DESK</small></span></a>
        <nav class="desktop-nav" aria-label="Primary navigation"><a v-for="item in [['/','Overview'],['/signal','Scenario'],['/stats','Board'],['/docs','Notes']]" :key="item[0]" :href="item[0]" :class="{ active: path === item[0] }" @click.prevent="navigate(item[0])">{{ item[1] }}</a></nav>
        <div class="top-actions"><SolanaWalletButton @connected="onWalletConnected" @disconnected="onWalletDisconnected" /><button class="menu-toggle" :aria-expanded="menuOpen" aria-label="Open navigation" @click="menuOpen = !menuOpen"> <X v-if="menuOpen" :size="20" /><Menu v-else :size="20" /></button></div>
      </div>
      <div class="market-tape"><span class="tape-label"><span class="offline-dot"></span> SOLANA REFERENCE LIST</span><span v-for="peer in peers" :key="peer.symbol" class="tape-item"><b>{{ peer.symbol }}</b><strong>{{ peer.status }}</strong><em :class="peer.tone">read only</em></span><span class="tape-source">No live feed / illustrative context</span></div>
      <nav v-if="menuOpen" class="mobile-nav" aria-label="Mobile navigation"><a v-for="item in [['/','Overview'],['/signal','Scenario'],['/stats','Board'],['/docs','Notes']]" :key="item[0]" :href="item[0]" @click.prevent="navigate(item[0])">{{ item[1] }}</a></nav>
    </header>

    <main id="main-content">
      <p v-if="walletMessage" class="wallet-message" role="status">{{ walletMessage }}</p>
      <template v-if="path === '/'">
        <section class="dashboard-hero"><div><div class="eyebrow"><span class="live-dot"></span> SOLANA MARKET WORKSPACE</div><h1 ref="heading" tabindex="-1">Make the move.<br /><em>Keep the why.</em></h1><p class="hero-lede">Lumquira is a private desk for reading public context, testing a price thesis and keeping the evidence close.</p><div class="hero-actions"><a class="btn btn-primary" href="/signal" @click.prevent="navigate('/signal')">Open scenario lab <ArrowUpRight :size="16" /></a><a class="btn btn-ghost" href="/stats" @click.prevent="navigate('/stats')">View board <BarChart3 :size="16" /></a></div></div><div class="hero-terminal"><div class="terminal-head"><span>LMQR / USER INPUT</span><span class="status-chip">{{ solanaConfig.tokenConfigured ? 'MINT READY' : 'MINT PENDING' }}</span></div><div class="terminal-price">—<span>USD</span></div><div class="terminal-change">-- market data provider is not configured <span>{{ solanaConfig.cluster.toUpperCase() }}</span></div><div class="terminal-status"><span><b>MINT</b><strong>{{ solanaConfig.tokenConfigured ? 'Configured' : 'Pending' }}</strong></span><span><b>QUOTE FEED</b><strong>Offline</strong></span><span><b>CLUSTER</b><strong>{{ solanaConfig.cluster }}</strong></span></div><div class="terminal-foot"><span>Use your own reference</span><span>Illustrative only</span></div></div></section>
        <section class="section"><div class="section-head"><div><span class="eyebrow">DESK STATUS</span><h2>One desk for the next decision.</h2></div><span class="mono">NO WALLET EXECUTION</span></div><div class="metric-grid"><article class="metric-card accent"><span class="metric-label">NETWORK</span><strong>Solana</strong><small>{{ solanaConfig.cluster }} / RPC endpoint selected</small></article><article class="metric-card"><span class="metric-label">MINT</span><strong>{{ solanaConfig.tokenConfigured ? 'Address set' : 'Pending' }}</strong><small>{{ solanaConfig.tokenConfigured ? `${solanaConfig.cluster} address format checked` : `Awaiting ${solanaConfig.cluster} mint deployment` }}</small></article><article class="metric-card"><span class="metric-label">JOURNAL</span><strong>{{ record ? '1 active' : 'Empty' }}</strong><small>Stored in this browser only</small></article><article class="metric-card"><span class="metric-label">WALLET</span><strong>{{ wallet ? 'Linked' : 'Offline' }}</strong><small>Public address display only</small></article></div></section>
        <section class="section split-section"><div><span class="eyebrow">THE LUMQUIRA LOOP</span><h2>Observe. Stress test. Record.</h2><p>Keep the chain boundary simple while market data is being prepared. Enter a reference price yourself; every assumption stays visible.</p><a class="text-link" href="/docs" @click.prevent="navigate('/docs')">Read protocol notes <ArrowUpRight :size="14" /></a></div><div class="steps-list"><div v-for="(label, i) in stages" :key="label"><span>0{{ i + 1 }}</span><strong>{{ label }}</strong><small>{{ ['Choose the asset context.','Set amount, price and move.','Review fees and execution limits.','Export your reasoning.'][i] }}</small></div></div></section>
      </template>

      <template v-else-if="path === '/signal'">
        <section class="page-shell"><div class="eyebrow"><span class="live-dot"></span> SCENARIO LAB / {{ solanaConfig.cluster.toUpperCase() }}</div><h1 ref="heading" tabindex="-1">Put a number<br /><em>behind the thesis.</em></h1><p class="page-lede">Enter an amount, your own reference price and a hypothetical move. The arithmetic stays local and is not a quote or forecast.</p><p v-if="storageNotice" class="notice" role="alert">{{ storageNotice }}</p><p v-if="feedback" class="feedback" role="status">{{ feedback }}</p>
          <div v-if="step === 'form'" class="signal-layout"><form class="panel signal-form" @submit.prevent="review"><div class="panel-head"><div><span class="step">01 / INPUTS</span><h2>Set your assumption.</h2></div><span class="status-chip">NO TX</span></div><label for="amount">Amount <span class="unit">LMQR</span></label><input id="amount" v-model="amount" class="field" inputmode="decimal" :aria-invalid="Boolean(errors.amount)" /><p v-if="errors.amount" class="input-error">{{ errors.amount }}</p><label for="base-price">Reference price <span class="unit">USD / LMQR</span></label><input id="base-price" v-model="basePrice" class="field" inputmode="decimal" :aria-invalid="Boolean(errors.basePrice)" /><p v-if="errors.basePrice" class="input-error">{{ errors.basePrice }}</p><label for="move">Hypothetical move <output>{{ movePct }}%</output></label><input id="move" v-model="movePct" class="range" type="range" min="-90" max="100" step="0.5" /><div class="range-scale"><span>-90%</span><span>0</span><span>+100%</span></div><label for="move-text">Exact percentage</label><input id="move-text" v-model="movePct" class="field" inputmode="decimal" :aria-invalid="Boolean(errors.movePct)" /><p v-if="errors.movePct" class="input-error">{{ errors.movePct }}</p><label for="note">Thesis note <span class="unit">OPTIONAL</span></label><textarea id="note" v-model="note" class="field note-input" maxlength="1000" placeholder="What would make this move plausible?"></textarea><div class="char-count">{{ remaining }} characters remaining</div><button class="btn btn-primary btn-wide" type="submit">Review scenario <ArrowUpRight :size="16" /></button></form><aside class="panel signal-aside"><span class="step">USER INPUT / NO QUOTE</span><strong class="baseline-price">—</strong><span class="muted">LMQR / USD, entered locally</span><div class="aside-divider"></div><p>No live quote is loaded. Enter a reference price for this private what-if; it is not a forecast or execution price.</p><div class="aside-row"><span>Network</span><b>Solana {{ solanaConfig.cluster }}</b></div><div class="aside-row"><span>Wallet</span><b>{{ wallet ? 'Connected' : 'Optional' }}</b></div></aside></div>
          <div v-else-if="step === 'review'" class="review-layout"><div class="panel review-card"><div class="panel-head"><div><span class="step">02 / REVIEW</span><h2>Check the numbers.</h2><small class="muted">Calculated from user-entered assumptions only.</small></div><ShieldCheck :size="23" /></div><div class="review-rows"><div><span>Reference amount</span><strong>{{ Number(amount).toLocaleString() }} LMQR</strong></div><div><span>Reference price</span><strong>{{ currency(result.basePrice, 4) }}</strong></div><div><span>Reference value</span><strong>{{ currency(result.baselineValue, 4) }}</strong></div><div><span>Scenario move</span><strong :class="Number(movePct) >= 0 ? 'positive' : 'negative'">{{ percent(movePct) }}</strong></div><div><span>Scenario value</span><strong>{{ currency(result.scenarioValue, 4) }}</strong></div></div><div class="delta-box"><span>Change in reference value</span><strong :class="result.deltaUsd >= 0 ? 'positive' : 'negative'">{{ result.deltaUsd >= 0 ? '+' : '' }}{{ currency(result.deltaUsd, 4) }}</strong></div><div class="form-actions"><button class="btn btn-primary" @click="save">Save to journal <Check :size="16" /></button><button class="btn btn-ghost" @click="edit">Edit inputs</button></div></div></div>
          <div v-else class="journal-layout"><div class="panel journal-main"><div class="panel-head"><div><span class="step">03 / JOURNAL</span><h2>Your local record.</h2></div><span class="status-chip success"><Check :size="12" /> SAVED</span></div><div class="stage-track"><button v-for="(label, i) in stages" :key="label" :class="{ current: record.stage === i, done: record.stage > i }" @click="changeStage(i - record.stage)"><span>{{ record.stage > i ? '✓' : `0${i + 1}` }}</span>{{ label }}</button></div><div class="journal-summary"><div><span>Amount</span><strong>{{ Number(record.amount).toLocaleString() }} LMQR</strong></div><div><span>Reference price</span><strong>{{ currency(record.basePrice, 4) }}</strong></div><div><span>Move</span><strong>{{ percent(record.movePct) }}</strong></div><div><span>Scenario value</span><strong>{{ currency(result.scenarioValue, 4) }}</strong></div></div><blockquote v-if="record.note">{{ record.note }}</blockquote><p class="muted">Created {{ new Date(record.createdAt).toLocaleString() }}. Stored only in this browser.</p><div class="form-actions"><button class="btn btn-primary" @click="downloadJournal">Export JSON <ArrowUpRight :size="16" /></button><button class="btn btn-ghost" @click="edit">Edit</button><button class="danger-link" @click="removeJournal">Delete local record</button></div></div></div>
        </section>
      </template>

      <template v-else-if="path === '/stats'"><section class="page-shell"><div class="eyebrow"><span class="live-dot"></span> MARKET BOARD / WATCHLIST</div><h1 ref="heading" tabindex="-1">A compact view<br /><em>of the tape.</em></h1><p class="page-lede">Watchlist symbols are references only. Quotes remain blank until a market data provider is selected.</p><div class="board-grid"><article v-for="peer in peers" :key="peer.symbol" class="board-card"><div><span class="coin-dot" :class="peer.symbol.toLowerCase()"></span><b>{{ peer.symbol }}</b><span class="muted">/ USD</span></div><strong>—</strong><em class="muted">No feed connected</em><small class="feed-status">NO LIVE QUOTE SOURCE</small></article></div><div class="panel comparison"><div class="panel-head"><div><span class="step">SOLANA CONTEXT</span><h2>Network status</h2></div><span class="status-chip">READ ONLY</span></div><div class="readiness"><div><span>Selected cluster</span><b>{{ solanaConfig.cluster }}</b></div><div><span>Devnet mint</span><a v-if="solanaExplorerToken('devnet')" :href="solanaExplorerToken('devnet')" target="_blank" rel="noreferrer">Open devnet token <ExternalLink :size="13" /></a><b v-else>Pending deployment</b></div><div><span>Testnet mint</span><a v-if="solanaExplorerToken('testnet')" :href="solanaExplorerToken('testnet')" target="_blank" rel="noreferrer">Open testnet token <ExternalLink :size="13" /></a><b v-else>Pending deployment</b></div><div><span>Wallet execution</span><b>Disabled</b></div></div></div></section></template>

      <template v-else><section class="page-shell docs-page"><div class="eyebrow"><span class="live-dot"></span> PROTOCOL NOTES / LUMQUIRA</div><h1 ref="heading" tabindex="-1">Keep the chain<br /><em>easy to trust.</em></h1><p class="page-lede">Lumquira keeps scenario work local. Its wallet bridge displays a public address, and its RPC helper is restricted to public reads; this interface does not load market quotes.</p><div class="docs-grid"><nav class="docs-index"><a v-for="item in sections" :key="item.id" :href="`#${item.id}`">{{ item.title }}</a></nav><div class="docs-content"><section id="overview"><span class="step">01 / OVERVIEW</span><h2>Solana token status.</h2><p>The selected network is {{ solanaConfig.cluster }}. The interface reads its public mint address from the matching environment setting; live quotes are not connected.</p></section><section id="scenario"><span class="step">02 / SCENARIO MATH</span><h2>Visible assumptions.</h2><p>Amount multiplied by your entered reference price, then adjusted by your hypothetical percentage. Fees, slippage, taxes and execution are excluded.</p></section><section id="journal"><span class="step">03 / LOCAL JOURNAL</span><h2>Your browser, your record.</h2><p>Journal data stays in localStorage under the Lumquira namespace. Export JSON before clearing site data.</p></section><section id="limits"><span class="step">04 / LIMITS</span><h2>Read only in the browser.</h2><p>The website contains no signer, private key, minting or transaction-submission path. Its RPC helper accepts a small allowlist of public read methods. Configure <code>VITE_SOLANA_DEVNET_TOKEN_MINT</code> and <code>VITE_SOLANA_TESTNET_TOKEN_MINT</code> with the public addresses for their respective networks.</p></section></div></div></section></template>
    </main>
    <footer class="footer"><div><b>LUMQUIRA</b><span>Solana-native research desk</span></div><nav><a href="/docs" @click.prevent="navigate('/docs')">Protocol notes</a><a href="https://x.com/Lumquira" target="_blank" rel="noreferrer">X <ExternalLink :size="12" /></a><button class="icon-link" title="Copy mint address" @click="copyMint"><Copy :size="14" /></button></nav><small>Not financial advice. Wallet transactions are not enabled in this interface.</small></footer>
  </div>
</template>
