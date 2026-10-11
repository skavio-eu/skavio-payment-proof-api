# Skavio Payment Proof SDKs 1.0.0

Local release candidates for API version 1.0 at `/proof/v1`. REST source of truth: [OpenAPI](../openapi.json). These clients create proof requests and merchant invoices; they never transfer USDC, sign wallets, hold funds, or confirm payments. No GitHub, npm, PyPI, Postman workspace or DEV publication has occurred.

Python >=3.9, stdlib-only runtime:

```sh
python -m pip install -e integration_docs/sdk/python
```

For an offline install with setuptools >=61 already available, add `--no-index --no-build-isolation`. Building requires setuptools; it is a build dependency, not a runtime dependency.

Node >=18, native fetch, no runtime dependencies, ESM only:

```sh
npm install ./integration_docs/sdk/typescript
```

The planned package name is `@skavio/payment-proof`; do not assume it exists on npm. JavaScript and schema-derived `.d.ts` declarations ship together. TypeScript consumers using Node types need their usual development `typescript` and `@types/node` setup. CJS is unsupported. The declaration compiler and minimum-runtime compatibility must be checked by the release supervisor; neither toolchain is installed here.

See [Python](python/README.md) and [Node](typescript/README.md) usage. [Actual test report](../SDK_TEST_REPORT_20261011.md) records commands and limitations.

## Write safety and pagination

All POST methods generate a UUID unless a stable idempotency key is supplied. Persist the key with the business operation **before** the call. Reuse it after a timeout or uncertain response; auto-generated keys are convenient for single attempts, and cannot safely be regenerated for retries. No automatic retries occur. A changed operation/payload with the same key returns 409. Creation of an invoice issues an immutable document and consumes invoice and request allowances. Email consent options must be false; `sendInvoice`/`send_invoice` requires literal explicit approval and must only be used after actual approval. HTTP success is not payment confirmation.

Resource pages expose `{data,next_cursor}`. Pass the opaque cursor back as `before`, stop on null. Events use integer `after`; stop when the cursor does not advance. Lists are bounded at 100; resource ID order is not chronological. No bulk export or automatic infinite pagination is provided. Fetch account entitlements rather than hardcoding plan assumptions. Existing Starter 9, Business 19, Pro 29 native USDC/30 days and seven-day trial remain as documented in API_V1.md; no pricing or availability changes are made here.

## Webhooks and durable deduplication

Pass untouched raw request bytes and header values to `verify_webhook` or `verifyWebhookSignature`. Never parse or reserialize first. Timestamp is signed exactly as received, including leading zeros; clock difference over 300 seconds in either direction fails. The signed body ID must equal the event header; API version must be 1.0. Invalid signatures, JSON, secret types, identities, or clocks throw `VerificationError`. Verification alone does not detect repeated delivery inside the clock window.

Use a durable table with a UNIQUE/PRIMARY KEY event ID. In one local database transaction: insert the verified ID; if duplicate, acknowledge without repeating effects; otherwise validate event type/resource/network/exact atomic amount against your order, then apply the business effect or enqueue a local transactional outbox. Commit before returning 2xx. Roll back on failure so a later delivery can retry. Do not dedup solely in memory, on delivery ID, or before verification. Unknown additive fields may be ignored; route unsupported events safely. Treat only verified payment evidence/events with matching order data as settlement. Receiver examples in the parent docs show durable SQLite patterns.

## Postman and release contract

Import `../Skavio-Payment-Proof-v1.postman_collection.json` (v2.1) and the placeholder environment. It contains all eleven operations across eight REST paths plus nine documented dashboard management requests. Keys are blank placeholders; keep real keys in a private secret environment. REST uses Bearer; management overrides auth and requires your dashboard session/CSRF, with a guard that must be consciously removed. Send-email is guarded separately. UUID scripts provide a local operation key; keep it stable through retries and deliberately change it for each new operation. Do not run templates against real customers during validation. Collection test script is a synthetic HMAC demonstration, not a production receiver or durable verifier. A Postman import/schema check in the actual client remains a release check.

Supervisor release sequence: review diff limited to integration_docs, verify license ownership/terms (no MIT license assumed), test Python 3.9 and Node 18 plus TypeScript compilation, test offline package installation with build tools, import Postman without running requests, then publish approved tagged source/artifacts to the owner's GitHub/Postman/DEV. API, DB, Caddy and website need no deployment for these source artifacts. Never publish private credentials or customer fixtures.
