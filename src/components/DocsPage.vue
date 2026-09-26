<script setup>
import { computed } from 'vue'
import { ArrowRight, ExternalLink } from 'lucide-vue-next'
import { concepts } from '../concepts.js'

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
  ['documents', 'Documents'],
  ['terms', 'Terms'],
  ['privacy', 'Privacy'],
]

const steps = [
  ['01', 'Deposit a Stock Token', 'Into a series: one Stock Token, one epoch, one cap. The vault holds it.'],
  ['02', 'Split into Income + Upside', 'One Income position and one Upside position per unit, as two ERC-20s.'],
  ['03', 'Auction Upside', "Subscribers' Upside is sold in a descending-clock auction; the proceeds are their premium."],
  ['04', 'Review the epoch', 'Both positions are shown as model examples. This preview does not run a venue or route a trade.'],
  ['05', 'Settle or recompose', 'At settlement Upside takes the amount above K, Income the rest. Or merge Income + Upside back, any time, free.'],
]

const conceptLinks = computed(() => concepts.map((concept) => ({ ...concept, anchor: `concept-${concept.id}` })))
const legalPage = computed(() => ['/risk', '/terms', '/privacy'].includes(props.path))
const legalTitle = computed(() => ({ '/risk': 'Risk notice.', '/terms': 'Terms of this demo.', '/privacy': 'Privacy notice.' }[props.path] || ''))
const legalBody = computed(() => ({
  '/risk': [
    'This local interface is an educational scenario lab. It does not create, sell, or settle a financial product.',
    'Income positions retain downside exposure to the underlying Stock Token. Upside can expire without a payoff and its maximum loss is the premium paid. Verify the underlying, oracle, liquidity, and legal status independently before relying on any model output.',
  ],
  '/terms': [
    'This website is a local product demonstration. Buttons, prices, markets, wallets, and contract references are illustrative unless a connected production integration says otherwise.',
    'Use of this demo does not create an account, custody relationship, order, or agreement with Scenovia. Contract references and the scenario lab are read-only in this build.',
  ],
  '/privacy': [
    'The demo keeps interface state in your browser. It does not require a wallet connection to read the pages and does not send a trade order from this interface.',
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
        <a class="text-link" href="/" @click.prevent="go('/')">Back to home <ArrowRight :size="14" /></a>
      </div>
    </div>
  </section>

  <section v-else class="docs-page">
    <div class="container docs-hero">
      <p class="docs-kicker">Docs</p>
      <h1 tabindex="-1">How Scenovia works.</h1>
      <p class="docs-lead">Deposit a Stock Token into a series. Receive one Income position and one Upside position per unit. At settlement, Upside pays the amount of one unit's value above the cap price K, in Stock Tokens; its maximum loss is the price paid for it. Income keeps everything up to K plus whatever the auction paid for Upside. Income is not protected: if the Stock Token falls, Income falls with it. One Income position plus one Upside position of the same series merge back into one Stock Token at any time, free.</p>
      <p class="demo-note">Solana Chain interface preview. The scenario lab and contract references are read-only; this build has no trade execution or live oracle integration.</p>
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
            <article><p class="role-label income">Income</p><h3>Keeps the Stock Token up to K.</h3><p>Income receives the auction proceeds. It is not protected: if the Stock Token falls, Income falls with it.</p></article>
            <article><p class="role-label upside">Upside</p><h3>Receives value above K.</h3><p>Upside is prefunded by the Stock Tokens in the vault. No borrowing, funding rate, or liquidation engine. Maximum loss is the price paid.</p></article>
          </div>
        </section>

        <section id="concepts" class="docs-section">
          <div class="section-heading"><div><p class="section-label">Concepts</p><h2>One card per concept.</h2><p>Each card links to a related detail below or in the local app.</p></div></div>
          <ul class="concept-grid">
            <li v-for="(concept, index) in conceptLinks" :id="concept.anchor" :key="concept.id" class="concept-card">
              <img :src="concept.image" :alt="concept.title" width="1600" height="900" loading="lazy" />
              <div class="concept-card-copy"><p class="concept-index">{{ String(index + 1).padStart(2, '0') }}</p><h3>{{ concept.title }}</h3><p>{{ concept.description }}</p><a :href="`#${concept.anchor}`">Permalink <ArrowRight :size="12" /></a></div>
            </li>
          </ul>
        </section>

        <section id="settlement" class="docs-section split-section">
          <div><p class="section-label">Settlement</p><h2>A defined cap sets the split.</h2><p>For a starting price P0 and a cap rate, K = P0 × (1 + cap). At settlement, Upside receives max(0, oracle price − K), while Income receives the value up to K and the auction premium.</p></div>
          <div class="formula-card"><p class="formula-label">Illustrative scenario</p><strong>P0 $250 · K $262.50</strong><dl><div><dt>Oracle $200</dt><dd>Upside $0</dd></div><div><dt>Oracle $250</dt><dd>Upside $0</dd></div><div><dt>Oracle $300</dt><dd>Upside $37.50</dd></div></dl></div>
        </section>

        <section id="oracle" class="docs-section prose-section"><p class="section-label">Oracle</p><h2>Settlement starts with a price.</h2><p>A production series would use a defined oracle method, market session, and settlement window. The reference design uses a 30-minute average of the Chainlink feed inside the regular session. This interface displays the rule as documentation only.</p></section>
        <section id="fees" class="docs-section prose-section"><p class="section-label">Fees</p><h2>Activity first. Revenue follows.</h2><p>The reference model has one fee: 5% of gross auction proceeds, in USDG. Split, merge, and settlement claims are free. No live fee is charged by this demo.</p></section>
        <section id="listing" class="docs-section prose-section"><p class="section-label">Listing</p><h2>Familiar assets, defined exposure.</h2><p>A candidate Stock Token needs an oracle feed and a USDG liquidity path. Listing rules, custody, jurisdiction, and permissions must be verified before a production launch.</p></section>
        <section id="risks" class="docs-section prose-section"><p class="section-label">Risks</p><h2>Premium is income, not a shield.</h2><p>Income still bears downside in the Stock Token. Upside may lose the premium paid. Oracle, liquidity, smart contract, counterparty, market, and regulatory risks remain outside this interface.</p></section>
        <section id="token" class="docs-section prose-section"><p class="section-label">Token</p><h2>Positions are distinct from SCNV.</h2><p>Income and Upside are positions created from market units. The proposed SCNV symbol is separate from those positions and has not been issued. Any supply, utility, or launch statement shown here is a product concept, not a promise of production availability.</p></section>
        <section id="documents" class="docs-section prose-section"><p class="section-label">Documents</p><h2>Read the model with the interface.</h2><p>Use the concept cards, payoff explorer, and local scenario lab together. External protocol documentation is linked only where it is public and relevant.</p><a class="text-link" href="/signal" @click.prevent="go('/signal')">Open local scenario lab <ArrowRight :size="14" /></a></section>
        <section id="terms" class="docs-section prose-section"><p class="section-label">Terms</p><h2>Terms for this local preview.</h2><p>This page is a readable product notice for the interface. It does not replace production terms or create a contractual relationship.</p><a class="text-link" href="/terms" @click.prevent="go('/terms')">Read the demo terms <ExternalLink :size="13" /></a></section>
        <section id="privacy" class="docs-section prose-section"><p class="section-label">Privacy</p><h2>Your browser holds the demo state.</h2><p>No trade order or private key is requested by this documentation view. External links have their own privacy practices.</p><a class="text-link" href="/privacy" @click.prevent="go('/privacy')">Read the demo privacy notice <ExternalLink :size="13" /></a></section>

        <section id="overview" class="legacy-anchor" aria-label="Legacy overview anchor"></section>
        <section id="scenario" class="legacy-anchor" aria-label="Legacy scenario anchor"></section>
        <section id="journal" class="legacy-anchor" aria-label="Legacy journal anchor"></section>
        <section id="limits" class="legacy-anchor" aria-label="Legacy limits anchor"></section>
      </div>
    </div>
  </section>
</template>

<style scoped>
.docs-page { background: var(--bg); color: var(--fg); }
.docs-hero { padding: 82px 0 58px; max-width: 930px; }
.docs-kicker, .section-label, .toc-label, .concept-index, .role-label, .formula-label { margin: 0; color: var(--muted); font-size: 10px; font-weight: 600; letter-spacing: .14em; line-height: 1.45; text-transform: uppercase; }
.docs-hero h1 { margin: 12px 0 22px; font-size: clamp(44px, 6vw, 70px); font-weight: 600; letter-spacing: -.055em; line-height: 1; }
.docs-lead { max-width: 790px; margin: 0; color: var(--muted); font-size: 16px; line-height: 1.72; }
.demo-note { margin: 20px 0 0; color: var(--green); font-family: var(--mono); font-size: 11px; }
.docs-layout { display: grid; grid-template-columns: 170px minmax(0, 1fr); align-items: start; gap: 64px; padding-bottom: 100px; }
.docs-toc { position: sticky; top: 92px; display: flex; flex-direction: column; gap: 10px; padding: 16px 0; border-top: 1px solid var(--line); }
.docs-toc a { color: var(--muted); font-size: 12px; text-decoration: none; }
.docs-toc a:hover { color: var(--green); }
.docs-content { min-width: 0; }
.docs-section { scroll-margin-top: 92px; padding: 68px 0; border-top: 1px solid var(--line); }
.docs-section h2 { margin: 8px 0 14px; font-size: clamp(25px, 3vw, 38px); font-weight: 600; letter-spacing: -.04em; line-height: 1.08; }
.docs-section p { color: var(--muted); font-size: 14px; line-height: 1.7; }
.mechanism-list { display: grid; gap: 0; margin: 26px 0 0; padding: 0; list-style: none; }
.mechanism-list li { display: grid; grid-template-columns: 44px minmax(0, 1fr); gap: 18px; padding: 20px 0; border-top: 1px solid var(--line); }
.step-number { color: var(--green); font-family: var(--mono); font-size: 11px; padding-top: 4px; }
.mechanism-list h2 { margin: 0 0 5px; font-size: 18px; letter-spacing: -.02em; }
.mechanism-list p { margin: 0; max-width: 600px; font-size: 13px; }
.role-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin-top: 30px; }
.role-grid article, .formula-card { padding: 20px; border: 1px solid var(--line); border-radius: 10px; background: var(--raised); }
.role-grid h3 { margin: 8px 0; font-size: 17px; font-weight: 600; }
.role-grid p:last-child { margin: 0; font-size: 12px; }
.role-label.income { color: var(--green); }
.role-label.upside { color: #8e9d00; }
.section-heading { margin-bottom: 28px; }
.section-heading p:last-child { margin: 0; }
.concept-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 28px 18px; margin: 0; padding: 0; list-style: none; }
.concept-card { scroll-margin-top: 92px; min-width: 0; }
.concept-card img { width: 100%; aspect-ratio: 16 / 9; object-fit: cover; border: 1px solid var(--line); border-radius: 9px; }
.concept-card-copy { position: relative; padding: 14px 2px 0 30px; }
.concept-index { position: absolute; top: 17px; left: 0; font-family: var(--mono); font-size: 9px; }
.concept-card h3 { margin: 0 0 6px; font-size: 15px; font-weight: 600; }
.concept-card p { margin: 0; font-size: 12px; line-height: 1.6; }
.concept-card a { display: inline-flex; align-items: center; gap: 5px; margin-top: 9px; color: var(--green); font-size: 11px; text-decoration: none; }
.split-section { display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(250px, .8fr); align-items: center; gap: 46px; }
.split-section > div > p { max-width: 590px; }
.formula-card strong { display: block; margin: 12px 0 19px; font-family: var(--mono); font-size: 16px; font-weight: 500; }
.formula-card dl { display: grid; gap: 8px; margin: 0; }
.formula-card dl div { display: flex; justify-content: space-between; gap: 10px; padding-top: 8px; border-top: 1px solid var(--line); font-family: var(--mono); font-size: 11px; }
.formula-card dt { color: var(--muted); }
.formula-card dd { margin: 0; color: var(--green); }
.prose-section { max-width: 760px; }
.prose-section .text-link { margin-top: 8px; }
.legacy-anchor { height: 1px; padding: 0; border: 0; scroll-margin-top: 92px; }
.legal-hero { padding-bottom: 32px; }
.legal-copy { max-width: 760px; padding-bottom: 120px; }
.legal-copy p { margin: 0 0 20px; color: var(--muted); font-size: 15px; line-height: 1.8; }
.legal-actions { display: flex; align-items: center; gap: 18px; margin-top: 34px; }
.text-link { display: inline-flex; align-items: center; gap: 6px; color: var(--green); font-size: 12px; text-decoration: none; }
.text-link:hover { color: var(--forest); }
@media (max-width: 800px) {
  .docs-hero { padding: 58px 0 40px; }
  .docs-layout { display: block; }
  .docs-toc { position: static; display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px 14px; margin-bottom: 18px; }
  .toc-label { grid-column: 1 / -1; }
  .docs-section { padding: 48px 0; }
  .concept-grid { grid-template-columns: 1fr; }
  .split-section, .role-grid { grid-template-columns: 1fr; gap: 20px; }
}
@media (max-width: 480px) {
  .docs-hero h1 { font-size: 44px; }
  .docs-lead { font-size: 14px; }
  .docs-toc { grid-template-columns: repeat(2, 1fr); }
  .legal-actions { align-items: flex-start; flex-direction: column; }
}
</style>
