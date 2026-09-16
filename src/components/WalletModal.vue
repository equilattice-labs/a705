<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";
import { brand, storageKeys } from "../brand.js";
import {
  ArrowRight,
  Check,
  ExternalLink,
  LoaderCircle,
  ShieldCheck,
  Wallet,
  X,
} from "lucide-vue-next";

const props = defineProps({ open: Boolean });
const emit = defineEmits(["close", "connected", "session-invalidated"]);
const stage = ref("idle");
const error = ref("");
const account = ref("");
const pending = ref(false);
const dialog = ref(null);
const title = ref(null);
const primaryAction = ref(null);
let returnFocus = null;
let previousOverflow = "";
let operation = 0;
let provider = null;
let scrollLocked = false;

const shortAccount = computed(() =>
  account.value
    ? `${account.value.slice(0, 6)}…${account.value.slice(-4)}`
    : "",
);
const network = {
  chainId: "0x1237",
  chainName: "Robinhood Chain",
  nativeCurrency: { name: "Ether", symbol: "ETH", decimals: 18 },
  rpcUrls: ["https://rpc.mainnet.chain.robinhood.com/"],
  blockExplorerUrls: ["https://robinhoodchain.blockscout.com"],
};

function isCurrent(id) {
  return id === operation && props.open;
}

function close() {
  operation += 1;
  emit("close");
}

function resetSession() {
  account.value = "";
  stage.value = "idle";
  try {
    sessionStorage.removeItem(storageKeys.session);
  } catch {
    /* Parent also clears its in-memory session. */
  }
  emit("session-invalidated");
}

function providerChanged() {
  // A network switch is expected while connecting; all request results are rechecked.
  if (
    pending.value ||
    !props.open ||
    !["ready", "complete"].includes(stage.value)
  )
    return;
  resetSession();
  error.value =
    "Your wallet account or network changed. Connect again to continue.";
}

function detachProvider() {
  provider?.removeListener?.("accountsChanged", providerChanged);
  provider?.removeListener?.("chainChanged", providerChanged);
  provider?.removeListener?.("disconnect", providerChanged);
}

function attachProvider(nextProvider) {
  if (provider === nextProvider) return;
  detachProvider();
  provider = nextProvider;
  provider.on?.("accountsChanged", providerChanged);
  provider.on?.("chainChanged", providerChanged);
  provider.on?.("disconnect", providerChanged);
}

async function ensureNetwork(wallet, id) {
  const chain = await wallet.request({ method: "eth_chainId" });
  if (!isCurrent(id)) return;
  if (String(chain).toLowerCase() === network.chainId) return;
  try {
    await wallet.request({
      method: "wallet_switchEthereumChain",
      params: [{ chainId: network.chainId }],
    });
  } catch (cause) {
    if (Number(cause?.code) !== 4902) throw cause;
    if (!isCurrent(id)) return;
    await wallet.request({
      method: "wallet_addEthereumChain",
      params: [network],
    });
    if (!isCurrent(id)) return;
    const addedChain = await wallet.request({ method: "eth_chainId" });
    if (!isCurrent(id)) return;
    if (String(addedChain).toLowerCase() !== network.chainId) {
      await wallet.request({
        method: "wallet_switchEthereumChain",
        params: [{ chainId: network.chainId }],
      });
    }
  }
}

async function verifyContext(wallet, expectedAccount) {
  const [accounts, chain] = await Promise.all([
    wallet.request({ method: "eth_accounts" }),
    wallet.request({ method: "eth_chainId" }),
  ]);
  if (String(chain).toLowerCase() !== network.chainId)
    throw new Error("Switch to Robinhood Chain (4663), then reconnect.");
  if (!Array.isArray(accounts) || !/^0x[0-9a-f]{40}$/i.test(accounts[0] || ""))
    throw new Error(
      "No wallet account is available. Unlock your wallet and reconnect.",
    );
  if (
    expectedAccount &&
    accounts[0].toLowerCase() !== expectedAccount.toLowerCase()
  )
    throw new Error(
      "Your active wallet account changed. Reconnect before signing in.",
    );
  return accounts[0];
}

function explainError(cause, action) {
  if (Number(cause?.code) === 4001)
    return `${action} cancelled in your wallet. You can try again when ready.`;
  if (Number(cause?.code) === -32002)
    return "A request is already open in your wallet. Complete or dismiss it there, then try again.";
  if (Number(cause?.code) === 4900)
    return "Your wallet is offline. Reconnect it, then try again.";
  return String(
    cause?.message || `${action} could not be completed. Please try again.`,
  ).slice(0, 240);
}

