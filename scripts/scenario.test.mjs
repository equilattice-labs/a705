import test from 'node:test'
import assert from 'node:assert/strict'
import { DEFAULT_BASE_PRICE, SCHEMA_VERSION, calculateScenario, createJournalRecord, restoreJournalRecord, validateJournalRecord, validateScenarioInputs } from '../src/scenario.js'

const inputs = { amount: '1000', basePrice: '0.0248', movePct: '-15', note: 'A deliberately chosen downside case.' }
const options = { id: 'LM-TEST01', createdAt: '2026-09-23T08:00:00.000Z' }
const close = (actual, expected) => assert.ok(Math.abs(actual - expected) <= Math.max(1e-12, Math.abs(expected) * 1e-12), `${actual} differs from ${expected}`)

test('scenario uses the explicitly entered price without premature currency rounding', () => {
  const result = calculateScenario(inputs)
  close(result.basePrice, 0.0248)
  close(result.baselineValue, 24.8)
  close(result.scenarioPrice, 0.02108)
  close(result.scenarioValue, 21.08)
  close(result.deltaUsd, -3.72)
  close(result.scenarioValue - result.baselineValue, result.deltaUsd)
})

test('flat, maximum upside and maximum downside scenarios reconcile', () => {
  for (const [movePct, price, delta] of [[0, 0.0248, 0], [100, 0.0496, 24.8], [-90, 0.00248, -22.32]]) {
    const result = calculateScenario({ ...inputs, movePct })
    close(result.scenarioPrice, price)
    close(result.deltaUsd, delta)
    close(result.baselineValue + result.deltaUsd, result.scenarioValue)
  }
  assert.equal(Object.is(calculateScenario({ ...inputs, movePct: '-0' }).deltaUsd, -0), false)
})

test('minimum token amount and small reference price remain finite', () => {
  assert.equal(validateScenarioInputs({ amount: '0.00000001', basePrice: '0.00000001', movePct: '0.01' }).valid, true)
  assert.equal(validateScenarioInputs({ amount: 1e-8, basePrice: 1e-8, movePct: 0.01 }).valid, true)
  for (const amount of ['0.00000001', '1000000000']) {
    const result = calculateScenario({ amount, basePrice: '0.000001', movePct: '100' })
    assert.ok(Object.values(result).every(Number.isFinite))
    assert.ok(result.baselineValue > 0)
    close(result.scenarioValue, result.baselineValue * 2)
  }
})

test('amount rejects invalid types, nondecimal notation, bounds and excess precision', () => {
  for (const amount of ['', ' ', '0', '-1', '1000000001', '1000000000.00000001', '1e3', '0x10', 'Infinity', '1,000', '0.000000001', 1e-9, Infinity, NaN, null, true, {}, []]) {
    assert.equal(validateScenarioInputs({ ...inputs, amount }).valid, false, `accepted ${String(amount)}`)
  }
})

test('reference price must be a positive finite decimal within supported precision', () => {
  for (const basePrice of ['', ' ', '0', '-1', '1000000001', '0.0000000000001', '1e3', 'Infinity', Infinity, NaN, null, true, {}, []]) {
    assert.equal(validateScenarioInputs({ ...inputs, basePrice }).valid, false, `accepted ${String(basePrice)}`)
  }
  assert.equal(validateScenarioInputs({ ...inputs, basePrice: ' 0.000000000001 ' }).valid, true)
  assert.equal(DEFAULT_BASE_PRICE, '1.00')
})

test('price change has a bounded, two-decimal value', () => {
  for (const movePct of ['', ' ', '-90.01', '100.01', '1.001', '1e1', Infinity, NaN, false, null, [], {}]) {
    assert.equal(validateScenarioInputs({ ...inputs, movePct }).valid, false, `accepted ${String(movePct)}`)
  }
  assert.equal(validateScenarioInputs({ ...inputs, amount: ' 1.23456789 ', basePrice: '0.1', movePct: ' -15.25 ' }).valid, true)
})

test('notes preserve user text and enforce their size limit', () => {
  const note = '  Keep my observation.\nSecond line.  '
  assert.equal(validateScenarioInputs({ ...inputs, note }).value.note, note)
  assert.equal(validateScenarioInputs({ ...inputs, note: 'a'.repeat(1000) }).valid, true)
  assert.equal(validateScenarioInputs({ ...inputs, note: 'a'.repeat(1001) }).valid, false)
  assert.equal(validateScenarioInputs({ ...inputs, note: {} }).valid, false)
})

