import test from 'node:test'
import assert from 'node:assert/strict'
import { getWallets } from '@wallet-standard/app'
import { connectSolanaWallet, disconnectSolanaWallet, getSolanaWallets, initializeSolanaWallets, isValidSolanaAddress, resolveSolanaTokenMints, solanaConfig, solanaExplorerAddress, solanaExplorerToken, solanaMintEnvironmentName, solanaRpcRequest, watchAvailableSolanaWallets, watchSolanaWallet } from '../src/solana.js'

const VALID_ADDRESS = '11111111111111111111111111111111'

test('Solana defaults to the deployed testnet mint and cannot deploy in the browser', () => {
  assert.equal(solanaConfig.cluster, 'testnet')
  assert.equal(solanaConfig.mintEnvironmentName, 'VITE_SOLANA_TESTNET_TOKEN_MINT')
  assert.equal(solanaConfig.tokenMints.devnet, null)
  assert.equal(solanaConfig.tokenMints.testnet, 'EtzFpGbJ4ex4bsaYvviQGWA2NEEa8HMz3oxdxaES5Q7j')
  assert.equal(solanaConfig.tokenMint, 'EtzFpGbJ4ex4bsaYvviQGWA2NEEa8HMz3oxdxaES5Q7j')
  assert.equal(solanaConfig.tokenConfigured, true)
  assert.equal(solanaConfig.deploymentEnabled, false)
  assert.equal(solanaExplorerToken(), 'https://explorer.solana.com/address/EtzFpGbJ4ex4bsaYvviQGWA2NEEa8HMz3oxdxaES5Q7j?cluster=testnet')
})

test('each supported cluster resolves to an isolated public mint setting', () => {
  assert.equal(solanaMintEnvironmentName('devnet'), 'VITE_SOLANA_DEVNET_TOKEN_MINT')
  assert.equal(solanaMintEnvironmentName('testnet'), 'VITE_SOLANA_TESTNET_TOKEN_MINT')
  assert.equal(solanaMintEnvironmentName('mainnet-beta'), 'VITE_SOLANA_MAINNET_BETA_TOKEN_MINT')
  assert.equal(solanaMintEnvironmentName('unknown'), 'VITE_SOLANA_TESTNET_TOKEN_MINT')
  const configured = resolveSolanaTokenMints({
    VITE_SOLANA_DEVNET_TOKEN_MINT: VALID_ADDRESS,
    VITE_SOLANA_TESTNET_TOKEN_MINT: 'bad',
  })
  assert.equal(configured.devnet, VALID_ADDRESS)
  assert.equal(configured.testnet, null)
  assert.equal(configured['mainnet-beta'], null)
})

test('verified testnet mint links use the testnet explorer and allow a public env override', () => {
  const mint = 'EtzFpGbJ4ex4bsaYvviQGWA2NEEa8HMz3oxdxaES5Q7j'
  assert.equal(solanaConfig.tokenMints.testnet, mint)
  assert.equal(solanaExplorerToken('testnet'), `https://explorer.solana.com/address/${mint}?cluster=testnet`)
  assert.equal(resolveSolanaTokenMints({ VITE_SOLANA_TESTNET_TOKEN_MINT: VALID_ADDRESS }).testnet, VALID_ADDRESS)
})

test('base58 address and explorer helpers reject malformed account strings', () => {
  assert.equal(isValidSolanaAddress(VALID_ADDRESS), true)
  assert.equal(isValidSolanaAddress('1111111111111111111111111111111'), false)
  assert.equal(isValidSolanaAddress('0'.repeat(32)), false)
  assert.equal(solanaExplorerAddress('invalid'), null)
  assert.equal(solanaExplorerAddress(VALID_ADDRESS), `https://explorer.solana.com/address/${VALID_ADDRESS}?cluster=testnet`)
  assert.equal(solanaExplorerAddress(VALID_ADDRESS, 'testnet'), `https://explorer.solana.com/address/${VALID_ADDRESS}?cluster=testnet`)
})

function mockStandardWallet(name = 'MetaMask') {
  const listeners = new Set()
  let disconnected = false
  const wallet = {
    name,
    icon: 'data:image/svg+xml,<svg></svg>',
    chains: ['solana:4uhcVJyU9pJkvQyS88uRDiswHXSCkY3z'],
    features: {
      'standard:connect': {
        version: '1.0.0',
        connect: async () => ({ accounts: [{ address: VALID_ADDRESS }] }),
      },
      'standard:disconnect': {
        version: '1.0.0',
        disconnect: async () => { disconnected = true },
      },
      'standard:events': {
        version: '1.0.0',
        on: (_event, listener) => {
          listeners.add(listener)
          return () => listeners.delete(listener)
        },
      },
    },
  }
  return {
    wallet,
    disconnected: () => disconnected,
    emit: (event) => listeners.forEach((listener) => listener(event)),
    listenerCount: () => listeners.size,
  }
}

