<script setup>
import { computed, ref, watch } from 'vue'
import { ArrowDown, ArrowUp } from 'lucide-vue-next'
import { calculatePayoff } from '../payoff.js'

const props = defineProps({ spot: { type: Number, default: 250 }, asset: { type: String, default: 'SOL' } })
const cap = ref(5)
const settlement = ref(props.spot)
const showTable = ref(false)
watch(() => props.spot, spot => { settlement.value = spot })
const model = computed(() => calculatePayoff({ spot: props.spot, capPercent: cap.value, settlementPrice: settlement.value }))
const money = value => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value)
const change = computed(() => `${model.value.spotChangePercent > 0 ? '+' : ''}${model.value.spotChangePercent.toFixed(1)}%`)
const low = computed(() => props.spot * 0.7)
const high = computed(() => props.spot * 1.3)
const chartMax = computed(() => Math.max(high.value * 1.45, 2))
const gridTicks = computed(() => Array.from({ length: 5 }, (_, index) => chartMax.value * index / 4))
const x = value => 74 + (value - low.value) / (high.value - low.value) * 454
const y = value => 276 - value / chartMax.value * 232
const stockPath = computed(() => `M ${x(low.value)} ${y(low.value)} L ${x(high.value)} ${y(high.value)}`)
const incomePath = computed(() => `M ${x(low.value)} ${y(low.value)} L ${x(model.value.strike)} ${y(model.value.strike)} L ${x(high.value)} ${y(model.value.strike)}`)
const upsidePath = computed(() => `M ${x(low.value)} ${y(0)} L ${x(model.value.strike)} ${y(0)} L ${x(high.value)} ${y(high.value - model.value.strike)}`)
const tableRows = computed(() => [...new Set([low.value, props.spot, model.value.strike, high.value, settlement.value])].sort((a, b) => a - b).map(price => ({
  price,
  income: Math.min(price, model.value.strike),
  upside: Math.max(price - model.value.strike, 0),
})))
const chartDescription = computed(() => `At a settlement price of ${money(settlement.value)}, Income is worth ${money(model.value.incomeSettlement)} and Upside is worth ${money(model.value.upsideSettlement)} per unit. Income follows the stock up to the cap of ${money(model.value.strike)}. Upside receives any amount above the cap.`)
</script>

