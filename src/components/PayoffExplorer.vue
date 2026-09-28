<script setup>
import { computed, ref } from 'vue'
import { ArrowDown, ArrowUp } from 'lucide-vue-next'
import { calculatePayoff } from '../payoff.js'

const cap = ref(5)
const settlement = ref(250)
const showTable = ref(false)
const model = computed(() => calculatePayoff({ capPercent: cap.value, settlementPrice: settlement.value }))
const money = value => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value)
const change = computed(() => `${model.value.spotChangePercent > 0 ? '+' : ''}${model.value.spotChangePercent.toFixed(1)}%`)
const x = value => 74 + (value - 175) / 150 * 454
const y = value => 276 - value / 400 * 232
const stockPath = `M ${x(175)} ${y(175)} L ${x(325)} ${y(325)}`
const incomePath = computed(() => `M ${x(175)} ${y(175)} L ${x(model.value.strike)} ${y(model.value.strike)} L ${x(325)} ${y(model.value.strike)}`)
const upsidePath = computed(() => `M ${x(175)} ${y(0)} L ${x(model.value.strike)} ${y(0)} L ${x(325)} ${y(325 - model.value.strike)}`)
const tableRows = computed(() => [...new Set([175, 200, 225, 250, model.value.strike, 275, 300, 325, settlement.value])].sort((a, b) => a - b).map(price => ({
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
        <p class="cap-explanation">A higher cap keeps more of the move in Income. A lower cap sells more of it to Upside, for a larger premium. At settlement, Upside takes the amount above K; Income keeps the rest plus the premium.</p>

        <div class="cap-control">
          <div class="control-label"><label for="cap-range">Cap</label><output for="cap-range">+{{ cap }}%</output></div>
          <input id="cap-range" v-model.number="cap" type="range" min="0" max="10" step="1" :style="{ '--range-fill': `${cap * 10}%` }" :aria-valuetext="`${cap}% cap, strike ${money(model.strike)}`" aria-describedby="cap-model-note">
          <div class="cap-ticks" aria-hidden="true"><span>0%</span><span>2%</span><span :class="{ 'selected-tick': cap === 5 }">5%</span><span>10%</span></div>
          <p id="cap-model-note" class="model-note">SOL example at <span>{{ money(model.spot) }}</span> / cap price (K) <span>{{ money(model.strike) }}</span> / 30 days / model at 25% vol</p>
        </div>
      </div>

      <div class="payoff-visual">
        <div class="settlement-card">
          <div class="chart-heading"><div><h3>Value at settlement</h3><p>Per unit / SOL example at {{ money(model.spot) }} / cap +{{ cap }}% / K {{ money(model.strike) }}</p></div><button class="table-toggle" type="button" :aria-pressed="showTable" aria-controls="payoff-display" @click="showTable = !showTable">{{ showTable ? 'Chart' : 'Table' }}</button></div>
          <ul class="chart-legend" aria-label="Chart legend"><li class="legend-stock">SOL market unit</li><li class="legend-income">Income</li><li class="legend-upside">Upside</li></ul>

          <div id="payoff-display" class="payoff-display">
            <div v-if="showTable" class="payoff-table-wrap" tabindex="0" role="region" aria-label="Settlement values table">
              <table class="payoff-table"><caption>Per-unit settlement value, before premium</caption><thead><tr><th scope="col">Stock price</th><th scope="col">Income</th><th scope="col">Upside</th></tr></thead><tbody><tr v-for="row in tableRows" :key="row.price" :class="{ 'current-row': row.price === settlement }"><th scope="row">{{ money(row.price) }}<span v-if="row.price === settlement" class="current-label">Current</span></th><td>{{ money(row.income) }}</td><td>{{ money(row.upside) }}</td></tr></tbody></table>
            </div>
            <svg v-else class="payoff-chart" viewBox="0 0 650 320" role="img" aria-labelledby="payoff-chart-title payoff-chart-description">
              <title id="payoff-chart-title">Stock, Income and Upside settlement values</title><desc id="payoff-chart-description">{{ chartDescription }}</desc>
              <g class="chart-grid"><template v-for="tick in [0, 100, 200, 300, 400]" :key="tick"><line x1="74" x2="528" :y1="y(tick)" :y2="y(tick)"/><text x="63" :y="y(tick) + 5" text-anchor="end">${{ tick }}</text></template></g>
              <g class="chart-axis"><text v-for="tick in [200, 250, 300]" :key="tick" :x="x(tick)" y="301" text-anchor="middle">${{ tick }}</text></g>
              <line class="strike-line" :x1="x(model.strike)" :x2="x(model.strike)" y1="44" y2="276"/><text class="reference-label" :x="x(model.strike)" y="34" text-anchor="middle">K {{ money(model.strike) }}</text>
              <text class="reference-label" :x="x(250)" y="14" text-anchor="middle">P0 / now $250.00</text>
              <path class="stock-line" :d="stockPath"/><path class="income-line" :d="incomePath"/><path class="upside-line" :d="upsidePath"/>
              <line class="settlement-line" :x1="x(settlement)" :x2="x(settlement)" y1="44" y2="276"/>
              <text class="settlement-label" :x="x(settlement) + (settlement > 285 ? -12 : 12)" y="66" :text-anchor="settlement > 285 ? 'end' : 'start'">S {{ money(settlement) }}</text>
              <circle class="income-point" :cx="x(settlement)" :cy="y(model.incomeSettlement)" r="7"/><circle class="upside-point" :cx="x(settlement)" :cy="y(model.upsideSettlement)" r="8"/>
              <g class="endpoint stock-endpoint"><circle cx="541" :cy="y(325)" r="3.5"/><text x="550" :y="y(325) + 5">$325.00</text></g>
              <g class="endpoint income-endpoint"><circle cx="541" :cy="y(model.strike)" r="3.5"/><text x="550" :y="y(model.strike) + 5">{{ money(model.strike) }}</text></g>
              <g class="endpoint upside-endpoint"><circle cx="541" :cy="y(325 - model.strike)" r="3.5"/><text x="550" :y="y(325 - model.strike) + 5">{{ money(325 - model.strike) }}</text></g>
            </svg>
          </div>

          <div class="settlement-control"><div class="settlement-label-row"><label for="settlement-range">Settlement price S</label><output for="settlement-range">{{ money(settlement) }} <small>{{ change }} vs P0</small></output></div><input id="settlement-range" v-model.number="settlement" type="range" min="175" max="325" step="1" :style="{ '--range-fill': `${(settlement - 175) / 1.5}%` }" :aria-valuetext="`${money(settlement)}, ${change} versus initial stock price`" aria-describedby="settlement-summary"></div>
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
.payoff-section {scroll-margin-top:90px;
  padding: 62px 0 74px; color: var(--fg);
}
.payoff-layout {
  display:grid;align-items:start;
  gap: 38px; grid-template-columns: minmax(0, .8fr) minmax(0, 1.2fr);
}
.cap-copy h2 {
  margin:0 0 22px;font-weight:550;line-height:1.02;
  margin-bottom: 15px; font-size: clamp(30px, 4vw, 42px); letter-spacing: -.04em;
}
.cap-lead {
  margin:0 0 20px;font-size:15px;line-height:1.6;
  margin-bottom: 13px; color: var(--amber); font: 11px var(--mono); text-transform: uppercase;
}
.cap-explanation {margin:0;
  max-width: 470px; color: #879caf; font-size: 12px; line-height: 1.65;
}
.cap-control {
  margin-top: 27px;
}
.control-label {
  display:flex;justify-content:space-between;align-items:center;margin-bottom:13px;font-size:12px;
  color: #8195a7; font: 10px var(--mono); text-transform: uppercase;
}
.control-label output {
  font-family:var(--mono,monospace);
  color: var(--cyan);
}
input[type=range] {
  display:block;width:100%;height:22px;margin:0;padding:0;appearance:none;-webkit-appearance:none;cursor:pointer;background:transparent;accent-color:var(--cyan);
}
input[type=range]::-webkit-slider-runnable-track {
  height:3px;
  background: linear-gradient(to right, var(--cyan) 0 var(--range-fill), #263c50 var(--range-fill) 100%);
}
input[type=range]::-moz-range-track {
  height:3px;
  background: linear-gradient(to right, var(--cyan) 0 var(--range-fill), #263c50 var(--range-fill) 100%);
}
input[type=range]::-webkit-slider-thumb {
  width:20px;height:20px;margin-top:-8.5px;border:3px solid var(--bg);border-radius:50%;outline:1px solid var(--amber);appearance:none;-webkit-appearance:none;
  border-color: #0a111a; background: var(--cyan); outline-color: var(--cyan);
}
input[type=range]::-moz-range-thumb {
  width:14px;height:14px;border:3px solid var(--bg);border-radius:50%;outline:1px solid var(--amber);
  border-color: #0a111a; background: var(--cyan); outline-color: var(--cyan);
}
input[type=range]:focus-visible {
  outline:2px solid var(--cyan);outline-offset:5px;border-radius:3px;
}
.cap-ticks {
  position:relative;height:35px;margin:9px 5px 0;font-family:var(--mono,monospace);font-size:10px;
  color: #6f8497;
}
.cap-ticks span {
  position:absolute;top:10px;transform:translateX(-50%);
}
.cap-ticks span::before {
  content:'';position:absolute;top:-10px;left:50%;width:4px;height:4px;transform:translateX(-50%);border-radius:50%;
  background: #365269;
}
.cap-ticks span:nth-child(1) {
  left:0;transform:none;
}
.cap-ticks span:nth-child(2) {
  left:20%;
}
.cap-ticks span:nth-child(3) {
  left:50%;
}
.cap-ticks span:nth-child(4) {
  right:0;transform:none;
}
.cap-ticks .selected-tick {font-weight:700;
  color: var(--cyan);
}
.cap-ticks .selected-tick::before {
  background: var(--cyan);
}
.model-note {
  margin:0;font-size:10px;line-height:1.9;
  color: #6f8497;
}
.model-note span {
  font-family:var(--mono,monospace);
}
.settlement-card {border:1px solid var(--line);
  padding: 15px; border-radius: 4px; background: #0e1521;
}
.chart-heading {
  display:flex;align-items:flex-start;justify-content:space-between;gap:8px;
}
.chart-heading h3 {
  margin:0 0 3px;font-weight:550;line-height:1.3;
  font-family: var(--mono); font-size: 12px; text-transform: uppercase;
}
.chart-heading p {
  margin:0;line-height:1.5;
  color: #758ba0; font-size: 9px;
}
.table-toggle {
  flex-shrink:0;border:1px solid var(--line);font-size:10px;line-height:1.4;cursor:pointer;
  padding: 5px 9px; border-color: #29445b; border-radius: 3px; background: #101e2c; color: var(--cyan); font: 9px var(--mono); text-transform: uppercase;
}
.table-toggle:hover {
  background: #123547;
}
.table-toggle:focus-visible {
  outline:2px solid var(--cyan);outline-offset:3px;
}
.chart-legend {
  display:flex;flex-wrap:wrap;padding:0;list-style:none;font-size:10px;
  gap: 13px; margin: 10px 0 8px; color: #7e94a6; font: 9px var(--mono); text-transform: uppercase;
}
.chart-legend li,.value-label {
  position:relative;padding-left:20px;
}
.chart-legend li::before,.value-label::before {
  content:'';position:absolute;left:0;top:.65em;width:14px;height:2px;background:var(--series-color);
}
.legend-stock {
  --series-color:var(--muted);
}
.legend-income {
  --series-color:var(--cyan);
}
.legend-upside {
  --series-color:var(--amber);
}
.payoff-display {overflow:hidden;
  border: 1px solid var(--line); border-radius: 3px; background: #080d15;
}
.payoff-chart {
  display:block;width:100%;height:auto;min-height:218px;padding:14px 0 4px;overflow:visible;
}
.payoff-chart text {
  font-family:var(--mono,monospace);
  fill: #6e8498; font-size: 11px;
}
.chart-grid line {stroke-width:1;
  stroke: #172c3e;
}
.chart-axis text {
  font-size:14px;
}
.payoff-chart .reference-label {
  fill: #72879b; font-size: 10px;
}
.strike-line {stroke-dasharray:4 5;stroke-width:1.4;
  stroke: var(--amber);
}
.stock-line,.income-line,.upside-line {
  fill:none;stroke-width:2.6;
}
.stock-line {
  stroke: #6c8297;
}
.income-line {
  stroke: var(--cyan);
}
.upside-line {
  stroke: var(--magenta);
}
.settlement-line {stroke-width:2;
  stroke: var(--amber);
}
.payoff-chart .settlement-label {font-weight:700;
  fill: var(--amber); font-size: 12px;
}
.income-point {stroke-width:3;
  fill: var(--cyan); stroke: #071019;
}
.upside-point {stroke-width:3;
  fill: var(--magenta); stroke: #071019;
}
.endpoint text {
  fill: #a9b9c6; font-size: 10px;
}
.stock-endpoint circle {
  fill: #6c8297;
}
.income-endpoint circle {
  fill: var(--cyan);
}
.upside-endpoint circle {
  fill: var(--magenta);
}
.settlement-control {
  padding: 14px 0 6px;
}
.settlement-label-row {
  display:flex;justify-content:space-between;gap:8px;align-items:center;font-size:11px;
  color: #7e94a6; font: 9px var(--mono); text-transform: uppercase;
}
.settlement-label-row output {font-family:var(--mono,monospace);
  color: var(--cyan); font-size: 11px;
}
.settlement-label-row small {font-size:10px;
  color: #6e8498;
}
.settlement-control input {
  height:18px;margin-top:7px;
}
.settlement-control input::-webkit-slider-runnable-track {
  height:2px;
  background: linear-gradient(to right, var(--amber) 0 var(--range-fill), #263c50 var(--range-fill) 100%);
}
.settlement-control input::-moz-range-track {
  height:2px;
  background: linear-gradient(to right, var(--amber) 0 var(--range-fill), #263c50 var(--range-fill) 100%);
}
.settlement-control input::-webkit-slider-thumb {
  width:12px;height:12px;margin-top:-5px;border:2px solid var(--bg,var(--bg));outline:1px solid #47647b;
  outline-color: var(--amber); background: var(--amber);
}
.settlement-control input::-moz-range-thumb {
  width:8px;height:8px;border:2px solid var(--bg,var(--bg));outline:1px solid #47647b;
  outline-color: var(--amber); background: var(--amber);
}
.value-row {
  display:flex;justify-content:space-between;gap:16px;align-items:center;border-top:1px solid var(--line);padding:13px 0;font-size:11px;line-height:1.5;
  border-top-color: var(--line); color: #7d92a5;
}
.value-row>div {
  text-align:right;font-family:var(--mono,monospace);
}
.value-row strong {font-size:14px;font-weight:400;
  color: var(--fg);
}
.value-row small {
  font-size:10px;
}
.value-label {
  flex-shrink:0;max-width:160px;
  font-family: var(--mono); font-size: 9px; text-transform: uppercase;
}
.value-label::before {
  top:1.1em;
  background: var(--series-color);
}
.chart-disclaimer {
  margin:10px 0 0;font-size:10px;line-height:1.8;
  color: #6e8498; font: 9px/1.7 var(--mono);
}
.chart-disclaimer b {
  font-family:var(--mono,monospace);font-weight:400;
  color: var(--amber);
}
.position-card {border:1px solid var(--line);
  margin-top: 8px; padding: 14px; border-radius: 4px;
}
.income-card {--position-color:var(--cyan);
  background: #0d2632;
}
.upside-card {--position-color:var(--magenta);
  background: #2b1629;
}
.position-label {
  display:flex;align-items:center;gap:8px;font-size:11px;line-height:1.5;
  color: #8195a7; font: 9px var(--mono); text-transform: uppercase;
}
.position-label b {
  font-size:10px;font-weight:500;letter-spacing:1.4px;
  color: var(--fg);
}
.position-mark {
  color:var(--position-color);font-size:14px;
}
.position-price {
  display:flex;align-items:baseline;justify-content:space-between;gap:20px;font-family:var(--mono);
  margin: 7px 0 11px;
}
.position-price strong {line-height:1.3;font-weight:400;letter-spacing:-1px;
  font-size: 25px;
}
.position-price>span {
  font-size:10px;color:var(--muted);
}
.position-track {overflow:hidden;border-radius:3px;
  height: 3px; background: #203648;
}
.position-track>span {
  display:block;height:100%;border-radius:3px;background:var(--position-color);min-width:3px;transition:width .2s ease;
}
.payoff-table-wrap {overflow:auto;
  height: 215px;
}
.payoff-table {
  width:100%;border-collapse:collapse;text-align:right;font-family:var(--mono,monospace);
  color: var(--fg); font-size: 10px;
}
.payoff-table caption {
  padding:9px;font-family:inherit;font-size:10px;text-align:left;
  color: #71869a;
}
.payoff-table th,.payoff-table td {border-bottom:1px solid var(--line);font-weight:400;white-space:nowrap;
  border-bottom-color: var(--line); padding: 8px 10px;
}
.payoff-table thead th {
  position:sticky;top:0;font-weight:600;
  background: #101e2c; color: #8fa3b4;
}
.payoff-table th:first-child {
  text-align:left;
}
.payoff-table .current-row {
  background: #103242;
}
.current-label {
  display:block;font-size:9px;
  color: var(--cyan);
}
@media(min-width:1500px) {
  .payoff-layout {
    gap:180px;
  }
}
@media(max-width:1150px) {
  .payoff-layout {
    gap:70px;grid-template-columns:1fr 1fr;
  }
  .cap-copy h2 {
    font-size:44px;
  }
  .value-row {
    gap:8px;
  }
  .value-row small {
    font-size:9px;
  }
}
@media(max-width:850px) {
  .payoff-section {
    padding: 48px 0 60px;
  }
  .payoff-layout {
    gap: 28px; grid-template-columns: 1fr;
  }
  .cap-copy {
    max-width:600px;
  }
  .cap-copy h2 {
    font-size:42px;
  }
  .cap-explanation {
    max-width:470px;
  }
  .payoff-visual {
    max-width:590px;width:100%;
  }
  .cap-control {
    margin-top:30px;
  }
  .settlement-card {
    padding:20px;
  }
  .value-row small {
    font-size:10px;
  }
}
@media(max-width:480px) {
  .payoff-section {
    padding: 42px 0 52px;
  }
  .cap-copy h2 {letter-spacing:-1.6px;
    font-size: 30px;
  }
  .cap-lead {
    font-size:13px;
  }
  .cap-explanation {
    font-size:13px;
  }
  .settlement-card {border-radius:14px;
    padding: 11px;
  }
  .chart-heading p {
    font-size:9px;
  }
  .chart-heading h3 {
    font-size:13px;
  }
  .chart-legend {
    gap:12px;font-size:9px;
  }
  .chart-legend li {
    padding-left:16px;
  }
  .chart-legend li::before {
    width:11px;
  }
  .payoff-chart {
    min-height:185px;
  }
  .settlement-label-row {
    font-size:10px;
  }
  .settlement-label-row output {
    font-size:12px;
  }
  .settlement-label-row small {
    font-size:8px;
  }
  .value-row {
    gap:9px;font-size:10px;align-items:start;
  }
  .value-label {
    max-width:107px;padding-left:16px;
  }
  .value-label::before {
    width:10px;
  }
  .value-row strong {
    font-size:12px;
  }
  .value-row small {
    font-size:8px;
  }
  .position-card {
    padding: 12px;
  }
  .position-price strong {
    font-size:28px;
  }
  .chart-disclaimer {
    font-size:9px;
  }
}
@media(prefers-reduced-motion:reduce) {
  .position-track>span {
    transition:none;
  }
}
.position-price > span {
  color: #71869a; font: 9px var(--mono);
}
</style>
