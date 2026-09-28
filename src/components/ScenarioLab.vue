<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { ArrowDownToLine, ArrowUpRight, Check, ChevronRight, FlaskConical, ShieldCheck } from 'lucide-vue-next'
import { brand, storageKeys } from '../brand.js'
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
const legacyJournalKeys = ['Kovrane:journal:v1', 'kinovra:journal:v1', 'Kinovra:journal:v1', 'Scenarill:journal:v1', 'Solenzi:journal:v1']
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
    link.download = `orbinza-${record.value.id.toLowerCase()}.json`
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
          <div><label for="amount">Amount <span>{{ brand.asset }} units</span></label><input id="amount" v-model="amount" inputmode="decimal" :aria-invalid="Boolean(errors.amount)" :aria-describedby="errors.amount ? 'amount-error' : undefined" /><p v-if="errors.amount" id="amount-error" class="sl-error">{{ errors.amount }}</p></div>
          <div><label for="base-price">Reference price <span>USD / {{ brand.asset }}</span></label><input id="base-price" v-model="basePrice" inputmode="decimal" :aria-invalid="Boolean(errors.basePrice)" :aria-describedby="errors.basePrice ? 'price-error' : undefined" /><p v-if="errors.basePrice" id="price-error" class="sl-error">{{ errors.basePrice }}</p></div>
        </div>
        <label for="move">Hypothetical move <output>{{ movePct }}%</output></label>
        <input id="move" v-model="movePct" class="sl-range" type="range" min="-90" max="100" step="0.5" />
        <div class="sl-range-scale"><span>-90%</span><span>0</span><span>+100%</span></div>
        <label for="move-text">Exact percentage <span>%</span></label><input id="move-text" v-model="movePct" inputmode="decimal" :aria-invalid="Boolean(errors.movePct)" :aria-describedby="errors.movePct ? 'move-error' : undefined" /><p v-if="errors.movePct" id="move-error" class="sl-error">{{ errors.movePct }}</p>
        <label for="note">Thesis note <span>OPTIONAL</span></label><textarea id="note" v-model="note" :maxlength="MAX_NOTE_LENGTH" :aria-invalid="Boolean(errors.note)" :aria-describedby="errors.note ? 'note-error' : 'note-count'" placeholder="What would make this move plausible?"></textarea><p v-if="errors.note" id="note-error" class="sl-error">{{ errors.note }}</p><p id="note-count" class="sl-char-count">{{ remaining }} characters remaining</p>
        <button class="sl-button sl-primary sl-wide" type="submit">Review scenario <ArrowUpRight :size="17" /></button>
      </form>
      <aside class="sl-card sl-aside"><div class="sl-aside-icon"><ShieldCheck :size="27" /></div><span class="sl-step">A LITTLE SPACE TO THINK</span><h2>Your idea.<br />Your assumptions.</h2><p>This is a private what-if calculator. Reference prices are entered by you; they are not live quotes or execution prices.</p><dl><div><dt>Asset</dt><dd>{{ brand.asset }} / USD</dd></div><div><dt>Network</dt><dd>{{ brand.network }} - preview</dd></div><div><dt>Wallet</dt><dd>Not required</dd></div><div><dt>Storage</dt><dd>This browser only</dd></div></dl><p class="sl-aside-foot">Fees, slippage and taxes are excluded. No transaction is created.</p></aside>
    </div>

    <div v-else-if="step === 'review'" class="sl-card sl-review">
      <div class="sl-card-heading"><div><span class="sl-step">02 / REVIEW</span><h2>Check the numbers.</h2></div><ShieldCheck :size="26" /></div><p class="sl-muted">Calculated from your assumptions.</p>
      <dl class="sl-review-rows"><div><dt>Reference amount</dt><dd>{{ Number(record.amount).toLocaleString() }} {{ brand.asset }}</dd></div><div><dt>Reference price</dt><dd>{{ currency(result.basePrice, 4) }}</dd></div><div><dt>Reference value</dt><dd>{{ currency(result.baselineValue, 4) }}</dd></div><div><dt>Scenario move</dt><dd :class="record.movePct >= 0 ? 'sl-positive' : 'sl-negative'">{{ percent(record.movePct) }}</dd></div><div><dt>Scenario value</dt><dd>{{ currency(result.scenarioValue, 4) }}</dd></div></dl>
      <div class="sl-delta"><span>Change in reference value</span><strong :class="result.deltaUsd >= 0 ? 'sl-positive' : 'sl-negative'">{{ result.deltaUsd >= 0 ? '+' : '' }}{{ currency(result.deltaUsd, 4) }}</strong></div>
      <div class="sl-actions"><button class="sl-button sl-primary" @click="save">Save to journal <Check :size="17" /></button><button class="sl-button sl-secondary" @click="edit">Edit inputs</button></div>
    </div>

    <div v-else class="sl-card sl-journal">
      <div class="sl-card-heading"><div><span class="sl-step">03 / JOURNAL</span><h2>Your local record.</h2></div><span class="sl-badge" :class="{ 'sl-unsaved': !isSaved }"><Check v-if="isSaved" :size="13" />{{ isSaved ? 'SAVED' : 'NOT SAVED' }}</span></div>
      <div class="sl-stage-track" aria-label="Journal review stages"><button v-for="(label, i) in stages" :key="label" :class="{ current: record.stage === i, done: record.stage > i }" :aria-current="record.stage === i ? 'step' : undefined" @click="changeStage(i)"><span class="sl-stage-number"><Check v-if="record.stage > i" :size="13" /><template v-else>{{ i + 1 }}</template></span><span>{{ label }}</span><ChevronRight v-if="i < stages.length - 1" class="sl-stage-arrow" :size="14" /></button></div>
      <dl class="sl-summary"><div><dt>Amount</dt><dd>{{ Number(record.amount).toLocaleString() }} {{ brand.asset }}</dd></div><div><dt>Reference price</dt><dd>{{ currency(record.basePrice, 4) }}</dd></div><div><dt>Move</dt><dd :class="record.movePct >= 0 ? 'sl-positive' : 'sl-negative'">{{ percent(record.movePct) }}</dd></div><div><dt>Scenario value</dt><dd>{{ currency(result.scenarioValue, 4) }}</dd></div></dl>
      <blockquote v-if="record.note">{{ record.note }}</blockquote><p class="sl-muted">Created {{ new Date(record.createdAt).toLocaleString() }}. {{ isSaved ? 'Stored only in this browser.' : 'Export a copy to keep this record.' }}</p>
      <div class="sl-actions"><button class="sl-button sl-primary" @click="downloadJournal">Export JSON <ArrowDownToLine :size="16" /></button><button v-if="!isSaved" class="sl-button sl-secondary" @click="persist">Retry saving</button><button class="sl-button sl-secondary" @click="edit">Edit</button><button class="sl-delete" @click="removeJournal">Delete local record</button></div>
    </div>
  </section>
