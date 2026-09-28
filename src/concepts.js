// Illustrative mechanics for the Solana market model.
export const concepts = [
  {
    id: 'backing',
    title: 'Asset backing',
    description: 'A reference series starts with one SPL market unit held against the modeled positions. This preview does not create or custody an asset.',
    image: '/concept-backing.webp',
  },
  {
    id: 'cap',
    title: 'Cap boundary',
    description: 'The cap K is calculated from a starting price and a chosen rate. The payoff explorer shows the modeled value on either side of K.',
    image: '/concept-cap.webp',
  },
  {
    id: 'settlement',
    title: 'Settlement split',
    description: 'At the assumed settlement price, Upside receives value above K and Income retains value up to K plus any hypothetical auction premium.',
    image: '/concept-settlement.webp',
  },
]
