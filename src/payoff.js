/** Illustrative, zero-interest Black–Scholes model; auction prices can differ. */
export const PAYOFF_DEFAULTS = Object.freeze({
  spot: 250,
  capPercent: 5,
  settlementPrice: 250,
  days: 30,
  volatility: 0.25,
})

function finiteNumber(value, name, minimum = 0, exclusive = false) {
  if (typeof value !== 'number' || !Number.isFinite(value) || (exclusive ? value <= minimum : value < minimum)) {
    throw new RangeError(`${name} must be a finite number ${exclusive ? 'greater than' : 'at least'} ${minimum}.`)
  }
  return value
}

/** Standard normal cumulative distribution, with absolute error below 8e-8. */
export function normalCdf(value) {
  if (value === Infinity) return 1
  if (value === -Infinity) return 0
  if (!Number.isFinite(value)) throw new RangeError('Normal variate must be a number.')
  if (value === 0) return 0.5
  const x = Math.abs(value)
  const t = 1 / (1 + 0.2316419 * x)
  const density = Math.exp(-0.5 * x * x) / Math.sqrt(2 * Math.PI)
  const tail = density * t * (0.31938153 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
  return value > 0 ? 1 - tail : tail
}

export function calculateCallPremium({ spot, strike, days = 30, volatility = 0.25 }) {
  finiteNumber(spot, 'Spot', 0, true)
  finiteNumber(strike, 'Strike', 0, true)
  finiteNumber(days, 'Days')
  finiteNumber(volatility, 'Volatility')
  if (days === 0 || volatility === 0) return Math.max(spot - strike, 0)
  const time = days / 365
  const sigmaRootTime = volatility * Math.sqrt(time)
  const d1 = (Math.log(spot / strike) + 0.5 * volatility * volatility * time) / sigmaRootTime
  const d2 = d1 - sigmaRootTime
  return Math.max(0, spot * normalCdf(d1) - strike * normalCdf(d2))
}

/** Per-unit settlement values preserve income + upside = stock value. */
export function calculatePayoff(options = {}) {
  const input = { ...PAYOFF_DEFAULTS, ...options }
  const { spot, capPercent, settlementPrice, days, volatility } = input
  finiteNumber(spot, 'Spot', 0, true)
  finiteNumber(capPercent, 'Cap')
  finiteNumber(settlementPrice, 'Settlement price')
  const strike = spot * (1 + capPercent / 100)
  const premium = calculateCallPremium({ spot, strike, days, volatility })
  const incomeSettlement = Math.min(settlementPrice, strike)
  const upsideSettlement = Math.max(settlementPrice - strike, 0)
  return {
    ...input,
    strike,
    premium,
    incomePrice: spot - premium,
    upsidePrice: premium,
    incomeSettlement,
    upsideSettlement,
    incomeWithPremium: incomeSettlement + premium,
    breakeven: strike + premium,
    spotChangePercent: (settlementPrice / spot - 1) * 100,
    incomeShare: (spot - premium) / spot * 100,
    upsideShare: premium / spot * 100,
  }
}
