<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, shallowRef } from 'vue'
import { ExternalLink, ShieldCheck, Wallet, X } from 'lucide-vue-next'
import {
  connectSolanaWallet,
  disconnectSolanaWallet,
  getSolanaWalletSetupError,
  getSolanaWallets,
  initializeSolanaWallets,
  watchAvailableSolanaWallets,
  watchSolanaWallet,
} from '../solana.js'

const emit = defineEmits(['connected', 'disconnected'])
const wallets = shallowRef([])
const activeWallet = shallowRef(null)
const address = ref('')
const modalOpen = ref(false)
const discovering = ref(false)
const pendingWallet = ref('')
const errorMessage = ref('')
const setupMessage = ref('')
const dialogPanel = ref(null)
let stopWalletDiscovery = () => {}
let stopWalletEvents = () => {}
let returnFocus = null

const shortAddress = computed(() => address.value ? address.value.slice(0, 5) + '...' + address.value.slice(-5) : '')
const buttonLabel = computed(() => address.value ? shortAddress.value : 'Connect wallet')

function showModal() {
  returnFocus = document.activeElement
  modalOpen.value = true
  errorMessage.value = ''
  setupMessage.value = ''
  wallets.value = getSolanaWallets()
  discovering.value = true
  void nextTick(() => dialogPanel.value?.querySelector('.wallet-dialog-close')?.focus())
  void initializeSolanaWallets()
    .then((available) => {
      wallets.value = available
      setupMessage.value = getSolanaWalletSetupError()
    })
    .catch((error) => {
      setupMessage.value = error?.message || 'Wallet discovery could not start.'
    })
    .finally(() => { discovering.value = false })
}

function closeModal() {
  modalOpen.value = false
  void nextTick(() => returnFocus?.focus?.())
}

