import test from 'node:test'
import assert from 'node:assert/strict'
import { calculateCallPremium, calculatePayoff } from '../src/payoff.js'

test('default 30-day BSM model reproduces the indicative $2.71 premium', () => {
  const result = calculatePayoff()
  assert.equal(result.strike, 262.5)
  assert.equal(result.premium.toFixed(2), '2.71')
  assert.equal(result.incomePrice.toFixed(2), '247.29')
  assert.equal(result.breakeven.toFixed(2), '265.21')
})

test('settlement partitions the stock value below, at, and above every supported cap', () => {
  for (const capPercent of [0, 5, 10]) {
    const strike = 250 * (1 + capPercent / 100)
    for (const settlementPrice of [0, 175, strike, 325, 1000]) {
      const result = calculatePayoff({ capPercent, settlementPrice })
      assert.equal(result.incomeSettlement + result.upsideSettlement, settlementPrice)
      assert.ok(result.incomeSettlement <= strike)
      assert.ok(result.upsideSettlement >= 0)
      assert.ok(Math.abs(result.incomePrice + result.upsidePrice - 250) < 1e-10)
    }
  }
})

test('a higher cap reduces the option premium, and settlement does not change the initial premium', () => {
  assert.ok(calculatePayoff({ capPercent: 0 }).premium > calculatePayoff({ capPercent: 5 }).premium)
  assert.ok(calculatePayoff({ capPercent: 5 }).premium > calculatePayoff({ capPercent: 10 }).premium)
  assert.equal(calculatePayoff({ settlementPrice: 175 }).premium, calculatePayoff({ settlementPrice: 325 }).premium)
})

test('expired or zero-volatility options have intrinsic value and invalid inputs are rejected', () => {
  assert.equal(calculateCallPremium({ spot: 250, strike: 225, days: 0 }), 25)
  assert.equal(calculateCallPremium({ spot: 250, strike: 275, volatility: 0 }), 0)
  assert.throws(() => calculatePayoff({ settlementPrice: -1 }), RangeError)
  assert.throws(() => calculatePayoff({ capPercent: NaN }), RangeError)
  assert.throws(() => calculateCallPremium({ spot: 0, strike: 250 }), RangeError)
})