async function connect() {
  if (pending.value) return;
  error.value = "";
  if (!window.ethereum?.request) {
    error.value =
      "No EVM wallet was detected. Open this page in a wallet browser or enable a compatible browser extension, then try again.";
    stage.value = "error";
    return;
  }
  attachProvider(window.ethereum);
  const wallet = provider;
  const id = ++operation;
  pending.value = true;
  stage.value = "connecting";
  try {
    const accounts = await wallet.request({ method: "eth_requestAccounts" });
    if (!isCurrent(id)) return;
    if (
      !Array.isArray(accounts) ||
      !/^0x[0-9a-f]{40}$/i.test(accounts[0] || "")
    )
      throw new Error(
        "No account was shared. Unlock your wallet and try again.",
      );
    await ensureNetwork(wallet, id);
    if (!isCurrent(id)) return;
    const verifiedAccount = await verifyContext(wallet, accounts[0]);
    if (!isCurrent(id)) return;
    account.value = verifiedAccount;
    stage.value = "ready";
  } catch (cause) {
    if (!isCurrent(id)) return;
    error.value = explainError(cause, "Connection");
    stage.value = "error";
  } finally {
    pending.value = false;
    if (!isCurrent(id) && ["connecting", "signing"].includes(stage.value))
      stage.value = "idle";
  }
}

async function signIn() {
  if (pending.value || stage.value !== "ready" || !provider) return;
  const wallet = provider;
  const id = ++operation;
  const signingAccount = account.value;
  pending.value = true;
  stage.value = "signing";
  error.value = "";
  let contextValid = false;
  try {
    await verifyContext(wallet, signingAccount);
    if (!isCurrent(id)) return;
    contextValid = true;
    const nonce = crypto.randomUUID();
    const issuedAt = new Date();
    const expiresAt = new Date(issuedAt.getTime() + 5 * 60 * 1000);
    const message = [
      `${brand.name} sign-in`,
      "",
      `Origin: ${window.location.origin}`,
      `Wallet: ${signingAccount}`,
      "Chain: Robinhood Chain (4663)",
      `Nonce: ${nonce}`,
      `Issued at: ${issuedAt.toISOString()}`,
      `Expires at: ${expiresAt.toISOString()}`,
      "",
      "This signature records wallet consent for a local preview session. It does not authorize a transaction.",
    ].join("\n");
    const signature = await wallet.request({
      method: "personal_sign",
      params: [message, signingAccount],
    });
    if (!isCurrent(id)) return;
    if (typeof signature !== "string" || !/^0x[0-9a-f]{130}$/i.test(signature))
      throw new Error(
        "The wallet returned an invalid signature. Please try signing again.",
      );
    if (Date.now() > expiresAt.getTime())
      throw new Error(
        "This sign-in request expired. Try again to receive a new nonce.",
      );
    contextValid = false;
    await verifyContext(wallet, signingAccount);
    if (!isCurrent(id)) return;
    contextValid = true;
    try {
      sessionStorage.setItem(
        storageKeys.session,
        JSON.stringify({
          account: signingAccount,
          chainId: 4663,
          signedAt: Date.now(),
        }),
      );
    } catch {
      throw new Error(
        "The signature was received, but session storage is unavailable. Allow browser storage and try again.",
      );
    }
    stage.value = "complete";
    emit("connected", signingAccount);
  } catch (cause) {
    if (!isCurrent(id)) return;
    if (!contextValid) resetSession();
    else stage.value = "ready";
    error.value = explainError(cause, "Signature");
  } finally {
    pending.value = false;
    if (!isCurrent(id) && ["connecting", "signing"].includes(stage.value))
      stage.value = "idle";
  }
}

function handleKeydown(event) {
  if (!props.open) return;
  if (event.key === "Escape") {
    event.preventDefault();
    close();
    return;
  }
  if (event.key !== "Tab") return;
  const items = [
    ...(dialog.value?.querySelectorAll(
      'button:not([disabled]), a[href], [tabindex="0"]',
    ) || []),
  ].filter((item) => item.getClientRects().length);
  if (!items.length) {
    event.preventDefault();
    title.value?.focus();
    return;
  }
  const first = items[0];
  const last = items[items.length - 1];
  if (
    event.shiftKey &&
    (document.activeElement === first ||
      !items.includes(document.activeElement))
  ) {
    event.preventDefault();
    last.focus();
  } else if (
    !event.shiftKey &&
    (document.activeElement === last ||
      !dialog.value?.contains(document.activeElement))
  ) {
    event.preventDefault();
    first.focus();
  }
}

