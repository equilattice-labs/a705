/**
 * Solana runtime configuration and wallet bridge.
 *
 * This module deliberately contains no signer, private key, deployment, or
 * minting code. The application reads public cluster configuration and can
 * ask an injected wallet to display its public address.
 */

import { getWallets } from '@wallet-standard/app'

const viteEnv = import.meta.env || {}

const DEFAULT_RPC_URLS = Object.freeze({
  'mainnet-beta': 'https://api.mainnet-beta.solana.com',
  devnet: 'https://api.devnet.solana.com',
  testnet: 'https://api.testnet.solana.com',
  localnet: 'http://127.0.0.1:8899',
})

// The public LMQR mint is deployed on testnet. Other clusters remain unset.
const DEFAULT_TOKEN_MINTS = Object.freeze({
  'mainnet-beta': null,
  devnet: null,
  testnet: 'EtzFpGbJ4ex4bsaYvviQGWA2NEEa8HMz3oxdxaES5Q7j',
  localnet: null,
})

const CLUSTERS = new Set(Object.keys(DEFAULT_RPC_URLS))
const READ_ONLY_RPC_METHODS = new Set([
  'getBalance', 'getBlock', 'getBlockHeight', 'getEpochInfo', 'getGenesisHash',
  'getHealth', 'getLatestBlockhash', 'getSignatureStatuses', 'getSlot',
  'getTokenAccountBalance', 'getTokenAccountsByOwner', 'getTokenSupply',
  'getTransaction', 'getVersion', 'getAccountInfo', 'getMultipleAccounts',
])
const BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
const BASE58_VALUES = new Map([...BASE58_ALPHABET].map((character, index) => [character, index]))

function normalizeCluster(value) {
  const candidate = String(value || '').trim().toLowerCase()
  if (candidate === 'mainnet' || candidate === 'mainnet-beta') return 'mainnet-beta'
  return CLUSTERS.has(candidate) ? candidate : 'testnet'
}

function decodeBase58(value) {
  if (typeof value !== 'string' || value.length === 0) return null
  let number = 0n
  for (const character of value) {
    const digit = BASE58_VALUES.get(character)
    if (digit === undefined) return null
    number = number * 58n + BigInt(digit)
  }
  const bytes = []
  while (number > 0n) {
    bytes.push(Number(number & 255n))
    number >>= 8n
  }
  for (const character of value) {
    if (character !== '1') break
    bytes.push(0)
  }
  return Uint8Array.from(bytes.reverse())
}

/** Return true for a 32-byte Solana public key encoded as base58. */
export function isValidSolanaAddress(value) {
  const bytes = decodeBase58(value)
  return Boolean(bytes && bytes.length === 32)
}

const cluster = normalizeCluster(viteEnv.VITE_SOLANA_CLUSTER)
const configuredRpcUrl = String(viteEnv.VITE_SOLANA_RPC_URL || '').trim()
const rpcUrl = configuredRpcUrl || DEFAULT_RPC_URLS[cluster]
export function solanaMintEnvironmentName(value) {
  const normalized = normalizeCluster(value)
  return `VITE_SOLANA_${normalized.toUpperCase().replaceAll('-', '_')}_TOKEN_MINT`
}

const mintEnvironmentName = solanaMintEnvironmentName(cluster)
const configuredMint = String(viteEnv[mintEnvironmentName] || '').trim()
export function resolveSolanaTokenMints(env = {}) {
  return Object.freeze(Object.fromEntries(
    [...CLUSTERS].map((name) => {
      const override = String(env[solanaMintEnvironmentName(name)] || '').trim()
      const candidate = override || DEFAULT_TOKEN_MINTS[name]
      return [name, candidate && isValidSolanaAddress(candidate) ? candidate : null]
    }),
  ))
}

const tokenMints = resolveSolanaTokenMints(viteEnv)
const tokenMint = tokenMints[cluster]

/**
 * Public Solana settings. `tokenMint` is selected from the variable for the
 * configured cluster. Deployment is intentionally disabled and cannot be
 * enabled through an environment variable.
 */
export const solanaConfig = Object.freeze({
  cluster,
  rpcUrl,
  mintEnvironmentName,
  tokenMints,
  tokenMint,
  tokenConfigured: Boolean(tokenMint),
  invalidTokenMint: Boolean(configuredMint && !tokenMint),
  deploymentEnabled: false,
  deploymentStatus: 'disabled',
})

export const solanaClusters = Object.freeze([...CLUSTERS])
export const SOLANA_DEPLOYMENT_DISABLED = true

