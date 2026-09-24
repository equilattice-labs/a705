export const SCHEMA_VERSION = 3
export const MAX_NOTE_LENGTH = 1000
export const DEFAULT_BASE_PRICE = '1.00'
const ASSET = 'LMQR'
const LEGACY_ASSET = 'KNVR'
const LEGACY_SNAPSHOT_SOURCE = 'https://solscan.io/tokens'
const isObject = value => value !== null && typeof value === 'object' && !Array.isArray(value)

function decimal(value, places) {
  if (typeof value !== 'string' && typeof value !== 'number') return null
  const text = typeof value === 'number'
    ? (Number.isFinite(value) && Math.abs(value) <= 1e9 && Number(value.toFixed(places)) === value ? value.toFixed(places) : '')
    : value.trim()
  if (text.length > 100 || !/^-?\d+(?:\.\d+)?$/.test(text) || (text.split('.')[1] || '').length > places) return null
  const number = Number(text)
  if (!Number.isFinite(number)) return null
  const [whole, fraction = ''] = text.replace(/^-/, '').split('.')
  return { number: number === 0 ? 0 : number, units: BigInt(whole + fraction.padEnd(places, '0')) * (text.startsWith('-') ? -1n : 1n) }
}

function isUtcTimestamp(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/.test(value)) return false
  const time = Date.parse(value)
  return Number.isFinite(time) && new Date(time).toISOString() === (value.includes('.') ? value : value.replace('Z', '.000Z'))
}

export function validateScenarioInputs(input) {
  const errors = {}
  const value = isObject(input) ? input : {}
  const amount = decimal(value.amount, 8)
  const basePrice = decimal(value.basePrice, 12)
  const movePct = decimal(value.movePct, 2)
  if (amount === null || amount.units <= 0n || amount.units > 100000000000000000n) errors.amount = 'Enter more than 0 and at most 1,000,000,000 LMQR, with up to 8 decimal places.'
  if (basePrice === null || basePrice.units <= 0n || basePrice.number > 1e9) errors.basePrice = 'Enter a price greater than $0 and no more than $1,000,000,000, with up to 12 decimal places.'
  if (movePct === null || movePct.units < -9000n || movePct.units > 10000n) errors.movePct = 'Enter a price change from -90% to +100%, with up to 2 decimal places.'
  const note = value.note === undefined ? '' : value.note
  if (typeof note !== 'string' || note.length > MAX_NOTE_LENGTH) errors.note = `Keep the journal note within ${MAX_NOTE_LENGTH} characters.`
  const valid = Object.keys(errors).length === 0
  return { valid, errors, value: valid ? { amount: amount.number, basePrice: basePrice.number, movePct: movePct.number, note } : null }
}

export function calculateScenario(input) {
  const validated = validateScenarioInputs(input)
  if (!validated.valid) throw new RangeError(Object.values(validated.errors).join(' '))
  const { amount, basePrice, movePct } = validated.value
  const baselineValue = amount * basePrice
  const scenarioPrice = basePrice * (1 + movePct / 100)
  const scenarioValue = amount * scenarioPrice
  return { basePrice, baselineValue, scenarioPrice, scenarioValue, deltaUsd: baselineValue * movePct / 100 || 0 }
}

export function validateJournalRecord(record) {
  const errors = {}
  if (!isObject(record)) return { valid: false, errors: { record: 'Journal record is not an object.' }, value: null }
  if (record.schemaVersion !== SCHEMA_VERSION || record.asset !== ASSET) errors.schema = 'This is not a supported LMQR journal record.'
  if (typeof record.id !== 'string' || !/^LM-[A-Za-z0-9-]{1,64}$/.test(record.id)) errors.id = 'Journal ID is invalid.'
  if (!isUtcTimestamp(record.createdAt)) errors.createdAt = 'Journal creation timestamp is invalid.'
  if (!Number.isInteger(record.stage) || record.stage < 0 || record.stage > 3) errors.stage = 'Journal stage must be between 0 and 3.'
  const inputs = validateScenarioInputs(record)
  Object.assign(errors, inputs.errors)
  if (record.note === undefined) errors.note = 'Journal note is missing.'
  const valid = Object.keys(errors).length === 0
  return { valid, errors, value: valid ? { schemaVersion: SCHEMA_VERSION, asset: ASSET, id: record.id, createdAt: record.createdAt, ...inputs.value, stage: record.stage } : null }
}

export function createJournalRecord(input, { id, createdAt, stage = 0 } = {}) {
  const validated = validateScenarioInputs(input)
  if (!validated.valid) throw new RangeError(Object.values(validated.errors).join(' '))
  const candidate = { ...validated.value, schemaVersion: SCHEMA_VERSION, asset: ASSET, id, createdAt, stage }
  const result = validateJournalRecord(candidate)
  if (!result.valid) throw new RangeError(Object.values(result.errors).join(' '))
  return result.value
}

/** Restore a current record or convert the previous placeholder snapshot into an explicit user assumption. */
export function restoreJournalRecord(record) {
  const current = validateJournalRecord(record)
  if (current.valid) return { ...current, migrated: false }
  const legacySnapshot = record?.snapshot
  if (
    !isObject(record) || record.schemaVersion !== 2 || record.asset !== LEGACY_ASSET ||
    typeof record.id !== 'string' || !/^KN-[A-Za-z0-9-]{1,64}$/.test(record.id) ||
    !isUtcTimestamp(record.createdAt) || !Number.isInteger(record.stage) || record.stage < 0 || record.stage > 3 ||
    !isObject(legacySnapshot) || legacySnapshot.source !== LEGACY_SNAPSHOT_SOURCE ||
    !isUtcTimestamp(legacySnapshot.observedAt) || Date.parse(record.createdAt) < Date.parse(legacySnapshot.observedAt)
  ) return { valid: false, errors: current.errors, value: null, migrated: false }

  try {
    const value = createJournalRecord({ amount: record.amount, basePrice: legacySnapshot.price, movePct: record.movePct, note: record.note }, {
      id: `LM-${record.id.slice(3)}`,
      createdAt: record.createdAt,
      stage: record.stage,
    })
    return { valid: true, errors: {}, value, migrated: true }
  } catch {
    return { valid: false, errors: current.errors, value: null, migrated: false }
  }
}
