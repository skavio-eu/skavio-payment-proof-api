# Skavio Payment Proof — Developer API & SDKs v1.0.0

Official **noncustodial native USDC invoicing and payment notification** integration resources for [Skavio Payment Proof](https://www.skavio.eu/proof/).

## AI agents and MCP integrations

Skavio LLC also operates separate hosted MCP / x402 blockchain tools for AI agents. Their discovery, native USDC transfer verification, recipient/amount matching, PDF payment evidence and DNS/TLS audit tools are **not** the Payment Proof merchant dashboard and do **not** share Proof API credentials.

- [Skavio Agent Tools for Cursor and Claude Desktop](https://github.com/skavio-eu/skavio-agent-tools/blob/main/MCP_CLIENT_SETUP.md) — ready-to-copy MCP configuration and payment limitations.
- [Cursor MCP setup JSON](https://github.com/skavio-eu/skavio-agent-tools/blob/main/examples/cursor-mcp.json).
- [Claude Desktop MCP setup JSON](https://github.com/skavio-eu/skavio-agent-tools/blob/main/examples/claude-desktop-mcp.json).
- [Skavio Processing MCP / OCR and PDF API](https://github.com/skavio-eu/skavio-processing-api/blob/main/MCP_CLIENT_SETUP.md) — independent company OAuth and shared processing credits.
PayAPI Market publicly lists and settlement-verifies the HTTP Verify route only: https://payapi.market/api/skavio-usdc-transaction-verification . Other route settlement verification is not asserted.

## Resources
- [REST API v1 specification](openapi/openapi.json) (OpenAPI 3.1)
- [API reference and event documentation](docs/API_V1.md)
- [Quickstart](docs/quickstart.md)
- [Python SDK](sdk/python/README.md) — `python -m pip install skavio-payment-proof==1.0.0`
- [JavaScript/TypeScript SDK](sdk/typescript/README.md) — Node 18+ ESM and TypeScript declarations; `npm install @skavio-llc/payment-proof@1.0.0`
- [Postman collection](postman/Skavio-Payment-Proof-v1.postman_collection.json) and [placeholder environment](postman/Skavio-Payment-Proof-v1.postman_environment.json)
- [HMAC and durable deduplication examples](examples)
- [Live developer docs](https://www.skavio.eu/proof/developers)

### Authentication and API use
Each merchant creates **Payment Proof-specific bearer keys** in their own Integrations dashboard. Keys from the separate Skavio Processing API are not interchangeable. Webhook signing secrets are shown only at registration or rotation. Never commit keys, wallet seed phrases or private credentials.

REST base URL: `https://www.skavio.eu/proof`. Mutating API calls require an `Idempotency-Key`. The SDKs automatically generate one unless you supply a stable key for safe network retries. Payments are verified from public chain records; the API does not debit wallets or transfer funds.

### Included in plans
Starter 9 native USDC / 30 days: 50 payment requests and 50 invoices, 1 API key and 1 webhook.
Business 19 native USDC / 30 days: 200/200, 3 keys and 3 webhooks.
Pro 29 native USDC / 30 days: unlimited monthly payment requests/invoices, 10 keys and 10 webhook destinations (API rate limits and reasonable fair use apply).
Seven-day free trial: 12 requests / 12 invoices, 1 key and 1 webhook. Mail/schedules/wallet limits are detailed on the [pricing page](https://www.skavio.eu/pricing/).

### Tests
```bash
python -m unittest discover -s sdk/python/tests -p test_sdk.py -v
node --test sdk/typescript/test/sdk.test.js
```
Synthetic only; no real settlement or customer emails. The backend integration suite runs independently on the Skavio DEV environment. Official WooCommerce/Shopify/Make app connectors are **not included**; the reference API and integration recipes can be used to build them.

License: [MIT](LICENSE), consistent with the established Skavio Processing API repository. © 2026 Skavio.

Both SDKs are publicly available on the official registries: [PyPI skavio-payment-proof](https://pypi.org/project/skavio-payment-proof/1.0.0/) and [npm @skavio-llc/payment-proof](https://www.npmjs.com/package/@skavio-llc/payment-proof/v/1.0.0). Both were verified by clean registry install and import. A future GitHub release is a separate event; publishing workflows require registered trusted publishers.

<!-- discovery-release-20261017 -->

## USDC payment verification for AI agents

Skavio USDC Payment Verification — x402 API inspects native Circle USDC transfers, matches an exact recipient and decimal amount, and generates blockchain evidence PDFs. Use it for merchant payment reconciliation, accountant transaction review and agent workflows. PDF evidence is not a tax invoice or a guarantee of third-party authorization.

- HTTP Verify: **0.02 native USDC**; Match: **0.03 USDC**; PDF: **0.05 USDC**. Payment settles separately on **Base** through x402 v2. Inspection supports Base, Polygon, Arbitrum, Optimism, Ethereum, Avalanche and finalized Solana.
- [API quickstart, schemas, errors and client configurations](https://www.skavio.eu/x402/docs/) · [three-route discovery](https://www.skavio.eu/.well-known/x402) · [OpenAPI](https://www.skavio.eu/x402/openapi.json).
- [Skavio USDC Payment Verification & Proof MCP](https://registry.modelcontextprotocol.io/v0.1/servers/eu.skavio%2Fpaid-micro-apis/versions/1.1.1), version **1.1.1**. Stable registry namespace and tool IDs are unchanged. Connect using `https://www.skavio.eu/mcp` (Streamable HTTP).
- MCP has four paid blockchain/domain tools (`verify_native_usdc`, `match_native_usdc_payment`, `usdc_transfer_evidence_pdf`, `domain_dns_tls_audit`), two free discovery tools, and twelve separate authenticated AgentTools processing/job/wallet relays. The DNS/TLS audit is 0.05 USDC and is not a vulnerability scan.
- **A standard MCP client without a wallet x402 extension cannot automatically pay.** Discovery is free. Paid MCP retries preserve `params._meta["x402/payment"]`; HTTP retries use `PAYMENT-SIGNATURE`. Never send a private key or seed phrase. No custody or automatic spending is created by adding a server.
- [PayAPI listing](https://payapi.market/api/skavio-usdc-transaction-verification) is publicly listed and settlement-verified for **HTTP Verify only**. Match and PDF are not claimed settlement-verified by that marketplace.
- RPC availability and finality affect results. No fixed latency SLA is promised. EVM requests use a 32-byte 0x hash; Solana uses its transaction signature. Match takes a recipient wallet and a positive exact USDC decimal string with at most six decimal places.

Cursor `.cursor/mcp.json`:

```json
{"mcpServers":{"skavio-usdc":{"url":"https://www.skavio.eu/mcp"}}}
```

Claude Code:

```sh
claude mcp add --transport http skavio-usdc https://www.skavio.eu/mcp
```

Claude Desktop with Node.js and a reviewed stdio-to-HTTP bridge:

```json
{"mcpServers":{"skavio-usdc":{"command":"npx","args":["-y","mcp-remote","https://www.skavio.eu/mcp"]}}}
```

The bridge may download a third-party package and does not supply wallet payment support. Current Desktop remote connectors may accept the HTTPS URL directly.

First unpaid request (no signing or transfer):

```sh
curl -i 'https://www.skavio.eu/x402/v1/usdc/verify?tx_hash=0x98809948204426c574b6f0aabdec03baa996b5c43ce28cc9ca704fa5d07e592e&network=base'
```

Expect HTTP 402 and decode `PAYMENT-REQUIRED`. Inspect the exact amount, Base USDC asset and recipient before authorizing an x402 wallet client; only then retry the same request. After an ambiguous response, inspect recovery state instead of blindly paying again.

Separate [Skavio PDF, OCR & Document Processing MCP](https://registry.modelcontextprotocol.io/v0.1/servers/io.github.skavio-eu%2Fprocessing/versions/0.2.7), version **0.2.7**, uses company OAuth at `https://www.skavio.eu/processing/mcp` and shared prepaid credits. [Processing docs](https://www.skavio.eu/processing/docs/mcp/) explain company ownership and measured jobs. Optional AgentTools relays require the caller's own key and current backend availability; preserve the idempotency key, poll status, download results and verify SHA256. HTTP `/x402/v1/processing` stays disabled.
