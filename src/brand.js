export const brand = Object.freeze({
  name: "DogePulse",
  slug: "dogepulse",
  asset: "DOGE",
  domain: "dogepulse.app",
  handle: "@DogePulse",
  tagline: "Read the DOGE pulse before you move.",
  supportingLine: "A clear market signal for a noisy coin.",
});
// The new journal has a different schema and asset. Old browser data is left
// untouched; it must never be interpreted as a new DOGE scenario.
export const storageKeys = Object.freeze({ journal: "dogepulse:journal:v1" });
