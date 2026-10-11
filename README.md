# Skavio Payment Proof — Developer API & SDKs v1.0.0

Official **noncustodial native USDC invoicing and payment notification** integration resources for [Skavio Payment Proof](https://www.skavio.eu/proof/).

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
