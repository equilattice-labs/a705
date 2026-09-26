<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { ArrowDownToLine, ArrowUpRight, Check, ChevronRight, FlaskConical, ShieldCheck } from 'lucide-vue-next'
import { storageKeys } from '../brand.js'
import { DEFAULT_BASE_PRICE, MAX_NOTE_LENGTH, calculateScenario, createJournalRecord, restoreJournalRecord, validateScenarioInputs } from '../scenario.js'

defineProps({ wallet: { type: String, default: '' } })

const root = ref(null)
const heading = ref(null)
const amount = ref('1000')
const basePrice = ref(DEFAULT_BASE_PRICE)
const movePct = ref('-15')
const note = ref('')
const step = ref('form')
const record = ref(null)
const errors = ref({})
const feedback = ref('')
const storageNotice = ref('')
const isSaved = ref(false)
const stages = ['Inputs recorded', 'Assumption reviewed', 'Limits reviewed', 'Review complete']
const legacyJournalKeys = ['Kovrane:journal:v1', 'kinovra:journal:v1']
const input = computed(() => ({ amount: amount.value, basePrice: basePrice.value, movePct: movePct.value, note: note.value }))
const result = computed(() => record.value ? calculateScenario(record.value) : null)
const remaining = computed(() => MAX_NOTE_LENGTH - note.value.length)
const currency = (value, digits = 2) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value)
const percent = value => `${Number(value) > 0 ? '+' : ''}${Number(value).toFixed(2)}%`

async function focusHeading() {
  await nextTick()
  heading.value?.focus({ preventScroll: true })
}

function fillInputs(value) {
  amount.value = String(value.amount)
  basePrice.value = String(value.basePrice)
  movePct.value = String(value.movePct)
  note.value = value.note
}

async function review() {
  const validation = validateScenarioInputs(input.value)
  errors.value = validation.errors
  feedback.value = ''
  if (!validation.valid) {
    await nextTick()
    root.value?.querySelector('[aria-invalid="true"]')?.focus()
    return
  }
  record.value = createJournalRecord(validation.value, { id: `SC-${crypto.randomUUID()}`, createdAt: new Date().toISOString() })
  isSaved.value = false
  step.value = 'review'
  await focusHeading()
}

function persist() {
  if (!record.value) return false
  feedback.value = ''
  try {
    localStorage.setItem(storageKeys.journal, JSON.stringify(record.value))
    isSaved.value = true
    storageNotice.value = ''
    feedback.value = 'Saved locally on this device.'
    return true
  } catch {
    isSaved.value = false
    storageNotice.value = 'This record could not be saved to your browser. Export JSON to keep a copy, or retry saving.'
    return false
  }
}

async function save() {
  persist()
  step.value = 'journal'
  await focusHeading()
}

async function edit() {
  if (record.value) fillInputs(record.value)
  errors.value = {}
  feedback.value = ''
  step.value = 'form'
  await focusHeading()
}

async function removeJournal() {
  feedback.value = ''
  try {
    // Remove the older namespace too, so a deleted record cannot reappear on reload.
    legacyJournalKeys.forEach(key => localStorage.removeItem(key))
    localStorage.removeItem(storageKeys.journal)
  } catch {
    storageNotice.value = 'The browser could not delete your saved journal. Your current record is still available; try again or export a copy.'
    return
  }
  record.value = null
  isSaved.value = false
  step.value = 'form'
  amount.value = '1000'
  basePrice.value = DEFAULT_BASE_PRICE
  movePct.value = '-15'
  note.value = ''
  errors.value = {}
  storageNotice.value = ''
  feedback.value = 'Local journal removed.'
  await focusHeading()
}

function changeStage(stage) {
  if (!record.value) return
  record.value = { ...record.value, stage: Math.max(0, Math.min(3, stage)) }
  persist()
}

function downloadJournal() {
  if (!record.value) return
  const data = {
    ...record.value,
    calculations: result.value,
    disclaimer: 'User-entered price and move. Not a quote or forecast. This interface does not enable wallet transactions.',
  }
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }))
  const link = document.createElement('a')
  link.href = url
    link.download = `scenovia-${record.value.id.toLowerCase()}.json`
  link.click()
  URL.revokeObjectURL(url)
  feedback.value = 'Journal export prepared.'
}

