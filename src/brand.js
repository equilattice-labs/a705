export const brand = Object.freeze({
  name: "Zecpass",
  slug: "zecpass",
  ticker: "$ZECPASS",
  domain: "zecpass.app",
  handle: "@ZecPass",
  tagline: "The pass from Zcash to Robinhood Chain.",
  supportingLine: "Buy in private, hold in the open.",
});

export const storageKeys = Object.freeze({
  order: "zecpass:order",
  email: "zecpass:email",
  session: "zecpass:session",
  journal: "zecpass:journal",
});

// Compatibility aliases are read only during local migration. They preserve
// browser data created before the Zecpass rebrand without exposing old names
// in the product interface.
export const legacyStorageKeys = Object.freeze([
  "scenarill:",
  "premicairn:",
  "thesivellum:",
  "evidune:",
  "folivect:",
  "decisift:",
  "stockorbit:",
]);

export function migrateBrandStorage(storage) {
  const migrated = [];
  if (storage === undefined) {
    try { storage = globalThis.localStorage; } catch { return { migrated, error: "Browser storage is unavailable." }; }
  }
  if (!storage) return { migrated };
  const targets = [storageKeys.order, storageKeys.email, storageKeys.session, storageKeys.journal];
  const legacyPrefixes = ["zecpass.", ...legacyStorageKeys];
  try {
    for (const target of targets) {
      if (storage.getItem(target) !== null) continue;
      for (const prefix of legacyPrefixes) {
        const legacyKey = `${prefix}${target.slice(target.indexOf(":") + 1)}`;
        const value = storage.getItem(legacyKey);
        if (value === null) continue;
        storage.setItem(target, value);
        migrated.push({ from: legacyKey, to: target });
        break;
      }
    }
  } catch {
    return { migrated, error: "Browser storage is unavailable." };
  }
  return { migrated };
}
