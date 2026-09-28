<script setup>
import { ArrowRight, ArrowUpRight, Search, SlidersHorizontal } from 'lucide-vue-next'
import { ref, computed } from 'vue'
import MarketTable from './MarketTable.vue'
import { brand } from '../brand.js'
const props = defineProps({ path: { type: String, default: '/app/markets' } })
const emit = defineEmits(['navigate'])
const query = ref('')
const side = ref('All')
const showFilters = ref(false)
const pageTitle = computed(() => props.path.includes('launchpad') ? 'Launchpad' : props.path.includes('auctions') ? 'Auctions' : props.path.includes('recompose') ? 'Recompose positions' : 'Markets')
const copy = computed(() => ({ Markets: 'Scan Solana token series with a defined cap. Prices are illustrative until a market data provider is connected.', Launchpad: 'Propose a Solana token market. This interface records the shape of the request; no listing transaction is enabled.', Auctions: 'Explore Upside auctions. The sample series below explains the settlement model without placing an order.', 'Recompose positions': 'Merge one Income position and one Upside position from the same series back into one Solana token.' }[pageTitle.value]))
</script>

<template>
  <section class="workspace container"><div class="workspace-head"><div><p class="eyebrow">{{ brand.name }} workspace / {{ brand.network }} preview</p><h1 tabindex="-1">{{ pageTitle }}</h1><p class="workspace-lede">{{ copy }}</p></div><a href="/" class="text-link" @click.prevent="emit('navigate','/')">Back to markets <ArrowRight :size="14" /></a></div>
    <div v-if="pageTitle === 'Launchpad'" class="workspace-card launchpad-card"><div><p class="eyebrow">Open listing rules</p><h2>Suggest a market.</h2><p>Any SPL market unit with a verified price feed and USDC liquidity path may qualify. Connect nothing here: this CA preview keeps the request local.</p></div><a href="/docs#listing" class="button primary" @click.prevent="emit('navigate','/docs#listing')">Read listing notes <ArrowUpRight :size="16" /></a></div>
    <div v-else-if="pageTitle === 'Recompose positions'" class="workspace-card recompose-panel"><p class="eyebrow">Income + Upside</p><h2>One asset again.</h2><p>Selecting and merging positions would require a wallet transaction. This local preview keeps wallet actions disabled.</p><button class="button" type="button" disabled>Recompose disabled in preview</button></div>
    <template v-else><div class="stats-strip"><div><span>Value locked</span><strong>—</strong></div><div><span>Premium received (net)</span><strong>—</strong></div><div><span>Epochs settled</span><strong>0</strong></div><div><span>Active series</span><strong>4</strong></div></div><div class="filters"><label class="search-field"><Search :size="15" /><span class="sr-only">Search markets</span><input v-model="query" placeholder="Search asset" /></label><div class="side-tabs"><button v-for="option in ['All','Income','Upside']" :key="option" :aria-pressed="side === option" :class="{active:side===option}" @click="side=option">{{ option }}</button></div><button class="filter-button" type="button" :aria-expanded="showFilters" @click="showFilters = !showFilters"><SlidersHorizontal :size="14" /> Market details</button></div><p v-if="showFilters" class="filter-details">All example series use a +5% cap, 30-day epoch and 25% model volatility.</p><MarketTable :query="query" :side="side" @reset="query = ''" @navigate="to => emit('navigate',to)" /></template>
  </section>
</template>

