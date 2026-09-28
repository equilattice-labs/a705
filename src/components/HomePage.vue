<script setup>
import { computed, ref } from 'vue'
import { ArrowDown, ArrowRight, ArrowUp, ArrowUpRight, BookOpen, Info, Search, ShieldCheck } from 'lucide-vue-next'
import PayoffExplorer from './PayoffExplorer.vue'
import MarketTable from './MarketTable.vue'
import { calculatePayoff } from '../payoff.js'
import { brand } from '../brand.js'

const emit = defineEmits(['navigate'])
const query = ref('')
const side = ref('All')
const quoteSide = ref('Income')
const units = ref(1)
const selected = ref('SOL')
const cap = ref(5)
const assets = [
  { symbol: 'SOL', name: 'Solana', spot: 182, initials: 'S', style: 'sol' },
  { symbol: 'JUP', name: 'Jupiter', spot: 1.12, initials: 'J', style: 'jupiter' },
  { symbol: 'BONK', name: 'Bonk', spot: 0.000021, initials: 'B', style: 'bonk' },
  { symbol: 'USDC', name: 'USD Coin', spot: 1, initials: '$', style: 'usdc' },
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
    <section class="market-ticker" aria-label="Solana market tape">
      <span class="ticker-label"><i></i> Solana market</span>
      <span><b>SOL</b><strong>$182.40</strong><em>+4.82%</em></span>
      <span><b>JUP</b><strong>$1.12</strong><em>+2.10%</em></span>
      <span><b>BONK</b><strong>$0.000021</strong><em class="down">-1.34%</em></span>
      <span><b>USDC</b><strong>$1.00</strong><em>+0.01%</em></span>
      <span class="ticker-note">sample tape / 24h</span>
    </section>
    <section class="market-welcome" aria-labelledby="market-title">
      <div>
        <div class="welcome-status"><span class="network-dot"></span>{{ brand.network }} <span class="status-separator">/</span><strong>CA preview</strong><span class="wallet-state">wallet optional</span></div>
        <h1 id="market-title" tabindex="-1">Markets</h1>
        <p>Explore tokenized market examples and model outcomes.</p>
      </div>
      <a href="/signal" class="journal-shortcut" @click.prevent="emit('navigate', '/signal')"><span class="journal-shortcut-icon"><BookOpen :size="15" /></span><span><strong>Your journal</strong><small>Keep a local record</small></span><ArrowUpRight :size="16" /></a>
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
        <div class="asset-select-wrap"><span class="coin-mark coin-selected">{{ asset.initials }}</span><select id="estimate-asset" v-model="selected"><option v-for="item in assets" :key="item.symbol" :value="item.symbol">{{ item.symbol }} / {{ item.name }}</option></select></div>
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
      <div class="helper-chip"><span class="helper-icon income-icon"><ArrowDown :size="14" /></span><span><strong>Income</strong><small>Value up to the cap</small></span></div>
      <div class="helper-chip"><span class="helper-icon upside-icon"><ArrowUp :size="14" /></span><span><strong>Upside</strong><small>Value above the cap</small></span></div>
      <a href="/docs#mechanism" @click.prevent="emit('navigate', '/docs#mechanism')">Learn how the model works <ArrowUpRight :size="14" /></a>
    </div>
    <p class="market-disclosure"><Info :size="14" /> Prices and markets on this page are illustrative. {{ brand.network }} is the target network; this preview has no live data, wallet connection or transaction execution.</p>
  </div>

  <PayoffExplorer />

  <section id="how-it-works" class="how-it-works container">
    <div class="how-heading"><div class="section-kicker">The model</div><h2>One asset. Two positions.</h2><p>A simple example to explore how a defined cap changes the split.</p></div>
    <ol><li><span class="how-number">1</span><div><strong>Choose an asset</strong><p>Start with an example price.</p></div></li><li><span class="how-number">2</span><div><strong>Set a cap</strong><p>Move the slider to see each side.</p></div></li><li><span class="how-number">3</span><div><strong>Save your thinking</strong><p>Keep assumptions in a browser-local journal.</p></div></li></ol>
    <a class="how-journal-link" href="/signal" @click.prevent="emit('navigate', '/signal')">Open your journal <ArrowRight :size="15" /></a>
  </section>
</template>

<style scoped>
.crypto-home {
  padding-block: 18px 0;
}
.market-ticker {
  display: flex; align-items: center; overflow-x: auto; border: 1px solid var(--line); color: var(--muted); font: 10px var(--mono); white-space: nowrap; scrollbar-width: none;
  min-height: 34px; margin-bottom: 22px; padding: 0 11px; gap: 17px; border-color: #24445a; border-radius: 4px; background: #090f18; box-shadow: inset 0 0 20px rgba(53,215,255,.025);
}
.market-ticker::-webkit-scrollbar {
  display: none;
}
.market-ticker > span {
  display: inline-flex; align-items: center;
  gap: 6px;
}
.ticker-label { font-weight: 600;
  color: var(--cyan); text-transform: uppercase; letter-spacing: .08em;
}
.ticker-label i { border-radius: 50%;
  width: 5px; height: 5px; background: var(--cyan); box-shadow: 0 0 0 3px #28d7e820, 0 0 8px #28d7e888;
}
.market-ticker b { font-weight: 600;
  color: #9cb0c3;
}
.market-ticker strong { font-weight: 500;
  color: var(--fg);
}
.market-ticker em { font-style: normal;
  color: var(--cyan);
}
.market-ticker em.down {
  color: var(--magenta);
}
.ticker-note {
  margin-left: auto; font-size: 9px;
  color: #627488;
}
.market-welcome {
  display: flex; justify-content: space-between; gap: 20px;
  align-items: center; margin-bottom: 20px;
}
.market-welcome h1 { line-height: 1.12; font-weight: 650;
  margin: 8px 0 4px; font-size: clamp(30px, 4vw, 42px); letter-spacing: -.03em;
}
.market-welcome p {
  margin: 0;
  color: #91a3b4; font-size: 13px;
}
.welcome-status {
  display: flex; align-items: center; gap: 8px;
  color: #8ba0b2; font-family: var(--mono); font-size: 10px; letter-spacing: .02em; text-transform: uppercase;
}
.welcome-status strong { font-weight: 650;
  color: var(--amber);
}
.wallet-state {
  padding-left: 8px; font-family: var(--mono); font-size: 10px;
  color: #64798b;
}
.network-dot { border-radius: 50%;
  width: 6px; height: 6px; background: var(--cyan); box-shadow: 0 0 0 3px #28d7e818, 0 0 7px #28d7e888;
}
.status-separator {
  color: #506477;
}
.journal-shortcut {
  display: flex; align-items: center; gap: 11px; border: 1px solid var(--line); text-decoration: none; transition: border-color .18s, transform .18s;
  min-height: 48px; padding: 8px 11px; border-color: var(--line); border-radius: 4px; background: #0d1622; box-shadow: none;
}
.journal-shortcut:hover { transform: translateY(-1px);
  border-color: var(--cyan); background: #102131;
}
.journal-shortcut-icon {
  display: grid; place-items: center;
  width: 29px; height: 29px; border-radius: 3px; background: #123547; color: var(--cyan); font-size: 15px;
}
.journal-shortcut > span:nth-child(2) {
  display: grid; gap: 2px;
}
.journal-shortcut strong {
  font-size: 11px;
}
.journal-shortcut small {
  color: #71879a; font-size: 9px;
}
.journal-shortcut > svg {
  color: var(--muted); margin-left: 4px;
}
.asset-strip {
  display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px; margin-bottom: 20px;
}
.asset-tile {
  display: flex; align-items: center; min-width: 0; border: 1px solid var(--line); text-align: left; cursor: pointer; transition: border-color .18s, box-shadow .18s, transform .18s;
  gap: 9px; padding: 10px 11px; border-color: var(--line); border-radius: 4px; background: #0d1420; box-shadow: none;
}
.asset-tile:hover { transform: translateY(-1px);
  border-color: #3a627d; background: #101b29;
}
.asset-tile.selected {
  border-color: var(--cyan); box-shadow: inset 0 0 0 1px #28d7e844;
}
.coin-mark {
  display: grid; place-items: center; flex: none; border-radius: 50%; font-weight: 700;
  width: 32px; height: 32px; background: #113b4c; color: var(--cyan); font-family: var(--mono); font-size: 12px;
}
.coin-jupiter {
  background: #3d3020; color: var(--amber);
}
.coin-bonk {
  background: #2b2040; color: var(--magenta);
}
.coin-usdc {
  background: #421d37; color: var(--magenta);
}
.asset-tile-copy,.asset-tile-price {
  display: grid; gap: 2px; min-width: 0;
}
.asset-tile-copy strong { letter-spacing: .01em;
  font-family: var(--mono); font-size: 11px;
}
.asset-tile-copy small,.asset-tile-price small {
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  color: #71869a; font-size: 9px;
}
.asset-tile-price {
  margin-left: auto; text-align: right;
}
.asset-tile-price strong { font-variant-numeric: tabular-nums;
  font-family: var(--mono); font-size: 11px;
}
.market-tabs {
  display: flex; align-items: center; border-bottom: 1px solid var(--line);
  min-height: 42px; gap: 18px; margin-bottom: 14px; border-bottom-color: var(--line);
}
.market-tabs button {
  display: inline-flex; align-items: center; gap: 7px; align-self: stretch; border: 0; border-bottom: 2px solid transparent; background: transparent; color: var(--muted); cursor: pointer;
  font-family: var(--mono); font-size: 10px; letter-spacing: .04em; text-transform: uppercase;
}
.market-tabs button.active { font-weight: 650;
  border-bottom-color: var(--cyan); color: var(--cyan);
}
.market-tabs button span {
  padding: 3px 6px; font-size: 9px;
  border-radius: 3px; background: #101c2a; color: #73889b;
}
.market-layout {
  display: grid; grid-template-columns: minmax(0, 1.55fr) minmax(290px, .85fr); align-items: start;
  gap: 12px;
}
.market-card,.estimate-card {
  min-width: 0; border: 1px solid var(--line);
  border-color: var(--line); border-radius: 5px; background: #0e1521; box-shadow: var(--card-shadow);
}
.market-card {
  padding: 17px 18px 13px;
}
.market-card-heading,.estimate-heading {
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
}
.section-kicker { font-weight: 550;
  color: #7890a4; font-family: var(--mono); font-size: 9px; letter-spacing: .06em; text-transform: uppercase;
}
.market-card-heading h2,.estimate-heading h2 {
  margin: 4px 0 0; font-weight: 650;
  margin-top: 3px; font-size: 17px; letter-spacing: -.01em;
}
.market-count {
  color: #7890a4; font-family: var(--mono); font-size: 9px; letter-spacing: .06em; text-transform: uppercase;
}
.market-tools {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  margin: 14px 0 3px;
}
.market-filter-tabs {
  display: flex;
  gap: 2px; padding: 2px; border-radius: 4px; background: #080f18;
}
.market-filter-tabs button { padding: 0 12px; border: 0; background: transparent; color: var(--muted); cursor: pointer;
  min-height: 30px; border-radius: 3px; font-family: var(--mono); font-size: 10px;
}
.market-filter-tabs button.active { font-weight: 600;
  background: #143349; color: var(--cyan); box-shadow: inset 0 0 0 1px #245a73;
}
.market-search {
  display: flex; align-items: center; gap: 8px; padding: 0 11px; border: 1px solid var(--line); color: var(--muted);
  min-height: 35px; border-color: #22394d; border-radius: 3px; background: #090f18;
  width: min(190px, 45%);
}
.market-search input {
  width: 100%; min-width: 0; border: 0; outline: 0; background: transparent;
  color: var(--fg); font-family: var(--mono); font-size: 10px;
}
.market-search input::placeholder {
  color: #8c9790;
}
.browse-all-link {
  display: flex; align-items: center; justify-content: center; gap: 7px; min-height: 41px; margin-top: 11px; border: 1px solid var(--line); border-radius: 10px; color: var(--fg); font-size: 12px; font-weight: 550; text-decoration: none; transition: background .18s, border-color .18s;
}
.browse-all-link:hover {
  border-color: #b9d9c8; background: var(--cyan-soft);
}
.estimate-card {
  padding: 17px;
}
.sample-chip {
  display: inline-flex; align-items: center; gap: 5px; padding: 5px 8px;
  border-radius: 3px; background: #3b2e1d; color: var(--amber); font-family: var(--mono); font-size: 9px;
}
.field-label {
  display: block; margin: 19px 0 7px;
  color: #8195a7; font-family: var(--mono); font-size: 9px;
}
.asset-select-wrap {
  display: flex; align-items: center; gap: 10px; padding: 5px 11px; border: 1px solid var(--line); border-color: #22394d; border-radius: 3px; background: #090f18;
  min-height: 41px;
}
.coin-selected {
  width: 26px; height: 26px;
}
.asset-select-wrap select {
  flex: 1; min-width: 0; border: 0; outline: 0; appearance: none; background: transparent;
  color: var(--fg); font-family: var(--mono); font-size: 10px;
}
.position-picker {
  display: grid; grid-template-columns: 1fr 1fr; margin-top: 14px;
  gap: 2px; padding: 2px; border-radius: 4px; background: #080f18;
}
.position-picker button { border: 0; background: transparent; color: var(--muted); cursor: pointer;
  min-height: 30px; border-radius: 3px; font-family: var(--mono); font-size: 10px;
}
.position-picker button.active { font-weight: 650;
  background: var(--cyan); color: #05121a;
}
.position-picker button.active.upside {
  background: var(--magenta); color: #170a12;
}
.estimate-fields {
  display: grid; grid-template-columns: 1fr; gap: 15px; margin-top: 16px;
}
.estimate-input,.estimate-cap {
  display: grid; gap: 8px;
  color: #8195a7; font-family: var(--mono); font-size: 9px;
}
.input-with-unit {
  display: flex; align-items: center; justify-content: space-between; border: 1px solid var(--line);
  min-height: 35px; border-color: #22394d; border-radius: 3px; background: #090f18;
}
.input-with-unit input {
  width: 100%; min-width: 0; height: 41px; padding: 0 11px; border: 0; outline: 0; background: transparent; font-variant-numeric: tabular-nums;
  color: var(--fg); font-family: var(--mono); font-size: 10px;
}
.input-with-unit b {
  padding: 0 11px; color: var(--muted); font-size: 11px; font-weight: 500;
}
.estimate-cap > span:first-child {
  display: flex; justify-content: space-between;
}
.estimate-cap output {
  color: var(--fg); font-weight: 650;
}
.estimate-cap input {
  width: 100%; accent-color: var(--cyan);
}
.range-caption {
  display: flex; justify-content: space-between; margin-top: -4px; color: var(--muted); font-size: 9px;
}
.estimate-details {
  display: grid; gap: 0; margin: 17px 0 0;
}
.estimate-details > div {
  display: flex; justify-content: space-between; gap: 10px; border-top: 1px solid var(--line);
  padding: 8px 0; border-top-color: #1c2c3d; font-size: 10px;
}
.estimate-details dt {
  color: var(--muted);
}
.estimate-details dd {
  margin: 0; font-variant-numeric: tabular-nums; font-weight: 550;
}
.estimate-total {
  display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: 5px; border-top: 1px solid var(--line); color: var(--muted);
  padding: 11px 0; border-top-color: #1c2c3d; font-family: var(--mono); font-size: 10px;
}
.estimate-total strong { font-variant-numeric: tabular-nums;
  color: var(--cyan); font-size: 16px;
}
.estimate-action {
  display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; border: 0; font-weight: 650; cursor: pointer; transition: background .18s, transform .18s;
  min-height: 40px; border-radius: 3px; background: var(--cyan); color: #05121a; font-family: var(--mono); font-size: 11px; text-transform: uppercase;
}
.estimate-action:hover { transform: translateY(-1px);
  background: #73e4ff;
}
.estimate-action:disabled {
  opacity: .5; cursor: not-allowed; transform: none;
}
.estimate-note {
  display: flex; align-items: center; gap: 6px; margin: 11px 0 0; line-height: 1.4;
  color: #6f8599; font-family: var(--mono); font-size: 9px;
}
.estimate-note svg {
  flex: none;
  color: var(--cyan);
}
.market-helper-row {
  display: flex; align-items: center; border: 1px solid var(--line);
  gap: 17px; margin: 12px 0 10px; padding: 9px 12px; border-color: var(--line); border-radius: 4px; background: #0d1420;
}
.helper-chip {
  display: flex; align-items: center; gap: 9px;
}
.helper-chip > span:last-child {
  display: grid; gap: 1px;
}
.helper-chip strong {
  font-family: var(--mono); font-size: 10px;
}
.helper-chip small {
  color: #70869a; font-size: 8px;
}
.helper-icon {
  display: grid; place-items: center;
  width: 24px; height: 24px; border-radius: 3px; background: #123547; color: var(--cyan); font-size: 13px;
}
.upside-icon {
  background: #421d37; color: var(--magenta);
}
.market-helper-row > a {
  display: flex; align-items: center; gap: 5px; margin-left: auto; font-weight: 550; text-decoration: none;
  color: var(--cyan); font-family: var(--mono); font-size: 9px; text-transform: uppercase;
}
.market-disclosure {
  display: flex; align-items: flex-start; gap: 7px; max-width: 1000px; margin: 0 0 10px; line-height: 1.55;
  color: #6e8396; font-family: var(--mono); font-size: 9px;
}
.market-disclosure svg {
  flex: none; margin-top: 1px;
}
.how-it-works {
  display: grid; align-items: center; border-top: 1px solid var(--line);
  grid-template-columns: .8fr 1.5fr auto; gap: 24px; padding-block: 44px 60px; border-top-color: var(--line);
}
.how-heading h2 {
  margin: 6px 0; letter-spacing: -.03em;
  font-size: 21px;
}
.how-heading p {
  margin: 0; line-height: 1.6;
  color: #8094a6; font-size: 11px;
}
.how-it-works ol {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 0; padding: 0; list-style: none;
}
.how-it-works li {
  display: flex; gap: 9px; align-items: flex-start;
}
.how-number {
  display: grid; place-items: center; flex: none; font-size: 10px; font-weight: 700;
  width: 21px; height: 21px; border-radius: 3px; background: #123547; color: var(--cyan); font-family: var(--mono);
}
.how-it-works li strong {
  font-family: var(--mono); font-size: 10px; text-transform: uppercase;
}
.how-it-works li p {
  margin: 3px 0 0; line-height: 1.4;
  color: #71879a; font-size: 9px;
}
.how-journal-link {
  display: inline-flex; align-items: center; gap: 5px; font-weight: 600; text-decoration: none; white-space: nowrap;
  color: var(--cyan); font-family: var(--mono); font-size: 9px; text-transform: uppercase;
}
@media (max-width: 980px) {
  .crypto-home {
    padding-top: 30px;
  }
  .asset-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .market-layout {
    grid-template-columns: minmax(0, 1.25fr) minmax(270px, .85fr);
  }
  .market-card {
    padding: 18px;
  }
  .estimate-card {
    padding: 18px;
  }
  .how-it-works {
    grid-template-columns: 1fr; gap: 18px;
  }
  .how-journal-link {
    justify-self: start;
  }
}
@media (max-width: 720px) {
  .market-welcome {
    align-items: flex-start;
  }
  .market-welcome h1 {
    font-size: 30px;
  }
  .market-welcome p {
    max-width: 290px;
    font-size: 11px;
  }
  .journal-shortcut {
    padding: 8px; gap: 7px;
    min-height: 39px;
  }
  .journal-shortcut > span:nth-child(2) {
    display: none;
  }
  .journal-shortcut > svg {
    margin: 0;
  }
  .asset-strip {
    gap: 8px;
  }
  .asset-tile {
    gap: 8px; border-radius: 13px;
    padding: 9px 8px;
  }
  .asset-tile-price strong {
    font-size: 11px;
  }
  .asset-tile-copy strong {
    font-size: 12px;
  }
  .coin-mark {
    width: 32px; height: 32px; font-size: 12px;
  }
  .market-layout {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  .estimate-card {
    order: -1;
    border-radius: 4px;
  }
  .estimate-fields {
    grid-template-columns: 1fr 1fr; gap: 12px;
  }
  .market-helper-row {
    flex-wrap: wrap;
    gap: 10px;
  }
  .market-helper-row > a {
    width: 100%; margin: 2px 0 0; padding-top: 10px; border-top: 1px solid var(--line);
  }
  .crypto-home {
    padding-top: 13px;
  }
  .market-card {
    border-radius: 4px;
  }
}
@media (max-width: 420px) {
  .crypto-home {
    padding-top: 22px;
  }
  .asset-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .asset-tile {
    padding: 10px 8px; gap: 7px;
  }
  .asset-tile-price small {
    font-size: 8px;
  }
  .asset-tile-price strong {
    font-size: 10px;
  }
  .market-card {
    padding: 15px 13px;
  }
  .market-tools {
    align-items: stretch; flex-direction: column;
  }
  .market-search {
    width: 100%;
  }
  .market-filter-tabs {
    align-self: flex-start;
  }
  .estimate-card {
    padding: 16px;
  }
  .estimate-fields {
    grid-template-columns: 1fr;
  }
  .how-it-works {
    padding-block: 42px 50px;
  }
  .how-it-works ol {
    grid-template-columns: 1fr; gap: 15px;
  }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    scroll-behavior: auto !important; transition-duration: .01ms !important; animation-duration: .01ms !important;
  }
}
</style>
