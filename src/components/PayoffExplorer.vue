<script setup>
import { computed, ref } from 'vue'
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
          <p id="cap-model-note" class="model-note">ETHX example at <span>{{ money(model.spot) }}</span> · cap price (K) <span>{{ money(model.strike) }}</span> · 30 days · model at 25% vol</p>
        </div>
      </div>

      <div class="payoff-visual">
        <div class="settlement-card">
          <div class="chart-heading"><div><h3>Value at settlement</h3><p>Per unit · ETHX example at {{ money(model.spot) }} · cap +{{ cap }}% · K {{ money(model.strike) }}</p></div><button class="table-toggle" type="button" :aria-pressed="showTable" aria-controls="payoff-display" @click="showTable = !showTable">{{ showTable ? 'Chart' : 'Table' }}</button></div>
          <ul class="chart-legend" aria-label="Chart legend"><li class="legend-stock">ETHX market unit</li><li class="legend-income">Income</li><li class="legend-upside">Upside</li></ul>

          <div id="payoff-display" class="payoff-display">
            <div v-if="showTable" class="payoff-table-wrap" tabindex="0" role="region" aria-label="Settlement values table">
              <table class="payoff-table"><caption>Per-unit settlement value, before premium</caption><thead><tr><th scope="col">Stock price</th><th scope="col">Income</th><th scope="col">Upside</th></tr></thead><tbody><tr v-for="row in tableRows" :key="row.price" :class="{ 'current-row': row.price === settlement }"><th scope="row">{{ money(row.price) }}<span v-if="row.price === settlement" class="current-label">Current</span></th><td>{{ money(row.income) }}</td><td>{{ money(row.upside) }}</td></tr></tbody></table>
            </div>
            <svg v-else class="payoff-chart" viewBox="0 0 650 320" role="img" aria-labelledby="payoff-chart-title payoff-chart-description">
              <title id="payoff-chart-title">Stock, Income and Upside settlement values</title><desc id="payoff-chart-description">{{ chartDescription }}</desc>
              <g class="chart-grid"><template v-for="tick in [0, 100, 200, 300, 400]" :key="tick"><line x1="74" x2="528" :y1="y(tick)" :y2="y(tick)"/><text x="63" :y="y(tick) + 5" text-anchor="end">${{ tick }}</text></template></g>
              <g class="chart-axis"><text v-for="tick in [200, 250, 300]" :key="tick" :x="x(tick)" y="301" text-anchor="middle">${{ tick }}</text></g>
              <line class="strike-line" :x1="x(model.strike)" :x2="x(model.strike)" y1="44" y2="276"/><text class="reference-label" :x="x(model.strike)" y="34" text-anchor="middle">K {{ money(model.strike) }}</text>
              <text class="reference-label" :x="x(250)" y="14" text-anchor="middle">P0 · now $250.00</text>
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
            <div class="value-row"><span class="value-label legend-income">Income ·<br> min(S, K)</span><div><strong>{{ money(model.incomeSettlement) }}</strong><small> + premium {{ money(model.premium) }} if subscribed (model)<br> = {{ money(model.incomeWithPremium) }}</small></div></div>
            <div class="value-row"><span class="value-label legend-upside">Upside · max(S − K, 0)</span><div><strong>{{ money(model.upsideSettlement) }}</strong><small> breakeven {{ money(model.breakeven) }} (model)</small></div></div>
          </div>
          <p class="chart-disclaimer">Indicative premium <b>{{ money(model.premium) }}</b> per unit · model at 25% vol · 30 days · the auction sets the price. Values per unit; Income is paid in Stock Tokens worth min(S, K); the premium goes to subscribers only.</p>
        </div>

        <div class="position-card income-card"><div class="position-label"><span class="position-mark">◢</span><b>INCOME</b><span>(Up to the cap)</span></div><div class="position-price"><strong>{{ money(model.incomePrice) }}</strong><span>~{{ model.incomeShare.toFixed(1) }}%</span></div><div class="position-track" aria-hidden="true"><span :style="{ width: `${model.incomeShare}%` }"></span></div></div>
        <div class="position-card upside-card"><div class="position-label"><span class="position-mark">↗</span><b>UPSIDE</b><span>(Above the cap)</span></div><div class="position-price"><strong>{{ money(model.upsidePrice) }}</strong><span>~{{ model.upsideShare.toFixed(1) }}%</span></div><div class="position-track" aria-hidden="true"><span :style="{ width: `${model.upsideShare}%` }"></span></div></div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.payoff-section{padding:104px 0 112px;scroll-margin-top:90px;color:var(--fg,#0f1f18)}
.payoff-layout{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,1fr);gap:160px;align-items:start}
.cap-copy h2{margin:0 0 22px;font-size:48px;font-weight:550;line-height:1.02;letter-spacing:-2.2px}
.cap-lead{margin:0 0 20px;font-size:15px;line-height:1.6;color:var(--fg,#0f1f18)}
.cap-explanation{max-width:405px;margin:0;color:var(--muted,#4d5f56);font-size:14px;line-height:1.65}
.cap-control{margin-top:38px}
.control-label{display:flex;justify-content:space-between;align-items:center;margin-bottom:13px;font-size:12px;color:var(--muted,#4d5f56)}
.control-label output{font-family:var(--mono,monospace);color:var(--fg,#0f1f18)}
input[type=range]{display:block;width:100%;height:22px;margin:0;padding:0;appearance:none;-webkit-appearance:none;cursor:pointer;background:transparent;accent-color:var(--green,#006838)}
input[type=range]::-webkit-slider-runnable-track{height:3px;background:linear-gradient(to right,var(--lime,#d5ef00) 0 var(--range-fill),#b8bcb4 var(--range-fill) 100%)}
input[type=range]::-moz-range-track{height:3px;background:linear-gradient(to right,var(--lime,#d5ef00) 0 var(--range-fill),#b8bcb4 var(--range-fill) 100%)}
input[type=range]::-webkit-slider-thumb{width:20px;height:20px;margin-top:-8.5px;border:3px solid var(--bg,#f0ebe5);border-radius:50%;background:var(--fg,#0f1f18);outline:1px solid var(--lime,#d5ef00);appearance:none;-webkit-appearance:none}
input[type=range]::-moz-range-thumb{width:14px;height:14px;border:3px solid var(--bg,#f0ebe5);border-radius:50%;background:var(--fg,#0f1f18);outline:1px solid var(--lime,#d5ef00)}
input[type=range]:focus-visible{outline:2px solid var(--green,#006838);outline-offset:5px;border-radius:3px}
.cap-ticks{position:relative;height:35px;margin:9px 5px 0;color:var(--muted,#4d5f56);font-family:var(--mono,monospace);font-size:10px}
.cap-ticks span{position:absolute;top:10px;transform:translateX(-50%)}
.cap-ticks span::before{content:'';position:absolute;top:-10px;left:50%;width:4px;height:4px;transform:translateX(-50%);border-radius:50%;background:#b8bcb4}
.cap-ticks span:nth-child(1){left:0;transform:none}.cap-ticks span:nth-child(2){left:20%}.cap-ticks span:nth-child(3){left:50%}.cap-ticks span:nth-child(4){right:0;transform:none}
.cap-ticks .selected-tick{color:var(--fg,#0f1f18);font-weight:700}.cap-ticks .selected-tick::before{background:var(--lime,#d5ef00)}
.model-note{margin:0;font-size:10px;line-height:1.9;color:var(--muted,#4d5f56)}.model-note span{font-family:var(--mono,monospace)}
.settlement-card{padding:20px;border:1px solid var(--line,rgba(15,31,24,.12));border-radius:17px;background:rgba(255,255,255,.44)}
.chart-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:8px}.chart-heading h3{margin:0 0 3px;font-size:14px;font-weight:550;line-height:1.3}.chart-heading p{margin:0;font-size:11px;color:var(--muted,#4d5f56);line-height:1.5}
.table-toggle{flex-shrink:0;padding:6px 11px;border:1px solid var(--line,rgba(15,31,24,.12));border-radius:24px;background:#e6e1d6;color:var(--muted,#4d5f56);font:inherit;font-size:10px;line-height:1.4;cursor:pointer}.table-toggle:hover{background:#dad5c9}.table-toggle:focus-visible{outline:2px solid var(--green,#006838);outline-offset:3px}
.chart-legend{display:flex;gap:16px;flex-wrap:wrap;margin:13px 0 10px;padding:0;list-style:none;font-size:10px;color:var(--muted,#4d5f56)}.chart-legend li,.value-label{position:relative;padding-left:20px}.chart-legend li::before,.value-label::before{content:'';position:absolute;left:0;top:.65em;width:14px;height:2px;background:var(--series-color)}
.legend-stock{--series-color:#7e9185}.legend-income{--series-color:var(--green,#006838)}.legend-upside{--series-color:#94a500}
.payoff-display{border-radius:11px;background:var(--bg,#f0ebe5);overflow:hidden}.payoff-chart{display:block;width:100%;height:auto;min-height:218px;padding:14px 0 4px;overflow:visible}.payoff-chart text{font-family:var(--mono,monospace);font-size:14px;fill:var(--muted,#4d5f56)}.chart-grid line{stroke:#d5d0c7;stroke-width:1}.chart-axis text{font-size:14px}.payoff-chart .reference-label{font-size:13px;fill:#74877e}.strike-line{stroke:#bfbfb1;stroke-dasharray:4 5;stroke-width:1.4}.stock-line,.income-line,.upside-line{fill:none;stroke-width:2.6}.stock-line{stroke:#7e9185}.income-line{stroke:var(--green,#006838)}.upside-line{stroke:#91a000}.settlement-line{stroke:var(--fg,#0f1f18);stroke-width:2}.payoff-chart .settlement-label{fill:var(--fg,#0f1f18);font-weight:700;font-size:16px}.income-point{fill:var(--green,#006838);stroke:var(--bg,#f0ebe5);stroke-width:3}.upside-point{fill:var(--fg,#0f1f18);stroke:var(--bg,#f0ebe5);stroke-width:3}.endpoint text{fill:var(--fg,#0f1f18);font-size:14px}.stock-endpoint circle{fill:#7e9185}.income-endpoint circle{fill:var(--green,#006838)}.upside-endpoint circle{fill:#91a000}
.settlement-control{padding:20px 0 8px}.settlement-label-row{display:flex;justify-content:space-between;gap:8px;align-items:center;font-size:11px;color:var(--muted,#4d5f56)}.settlement-label-row output{color:var(--fg,#0f1f18);font-family:var(--mono,monospace);font-size:14px}.settlement-label-row small{color:var(--muted,#4d5f56);font-size:10px}.settlement-control input{height:18px;margin-top:7px}.settlement-control input::-webkit-slider-runnable-track{height:2px;background:linear-gradient(to right,#80978a 0 var(--range-fill),#d0d2c8 var(--range-fill) 100%)}.settlement-control input::-moz-range-track{height:2px;background:linear-gradient(to right,#80978a 0 var(--range-fill),#d0d2c8 var(--range-fill) 100%)}.settlement-control input::-webkit-slider-thumb{width:12px;height:12px;margin-top:-5px;border:2px solid var(--bg,#f0ebe5);outline:1px solid #80978a}.settlement-control input::-moz-range-thumb{width:8px;height:8px;border:2px solid var(--bg,#f0ebe5);outline:1px solid #80978a}
.value-row{display:flex;justify-content:space-between;gap:16px;align-items:center;border-top:1px solid var(--line,rgba(15,31,24,.12));padding:13px 0;color:var(--muted,#4d5f56);font-size:11px;line-height:1.5}.value-row>div{text-align:right;font-family:var(--mono,monospace)}.value-row strong{color:var(--fg,#0f1f18);font-size:14px;font-weight:400}.value-row small{font-size:10px}.value-label{flex-shrink:0;max-width:160px}.value-label::before{top:1.1em}.chart-disclaimer{margin:10px 0 0;color:var(--muted,#4d5f56);font-size:10px;line-height:1.8}.chart-disclaimer b{font-family:var(--mono,monospace);font-weight:400;color:var(--fg,#0f1f18)}
.position-card{margin-top:12px;padding:20px;border:1px solid var(--line,rgba(15,31,24,.12));border-radius:13px}.income-card{background:linear-gradient(125deg,rgba(0,104,56,.2),rgba(0,104,56,.03) 65%,rgba(0,104,56,.12));--position-color:var(--green,#006838)}.upside-card{background:linear-gradient(125deg,rgba(213,239,0,.23),rgba(213,239,0,.04) 65%,rgba(213,239,0,.13));--position-color:var(--lime,#d5ef00)}.position-label{display:flex;align-items:center;gap:8px;font-size:11px;line-height:1.5;color:var(--muted,#4d5f56)}.position-label b{font-size:10px;font-weight:500;letter-spacing:1.4px;color:var(--fg,#0f1f18)}.position-mark{color:var(--position-color);font-size:14px}.position-price{display:flex;align-items:baseline;justify-content:space-between;gap:20px;margin:9px 0 16px;font-family:var(--mono,monospace)}.position-price strong{font-size:30px;line-height:1.3;font-weight:400;letter-spacing:-1px}.position-price>span{font-size:10px;color:var(--muted,#4d5f56)}.position-track{height:4px;overflow:hidden;border-radius:3px;background:rgba(15,31,24,.16)}.position-track>span{display:block;height:100%;border-radius:3px;background:var(--position-color);min-width:3px;transition:width .2s ease}
.payoff-table-wrap{height:236px;overflow:auto}.payoff-table{width:100%;border-collapse:collapse;text-align:right;font-family:var(--mono,monospace);font-size:11px}.payoff-table caption{padding:9px;font-family:inherit;font-size:10px;color:var(--muted,#4d5f56);text-align:left}.payoff-table th,.payoff-table td{padding:9px 12px;border-bottom:1px solid var(--line,rgba(15,31,24,.12));font-weight:400;white-space:nowrap}.payoff-table thead th{position:sticky;top:0;background:#e6e1d6;font-weight:600}.payoff-table th:first-child{text-align:left}.payoff-table .current-row{background:rgba(0,104,56,.08)}.current-label{display:block;font-size:9px;color:var(--green,#006838)}
@media(min-width:1500px){.payoff-layout{gap:180px}}
@media(max-width:1150px){.payoff-layout{gap:70px;grid-template-columns:1fr 1fr}.cap-copy h2{font-size:44px}.value-row{gap:8px}.value-row small{font-size:9px}}
@media(max-width:850px){.payoff-section{padding:72px 0}.payoff-layout{gap:44px;grid-template-columns:1fr}.cap-copy{max-width:600px}.cap-copy h2{font-size:42px}.cap-explanation{max-width:470px}.payoff-visual{max-width:590px;width:100%}.cap-control{margin-top:30px}.settlement-card{padding:20px}.value-row small{font-size:10px}}
@media(max-width:480px){.payoff-section{padding:56px 0 64px}.cap-copy h2{font-size:38px;letter-spacing:-1.6px}.cap-lead{font-size:13px}.cap-explanation{font-size:13px}.settlement-card{padding:15px;border-radius:14px}.chart-heading p{font-size:9px}.chart-heading h3{font-size:13px}.chart-legend{gap:12px;font-size:9px}.chart-legend li{padding-left:16px}.chart-legend li::before{width:11px}.payoff-chart{min-height:185px}.settlement-label-row{font-size:10px}.settlement-label-row output{font-size:12px}.settlement-label-row small{font-size:8px}.value-row{gap:9px;font-size:10px;align-items:start}.value-label{max-width:107px;padding-left:16px}.value-label::before{width:10px}.value-row strong{font-size:12px}.value-row small{font-size:8px}.position-card{padding:17px}.position-price strong{font-size:28px}.chart-disclaimer{font-size:9px}}
@media(prefers-reduced-motion:reduce){.position-track>span{transition:none}}
</style>
