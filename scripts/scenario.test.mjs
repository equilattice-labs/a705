import test from 'node:test'
import assert from 'node:assert/strict'
import { SNAPSHOT, validateScenarioInputs, calculateScenario, createJournalRecord, validateJournalRecord } from '../src/scenario.js'

const inputs = { amount: '1000', movePct: '-15', note: 'A deliberately chosen downside case.' }
const options = { id: 'DP-TEST01', createdAt: '2026-09-22T03:00:00.000Z' }
const close = (actual, expected) => assert.ok(Math.abs(actual - expected) <= Math.max(1e-12, Math.abs(expected) * 1e-12), `${actual} differs from ${expected}`)

test('downside calculation uses the captured price without premature currency rounding', () => {
  const result = calculateScenario(inputs)
  close(result.baselineValue, 99.869125)
  close(result.scenarioPrice, 0.08488875625)
  close(result.scenarioValue, 84.88875625)
  close(result.deltaUsd, -14.98036875)
  close(result.scenarioValue - result.baselineValue, result.deltaUsd)
})

test('flat, maximum upside and maximum downside scenarios reconcile', () => {
  for (const [movePct, price, delta] of [[0, 0.099869125, 0], [100, 0.19973825, 99.869125], [-90, 0.0099869125, -89.8822125]]) {
    const result = calculateScenario({ amount: 1000, movePct })
    close(result.scenarioPrice, price)
    close(result.deltaUsd, delta)
    close(result.baselineValue + result.deltaUsd, result.scenarioValue)
  }
  assert.equal(Object.is(calculateScenario({ amount: 1, movePct: '-0' }).deltaUsd, -0), false)
})

test('minimum eight-decimal amount and maximum amount remain finite', () => {
  assert.equal(validateScenarioInputs({ amount: '0.00000001', movePct: '0.01' }).valid, true)
  assert.equal(validateScenarioInputs({ amount: 1e-8, movePct: 0.01 }).valid, true)
  for (const amount of ['0.00000001', '1000000000']) {
    const result = calculateScenario({ amount, movePct: '100' })
    assert.ok(Object.values(result).every(Number.isFinite))
    assert.ok(result.baselineValue > 0)
    close(result.scenarioValue, result.baselineValue * 2)
  }
})

test('amount rejects invalid types, nondecimal notation, bounds and excess precision', () => {
  for (const amount of ['', ' ', '0', '-1', '1000000001', '1000000000.00000001', '1e3', '0x10', 'Infinity', '1,000', '0.000000001', 1e-9, Infinity, NaN, null, true, {}, []]) {
    assert.equal(validateScenarioInputs({ amount, movePct: 0 }).valid, false, `accepted ${String(amount)}`)
  }
})

test('price change requires its own two-decimal bounded value', () => {
  for (const movePct of ['', ' ', '-90.01', '100.01', '1.001', '1e1', Infinity, NaN, false, null, [], {}]) {
    assert.equal(validateScenarioInputs({ amount: 1, movePct }).valid, false, `accepted ${String(movePct)}`)
  }
  assert.equal(validateScenarioInputs({ amount: ' 1.23456789 ', movePct: ' -15.25 ' }).valid, true)
})

test('notes keep user text and enforce a finite size', () => {
  const note = '  Keep my observation.\nSecond line.  '
  assert.equal(validateScenarioInputs({ ...inputs, note }).value.note, note)
  assert.equal(validateScenarioInputs({ ...inputs, note: 'a'.repeat(1000) }).valid, true)
  assert.equal(validateScenarioInputs({ ...inputs, note: 'a'.repeat(1001) }).valid, false)
  assert.equal(validateScenarioInputs({ ...inputs, note: {} }).valid, false)
})

test('journal round trip preserves inputs, source and progress', () => {
  const original = createJournalRecord(inputs, { ...options, stage: 2 })
  const restored = validateJournalRecord(JSON.parse(JSON.stringify(original)))
  assert.equal(restored.valid, true)
  assert.deepEqual(restored.value, original)
  assert.deepEqual(calculateScenario(restored.value, restored.value.snapshot), calculateScenario(inputs))
  assert.notEqual(original.snapshot, SNAPSHOT)
  assert.equal(original.asset, 'DOGE')
  assert.equal(original.stage, 2)
})

test('recovered snapshot is used instead of silently replacing it with the current default', () => {
  const record = createJournalRecord(inputs, { ...options, snapshot: { ...SNAPSHOT, price: 0.1 } })
  const restored = validateJournalRecord(record)
  close(calculateScenario(restored.value, restored.value.snapshot).baselineValue, 100)
  close(calculateScenario(restored.value, restored.value.snapshot).deltaUsd, -15)
})

test('legacy ZEC orders, corrupt values and unsupported schemas do not become DOGE journals', () => {
  const record = createJournalRecord(inputs, options)
  const bad = [null, [], '', 42, { id: 'ZP-OLD', station: 2, beneficiary: '0x123' }, { ...record, schemaVersion: 2 }, { ...record, asset: 'ZEC' }, { ...record, stage: 4 }, { ...record, stage: -1 }, { ...record, stage: 1.5 }, { ...record, stage: '2' }, { ...record, amount: '0' }, { ...record, movePct: 101 }, { ...record, note: undefined }, { ...record, id: 'DP-\nBAD' }]
  for (const candidate of bad) assert.equal(validateJournalRecord(candidate).valid, false)
})

test('recovery checks capture provenance, real timestamps and finite prices', () => {
  const record = createJournalRecord(inputs, options)
  for (const snapshot of [null, { ...SNAPSHOT, price: 0 }, { ...SNAPSHOT, price: Infinity }, { ...SNAPSHOT, price: '0.1' }, { ...SNAPSHOT, source: 'https://example.com/' }, { ...SNAPSHOT, observedAt: '2026-02-30T01:50:00Z' }]) {
    assert.equal(validateJournalRecord({ ...record, snapshot }).valid, false)
  }
  assert.equal(validateJournalRecord({ ...record, createdAt: 'not a date' }).valid, false)
  assert.equal(validateJournalRecord({ ...record, createdAt: '2026-09-21T00:00:00Z' }).valid, false)
  assert.equal(validateJournalRecord({ ...record, createdAt: '2026-09-22T03:00:00Z' }).valid, true)
})

test('creation and calculation reject invalid input instead of manufacturing a result', () => {
  assert.throws(() => createJournalRecord({ ...inputs, amount: -1 }, options), RangeError)
  assert.throws(() => createJournalRecord(inputs), RangeError)
  assert.throws(() => calculateScenario({ ...inputs, movePct: 101 }), RangeError)
  assert.throws(() => calculateScenario(inputs, { ...SNAPSHOT, price: NaN }), RangeError)
})

test('recovery strips unrelated fields and does not mutate caller-owned data', () => {
  const record = createJournalRecord(inputs, options)
  const restored = validateJournalRecord({ ...record, beneficiary: 'old address', snapshot: { ...record.snapshot, extra: 'old' } })
  assert.equal(restored.valid, true)
  assert.equal('beneficiary' in restored.value, false)
  assert.equal('extra' in restored.value.snapshot, false)
  restored.value.snapshot.price = 0.2
  assert.equal(record.snapshot.price, SNAPSHOT.price)
})
