<script setup>
import { computed, ref } from 'vue'
import { ArrowRight, ArrowUpRight, Info, Search, ShieldCheck } from 'lucide-vue-next'
import PayoffExplorer from './PayoffExplorer.vue'
import MarketTable from './MarketTable.vue'
import { calculatePayoff } from '../payoff.js'
import { brand } from '../brand.js'

const emit = defineEmits(['navigate'])
const query = ref('')
const side = ref('All')
const quoteSide = ref('Income')
const units = ref(1)
const selected = ref('ETHX')
const cap = ref(5)
const assets = [
  { symbol: 'ETHX', name: 'Ethereum', spot: 250, initials: 'E', style: 'apple' },
  { symbol: 'BTCX', name: 'Bitcoin', spot: 130, initials: 'B', style: 'nvidia' },
  { symbol: 'SOLX', name: 'Solana', spot: 430, initials: 'S', style: 'microsoft' },
  { symbol: 'USDCX', name: 'USD Coin', spot: 1, initials: '$', style: 'tesla' },
]
const asset = computed(() => assets.find(item => item.symbol === selected.value) || assets[0])
const model = computed(() => calculatePayoff({ spot: asset.value.spot, capPercent: cap.value, settlementPrice: asset.value.spot }))
const price = computed(() => quoteSide.value === 'Income' ? model.value.incomePrice : model.value.upsidePrice)
const amount = computed(() => Number.isFinite(Number(units.value)) && Number(units.value) > 0 ? Number(units.value) : 0)
const money = value => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(value)

