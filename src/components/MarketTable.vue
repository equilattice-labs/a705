<script setup>
import { computed } from 'vue'
import { calculatePayoff } from '../payoff.js'

const props = defineProps({
  compact: { type: Boolean, default: false },
  query: { type: String, default: '' },
  side: { type: String, default: 'All' },
})

const emit = defineEmits(['navigate', 'reset'])

const money = value => new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
}).format(value)

const assets = Object.freeze([
  { symbol: 'AAPL', name: 'Apple Inc.', spot: 250, initials: 'A' },
  { symbol: 'NVDA', name: 'NVIDIA Corp.', spot: 130, initials: 'N' },
  { symbol: 'MSFT', name: 'Microsoft Corp.', spot: 430, initials: 'M' },
  { symbol: 'TSLA', name: 'Tesla Inc.', spot: 350, initials: 'T' },
])

const allRows = assets.map(asset => ({
  ...asset,
  payoff: calculatePayoff({ spot: asset.spot, capPercent: 5, settlementPrice: asset.spot }),
}))

const rows = computed(() => {
  const needle = props.query.trim().toLocaleLowerCase()
  const source = allRows
  if (!needle) return source
  return source.filter(asset => `${asset.symbol} ${asset.name}`.toLocaleLowerCase().includes(needle))
})

const activeSide = computed(() => {
  const value = props.side.trim().toLocaleLowerCase()
  return value === 'income' || value === 'upside' ? value : ''
})

const stats = Object.freeze([
  { label: 'Premium received', detail: 'Model epoch' },
  { label: 'Open series', detail: 'Current epoch' },
  { label: 'Active income', detail: 'Indicative' },
  { label: 'Total volume', detail: 'Model ledger' },
])

function navigate(symbol) {
  emit('navigate', `/app/markets/${symbol}`)
}

function resetSearch() {
  emit('reset')
}
</script>

<template>
  <section class="market-table-section" :class="{ 'compact-market-table': compact }" :aria-label="compact ? 'Market quote table' : undefined" :aria-labelledby="!compact ? 'market-table-title' : undefined">
    <div v-if="!compact" class="market-table-heading">
      <div>
        <p class="market-eyebrow">Markets</p>
        <h2 id="market-table-title">Market quotes</h2>
      </div>
      <p class="market-feed-note"><span class="feed-dot" aria-hidden="true"></span>Example quotes · no live feed</p>
    </div>

    <div v-if="!compact" class="on-chain-stats" aria-label="On chain stats preview">
      <div class="stats-heading"><span>On chain stats</span><span class="stats-note">Interface preview · no live feed</span></div>
      <div class="stats-grid">
        <article v-for="stat in stats" :key="stat.label" class="stat-card">
          <div class="stat-card-top"><span>{{ stat.label }}</span><span class="preview-badge">Preview</span></div>
          <strong class="stat-value">—</strong>
          <small>{{ stat.detail }}</small>
        </article>
      </div>
    </div>

    <div class="market-table-toolbar">
      <p class="table-intro">Cap +5% · 30-day epoch · model values per unit</p>
      <p v-if="props.query.trim()" class="search-state" aria-live="polite">{{ rows.length }} result{{ rows.length === 1 ? '' : 's' }} for “{{ props.query.trim() }}”</p>
    </div>

    <div v-if="rows.length" class="table-scroll">
      <table class="market-table">
        <caption class="sr-only">Model market values. Quotes are examples and are not live prices.</caption>
        <thead>
          <tr>
            <th scope="col">Asset</th>
            <th scope="col">Cap</th>
            <th scope="col" :class="{ 'is-emphasized': activeSide === 'income' }">Income</th>
            <th scope="col" :class="{ 'is-emphasized': activeSide === 'upside' }">Upside</th>
            <th scope="col">Epoch</th>
            <th scope="col">Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="asset in rows" :key="asset.symbol">
            <td>
              <a class="asset-link" :href="`/app/markets/${asset.symbol}`" :aria-label="`Open ${asset.symbol} market, example quote ${money(asset.spot)}`" @click.prevent="navigate(asset.symbol)">
                <span class="token-circle" aria-hidden="true">{{ asset.initials }}</span>
                <span class="asset-copy"><b>{{ asset.symbol }}</b><small>{{ asset.name }} · Example quote</small></span>
              </a>
            </td>
            <td><span class="cap-value">+5%</span></td>
            <td :class="{ 'is-emphasized': activeSide === 'income' }"><span class="model-value income-value">{{ money(asset.payoff.incomePrice) }}</span><small class="quote-label">Model</small></td>
            <td :class="{ 'is-emphasized': activeSide === 'upside' }"><span class="model-value upside-value">{{ money(asset.payoff.upsidePrice) }}</span><small class="quote-label">Model</small></td>
            <td><span class="epoch-value">30 days</span></td>
            <td><span class="status-badge"><i aria-hidden="true"></i>Model</span></td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="empty-market-state" role="status" aria-live="polite">
      <p>No model markets match “{{ props.query.trim() }}”.</p>
      <button type="button" @click="resetSearch">Reset search</button>
    </div>

    <div class="market-table-footnote"><span>Indicative model values use a 30-day epoch and 25% volatility.</span><span>Example quotes are not live prices.</span></div>
  </section>
