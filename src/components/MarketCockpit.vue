<script setup>
import { computed, onMounted, ref } from "vue";
import { ArrowRight, Check, Copy, ShieldCheck } from "lucide-vue-next";
import { brand, storageKeys } from "../brand.js";

const stations = [
  ["Deposit", "Shielded ZEC received"],
  ["Settle", "NEAR Intents settles the route"],
  ["Relay", "ETH moves to Robinhood Chain"],
  ["Deliver", `${brand.ticker} arrives at your address`],
];
const station = ref(0);
const copied = ref(false);
const depositAddress = "t1ZecpassDemo9wWmJ9KxYp3yP9o7qQ8rT6sU5";
const current = computed(() => stations[station.value]);

function persist() {
  try {
    const existing = JSON.parse(localStorage.getItem(storageKeys.order) || "{}");
    localStorage.setItem(storageKeys.order, JSON.stringify({ ...existing, station: station.value }));
  } catch {
    // The route preview remains usable when browser storage is disabled.
  }
}
function advance() {
  if (station.value < stations.length - 1) station.value += 1;
  persist();
}
async function copyAddress() {
  await navigator.clipboard?.writeText(depositAddress).catch(() => {});
  copied.value = true;
  window.setTimeout(() => { copied.value = false; }, 1400);
}
onMounted(() => {
  try {
    const saved = JSON.parse(localStorage.getItem(storageKeys.order) || "null");
    if (Number.isInteger(saved?.station)) station.value = Math.min(Math.max(saved.station, 0), stations.length - 1);
  } catch {
    // Ignore malformed preview state.
  }
});

defineExpose({ advance });
</script>

<template>
  <section class="route-cockpit" :aria-label="`${brand.name} route monitor`">
    <header class="cockpit-header">
      <div><span class="cockpit-kicker">{{ brand.name }} / ROUTE MONITOR</span><h3>Your pass is moving.</h3></div>
      <span class="cockpit-status"><span></span> Preview route</span>
    </header>
    <div class="cockpit-progress" aria-label="Route progress">
      <div v-for="(item, index) in stations" :key="item[0]" class="cockpit-step" :class="{ done: index < station, current: index === station }">
        <span class="cockpit-dot"><Check v-if="index < station" :size="13" /><template v-else>{{ String(index + 1).padStart(2, "0") }}</template></span>
        <div><strong>{{ item[0] }}</strong><small>{{ item[1] }}</small></div>
      </div>
    </div>
    <div class="cockpit-footer">
      <div><span class="cockpit-kicker">ONE-TIME DEPOSIT ADDRESS</span><code>{{ depositAddress }}</code></div>
      <button class="cockpit-copy" type="button" @click="copyAddress"><Copy :size="14" />{{ copied ? "Copied" : "Copy" }}</button>
      <button class="cockpit-next" type="button" :disabled="station >= stations.length - 1" @click="advance">{{ station >= stations.length - 1 ? "Delivered" : `Simulate ${current[0].toLowerCase()}` }} <ArrowRight :size="15" /></button>
    </div>
    <p class="cockpit-note"><ShieldCheck :size="14" /> Private in. Public out. This local monitor never submits a transaction.</p>
  </section>
</template>

<style scoped>
.route-cockpit { color: var(--ink, #242224); border: 1px solid var(--line, #d8d4d1); border-radius: 12px; background: var(--paper, #f8f8f6); overflow: hidden; }
.cockpit-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 18px; padding: 24px; border-bottom: 1px solid var(--line, #d8d4d1); }
.cockpit-kicker { color: var(--muted, #777); font: 10px var(--mono, Consolas, monospace); letter-spacing: .1em; text-transform: uppercase; }
.cockpit-header h3 { margin: 8px 0 0; font: 500 27px/1.05 var(--serif, Georgia, serif); }
.cockpit-status { display: inline-flex; align-items: center; gap: 7px; color: #5d8457; font: 10px var(--mono, Consolas, monospace); text-transform: uppercase; }
.cockpit-status span { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.cockpit-progress { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0; padding: 22px 24px; }
.cockpit-step { display: flex; gap: 10px; min-width: 0; padding-right: 12px; color: #aaa; }
.cockpit-step + .cockpit-step { padding-left: 12px; border-left: 1px solid var(--line, #d8d4d1); }
.cockpit-step.current { color: var(--ink, #242224); }
.cockpit-step.done { color: #6b9863; }
.cockpit-dot { display: grid; place-items: center; width: 25px; height: 25px; flex: 0 0 25px; border: 1px solid currentColor; border-radius: 50%; font: 10px var(--mono, Consolas, monospace); }
.cockpit-step.current .cockpit-dot { color: #9e6798; background: #f4eafa; }
.cockpit-step strong, .cockpit-step small { display: block; }
.cockpit-step strong { font-size: 12px; }
.cockpit-step small { margin-top: 4px; color: #858487; font-size: 10px; line-height: 1.35; }
.cockpit-footer { display: grid; grid-template-columns: 1fr auto auto; align-items: end; gap: 12px; padding: 18px 24px; background: #fff; border-top: 1px solid var(--line, #d8d4d1); }
.cockpit-footer code { display: block; margin-top: 7px; overflow-wrap: anywhere; font: 11px var(--mono, Consolas, monospace); }
.cockpit-copy, .cockpit-next { display: inline-flex; align-items: center; justify-content: center; gap: 7px; min-height: 38px; padding: 8px 12px; border: 1px solid var(--line, #d8d4d1); border-radius: 6px; font-size: 11px; cursor: pointer; }
.cockpit-copy { color: var(--ink, #242224); background: var(--paper, #f8f8f6); }
.cockpit-next { color: #fff; background: var(--ink, #242224); border-color: var(--ink, #242224); }
.cockpit-next:disabled { opacity: .55; cursor: default; }
.cockpit-note { display: flex; align-items: center; gap: 7px; margin: 0; padding: 0 24px 18px; color: #777; font-size: 11px; }
.cockpit-note svg { color: #9e6798; }
@media (max-width: 720px) { .cockpit-progress { grid-template-columns: 1fr 1fr; gap: 18px 0; } .cockpit-step:nth-child(3) { padding-left: 0; border-left: 0; } .cockpit-footer { grid-template-columns: 1fr auto; } .cockpit-next { grid-column: 1 / -1; } }
@media (max-width: 430px) { .cockpit-header { display: block; } .cockpit-status { margin-top: 14px; } .cockpit-progress { grid-template-columns: 1fr; } .cockpit-step + .cockpit-step, .cockpit-step:nth-child(3) { padding-left: 0; border-left: 0; } }
</style>
