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
const legacyJournalKeys = ['Orbinza:journal:v1', 'Kovrane:journal:v1', 'kinovra:journal:v1', 'Kinovra:journal:v1', 'Scenarill:journal:v1', 'Solenzi:journal:v1']
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
    link.download = `tikriva-${record.value.id.toLowerCase()}.json`
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
.scenario-lab{background:var(--bg);padding:30px 0 60px;color:var(--fg)}.sl-header,.sl-layout,.sl-review,.sl-journal,.sl-notice,.sl-feedback{width:min(100%,1080px);margin-inline:auto}.sl-eyebrow,.sl-step,.sl-badge{font:600 10px var(--mono,monospace);letter-spacing:.08em;text-transform:uppercase}.sl-eyebrow{color:var(--mint)}.sl-header h1{margin:9px 0 8px;color:var(--fg);font-size:30px;line-height:1.15;font-weight:650}.sl-layout{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(240px,.65fr);gap:14px;margin-top:24px}.sl-card{min-width:0;padding:20px;border:1px solid var(--line);border-radius:3px;background:var(--surface);box-shadow:0 12px 30px #0003}.sl-card-heading{display:flex;justify-content:space-between;gap:15px;margin-bottom:16px}.sl-card h2{margin:7px 0 0;color:var(--fg);border:0;background:none;font-size:20px;line-height:1.25;font-weight:600}.sl-unsaved{color:var(--accent);border-color:#667735;background:#2b2618}.sl-field-pair{display:grid;grid-template-columns:1fr 1fr;gap:14px}.sl-form label{display:flex;justify-content:space-between;margin:15px 0 6px;color:var(--muted);font:600 10px var(--mono,monospace);text-transform:uppercase}.sl-form label span{font-weight:400;color:#a0a79b}.sl-form input:not([type=range]),.sl-form textarea{width:100%;padding:10px;color:var(--fg);border:1px solid var(--line);border-radius:3px;outline:0;background:var(--panel);font:12px var(--mono,monospace)}.sl-form input:focus-visible,.sl-form textarea:focus-visible{border-color:var(--mint);box-shadow:0 0 0 3px #75d8a822}.sl-form textarea{min-height:100px;resize:vertical}.sl-range{width:100%;accent-color:var(--mint)}.sl-range-scale{display:flex;justify-content:space-between;color:var(--muted);font:10px var(--mono,monospace)}.sl-char-count,.sl-muted{color:var(--muted);font-size:11px;line-height:1.5}.sl-char-count{text-align:right}.sl-button{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:38px;padding:0 13px;border:1px solid var(--line);border-radius:3px;font:600 11px var(--mono,monospace);cursor:pointer}.sl-primary{color:#171b10;background:var(--accent);border-color:var(--accent)}.sl-secondary{color:var(--mint);background:var(--panel);border-color:#75d8a855}.sl-wide{width:100%;margin-top:8px}.sl-aside{background:var(--panel)}.sl-aside-icon{display:grid;place-items:center;width:36px;height:36px;margin-bottom:22px;color:var(--mint);border:1px solid #75d8a855;background:#1b2b20}.sl-aside h2{font-size:20px}.sl-aside p{color:var(--muted);font-size:12px;line-height:1.6}.sl-aside dl{margin-top:22px}.sl-aside dl div,.sl-review-rows div{display:flex;justify-content:space-between;gap:12px;padding:11px 0;border-top:1px solid var(--line)}.sl-aside dt,.sl-review-rows dt,.sl-summary dt{color:var(--muted);font:10px var(--mono,monospace);text-transform:uppercase}.sl-aside dd,.sl-review-rows dd,.sl-summary dd{margin:0;color:var(--fg);font:11px var(--mono,monospace);text-align:right}.sl-notice,.sl-feedback{margin-top:12px;padding:9px 11px;border:1px solid var(--line);color:var(--accent);font:11px var(--mono,monospace)}.sl-feedback{color:var(--mint)}.sl-error{margin:5px 0;color:var(--pink);font-size:11px}.sl-review,.sl-journal{margin-top:24px}.sl-review-rows{margin-top:18px}.sl-review-rows dd{font-size:13px}.sl-delta{display:flex;justify-content:space-between;gap:12px;margin-top:18px;padding:14px;border:1px solid #75d8a855;background:#1b2b20;color:var(--muted);font-size:12px}.sl-delta strong{color:var(--mint);font:500 20px var(--mono,monospace)}.sl-positive{color:var(--mint)!important}.sl-negative{color:var(--pink)!important}.sl-actions{display:flex;flex-wrap:wrap;gap:9px;margin-top:22px}.sl-stage-track{display:grid;grid-template-columns:repeat(4,1fr);gap:3px;margin:16px 0;padding:3px;background:var(--panel);border:1px solid var(--line)}.sl-stage-track button{display:flex;align-items:center;gap:7px;min-height:38px;padding:8px;border:1px solid transparent;background:transparent;color:var(--muted);font:10px var(--mono,monospace);text-align:left;cursor:pointer}.sl-stage-track button.current{color:var(--mint);border-color:#75d8a855;background:#1b2b20}.sl-stage-track button.done{color:var(--fg);background:var(--raised)}.sl-stage-number{display:grid;place-items:center;flex:none;width:22px;height:22px;border:1px solid currentColor;border-radius:50%}.sl-stage-arrow{margin-left:auto}.sl-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;margin:0 0 17px;background:var(--line)}.sl-summary>div{padding:11px;background:var(--panel)}.sl-summary dd{margin-top:7px;font-size:13px}.sl-journal blockquote{margin:16px 0;padding:10px 12px;border-left:2px solid var(--accent);background:#282e1c;color:#f1f3ed;font-size:13px;line-height:1.6}.sl-delete{margin-left:auto;color:var(--pink);background:none;border:0;font:10px var(--mono,monospace);cursor:pointer}.sl-button:focus-visible,.sl-stage-track button:focus-visible,.sl-delete:focus-visible{outline:2px solid var(--mint);outline-offset:3px}@media(max-width:800px){.sl-layout{grid-template-columns:1fr}.sl-aside{display:none}.sl-stage-track{grid-template-columns:1fr 1fr}.sl-summary{grid-template-columns:1fr 1fr}}@media(max-width:520px){.scenario-lab{padding:24px 0 50px}.sl-field-pair{grid-template-columns:1fr}.sl-card{padding:16px}.sl-stage-track{grid-template-columns:1fr}.sl-delete{width:100%;margin-left:0;text-align:left}}
</style>

<style scoped>
.sl-header h1 span { color:var(--accent); }
.sl-badge,.sl-secondary { border-color:#75d8a844; background:#1b2b20; }
.sl-badge { color:var(--mint); }
.sl-unsaved { border-color:#d8fa6355; background:#282e1c; }
.sl-aside-icon { border-color:#75d8a844; background:#1b2b20; }
.sl-delta,.sl-stage-track button.current { border-color:#75d8a844; background:#1b2b20; }
.sl-journal blockquote { border-left-color:var(--accent); background:var(--raised); color:var(--fg); }
.sl-primary { color:#171b10; }
.sl-stage-track button.current { color:var(--mint); }
.sl-form input:focus-visible,.sl-form textarea:focus-visible { box-shadow:0 0 0 3px #75d8a822; }
</style>

