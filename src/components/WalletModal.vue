<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { ArrowRight, Check, ExternalLink, LoaderCircle, ShieldCheck, Wallet, X } from 'lucide-vue-next'

const props = defineProps({ open: Boolean })
const emit = defineEmits(['close', 'connected', 'session-invalidated'])
const stage = ref('idle')
const error = ref('')
const account = ref('')
const pending = ref(false)
const dialog = ref(null)
const title = ref(null)
const primaryAction = ref(null)
let returnFocus = null
let previousOverflow = ''
let operation = 0
let provider = null
let scrollLocked = false

const shortAccount = computed(() => account.value ? `${account.value.slice(0, 6)}…${account.value.slice(-4)}` : '')
const network = {
  chainId: '0x1237',
  chainName: 'Robinhood Chain',
  nativeCurrency: { name: 'Ether', symbol: 'ETH', decimals: 18 },
  rpcUrls: ['https://rpc.mainnet.chain.robinhood.com/'],
  blockExplorerUrls: ['https://robinhoodchain.blockscout.com'],
}

function isCurrent(id) { return id === operation && props.open }

function close() {
  operation += 1
  emit('close')
}

function resetSession() {
  account.value = ''
  stage.value = 'idle'
  try { sessionStorage.removeItem('decisift:session') } catch { /* Parent also clears its in-memory session. */ }
  emit('session-invalidated')
}

function providerChanged() {
  // A network switch is expected while connecting; all request results are rechecked.
  if (pending.value || !props.open || !['ready', 'complete'].includes(stage.value)) return
  resetSession()
  error.value = 'Your wallet account or network changed. Connect again to continue.'
}

function detachProvider() {
  provider?.removeListener?.('accountsChanged', providerChanged)
  provider?.removeListener?.('chainChanged', providerChanged)
  provider?.removeListener?.('disconnect', providerChanged)
}

function attachProvider(nextProvider) {
  if (provider === nextProvider) return
  detachProvider()
  provider = nextProvider
  provider.on?.('accountsChanged', providerChanged)
  provider.on?.('chainChanged', providerChanged)
  provider.on?.('disconnect', providerChanged)
}

async function ensureNetwork(wallet, id) {
  const chain = await wallet.request({ method: 'eth_chainId' })
  if (!isCurrent(id)) return
  if (String(chain).toLowerCase() === network.chainId) return
  try {
    await wallet.request({ method: 'wallet_switchEthereumChain', params: [{ chainId: network.chainId }] })
  } catch (cause) {
    if (Number(cause?.code) !== 4902) throw cause
    if (!isCurrent(id)) return
    await wallet.request({ method: 'wallet_addEthereumChain', params: [network] })
    if (!isCurrent(id)) return
    const addedChain = await wallet.request({ method: 'eth_chainId' })
    if (!isCurrent(id)) return
    if (String(addedChain).toLowerCase() !== network.chainId) {
      await wallet.request({ method: 'wallet_switchEthereumChain', params: [{ chainId: network.chainId }] })
    }
  }
}

async function verifyContext(wallet, expectedAccount) {
  const [accounts, chain] = await Promise.all([
    wallet.request({ method: 'eth_accounts' }),
    wallet.request({ method: 'eth_chainId' }),
  ])
  if (String(chain).toLowerCase() !== network.chainId) throw new Error('Switch to Robinhood Chain (4663), then reconnect.')
  if (!Array.isArray(accounts) || !/^0x[0-9a-f]{40}$/i.test(accounts[0] || '')) throw new Error('No wallet account is available. Unlock your wallet and reconnect.')
  if (expectedAccount && accounts[0].toLowerCase() !== expectedAccount.toLowerCase()) throw new Error('Your active wallet account changed. Reconnect before signing in.')
  return accounts[0]
}

