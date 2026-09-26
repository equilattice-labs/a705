<script setup>
import { computed, ref } from 'vue'
import { ArrowUpRight, ArrowRight, Search, SlidersHorizontal, ChevronDown, ShieldCheck, ChevronRight, ArrowDownUp, Info } from 'lucide-vue-next'
import PayoffExplorer from './PayoffExplorer.vue'
import MarketTable from './MarketTable.vue'
import { calculatePayoff } from '../payoff.js'

const emit = defineEmits(['navigate'])
const query = ref('')
const side = ref('All')
const quoteSide = ref('Income')
const units = ref(1)
const selected = ref('AAPL')
const cap = ref(5)
const assets = [{ symbol: 'AAPL', name: 'Apple', spot: 250 }, { symbol: 'NVDA', name: 'NVIDIA', spot: 130 }, { symbol: 'MSFT', name: 'Microsoft', spot: 430 }, { symbol: 'TSLA', name: 'Tesla', spot: 350 }]
const asset = computed(() => assets.find(item => item.symbol === selected.value) || assets[0])
const model = computed(() => calculatePayoff({ spot: asset.value.spot, capPercent: cap.value, settlementPrice: asset.value.spot }))
const price = computed(() => quoteSide.value === 'Income' ? model.value.incomePrice : model.value.upsidePrice)
const amount = computed(() => Number.isFinite(Number(units.value)) && Number(units.value) > 0 ? Number(units.value) : 0)
const money = value => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(value)
const showFilters = ref(false)
function resetSearch() { query.value = ''; side.value = 'All' }
function explore() { document.getElementById('cap')?.scrollIntoView({ behavior: 'smooth', block: 'start' }) }
</script>