const WALLET_CONNECT = 'standard:connect'
const WALLET_DISCONNECT = 'standard:disconnect'
const WALLET_EVENTS = 'standard:events'
const walletSubscribers = new Set()
let walletRegistry = null
let stopRegistering = () => {}
let stopUnregistering = () => {}
let metaMaskClient = null
let metaMaskSetupError = ''
let walletSetupPromise = null
let activeWallet = null

function registry() {
  if (typeof window === 'undefined') return null
  if (!walletRegistry) {
    walletRegistry = getWallets()
    stopRegistering = walletRegistry.on('register', notifyWalletSubscribers)
    stopUnregistering = walletRegistry.on('unregister', notifyWalletSubscribers)
  }
  return walletRegistry
}

function isStandardSolanaWallet(wallet) {
  return Boolean(
    wallet &&
    Array.isArray(wallet.chains) &&
    wallet.chains.some((chain) => typeof chain === 'string' && chain.startsWith('solana:')) &&
    typeof wallet.features?.[WALLET_CONNECT]?.connect === 'function',
  )
}

function legacySolanaWallets() {
  if (typeof window === 'undefined') return []
  const candidates = [
    ['Phantom', window.phantom?.solana],
    ['Solflare', window.solflare],
    ['Backpack', window.backpack?.solana],
  ]
  const generic = window.solana
  if (generic) {
    const name = generic.isPhantom ? 'Phantom' : generic.isSolflare ? 'Solflare' : 'Solana wallet'
    candidates.push([name, generic])
  }
  const seen = new Set()
  return candidates.flatMap(([name, provider]) => {
    if (!provider || typeof provider.connect !== 'function' || seen.has(provider)) return []
    seen.add(provider)
    return [{
      name,
      icon: provider.icon || '',
      chains: ['solana:testnet'],
      features: {},
      __lumquiraLegacyProvider: provider,
    }]
  })
}

function notifyWalletSubscribers() {
  const wallets = getSolanaWallets()
  walletSubscribers.forEach((listener) => listener(wallets))
}

/**
 * Discover Solana Wallet Standard wallets. This covers current Phantom,
 * Solflare, Backpack and MetaMask Solana accounts while retaining legacy
 * injected-wallet support for older extensions.
 */
export function getSolanaWallets() {
  const standardWallets = registry()?.get().filter(isStandardSolanaWallet) || []
  const standardNames = new Set(standardWallets.map((wallet) => wallet.name.toLowerCase()))
  const legacyWalletsFound = legacySolanaWallets().filter(
    (wallet) => !standardNames.has(wallet.name.toLowerCase()),
  )
  return [...standardWallets, ...legacyWalletsFound]
}

export function watchAvailableSolanaWallets(listener) {
  if (typeof listener !== 'function') return () => {}
  registry()
  walletSubscribers.add(listener)
  listener(getSolanaWallets())
  return () => walletSubscribers.delete(listener)
}

async function createMetaMaskSolanaClient(options) {
  const { createSolanaClient } = await import('@metamask/connect-solana')
  return createSolanaClient(options)
}

/** Register MetaMask with the Wallet Standard and return discovered wallets. */
export async function initializeSolanaWallets({ metaMaskInitializer = createMetaMaskSolanaClient } = {}) {
  const walletRegistryApi = registry()
  if (!walletRegistryApi) return []
  if (!walletSetupPromise) {
    walletSetupPromise = (async () => {
      try {
        const network = cluster === 'mainnet-beta' ? 'mainnet' : cluster
        metaMaskClient = await metaMaskInitializer({
          dapp: { name: 'Lumquira', url: window.location.origin },
          api: { supportedNetworks: network === 'localnet' ? {} : { [network]: rpcUrl } },
          analytics: { enabled: false },
        })
      } catch (error) {
        metaMaskSetupError = error?.message || 'MetaMask Solana support could not initialize.'
      } finally {
        notifyWalletSubscribers()
      }
    })()
  }
  await walletSetupPromise
  return getSolanaWallets()
}

export function getSolanaWalletSetupError() {
  return metaMaskSetupError
}

export function hasSolanaWallet() {
  return getSolanaWallets().length > 0
}

function publicKeyString(value) {
  if (typeof value === 'string') return value
  if (value && typeof value.toString === 'function') return value.toString()
  return ''
}

export class SolanaWalletError extends Error {
  constructor(code, message) {
    super(message)
    this.name = 'SolanaWalletError'
    this.code = code
  }
}

function walletConnectionErrorMessage(error, walletName) {
  const message = typeof error?.message === 'string' ? error.message.trim() : ''
  const normalized = message.toLowerCase()
  if (normalized.includes('timed out') || normalized.includes('timeout')) {
    return `${walletName} did not respond. Open the wallet and approve the Solana connection, then try again.`
  }
  if (['reject', 'denied', 'cancel'].some((term) => normalized.includes(term))) {
    return `The connection was declined in ${walletName}. Approve the Solana request in the wallet to continue.`
  }
  return message || `Could not connect to ${walletName}.`
}