function explainError(cause, action) {
  if (Number(cause?.code) === 4001) return `${action} cancelled in your wallet. You can try again when ready.`
  if (Number(cause?.code) === -32002) return 'A request is already open in your wallet. Complete or dismiss it there, then try again.'
  if (Number(cause?.code) === 4900) return 'Your wallet is offline. Reconnect it, then try again.'
  return String(cause?.message || `${action} could not be completed. Please try again.`).slice(0, 240)
}

async function connect() {
  if (pending.value) return
  error.value = ''
  if (!window.ethereum?.request) {
    error.value = 'No EVM wallet was detected. Open this page in a wallet browser or enable a compatible browser extension, then try again.'
    stage.value = 'error'
    return
  }
  attachProvider(window.ethereum)
  const wallet = provider
  const id = ++operation
  pending.value = true
  stage.value = 'connecting'
  try {
    const accounts = await wallet.request({ method: 'eth_requestAccounts' })
    if (!isCurrent(id)) return
    if (!Array.isArray(accounts) || !/^0x[0-9a-f]{40}$/i.test(accounts[0] || '')) throw new Error('No account was shared. Unlock your wallet and try again.')
    await ensureNetwork(wallet, id)
    if (!isCurrent(id)) return
    const verifiedAccount = await verifyContext(wallet, accounts[0])
    if (!isCurrent(id)) return
    account.value = verifiedAccount
    stage.value = 'ready'
  } catch (cause) {
    if (!isCurrent(id)) return
    error.value = explainError(cause, 'Connection')
    stage.value = 'error'
  } finally {
    pending.value = false
    if (!isCurrent(id) && ['connecting', 'signing'].includes(stage.value)) stage.value = 'idle'
  }
}

async function signIn() {
  if (pending.value || stage.value !== 'ready' || !provider) return
  const wallet = provider
  const id = ++operation
  const signingAccount = account.value
  pending.value = true
  stage.value = 'signing'
  error.value = ''
  let contextValid = false
  try {
    await verifyContext(wallet, signingAccount)
    if (!isCurrent(id)) return
    contextValid = true
    const nonce = crypto.randomUUID()
    const issuedAt = new Date()
    const expiresAt = new Date(issuedAt.getTime() + 5 * 60 * 1000)
    const message = [
      'Decisift sign-in', '',
      `Origin: ${window.location.origin}`,
      `Wallet: ${signingAccount}`,
      'Chain: Robinhood Chain (4663)',
      `Nonce: ${nonce}`,
      `Issued at: ${issuedAt.toISOString()}`,
      `Expires at: ${expiresAt.toISOString()}`, '',
      'This signature records wallet consent for a local preview session. It does not authorize a transaction.',
    ].join('\n')
    const signature = await wallet.request({ method: 'personal_sign', params: [message, signingAccount] })
    if (!isCurrent(id)) return
    if (typeof signature !== 'string' || !/^0x[0-9a-f]{130}$/i.test(signature)) throw new Error('The wallet returned an invalid signature. Please try signing again.')
    if (Date.now() > expiresAt.getTime()) throw new Error('This sign-in request expired. Try again to receive a new nonce.')
    contextValid = false
    await verifyContext(wallet, signingAccount)
    if (!isCurrent(id)) return
    contextValid = true
    try {
      sessionStorage.setItem('decisift:session', JSON.stringify({ account: signingAccount, chainId: 4663, signedAt: Date.now() }))
    } catch {
      throw new Error('The signature was received, but session storage is unavailable. Allow browser storage and try again.')
    }
    stage.value = 'complete'
    emit('connected', signingAccount)
  } catch (cause) {
    if (!isCurrent(id)) return
    if (!contextValid) resetSession()
    else stage.value = 'ready'
    error.value = explainError(cause, 'Signature')
  } finally {
    pending.value = false
    if (!isCurrent(id) && ['connecting', 'signing'].includes(stage.value)) stage.value = 'idle'
  }
}