function onDialogKeydown(event) {
  if (event.key === 'Escape') {
    event.preventDefault()
    closeModal()
    return
  }
  if (event.key !== 'Tab' || !dialogPanel.value) return
  const focusable = [...dialogPanel.value.querySelectorAll('button:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])')]
  if (!focusable.length) return
  const first = focusable[0]
  const last = focusable[focusable.length - 1]
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

function syncAddress(nextAddress) {
  const value = typeof nextAddress === 'string' ? nextAddress : nextAddress?.address || ''
  address.value = value
  if (!value) {
    activeWallet.value = null
    stopWalletEvents()
    stopWalletEvents = () => {}
    emit('disconnected')
  } else {
    emit('connected', value, activeWallet.value?.name || '')
  }
}

async function connect(wallet) {
  pendingWallet.value = wallet.name
  errorMessage.value = ''
  try {
    const result = await connectSolanaWallet(wallet)
    stopWalletEvents()
    activeWallet.value = result.wallet
    syncAddress(result.address)
    stopWalletEvents = watchSolanaWallet((event) => {
      const next = event?.accounts?.[0]?.address || event?.address || event?.publicKey?.toString?.() || event?.toString?.() || ''
      syncAddress(next)
    }, result.wallet)
  } catch (error) {
    errorMessage.value = error?.message || `Could not connect to ${wallet.name}.`
  } finally {
    pendingWallet.value = ''
  }
}

async function disconnect() {
  pendingWallet.value = activeWallet.value?.name || 'wallet'
  errorMessage.value = ''
  try {
    await disconnectSolanaWallet(activeWallet.value)
    syncAddress('')
    closeModal()
  } catch (error) {
    errorMessage.value = error?.message || 'Wallet could not disconnect.'
  } finally {
    pendingWallet.value = ''
  }
}

onMounted(() => {
  stopWalletDiscovery = watchAvailableSolanaWallets((available) => { wallets.value = available })
})

onBeforeUnmount(() => {
  stopWalletDiscovery()
  stopWalletEvents()
})
</script>

<template>
  <div class="solana-wallet-control">
    <button
      type="button"
      class="wallet-button"
      :class="{ connected: address }"
      :aria-haspopup="'dialog'"
      :aria-expanded="modalOpen"
      :disabled="Boolean(pendingWallet)"
      @click="showModal"
    >
      <Wallet :size="16" />
      {{ pendingWallet ? 'Connecting…' : buttonLabel }}
    </button>

    <Teleport to="body">
      <div v-if="modalOpen" class="solana-wallet-backdrop" @click.self="closeModal" @keydown.esc.stop="closeModal">
        <section ref="dialogPanel" class="solana-wallet-dialog" role="dialog" aria-modal="true" aria-labelledby="wallet-dialog-title" tabindex="-1" @keydown.stop="onDialogKeydown">
          <header class="wallet-dialog-header">
            <div>
              <span class="eyebrow">SOLANA / TESTNET</span>
              <h2 id="wallet-dialog-title">{{ address ? 'Wallet connected' : 'Choose a wallet' }}</h2>
            </div>
            <button class="wallet-dialog-close" type="button" aria-label="Close wallet dialog" @click="closeModal"><X :size="18" /></button>
          </header>

          <div v-if="address" class="wallet-account-card">
            <span class="wallet-account-name"><Wallet :size="16" /> {{ activeWallet?.name || 'Solana wallet' }}</span>
            <code>{{ address }}</code>
            <button class="wallet-disconnect" type="button" :disabled="Boolean(pendingWallet)" @click="disconnect">
              {{ pendingWallet ? 'Disconnecting…' : 'Disconnect wallet' }}
            </button>
          </div>

          <template v-else>
            <p class="wallet-dialog-copy">Connect a Solana account to display its public address. This site does not ask for transaction signatures.</p>
            <p class="wallet-network-note"><ShieldCheck :size="15" /> Use a Solana account on MetaMask; an Ethereum-only account cannot connect to Solana.</p>

            <p v-if="discovering" class="wallet-discovery" role="status">Looking for MetaMask, Phantom, Solflare and other Solana wallets…</p>
            <div v-else-if="wallets.length" class="wallet-options" aria-label="Available Solana wallets">
              <button v-for="wallet in wallets" :key="wallet.name" class="wallet-option" type="button" :disabled="Boolean(pendingWallet)" @click="connect(wallet)">
                <img v-if="wallet.icon" class="wallet-option-icon" :src="wallet.icon" alt="" />
                <span v-else class="wallet-option-icon wallet-option-placeholder"><Wallet :size="18" /></span>
                <span class="wallet-option-name">{{ wallet.name }}</span>
                <span v-if="pendingWallet === wallet.name" class="wallet-option-state">Connecting…</span>
                <ExternalLink v-else :size="15" class="wallet-option-arrow" />
              </button>
            </div>
            <div v-else class="wallet-empty-state">
              <p>No compatible Solana wallet was detected.</p>
              <p class="wallet-empty-help">Install a wallet, enable its Solana account, then reopen this panel.</p>
              <div class="wallet-install-links">
                <a href="https://metamask.io/download/" target="_blank" rel="noreferrer">MetaMask <ExternalLink :size="12" /></a>
                <a href="https://phantom.app/download" target="_blank" rel="noreferrer">Phantom <ExternalLink :size="12" /></a>
                <a href="https://solflare.com/download" target="_blank" rel="noreferrer">Solflare <ExternalLink :size="12" /></a>
              </div>
            </div>
          </template>

          <p v-if="errorMessage" class="wallet-dialog-error" role="alert">{{ errorMessage }}</p>
          <p v-if="setupMessage" class="wallet-dialog-setup" role="status">MetaMask connector: {{ setupMessage }}</p>
          <p class="wallet-dialog-footnote">Only the selected wallet’s public Solana address is read.</p>
        </section>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.solana-wallet-backdrop { position: fixed; inset: 0; z-index: 50; display: grid; place-items: center; padding: 20px; background: rgba(3, 6, 9, .76); backdrop-filter: blur(9px); }
.solana-wallet-dialog { width: min(100%, 440px); max-height: min(680px, calc(100vh - 40px)); overflow: auto; padding: 25px; color: var(--ink, #f2f4f7); background: #10151b; border: 1px solid #33404c; border-radius: 14px; box-shadow: 0 26px 90px rgba(0,0,0,.48); }
.wallet-dialog-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.wallet-dialog-header h2 { margin: 9px 0 0; font: 29px/1.05 var(--serif, Georgia, serif); }
.wallet-dialog-close { display: grid; place-items: center; width: 36px; height: 36px; color: #cad0d7; background: #1b232b; border: 1px solid #33404c; border-radius: 8px; cursor: pointer; }
.wallet-dialog-copy { margin: 22px 0 12px; color: #aab4bf; font-size: 13px; line-height: 1.6; }
.wallet-network-note { display: flex; align-items: flex-start; gap: 8px; margin: 0 0 20px; padding: 11px 12px; color: #c5d8b6; background: rgba(183,243,107,.07); border: 1px solid rgba(183,243,107,.18); border-radius: 8px; font-size: 11px; line-height: 1.5; }
.wallet-network-note svg { flex: 0 0 auto; color: var(--lime, #b7f36b); }
.wallet-discovery { padding: 18px 0; color: #aab4bf; font-size: 13px; }
.wallet-options { display: grid; gap: 9px; }
.wallet-option { display: flex; align-items: center; min-height: 58px; gap: 12px; padding: 9px 12px; color: #f2f4f7; text-align: left; background: #171e25; border: 1px solid #303b46; border-radius: 9px; cursor: pointer; }
.wallet-option:hover:not(:disabled) { border-color: var(--lime, #b7f36b); background: #1b2528; }
.wallet-option:disabled, .wallet-disconnect:disabled { opacity: .58; cursor: wait; }
.wallet-option-icon { display: grid; place-items: center; width: 36px; height: 36px; object-fit: contain; border-radius: 8px; }
.wallet-option-placeholder { color: var(--lime, #b7f36b); background: #28332a; }
.wallet-option-name { font-weight: 650; font-size: 13px; }
.wallet-option-state, .wallet-option-arrow { margin-left: auto; color: #98a4af; font-size: 11px; }
.wallet-option-arrow { color: var(--lime, #b7f36b); }
.wallet-empty-state { padding: 7px 0 2px; }
.wallet-empty-state p { margin: 0 0 7px; color: #e6e9ed; font-size: 13px; }
.wallet-empty-state .wallet-empty-help { color: #9ba6b2; font-size: 11px; line-height: 1.5; }
.wallet-install-links { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 15px; }
.wallet-install-links a { display: inline-flex; align-items: center; gap: 5px; padding: 8px 10px; color: var(--lime, #b7f36b); background: #1b2329; border: 1px solid #303b46; border-radius: 7px; font-size: 11px; text-decoration: none; }
.wallet-account-card { display: grid; gap: 15px; margin-top: 22px; padding: 16px; background: #171e25; border: 1px solid #303b46; border-radius: 9px; }
.wallet-account-name { display: flex; align-items: center; gap: 8px; color: var(--lime, #b7f36b); font-size: 12px; }
.wallet-account-card code { overflow-wrap: anywhere; color: #e0e5ea; font-size: 12px; }
.wallet-disconnect { min-height: 38px; color: #ffaaa4; background: rgba(255,117,109,.07); border: 1px solid rgba(255,117,109,.3); border-radius: 7px; cursor: pointer; font: inherit; font-size: 12px; }
.wallet-dialog-error, .wallet-dialog-setup { margin: 14px 0 0; color: #ffaaa4; font-size: 11px; line-height: 1.5; overflow-wrap: anywhere; }
.wallet-dialog-setup { color: #d8c991; }
.wallet-dialog-footnote { margin: 18px 0 0; padding-top: 14px; color: #798591; border-top: 1px solid #27313a; font: 10px/1.5 var(--mono, monospace); }
@media (max-width: 480px) { .solana-wallet-backdrop { padding: 12px; }.solana-wallet-dialog { padding: 20px; border-radius: 12px; }.wallet-dialog-header h2 { font-size: 26px; } }
</style>
