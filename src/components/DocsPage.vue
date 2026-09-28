<script setup>
import { computed } from 'vue'
import { ArrowRight, ExternalLink } from 'lucide-vue-next'
import { concepts } from '../concepts.js'
import { brand } from '../brand.js'

const props = defineProps({
  path: { type: String, default: '/docs' },
})
const emit = defineEmits(['navigate'])

const sections = [
  ['mechanism', 'Mechanism'],
  ['concepts', 'Concepts'],
  ['settlement', 'Settlement'],
  ['oracle', 'Oracle'],
  ['fees', 'Fees'],
  ['listing', 'Listing'],
  ['risks', 'Risks'],
  ['token', 'Token'],
  ['documents', 'Journal'],
  ['terms', 'Terms'],
  ['privacy', 'Privacy'],
]

const steps = [
  ['01', 'Choose a market unit', 'Select an SPL asset from the watchlist. Prices in this build are illustrative examples.'],
  ['02', 'Set a cap', 'The model pairs an Income position with an Upside position around cap price K.'],
  ['03', 'Price the scenario', 'Auction and premium mechanics are part of the reference design; no auction runs here.'],
  ['04', 'Review settlement', 'Change the assumed settlement price to see how the modeled value splits at K.'],
  ['05', 'Recompose the pair', 'The design describes matching positions recombining into one market unit. This action is not implemented.'],
]

const legalPage = computed(() => ['/risk', '/terms', '/privacy'].includes(props.path))
const legalTitle = computed(() => ({ '/risk': 'Risk notice.', '/terms': 'Terms of this demo.', '/privacy': 'Privacy notice.' }[props.path] || ''))
const legalBody = computed(() => ({
  '/risk': [
    'This local interface is an educational scenario lab. It does not create, sell, or settle a financial product.',
    'Income positions retain downside exposure to the underlying SPL market unit. Upside can expire without a payoff and its maximum modeled loss is the premium paid. Verify the underlying, oracle, liquidity, and legal status independently before relying on any model output.',
  ],
  '/terms': [
    'This website is a local product demonstration. Prices, markets, wallets, and contract references are illustrative unless a connected production integration says otherwise.',
    `Use of this demo does not create an account, custody relationship, order, or agreement with ${brand.name}. Contract references and the scenario lab are read-only in this build.`,
  ],
  '/privacy': [
    'The demo keeps journal state in your browser. You can read the pages without connecting a wallet, and this interface does not send a trade order.',
    'External links, such as the chart provider or X, are governed by their own policies. Do not enter secrets, seed phrases, or private keys into this local demo.',
  ],
}[props.path] || []))

function go(to) { emit('navigate', to) }
</script>