function handleKeydown(event) {
  if (!props.open) return
  if (event.key === 'Escape') { event.preventDefault(); close(); return }
  if (event.key !== 'Tab') return
  const items = [...(dialog.value?.querySelectorAll('button:not([disabled]), a[href], [tabindex="0"]') || [])].filter((item) => item.getClientRects().length)
  if (!items.length) { event.preventDefault(); title.value?.focus(); return }
  const first = items[0]
  const last = items[items.length - 1]
  if (event.shiftKey && (document.activeElement === first || !items.includes(document.activeElement))) { event.preventDefault(); last.focus() }
  else if (!event.shiftKey && (document.activeElement === last || !dialog.value?.contains(document.activeElement))) { event.preventDefault(); first.focus() }
}

function releaseScroll() {
  if (!scrollLocked) return
  document.body.style.overflow = previousOverflow
  scrollLocked = false
}

watch(() => props.open, async (open) => {
  operation += 1
  if (open) {
    returnFocus = document.activeElement
    previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    scrollLocked = true
    if (!pending.value) { stage.value = 'idle'; error.value = ''; account.value = '' }
    document.addEventListener('keydown', handleKeydown)
    await nextTick()
    title.value?.focus({ preventScroll: true })
  } else {
    document.removeEventListener('keydown', handleKeydown)
    releaseScroll()
    await nextTick()
    if (returnFocus?.isConnected) returnFocus.focus({ preventScroll: true })
  }
}, { immediate: true })

watch(stage, async (value) => {
  if (!props.open || !['ready', 'error', 'idle'].includes(value)) return
  await nextTick()
  primaryAction.value?.focus({ preventScroll: true })
})

onBeforeUnmount(() => {
  operation += 1
  detachProvider()
  document.removeEventListener('keydown', handleKeydown)
  releaseScroll()
})
</script>