</template>

<style scoped>
.scenario-lab { color: var(--sl-ink); font: inherit;
  --sl-ink: #eaf1f7; --sl-green: var(--cyan); --sl-line: var(--line); background: #090f18; padding: 34px var(--gutter, 4vw) 64px;
}
.scenario-lab > * {
  width: min(1280px, 100%); margin-inline: auto;
}
.scenario-lab *, .scenario-lab *::before, .scenario-lab *::after {
  box-sizing: border-box;
}
.sl-header {
  max-width: 760px; margin-bottom: 24px;
}
.sl-eyebrow {
  display: flex; align-items: center; gap: 7px; font-weight: 700;
  color: var(--cyan); font-family: var(--mono); font-size: 9px; letter-spacing: .1em;
}
.sl-header h1 { line-height: 1.04; font-weight: 600; outline: none;
  margin: 10px 0 10px; font-size: clamp(30px, 4vw, 44px); letter-spacing: -.03em;
}
.sl-header h1 span {
  color: var(--cyan);
}
.sl-header p { margin: 0;
  max-width: 620px; color: #8ba0b2; font-size: 12px; line-height: 1.6;
}
.sl-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(240px, .55fr); gap: 12px;
}
.sl-card { border: 1px solid var(--sl-line); min-width: 0;
  padding: 21px; border-color: var(--line); border-radius: 4px; background: #0e1521; box-shadow: var(--card-shadow);
}
.sl-card-heading {
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
  margin-bottom: 16px;
}
.sl-step {
  display: block; font-weight: 650;
  color: #7890a4; font-family: var(--mono); font-size: 9px; letter-spacing: .08em;
}
.sl-card h2 {
  margin: 9px 0 0; letter-spacing: -.035em; line-height: 1.15; font-weight: 600;
  margin-top: 7px; font-size: 20px;
}
.sl-badge {
  display: inline-flex; align-items: center; gap: 5px; white-space: nowrap; font-size: 9px; font-weight: 700; letter-spacing: .04em;
  padding: 5px 7px; border-radius: 3px; background: #123547; color: var(--cyan); font: 9px var(--mono);
}
.sl-badge.sl-unsaved {
  background: #3a2b1b; color: var(--amber);
}
.sl-field-pair {
  display: grid; grid-template-columns: 1fr 1fr; gap: 18px;
}
.sl-form label {
  display: flex; align-items: baseline; justify-content: space-between; gap: 8px; font-size: 12px; font-weight: 550;
  margin: 16px 0 7px; color: #a9b9c6; font: 10px var(--mono); letter-spacing: .02em; text-transform: uppercase;
}
.sl-form label span { font-weight: 400;
  color: #70869a; font-size: 8px;
}
.sl-form label output { font-weight: 650;
  color: var(--cyan);
}
.sl-form input:not([type=range]), .sl-form textarea {
  width: 100%; border: 1px solid var(--line); font-size: 14px; outline: none;
  padding: 10px 11px; border-color: #22394d; border-radius: 3px; background: #090f18; color: var(--fg); font: 12px var(--mono);
}
.sl-form input:focus-visible, .sl-form textarea:focus-visible {
  border-color: var(--cyan); box-shadow: 0 0 0 3px #28d7e816;
}
.sl-form input[aria-invalid=true], .sl-form textarea[aria-invalid=true] {
  border-color: var(--magenta);
}
.sl-form textarea { resize: vertical; line-height: 1.5;
  min-height: 90px;
}
.sl-form textarea::placeholder {
  color: #5f7488;
}
.sl-range {
  display: block; width: 100%;
  accent-color: var(--cyan); margin: 14px 0 8px;
}
.sl-range-scale {
  display: flex; justify-content: space-between; font-size: 10px;
  color: #6e8397; font: 9px var(--mono);
}
.sl-char-count { text-align: right; font-size: 10px;
  color: #6e8397; font: 9px var(--mono);
  margin: 5px 0 17px;
}
.sl-button { display: inline-flex; align-items: center; justify-content: center; gap: 12px; font-size: 12px; font-weight: 550; border: 1px solid transparent; cursor: pointer;
  min-height: 38px; padding: 9px 15px; border-radius: 3px; font: 10px var(--mono); letter-spacing: .03em; text-transform: uppercase;
}
.sl-primary {
  border-color: var(--cyan); background: var(--cyan); color: #05121a;
}
.sl-primary:hover {
  background: #73e4ff;
}
.sl-secondary {
  border-color: #2b455c; background: #111d2b; color: #a9b9c6;
}
.sl-secondary:hover {
  background: var(--cyan-soft);
  border-color: var(--cyan); color: var(--cyan);
}
.sl-wide {
  width: 100%;
}
.sl-button:focus-visible, .sl-stage-track button:focus-visible, .sl-delete:focus-visible {
  outline: 2px solid var(--sl-green); outline-offset: 3px;
}
.sl-aside {
  align-self: start; padding: 34px 28px;
  background: #0b131e;
}
.sl-aside-icon { margin-bottom: 32px;
  display: grid; width: 38px; height: 38px; place-items: center; border: 1px solid #26526a; border-radius: 3px; background: #123547; color: var(--cyan);
}
.sl-aside h2 { margin-top: 14px;
  font-size: 19px;
}
.sl-aside p { margin: 20px 0;
  color: #8195a7; font-size: 11px; line-height: 1.6;
}
.sl-aside dl {
  margin: 28px 0 0;
  border-top-color: var(--line);
}
.sl-aside dl > div {
  display: flex; align-items: baseline; justify-content: space-between; border-top: 1px solid var(--line); gap: 12px; padding: 14px 0; font-size: 11px;
}
.sl-aside dt {
  color: #71869a; font: 9px var(--mono); text-transform: uppercase;
}
.sl-aside dd {
  margin: 0; font-weight: 550; text-align: right;
  color: var(--fg); font: 11px var(--mono);
}
.sl-aside .sl-aside-foot {
  font-size: 10px; margin-bottom: 0; padding-top: 16px; border-top: 1px solid var(--line);
}
.sl-notice, .sl-feedback { font-size: 12px; line-height: 1.6;
  max-width: 1280px; margin: 10px auto; padding: 9px 11px; border: 1px solid #5b3b2e; border-radius: 3px; background: #211714; color: var(--amber); font: 10px var(--mono);
}
.sl-notice {
  background: var(--surface); color: var(--magenta); border: 1px solid var(--fg);
}
.sl-feedback { border: 1px solid var(--line);
  border-color: #21536a; background: #0c2430; color: var(--cyan);
}
.sl-error {
  color: var(--magenta); font-size: 11px; line-height: 1.5; margin: 7px 0 0;
}
.sl-muted { margin: 0;
  color: #8195a7; font-size: 11px; line-height: 1.6;
}
.sl-review {
  max-width: 760px;
}
.sl-review .sl-card-heading {
  margin-bottom: 10px;
}
.sl-review-rows {
  margin: 25px 0 0;
}
.sl-review-rows > div {
  display: flex; justify-content: space-between; align-items: baseline; gap: 20px; padding: 17px 0; border-bottom: 1px solid var(--sl-line);
  border-color: var(--line);
}
.sl-review-rows dt { font-size: 12px;
  color: #71869a; font: 9px var(--mono); text-transform: uppercase;
}
.sl-review-rows dd {
  font-size: 16px; margin: 0; text-align: right; font-variant-numeric: tabular-nums;
  color: var(--fg); font: 11px var(--mono);
}
.sl-delta {
  display: flex; align-items: center; justify-content: space-between; gap: 20px; margin: 24px 0 0; padding: 20px; border-radius: 8px;
  border-color: #21536a; background: #0c2430;
}
.sl-delta span {
  color: var(--muted); font-size: 12px;
}
.sl-delta strong {
  font-size: 25px; letter-spacing: -.025em;
  color: var(--cyan); font-family: var(--mono);
}
.sl-positive {
  color: var(--cyan) !important;
}
.sl-negative {
  color: var(--magenta) !important;
}
.sl-actions {
  display: flex; align-items: center; flex-wrap: wrap; gap: 10px; margin-top: 28px;
}
.sl-stage-track {
  display: grid; grid-template-columns: repeat(4, 1fr); margin: 30px 0;
  gap: 2px; padding: 3px; border: 1px solid var(--line); border-radius: 3px; background: #090f18;
}
.sl-stage-track button {
  position: relative; display: flex; align-items: center; gap: 9px; padding: 11px 16px 11px 11px; border: 1px solid var(--sl-line); background: transparent; text-align: left; font-size: 10px; line-height: 1.4; cursor: pointer;
  min-height: 35px; border-radius: 2px; color: #71869a; font: 9px var(--mono);
}
.sl-stage-track button.current { border-color: var(--sl-green);
  background: #123547; color: var(--cyan);
}
.sl-stage-track button.done { background: var(--cyan-soft);
  color: #a9b9c6;
}
.sl-stage-number {
  flex-shrink: 0; width: 25px; height: 25px; border-radius: 50%; border: 1px solid currentColor; display: grid; place-items: center; font-size: 10px;
  border-color: #2a465e; background: #101d2b;
}
.sl-stage-arrow {
  position: absolute; right: 5px; opacity: .55;
  color: #456179;
}
.sl-summary {
  display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); margin: 0 0 25px;
  gap: 0;
}
.sl-summary > div {
  background: var(--surface); border-radius: 8px;
  border-color: var(--line);
  padding: 12px 0;
}
.sl-summary dt {
  font-size: 10px;
  color: #71869a; font: 9px var(--mono); text-transform: uppercase;
}
.sl-summary dd {
  margin: 15px 0 0; font-variant-numeric: tabular-nums; overflow-wrap: anywhere;
  color: var(--fg); font: 11px var(--mono);
  margin-top: 7px; font-size: 15px;
}
.sl-journal blockquote { border-left: 3px solid var(--amber); font-size: 14px; line-height: 1.7; white-space: pre-wrap; overflow-wrap: anywhere;
  margin: 18px 0; border-left-color: var(--amber); padding: 9px 13px; color: #d4b078; font: 11px/1.6 var(--mono);
}
.sl-delete {
  margin-left: auto; border: 0; background: transparent; font-size: 11px; padding: 10px 0; cursor: pointer;
  color: var(--magenta); font: 10px var(--mono);
}
@media (max-width: 850px) {
  .sl-layout {
    grid-template-columns: 1fr;
  }
  .sl-aside {
    display: none;
  }
  .sl-stage-track {
    grid-template-columns: repeat(2, 1fr);
  }
  .sl-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 520px) {
  .scenario-lab {
    padding: 25px 0 46px;
  }
  .sl-header h1 {
    font-size: 30px;
  }
  .sl-header p {
    font-size: 13px;
  }
  .sl-card {
    padding: 17px;
  }
  .sl-card h2 {
    font-size: 19px;
  }
  .sl-field-pair {
    grid-template-columns: 1fr; gap: 0;
  }
  .sl-card-heading {
    gap: 9px;
  }
  .sl-badge {
    font-size: 8px; padding: 5px 7px;
  }
  .sl-summary {
    gap: 8px;
  }
  .sl-summary > div {
    padding: 13px;
  }
  .sl-summary dd {
    font-size: 15px;
  }
  .sl-delta {
    padding: 15px;
  }
  .sl-delta strong {
    font-size: 21px;
  }
  .sl-delete {
    margin-left: 0; width: 100%; text-align: left;
  }
}
.sl-aside-foot {
  color: #8195a7; font-size: 11px; line-height: 1.6;
}
.sl-stage-track button.current .sl-stage-number, .sl-stage-track button.done .sl-stage-number {
  border-color: var(--cyan); color: var(--cyan);
}
</style>

