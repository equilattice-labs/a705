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
const formatSpot = value => value < 0.01 ? `$${value.toFixed(6)}` : money(value)

function explore() {
  document.getElementById('cap')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<template>
  <div class="market-home container">
    <section class="market-overview" aria-labelledby="market-title">
      <div>
        <span class="overview-kicker">{{ brand.network }} / Market workspace</span>
        <h1 id="market-title" tabindex="-1">Markets</h1>
        <p>Example quotes and a local payoff model. No live feed or execution.</p>
      </div>
      <div class="overview-actions">
        <span class="preview-tag"><i aria-hidden="true"></i> Preview data</span>
        <a class="button primary" href="/app/markets" @click.prevent="emit('navigate', '/app/markets')">Browse markets <ArrowUpRight :size="15" /></a>
      </div>
    </section>

    <section class="market-ribbon" aria-label="Illustrative Solana market examples">
      <span class="ribbon-title">Example tape</span>
      <span><b>SOL</b><strong>$182.40</strong><em>+4.82%</em></span>
      <span><b>JUP</b><strong>$1.12</strong><em>+2.10%</em></span>
      <span><b>BONK</b><strong>$0.000021</strong><em class="down">-1.34%</em></span>
      <span><b>USDC</b><strong>$1.00</strong><em>+0.01%</em></span>
      <span class="ribbon-note">illustrative / not live</span>
    </section>

    <section class="asset-deck" aria-label="Example assets">
      <button v-for="item in assets" :key="item.symbol" type="button" class="asset-card" :class="{ selected: selected === item.symbol }" :aria-pressed="selected === item.symbol" @click="selected = item.symbol">
        <span class="asset-avatar" :class="`avatar-${item.style}`">{{ item.initials }}</span>
        <span class="asset-card-main"><b>{{ item.symbol }}</b><small>{{ item.name }}</small></span>
        <span class="asset-card-price"><b>{{ formatSpot(item.spot) }}</b><small>example</small></span>
      </button>
    </section>

    <div class="board-nav" aria-label="Product section">
      <button class="active" type="button">Markets <span>04</span></button>
      <button type="button" @click="emit('navigate', '/app/auctions')">Auctions <span>preview</span></button>
      <button type="button" @click="emit('navigate', '/app/recompose')">Recompose <span>preview</span></button>
    </div>

    <div class="board-grid">
      <section class="market-card" aria-labelledby="market-card-title">
        <div class="card-heading">
          <div><span class="card-kicker">Watchlist / SPL assets</span><h2 id="market-card-title">The board</h2></div>
          <span class="status-pill"><i aria-hidden="true"></i> Preview</span>
        </div>
        <div class="market-tools">
          <div class="market-filter-tabs" aria-label="Position type">
            <button v-for="option in ['All', 'Income', 'Upside']" :key="option" type="button" :aria-pressed="side === option" :class="{ active: side === option }" @click="side = option">{{ option }}</button>
          </div>
          <label class="market-search"><Search :size="16" /><span class="sr-only">Search markets</span><input v-model="query" placeholder="Find a token" /></label>
        </div>
        <MarketTable compact :query="query" :side="side" @reset="query = ''" @navigate="to => emit('navigate', to)" />
        <a class="browse-all-link" href="/app/markets" @click.prevent="emit('navigate', '/app/markets')">Open full board <ArrowRight :size="15" /></a>
      </section>

      <aside class="estimate-card" aria-labelledby="estimate-title">
        <div class="card-heading">
          <div><span class="card-kicker">Local model</span><h2 id="estimate-title">Quick price</h2></div>
          <span class="model-badge"><Info :size="13" /> Sandbox</span>
        </div>
        <label class="field-label" for="estimate-asset">Choose an asset</label>
        <div class="asset-select-wrap">
          <span class="asset-avatar avatar-selected">{{ asset.initials }}</span>
          <select id="estimate-asset" v-model="selected"><option v-for="item in assets" :key="item.symbol" :value="item.symbol">{{ item.symbol }} / {{ item.name }}</option></select>
        </div>
        <div class="position-picker" aria-label="Position type">
          <button v-for="option in ['Income', 'Upside']" :key="option" type="button" :aria-pressed="quoteSide === option" :class="{ active: quoteSide === option, upside: option === 'Upside' }" @click="quoteSide = option">{{ option }}</button>
        </div>
        <div class="estimate-fields">
          <label class="estimate-input"><span>Amount</span><span class="input-with-unit"><input v-model.number="units" inputmode="decimal" type="number" min="0.01" max="1000000" step="0.01" /><b>{{ selected }}</b></span></label>
          <label class="estimate-cap"><span>Cap <output>+{{ cap }}%</output></span><input v-model.number="cap" type="range" min="0" max="10" step="1" /><span class="range-caption"><span>0%</span><span>10%</span></span></label>
        </div>
        <dl class="estimate-details"><div><dt>Spot / example</dt><dd>{{ formatSpot(asset.spot) }}</dd></div><div><dt>Cap price</dt><dd>{{ money(model.strike) }}</dd></div><div><dt>Model / unit</dt><dd>{{ money(price) }}</dd></div></dl>
        <div class="estimate-total"><span>Estimated value</span><strong>{{ money(price * amount) }}</strong></div>
        <button class="estimate-action" type="button" :disabled="!amount" @click="explore">See the split <ArrowRight :size="16" /></button>
        <p class="estimate-note"><ShieldCheck :size="14" /> Example math only. No live quote or transaction.</p>
      </aside>
    </div>

    <div class="market-disclosure"><Info :size="14" /> {{ brand.network }} preview. Values are illustrative; wallet connection is optional; no CA or execution is live.</div>
  </div>

  <PayoffExplorer :spot="asset.spot" :asset="asset.symbol" />
</template>

<style scoped>
.market-home { padding-block:20px 0; }
.market-overview { display:flex; align-items:center; justify-content:space-between; gap:20px; min-height:112px; padding:12px 0 18px; border-bottom:1px solid var(--line); }
.overview-kicker,.card-kicker { color:var(--muted); font:600 10px/1.4 var(--mono); text-transform:uppercase; }
.market-overview h1 { margin:5px 0 3px; font:600 30px/1.15 var(--display); }
.market-overview p { margin:0; color:var(--muted); font-size:12px; }
.overview-actions { display:flex; align-items:center; gap:14px; }
.preview-tag { display:inline-flex; align-items:center; gap:7px; color:var(--muted); font:10px var(--mono); white-space:nowrap; }
.preview-tag i { width:7px; height:7px; border-radius:50%; background:var(--accent); }
.market-overview .button.primary { min-height:38px; border-radius:5px; color:#171b10; }
.market-ribbon { display:flex; align-items:center; gap:20px; min-height:43px; margin:0 0 14px; padding:0 2px; overflow-x:auto; border-bottom:1px solid var(--line); white-space:nowrap; scrollbar-width:none; }
.market-ribbon::-webkit-scrollbar { display:none; }
.market-ribbon>span { display:inline-flex; align-items:center; gap:7px; font:10px var(--mono); }
.market-ribbon b { color:var(--muted); font-weight:500; }
.market-ribbon strong { color:var(--fg); font-weight:500; }
.market-ribbon em { color:var(--mint); font-style:normal; }
.market-ribbon em.down { color:var(--pink); }
.ribbon-note { margin-left:auto; color:var(--muted); font-size:9px!important; }
.ribbon-title { color:var(--accent)!important; text-transform:uppercase; }
.asset-deck { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:8px; margin-bottom:17px; }
.asset-card { display:flex; align-items:center; gap:9px; min-width:0; min-height:62px; padding:10px; border:1px solid var(--line); border-radius:6px; background:var(--surface); text-align:left; cursor:pointer; transition:border-color .16s,background .16s; }
.asset-card:hover,.asset-card.selected { border-color:var(--accent); background:var(--raised); }
.asset-avatar { display:grid; place-items:center; flex:none; width:32px; height:32px; border-radius:5px; background:#303b27; color:var(--accent); font:700 12px var(--mono); }
.avatar-jupiter { background:#29353b; color:#9fc1ff; }
.avatar-bonk { background:#3c2927; color:#ff9a70; }
.avatar-usdc { background:#263a31; color:#8ce0b4; }
.avatar-selected { width:28px; height:28px; }
.asset-card-main,.asset-card-price { display:grid; gap:2px; min-width:0; }
.asset-card-main b,.asset-card-price b { font:600 11px var(--mono); }
.asset-card-main small,.asset-card-price small { overflow:hidden; color:var(--muted); font-size:9px; text-overflow:ellipsis; white-space:nowrap; }
.asset-card-price { margin-left:auto; text-align:right; }
.asset-card-price b { color:var(--fg); }
.board-nav { display:flex; gap:4px; margin-bottom:10px; border-bottom:1px solid var(--line); }
.board-nav button { padding:10px 12px; border:0; border-bottom:2px solid transparent; background:transparent; color:var(--muted); font:10px var(--mono); cursor:pointer; text-transform:uppercase; }
.board-nav button.active { border-bottom-color:var(--accent); color:var(--accent); }
.board-nav button span { margin-left:5px; color:var(--muted); font-size:8px; }
.board-grid { display:grid; grid-template-columns:minmax(0,1.45fr) minmax(280px,.85fr); gap:10px; align-items:start; }
.market-card,.estimate-card { min-width:0; padding:16px; border:1px solid var(--line); border-radius:6px; background:var(--surface); }
.card-heading { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; }
.card-heading h2 { margin:4px 0 0; font:600 20px var(--display); }
.status-pill,.model-badge { display:inline-flex; align-items:center; gap:5px; padding:4px 7px; border:1px solid var(--line); border-radius:4px; color:var(--muted); font:9px var(--mono); text-transform:uppercase; }
.status-pill i { width:6px; height:6px; border-radius:50%; background:var(--accent); }
.model-badge { color:var(--accent); }
.market-tools { display:flex; align-items:center; justify-content:space-between; gap:10px; margin:14px 0 5px; }
.market-filter-tabs { display:flex; gap:2px; padding:2px; border-radius:5px; background:var(--panel); }
.market-filter-tabs button { min-height:29px; padding:0 10px; border:0; border-radius:3px; background:transparent; color:var(--muted); font:10px var(--mono); cursor:pointer; }
.market-filter-tabs button.active { background:var(--raised); color:var(--fg); }
.market-search { display:flex; align-items:center; gap:7px; width:min(190px,45%); min-height:34px; padding:0 9px; border:1px solid var(--line); border-radius:4px; color:var(--muted); background:var(--panel); }
.market-search input { width:100%; min-width:0; border:0; outline:0; background:none; color:var(--fg); font:10px var(--mono); }
.browse-all-link { display:flex; align-items:center; justify-content:center; gap:7px; min-height:36px; margin-top:10px; border:1px solid var(--line); border-radius:4px; color:var(--fg); font-size:11px; text-decoration:none; }
.browse-all-link:hover { border-color:var(--accent); color:var(--accent); }
.field-label { display:block; margin:14px 0 6px; color:var(--muted); font:10px var(--mono); text-transform:uppercase; }
.asset-select-wrap { display:flex; align-items:center; gap:8px; min-height:40px; padding:5px 8px; border:1px solid var(--line); border-radius:4px; background:var(--panel); }
.asset-select-wrap select { flex:1; min-width:0; border:0; outline:0; appearance:none; background:none; color:var(--fg); font:11px var(--mono); }
.position-picker { display:grid; grid-template-columns:1fr 1fr; gap:2px; margin-top:11px; padding:2px; border-radius:5px; background:var(--panel); }
.position-picker button { min-height:30px; border:0; border-radius:3px; background:transparent; color:var(--muted); font:10px var(--mono); cursor:pointer; }
.position-picker button.active { background:var(--mint); color:#101812; }
.position-picker button.active.upside { background:var(--pink); color:#231216; }
.estimate-fields { display:grid; gap:12px; margin-top:13px; }
.estimate-input,.estimate-cap { display:grid; gap:6px; color:var(--muted); font:10px var(--mono); }
.input-with-unit { display:flex; align-items:center; min-height:37px; border:1px solid var(--line); border-radius:4px; background:var(--panel); }
.input-with-unit input { width:100%; min-width:0; height:35px; padding:0 9px; border:0; outline:0; background:none; color:var(--fg); font:11px var(--mono); }
.input-with-unit b { padding:0 9px; color:var(--accent); font:11px var(--mono); }
.estimate-cap>span:first-child { display:flex; justify-content:space-between; }
.estimate-cap output { color:var(--accent); }
.estimate-cap input { width:100%; accent-color:var(--accent); }
.range-caption { display:flex; justify-content:space-between; color:var(--muted); font-size:9px; }
.estimate-details { display:grid; margin:14px 0 0; }
.estimate-details>div { display:flex; justify-content:space-between; gap:8px; padding:8px 0; border-top:1px solid var(--line); color:var(--muted); font-size:10px; }
.estimate-details dd { margin:0; color:var(--fg); font:500 10px var(--mono); }
.estimate-total { display:flex; justify-content:space-between; align-items:center; gap:8px; padding:11px 0; border-top:1px solid var(--line); color:var(--muted); font:10px var(--mono); }
.estimate-total strong { color:var(--accent); font:600 18px var(--mono); }
.estimate-action { display:flex; align-items:center; justify-content:center; gap:8px; width:100%; min-height:39px; border:0; border-radius:4px; background:var(--accent); color:#171b10; font:600 10px var(--mono); cursor:pointer; text-transform:uppercase; }
.estimate-action:hover { filter:brightness(1.08); }
.estimate-action:disabled { cursor:not-allowed; opacity:.45; }
.estimate-note { display:flex; align-items:flex-start; gap:6px; margin:9px 0 0; color:var(--muted); font:9px/1.5 var(--mono); }
.estimate-note svg { color:var(--mint); flex:none; }
.market-disclosure { display:flex; align-items:flex-start; gap:7px; max-width:900px; margin:13px 0 10px; color:var(--muted); font:9px/1.55 var(--mono); }
.market-disclosure svg { flex:none; color:var(--accent); }
@media(max-width:980px) { .asset-deck { grid-template-columns:repeat(2,minmax(0,1fr)); } .board-grid { grid-template-columns:1fr; } }
@media(max-width:560px) { .market-home { padding-top:12px; } .market-overview { align-items:flex-start; flex-direction:column; gap:12px; padding-bottom:14px; } .overview-actions { width:100%; justify-content:space-between; } .market-overview h1 { font-size:27px; } .market-ribbon { gap:14px; } .asset-card { padding:8px; } .asset-card-price small { font-size:8px; } .market-tools { align-items:stretch; flex-direction:column; } .market-search { width:100%; } .market-card,.estimate-card { padding:13px; } }
</style>