<template>
  <section v-if="legalPage" class="docs-page legal-page">
    <div class="container docs-hero legal-hero">
      <p class="docs-kicker">Local interface preview</p>
      <h1 tabindex="-1">{{ legalTitle }}</h1>
      <p class="docs-lead">This page describes how this local product demonstration should be read. It is not a production protocol policy, legal agreement, or investment recommendation.</p>
    </div>
    <div class="container legal-copy">
      <p v-for="paragraph in legalBody" :key="paragraph">{{ paragraph }}</p>
      <div class="legal-actions">
        <a class="button primary" href="/docs" @click.prevent="go('/docs')">Read how it works <ArrowRight :size="15" /></a>
        <a class="text-link" href="/" @click.prevent="go('/')">Back to markets <ArrowRight :size="14" /></a>
      </div>
    </div>
  </section>

  <section v-else class="docs-page">
    <div class="container docs-hero">
      <p class="docs-kicker">{{ brand.network }} / Model notes</p>
      <h1 tabindex="-1">How {{ brand.name }} works.</h1>
      <p class="docs-lead">This preview models an illustrative split around a cap price. It does not custody SPL assets, run an auction, connect an oracle, or settle transactions.</p>
      <p class="demo-note">All displayed market values are examples. No token or Solana program has been issued by this preview.</p>
    </div>

    <div class="container docs-layout">
      <nav class="docs-toc" aria-label="On this page">
        <p class="toc-label">On this page</p>
        <a v-for="[id, label] in sections" :key="id" :href="`#${id}`">{{ label }}</a>
      </nav>

      <div class="docs-content">
        <section id="mechanism" class="docs-section">
          <p class="section-label">Mechanism</p>
          <ol class="mechanism-list">
            <li v-for="[number, title, body] in steps" :key="number">
              <span class="step-number">{{ number }}</span>
              <div><h2>{{ title }}</h2><p>{{ body }}</p></div>
            </li>
          </ol>
          <div class="role-grid">
            <article><p class="role-label income">Income</p><h3>Value up to K, plus any premium.</h3><p>Income still bears the underlying asset's downside. A premium does not protect the market unit from a price decline.</p></article>
            <article><p class="role-label upside">Upside</p><h3>Value above K.</h3><p>The modeled payoff is max(0, settlement price - K). A buyer's maximum modeled loss is the hypothetical premium paid.</p></article>
          </div>
        </section>

        <section id="concepts" class="docs-section">
          <div class="section-heading">
            <p class="section-label">Concepts</p>
            <h2>Three parts of the model.</h2>
            <p>These illustrations describe a product concept, not deployed Solana programs.</p>
          </div>
          <ul class="concept-grid">
            <li v-for="(concept, index) in concepts" :id="`concept-${concept.id}`" :key="concept.id" class="concept-card">
              <img :src="concept.image" :alt="concept.title" width="1200" height="675" loading="lazy" />
              <div class="concept-card-copy">
                <p class="concept-index">{{ String(index + 1).padStart(2, '0') }}</p>
                <h3>{{ concept.title }}</h3>
                <p>{{ concept.description }}</p>
              </div>
            </li>
          </ul>
        </section>

        <section id="settlement" class="docs-section split-section">
          <div>
            <p class="section-label">Settlement</p>
            <h2>A defined cap sets the split.</h2>
            <p>For starting price P0 and cap rate c, K = P0 x (1 + c). At assumed settlement price S, Upside receives max(0, S - K). Income receives value up to K plus any hypothetical auction premium.</p>
          </div>
          <div class="formula-card">
            <p class="formula-label">Illustrative scenario</p>
            <strong>P0 $250 / 5% cap / K $262.50</strong>
            <dl><div><dt>Settlement $200</dt><dd>Upside $0</dd></div><div><dt>Settlement $250</dt><dd>Upside $0</dd></div><div><dt>Settlement $300</dt><dd>Upside $37.50</dd></div></dl>
          </div>
        </section>

        <section id="oracle" class="docs-section prose-section"><p class="section-label">Oracle</p><h2>No live price source is connected.</h2><p>A production series would need a named feed, market session, fallback behavior, and settlement window. This preview uses local assumptions and performs no oracle reads.</p></section>
        <section id="fees" class="docs-section prose-section"><p class="section-label">Fees</p><h2>No fee is charged by this demo.</h2><p>A 5% auction fee appeared in an earlier reference model. It is only a design assumption and is not active, binding, or a production term.</p></section>
        <section id="listing" class="docs-section prose-section"><p class="section-label">Listing</p><h2>Assets need a verified market path.</h2><p>A candidate SPL market unit would need a reliable price source and a USDC liquidity path. Listing, custody, jurisdiction, and program permissions require separate review before production.</p></section>
        <section id="risks" class="docs-section prose-section"><p class="section-label">Risks</p><h2>A premium does not remove risk.</h2><p>Income still bears underlying downside. Upside may expire without a payoff. Oracle, liquidity, smart contract, counterparty, market, and regulatory risks remain outside this interface.</p></section>
        <section id="token" class="docs-section prose-section"><p class="section-label">Token</p><h2>The proposed {{ brand.asset }} symbol is separate.</h2><p>Income and Upside describe modeled positions. {{ brand.asset }} is a proposed symbol only; it has not been issued, and no supply or utility is enabled in this preview.</p></section>
        <section id="documents" class="docs-section prose-section"><p class="section-label">Journal</p><h2>Keep assumptions in this browser.</h2><p>The scenario journal stores its record locally and can export it as JSON. It does not submit a transaction or publish the record on chain.</p><a class="text-link" href="/signal" @click.prevent="go('/signal')">Open the journal <ArrowRight :size="14" /></a></section>
        <section id="terms" class="docs-section prose-section"><p class="section-label">Terms</p><h2>Terms for this local preview.</h2><p>This page is a readable product notice for the interface. It does not replace production terms or create a contractual relationship.</p><a class="text-link" href="/terms" @click.prevent="go('/terms')">Read the demo terms <ExternalLink :size="13" /></a></section>
        <section id="privacy" class="docs-section prose-section"><p class="section-label">Privacy</p><h2>Your browser holds the journal state.</h2><p>No trade order or private key is requested by this documentation view. External links have their own privacy practices.</p><a class="text-link" href="/privacy" @click.prevent="go('/privacy')">Read the demo privacy notice <ExternalLink :size="13" /></a></section>

        <section id="overview" class="legacy-anchor" aria-label="Legacy overview anchor"></section>
        <section id="scenario" class="legacy-anchor" aria-label="Legacy scenario anchor"></section>
        <section id="journal" class="legacy-anchor" aria-label="Legacy journal anchor"></section>
        <section id="limits" class="legacy-anchor" aria-label="Legacy limits anchor"></section>
      </div>
    </div>
  </section>