<template>
  <Teleport to="body">
    <Transition name="wallet-dialog">
      <div v-if="props.open" class="wallet-backdrop" @click.self="close">
        <section ref="dialog" class="wallet-dialog" role="dialog" aria-modal="true" aria-labelledby="wallet-title" aria-describedby="wallet-description">
          <button class="wallet-close" aria-label="Close wallet dialog" @click="close"><X :size="19" /></button>
          <div class="wallet-emblem"><Wallet :size="24" /></div>
          <p class="wallet-eyebrow">DECISIFT / WALLET SESSION</p>
          <h2 id="wallet-title" ref="title" tabindex="-1">Your wallet.<br /><em>Your decision.</em></h2>
          <p id="wallet-description" class="wallet-description">Connect to Robinhood Chain, then sign a separate message to start a local preview session.</p>
          <ol class="connection-steps" aria-label="Connection progress"><li :class="{ done: ['ready', 'signing', 'complete'].includes(stage) }"><span><Check v-if="['ready', 'signing', 'complete'].includes(stage)" :size="12" /><template v-else>1</template></span>Connect wallet</li><li :class="{ done: stage === 'complete' }"><span><Check v-if="stage === 'complete'" :size="12" /><template v-else>2</template></span>Sign message</li></ol>
          <div class="network-summary"><span class="network-dot"></span><div><strong>Robinhood Chain</strong><small>Network for this session</small></div><code>4663</code></div>
          <div v-if="account && ['ready', 'signing', 'complete'].includes(stage)" class="connected-account"><Check :size="15" /><span>Wallet connected</span><code :title="account">{{ shortAccount }}</code></div>
          <button v-if="stage === 'idle' || stage === 'error'" ref="primaryAction" class="wallet-primary" :disabled="pending" @click="connect"><Wallet :size="17" />{{ stage === 'error' ? 'Try connection again' : 'Connect wallet' }}<ArrowRight :size="17" /></button>
          <div v-if="stage === 'connecting'" class="wallet-waiting" role="status"><LoaderCircle class="spin" :size="18" /><span>Continue in your wallet<small>Approve the connection and network switch.</small></span></div>
          <button v-if="stage === 'ready' || stage === 'signing'" ref="primaryAction" class="wallet-primary" :disabled="pending" @click="signIn"><LoaderCircle v-if="stage === 'signing'" class="spin" :size="17" /><ShieldCheck v-else :size="17" />{{ stage === 'signing' ? 'Waiting for your signature' : 'Sign in with wallet' }}<ArrowRight v-if="stage === 'ready'" :size="17" /></button>
          <p v-if="pending" class="pending-note" role="status">You can close this dialog. Dismiss any pending request in your wallet before starting again.</p>
          <div v-if="stage === 'complete'" class="wallet-success" role="status"><Check :size="20" /><div><strong>Local session ready</strong><small>{{ shortAccount }}</small></div></div>
          <p v-if="error" class="wallet-error" role="alert">{{ error }}</p>
          <p class="signature-note"><ShieldCheck :size="14" /><span>A message signature costs no gas and does not submit a trade. Decisift never receives your private key.</span></p>
          <a class="wallet-docs" href="https://docs.robinhood.com/chain/add-network-to-wallet" target="_blank" rel="noreferrer">Verify the network details <ExternalLink :size="13" /></a>
          <p class="wallet-preview-note">Preview only. Session data stays in this browser tab; no server authentication or onchain proof is created.</p>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.wallet-backdrop{position:fixed;inset:0;z-index:1000;display:grid;place-items:center;background:#142b24a6;backdrop-filter:blur(8px);padding:24px;overflow-y:auto;color:var(--ink,#20332e);font-family:var(--sans,'Segoe UI',sans-serif)}
.wallet-dialog{position:relative;width:min(100%,456px);max-height:calc(100dvh - 48px);overflow-y:auto;background:#fffefa;border:1px solid #fffefa;border-radius:16px;box-shadow:0 30px 100px #0e261943;padding:34px 36px;text-align:left;box-sizing:border-box}
.wallet-dialog *{box-sizing:border-box}.wallet-dialog p,.wallet-dialog h2{margin:0}.wallet-dialog button{font:inherit;cursor:pointer}.wallet-dialog button:focus-visible,.wallet-dialog a:focus-visible,.wallet-dialog [tabindex]:focus-visible{outline:3px solid #a74222;outline-offset:4px}.wallet-close{position:absolute;right:15px;top:15px;width:40px;height:40px;border:0;border-radius:6px;background:transparent;color:var(--muted,#66756d);display:grid;place-items:center}.wallet-close:hover{background:var(--sage,#e7ede6)}.wallet-emblem{display:grid;place-items:center;width:49px;height:49px;border-radius:11px;background:var(--sage,#e7ede6);color:var(--forest,#183b35);margin-bottom:24px}.wallet-eyebrow{font:9px var(--mono,Consolas,monospace);letter-spacing:1.5px;color:var(--muted,#66756d)}.wallet-dialog h2{font:37px/1.17 Georgia,serif;letter-spacing:-1.3px;margin:13px 0 16px}.wallet-dialog h2 em{color:#54745b;font-weight:400}.wallet-description{font-size:12px;line-height:1.9;color:var(--muted,#66756d)}.connection-steps{display:flex;gap:22px;margin:26px 0 18px;padding:0;list-style:none;font-size:10px;color:var(--muted,#66756d)}.connection-steps li{display:flex;align-items:center;gap:7px}.connection-steps li>span{width:21px;height:21px;border:1px solid #cbd5c7;border-radius:50%;display:grid;place-items:center;font:9px var(--mono,Consolas,monospace)}.connection-steps .done{color:var(--forest,#183b35)}.connection-steps .done>span{border-color:var(--forest,#183b35);background:var(--forest,#183b35);color:#fffefa}.network-summary{display:flex;align-items:center;gap:10px;padding:16px;border:1px solid var(--line,#dce2d8);border-radius:7px;background:#f8f9f2}.network-dot{width:7px;height:7px;border-radius:50%;background:#73916f}.network-summary strong{font-size:12px;font-weight:600}.network-summary small{display:block;font-size:9px;margin-top:4px;color:var(--muted,#66756d)}.network-summary code{margin-left:auto;font:11px var(--mono,Consolas,monospace);color:var(--muted,#66756d)}.connected-account{display:flex;gap:7px;align-items:center;padding:15px 0 0;font-size:10px;color:#46684b}.connected-account code{margin-left:auto;font:11px var(--mono,Consolas,monospace);color:var(--ink,#20332e)}.wallet-primary{display:flex;align-items:center;justify-content:center;gap:9px;width:100%;min-height:48px;margin-top:18px;padding:13px 15px;background:var(--forest,#183b35);border:1px solid var(--forest,#183b35);border-radius:6px;color:#fffefa;font-size:12px!important;font-weight:600!important}.wallet-primary>svg:last-child:not(:first-child){margin-left:auto}.wallet-primary>svg:first-child{margin-right:auto}.wallet-primary:hover:not(:disabled){background:#2c5147}.wallet-primary:disabled{opacity:.65;cursor:wait}.wallet-waiting{display:flex;align-items:center;gap:12px;min-height:64px;margin-top:18px;padding:13px;background:var(--sage,#e7ede6);border-radius:6px;color:var(--forest,#183b35);font-size:12px}.wallet-waiting small{display:block;color:var(--muted,#66756d);font-size:10px;margin-top:6px}.pending-note{font-size:9px;line-height:1.8;color:var(--muted,#66756d);margin-top:10px!important}.wallet-error{margin-top:16px!important;color:#a74222;background:#f7e9df;border-radius:6px;padding:12px;font-size:11px;line-height:1.8;overflow-wrap:anywhere}.signature-note{display:flex;gap:8px;color:var(--muted,#66756d);font-size:10px;line-height:1.8;margin-top:19px!important}.signature-note svg{flex-shrink:0;margin-top:3px;color:#54745b}.wallet-docs{display:inline-flex;align-items:center;gap:7px;color:var(--forest,#183b35);font-size:10px;min-height:38px;margin-top:10px;text-decoration:underline;text-underline-offset:4px}.wallet-preview-note{font-size:9px;line-height:1.8;color:var(--muted,#66756d);padding-top:15px;margin-top:6px!important;border-top:1px solid var(--line,#dce2d8)}.wallet-success{margin-top:18px;padding:15px;display:flex;align-items:center;gap:12px;background:var(--sage,#e7ede6);border-radius:6px;color:var(--forest,#183b35)}.wallet-success strong{display:block;font-size:12px}.wallet-success small{display:block;font:10px var(--mono,Consolas,monospace);margin-top:5px}.spin{animation:wallet-spin 1s linear infinite}@keyframes wallet-spin{to{transform:rotate(360deg)}}.wallet-dialog-enter-active,.wallet-dialog-leave-active{transition:opacity .18s ease}.wallet-dialog-enter-active .wallet-dialog,.wallet-dialog-leave-active .wallet-dialog{transition:transform .18s ease}.wallet-dialog-enter-from,.wallet-dialog-leave-to{opacity:0}.wallet-dialog-enter-from .wallet-dialog,.wallet-dialog-leave-to .wallet-dialog{transform:translateY(10px)}
@media(max-width:520px){.wallet-backdrop{padding:14px;align-items:center}.wallet-dialog{padding:28px 24px;max-height:calc(100dvh - 28px);border-radius:12px}.wallet-dialog h2{font-size:34px}.wallet-description{font-size:12px}.wallet-emblem{margin-bottom:22px}.wallet-primary{min-height:48px}.connection-steps{gap:18px}.wallet-docs{min-height:44px}}
@media(prefers-reduced-motion:reduce){.wallet-backdrop,.wallet-dialog,.spin{animation:none!important;transition:none!important}}
</style>
