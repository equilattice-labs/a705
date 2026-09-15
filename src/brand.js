export const storageKeys = Object.freeze({ session: 'decisift:session', email: 'decisift:beta-email' })

function isValid(key, value) {
  if (key === storageKeys.email) return typeof value === 'string' && /^\S+@\S+\.\S+$/.test(value)
  try {
    const session = JSON.parse(value)
    return /^0x[0-9a-f]{40}$/i.test(session?.account || '') && session.chainId === 4663 && Number.isFinite(session.signedAt)
  } catch { return false }
}

// Compatibility only: preserve existing local preferences across the brand rename.
export function migrateBrandStorage() {
  for (const [storageName, oldKey, newKey] of [
    ['sessionStorage', 'stockorbit:session', storageKeys.session],
    ['localStorage', 'stockorbit:beta-email', storageKeys.email],
  ]) {
    try {
      const storage = window[storageName]
      const oldValue = storage.getItem(oldKey)
      if (oldValue !== null) {
        if (!isValid(newKey, storage.getItem(newKey)) && isValid(newKey, oldValue)) storage.setItem(newKey, oldValue)
        if (isValid(newKey, storage.getItem(newKey))) storage.removeItem(oldKey)
      }
    } catch { /* Storage may be disabled. The UI remains usable. */ }
  }
}