</template>

<style scoped>
.market-table-section{color:var(--fg,#0f1f18)}
.market-table-heading{display:flex;justify-content:space-between;align-items:flex-end;gap:22px;margin-bottom:27px}.market-eyebrow{margin:0 0 9px;color:var(--muted,#4d5f56);font-size:10px;letter-spacing:1.4px;text-transform:uppercase}.market-table-heading h2{margin:0;font-size:27px;font-weight:500;letter-spacing:-.8px;line-height:1.08}.market-feed-note{display:flex;align-items:center;gap:7px;margin:0 0 3px;color:var(--muted,#4d5f56);font-size:11px}.feed-dot{display:block;width:6px;height:6px;border:1px solid #7b8c84;border-radius:50%;background:transparent}
.on-chain-stats{padding:18px 20px 20px;border:1px solid var(--line,rgba(15,31,24,.12));border-radius:15px;background:rgba(255,255,255,.34)}.stats-heading{display:flex;justify-content:space-between;align-items:center;gap:18px;margin-bottom:14px;color:var(--fg,#0f1f18);font-size:12px;font-weight:550}.stats-note{color:var(--muted,#4d5f56);font-size:10px;font-weight:400}.stats-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px}.stat-card{min-height:80px;padding:14px 14px 12px;border:1px solid var(--line,rgba(15,31,24,.1));border-radius:11px;background:rgba(240,235,229,.57)}.stat-card-top{display:flex;align-items:flex-start;justify-content:space-between;gap:7px;color:var(--muted,#4d5f56);font-size:10px;line-height:1.3}.preview-badge{flex:none;padding:3px 6px;border:1px solid rgba(0,104,56,.22);border-radius:100px;color:var(--green,#006838);font-size:8px;letter-spacing:.4px;text-transform:uppercase}.stat-value{display:block;margin:9px 0 2px;font-family:var(--mono,monospace);font-size:21px;font-weight:400;line-height:1;color:var(--fg,#0f1f18)}.stat-card small{color:var(--muted,#4d5f56);font-size:9px}
.market-table-toolbar{display:flex;justify-content:space-between;gap:20px;align-items:baseline;margin:27px 0 12px}.table-intro,.search-state{margin:0;color:var(--muted,#4d5f56);font-size:10px}.search-state{font-family:var(--mono,monospace);text-align:right}.table-scroll{overflow-x:auto;border-top:1px solid var(--line,rgba(15,31,24,.12));border-bottom:1px solid var(--line,rgba(15,31,24,.12))}.market-table{width:100%;min-width:730px;border-collapse:collapse;font-size:12px}.market-table th,.market-table td{padding:14px 12px;border-bottom:1px solid var(--line,rgba(15,31,24,.1));text-align:right;vertical-align:middle}.market-table th{color:var(--muted,#4d5f56);font-size:10px;font-weight:450;letter-spacing:.3px;white-space:nowrap}.market-table th:first-child,.market-table td:first-child{text-align:left;padding-left:5px}.market-table tbody tr:last-child td{border-bottom:0}.market-table tbody tr:hover{background:rgba(255,255,255,.32)}.market-table th.is-emphasized{color:var(--fg,#0f1f18)}.market-table td.is-emphasized{background:rgba(0,104,56,.045)}
.asset-link{display:flex;align-items:center;gap:10px;width:max-content;max-width:100%;color:inherit;text-decoration:none}.asset-link:focus-visible{outline:2px solid var(--green,#006838);outline-offset:4px;border-radius:4px}.token-circle{display:grid;place-items:center;flex:none;width:29px;height:29px;border:1px solid rgba(0,104,56,.24);border-radius:50%;background:rgba(0,104,56,.09);color:var(--green,#006838);font-family:var(--mono,monospace);font-size:11px}.asset-copy{display:flex;flex-direction:column;min-width:0;line-height:1.25}.asset-copy b{font-family:var(--mono,monospace);font-size:12px;font-weight:500}.asset-copy small{overflow:hidden;color:var(--muted,#4d5f56);font-size:9px;text-overflow:ellipsis;white-space:nowrap}.cap-value{font-family:var(--mono,monospace);font-size:11px;color:var(--green,#006838)}.model-value{display:block;font-family:var(--mono,monospace);font-size:12px;line-height:1.25}.income-value{color:var(--green,#006838)}.upside-value{color:#829000}.quote-label{display:block;margin-top:3px;color:var(--muted,#4d5f56);font-size:8px;text-transform:uppercase;letter-spacing:.6px}.epoch-value{color:var(--muted,#4d5f56);font-family:var(--mono,monospace);font-size:10px}.status-badge{display:inline-flex;align-items:center;gap:5px;color:var(--muted,#4d5f56);font-size:10px}.status-badge i{display:block;width:5px;height:5px;border:1px solid var(--green,#006838);border-radius:50%;background:rgba(0,104,56,.12)}
.empty-market-state{display:flex;align-items:center;justify-content:space-between;gap:15px;padding:26px 12px;border-top:1px solid var(--line,rgba(15,31,24,.12));border-bottom:1px solid var(--line,rgba(15,31,24,.12));color:var(--muted,#4d5f56);font-size:12px}.empty-market-state p{margin:0}.empty-market-state button{padding:8px 12px;border:1px solid var(--line,rgba(15,31,24,.2));border-radius:100px;background:transparent;color:var(--fg,#0f1f18);font:inherit;font-size:11px;cursor:pointer}.empty-market-state button:hover{background:rgba(255,255,255,.4)}.empty-market-state button:focus-visible{outline:2px solid var(--green,#006838);outline-offset:3px}.market-table-footnote{display:flex;justify-content:space-between;gap:20px;margin-top:12px;color:var(--muted,#4d5f56);font-size:9px;line-height:1.5}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
@media(max-width:780px){.market-table-heading{align-items:flex-start;flex-direction:column;gap:12px}.market-feed-note{margin:0}.stats-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.market-table-toolbar{align-items:flex-start;flex-direction:column;gap:6px}.search-state{text-align:left}.market-table-footnote{flex-direction:column;gap:4px}}
@media(max-width:430px){.on-chain-stats{padding:14px}.stats-heading{align-items:flex-start;flex-direction:column;gap:5px}.stats-grid{gap:7px}.stat-card{padding:11px 10px;min-height:72px}.stat-card-top{font-size:9px}.preview-badge{font-size:7px}.stat-value{font-size:18px}.market-table-heading h2{font-size:25px}}
</style>