onMounted(() => {
  try {
    const activeRaw = localStorage.getItem(storageKeys.journal)
    const legacyKey = legacyJournalKeys.find(key => localStorage.getItem(key))
    const legacyRaw = legacyKey ? localStorage.getItem(legacyKey) : null
    const raw = activeRaw || legacyRaw
    if (!raw) return
    const restored = restoreJournalRecord(JSON.parse(raw))
    if (!restored.valid) {
      storageNotice.value = 'The saved journal has an unsupported format. You can start a new scenario.'
      return
    }
    record.value = restored.value
    fillInputs(restored.value)
    step.value = 'journal'
    isSaved.value = true
    if (restored.migrated || legacyRaw) {
      if (persist()) feedback.value = 'Your earlier record is ready. Its original price is retained as your own assumption.'
    }
  } catch {
    storageNotice.value = 'Saved journal could not be restored. You can still calculate a scenario and export it.'
  }
})

defineExpose({ focusHeading })
</script>

<template>
  <section ref="root" class="scenario-lab" aria-labelledby="scenario-title">
    <header class="sl-header">
      <span class="sl-eyebrow"><FlaskConical :size="15" /> YOUR PRIVATE WORKSPACE</span>
      <h1 id="scenario-title" ref="heading" tabindex="-1">Local scenario lab<span>.</span></h1>
      <p>Put a number behind your next idea. Enter a reference price, explore a hypothetical move, and keep your reasoning close.</p>
    </header>
    <p v-if="storageNotice" class="sl-notice" role="alert">{{ storageNotice }}</p>
    <p v-if="feedback" class="sl-feedback" role="status">{{ feedback }}</p>

    <div v-if="step === 'form'" class="sl-layout">
      <form class="sl-card sl-form" @submit.prevent="review">
        <div class="sl-card-heading"><div><span class="sl-step">01 / INPUTS</span><h2>Set your assumption.</h2></div><span class="sl-badge">LOCAL ONLY</span></div>
        <div class="sl-field-pair">
          <div><label for="amount">Amount <span>SCNV units</span></label><input id="amount" v-model="amount" inputmode="decimal" :aria-invalid="Boolean(errors.amount)" :aria-describedby="errors.amount ? 'amount-error' : undefined" /><p v-if="errors.amount" id="amount-error" class="sl-error">{{ errors.amount }}</p></div>
          <div><label for="base-price">Reference price <span>USD / SCNV</span></label><input id="base-price" v-model="basePrice" inputmode="decimal" :aria-invalid="Boolean(errors.basePrice)" :aria-describedby="errors.basePrice ? 'price-error' : undefined" /><p v-if="errors.basePrice" id="price-error" class="sl-error">{{ errors.basePrice }}</p></div>
        </div>
        <label for="move">Hypothetical move <output>{{ movePct }}%</output></label>
        <input id="move" v-model="movePct" class="sl-range" type="range" min="-90" max="100" step="0.5" />
        <div class="sl-range-scale"><span>-90%</span><span>0</span><span>+100%</span></div>
        <label for="move-text">Exact percentage <span>%</span></label><input id="move-text" v-model="movePct" inputmode="decimal" :aria-invalid="Boolean(errors.movePct)" :aria-describedby="errors.movePct ? 'move-error' : undefined" /><p v-if="errors.movePct" id="move-error" class="sl-error">{{ errors.movePct }}</p>
        <label for="note">Thesis note <span>OPTIONAL</span></label><textarea id="note" v-model="note" :maxlength="MAX_NOTE_LENGTH" :aria-invalid="Boolean(errors.note)" :aria-describedby="errors.note ? 'note-error' : 'note-count'" placeholder="What would make this move plausible?"></textarea><p v-if="errors.note" id="note-error" class="sl-error">{{ errors.note }}</p><p id="note-count" class="sl-char-count">{{ remaining }} characters remaining</p>
        <button class="sl-button sl-primary sl-wide" type="submit">Review scenario <ArrowUpRight :size="17" /></button>
      </form>
      <aside class="sl-card sl-aside"><div class="sl-aside-icon"><ShieldCheck :size="27" /></div><span class="sl-step">A LITTLE SPACE TO THINK</span><h2>Your idea.<br />Your assumptions.</h2><p>This is a private what-if calculator. Reference prices are entered by you; they are not live quotes or execution prices.</p><dl><div><dt>Asset</dt><dd>SCNV / USD</dd></div><div><dt>Network</dt><dd>Robinhood Chain · preview</dd></div><div><dt>Wallet</dt><dd>Not required</dd></div><div><dt>Storage</dt><dd>This browser only</dd></div></dl><p class="sl-aside-foot">Fees, slippage and taxes are excluded. No transaction is created.</p></aside>
    </div>

    <div v-else-if="step === 'review'" class="sl-card sl-review">
      <div class="sl-card-heading"><div><span class="sl-step">02 / REVIEW</span><h2>Check the numbers.</h2></div><ShieldCheck :size="26" /></div><p class="sl-muted">Calculated from your assumptions.</p>
      <dl class="sl-review-rows"><div><dt>Reference amount</dt><dd>{{ Number(record.amount).toLocaleString() }} SCNV</dd></div><div><dt>Reference price</dt><dd>{{ currency(result.basePrice, 4) }}</dd></div><div><dt>Reference value</dt><dd>{{ currency(result.baselineValue, 4) }}</dd></div><div><dt>Scenario move</dt><dd :class="record.movePct >= 0 ? 'sl-positive' : 'sl-negative'">{{ percent(record.movePct) }}</dd></div><div><dt>Scenario value</dt><dd>{{ currency(result.scenarioValue, 4) }}</dd></div></dl>
      <div class="sl-delta"><span>Change in reference value</span><strong :class="result.deltaUsd >= 0 ? 'sl-positive' : 'sl-negative'">{{ result.deltaUsd >= 0 ? '+' : '' }}{{ currency(result.deltaUsd, 4) }}</strong></div>
      <div class="sl-actions"><button class="sl-button sl-primary" @click="save">Save to journal <Check :size="17" /></button><button class="sl-button sl-secondary" @click="edit">Edit inputs</button></div>
    </div>

    <div v-else class="sl-card sl-journal">
      <div class="sl-card-heading"><div><span class="sl-step">03 / JOURNAL</span><h2>Your local record.</h2></div><span class="sl-badge" :class="{ 'sl-unsaved': !isSaved }"><Check v-if="isSaved" :size="13" />{{ isSaved ? 'SAVED' : 'NOT SAVED' }}</span></div>
      <div class="sl-stage-track" aria-label="Journal review stages"><button v-for="(label, i) in stages" :key="label" :class="{ current: record.stage === i, done: record.stage > i }" :aria-current="record.stage === i ? 'step' : undefined" @click="changeStage(i)"><span class="sl-stage-number"><Check v-if="record.stage > i" :size="13" /><template v-else>{{ i + 1 }}</template></span><span>{{ label }}</span><ChevronRight v-if="i < stages.length - 1" class="sl-stage-arrow" :size="14" /></button></div>
      <dl class="sl-summary"><div><dt>Amount</dt><dd>{{ Number(record.amount).toLocaleString() }} SCNV</dd></div><div><dt>Reference price</dt><dd>{{ currency(record.basePrice, 4) }}</dd></div><div><dt>Move</dt><dd :class="record.movePct >= 0 ? 'sl-positive' : 'sl-negative'">{{ percent(record.movePct) }}</dd></div><div><dt>Scenario value</dt><dd>{{ currency(result.scenarioValue, 4) }}</dd></div></dl>
      <blockquote v-if="record.note">{{ record.note }}</blockquote><p class="sl-muted">Created {{ new Date(record.createdAt).toLocaleString() }}. {{ isSaved ? 'Stored only in this browser.' : 'Export a copy to keep this record.' }}</p>
      <div class="sl-actions"><button class="sl-button sl-primary" @click="downloadJournal">Export JSON <ArrowDownToLine :size="16" /></button><button v-if="!isSaved" class="sl-button sl-secondary" @click="persist">Retry saving</button><button class="sl-button sl-secondary" @click="edit">Edit</button><button class="sl-delete" @click="removeJournal">Delete local record</button></div>
    </div>
  </section>