test('journal round trip preserves the entered assumptions and review stage', () => {
  const original = createJournalRecord(inputs, { ...options, stage: 2 })
  const restored = restoreJournalRecord(JSON.parse(JSON.stringify(original)))
  assert.equal(restored.valid, true)
  assert.equal(restored.migrated, false)
  assert.deepEqual(restored.value, original)
  assert.deepEqual(calculateScenario(restored.value), calculateScenario(inputs))
  assert.equal(original.asset, 'SCNV')
  assert.equal(original.id, 'SC-TEST01')
  assert.equal(original.schemaVersion, SCHEMA_VERSION)
  assert.equal(original.basePrice, 0.0248)
  assert.equal(original.stage, 2)
})

test('old placeholder journal converts its value into a user-entered assumption', () => {
  const old = {
    schemaVersion: 2,
    asset: 'KNVR',
    id: 'KN-OLD01',
    createdAt: '2026-09-23T08:00:00.000Z',
    amount: 1000,
    movePct: -15,
    note: 'Previous local note.',
    snapshot: { price: 0.0248, observedAt: '2026-09-22T02:27:11.618Z', source: 'https://solscan.io/tokens' },
    stage: 1,
  }
  const restored = restoreJournalRecord(old)
  assert.equal(restored.valid, true)
  assert.equal(restored.migrated, true)
  assert.equal(restored.value.id, 'SC-OLD01')
  assert.equal(restored.value.asset, 'SCNV')
  assert.equal(restored.value.basePrice, 0.0248)
  assert.equal('snapshot' in restored.value, false)
  assert.equal(validateJournalRecord(old).valid, false)
})

test('current-version legacy brand records normalize once into the Scenovia identity', () => {
  const older = { ...createJournalRecord(inputs, options), asset: 'LMQR', id: 'LM-TEST01' }
  const restored = restoreJournalRecord(older)
  assert.equal(restored.valid, true)
  assert.equal(restored.migrated, true)
  assert.equal(restored.value.asset, 'SCNV')
  assert.equal(restored.value.id, 'SC-TEST01')
  assert.equal(restoreJournalRecord(restored.value).migrated, false)
})

test('legacy records from any other asset and corrupted journals are rejected', () => {
  const record = createJournalRecord(inputs, options)
  const bad = [null, [], '', 42, { id: 'OLD-1', station: 2 }, { ...record, schemaVersion: 2 }, { ...record, asset: 'DOGE' }, { ...record, stage: 4 }, { ...record, stage: -1 }, { ...record, stage: 1.5 }, { ...record, stage: '2' }, { ...record, amount: '0' }, { ...record, basePrice: '0' }, { ...record, movePct: 101 }, { ...record, note: undefined }, { ...record, id: 'LM-\nBAD' }]
  for (const candidate of bad) assert.equal(restoreJournalRecord(candidate).valid, false)
})

test('journal validation rejects invalid dates and non-finite assumptions', () => {
  const record = createJournalRecord(inputs, options)
  for (const candidate of [
    { ...record, basePrice: Infinity },
    { ...record, basePrice: '0' },
    { ...record, createdAt: 'not a date' },
    { ...record, createdAt: '2026-02-30T01:50:00Z' },
  ]) assert.equal(validateJournalRecord(candidate).valid, false)
  assert.equal(validateJournalRecord({ ...record, createdAt: '2026-09-22T00:00:00Z' }).valid, true)
})

test('creating and calculating scenarios reject invalid input instead of manufacturing a result', () => {
  assert.throws(() => createJournalRecord({ ...inputs, amount: -1 }, options), RangeError)
  assert.throws(() => createJournalRecord(inputs), RangeError)
  assert.throws(() => calculateScenario({ ...inputs, movePct: 101 }), RangeError)
  assert.throws(() => calculateScenario({ ...inputs, basePrice: NaN }), RangeError)
})

test('journal validation strips unrelated fields and does not mutate caller data', () => {
  const record = createJournalRecord(inputs, options)
  const restored = validateJournalRecord({ ...record, beneficiary: 'old address', unused: 'old' })
  assert.equal(restored.valid, true)
  assert.equal('beneficiary' in restored.value, false)
  assert.equal('unused' in restored.value, false)
  restored.value.basePrice = 0.2
  assert.equal(record.basePrice, 0.0248)
})
