// Concept copy for the Scenovia market model.
export const concepts = [
  {
    "id": "asset-backing",
    "title": "Asset Backing",
    "description": "The Stock Token is locked in the series vault to back the payoff. No margin, no funding rate, no liquidation engine.",
    "image": "/stack.webp"
  },
  {
    "id": "asset-distinction",
    "title": "Asset Distinction",
    "description": "Positions are created from Stock Tokens and carry Income or Upside exposure. The protocol token is separate from them.",
    "image": "/token.webp"
  },
  {
    "id": "defined-cap",
    "title": "Defined Cap",
    "description": "K = P0 × (1 + cap). Upside pays nothing at or below K and the amount above it.",
    "image": "/hero.webp"
  },
  {
    "id": "income-position",
    "title": "Income Position",
    "description": "Accept an upside cap for a defined period. Receive the premium paid by the upside buyer. Underlying downside exposure remains.",
    "image": "/network.webp"
  },
  {
    "id": "market-epochs",
    "title": "Market Epochs",
    "description": "Each epoch records a starting price and a cap. Monthly, settling on the third Friday; 28 or 35 days each.",
    "image": "/hero.webp"
  },
  {
    "id": "market-structure",
    "title": "Market Structure",
    "description": "One Stock Token, one epoch, one cap per series. Income earns the premium; Upside buys the move above the cap.",
    "image": "/stack.webp"
  },
  {
    "id": "oracle-settlement",
    "title": "Oracle Settlement",
    "description": "A 30-minute average of the Chainlink feed inside the regular session sets the value allocated to each side.",
    "image": "/network.webp"
  },
  {
    "id": "outcome-scenarios",
    "title": "Outcome Scenarios",
    "description": "Start $250, cap $262.50. At $200 or $250 Upside pays nothing. At $300 Upside pays $37.50; Income keeps $262.50 plus the premium.",
    "image": "/token.webp"
  },
  {
    "id": "position-redemption",
    "title": "Position Redemption",
    "description": "One Income position plus one Upside position of the same series merge back into one Stock Token at any time, free.",
    "image": "/stack.webp"
  },
  {
    "id": "premium-exchange",
    "title": "Premium Exchange",
    "description": "The upside buyer pays a premium in a descending-clock auction. The proceeds are credited to the Income side.",
    "image": "/hero.webp"
  },
  {
    "id": "protocol-revenue",
    "title": "Protocol Revenue",
    "description": "One fee: 5 % of gross auction proceeds, in USDG. Split, merge and settlement claims are free.",
    "image": "/network.webp"
  },
  {
    "id": "risk-perspective",
    "title": "Risk Perspective",
    "description": "Income still bears the downside of the Stock Token. The upside buyer can lose the premium paid.",
    "image": "/token.webp"
  },
  {
    "id": "tokenized-markets",
    "title": "Tokenized Markets",
    "description": "Stock Tokens on Robinhood Chain. A token with a Chainlink feed and a USDG pool can be listed.",
    "image": "/hero.webp"
  },
  {
    "id": "token-utility",
    "title": "Token Utility",
    "description": "SCNV is a proposed symbol only. No token has been issued and no production utility is enabled in this preview.",
    "image": "/icon.svg"
  },
  {
    "id": "upside-position",
    "title": "Upside Position",
    "description": "Pay a premium for exposure above a defined level. The position can expire without a payoff.",
    "image": "/token.webp"
  }
]