function releaseScroll() {
  if (!scrollLocked) return;
  document.body.style.overflow = previousOverflow;
  scrollLocked = false;
}

watch(
  () => props.open,
  async (open) => {
    operation += 1;
    if (open) {
      returnFocus = document.activeElement;
      previousOverflow = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      scrollLocked = true;
      if (!pending.value) {
        stage.value = "idle";
        error.value = "";
        account.value = "";
      }
      document.addEventListener("keydown", handleKeydown);
      await nextTick();
      title.value?.focus({ preventScroll: true });
    } else {
      document.removeEventListener("keydown", handleKeydown);
      releaseScroll();
      await nextTick();
      if (returnFocus?.isConnected) returnFocus.focus({ preventScroll: true });
    }
  },
  { immediate: true },
);

watch(stage, async (value) => {
  if (!props.open || !["ready", "error", "idle"].includes(value)) return;
  await nextTick();
  primaryAction.value?.focus({ preventScroll: true });
});

onBeforeUnmount(() => {
  operation += 1;
  detachProvider();
  document.removeEventListener("keydown", handleKeydown);
  releaseScroll();
});
</script>

<template>
  <Teleport to="body">
    <Transition name="wallet-dialog">
      <div v-if="props.open" class="wallet-backdrop" @click.self="close">
        <section
          ref="dialog"
          class="wallet-dialog"
          role="dialog"
          aria-modal="true"
          aria-labelledby="wallet-title"
          aria-describedby="wallet-description"
        >
          <button
            class="wallet-close"
            aria-label="Close wallet dialog"
            @click="close"
          >
            <X :size="19" />
          </button>
          <div class="wallet-emblem"><Wallet :size="24" /></div>
          <p class="wallet-eyebrow">{{ brand.name }} / WALLET SESSION</p>
          <h2 id="wallet-title" ref="title" tabindex="-1">
            Start a wallet session
          </h2>
          <p id="wallet-description" class="wallet-description">
            Connect to Robinhood Chain, then sign a separate message to start a
            local preview session.
          </p>
          <ol class="connection-steps" aria-label="Connection progress">
            <li
              :class="{
                done: ['ready', 'signing', 'complete'].includes(stage),
              }"
            >
              <span
                ><Check
                  v-if="['ready', 'signing', 'complete'].includes(stage)"
                  :size="12"
                /><template v-else>1</template></span
              >Connect wallet
            </li>
            <li :class="{ done: stage === 'complete' }">
              <span
                ><Check v-if="stage === 'complete'" :size="12" /><template
                  v-else
                  >2</template
                ></span
              >Sign message
            </li>
          </ol>
          <div class="network-summary">
            <span class="network-dot"></span>
            <div>
              <strong>Robinhood Chain</strong
              ><small>Network for this session</small>
            </div>
            <code>4663</code>
          </div>
          <div
            v-if="account && ['ready', 'signing', 'complete'].includes(stage)"
            class="connected-account"
          >
            <Check :size="15" /><span>Wallet connected</span
            ><code :title="account">{{ shortAccount }}</code>
          </div>
          <button
            v-if="stage === 'idle' || stage === 'error'"
            ref="primaryAction"
            class="wallet-primary"
            :disabled="pending"
            @click="connect"
          >
            <Wallet :size="17" />{{
              stage === "error" ? "Try connection again" : "Connect wallet"
            }}<ArrowRight :size="17" />
          </button>
          <div
            v-if="stage === 'connecting'"
            class="wallet-waiting"
            role="status"
          >
            <LoaderCircle class="spin" :size="18" /><span
              >Continue in your wallet<small
                >Approve the connection and network switch.</small
              ></span
            >
          </div>
          <button
            v-if="stage === 'ready' || stage === 'signing'"
            ref="primaryAction"
            class="wallet-primary"
            :disabled="pending"
            @click="signIn"
          >
            <LoaderCircle
              v-if="stage === 'signing'"
              class="spin"
              :size="17"
            /><ShieldCheck v-else :size="17" />{{
              stage === "signing"
                ? "Waiting for your signature"
                : "Sign in with wallet"
            }}<ArrowRight v-if="stage === 'ready'" :size="17" />
          </button>
          <p v-if="pending" class="pending-note" role="status">
            You can close this dialog. Dismiss any pending request in your
            wallet before starting again.
          </p>
          <div v-if="stage === 'complete'" class="wallet-success" role="status">
            <Check :size="20" />
            <div>
              <strong>Local session ready</strong
              ><small>{{ shortAccount }}</small>
            </div>
          </div>
          <p v-if="error" class="wallet-error" role="alert">{{ error }}</p>
          <p class="signature-note">
            <ShieldCheck :size="14" /><span
              >A message signature costs no gas and does not submit a trade.
              {{ brand.name }} never receives your private key.</span
            >
          </p>
          <a
            class="wallet-docs"
            href="https://docs.robinhood.com/chain/add-network-to-wallet"
            target="_blank"
            rel="noreferrer"
            >Verify the network details <ExternalLink :size="13"
          /></a>
          <p class="wallet-preview-note">
            Preview only. Session data stays in this browser tab; no server
            authentication or onchain proof is created.
          </p>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.wallet-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: grid;
  place-items: center;
  overflow-y: auto;
  padding: 24px;
  background: #050707d9;
  backdrop-filter: blur(12px);
  color: var(--ink, #eef2ed);
  font: 14px/1.6 var(--sans, "Segoe UI", sans-serif);
}
.wallet-dialog {
  position: relative;
  display: grid;
  grid-template-columns: 40px minmax(0, 1fr);
  align-content: start;
  gap: 0 12px;
  width: min(100%, 540px);
  max-height: calc(100dvh - 48px);
  padding: 26px;
  overflow-y: auto;
  overscroll-behavior: contain;
  background: var(--surface, #191e22);
  border: 1px solid var(--line, #344039);
  border-top: 3px solid var(--accent, #cef576);
  border-radius: 4px;
  box-shadow: 0 24px 80px #0008;
  text-align: left;
  box-sizing: border-box;
  scrollbar-color: #57655c var(--surface, #191e22);
}
.wallet-dialog *,
.wallet-dialog *::before,
.wallet-dialog *::after {
  box-sizing: border-box;
}
.wallet-dialog > * {
  grid-column: 1 / -1;
  min-width: 0;
}
.wallet-dialog p,
.wallet-dialog h2 {
  margin: 0;
}
.wallet-dialog button {
  font: inherit;
  cursor: pointer;
}
.wallet-dialog button:focus-visible,
.wallet-dialog a:focus-visible,
.wallet-dialog [tabindex]:focus-visible {
  outline: 2px solid var(--accent, #cef576);
  outline-offset: 4px;
}
.wallet-dialog svg {
  flex-shrink: 0;
}
.wallet-close {
  position: absolute;
  right: 14px;
  top: 14px;
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border: 1px solid transparent;
  border-radius: 3px;
  color: var(--muted, #a7b2ab);
  background: transparent;
}
.wallet-close:hover {
  border-color: var(--line, #344039);
  background: var(--paper, #101315);
  color: var(--ink, #eef2ed);
}
.wallet-emblem {
  grid-column: 1;
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  background: var(--sage, #273222);
  color: var(--accent, #cef576);
  border: 1px solid #4a5b38;
  border-radius: 3px;
}
.wallet-eyebrow {
  grid-column: 2;
  align-self: center;
  padding-right: 34px;
  font: 12px/1.6 var(--mono, Consolas, monospace);
  letter-spacing: 0.8px;
  text-transform: uppercase;
  color: var(--muted, #a7b2ab);
}
.wallet-dialog h2 {
  margin-top: 24px;
  font: 650 30px/1.15 var(--sans, "Segoe UI", sans-serif);
  letter-spacing: -1px;
}
.wallet-description {
  margin-top: 10px !important;
  max-width: 420px;
  font-size: 13px;
  line-height: 1.7;
  color: var(--muted, #a7b2ab);
}
.connection-steps {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px;
  margin: 24px 0 0;
  padding: 0;
  background: var(--line, #344039);
  border: 1px solid var(--line, #344039);
  list-style: none;
  font-size: 12px;
  color: var(--muted, #a7b2ab);
}
.connection-steps li {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  min-height: 54px;
  padding: 10px 12px;
  background: var(--paper, #101315);
}
.connection-steps li > span {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  border: 1px solid #657468;
  border-radius: 2px;
  font: 12px var(--mono, Consolas, monospace);
  color: var(--ink, #eef2ed);
}
.connection-steps .done {
  color: var(--accent, #cef576);
  background: var(--sage, #273222);
}
.connection-steps .done > span {
  background: var(--accent, #cef576);
  border-color: var(--accent, #cef576);
  color: #101315;
}
.network-summary {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 0;
  border-bottom: 1px solid var(--line, #344039);
}
.network-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent, #cef576);
  flex-shrink: 0;
}
.network-summary strong {
  font-size: 13px;
  font-weight: 600;
}
.network-summary small {
  display: block;
  margin-top: 2px;
  font-size: 12px;
  color: var(--muted, #a7b2ab);
}
.network-summary code {
  margin-left: auto;
  padding: 3px 8px;
  border: 1px solid var(--line, #344039);
  font: 12px/1.5 var(--mono, Consolas, monospace);
  color: var(--muted, #a7b2ab);
}
.connected-account {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding-top: 15px;
  color: var(--accent, #cef576);
  font-size: 12px;
}
.connected-account code {
  margin-left: auto;
  color: var(--ink, #eef2ed);
  font: 12px var(--mono, Consolas, monospace);
}
.wallet-primary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  width: 100%;
  min-height: 48px;
  margin-top: 20px;
  padding: 12px 15px;
  border: 1px solid var(--accent, #cef576);
  border-radius: 2px;
  background: var(--accent, #cef576);
  color: #101315;
  font-size: 13px !important;
  font-weight: 650 !important;
}
.wallet-primary > svg:last-child:not(:first-child) {
  margin-left: auto;
}
.wallet-primary > svg:first-child {
  margin-right: auto;
}
.wallet-primary:hover:not(:disabled) {
  background: #ddff96;
  border-color: #ddff96;
}
.wallet-primary:active:not(:disabled) {
  background: #bce15f;
}
.wallet-primary:disabled {
  background: #748653;
  border-color: #748653;
  color: #101315;
  cursor: wait;
}
.wallet-waiting,
.wallet-success {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 64px;
  margin-top: 20px;
  padding: 14px;
  border: 1px solid #4a5b38;
  border-left: 3px solid var(--accent, #cef576);
  background: var(--sage, #273222);
  color: var(--accent, #cef576);
  font-size: 13px;
}
.wallet-waiting small,
.wallet-success small {
  display: block;
  margin-top: 4px;
  color: var(--muted, #a7b2ab);
  font-size: 12px;
}
.wallet-success strong {
  font-size: 13px;
  font-weight: 600;
}
.wallet-success small {
  font-family: var(--mono, Consolas, monospace);
}
.pending-note {
  margin-top: 10px !important;
  color: var(--muted, #a7b2ab);
  font-size: 12px;
  line-height: 1.7;
}
.wallet-error {
  margin-top: 16px !important;
  padding: 12px 14px;
  border: 1px solid #7a4744;
  border-left: 3px solid #ffaaa1;
  background: #352526;
  color: #ffc3bb;
  font-size: 12px;
  line-height: 1.7;
  overflow-wrap: anywhere;
}
.signature-note {
  display: flex;
  gap: 10px;
  margin-top: 20px !important;
  color: var(--muted, #a7b2ab);
  font-size: 12px;
  line-height: 1.7;
}
.signature-note svg {
  margin-top: 3px;
  color: var(--accent, #cef576);
}
.wallet-docs {
  display: inline-flex;
  align-items: center;
  justify-self: start;
  gap: 8px;
  min-height: 44px;
  margin-top: 4px;
  color: var(--ink, #eef2ed);
  font-size: 12px;
  text-decoration: underline;
  text-underline-offset: 4px;
  text-decoration-color: #657468;
}
.wallet-docs:hover {
  color: var(--accent, #cef576);
}
.wallet-preview-note {
  margin-top: 6px !important;
  padding-top: 14px;
  border-top: 1px solid var(--line, #344039);
  color: var(--muted, #a7b2ab);
  font-size: 12px;
  line-height: 1.7;
}
.spin {
  animation: wallet-spin 1s linear infinite;
}
@keyframes wallet-spin {
  to {
    transform: rotate(360deg);
  }
}
.wallet-dialog-enter-active,
.wallet-dialog-leave-active {
  transition: opacity 0.15s ease;
}
.wallet-dialog-enter-active .wallet-dialog,
.wallet-dialog-leave-active .wallet-dialog {
  transition: transform 0.15s ease;
}
.wallet-dialog-enter-from,
.wallet-dialog-leave-to {
  opacity: 0;
}
.wallet-dialog-enter-from .wallet-dialog,
.wallet-dialog-leave-to .wallet-dialog {
  transform: translateY(8px);
}
@media (max-width: 540px) {
  .wallet-backdrop {
    padding: 12px;
  }
  .wallet-dialog {
    max-height: calc(100dvh - 24px);
    padding: 22px 18px;
  }
  .wallet-dialog h2 {
    font-size: 27px;
  }
  .wallet-eyebrow {
    letter-spacing: 0.2px;
    padding-right: 30px;
  }
  .wallet-close {
    right: 8px;
    top: 12px;
  }
  .connection-steps li {
    padding: 10px 8px;
    gap: 7px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .wallet-backdrop,
  .wallet-dialog,
  .spin {
    animation: none !important;
    transition: none !important;
  }
}
</style>
