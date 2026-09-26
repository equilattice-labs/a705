<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ArrowRight, ArrowUpRight, BarChart3, BookOpen, Menu, Search, X } from 'lucide-vue-next'
import HomePage from './components/HomePage.vue'
import MarketWorkspace from './components/MarketWorkspace.vue'
import DocsPage from './components/DocsPage.vue'
import ScenarioLab from './components/ScenarioLab.vue'
import { brand } from './brand.js'

const pathname = ref(location.pathname.replace(/\/$/, '') || '/')
const menuOpen = ref(false)
const appPage = computed(() => pathname.value.startsWith('/app/') || pathname.value === '/stats')
const nav = [['Markets', '/'], ['Explore', '/app/markets'], ['Journal', '/signal'], ['Learn', '/docs']]
const footerLinks = [['Markets', '/'], ['Journal', '/signal'], ['Risk', '/risk'], ['Docs', '/docs'], ['Privacy', '/privacy']]

function scrollToHash() {
  if (location.hash) document.getElementById(decodeURIComponent(location.hash.slice(1)))?.scrollIntoView({ behavior: 'instant' })
}

async function navigate(to) {
  menuOpen.value = false
  const url = new URL(to, location.origin)
  history.pushState({}, '', url.pathname + url.hash)
  pathname.value = url.pathname.replace(/\/$/, '') || '/'
  await nextTick()
  if (url.hash) scrollToHash()
  else {
    window.scrollTo({ top: 0, behavior: 'instant' })
    document.querySelector('main h1')?.focus({ preventScroll: true })
  }
}

async function popState() {
  pathname.value = location.pathname.replace(/\/$/, '') || '/'
  menuOpen.value = false
  await nextTick()
  scrollToHash()
}

function escapeMenu(event) {
  if (event.key === 'Escape' && menuOpen.value) {
    menuOpen.value = false
    document.querySelector('.menu-toggle')?.focus()
  }
}

watch(pathname, path => {
  const title = path === '/' ? 'Markets' : path === '/signal' ? 'Your journal' : path === '/docs' ? 'Learn' : path.split('/').pop().replace(/^./, letter => letter.toUpperCase())
  document.title = `${title} · ${brand.name}`
}, { immediate: true })

onMounted(() => {
  addEventListener('popstate', popState)
  addEventListener('keydown', escapeMenu)
  nextTick(scrollToHash)
})

onBeforeUnmount(() => {
  removeEventListener('popstate', popState)
  removeEventListener('keydown', escapeMenu)
})
</script>

<template>
  <a href="#main" class="skip-link">Skip to content</a>
  <header class="site-header">
    <div class="container header-inner">
      <a class="wordmark wordmark-text" href="/" :aria-label="`${brand.name} markets`" @click.prevent="navigate('/')">
        <img src="/icon.svg" alt="" width="30" height="30" />
        <span>{{ brand.name }}</span>
      </a>
      <nav class="desktop-nav" aria-label="Primary">
        <a v-for="[label, to] in nav" :key="to" :href="to" :aria-current="pathname === to ? 'page' : undefined" @click.prevent="navigate(to)">{{ label }}</a>
      </nav>
      <div class="header-actions">
        <span class="network-pill header-network"><i></i>{{ brand.network }} <span>Preview</span></span>
        <span v-if="appPage || pathname === '/signal'" class="preview-mode">Local preview</span>
        <a v-else href="/app/markets" class="button primary header-launch" @click.prevent="navigate('/app/markets')">Browse markets <ArrowUpRight :size="15" /></a>
        <button class="circle-button menu-toggle" :aria-expanded="menuOpen" aria-controls="mobile-navigation" :aria-label="menuOpen ? 'Close navigation' : 'Open navigation'" @click="menuOpen = !menuOpen">
          <X v-if="menuOpen" :size="18" /><Menu v-else :size="18" />
        </button>
      </div>
    </div>
    <nav v-if="menuOpen" id="mobile-navigation" class="mobile-navigation container" aria-label="Mobile navigation">
      <a v-for="[label, to] in nav" :key="to" :href="to" @click.prevent="navigate(to)">{{ label }} <ArrowUpRight :size="16" /></a>
      <a href="/app/launchpad" @click.prevent="navigate('/app/launchpad')">Listing notes <ArrowUpRight :size="16" /></a>
      <a href="/app/auctions" @click.prevent="navigate('/app/auctions')">Auction examples <ArrowUpRight :size="16" /></a>
    </nav>
  </header>

  <main id="main">
    <HomePage v-if="pathname === '/'" @navigate="navigate" />
    <MarketWorkspace v-else-if="appPage" :path="pathname" @navigate="navigate" />
    <ScenarioLab v-else-if="pathname === '/signal'" />
    <DocsPage v-else-if="['/docs', '/risk', '/terms', '/privacy'].includes(pathname)" :path="pathname" @navigate="navigate" />
    <section v-else class="container not-found">
      <p class="eyebrow">404</p><h1 tabindex="-1">This page isn't here.</h1><p>Try the markets list or head back to the overview.</p>
      <a class="button primary" href="/" @click.prevent="navigate('/')">Back to markets <ArrowRight :size="16" /></a>
    </section>
  </main>

  <footer class="site-footer">
    <div class="container footer-inner">
      <div class="footer-brand">
        <a href="/" class="wordmark wordmark-text" :aria-label="`${brand.name} markets`" @click.prevent="navigate('/')"><img src="/icon.svg" width="26" height="26" alt="" /><span>{{ brand.name }}</span></a>
        <span>{{ brand.network }} preview · sample prices · no transactions</span>
      </div>
      <div class="footer-right">
        <nav aria-label="Site links"><a v-for="[label, to] in footerLinks" :key="to" :href="to" @click.prevent="navigate(to)">{{ label }}</a><a href="/app/launchpad" @click.prevent="navigate('/app/launchpad')">Listing notes</a></nav>
      </div>
    </div>
  </footer>

  <nav class="mobile-tabbar" aria-label="App navigation">
    <a href="/" :aria-current="pathname === '/' ? 'page' : undefined" @click.prevent="navigate('/')"><BarChart3 :size="19" /><span>Markets</span></a>
    <a href="/app/markets" :aria-current="pathname.startsWith('/app/') ? 'page' : undefined" @click.prevent="navigate('/app/markets')"><Search :size="19" /><span>Explore</span></a>
    <a href="/signal" :aria-current="pathname === '/signal' ? 'page' : undefined" @click.prevent="navigate('/signal')"><BookOpen :size="19" /><span>Journal</span></a>
  </nav>
</template>