<style scoped>
.workspace{padding-block:52px 96px}.workspace-head{display:flex;align-items:flex-end;justify-content:space-between;gap:25px;border-bottom:1px solid var(--line);padding-bottom:30px}.workspace-head h1{margin:13px 0 12px;font-family:var(--display);font-size:clamp(38px,4vw,54px);line-height:1;font-weight:600}.workspace-lede{max-width:570px;margin:0;color:var(--muted);font-size:14px;line-height:1.7}.stats-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;margin:24px 0;border:1px solid var(--line);border-radius:8px;overflow:hidden;background:var(--line)}.stats-strip div{display:flex;flex-direction:column;gap:8px;padding:20px;background:var(--surface)}.stats-strip span{font-family:var(--mono);font-size:10px;color:var(--muted)}.stats-strip strong{font:500 24px var(--mono);color:var(--cyan)}.filters{display:flex;align-items:center;gap:10px;margin:24px 0 16px}.search-field{display:flex;align-items:center;gap:8px;flex:1;max-width:320px;height:40px;padding:0 12px;border:1px solid var(--line);border-radius:6px;background:var(--surface);color:var(--muted)}.search-field input{width:100%;border:0;outline:0;background:none;color:var(--fg);font-size:12px}.side-tabs{display:flex;gap:4px}.side-tabs button,.filter-button{height:40px;padding:0 13px;border:1px solid var(--line);border-radius:6px;background:var(--surface);color:var(--muted);font-size:11px;cursor:pointer}.side-tabs button.active,.side-tabs button:hover{background:var(--cyan);border-color:var(--cyan);color:#08120e}.filter-button{display:inline-flex;align-items:center;gap:6px;margin-left:auto}.workspace-card{display:flex;align-items:center;justify-content:space-between;gap:30px;margin-top:34px;padding:32px;border:1px solid var(--line);border-radius:8px;background:var(--surface)}.workspace-card h2{margin:12px 0;font-size:34px}.workspace-card p:not(.eyebrow){max-width:600px;margin:0;color:var(--muted);font-size:14px;line-height:1.7}.workspace-card button{margin-top:22px}.recompose-panel{display:block;max-width:780px}.launchpad-card{min-height:260px}@media(max-width:700px){.workspace{padding-block:38px 70px}.workspace-head{display:block}.workspace-head>.text-link{margin-top:24px}.stats-strip{grid-template-columns:1fr 1fr}.stats-strip strong{font-size:21px}.filters{flex-wrap:wrap}.search-field{max-width:none;flex-basis:100%}.filter-button{margin-left:0}.workspace-card{display:block;padding:24px}.workspace-card .button{margin-top:22px}}

/* Dense market terminal surface. */
.workspace { padding-block: 34px 72px; }
.workspace-head { gap: 20px; padding-bottom: 22px; border-bottom-color: var(--line); }
.workspace-head h1 { margin: 9px 0 8px; font-size: clamp(30px, 4vw, 44px); letter-spacing: -.03em; }
.workspace-head .eyebrow { color: var(--cyan); font-family: var(--mono); font-size: 9px; letter-spacing: .06em; text-transform: uppercase; }
.workspace-lede { max-width: 620px; color: #8ba0b2; font-size: 12px; line-height: 1.6; }
.workspace-head .text-link { color: var(--cyan); font-family: var(--mono); font-size: 10px; text-transform: uppercase; }
.stats-strip { gap: 1px; margin: 16px 0; border-color: var(--line); border-radius: 4px; background: var(--line); }
.stats-strip div { gap: 6px; padding: 14px 15px; background: #0e1521; }
.stats-strip span { color: #7890a4; font-size: 9px; letter-spacing: .03em; text-transform: uppercase; }
.stats-strip strong { color: var(--cyan); font-size: 20px; }
.filters { gap: 7px; margin: 16px 0 12px; }
.search-field { max-width: 300px; height: 36px; padding: 0 10px; border-color: #22394d; border-radius: 3px; background: #090f18; }
.search-field input { font-family: var(--mono); font-size: 10px; }
.side-tabs { gap: 2px; }
.side-tabs button, .filter-button { height: 36px; padding: 0 11px; border-color: #22394d; border-radius: 3px; background: #0e1521; font-family: var(--mono); font-size: 9px; text-transform: uppercase; }
.side-tabs button.active, .side-tabs button:hover { border-color: var(--cyan); background: #123547; color: var(--cyan); }
.filter-button { color: #90a5b6; }
.filter-details { margin: 0 0 12px; padding: 8px 10px; border-left: 2px solid var(--amber); background: #171514; color: #c2a06f; font: 10px var(--mono); }
.workspace-card { gap: 24px; margin-top: 24px; padding: 24px; border-color: var(--line); border-radius: 4px; background: #0e1521; box-shadow: var(--card-shadow); }
.workspace-card .eyebrow { color: var(--amber); font-family: var(--mono); font-size: 9px; text-transform: uppercase; }
.workspace-card h2 { margin: 8px 0; font-size: 26px; }
.workspace-card p:not(.eyebrow) { color: #8ba0b2; font-size: 12px; line-height: 1.6; }
.workspace-card .button { margin-top: 0; }
@media (max-width: 700px) {
  .workspace { padding-block: 26px 60px; }
  .workspace-head h1 { font-size: 30px; }
  .stats-strip div { padding: 12px 11px; }
  .stats-strip strong { font-size: 17px; }
  .workspace-card { padding: 19px; }
}
</style>
