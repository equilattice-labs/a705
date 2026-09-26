<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ArrowUpRight, ArrowRight, Menu, X } from 'lucide-vue-next'
import HomePage from './components/HomePage.vue'
import MarketWorkspace from './components/MarketWorkspace.vue'
import DocsPage from './components/DocsPage.vue'
import ScenarioLab from './components/ScenarioLab.vue'
import { brand } from './brand.js'

const pathname = ref(location.pathname.replace(/\/$/, '') || '/')
const menuOpen = ref(false)
const copied = ref(false)
const copyError = ref('')
const wallet = ref('')
const appPage = computed(() => pathname.value.startsWith('/app/') || pathname.value === '/stats')
const nav = [['Markets', '/app/markets'], ['How It Works', '/#how-it-works'], ['Launchpad', '/app/launchpad'], ['Docs', '/docs']]
const footerLinks = [['Risk', '/risk'], ['Terms', '/terms'], ['Privacy', '/privacy'], ['Docs', '/docs']]
let copyTimer
function scrollToHash() { if (location.hash) document.getElementById(decodeURIComponent(location.hash.slice(1)))?.scrollIntoView({ behavior: 'instant' }) }
async function navigate(to) { menuOpen.value = false; const url = new URL(to, location.origin); history.pushState({}, '', url.pathname + url.hash); pathname.value = url.pathname.replace(/\/$/, '') || '/'; await nextTick(); if (url.hash) scrollToHash(); else { window.scrollTo({ top: 0, behavior: 'instant' }); document.querySelector('main h1')?.focus({ preventScroll: true }) } }
async function popState() { pathname.value = location.pathname.replace(/\/$/, '') || '/'; menuOpen.value = false; await nextTick(); scrollToHash() }
function escapeMenu(e) { if (e.key === 'Escape' && menuOpen.value) { menuOpen.value = false; document.querySelector('.menu-toggle')?.focus() } }
watch(pathname, path => { const title = path === '/' ? 'See the move. Keep the proof.' : path === '/signal' ? 'Local scenario lab' : path === '/docs' ? 'Docs' : path.split('/').pop().replace(/^./, c => c.toUpperCase()); document.title = `${title} · ${brand.name}` }, { immediate: true })
onMounted(() => { addEventListener('popstate', popState); addEventListener('keydown', escapeMenu); nextTick(scrollToHash) })
onBeforeUnmount(() => { removeEventListener('popstate', popState); removeEventListener('keydown', escapeMenu); clearTimeout(copyTimer) })
</script>

<template>
  <a href="#main" class="skip-link">Skip to content</a>
  <header class="site-header">
    <div class="container header-inner">
      <a class="wordmark wordmark-text" href="/" :aria-label="`${brand.name} home`" @click.prevent="navigate('/')"><img src="/icon.svg" alt="" width="26" height="26" /><span>{{ brand.name }}</span></a>
      <nav class="desktop-nav" aria-label="Primary"><a v-for="[label,to] in nav" :key="to" :href="to" :aria-current="pathname === to ? 'page' : undefined" @click.prevent="navigate(to)">{{ label }}</a></nav>
      <div class="header-actions">
        <div v-if="!appPage && pathname !== '/signal'" class="contract-actions"><span class="contract-pill"><span>KVRN</span><span class="mono">CA pending</span></span></div>
        <span v-if="appPage || pathname === '/signal'" class="preview-mode"><i></i> Preview mode</span>
        <template v-else><a href="/app/markets" class="button primary header-launch" @click.prevent="navigate('/app/markets')">Launch App</a><a href="/app/markets" class="circle-button launch-icon" aria-label="Open the app" @click.prevent="navigate('/app/markets')"><ArrowUpRight :size="16" /></a></template>
        <button class="circle-button menu-toggle" :aria-expanded="menuOpen" aria-controls="mobile-navigation" :aria-label="menuOpen ? 'Close navigation' : 'Open navigation'" @click="menuOpen = !menuOpen"><X v-if="menuOpen" :size="18" /><Menu v-else :size="18" /></button>
      </div>
    </div>
    <nav v-if="menuOpen" id="mobile-navigation" class="mobile-navigation container" aria-label="Mobile navigation"><a v-for="[label,to] in nav" :key="to" :href="to" @click.prevent="navigate(to)">{{ label }} <ArrowUpRight :size="16" /></a><a href="/signal" @click.prevent="navigate('/signal')">Local scenario lab <ArrowUpRight :size="16" /></a></nav>
  </header>
  <p v-if="copied" class="sr-only" role="status">Reference contract address copied.</p><p v-if="copyError" class="copy-error" role="alert">{{ copyError }}</p>
  <main id="main">
    <HomePage v-if="pathname === '/'" @navigate="navigate" />
    <MarketWorkspace v-else-if="appPage" :path="pathname" @navigate="navigate" />
    <ScenarioLab v-else-if="pathname === '/signal'" :wallet="wallet" />
    <DocsPage v-else-if="['/docs','/risk','/terms','/privacy'].includes(pathname)" :path="pathname" @navigate="navigate" />
    <section v-else class="container not-found"><p class="eyebrow">404</p><h1 tabindex="-1">A different direction.</h1><p>This page could not be found.</p><a class="button primary" href="/" @click.prevent="navigate('/')">Back home <ArrowRight :size="16" /></a></section>
  </main>
  <footer class="site-footer"><div class="container footer-inner"><div class="footer-brand"><a href="/" class="wordmark wordmark-text" :aria-label="`${brand.name} home`" @click.prevent="navigate('/')"><img src="/icon.svg" width="24" height="24" alt="" /><span>{{ brand.name }}</span></a><span>{{ brand.tagline }}</span></div><div class="footer-right"><span class="network-pill"><i></i> Robinhood Chain · Preview</span><nav aria-label="Site"><a v-for="[label,to] in footerLinks" :key="to" :href="to" @click.prevent="navigate(to)">{{ label }}</a><a href="/signal" @click.prevent="navigate('/signal')">Local lab <ArrowUpRight :size="11" /></a></nav><a class="social-link" href="https://x.com/Kovrane" target="_blank" rel="noreferrer" aria-label="Kovrane on X">𝕏</a></div></div></footer>
</template>
