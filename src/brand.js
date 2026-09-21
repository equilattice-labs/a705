export const brand = Object.freeze({
  name: "Scenarill",
  slug: "scenarill",
  domain: "scenarill.xyz",
  handle: "@scenarill",
  tagline: "Explore the branches. Keep the reasoning.",
});

export const storageKeys = Object.freeze({
  session: "scenarill:session",
  email: "scenarill:beta-email",
  journal: "scenarill:journal",
});

function validPreference(key, value) {
  if (key === storageKeys.email)
    return typeof value === "string" && /^\S+@\S+\.\S+$/.test(value);
  try {
    const session = JSON.parse(value);
    return (
      /^0x[0-9a-f]{40}$/i.test(session?.account || "") &&
      session.chainId === 4663 &&
      Number.isFinite(session.signedAt)
    );
  } catch {
    return false;
  }
}

function readJournal(raw) {
  const entries = JSON.parse(raw);
  if (
    !Array.isArray(entries) ||
    !entries.every(
      (entry) =>
        entry &&
        typeof entry.id === "string" &&
        ["AAPL", "NVDA", "TSLA", "AMZN"].includes(entry.symbol) &&
        ["bear", "base", "bull"].includes(entry.scenario) &&
        Number.isFinite(entry.weight) &&
        entry.weight >= 1 &&
        entry.weight <= 50 &&
        Number.isFinite(entry.savedAt) &&
        !Number.isNaN(new Date(entry.savedAt).getTime()) &&
        typeof entry.thesis === "string" &&
        typeof entry.note === "string",
    )
  )
    throw new Error("Unreadable journal");
  return entries;
}

// Compatibility identifiers only. Never use these as product display names.
export function migrateBrandStorage() {
  for (const [storageName, previousKeys, nextKey] of [
    [
      "sessionStorage",
      [
        "premicairn:session",
        "thesivellum:session",
        "evidune:session",
        "folivect:session",
        "decisift:session",
        "stockorbit:session",
      ],
      storageKeys.session,
    ],
    [
      "localStorage",
      [
        "premicairn:beta-email",
        "thesivellum:beta-email",
        "evidune:beta-email",
        "folivect:beta-email",
        "decisift:beta-email",
        "stockorbit:beta-email",
      ],
      storageKeys.email,
    ],
  ]) {
    for (const previousKey of previousKeys) {
      try {
        const storage = window[storageName];
        const value = storage.getItem(previousKey);
        if (value === null || !validPreference(nextKey, value)) continue;
        if (!validPreference(nextKey, storage.getItem(nextKey)))
          storage.setItem(nextKey, value);
        if (validPreference(nextKey, storage.getItem(nextKey)))
          storage.removeItem(previousKey);
      } catch {
        /* The relevant action reports a storage failure when used. */
      }
    }
  }
  try {
    const storage = window.localStorage;
    for (const previousKey of [
      "premicairn:journal",
      "thesivellum:journal",
      "evidune:journal",
      "folivect:journal",
      "decisift:journal",
      "stockorbit:journal",
    ]) {
      const previous = storage.getItem(previousKey);
      if (previous === null) continue;
      const oldEntries = readJournal(previous);
      const existing = storage.getItem(storageKeys.journal);
      const currentEntries = existing === null ? [] : readJournal(existing);
      const ids = new Set(currentEntries.map((entry) => entry.id));
      const merged = [...currentEntries];
      for (const entry of oldEntries) {
        if (!ids.has(entry.id)) {
          merged.push(entry);
          ids.add(entry.id);
        }
      }
      const serialized = JSON.stringify(merged);
      storage.setItem(storageKeys.journal, serialized);
      if (storage.getItem(storageKeys.journal) !== serialized)
        throw new Error("Journal write not verified");
      storage.removeItem(previousKey);
    }
    return { journalError: "" };
  } catch {
    return {
      journalError:
        "Your existing journal could not be transferred. Its records have been kept. Allow browser storage or restore readable journal data, then retry.",
    };
  }
}
