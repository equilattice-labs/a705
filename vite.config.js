import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'node:url'

const mobileWalletProtocolCoreEsm = fileURLToPath(
  new URL('./node_modules/@metamask/mobile-wallet-protocol-core/dist/index.mjs', import.meta.url),
)

export default defineConfig({
  plugins: [vue()],
  optimizeDeps: {
    include: ['eciesjs'],
    needsInterop: ['eciesjs'],
  },
  resolve: {
    alias: [{
      find: /^@metamask\/mobile-wallet-protocol-core$/,
      replacement: mobileWalletProtocolCoreEsm,
    }],
  },
  server: { port: 4173 },
  preview: { port: 4173 },
})