</template>

<style scoped>
.docs-page { color:var(--fg); }
.docs-hero { max-width:900px; padding:30px 0 22px; }
.docs-kicker,.section-label,.toc-label,.concept-index,.role-label,.formula-label { color:var(--accent); font:600 10px/1.4 var(--mono); text-transform:uppercase; }
.docs-hero h1 { margin:8px 0 10px; font-size:30px; line-height:1.15; }
.docs-lead { max-width:790px; color:var(--fg); font-size:14px; line-height:1.65; }
.demo-note { margin-top:10px; color:var(--muted); font:10px/1.5 var(--mono); }
.docs-layout { display:grid; grid-template-columns:150px minmax(0,1fr); gap:30px; padding-bottom:64px; }
.docs-content { min-width:0; }
.docs-toc { position:sticky; top:78px; display:flex; flex-direction:column; gap:6px; padding:12px 0; border-top:1px solid var(--line); }
.docs-toc a { color:var(--muted); font:11px var(--mono); }
.docs-toc a:hover { color:var(--accent); }
.docs-section { scroll-margin-top:92px; padding:34px 0; border-top:1px solid var(--line); }
.docs-section h2 { margin:7px 0 10px; font-size:23px; }
.docs-section p { color:var(--muted); font-size:13px; line-height:1.65; }
.section-heading { margin-bottom:18px; }
.section-heading h2 { margin-bottom:7px; }
.section-heading p:last-child { margin:0; }
.mechanism-list { display:grid; gap:0; margin:26px 0 0; padding:0; list-style:none; }
.mechanism-list li { display:grid; grid-template-columns:36px minmax(0,1fr); gap:14px; padding:15px 0; border-top:1px solid var(--line); }
.step-number { color:var(--accent); font:600 11px var(--mono); }
.mechanism-list h2 { font-size:16px; }
.role-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; margin-top:18px; }
.role-grid article,.formula-card { padding:14px; border:1px solid var(--line); border-radius:5px; background:var(--surface); }
.role-grid h3 { margin:7px 0; font-size:15px; }
.role-label.income,.formula-card dd { color:var(--mint); }
.role-label.upside { color:var(--pink); }
.concept-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin:0; padding:0; list-style:none; }
.concept-card { min-width:0; }
.concept-card img { display:block; width:100%; height:auto; aspect-ratio:16/9; object-fit:cover; border:1px solid var(--line); border-radius:4px; background:var(--panel); }
.concept-card-copy { padding-top:10px; }
.concept-index { margin-bottom:5px; }
.concept-card h3 { margin:0 0 5px; font-size:15px; }
.concept-card p { margin:0; font-size:12px; }
.split-section { display:grid; grid-template-columns:minmax(0,1.2fr) minmax(250px,.8fr); align-items:center; gap:28px; }
.formula-card strong { display:block; margin:12px 0 17px; font:500 13px var(--mono); }
.formula-card dl { display:grid; gap:7px; margin:0; }
.formula-card dl div { display:flex; justify-content:space-between; gap:10px; padding-top:7px; border-top:1px solid var(--line); font:11px var(--mono); }
.formula-card dt { color:var(--muted); }
.formula-card dd { margin:0; }
.prose-section { max-width:760px; }
.prose-section .text-link { margin-top:8px; }
.legal-hero { padding-bottom:16px; }
.legal-copy { max-width:760px; padding-bottom:64px; }
.legal-copy p { margin:0 0 18px; color:var(--muted); font-size:14px; line-height:1.75; }
.legal-actions { display:flex; align-items:center; gap:16px; margin-top:26px; }
.text-link { display:inline-flex; align-items:center; gap:6px; color:var(--accent); font-size:12px; text-decoration:none; }
.text-link:hover { color:var(--fg); }
.legacy-anchor { height:1px; padding:0; border:0; scroll-margin-top:92px; }
.button.primary { background:var(--accent); border-color:var(--accent); color:#171b10; }
.button.primary:hover { filter:brightness(1.06); }
@media(max-width:800px) {
  .docs-hero { padding:25px 0 17px; }
  .docs-layout { display:block; }
  .docs-toc { position:static; display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); margin-bottom:5px; }
  .toc-label { grid-column:1/-1; }
  .docs-section { padding:28px 0; }
  .concept-grid,.split-section,.role-grid { grid-template-columns:1fr; }
}
@media(max-width:480px) {
  .docs-toc { grid-template-columns:repeat(2,minmax(0,1fr)); }
  .docs-lead { font-size:13px; }
  .legal-actions { align-items:flex-start; flex-direction:column; }
}
</style>
