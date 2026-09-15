<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { ArrowDown, ArrowRight, ArrowUpRight, Check, FileText, Fingerprint, Menu, SlidersHorizontal, Wallet, X } from 'lucide-vue-next'
import MarketCockpit from './components/MarketCockpit.vue'
import WalletModal from './components/WalletModal.vue'
import { migrateBrandStorage, storageKeys } from './brand'

const walletOpen = ref(false)
const menuOpen = ref(false)
const connectedAccount = ref('')
const email = ref('')
const subscribed = ref(false)
const emailError = ref('')
const emailNotice = ref('')
const workbench = ref(null)
const menuButton = ref(null)
const activeLayer = ref(0)
const shortAccount = computed(() => connectedAccount.value ? `${connectedAccount.value.slice(0, 6)}…${connectedAccount.value.slice(-4)}` : '')
const layers = [
  { label: 'Evidence', icon: FileText, title: 'Start with what you can inspect.', tag: 'RESEARCH BRIEF', headline: 'A thesis is only as useful as its counter-case.', left: 'The supporting case', right: 'What could change it', detail: 'Separate the observation from the interpretation. Keep both in view.' },
  { label: 'Scenarios', icon: SlidersHorizontal, title: 'Give uncertainty a little structure.', tag: 'SCENARIO LAB', headline: 'Explore the downside before you make a move.', left: 'Position size', right: 'Downside assumption', detail: 'Change the assumptions and see the impact. Scenarios are illustrations, not forecasts.' },
  { label: 'Journal', icon: Fingerprint, title: 'Keep the thinking behind the decision.', tag: 'DECISION JOURNAL', headline: 'Remember the why. Revisit it with context.', left: 'Your original thesis', right: 'Your risk boundary', detail: 'Save a snapshot on this device. Return to it, export it, or remove it when you choose.' },
]
const layer = computed(() => layers[activeLayer.value])
let provider
let sessionRevision = 0
function invalidateSession() {
  sessionRevision += 1
  connectedAccount.value = ''
  try { sessionStorage.removeItem(storageKeys.session) } catch { /* In-memory session cleared. */ }
}
function onAccountsChanged(accounts) {
  if (!accounts?.[0] || accounts[0].toLowerCase() !== connectedAccount.value.toLowerCase()) invalidateSession()
}
function onChainChanged(chain) { if (Number(chain) !== 4663) invalidateSession() }
function attachProvider(nextProvider) {
  if (provider === nextProvider) return
  provider?.removeListener?.('accountsChanged', onAccountsChanged)
  provider?.removeListener?.('chainChanged', onChainChanged)
  provider?.removeListener?.('disconnect', invalidateSession)
  provider = nextProvider
  provider?.on?.('accountsChanged', onAccountsChanged)
  provider?.on?.('chainChanged', onChainChanged)
  provider?.on?.('disconnect', invalidateSession)
}
onMounted(async () => {
  migrateBrandStorage()
  try {
    const saved = localStorage.getItem(storageKeys.email)
    if (saved && /^\S+@\S+\.\S+$/.test(saved)) { email.value = saved; subscribed.value = true }
  } catch { /* Saving reports storage errors explicitly. */ }
  attachProvider(window.ethereum)
  const revision = sessionRevision
  try {
    const session = JSON.parse(sessionStorage.getItem(storageKeys.session) || 'null')
    if (session?.account && provider) {
      const [accounts, chain] = await Promise.all([provider.request({ method: 'eth_accounts' }), provider.request({ method: 'eth_chainId' })])
      if (revision !== sessionRevision) return
      if (Number(chain) === 4663 && accounts?.[0]?.toLowerCase() === session.account.toLowerCase()) connectedAccount.value = session.account
      else invalidateSession()
    } else if (session) invalidateSession()
  } catch { if (revision === sessionRevision) invalidateSession() }
})
onBeforeUnmount(() => {
  provider?.removeListener?.('accountsChanged', onAccountsChanged)
  provider?.removeListener?.('chainChanged', onChainChanged)
  provider?.removeListener?.('disconnect', invalidateSession)
})
function handleConnected(account) { attachProvider(window.ethereum); sessionRevision += 1; connectedAccount.value = account; walletOpen.value = false }
function closeMenu() { menuOpen.value = false }
function escapeMenu() { if (menuOpen.value) { closeMenu(); menuButton.value?.focus() } }
async function openJournal() {
  workbench.value?.openJournal()
  await nextTick()
  window.location.hash = 'cockpit'
}
function subscribe() {
  emailError.value = ''; emailNotice.value = ''
  const value = email.value.trim()
  if (!/^\S+@\S+\.\S+$/.test(value)) { emailError.value = 'Enter a valid email address to save your interest.'; return }
  try {
    localStorage.setItem(storageKeys.email, value)
    email.value = value; subscribed.value = true
    emailNotice.value = 'Interest saved on this device. You have not joined a mailing list.'
  } catch { emailError.value = 'Your browser could not save this. Allow site storage and try again.' }
}
function forgetEmail() {
  try {
    localStorage.removeItem(storageKeys.email)
    email.value = ''; subscribed.value = false; emailError.value = ''
    emailNotice.value = 'Your saved email has been removed from this device.'
  } catch { emailError.value = 'Your browser could not remove the saved email. Check site storage settings.' }
}
</script>