test('MetaMask Solana connector registers a testnet wallet through Wallet Standard', async () => {
  const previousWindow = globalThis.window
  const browserWindow = new EventTarget()
  browserWindow.location = { origin: 'https://lumquira.xyz' }
  globalThis.window = browserWindow
  const standardWallet = mockStandardWallet('MetaMask')
  const registry = getWallets()
  let unregister = () => {}
  let config
  let clientDisconnected = false
  let updates = []
  const stopUpdates = watchAvailableSolanaWallets((wallets) => { updates.push(wallets.map((wallet) => wallet.name)) })
  try {
    const available = await initializeSolanaWallets({
      metaMaskInitializer: async (options) => {
        config = options
        unregister = registry.register(standardWallet.wallet)
        return {
          getWallet: () => standardWallet.wallet,
          disconnect: async () => { clientDisconnected = true },
        }
      },
    })
    assert.equal(available.some((wallet) => wallet.name === 'MetaMask'), true)
    assert.deepEqual(config.api.supportedNetworks, { testnet: 'https://api.testnet.solana.com' })
    assert.equal(config.analytics.enabled, false)
    assert.equal(updates.some((names) => names.includes('MetaMask')), true)
    const connected = await connectSolanaWallet(standardWallet.wallet)
    assert.equal(connected.address, VALID_ADDRESS)
    const events = []
    const stop = watchSolanaWallet((event) => events.push(event), standardWallet.wallet)
    standardWallet.emit({ accounts: [{ address: '11111111111111111111111111111112' }] })
    standardWallet.emit({ accounts: [] })
    assert.deepEqual(events, [
      { address: '11111111111111111111111111111112', accounts: [{ address: '11111111111111111111111111111112' }] },
      null,
    ])
    stop()
    assert.equal(standardWallet.listenerCount(), 0)
    await disconnectSolanaWallet(standardWallet.wallet)
    assert.equal(clientDisconnected, true)
  } finally {
    stopUpdates()
    unregister()
    if (previousWindow === undefined) delete globalThis.window
    else globalThis.window = previousWindow
  }
})

test('legacy Phantom injection stays available and invalid wallet addresses are rejected', async () => {
  const previousWindow = globalThis.window
  const provider = {
    publicKey: null,
    connect: async () => ({ publicKey: { toString: () => 'bad' } }),
    disconnect: async () => {},
  }
  try {
    globalThis.window = {}
    assert.equal(getSolanaWallets().length, 0)
    globalThis.window = { phantom: { solana: provider } }
    const phantom = getSolanaWallets().find((wallet) => wallet.name === 'Phantom')
    assert.ok(phantom)
    await assert.rejects(connectSolanaWallet(phantom), (error) => error.code === 'invalid-public-key')
  } finally {
    if (previousWindow === undefined) delete globalThis.window
    else globalThis.window = previousWindow
  }
})

test('wallet connection timeouts show actionable retry guidance', async () => {
  const { wallet } = mockStandardWallet('MetaMask')
  wallet.features['standard:connect'].connect = async () => {
    throw new Error('Transport request timed out')
  }
  await assert.rejects(
    connectSolanaWallet(wallet),
    (error) => error.code === 'connect-rejected' && /Open the wallet and approve the Solana connection/.test(error.message),
  )
})

test('RPC helper restricts requests to public read methods', async () => {
  let called = false
  await assert.rejects(
    solanaRpcRequest('sendTransaction', [], { fetchImpl: async () => { called = true } }),
    /not allowed/,
  )
  assert.equal(called, false)
  let request
  const result = await solanaRpcRequest('getBalance', [VALID_ADDRESS], {
    fetchImpl: async (url, options) => {
      request = { url, ...options, body: JSON.parse(options.body) }
      return { ok: true, json: async () => ({ jsonrpc: '2.0', result: { value: 42 } }) }
    },
  })
  assert.equal(request.url, solanaConfig.rpcUrl)
  assert.equal(request.method, 'POST')
  assert.equal(request.body.method, 'getBalance')
  assert.deepEqual(request.body.params, [VALID_ADDRESS])
  assert.deepEqual(result, { value: 42 })
  await assert.rejects(solanaRpcRequest('getSlot', [], { fetchImpl: async () => ({ ok: false, status: 503 }) }), /503/)
  await assert.rejects(solanaRpcRequest('getSlot', [], { fetchImpl: async () => ({ ok: true, json: async () => ({ error: { message: 'RPC unavailable' } }) }) }), /RPC unavailable/)
})