<template>
  <div class="market-desk container">
    <div class="desk-heading"><div><p class="desk-overline"><span></span> ROBINHOOD CHAIN</p><h1 tabindex="-1">Your market. <span>Your move.</span></h1><p>Explore tokenized markets. Know your exposure.</p></div><a class="desk-guide" href="/docs" @click.prevent="emit('navigate','/docs')">How it works <ArrowUpRight :size="14" /></a></div>
    <div class="desk-navigation"><nav aria-label="Market sections"><a class="active" href="/" aria-current="page" @click.prevent>Overview</a><a href="/app/markets" @click.prevent="emit('navigate','/app/markets')">All markets</a><a href="/app/auctions" @click.prevent="emit('navigate','/app/auctions')">Auctions</a><a href="/signal" @click.prevent="emit('navigate','/signal')">My journal</a></nav><span class="desk-network"><i></i> Preview environment</span></div>
    <div class="market-ticker" aria-label="Illustrative stock token prices">
      <button v-for="(item,index) in assets" :key="item.symbol" type="button" :class="{ selected: selected === item.symbol }" @click="selected = item.symbol"><span class="ticker-asset"><i :class="`asset-${index}`">{{ item.symbol.charAt(0) }}</i><span><b>{{ item.symbol }}</b><small>{{ item.name }}</small></span></span><span class="ticker-price"><strong>{{ money(item.spot) }}</strong><small>MODEL QUOTE</small></span><svg viewBox="0 0 90 28" aria-hidden="true"><path :d="index % 2 ? 'M1 22 13 18 24 20 35 9 45 13 56 11 68 6 79 9 89 2' : 'M1 22 12 18 25 22 35 16 47 18 58 9 68 13 79 7 89 9'" /></svg></button>
    </div>
    <div class="desk-layout">
      <section class="desk-market-panel" aria-labelledby="desk-market-title">
        <div class="panel-heading"><div><h2 id="desk-market-title">Market board <span>04</span></h2><p>Find your next position</p></div><span class="model-label"><i></i> Illustrative quotes</span></div>
        <div class="desk-filters"><div class="side-tabs" aria-label="Position type"><button v-for="option in ['All','Income','Upside']" :key="option" type="button" :aria-pressed="side === option" :class="{ active: side === option }" @click="side = option">{{ option === 'All' ? 'All positions' : option }}</button></div><label class="desk-search"><Search :size="15" /><input v-model="query" placeholder="Search markets" aria-label="Search markets" /></label><button class="desk-filter-toggle" type="button" :aria-expanded="showFilters" aria-controls="filter-details" aria-label="Show market information" @click="showFilters = !showFilters"><SlidersHorizontal :size="16" /></button></div>
        <p v-if="showFilters" id="filter-details" class="filter-details"><Info :size="14" /> All example series use a +5% cap, 30-day epoch and 25% model volatility.</p>
        <MarketTable compact :query="query" :side="side" @reset="resetSearch" @navigate="to => emit('navigate',to)" />
        <a class="all-markets-link" href="/app/markets" @click.prevent="emit('navigate','/app/markets')">Open full market workspace <ArrowRight :size="14" /></a>
      </section>
      <aside class="quote-ticket" aria-labelledby="quote-title">
        <div class="ticket-heading"><h2 id="quote-title">Quick estimate</h2><span>MODEL</span></div>
        <div class="ticket-side" aria-label="Estimate position"><button v-for="option in ['Income','Upside']" :key="option" type="button" :aria-pressed="quoteSide === option" :class="{ active: quoteSide === option, upside: option === 'Upside' }" @click="quoteSide = option">{{ option }} <ArrowUpRight :size="13" /></button></div>
        <label class="ticket-label" for="quote-asset">Underlying</label><div class="ticket-select"><span class="ticket-token">{{ selected.charAt(0) }}</span><select id="quote-asset" v-model="selected"><option v-for="item in assets" :key="item.symbol" :value="item.symbol">{{ item.symbol }} / USD</option></select><ChevronDown :size="14" /></div>
        <div class="ticket-amount"><label for="quote-units">Position units</label><div><input id="quote-units" v-model.number="units" inputmode="decimal" type="number" min="0.01" max="1000000" step="0.01" /><span>{{ selected }}</span></div></div>
        <div class="ticket-cap"><label for="quote-cap">Upside cap <output>+{{ cap }}%</output></label><input id="quote-cap" v-model.number="cap" type="range" min="0" max="10" step="1" /><div><span>0%</span><span>10%</span></div></div>
        <dl class="ticket-breakdown"><div><dt>Cap price</dt><dd>{{ money(model.strike) }}</dd></div><div><dt>Epoch</dt><dd>30 days</dd></div><div><dt>Price / unit</dt><dd>{{ money(price) }}</dd></div></dl>
        <div class="ticket-total"><span>Estimated value</span><strong>{{ money(price * amount) }}</strong></div><button class="ticket-submit" type="button" :disabled="!amount" @click="explore">Explore payoff <ArrowRight :size="16" /></button><p class="ticket-note"><ShieldCheck :size="13" /> Local model only. No order is placed.</p>
      </aside>
    </div>
    <div class="desk-bottom"><div><span class="desk-icon"><ArrowDownUp :size="19" /></span><div><strong>One asset. Two positions.</strong><p>Income keeps value up to the cap. Upside receives the move above it.</p></div><a href="#cap" @click.prevent="explore">Try the model <ChevronRight :size="14" /></a></div><div><span class="desk-icon coral"><ShieldCheck :size="19" /></span><div><strong>Your assumptions, on record.</strong><p>Build a scenario and save the reasoning in your local journal.</p></div><a href="/signal" @click.prevent="emit('navigate','/signal')">Open journal <ChevronRight :size="14" /></a></div></div>
    <p class="desk-disclaimer"><Info :size="13" /> All market prices are examples. Quotes are not live and this preview does not execute transactions.</p>
  </div>
  <div class="desk-payoff"><PayoffExplorer /></div>
  <section id="how-it-works" class="desk-learn container"><div><p class="eyebrow">POSITION FLOW</p><h2>A clear path from asset to exposure.</h2></div><ol><li><span>01</span><strong>Deposit</strong><p>A Stock Token backs the series.</p></li><li><span>02</span><strong>Split</strong><p>Receive Income and Upside positions.</p></li><li><span>03</span><strong>Settle or merge</strong><p>Follow the cap, or recompose one unit.</p></li></ol><a href="/docs#mechanism" @click.prevent="emit('navigate','/docs#mechanism')">Read the full mechanism <ArrowUpRight :size="14" /></a></section>
</template>