<template>
  <section id="cap" class="section-border payoff-section" aria-labelledby="cap-heading">
    <div class="container payoff-layout">
      <div class="cap-copy">
        <h2 id="cap-heading">A defined level.<br>A clear split.</h2>
        <p class="cap-lead">Choose the cap. K is fixed for the epoch.</p>
        <p class="cap-explanation">Set a cap, move the settlement slider, and inspect how the illustrative value splits between Income and Upside. No order or wallet action is created.</p>

        <div class="cap-control">
          <div class="control-label"><label for="cap-range">Cap</label><output for="cap-range">+{{ cap }}%</output></div>
          <input id="cap-range" v-model.number="cap" type="range" min="0" max="10" step="1" :style="{ '--range-fill': `${cap * 10}%` }" :aria-valuetext="`${cap}% cap, strike ${money(model.strike)}`" aria-describedby="cap-model-note">
          <div class="cap-ticks" aria-hidden="true"><span>0%</span><span>2%</span><span :class="{ 'selected-tick': cap === 5 }">5%</span><span>10%</span></div>
          <p id="cap-model-note" class="model-note">{{ asset }} example at <span>{{ money(model.spot) }}</span> / cap price (K) <span>{{ money(model.strike) }}</span> / 30 days / model at 25% vol</p>
        </div>
      </div>

      <div class="payoff-visual">
        <div class="settlement-card">
          <div class="chart-heading"><div><h3>{{ asset }} value at settlement</h3><p>Per unit / {{ asset }} example at {{ money(model.spot) }} / cap +{{ cap }}% / K {{ money(model.strike) }}</p></div><button class="table-toggle" type="button" :aria-pressed="showTable" aria-controls="payoff-display" @click="showTable = !showTable">{{ showTable ? 'Chart' : 'Table' }}</button></div>
          <ul class="chart-legend" aria-label="Chart legend"><li class="legend-stock">{{ asset }} market unit</li><li class="legend-income">Income</li><li class="legend-upside">Upside</li></ul>

          <div id="payoff-display" class="payoff-display">
            <div v-if="showTable" class="payoff-table-wrap" tabindex="0" role="region" aria-label="Settlement values table">
              <table class="payoff-table"><caption>Per-unit settlement value, before premium</caption><thead><tr><th scope="col">Stock price</th><th scope="col">Income</th><th scope="col">Upside</th></tr></thead><tbody><tr v-for="row in tableRows" :key="row.price" :class="{ 'current-row': row.price === settlement }"><th scope="row">{{ money(row.price) }}<span v-if="row.price === settlement" class="current-label">Current</span></th><td>{{ money(row.income) }}</td><td>{{ money(row.upside) }}</td></tr></tbody></table>
            </div>
            <svg v-else class="payoff-chart" viewBox="0 0 650 320" role="img" aria-labelledby="payoff-chart-title payoff-chart-description">
              <title id="payoff-chart-title">Stock, Income and Upside settlement values</title><desc id="payoff-chart-description">{{ chartDescription }}</desc>
              <g class="chart-grid"><template v-for="tick in gridTicks" :key="tick"><line x1="74" x2="528" :y1="y(tick)" :y2="y(tick)"/><text x="63" :y="y(tick) + 5" text-anchor="end">{{ money(tick) }}</text></template></g>
              <g class="chart-axis"><text v-for="tick in [low, model.spot, high]" :key="tick" :x="x(tick)" y="301" text-anchor="middle">{{ money(tick) }}</text></g>
              <line class="strike-line" :x1="x(model.strike)" :x2="x(model.strike)" y1="44" y2="276"/><text class="reference-label" :x="x(model.strike)" y="34" text-anchor="middle">K {{ money(model.strike) }}</text>
              <text class="reference-label" :x="x(model.spot)" y="14" text-anchor="middle">P0 / now {{ money(model.spot) }}</text>
              <path class="stock-line" :d="stockPath"/><path class="income-line" :d="incomePath"/><path class="upside-line" :d="upsidePath"/>
              <line class="settlement-line" :x1="x(settlement)" :x2="x(settlement)" y1="44" y2="276"/>
              <text class="settlement-label" :x="x(settlement) + (settlement > 285 ? -12 : 12)" y="66" :text-anchor="settlement > 285 ? 'end' : 'start'">S {{ money(settlement) }}</text>
              <circle class="income-point" :cx="x(settlement)" :cy="y(model.incomeSettlement)" r="7"/><circle class="upside-point" :cx="x(settlement)" :cy="y(model.upsideSettlement)" r="8"/>
              <g class="endpoint stock-endpoint"><circle cx="541" :cy="y(high)" r="3.5"/><text x="550" :y="y(high) + 5">{{ money(high) }}</text></g>
              <g class="endpoint income-endpoint"><circle cx="541" :cy="y(model.strike)" r="3.5"/><text x="550" :y="y(model.strike) + 5">{{ money(model.strike) }}</text></g>
              <g class="endpoint upside-endpoint"><circle cx="541" :cy="y(high - model.strike)" r="3.5"/><text x="550" :y="y(high - model.strike) + 5">{{ money(high - model.strike) }}</text></g>
            </svg>
          </div>

          <div class="settlement-control"><div class="settlement-label-row"><label for="settlement-range">Settlement price S</label><output for="settlement-range">{{ money(settlement) }} <small>{{ change }} vs P0</small></output></div><input id="settlement-range" v-model.number="settlement" type="range" :min="low" :max="high" :step="Math.max(props.spot / 100, 0.000001)" :style="{ '--range-fill': `${(settlement - low) / (high - low) * 100}%` }" :aria-valuetext="`${money(settlement)}, ${change} versus initial stock price`" aria-describedby="settlement-summary"></div>
          <div id="settlement-summary" class="settlement-values" aria-live="polite" aria-atomic="true">
            <div class="value-row"><span class="value-label legend-income">Income /<br> min(S, K)</span><div><strong>{{ money(model.incomeSettlement) }}</strong><small> + premium {{ money(model.premium) }} if subscribed (model)<br> = {{ money(model.incomeWithPremium) }}</small></div></div>
            <div class="value-row"><span class="value-label legend-upside">Upside / max(S - K, 0)</span><div><strong>{{ money(model.upsideSettlement) }}</strong><small> breakeven {{ money(model.breakeven) }} (model)</small></div></div>
          </div>
          <p class="chart-disclaimer">Indicative premium <b>{{ money(model.premium) }}</b> per unit / model at 25% vol / 30 days / the auction sets the price. Values per unit; Income is paid in SPL market units worth min(S, K); the premium goes to subscribers only.</p>
        </div>

        <div class="position-card income-card"><div class="position-label"><span class="position-mark"><ArrowDown :size="14" /></span><b>INCOME</b><span>(Up to the cap)</span></div><div class="position-price"><strong>{{ money(model.incomePrice) }}</strong><span>~{{ model.incomeShare.toFixed(1) }}%</span></div><div class="position-track" aria-hidden="true"><span :style="{ width: `${model.incomeShare}%` }"></span></div></div>
        <div class="position-card upside-card"><div class="position-label"><span class="position-mark"><ArrowUp :size="14" /></span><b>UPSIDE</b><span>(Above the cap)</span></div><div class="position-price"><strong>{{ money(model.upsidePrice) }}</strong><span>~{{ model.upsideShare.toFixed(1) }}%</span></div><div class="position-track" aria-hidden="true"><span :style="{ width: `${model.upsideShare}%` }"></span></div></div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.payoff-section{scroll-margin-top:70px;padding:32px 0 42px;background:var(--panel);border-block:1px solid var(--line)}.payoff-layout{display:grid;grid-template-columns:minmax(190px,.55fr) minmax(0,1.45fr);gap:22px}.cap-copy h2{margin:0 0 12px;font-size:30px;line-height:1.08;letter-spacing:-.035em}.cap-lead{margin:0 0 12px;color:var(--accent);font:600 10px var(--mono,monospace);text-transform:uppercase}.cap-explanation{margin:0;color:var(--muted);font-size:13px;line-height:1.6}.cap-control{margin-top:25px}.cap-ticks{display:flex;justify-content:space-between;margin-top:5px;color:var(--muted);font:9px var(--mono,monospace)}.cap-ticks .selected-tick{color:var(--accent)}.control-label,.settlement-label-row{display:flex;justify-content:space-between;align-items:center;color:var(--muted);font:600 10px var(--mono,monospace);text-transform:uppercase}.control-label output,.settlement-label-row output{color:var(--mint)}.model-note{margin-top:9px;color:var(--muted);font:10px/1.5 var(--mono,monospace)}.payoff-visual{min-width:0}.settlement-card{padding:15px;border:1px solid var(--line);background:var(--surface);box-shadow:0 12px 35px #0003}.chart-heading{display:flex;justify-content:space-between;gap:12px;align-items:start}.chart-heading h3{margin:0;font-size:15px}.chart-heading p{margin:5px 0 0;color:var(--muted);font:10px var(--mono,monospace)}.table-toggle{height:30px;padding:0 10px;color:var(--mint);border:1px solid #75d8a855;background:var(--panel);font:10px var(--mono,monospace);cursor:pointer}.chart-legend{display:flex;gap:15px;margin:13px 0 8px;padding:0;list-style:none;color:var(--muted);font:10px var(--mono,monospace)}.chart-legend li{position:relative;padding-left:12px}.chart-legend li:before{content:'';position:absolute;left:0;top:.45em;width:8px;height:2px;background:currentColor}.legend-stock{color:var(--muted)}.legend-income{color:var(--mint)}.legend-upside{color:var(--pink)}.payoff-display{border:1px solid var(--line);background:var(--panel)}.payoff-chart{display:block;width:100%;height:auto;min-height:220px}.chart-grid line{stroke:var(--line)}.chart-grid text,.chart-axis text,.reference-label,.endpoint text{fill:var(--muted);font:10px var(--mono,monospace)}.stock-line{stroke:var(--muted)}.income-line{stroke:var(--mint)}.upside-line{stroke:var(--pink)}.strike-line,.settlement-line{stroke:var(--accent)}.settlement-label{fill:var(--accent);font:600 11px var(--mono,monospace)}.income-point{fill:var(--mint);stroke:var(--panel);stroke-width:3}.upside-point{fill:var(--pink);stroke:var(--panel);stroke-width:3}.income-endpoint circle{fill:var(--mint)}.upside-endpoint circle{fill:var(--pink)}.stock-endpoint circle{fill:var(--muted)}.settlement-control{padding:14px 0 4px}.settlement-control input{width:100%;accent-color:var(--accent)}.settlement-label-row small{color:var(--muted);font-weight:400}.value-row{display:flex;justify-content:space-between;gap:12px;padding:10px 0;border-top:1px solid var(--line);color:var(--muted);font:10px var(--mono,monospace)}.value-row>div{text-align:right}.value-row strong{display:block;color:var(--fg);font-size:14px;font-weight:500}.value-row small{color:var(--muted)}.value-label{color:var(--mint)}.value-row:nth-child(2) .value-label{color:var(--pink)}.chart-disclaimer{margin:10px 0 0;color:var(--muted);font:9px/1.5 var(--mono,monospace)}.chart-disclaimer b{color:var(--accent)}.position-card{margin-top:7px;padding:12px 14px;border:1px solid var(--line);background:var(--surface)}.income-card{--position-color:var(--mint)}.upside-card{--position-color:var(--pink)}.position-label{display:flex;gap:7px;align-items:center;color:var(--muted);font:10px var(--mono,monospace)}.position-label b{color:var(--fg)}.position-mark{color:var(--position-color)}.position-price{display:flex;justify-content:space-between;align-items:baseline;margin:7px 0 9px;font-family:var(--mono,monospace)}.position-price strong{font-size:22px;font-weight:500}.position-price span{color:var(--muted);font-size:10px}.position-track{height:3px;background:var(--line)}.position-track>span{display:block;height:100%;background:var(--position-color)}.payoff-table-wrap{max-height:220px;overflow:auto}.payoff-table{width:100%;border-collapse:collapse;color:var(--fg);font:11px var(--mono,monospace)}.payoff-table th,.payoff-table td{padding:8px;border-bottom:1px solid var(--line);text-align:right}.payoff-table th:first-child{text-align:left}.payoff-table thead th{position:sticky;top:0;background:var(--raised);color:var(--muted)}.payoff-table .current-row{background:#1b2b20}.current-label{display:block;color:var(--mint);font-size:9px}@media(max-width:800px){.payoff-layout{grid-template-columns:1fr}.cap-copy{max-width:600px}}@media(max-width:480px){.payoff-section{padding:26px 0 32px}.cap-copy h2{font-size:27px}.settlement-card{padding:11px}.payoff-chart{min-height:185px}.chart-heading p{font-size:9px}.position-price strong{font-size:21px}}
</style>