</template>

<style scoped>
.scenario-lab { --sl-ink: #002a18; --sl-green: #006838; --sl-lime: #d5f000; --sl-line: #d8dbcd; color: var(--sl-ink); background: #f0ece4; font: inherit; padding: 58px var(--gutter, 5.55vw) 78px; }
.scenario-lab > * { width: min(1280px, 100%); margin-inline: auto; }
.scenario-lab *, .scenario-lab *::before, .scenario-lab *::after { box-sizing: border-box; }
.sl-header { max-width: 720px; margin-bottom: 34px; }
.sl-eyebrow { display: flex; align-items: center; gap: 7px; color: var(--sl-green); font-size: 10px; font-weight: 700; letter-spacing: .1em; }
.sl-header h1 { font-size: clamp(36px, 4.6vw, 62px); line-height: 1.04; letter-spacing: -.045em; margin: 15px 0 19px; font-weight: 600; outline: none; }
.sl-header h1 span { color: var(--sl-green); }
.sl-header p { max-width: 560px; font-size: 15px; line-height: 1.7; color: #607263; margin: 0; }
.sl-layout { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(260px, .7fr); gap: 22px; }
.sl-card { background: #faf9f5; border: 1px solid var(--sl-line); border-radius: 12px; padding: 30px; min-width: 0; }
.sl-card-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 22px; }
.sl-step { display: block; color: #64816c; font-size: 10px; font-weight: 650; letter-spacing: .08em; }
.sl-card h2 { margin: 9px 0 0; font-size: 25px; letter-spacing: -.035em; line-height: 1.15; font-weight: 600; }
.sl-badge { display: inline-flex; align-items: center; gap: 5px; white-space: nowrap; padding: 6px 9px; border-radius: 5px; background: #e9f0dc; color: var(--sl-green); font-size: 9px; font-weight: 700; letter-spacing: .04em; }
.sl-badge.sl-unsaved { color: #925115; background: #faead4; }
.sl-field-pair { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
.sl-form label { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; margin: 21px 0 9px; font-size: 12px; font-weight: 550; }
.sl-form label span { font-size: 9px; color: #748271; font-weight: 400; }
.sl-form label output { color: var(--sl-green); font-weight: 650; }
.sl-form input:not([type=range]), .sl-form textarea { width: 100%; background: #fffefa; color: var(--sl-ink); border: 1px solid #d5d9ce; border-radius: 8px; padding: 13px 14px; font: inherit; font-size: 14px; outline: none; }
.sl-form input:focus-visible, .sl-form textarea:focus-visible { border-color: var(--sl-green); box-shadow: 0 0 0 3px #00683815; }
.sl-form input[aria-invalid=true], .sl-form textarea[aria-invalid=true] { border-color: #ae503b; }
.sl-form textarea { min-height: 104px; resize: vertical; line-height: 1.5; }
.sl-form textarea::placeholder { color: #8c9585; }
.sl-range { display: block; width: 100%; accent-color: var(--sl-green); margin: 17px 0 10px; }
.sl-range-scale { display: flex; justify-content: space-between; color: #82917d; font-size: 10px; }
.sl-char-count { color: #82917d; text-align: right; font-size: 10px; margin: 6px 0 22px; }
.sl-button { min-height: 42px; border-radius: 99px; display: inline-flex; align-items: center; justify-content: center; gap: 12px; font: inherit; font-size: 12px; font-weight: 550; border: 1px solid transparent; padding: 11px 21px; cursor: pointer; }
.sl-primary { color: #fffefa; background: var(--sl-green); }
.sl-primary:hover { background: var(--sl-ink); }
.sl-secondary { color: var(--sl-ink); background: transparent; border-color: #c8cfbe; }
.sl-secondary:hover { background: #e9efdf; }
.sl-wide { width: 100%; }
.sl-button:focus-visible, .sl-stage-track button:focus-visible, .sl-delete:focus-visible { outline: 2px solid var(--sl-green); outline-offset: 3px; }
.sl-aside { align-self: start; background: #e7eadc; padding: 34px 28px; }
.sl-aside-icon { background: var(--sl-lime); width: 58px; height: 58px; border-radius: 50%; display: grid; place-items: center; margin-bottom: 32px; }
.sl-aside h2 { font-size: 31px; margin-top: 14px; }
.sl-aside p { color: #607263; font-size: 12px; line-height: 1.8; margin: 20px 0; }
.sl-aside dl { margin: 28px 0 0; }
.sl-aside dl > div { display: flex; align-items: baseline; justify-content: space-between; border-top: 1px solid #cbd3be; gap: 12px; padding: 14px 0; font-size: 11px; }
.sl-aside dt { color: #6b7d65; }
.sl-aside dd { margin: 0; font-weight: 550; text-align: right; }
.sl-aside .sl-aside-foot { font-size: 10px; margin-bottom: 0; padding-top: 16px; border-top: 1px solid #cbd3be; }
.sl-notice, .sl-feedback { padding: 14px 18px; border-radius: 8px; font-size: 12px; line-height: 1.6; margin: 0 0 20px; }
.sl-notice { background: #f9e6d8; color: #8e4a23; border: 1px solid #e8cbb9; }
.sl-feedback { background: #e3ecd8; color: var(--sl-green); border: 1px solid #cad8bc; }
.sl-error { color: #ae503b; font-size: 11px; line-height: 1.5; margin: 7px 0 0; }
.sl-muted { color: #76826c; font-size: 11px; line-height: 1.6; margin: 0; }
.sl-review { max-width: 760px; }
.sl-review .sl-card-heading { margin-bottom: 10px; }
.sl-review-rows { margin: 25px 0 0; }
.sl-review-rows > div { display: flex; justify-content: space-between; align-items: baseline; gap: 20px; padding: 17px 0; border-bottom: 1px solid var(--sl-line); }
.sl-review-rows dt { color: #6f8067; font-size: 12px; }
.sl-review-rows dd { font-size: 16px; margin: 0; text-align: right; font-variant-numeric: tabular-nums; }
.sl-delta { display: flex; align-items: center; justify-content: space-between; gap: 20px; background: #edf0e1; margin: 24px 0 0; padding: 20px; border-radius: 8px; }
.sl-delta span { color: #607263; font-size: 12px; }
.sl-delta strong { font-size: 25px; letter-spacing: -.025em; }
.sl-positive { color: var(--sl-green); }.sl-negative { color: #ae503b; }
.sl-actions { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; margin-top: 28px; }
.sl-stage-track { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin: 30px 0; }
.sl-stage-track button { position: relative; display: flex; align-items: center; gap: 9px; min-height: 57px; padding: 11px 16px 11px 11px; border: 1px solid var(--sl-line); border-radius: 8px; background: transparent; color: #819175; text-align: left; font: inherit; font-size: 10px; line-height: 1.4; cursor: pointer; }
.sl-stage-track button.current { background: var(--sl-green); color: #fffefa; border-color: var(--sl-green); }
.sl-stage-track button.done { color: var(--sl-green); background: #eaf0df; }
.sl-stage-number { flex-shrink: 0; width: 25px; height: 25px; border-radius: 50%; border: 1px solid currentColor; display: grid; place-items: center; font-size: 10px; }
.sl-stage-arrow { position: absolute; right: 5px; opacity: .55; }
.sl-summary { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 0 0 25px; }
.sl-summary > div { background: #f0f1e8; border-radius: 8px; padding: 18px; }
.sl-summary dt { font-size: 10px; color: #6c8064; }
.sl-summary dd { margin: 15px 0 0; font-size: 18px; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.sl-journal blockquote { margin: 25px 0; border-left: 3px solid var(--sl-lime); padding: 10px 18px; color: #49643f; font-size: 14px; line-height: 1.7; white-space: pre-wrap; overflow-wrap: anywhere; }
.sl-delete { margin-left: auto; border: 0; background: transparent; font: inherit; font-size: 11px; color: #a45138; padding: 10px 0; cursor: pointer; }
@media (max-width: 850px) { .sl-layout { grid-template-columns: 1fr; }.sl-aside { display: none; }.sl-stage-track { grid-template-columns: repeat(2, 1fr); }.sl-summary { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 520px) { .scenario-lab { padding: 34px 0 45px; }.sl-header h1 { font-size: 36px; }.sl-header p { font-size: 13px; }.sl-card { padding: 21px 18px; }.sl-card h2 { font-size: 22px; }.sl-field-pair { grid-template-columns: 1fr; gap: 0; }.sl-card-heading { gap: 9px; }.sl-badge { font-size: 8px; padding: 5px 7px; }.sl-summary { gap: 8px; }.sl-summary > div { padding: 13px; }.sl-summary dd { font-size: 15px; }.sl-delta { padding: 15px; }.sl-delta strong { font-size: 21px; }.sl-delete { margin-left: 0; width: 100%; text-align: left; } }
</style>