function explore() {
  document.getElementById('cap')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<template>
  <div class="crypto-home container">
    <section class="market-welcome" aria-labelledby="market-title">
      <div>
        <div class="welcome-status"><span class="network-dot"></span>{{ brand.network }} <span class="status-separator">·</span><strong>Preview</strong></div>
        <h1 id="market-title" tabindex="-1">Markets</h1>
        <p>Explore tokenized market examples and model outcomes.</p>
      </div>
      <a href="/signal" class="journal-shortcut" @click.prevent="emit('navigate', '/signal')"><span class="journal-shortcut-icon">▤</span><span><strong>Your journal</strong><small>Keep a local record</small></span><ArrowUpRight :size="16" /></a>
    </section>

    <section class="asset-strip" aria-label="Example assets">
      <button v-for="item in assets" :key="item.symbol" type="button" class="asset-tile" :class="{ selected: selected === item.symbol }" :aria-pressed="selected === item.symbol" @click="selected = item.symbol">
        <span class="coin-mark" :class="`coin-${item.style}`">{{ item.initials }}</span>
        <span class="asset-tile-copy"><strong>{{ item.symbol }}</strong><small>{{ item.name }}</small></span>
        <span class="asset-tile-price"><strong>{{ money(item.spot) }}</strong><small>Example price</small></span>
      </button>
    </section>

    <div class="market-tabs" aria-label="Product section">
      <button class="active" type="button" aria-current="page">Markets</button>
      <button type="button" @click="emit('navigate', '/app/auctions')">Auctions <span>Examples</span></button>
      <button type="button" @click="emit('navigate', '/app/recompose')">Recompose <span>Preview</span></button>
    </div>

    <div class="market-layout">
      <section class="market-card" aria-labelledby="market-card-title">
        <div class="market-card-heading">
          <div><div class="section-kicker">Tokenized assets</div><h2 id="market-card-title">Browse markets</h2></div>
          <span class="market-count">4 examples</span>
        </div>
        <div class="market-tools">
          <div class="market-filter-tabs" aria-label="Position type">
            <button v-for="option in ['All', 'Income', 'Upside']" :key="option" type="button" :aria-pressed="side === option" :class="{ active: side === option }" @click="side = option">{{ option }}</button>
          </div>
          <label class="market-search"><Search :size="17" /><span class="sr-only">Search markets</span><input v-model="query" placeholder="Search assets" /></label>
        </div>
        <MarketTable compact :query="query" :side="side" @reset="query = ''" @navigate="to => emit('navigate', to)" />
        <a class="browse-all-link" href="/app/markets" @click.prevent="emit('navigate', '/app/markets')">Open market list <ArrowRight :size="15" /></a>
      </section>

      <aside class="estimate-card" aria-labelledby="estimate-title">
        <div class="estimate-heading"><div><div class="section-kicker">Local calculator</div><h2 id="estimate-title">Quick estimate</h2></div><span class="sample-chip"><Info :size="13" /> Model</span></div>
        <label class="field-label" for="estimate-asset">Asset</label>
        <div class="asset-select-wrap"><span class="coin-mark coin-selected">{{ asset.initials }}</span><select id="estimate-asset" v-model="selected"><option v-for="item in assets" :key="item.symbol" :value="item.symbol">{{ item.symbol }} · {{ item.name }}</option></select></div>
        <div class="position-picker" aria-label="Position type"><button v-for="option in ['Income', 'Upside']" :key="option" type="button" :aria-pressed="quoteSide === option" :class="{ active: quoteSide === option, upside: option === 'Upside' }" @click="quoteSide = option">{{ option }}</button></div>
        <div class="estimate-fields">
          <label class="estimate-input"><span>Amount</span><span class="input-with-unit"><input v-model.number="units" inputmode="decimal" type="number" min="0.01" max="1000000" step="0.01" /><b>{{ selected }}</b></span></label>
          <label class="estimate-cap"><span>Upside cap <output>+{{ cap }}%</output></span><input v-model.number="cap" type="range" min="0" max="10" step="1" /><span class="range-caption"><span>0%</span><span>10%</span></span></label>
        </div>
        <dl class="estimate-details"><div><dt>Example spot price</dt><dd>{{ money(asset.spot) }}</dd></div><div><dt>Cap price</dt><dd>{{ money(model.strike) }}</dd></div><div><dt>Model price / unit</dt><dd>{{ money(price) }}</dd></div></dl>
        <div class="estimate-total"><span>Estimated value</span><strong>{{ money(price * amount) }}</strong></div>
        <button class="estimate-action" type="button" :disabled="!amount" @click="explore">View payoff <ArrowRight :size="17" /></button>
        <p class="estimate-note"><ShieldCheck :size="14" /> Uses example prices. No live quote or transaction.</p>
      </aside>
    </div>

    <div class="market-helper-row">
      <div class="helper-chip"><span class="helper-icon income-icon">↗</span><span><strong>Income</strong><small>Value up to the cap</small></span></div>
      <div class="helper-chip"><span class="helper-icon upside-icon">⌁</span><span><strong>Upside</strong><small>Value above the cap</small></span></div>
      <a href="/docs#mechanism" @click.prevent="emit('navigate', '/docs#mechanism')">Learn how the model works <ArrowUpRight :size="14" /></a>
    </div>
    <p class="market-disclosure"><Info :size="14" /> Prices and markets on this page are illustrative. Solana Chain is the target network; this preview has no live data, wallet connection or transaction execution.</p>
  </div>

  <PayoffExplorer />

  <section id="how-it-works" class="how-it-works container">
    <div class="how-heading"><div class="section-kicker">The model</div><h2>One asset. Two positions.</h2><p>A simple example to explore how a defined cap changes the split.</p></div>
    <ol><li><span class="how-number">1</span><div><strong>Choose an asset</strong><p>Start with an example price.</p></div></li><li><span class="how-number">2</span><div><strong>Set a cap</strong><p>Move the slider to see each side.</p></div></li><li><span class="how-number">3</span><div><strong>Save your thinking</strong><p>Keep assumptions in a browser-local journal.</p></div></li></ol>
    <a class="how-journal-link" href="/signal" @click.prevent="emit('navigate', '/signal')">Open your journal <ArrowRight :size="15" /></a>
  </section>
</template>

<style scoped>
.crypto-home { padding-block: 40px 0; }
.market-welcome { display: flex; align-items: end; justify-content: space-between; gap: 20px; margin-bottom: 26px; }
.market-welcome h1 { margin: 11px 0 5px; font-size: 36px; line-height: 1.12; letter-spacing: -.04em; font-weight: 650; }
.market-welcome p { margin: 0; color: var(--muted); font-size: 14px; }
.welcome-status { display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: 12px; }
.welcome-status strong { color: var(--green); font-weight: 650; }
.network-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--green); box-shadow: 0 0 0 3px color-mix(in srgb, var(--green) 13%, transparent); }
.status-separator { color: #a9b2ac; }
.journal-shortcut { display: flex; align-items: center; gap: 11px; padding: 10px 14px; min-height: 58px; border: 1px solid var(--line); border-radius: 14px; background: var(--surface); text-decoration: none; transition: border-color .18s, transform .18s; }
.journal-shortcut:hover { border-color: var(--green); transform: translateY(-1px); }
.journal-shortcut-icon { display: grid; place-items: center; width: 34px; height: 34px; border-radius: 11px; background: var(--green-soft); color: var(--green); font-size: 17px; }
.journal-shortcut > span:nth-child(2) { display: grid; gap: 2px; }
.journal-shortcut strong { font-size: 12px; }
.journal-shortcut small { color: var(--muted); font-size: 10px; }
.journal-shortcut > svg { color: var(--muted); margin-left: 4px; }
.asset-strip { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 27px; }
.asset-tile { display: flex; align-items: center; gap: 11px; min-width: 0; padding: 15px 16px; border: 1px solid var(--line); border-radius: 15px; background: var(--surface); text-align: left; cursor: pointer; transition: border-color .18s, box-shadow .18s, transform .18s; }
.asset-tile:hover { border-color: #b9d9c8; transform: translateY(-1px); }
.asset-tile.selected { border-color: var(--green); box-shadow: 0 0 0 2px color-mix(in srgb, var(--green) 12%, transparent); }
.coin-mark { display: grid; place-items: center; flex: none; width: 38px; height: 38px; border-radius: 50%; background: #e8f4ed; color: #137b50; font-size: 14px; font-weight: 700; }
.coin-nvidia { background: #edf4df; color: #548b1a; }.coin-microsoft { background: #eaf0fb; color: #4b6eaa; }.coin-tesla { background: #fae8e8; color: #c95454; }
.asset-tile-copy,.asset-tile-price { display: grid; gap: 2px; min-width: 0; }
.asset-tile-copy strong { font-size: 13px; letter-spacing: .01em; }
.asset-tile-copy small,.asset-tile-price small { overflow: hidden; color: var(--muted); font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
.asset-tile-price { margin-left: auto; text-align: right; }
.asset-tile-price strong { font-size: 13px; font-variant-numeric: tabular-nums; }
.market-tabs { display: flex; align-items: center; gap: 22px; min-height: 48px; margin-bottom: 18px; border-bottom: 1px solid var(--line); }
.market-tabs button { display: inline-flex; align-items: center; gap: 7px; align-self: stretch; border: 0; border-bottom: 2px solid transparent; background: transparent; color: var(--muted); font-size: 13px; cursor: pointer; }
.market-tabs button.active { border-bottom-color: var(--green); color: var(--fg); font-weight: 650; }
.market-tabs button span { padding: 3px 6px; border-radius: 6px; background: var(--panel); color: var(--muted); font-size: 9px; }
.market-layout { display: grid; grid-template-columns: minmax(0, 1.55fr) minmax(290px, .85fr); align-items: start; gap: 17px; }
.market-card,.estimate-card { min-width: 0; border: 1px solid var(--line); border-radius: 17px; background: var(--surface); box-shadow: var(--card-shadow); }
.market-card { padding: 21px 22px 16px; }
.market-card-heading,.estimate-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.section-kicker { color: var(--muted); font-size: 11px; font-weight: 550; }
.market-card-heading h2,.estimate-heading h2 { margin: 4px 0 0; font-size: 20px; letter-spacing: -.025em; font-weight: 650; }
.market-count { color: var(--muted); font-size: 11px; }
.market-tools { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin: 18px 0 4px; }
.market-filter-tabs { display: flex; gap: 4px; padding: 3px; border-radius: 10px; background: var(--panel); }
.market-filter-tabs button { min-height: 33px; padding: 0 12px; border: 0; border-radius: 8px; background: transparent; color: var(--muted); font-size: 11px; cursor: pointer; }
.market-filter-tabs button.active { background: var(--surface); color: var(--fg); box-shadow: 0 1px 3px #101b1420; font-weight: 600; }
.market-search { display: flex; align-items: center; gap: 8px; width: min(205px, 45%); min-height: 39px; padding: 0 11px; border: 1px solid var(--line); border-radius: 10px; color: var(--muted); }
.market-search input { width: 100%; min-width: 0; border: 0; outline: 0; background: transparent; color: var(--fg); font-size: 12px; }
.market-search input::placeholder { color: #8c9790; }
.browse-all-link { display: flex; align-items: center; justify-content: center; gap: 7px; min-height: 41px; margin-top: 11px; border: 1px solid var(--line); border-radius: 10px; color: var(--fg); font-size: 12px; font-weight: 550; text-decoration: none; transition: background .18s, border-color .18s; }
.browse-all-link:hover { border-color: #b9d9c8; background: var(--green-soft); }
.estimate-card { padding: 21px; }
.sample-chip { display: inline-flex; align-items: center; gap: 5px; padding: 5px 8px; border-radius: 8px; background: #eff4f0; color: #5d6d62; font-size: 10px; }
.field-label { display: block; margin: 19px 0 7px; color: var(--muted); font-size: 11px; }
.asset-select-wrap { display: flex; align-items: center; gap: 10px; min-height: 47px; padding: 5px 11px; border: 1px solid var(--line); border-radius: 11px; }
.coin-selected { width: 30px; height: 30px; }
.asset-select-wrap select { flex: 1; min-width: 0; border: 0; outline: 0; appearance: none; background: transparent; color: var(--fg); font-size: 13px; }
.position-picker { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; margin-top: 14px; padding: 4px; border-radius: 10px; background: var(--panel); }
.position-picker button { min-height: 36px; border: 0; border-radius: 8px; background: transparent; color: var(--muted); font-size: 12px; cursor: pointer; }
.position-picker button.active { background: var(--green); color: #fff; font-weight: 650; }
.position-picker button.active.upside { background: #db6559; }
.estimate-fields { display: grid; grid-template-columns: 1fr; gap: 15px; margin-top: 16px; }
.estimate-input,.estimate-cap { display: grid; gap: 8px; color: var(--muted); font-size: 11px; }
.input-with-unit { display: flex; align-items: center; justify-content: space-between; min-height: 43px; border: 1px solid var(--line); border-radius: 10px; }
.input-with-unit input { width: 100%; min-width: 0; height: 41px; padding: 0 11px; border: 0; outline: 0; background: transparent; color: var(--fg); font-variant-numeric: tabular-nums; }
.input-with-unit b { padding: 0 11px; color: var(--muted); font-size: 11px; font-weight: 500; }
.estimate-cap > span:first-child { display: flex; justify-content: space-between; }
.estimate-cap output { color: var(--fg); font-weight: 650; }
.estimate-cap input { width: 100%; accent-color: var(--green); }
.range-caption { display: flex; justify-content: space-between; margin-top: -4px; color: var(--muted); font-size: 9px; }
.estimate-details { display: grid; gap: 0; margin: 17px 0 0; }
.estimate-details > div { display: flex; justify-content: space-between; gap: 10px; padding: 9px 0; border-top: 1px solid var(--line); font-size: 11px; }
.estimate-details dt { color: var(--muted); }
.estimate-details dd { margin: 0; font-variant-numeric: tabular-nums; font-weight: 550; }
.estimate-total { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: 5px; padding: 13px 0; border-top: 1px solid var(--line); color: var(--muted); font-size: 12px; }
.estimate-total strong { color: var(--fg); font-size: 18px; font-variant-numeric: tabular-nums; }
.estimate-action { display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; min-height: 46px; border: 0; border-radius: 11px; background: var(--green); color: #fff; font-size: 13px; font-weight: 650; cursor: pointer; transition: background .18s, transform .18s; }
.estimate-action:hover { background: var(--green-dark); transform: translateY(-1px); }
.estimate-action:disabled { opacity: .5; cursor: not-allowed; transform: none; }
.estimate-note { display: flex; align-items: center; gap: 6px; margin: 11px 0 0; color: var(--muted); font-size: 10px; line-height: 1.4; }
.estimate-note svg { flex: none; color: var(--green); }
.market-helper-row { display: flex; align-items: center; gap: 22px; margin: 17px 0 13px; padding: 12px 16px; border: 1px solid var(--line); border-radius: 13px; background: var(--surface); }
.helper-chip { display: flex; align-items: center; gap: 9px; }
.helper-chip > span:last-child { display: grid; gap: 1px; }
.helper-chip strong { font-size: 11px; }.helper-chip small { color: var(--muted); font-size: 9px; }
.helper-icon { display: grid; place-items: center; width: 27px; height: 27px; border-radius: 9px; background: var(--green-soft); color: var(--green); font-size: 15px; }
.upside-icon { background: #faefed; color: #d05a51; }
.market-helper-row > a { display: flex; align-items: center; gap: 5px; margin-left: auto; color: var(--green); font-size: 11px; font-weight: 550; text-decoration: none; }
.market-disclosure { display: flex; align-items: flex-start; gap: 7px; max-width: 1000px; margin: 0 0 10px; color: var(--muted); font-size: 10px; line-height: 1.55; }
.market-disclosure svg { flex: none; margin-top: 1px; }
.how-it-works { display: grid; grid-template-columns: .9fr 1.4fr auto; align-items: center; gap: 30px; padding-block: 57px 72px; border-top: 1px solid var(--line); }
.how-heading h2 { margin: 6px 0; font-size: 24px; letter-spacing: -.03em; }
.how-heading p { margin: 0; color: var(--muted); font-size: 12px; line-height: 1.6; }
.how-it-works ol { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 0; padding: 0; list-style: none; }
.how-it-works li { display: flex; gap: 9px; align-items: flex-start; }
.how-number { display: grid; place-items: center; flex: none; width: 23px; height: 23px; border-radius: 50%; background: var(--green-soft); color: var(--green); font-size: 10px; font-weight: 700; }
.how-it-works li strong { font-size: 11px; }.how-it-works li p { margin: 3px 0 0; color: var(--muted); font-size: 10px; line-height: 1.4; }
.how-journal-link { display: inline-flex; align-items: center; gap: 5px; color: var(--green); font-size: 11px; font-weight: 600; text-decoration: none; white-space: nowrap; }
@media (max-width: 980px) {
  .crypto-home { padding-top: 30px; }
  .asset-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .market-layout { grid-template-columns: minmax(0, 1.25fr) minmax(270px, .85fr); }
  .market-card { padding: 18px; }
  .estimate-card { padding: 18px; }
  .how-it-works { grid-template-columns: 1fr; gap: 18px; }
  .how-journal-link { justify-self: start; }
}
@media (max-width: 720px) {
  .market-welcome { align-items: flex-start; }
  .market-welcome h1 { font-size: 32px; }
  .market-welcome p { max-width: 290px; font-size: 12px; }
  .journal-shortcut { padding: 8px; gap: 7px; }
  .journal-shortcut > span:nth-child(2) { display: none; }
  .journal-shortcut > svg { margin: 0; }
  .asset-strip { gap: 8px; }
  .asset-tile { gap: 8px; padding: 11px; border-radius: 13px; }
  .asset-tile-price strong { font-size: 11px; }
  .asset-tile-copy strong { font-size: 12px; }
  .coin-mark { width: 32px; height: 32px; font-size: 12px; }
  .market-layout { grid-template-columns: 1fr; }
  .estimate-card { order: -1; }
  .estimate-fields { grid-template-columns: 1fr 1fr; gap: 12px; }
  .market-helper-row { flex-wrap: wrap; gap: 12px; }
  .market-helper-row > a { width: 100%; margin: 2px 0 0; padding-top: 10px; border-top: 1px solid var(--line); }
}
@media (max-width: 420px) {
  .crypto-home { padding-top: 22px; }
  .asset-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .asset-tile { padding: 10px 8px; gap: 7px; }
  .asset-tile-price small { font-size: 8px; }
  .asset-tile-price strong { font-size: 10px; }
  .market-card { padding: 15px 13px; }
  .market-tools { align-items: stretch; flex-direction: column; }
  .market-search { width: 100%; }
  .market-filter-tabs { align-self: flex-start; }
  .estimate-card { padding: 16px; }
  .estimate-fields { grid-template-columns: 1fr; }
  .how-it-works { padding-block: 42px 50px; }
  .how-it-works ol { grid-template-columns: 1fr; gap: 15px; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { scroll-behavior: auto !important; transition-duration: .01ms !important; animation-duration: .01ms !important; }
}
</style>
