// A frozen public-page quote; observedAt preserves its published updated_at.
export const SNAPSHOT = Object.freeze({
  price: 0.099869125,
  observedAt: '2026-09-22T02:27:11.618Z',
  source: 'https://robinhood.com/us/en/crypto/DOGE/',
})

export const SCHEMA_VERSION = 1
export const MAX_NOTE_LENGTH = 1000

const isObject = value => value !== null && typeof value === 'object' && !Array.isArray(value)

function decimal(value, places) {
  if (typeof value !== 'string' && typeof value !== 'number') return null
  let text
  if (typeof value === 'number') {
    if (!Number.isFinite(value) || Math.abs(value) > 1e9) return null
    const fixed = value.toFixed(places)
    if (Number(fixed) !== value) return null
    text = fixed
  } else text = value.trim()
  if (text.length > 100) return null
  if (!/^-?\d+(?:\.\d+)?$/.test(text)) return null
  if ((text.split('.')[1] || '').length > places) return null
  const number = Number(text)
  if (!Number.isFinite(number)) return null
  const [whole, fraction = ''] = text.replace(/^-/, '').split('.')
  const units = BigInt(whole + fraction.padEnd(places, '0')) * (text.startsWith('-') ? -1n : 1n)
  return { number: number === 0 ? 0 : number, units }
}

function isUtcTimestamp(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/.test(value)) return false
  const time = Date.parse(value)
  if (!Number.isFinite(time)) return false
  // Date.parse normalizes impossible dates such as February 30; do not accept them.
  return new Date(time).toISOString() === (value.includes('.') ? value : value.replace('Z', '.000Z'))
}

function validateSnapshot(snapshot) {
  const errors = []
  if (!isObject(snapshot)) return ['Snapshot is missing.']
  if (typeof snapshot.price !== 'number' || !Number.isFinite(snapshot.price) || snapshot.price <= 0 || snapshot.price > 1e9) errors.push('Snapshot price is invalid.')
  if (!isUtcTimestamp(snapshot.observedAt)) errors.push('Snapshot capture timestamp is invalid.')
  if (snapshot.source !== SNAPSHOT.source) errors.push('Snapshot source must be the public Robinhood DOGE page.')
  return errors
}

export function validateScenarioInputs(input) {
  const errors = {}
  const value = isObject(input) ? input : {}
  const amount = decimal(value.amount, 8)
  const movePct = decimal(value.movePct, 2)
  if (amount === null || amount.units <= 0n || amount.units > 100000000000000000n) errors.amount = 'Enter more than 0 and at most 1,000,000,000 DOGE, with up to 8 decimal places.'
  if (movePct === null || movePct.units < -9000n || movePct.units > 10000n) errors.movePct = 'Enter a price change from -90% to +100%, with up to 2 decimal places.'
  const note = value.note === undefined ? '' : value.note
  if (typeof note !== 'string' || note.length > MAX_NOTE_LENGTH) errors.note = `Keep the journal note within ${MAX_NOTE_LENGTH} characters.`
  const valid = Object.keys(errors).length === 0
  return { valid, errors, value: valid ? { amount: amount.number, movePct: movePct.number, note } : null }
}

export function calculateScenario(input, snapshot = SNAPSHOT) {
  const validated = validateScenarioInputs(input)
  const snapshotErrors = validateSnapshot(snapshot)
  if (!validated.valid || snapshotErrors.length) throw new RangeError([...Object.values(validated.errors), ...snapshotErrors].join(' '))
  const { amount, movePct } = validated.value
  const baselineValue = amount * snapshot.price
  const scenarioPrice = snapshot.price * (1 + movePct / 100)
  const scenarioValue = amount * scenarioPrice
  // Keep source precision here; consumers round currency only when displaying it.
  const deltaUsd = baselineValue * movePct / 100
  return { baselineValue, scenarioPrice, scenarioValue, deltaUsd: deltaUsd === 0 ? 0 : deltaUsd }
}

export function validateJournalRecord(record) {
  const errors = {}
  if (!isObject(record)) return { valid: false, errors: { record: 'Journal record is not an object.' }, value: null }
  if (record.schemaVersion !== SCHEMA_VERSION || record.asset !== 'DOGE') errors.schema = 'This is not a supported DOGE journal record.'
  if (typeof record.id !== 'string' || !/^DP-[A-Za-z0-9-]{1,64}$/.test(record.id)) errors.id = 'Journal ID is invalid.'
  if (!isUtcTimestamp(record.createdAt)) errors.createdAt = 'Journal creation timestamp is invalid.'
  if (!Number.isInteger(record.stage) || record.stage < 0 || record.stage > 3) errors.stage = 'Journal stage must be between 0 and 3.'
  const inputs = validateScenarioInputs(record)
  Object.assign(errors, inputs.errors)
  if (record.note === undefined) errors.note = 'Journal note is missing.'
  const snapshotErrors = validateSnapshot(record.snapshot)
  if (snapshotErrors.length) errors.snapshot = snapshotErrors.join(' ')
  if (isUtcTimestamp(record.createdAt) && isUtcTimestamp(record.snapshot?.observedAt) && Date.parse(record.createdAt) < Date.parse(record.snapshot.observedAt)) errors.createdAt = 'Journal cannot predate its source capture.'
  const valid = Object.keys(errors).length === 0
  return {
    valid,
    errors,
    value: valid ? {
      schemaVersion: SCHEMA_VERSION,
      asset: 'DOGE',
      id: record.id,
      createdAt: record.createdAt,
      ...inputs.value,
      snapshot: { price: record.snapshot.price, observedAt: record.snapshot.observedAt, source: record.snapshot.source },
      stage: record.stage,
    } : null,
  }
}

// ID and clock are supplied by the caller so creation is deterministic and testable.
export function createJournalRecord(input, { id, createdAt, snapshot = SNAPSHOT, stage = 0 } = {}) {
  const candidate = { ...input, schemaVersion: SCHEMA_VERSION, asset: 'DOGE', id, createdAt, snapshot, stage, note: input?.note ?? '' }
  const validated = validateJournalRecord(candidate)
  if (!validated.valid) throw new RangeError(Object.values(validated.errors).join(' '))
  return validated.value
}