/**
 * Ask the injected wallet for a public account. No transaction is built or
 * signed here, and the result is safe to keep in UI state.
 */
export async function connectSolanaWallet(wallet) {
  if (!wallet) throw new SolanaWalletError('wallet-unavailable', 'Choose a Solana wallet to connect.')
  try {
    const response = wallet.__lumquiraLegacyProvider
      ? await wallet.__lumquiraLegacyProvider.connect()
      : await wallet.features[WALLET_CONNECT].connect()
    const account = response?.accounts?.[0]
    const address = publicKeyString(account?.address || response?.publicKey || wallet.__lumquiraLegacyProvider?.publicKey)
    if (!isValidSolanaAddress(address)) {
      throw new SolanaWalletError('invalid-public-key', 'The wallet returned an invalid Solana address.')
    }
    activeWallet = wallet
    return { address, wallet }
  } catch (error) {
    if (error instanceof SolanaWalletError) throw error
    const message = walletConnectionErrorMessage(error, wallet.name || 'the Solana wallet')
    throw new SolanaWalletError('connect-rejected', message)
  }
}

export async function disconnectSolanaWallet(wallet = activeWallet) {
  if (!wallet) return
  if (wallet.name === 'MetaMask' && typeof metaMaskClient?.disconnect === 'function') {
    await metaMaskClient.disconnect()
    if (activeWallet === wallet) activeWallet = null
    return
  }
  const disconnect = wallet.__lumquiraLegacyProvider?.disconnect || wallet.features?.[WALLET_DISCONNECT]?.disconnect
  if (typeof disconnect === 'function') await disconnect.call(wallet.__lumquiraLegacyProvider || wallet.features[WALLET_DISCONNECT])
  if (activeWallet === wallet) activeWallet = null
}

/** Subscribe to wallet events and return an unsubscribe function. */
export function watchSolanaWallet(listener, wallet = activeWallet) {
  if (!wallet || typeof listener !== 'function') return () => {}
  const standardEvents = wallet.features?.[WALLET_EVENTS]
  if (typeof standardEvents?.on === 'function') {
    return standardEvents.on('change', (change) => {
      const account = change?.accounts?.[0]
      listener(account ? { address: account.address, accounts: change.accounts } : null)
    })
  }
  const provider = wallet.__lumquiraLegacyProvider
  if (!provider || typeof provider.on !== 'function') return () => {}
  const onConnect = (event) => listener(event?.publicKey || provider.publicKey || null)
  const onDisconnect = () => listener(null)
  const onAccountChanged = (account) => listener(account || null)
  provider.on('connect', onConnect)
  provider.on('disconnect', onDisconnect)
  provider.on('accountChanged', onAccountChanged)
  return () => {
    const remove = provider.off || provider.removeListener
    if (typeof remove !== 'function') return
    remove.call(provider, 'connect', onConnect)
    remove.call(provider, 'disconnect', onDisconnect)
    remove.call(provider, 'accountChanged', onAccountChanged)
  }
}

/**
 * Minimal JSON-RPC helper for public reads. It never accepts a secret key and
 * intentionally omits sendTransaction/deploy helpers until the token is known.
 */
export async function solanaRpcRequest(method, params = [], { fetchImpl = globalThis.fetch, signal } = {}) {
  if (typeof fetchImpl !== 'function') throw new Error('Fetch is unavailable in this environment.')
  if (!READ_ONLY_RPC_METHODS.has(method)) throw new Error(`Solana RPC method is not allowed: ${method}.`)
  const response = await fetchImpl(solanaConfig.rpcUrl, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ jsonrpc: '2.0', id: Date.now(), method, params }),
    signal,
  })
  if (!response.ok) throw new Error(`Solana RPC request failed (${response.status}).`)
  const payload = await response.json()
  if (payload?.error) throw new Error(payload.error.message || 'Solana RPC returned an error.')
  return payload?.result
}

export function solanaExplorerAddress(address, network = solanaConfig.cluster) {
  if (!isValidSolanaAddress(address)) return null
  const explorerCluster = normalizeCluster(network)
  const suffix = explorerCluster === 'mainnet-beta' ? '' : `?cluster=${encodeURIComponent(explorerCluster)}`
  return `https://explorer.solana.com/address/${address}${suffix}`
}

export function solanaExplorerToken(network = solanaConfig.cluster) {
  const explorerCluster = normalizeCluster(network)
  const mint = solanaConfig.tokenMints[explorerCluster]
  return mint ? solanaExplorerAddress(mint, explorerCluster) : null
}
