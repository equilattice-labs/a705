# Solana integration notes

The website reads Solana public configuration without holding a key.
`src/solana.js` exposes the selected cluster, an allowlisted public
JSON-RPC helper, Wallet Standard discovery and explorer links. The connect
dialog uses Solana Wallet Standard to find MetaMask's Solana wallet, Phantom,
Solflare, Backpack and other compatible wallets; older Phantom/Solflare
injected providers remain supported. MetaMask must expose a Solana account;
an Ethereum-only MetaMask account is not a Solana wallet. The wallet dialog
only displays a public address and never requests transaction signatures.

Copy `.env.example` to `.env.local` when configuring a deployment:

- `VITE_SOLANA_CLUSTER` defaults to `testnet` and accepts `devnet`,
  `mainnet-beta` or `localnet`.
- `VITE_SOLANA_RPC_URL` is optional; the module uses the cluster's public RPC
  when omitted.
- `VITE_SOLANA_DEVNET_TOKEN_MINT` and `VITE_SOLANA_TESTNET_TOKEN_MINT` override
  separate public SPL mint addresses. The app selects the matching value from
  `VITE_SOLANA_CLUSTER`. The deployed testnet mint is built in as a public
  default; devnet and mainnet remain unset. Invalid
  base58/length overrides are ignored and surfaced as
  `solanaConfig.invalidTokenMint`; this does not verify on-chain ownership or
  that an account is a mint.

Token mint deployment is handled separately with the Solana CLI. The website
module exports `SOLANA_DEPLOYMENT_DISABLED` and has no signer, private-key,
transaction submission, minting or program-deployment path. Its JSON-RPC
helper allows only public read methods. Configuring a mint address does not
enable wallet transactions.

Wallet support is initialized by `@metamask/connect-solana`, which registers
MetaMask with the standard Solana wallet registry for the configured cluster.
The Vue interface selects an account using the Wallet Standard `connect`
feature and listens for standard account-change events. Analytics are disabled
in the MetaMask connector.

## Safe test-cluster mint deployment

MetaMask Solana Snap accounts are derived from the wallet recovery material
with Ed25519 on `m/44'/501'/{account-index}'/0'`. An Ethereum account's exported
32-byte private key is a different key and cannot sign for that Solana
account. Before spending SOL, check the CLI keypair's public key and confirm it
matches the intended Solana fee payer:

```sh
solana-keygen pubkey <SOLANA_KEYPAIR.json>
```

The CLI keypair file should be a Solana keypair JSON array, and must remain
local. Do not put a private key or recovery phrase in website source, `.env`,
or a browser bundle. Stop if the printed address does not match the funded
Solana account.

The project currently uses a classic SPL mint on testnet with 9 decimals, the
Solana wallet as mint authority, no freeze authority, and zero initial supply.
Its public mint is `EtzFpGbJ4ex4bsaYvviQGWA2NEEa8HMz3oxdxaES5Q7j`. To create a
replacement on testnet only when explicitly needed:

```sh
spl-token create-token --url testnet --fee-payer <SOLANA_KEYPAIR.json> --mint-authority <SOLANA_PUBKEY> --decimals 9
```

Do not pass `--enable-freeze` or run `spl-token mint`. Verify the mint with
`spl-token display <MINT> --url <CLUSTER>` and `spl-token supply <MINT> --url
<CLUSTER>`; confirm 9 decimals, the intended mint authority, no freeze
authority, and a supply of `0` before adding its public address to the matching
`VITE_SOLANA_<CLUSTER>_TOKEN_MINT` setting.
