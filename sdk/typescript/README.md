# Node / TypeScript Payment Proof 1.0.0

Node >=18, native fetch, ESM JavaScript plus type declarations, no runtime dependencies. Planned name `@skavio-llc/payment-proof`, not published. Local install: `npm install ./integration_docs/sdk/typescript` from the repo root.

```js
import {PaymentProofClient, verifyWebhookSignature} from '@skavio-llc/payment-proof';
const client = new PaymentProofClient({apiKey: process.env.SKAVIO_PROOF_KEY});
const account = await client.getAccount();
// Persist key before this operation; never replace it for an uncertain retry.
const proof = await client.createRequest({wallet_id:'YOUR_VERIFIED_WALLET_ID',
  amount_usdc:'29.00', description:'Order 0001'},
  {idempotencyKey:'merchant-order-20261011-0001'});
client.close();
```

Methods: getAccount, listRequests, createRequest, getRequest, listContacts, createContact, listInvoices (getInvoices alias), createInvoice, getInvoice, sendInvoice, listEvents. List options are `{limit,before}`; events `{after,limit}`. Send requires `{userApproved:true}` only after actual approval. Construction accepts `baseUrl`, `apiKey`, `timeoutMs=10000`, and an injectable `fetchImplementation`. Timeout AbortController covers fetch and response body reading; custom fetch must honor its signal. Redirects and retries are disabled. APIError exposes `status`, `code`, `retryAfter`; 429 uses RateLimitError. Empty responses return null; invalid success JSON throws APIError; transport/abort failures use TransportError. Private fields omit credentials from inspection and JSON serialization; close clears the in-memory key.

```js
const event = verifyWebhookSignature(rawBuffer, headers, signingSecret);
// Atomically dedup event.id and commit your business effect/outbox before 2xx.
```

Verifier requires an actual Buffer of untouched bytes; clock overrides `{now,timestampToleranceSeconds}` are in seconds. See [shared safety and release contract](../README.md). CJS unsupported. TypeScript compilation and Node 18 validation are pending release checks. No license grant is inferred.