<template>
  <div class="site-shell" :inert="walletOpen || undefined" @keydown.esc="escapeMenu">
    <a class="skip-link" href="#cockpit">Skip to research workspace</a>
    <header class="site-header">
      <a href="#top" class="brand-lockup" aria-label="Decisift home" @click="closeMenu"><img src="/logo-mark.svg" width="34" height="34" alt="" /><span>Decisift<span class="brand-period">.</span></span></a>
      <nav id="main-navigation" :class="['main-nav', { open: menuOpen }]" aria-label="Main navigation"><a href="#cockpit" @click="closeMenu">Workspace</a><a href="#method" @click="closeMenu">Our approach</a><a href="#journal" @click="closeMenu">Decision journal</a><a href="#roadmap" @click="closeMenu">Roadmap</a></nav>
      <div class="header-actions"><span class="preview-pill"><i></i> Research preview</span><button v-if="connectedAccount" class="button wallet-button" @click="invalidateSession" :aria-label="`End local session for ${shortAccount}`"><Check :size="15" /><span>{{ shortAccount }}</span><span class="session-end">End session</span></button><button v-else class="button wallet-button" @click="walletOpen = true"><Wallet :size="16" /><span>Connect wallet</span></button><button ref="menuButton" class="mobile-menu" :aria-label="menuOpen ? 'Close navigation' : 'Open navigation'" :aria-expanded="menuOpen" aria-controls="main-navigation" @click="menuOpen = !menuOpen"><X v-if="menuOpen" :size="22" /><Menu v-else :size="22" /></button></div>
    </header>
    <main id="top">
      <section class="hero-section page-container" aria-labelledby="hero-title">
        <div class="hero-copy"><p class="eyebrow"><span class="tiny-cross">✳</span> A CLEARER VIEW OF ONCHAIN EQUITIES</p><h1 id="hero-title">Sift the noise.<br /><span>Decide with<br class="desktop-break" /> clarity.</span></h1><p class="hero-lede">Markets move fast. Your thinking deserves space. Bring the evidence, the counter-case, and the risk into one clear view.</p><div class="hero-cta-row"><a href="#cockpit" class="button primary">Explore the workspace <ArrowUpRight :size="18" /></a><a href="#method" class="hero-secondary">Meet your process <ArrowRight :size="16" /></a></div><div class="hero-note"><span class="note-line"></span><span>Built for tokenized stocks on Robinhood Chain.<br />Open the preview. No wallet needed.</span></div></div>
        <div class="clarity-panel"><div class="panel-topline"><span><span class="panel-dot"></span> THE DECISIFT PROCESS</span><span>01 — 03</span></div><h2>{{ layer.title }}</h2><div class="sift-visual" aria-hidden="true"><div class="input-lines"><i></i><i></i><i></i><i></i><i></i></div><svg viewBox="0 0 400 105" preserveAspectRatio="none"><path d="M0 9L184 43M0 30L184 43M0 52L184 52M0 75L184 61M0 96L184 61"/><path class="output-path" d="M218 43L400 26M218 52L400 52M218 61L400 78"/><rect x="178" y="26" width="46" height="52" rx="7"/><path class="filter-path" d="M190 39H212M194 51H212M202 63H212"/></svg><div class="output-lines"><i></i><i></i><i></i></div><span class="sift-label label-left">INFORMATION</span><span class="sift-label label-right">PERSPECTIVE</span></div><article class="perspective-card" aria-live="polite"><div class="card-kicker"><component :is="layer.icon" :size="15" /><span>{{ layer.tag }}</span><span class="sample-tag">ILLUSTRATIVE</span></div><h3>{{ layer.headline }}</h3><div class="perspective-columns"><span><i></i>{{ layer.left }}</span><span><i></i>{{ layer.right }}</span></div><p>{{ layer.detail }}</p></article><div class="layer-selector" aria-label="Explore the Decisift process"><button v-for="(item, index) in layers" :key="item.label" :aria-pressed="activeLayer === index" @click="activeLayer = index"><span>0{{ index + 1 }}</span>{{ item.label }}<ArrowUpRight v-if="activeLayer === index" :size="14" /></button></div><span class="panel-corner" aria-hidden="true">d.</span></div>
      </section>
      <div class="principle-strip page-container" aria-label="Product principles"><span><FileText :size="17" /> Evidence before opinion</span><span><SlidersHorizontal :size="17" /> Downside before action</span><span><Fingerprint :size="17" /> Your keys. Your decisions.</span><a href="#cockpit">A little more perspective <ArrowDown :size="14" /></a></div>
      <section id="cockpit" class="workspace-section page-container" aria-labelledby="workspace-title"><div class="section-intro"><div><p class="eyebrow">01 / YOUR RESEARCH DESK</p><h2 id="workspace-title">Make room for a better decision.</h2></div><p>Choose an asset. Question the thesis.<br />See what changes when you change the assumptions.</p></div><MarketCockpit ref="workbench" /><div class="workspace-caption"><span><span class="small-square"></span> Illustrative market data · Research preview</span><span>Research is not investment advice.</span></div></section>
      <section id="method" class="method-section page-container" aria-labelledby="method-title"><div class="section-intro"><div><p class="eyebrow">02 / A PROCESS YOU CAN FOLLOW</p><h2 id="method-title">Good decisions have a paper trail.</h2></div><a class="text-link" href="#cockpit">Try the process <ArrowUpRight :size="17" /></a></div><div class="method-grid"><article class="method-item"><div class="method-top"><span>01</span><FileText :size="23" stroke-width="1.5" /></div><h3>Look beneath the headline.</h3><p>Read the thesis alongside its counter-case. Understand which inputs support a view and where the uncertainty begins.</p><span class="method-bottom">EVIDENCE, WITH CONTEXT <ArrowRight :size="16" /></span></article><article class="method-item"><div class="method-top"><span>02</span><SlidersHorizontal :size="23" stroke-width="1.5" /></div><h3>Put the downside in view.</h3><p>Turn a broad idea into a concrete scenario. Adjust position size and compare the impact of bear, base, and bull assumptions.</p><span class="method-bottom">ASSUMPTIONS YOU CAN CHANGE <ArrowRight :size="16" /></span></article><article class="method-item"><div class="method-top"><span>03</span><Fingerprint :size="23" stroke-width="1.5" /></div><h3>Leave a note for future you.</h3><p>Capture the thesis and the scenario together. Keep your reasoning close so you can revisit what you believed, and why.</p><span class="method-bottom">A DECISION WITH A MEMORY <Check :size="16" /></span></article></div></section>
      <section id="journal" class="journal-section" aria-labelledby="journal-title"><div class="journal-layout page-container"><div class="journal-copy"><p class="eyebrow">03 / THE DECISION JOURNAL</p><h2 id="journal-title">Your next insight<br />might be in your<br /><em>last decision.</em></h2><p>A position tells you what you own. A journal helps you remember what you were thinking. Save the context, revisit the assumptions, and keep learning.</p><button class="button light-button" @click="openJournal">Open your journal <ArrowUpRight :size="18" /></button><span class="journal-note">Stored on this device. Yours to export or delete.</span></div><div class="journal-preview"><div class="journal-sheet"><div class="journal-sheet-top"><span><FileText :size="16" /> DECISION NOTE</span><span>EXAMPLE / 001</span></div><h3>The thesis is a<br />starting point.</h3><p class="handwritten">Keep the counter-case close.</p><dl><div><dt>ASSET</dt><dd>AAPL <span>Apple Inc.</span></dd></div><div><dt>THESIS</dt><dd>Services resilience supports the case.</dd></div><div><dt>COUNTER-CASE</dt><dd>Valuation leaves less room for error.</dd></div><div><dt>NEXT QUESTION</dt><dd>What evidence would change my view?</dd></div></dl><div class="sheet-footer"><span class="small-square"></span> A snapshot of your thinking. Not a forecast.</div></div><div class="journal-underlay" aria-hidden="true"></div><span class="journal-margin" aria-hidden="true">THINK. RECORD. REVISIT.</span></div></div></section>
      <section id="roadmap" class="roadmap-section page-container" aria-labelledby="roadmap-title"><div class="section-intro"><div><p class="eyebrow">04 / WHAT COMES NEXT</p><h2 id="roadmap-title">Built with intention.<br />One step at a time.</h2></div><p>The research experience comes first.<br />Each new capability has a clear release gate.</p></div><ol class="roadmap-list"><li><span class="roadmap-number">01</span><div><h3>Research workspace</h3><p>Illustrative briefs, scenarios, and a local decision journal.</p></div><span class="roadmap-status current"><i></i> Preview available</span></li><li><span class="roadmap-number">02</span><div><h3>Connected intelligence</h3><p>Verified data sources and wallet context, after privacy review.</p></div><span class="roadmap-status">In planning</span></li><li><span class="roadmap-number">03</span><div><h3>Verifiable intent</h3><p>Testnet intent and a proof registry, subject to security review.</p></div><span class="roadmap-status">Research stage</span></li><li><span class="roadmap-number">04</span><div><h3>Carefully scoped execution</h3><p>Limited mainnet routing, gated by audit and legal approval.</p></div><span class="roadmap-status">Gated</span></li></ol></section>
      <section id="beta" class="waitlist-section page-container" aria-labelledby="beta-title"><div class="waitlist-copy"><p class="eyebrow">A MORE THOUGHTFUL START</p><h2 id="beta-title">Less scrolling.<br />More understanding.</h2><p>Interested in what we’re building? Save your email as a reminder on this device while you explore.</p></div><form class="waitlist-form" @submit.prevent="subscribe"><label for="email">Your email address</label><div class="email-controls"><input id="email" v-model="email" type="email" autocomplete="email" inputmode="email" placeholder="you@example.com" required maxlength="254" :aria-invalid="!!emailError" aria-describedby="email-help email-feedback" @input="subscribed = false; emailNotice = ''; emailError = ''" /><button class="button primary" type="submit"><Check v-if="subscribed" :size="17" />{{ subscribed ? 'Saved locally' : 'Save my interest' }}<ArrowRight v-if="!subscribed" :size="17" /></button></div><p id="email-help">This preview saves only to your browser. No email is sent and no mailing list subscription is created.</p><p v-if="emailError" id="email-feedback" class="form-error" role="alert">{{ emailError }}</p><p v-else id="email-feedback" class="form-success" role="status">{{ emailNotice }}</p><button v-if="subscribed" class="text-link forget-email" type="button" @click="forgetEmail">Remove saved email <X :size="14" /></button></form></section>
    </main>
    <footer class="site-footer page-container"><div class="footer-top"><a href="#top" class="brand-lockup" aria-label="Decisift home"><img src="/logo-mark.svg" width="34" height="34" alt="" /><span>Decisift<span class="brand-period">.</span></span></a><p>Sift the noise. Decide with clarity.</p><div class="footer-links"><a href="#cockpit">Workspace <ArrowUpRight :size="14" /></a><a href="https://docs.robinhood.com/chain/" target="_blank" rel="noopener noreferrer">Chain docs <ArrowUpRight :size="14" /></a></div></div><div class="footer-bottom"><p>Decisift is independent and is not affiliated with Robinhood Markets, Inc. Tokenized stocks and onchain services are subject to eligibility, jurisdictional, and market risks. Research is not investment advice.</p><span>© 2026 Decisift<br />Made for considered decisions.</span></div></footer>
  </div>
  <WalletModal :open="walletOpen" @close="walletOpen = false" @connected="handleConnected" @session-invalidated="invalidateSession" />
</template>
