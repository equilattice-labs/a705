<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import { brand, migrateBrandStorage, storageKeys } from './brand.js'
import { ArrowRight, Check, ChevronRight, Copy, ExternalLink, Menu, ShieldCheck, Sparkles, X, Zap, LockKeyhole, Timer, RefreshCw } from 'lucide-vue-next'

const path = ref(window.location.pathname || '/')
const menuOpen = ref(false)
const quoteLoading = ref(false)
const copied = ref('')
const passStep = ref('form')
const selectedAmount = ref('0.1')
const customAmount = ref('')
const beneficiary = ref('')
const refundTo = ref('')
const freshWallet = ref(false)
const generatedKey = ref('')
const quote = ref(null)
const order = ref(null)
const notice = ref('')
const quoteAt = ref(new Date())
const quoteExpiresAt = computed(() => quote.value?.expires ? new Date(quote.value.expires) : quoteAt.value)
const amount = computed(() => customAmount.value || selectedAmount.value)
const displayAmount = computed(() => Number(amount.value || 0).toFixed(2))
const ethOnArb = computed(() => quote.value?.ethOnArb || '0.05533')
const ethOnHood = computed(() => quote.value?.ethOnHood || '0.05529')
const fee = computed(() => quote.value?.fee || '0.00028')
const usdOut = computed(() => quote.value?.usdOut || '150.08')
const stations = [
  ['awaiting_deposit', 'Waiting for your ZEC', 'Send the quoted amount from Zodl or another shielded wallet.'],
  ['deposit_seen', 'Deposit seen on Zcash', 'Your deshield is confirmed and the route is being prepared.'],
  ['settling', 'Solvers settling', 'NEAR Intents is finding the best route to Arbitrum One.'],
  ['settled_arb', 'ETH on Arbitrum One', 'The base rail has settled the value for the relay.'],
  ['bridging', 'Relay in flight', 'Relay is carrying ETH to Robinhood Chain.'],
  ['bridged', 'ETH in your pass', 'The one-time pass address has received the relay.'],
  ['delivering', 'Sweeping the pass', 'The hub is buying $ZECPASS on the Pons curve.'],
  ['delivered', 'Delivered', 'Tokens are at the Robinhood Chain address you chose.'],
]
const stats = [
  ['Passes delivered', '1', 'preview route'], ['ETH through the gate', '0.0003', 'ETH'], ['Fees to treasury', '0.0000', 'ETH'], ['Tokens delivered', '41,930', '$ZECPASS'],
]
function navigate(to) {
  menuOpen.value = false
  if (to === path.value) return
  history.pushState({}, '', to)
  path.value = to
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
function onPop() { path.value = window.location.pathname; menuOpen.value = false }
function isActive(to) { return path.value === to }
function markCopy(value, label) {
  navigator.clipboard?.writeText(value).catch(() => {})
  copied.value = label
  window.setTimeout(() => copied.value = '', 1600)
}
function chooseAmount(value) { selectedAmount.value = value; customAmount.value = '' }
function makeKey() {
  const bytes = new Uint8Array(32); crypto.getRandomValues(bytes)
  generatedKey.value = '0x' + Array.from(bytes, b => b.toString(16).padStart(2, '0')).join(''); if (!beneficiary.value) beneficiary.value = '0x' + generatedKey.value.slice(-40)
}
function validAddress(value) { return /^0x[a-fA-F0-9]{40}$/.test(value.trim()) }
function validRefund(value) { return /^t[13][a-km-zA-HJ-NP-Z1-9]{33}$/.test(value.trim()) }
function generateQuote() {
  notice.value = ''
  const z = Number(amount.value)
  if (!Number.isFinite(z) || z < 0.01 || z > 5) { notice.value = 'Enter an amount between 0.01 and 5 ZEC.'; return }
  if (!validAddress(beneficiary.value)) { notice.value = 'Enter a valid Robinhood Chain address (0x…40 hex characters).'; return }
  if (!validRefund(refundTo.value)) { notice.value = 'Enter a transparent Zcash refund address starting with t1 or t3.'; return }
  quoteLoading.value = true
  window.setTimeout(() => {
    const base = z * 0.55331
    quote.value = { zecIn: z.toFixed(2), ethOnArb: base.toFixed(5), ethOnHood: (base * .99924).toFixed(5), fee: (base * .005).toFixed(5), usdOut: (z * 1500.8).toFixed(2), expires: Date.now() + 20 * 60 * 1000 }
    quoteAt.value = new Date(); quoteLoading.value = false; passStep.value = 'quote'
  }, 450)
}
function openGate() {
  if (!quote.value) return
  order.value = { id: `ZP-${Math.random().toString(36).slice(2, 8).toUpperCase()}`, created: Date.now(), station: 0, depositAddress: 't1ZecpassDemo9wWmJ9KxYp3yP9o7qQ8rT6sU5', beneficiary: beneficiary.value }
  localStorage.setItem(storageKeys.order, JSON.stringify(order.value))
  passStep.value = 'tracking'
}
function resetPass() { passStep.value = 'form'; quote.value = null; order.value = null; notice.value = '' }
function advanceOrder() { if (!order.value || order.value.station >= stations.length - 1) return; order.value = { ...order.value, station: order.value.station + 1 }; localStorage.setItem(storageKeys.order, JSON.stringify(order.value)) }
function downloadKey() {
  const blob = new Blob([`Zecpass fresh wallet\\nNetwork: Robinhood Chain (4663)\\nPrivate key: ${generatedKey.value}\\n`], { type: 'text/plain' })
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'zecpass-wallet.txt'; a.click(); URL.revokeObjectURL(a.href)
}
onMounted(() => { window.addEventListener('popstate', onPop); migrateBrandStorage(); try { const saved = JSON.parse(localStorage.getItem(storageKeys.order) || 'null'); if (saved?.station !== undefined) { order.value = saved; passStep.value = 'tracking' } } catch {} })
onBeforeUnmount(() => window.removeEventListener('popstate', onPop))
</script>

<template>
  <div class="zecpass-app">
    <header class="topbar">
      <div class="topbar-inner">
        <button class="brand" aria-label="Zecpass home" @click="navigate('/')"><span class="mark"><span></span></span><span class="serif brand-word">Zecpass</span></button>
        <nav class="desktop-nav" aria-label="Primary navigation">
          <button :class="{active:isActive('/')}" @click="navigate('/')">Market</button>
          <button :class="{active:isActive('/pass')}" @click="navigate('/pass')">Bridge</button>
          <button :class="{active:isActive('/docs')}" @click="navigate('/docs')">Docs</button>
          <button :class="{active:isActive('/stats')}" @click="navigate('/stats')">Stats</button>
        </nav>
        <div class="top-actions"><button class="btn btn-blush btn-sm" @click="navigate('/pass')">Trade ZEC <ArrowRight :size="14" /></button><button class="menu-toggle" :aria-label="menuOpen ? 'Close navigation' : 'Open navigation'" :aria-expanded="menuOpen" @click="menuOpen=!menuOpen"><X v-if="menuOpen" :size="20"/><Menu v-else :size="20"/></button></div>
      </div>
      <div class="market-tape" aria-label="Simulated market tape">
        <span class="market-tape-label"><span class="dot"></span> SIMULATED TAPE</span>
        <span class="market-tape-item"><b>ZEC</b><strong>$1,503.20</strong><em class="up">+2.84%</em></span>
        <span class="market-tape-item"><b>ETH</b><strong>$2,743.81</strong><em class="up">+1.17%</em></span>
        <span class="market-tape-item"><b>$ZECPASS</b><strong>$0.00366</strong><em class="down">-0.42%</em></span>
        <span class="market-tape-block">ROBINHOOD CHAIN <code>4663</code></span>
      </div>
      <nav v-if="menuOpen" class="mobile-nav"><button @click="navigate('/')">Market</button><button @click="navigate('/pass')">Bridge</button><button @click="navigate('/docs')">Docs</button><button @click="navigate('/stats')">Stats</button></nav>
    </header>

    <main class="main-content">
      <template v-if="path === '/pass'">
        <section class="route-shell pass-route"><div class="route-kicker"><span class="dot"></span> BRIDGE TERMINAL / ZEC → $ZECPASS</div><h1 class="serif route-title">Open a bridge position.</h1><p class="route-lede">Pay once in shielded ZEC. We route the value and deliver <strong>$ZECPASS</strong> to any address on Robinhood Chain.</p>
          <div v-if="passStep === 'form'" class="pass-grid"><form class="card pass-form" @submit.prevent="generateQuote"><div class="form-head"><div><span class="step-number">01</span><h2>Configure bridge order.</h2></div><span class="mono tiny">QUOTE / 20 MIN</span></div><label>How much ZEC are you sending?<div class="amount-pills"><button v-for="v in ['0.05','0.1','0.5','1']" :key="v" type="button" :class="{selected:selectedAmount===v && !customAmount}" @click="chooseAmount(v)">{{v}} ZEC</button></div><input v-model="customAmount" class="text-input" inputmode="decimal" placeholder="Or enter a custom amount" @input="selectedAmount=''"/></label><label>Robinhood Chain address<input v-model="beneficiary" class="text-input" placeholder="0x…" spellcheck="false" autocomplete="off"/></label><label>Transparent Zcash refund address<input v-model="refundTo" class="text-input" placeholder="t1… or t3…" spellcheck="false" autocomplete="off"/></label><label class="toggle-row"><input v-model="freshWallet" type="checkbox" @change="freshWallet && makeKey()"/><span class="toggle"><span></span></span><span><strong>Generate a fresh pass wallet</strong><small>We show the key once. You keep it safe.</small></span></label><div v-if="freshWallet && generatedKey" class="key-box"><span class="mono">{{generatedKey}}</span><button type="button" class="icon-button" aria-label="Download wallet key" @click="downloadKey"><ExternalLink :size="15"/></button></div><p v-if="notice" class="form-notice" role="alert">{{notice}}</p><button class="btn btn-ink btn-wide" :disabled="quoteLoading">{{quoteLoading ? 'Fetching live quote…' : 'Get live quote'}} <RefreshCw v-if="quoteLoading" class="spin" :size="16"/><ArrowRight v-else :size="16"/></button><p class="form-foot"><ShieldCheck :size="14"/> Refund routing is used only if this order expires.</p></form><aside class="pass-aside"><div class="art-card blush"><img src="/network.webp" alt="A line drawing of the Zecpass route"/><div class="art-caption"><span>ONE ROUTE</span><span class="mono">ZEC → ETH → $ZECPASS</span></div></div><div class="aside-note"><LockKeyhole :size="16"/><span>Nothing on Robinhood Chain links your bridge order to the Zcash sender.</span></div></aside></div>
          <div v-else-if="passStep === 'quote'" class="quote-layout"><div class="card quote-card"><div class="form-head"><div><span class="step-number">02</span><h2>Your route is ready.</h2></div><span class="mono tiny">VALID UNTIL {{quoteExpiresAt.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}}</span></div><div class="quote-hero"><span class="quote-amount">{{quote.zecIn}} <small>ZEC</small></span><span class="arrow-circle"><ArrowRight :size="19"/></span><span class="quote-amount">{{quote.ethOnHood}} <small>ETH</small></span></div><div class="quote-rows"><div><span>ETH on Arbitrum One</span><strong>{{quote.ethOnArb}} ETH</strong></div><div><span>Relay to Robinhood Chain</span><strong>{{quote.ethOnHood}} ETH</strong></div><div><span>Zecpass fee · 0.5%</span><strong>{{quote.fee}} ETH</strong></div><div class="total"><span>Estimated value delivered</span><strong>${{quote.usdOut}}</strong></div></div><div class="deposit-box"><span class="mono tiny">SEND SHIELDED ZEC TO THIS ONE-TIME ADDRESS</span><code>{{order?.depositAddress || 't1ZecpassDemo9wWmJ9KxYp3yP9o7qQ8rT6sU5'}}</code><button class="btn btn-paper btn-sm" @click="markCopy(order?.depositAddress || 't1ZecpassDemo9wWmJ9KxYp3yP9o7qQ8rT6sU5','deposit')"><Check v-if="copied==='deposit'" :size="14"/><Copy v-else :size="14"/> {{copied==='deposit' ? 'Copied' : 'Copy address'}}</button></div><div class="quote-actions"><button class="btn btn-ink" @click="openGate">Open the gate <ArrowRight :size="16"/></button><button class="btn btn-ghost" @click="resetPass">Edit details</button></div><p class="form-foot"><Timer :size="14"/> The deposit address expires in 20 minutes. Send exactly {{quote.zecIn}} ZEC.</p></div><div class="card route-summary"><div class="mono tiny">ROUTE SUMMARY</div><div class="route-node"><span class="node-icon zcash">Z</span><div><strong>Zcash</strong><small>Shielded deposit</small></div></div><ChevronRight :size="16"/><div class="route-node"><span class="node-icon arb">A</span><div><strong>Arbitrum One</strong><small>NEAR Intents</small></div></div><ChevronRight :size="16"/><div class="route-node"><span class="node-icon hood">R</span><div><strong>Robinhood Chain</strong><small>Pass delivery</small></div></div><div class="route-assurance"><Check :size="15"/> One deposit. One pass. Nothing held.</div></div></div>
          <div v-else class="tracking-layout"><div class="card tracking-card"><div class="form-head"><div><span class="step-number">03</span><h2>Your pass is moving.</h2></div><span class="mono tiny">ORDER {{order?.id}}</span></div><p class="tracking-copy">Keep this page open if you want to watch the handoff. You can safely come back later.</p><div class="stations"><div v-for="(s,i) in stations" :key="s[0]" class="station" :class="{done:i < (order?.station ?? 0), current:i === (order?.station ?? 0)}"><span class="station-dot"><Check v-if="i < (order?.station ?? 0)" :size="12"/><span v-else>{{String(i+1).padStart(2,'0')}}</span></span><div><strong>{{s[1]}}</strong><small>{{s[2]}}</small></div></div></div><div class="tracking-actions"><button class="btn btn-blush" @click="advanceOrder">Simulate next station <ArrowRight :size="16"/></button><button class="btn btn-ghost" @click="resetPass">Start another pass</button></div></div><aside class="card tracking-side"><div class="mono tiny">DELIVERY ADDRESS</div><code>{{order?.beneficiary}}</code><button class="btn btn-paper btn-sm" @click="markCopy(order?.beneficiary,'beneficiary')"><Check v-if="copied === 'beneficiary'" :size="14"/><Copy v-else :size="14"/> {{copied==='beneficiary'?'Copied':'Copy address'}}</button><div class="privacy-callout"><ShieldCheck :size="18"/><p><strong>Private in. Public out.</strong><br/>The pass, sweep, buy and holder are public. The sender is not.</p></div></aside></div>
        </section>
      </template>
      <template v-else-if="path === '/docs'"><section class="route-shell docs-route"><div class="route-kicker"><span class="dot"></span> DOCUMENTATION</div><h1 class="serif route-title">A pass, explained.</h1><p class="route-lede">The shortest path from shielded ZEC to an address on Robinhood Chain, with every handoff accounted for.</p><div class="docs-layout"><aside class="docs-index card"><span class="mono tiny">ON THIS PAGE</span><button v-for="item in ['Overview','Using Zecpass','Architecture','Privacy','Contract','Relayer','Token','API','Security','Operations','FAQ']" :key="item">{{item}} <ChevronRight :size="14"/></button></aside><article class="docs-content"><div v-for="section in [{t:'Overview',b:'Zecpass is a one-way privacy route from shielded ZEC to a Robinhood Chain address.'},{t:'Using Zecpass',b:'Choose an amount between 0.01 and 5 ZEC, enter a beneficiary and refund address, then review a twenty-minute quote.'},{t:'Architecture',b:'NEAR Intents settles ZEC to Arbitrum One; Relay carries ETH to Robinhood Chain.'},{t:'Privacy',b:'Your Zcash balance, history and sending address stay inside the shielded pool.'},{t:'Contract',b:'The public hub and pass flow can be inspected on the destination chain.'},{t:'Relayer',b:'The relayer coordinates settlement and bounded delivery across the two rails.'},{t:'Token',b:'$ZECPASS is the destination token shown in this preview; token details are reference data.'},{t:'API',b:'Quote and order endpoints are represented by the local preview flow and validation states.'},{t:'Security',b:'Never share a private key. Refunds go only to the transparent address supplied for an order.'},{t:'Operations',b:'Deposit addresses expire after twenty minutes and order stations show each handoff.'},{t:'FAQ',b:'This interface is a reversible preview. It does not custody funds or submit transactions.'}]" :key="section.t" class="doc-section"><span class="mono tiny">{{section.t.toUpperCase()}}</span><h2 class="serif">{{section.t}}</h2><p>{{section.b}}</p></div></article></div></section></template>
      <template v-else-if="path === '/whitepaper'"><section class="route-shell paper-route"><div class="paper-cover card"><div class="paper-stamp">Z</div><span class="mono tiny">Z E C P A S S / WHITEPAPER 01</span><h1 class="serif">Buy in private,<br/><em>hold in the open.</em></h1><p>The pass from Zcash to Robinhood Chain.</p><div class="paper-meta"><span>September 2026</span><span>zecpass.app</span></div></div><article class="paper-body"><div class="route-kicker"><span class="dot"></span> WHITEPAPER</div><h2 class="serif">A bridge without a bridge.</h2><p>Most routes ask you to trust a wrapper. Zecpass asks you to trust a sequence you can inspect: a shielded deposit, two settlement rails, and a contract that anyone can read.</p><div class="paper-grid"><div><span class="mono tiny">01 / THESIS</span><h3 class="serif">Privacy at the edge.</h3><p>Your Zcash history stays in the pool. The output is public, pseudonymous and useful on Robinhood Chain.</p></div><div><span class="mono tiny">02 / MODEL</span><h3 class="serif">A half-percent road fee.</h3><p>The fee pays for relay gas and the vault. There is no custody layer and no hidden allocation.</p></div><div><span class="mono tiny">03 / CONTRACT</span><h3 class="serif">One pass, one emptying key.</h3><p>Your pass address is created for the route and only the holder can empty it. The hub cannot name you.</p></div></div><button class="btn btn-ink" @click="markCopy('https://zecpass.app/whitepaper.pdf','paper')"><Check v-if="copied==='paper'" :size="15"/><Copy v-else :size="15"/> {{copied==='paper'?'Link copied':'Copy PDF link'}}</button></article></section></template>
      <template v-else-if="path === '/stats'"><section class="route-shell stats-route"><div class="route-kicker"><span class="dot"></span> PREVIEW ROUTE / REFRESHED ON LOAD</div><h1 class="serif route-title">The numbers behind the gate.</h1><p class="route-lede">A small public window into the rails, passes and fees moving through Zecpass.</p><div class="stats-grid"><article v-for="item in stats" :key="item[0]" class="stat-card card"><span class="mono tiny">{{item[0].toUpperCase()}}</span><strong class="serif">{{item[1]}}</strong><span>{{item[2]}}</span></article></div><div class="stats-lower"><article class="card rail-card"><div class="form-head"><h2>Rails online</h2><span class="status-pill"><span class="dot"></span> All systems go</span></div><div class="rail-row"><span class="rail-logo zcash">Z</span><div><strong>Zcash → Arbitrum One</strong><small>NEAR Intents / base rail</small></div><span class="mono">~7 min</span></div><div class="rail-row"><span class="rail-logo">R</span><div><strong>Arbitrum One → Robinhood Chain</strong><small>Relay / one block</small></div><span class="mono">~1 sec</span></div><div class="rail-row"><span class="rail-logo">P</span><div><strong>$ZECPASS on Pons</strong><small>Curve / 2% creator tax</small></div><span class="mono">PREVIEW</span></div></article><article class="card contract-card"><span class="mono tiny">PUBLIC ADDRESSES</span><div><span>Hub</span><code>0x2d2F…9232</code><button @click="markCopy('0x2d2F1e1c7B90272728a627605dD07FC46eF79232','hub')"><Check v-if="copied==='hub'" :size="14"/><Copy v-else :size="14"/></button></div><div><span>$ZECPASS</span><code>0x5F3E…a867</code><button @click="markCopy('0x5F3E6A9139CB1EB9A2deb59089D31Eac880Ba867','token')"><Check v-if="copied==='token'" :size="14"/><Copy v-else :size="14"/></button></div><p>Robinhood Chain · 4663</p></article></div></section></template>
      <template v-else>
        <section class="hero-wrap"><div class="hero-tile"><img src="/hero.webp" alt="" class="hero-art"/><div class="hero-copy"><span class="hero-terminal-kicker mono">ZEC / PRIVATE LIQUIDITY ROUTE</span><div class="hero-brand"><span class="mark mark-large"><span></span></span><span class="serif hero-word">Zecpass</span></div><p>Route shielded ZEC into <strong>$ZECPASS</strong> on Robinhood Chain.</p><div class="hero-actions"><button class="btn btn-ink" @click="navigate('/pass')">Open bridge <ArrowRight :size="16"/></button><button class="btn btn-paper" @click="navigate('/whitepaper')">Read the paper</button></div><div class="hero-market-stats" aria-label="Route market stats"><span><small>ROUTE FEE</small><b>0.50%</b></span><span><small>SETTLEMENT</small><b>~8 MIN</b></span><span><small>OUTPUT</small><b>$ZECPASS</b></span></div></div></div></section>
        <section class="card-row intro-cards"><article class="product-card card"><div class="product-art"><img src="/token.webp" alt="Abstract Zecpass token artwork"/></div><div class="product-copy"><h2 class="serif">One deposit.<br/>That's it.</h2><button class="btn btn-paper btn-sm" @click="navigate('/pass')">Get a pass <ArrowRight :size="14"/></button><p>Send shielded ZEC once.<br/>Zecpass does the rest.</p></div></article><article class="product-card card token-card"><div class="token-word serif">Zecpass</div><div class="product-art"><img src="/stack.webp" alt="Stacked Zecpass artwork"/></div><div class="token-address"><a href="https://ponsfamily.com/token/0x5F3E6A9139CB1EB9A2deb59089D31Eac880Ba867" target="_blank" rel="noreferrer">$ZECPASS <span class="mono">0x5F3E…a867</span> <ExternalLink :size="12"/></a></div></article></section>
        <section class="statement-section"><div class="statement-art"><img src="/network.webp" alt="Diagram of the Zcash to Robinhood Chain route"/></div><div class="statement-copy"><span class="mono tiny">THE SIMPLE VERSION</span><h2 class="serif">Send it shielded.<br/><em>Hold it in the open.</em></h2><p>Pay in shielded ZEC once. $ZECPASS shows up at the address you chose on Robinhood Chain, and nothing on that chain links the two.</p><button class="btn btn-blush" @click="navigate('/pass')">Start a pass <ArrowRight :size="16"/></button><div class="time-note"><Timer :size="16"/><span>About eight minutes, one thing to do on your side.</span></div></div></section>
        <section class="gradient-callout"><div><span class="mono tiny">YOUR PASS IS AN ADDRESS ONLY YOU CAN EMPTY.</span><h2 class="serif">About eight minutes.<br/><em>One thing to do.</em></h2><p>Send shielded ZEC once. We handle the handoff across the rails and deliver the pass to the address you chose.</p><button class="btn btn-ink" @click="navigate('/pass')">Start a pass <ArrowRight :size="16"/></button></div><div class="gradient-art"><img src="/network.webp" alt="Abstract route artwork"/></div></section>
        <section class="steps-section"><div class="section-heading"><span class="mono tiny">FOUR STEPS. NONE OF THEM YOURS TO TRUST.</span><h2 class="serif">Four steps. None of them yours to trust.</h2></div><div class="steps-grid"><article v-for="(s,i) in [['Ask','Give the Robinhood Chain address that should receive $ZECPASS and how much ZEC you are sending.','You get a one-time deposit address, valid twenty minutes.'],['Send','From Zodl or any shielded wallet, send the ZEC. It leaves the pool as a plain deshield: the amount is visible, your history is not.',''],['Settle','NEAR Intents pays ETH on Arbitrum in about seven minutes. Relay carries it to Robinhood Chain in one block, into a pass only you can empty.',''],['Hold','The hub sweeps your pass, buys $ZECPASS on the Pons curve, keeps half a percent for the road and hands the tokens to your address.','']]" :key="s[0]" class="step-item"><span class="step-index mono">0{{i+1}}</span><h3 class="serif">{{s[0]}}</h3><p>{{s[1]}}</p><small>{{s[2]}}</small></article></div></section>
        <section class="quote-section"><div class="quote-intro"><span class="mono tiny">PREVIEW ROUTE / 0.1 ZEC</span><h2 class="serif">What one tenth of a ZEC buys right now.</h2><p>Preview values from the NEAR Intents and Relay route. The fee line is the only number Zecpass decides.</p><button class="text-button" @click="navigate('/pass')">Get your own quote <ArrowRight :size="15"/></button></div><div class="card live-quote"><div class="live-head"><span><span class="dot"></span> QUOTE</span><span class="mono">{{quoteAt.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}} UTC</span></div><div class="live-row"><span>ZEC in</span><strong>0.1 ZEC</strong></div><div class="live-row"><span>ETH on Arbitrum One</span><strong>0.056171 ETH</strong></div><div class="live-row"><span>ETH on Robinhood Chain</span><strong>0.056128 ETH</strong></div><div class="live-row fee"><span>Zecpass fee, 0.5%</span><strong>0.000280 ETH</strong></div><div class="live-total"><span>Worth</span><strong>$153.24</strong></div><div class="live-foot"><span><Timer :size="14"/> 8 min, then 1 s, then one block</span><span class="mono">MON, 21 SEP 2026</span></div></div><div class="quote-rails"><article class="rail-card-dark"><h3 class="serif">The rails</h3><p><span class="dot"></span> NEAR Intents, ZEC to Arbitrum One</p><p><span class="dot"></span> Relay, Arbitrum One to Robinhood Chain</p><p><span class="dot"></span> Direct ZEC route, no solver yet</p></article><article class="rail-card-light card"><h3 class="serif">$ZECPASS on Pons</h3><div><span>Contract</span><code>0x5F3E…a867</code></div><div><span>Creator tax</span><code>2%</code></div><div><span>Pass fee</span><code>0.5% of ETH</code></div><div><span>Curve</span><code>pool / graduation</code></div></article></div></section>
        <section class="privacy-section"><div class="section-heading"><span class="mono tiny">THE PRIVACY MODEL</span><h2 class="serif">Three views of the same pass.</h2></div><div class="privacy-grid"><article><span class="privacy-word serif">hidden</span><p>On Zcash, your balance, past and the address you sent from stay in the shielded pool.</p></article><article><span class="privacy-word serif">pseudonymous</span><p>On the rails, NEAR Intents sees a deposit it generated. Relay sees the relayer pay a pass.</p></article><article><span class="privacy-word serif">public</span><p>On Robinhood Chain, the pass, sweep, buy and holder are all public. What is missing is any owner the chain can name.</p></article></div><button class="text-button" @click="navigate('/docs')">Read the privacy page <ArrowRight :size="15"/></button></section>
        <section class="alphabet-section"><div class="alphabet-grid"><span v-for="letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'" :key="letter">{{letter}}</span></div><div class="alphabet-copy"><span class="mark"><span></span></span><span class="serif">Zecpass</span><p>Buy in private,<br/>hold in the open.</p></div></section>
      </template>
    </main>
    <div class="status-strip"><span><span class="dot"></span> $ZECPASS not launched yet, the address will appear here</span><span>Hub contract tested, not deployed</span><span>Robinhood Chain 4663</span></div><footer class="footer"><div class="footer-main"><button class="brand" @click="navigate('/')"><span class="mark"><span></span></span><span class="serif brand-word">Zecpass</span></button><p>The pass from Zcash to Robinhood Chain.</p><nav><button @click="navigate('/pass')">Get a pass</button><button @click="navigate('/stats')">Stats</button><button @click="navigate('/docs')">Documentation</button><button @click="navigate('/whitepaper')">Whitepaper</button></nav></div><div class="footer-bottom"><p>Zecpass is software, not a custodian and not an exchange. Nothing here is financial advice. Read the whitepaper before you use it.</p><span class="mono">© 2026 Zecpass<br/>{{brand.tagline}}</span></div></footer>
    <div v-if="copied" class="toast"><Check :size="15"/> {{copied==='paper'?'PDF link copied': 'Copied to clipboard'}}</div>
  </div>
</template>
