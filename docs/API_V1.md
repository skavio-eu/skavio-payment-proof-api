# Payment Proof integrations — API version 1.0

Implementation documentation, pending independent verification and deployment. Paths below include the public `/proof` prefix; Flask receives stripped paths. These are Payment Proof credentials, separate from the Skavio Processing API and its credits. No wallet signing, phone, AI, transfers or custody endpoints exist.

## Included entitlements

No mandatory add-on subscription or hidden integration fees. Existing native USDC plans and IDs are unchanged: Starter `starter` 9 USDC/30 days, Business `business` 19, Pro `pro` 29. Starter includes 50 payment requests and 50 invoices, 1 active key and 1 destination. Business includes 200/200, 3 keys and 3 destinations. Pro has no monthly request/invoice caps, 10 keys and 10 destinations, with resource fair use and burst throttling. The 7-day trial includes 12 requests/12 invoices, 1 key/1 destination. Email and verified-wallet limits remain those of the current plan.

An invoice creates one payment request, so it consumes both allowances once. Replayed creation consumes neither again. Quotas and concurrency are enforced in the SQLite write transaction. Monthly resource counts retain the application's existing rolling 30-day semantics; trial counts start at the original trial start. Voiding does not restore creation quota. Pro's existing 300 requests/hour fair-use throttle remains. V1 adds 60 calls/key/minute and 120/IP/minute; inactive, expired and revoked keys fail. Downgrades retain history but only the earliest allowed active keys/destinations can be used. Disabled destinations count until deleted. Expired keys stop counting. Get limits from `/v1/me` or logged-in management, not hardcoded client assumptions.

## Credentials and management

Sign in and verify your receiving wallet in the existing dashboard. Save your business profile before issuing invoices. The Integrations tab creates bearer keys with `read`, `write`, or both scopes. Read permits GET; write permits POST. The opaque key is shown once, hashed at rest, and has prefix/last4 metadata. An optional expiration is a Unix UTC second up to 366 days away. No API key is an email alias. Never put it in a URL, log, browser storage or source control. Supply `Authorization: Bearer skp_...`. `/v1` never uses login cookies, CSRF tokens or Processing API keys. No cross-site CORS support. Use server-to-server integrations.

Logged-in `/proof/api/integrations` GET returns keys, webhook metadata, event types and current entitlements. Cookie actions require `X-CSRF-Token` and the existing production Origin check. Authorization headers are rejected on cookie management routes. Management requires an active customer plan/trial (internal accounts are excluded):

| Method | Management path below `/proof/api/integrations` | Body |
| --- | --- | --- |
| POST | `/keys` | `name`, `scopes`, optional `expires_at` |
| POST | `/keys/{id}/revoke` | `{}` |
| POST | `/webhooks` | `url`, `events` array |
| POST | `/webhooks/{id}/disable` | `{}` |
| POST | `/webhooks/{id}/delete` | `{}` (soft deletion) |
| POST | `/webhooks/{id}/rotate` | `{}`; new secret shown once |
| GET | `/deliveries?limit=25&before=...` | latest bounded metadata/history |
| POST | `/deliveries/{id}/retry` | `{}`; failed delivery with attempts left |

No historical event replay or re-enable operation exists. Delete a disabled destination and create a new one. Rotating a secret changes future attempts, including pending retries. `X-Skavio-Key-Version` identifies the signing version. In-flight sends may use the old version, and disabling/deleting cannot recall a send already in progress. Coordinate rotation with your receiver; keep the previous secret for in-flight traffic for a short transition, then remove it. Rotating `PROOF_SECRET` is **not** webhook rotation: it would make existing encrypted signing secrets unreadable and requires a separate coordinated migration.

## Public REST routes

All JSON mutations require a stable `Idempotency-Key` of 16–80 characters `[A-Za-z0-9_-]`. Keys are tenant-wide, across API keys and operations. Same operation and payload returns the originally stored response and status (even if resource state has since changed); different operation/payload yields 409. Store a durable random key per business operation before the first attempt; retry on timeouts with that same key. Do not generate a new key per retry. Retained responses do not expire. A 100,000 retained-response/account storage guard is a resource fair-use bound, **not** a monthly Pro payment/invoice limit; contact support before that storage threshold. No request or invoice is created when rejected. The invoice's existing owner `creation_key` is preserved and derived from this header; clients cannot supply it independently.

| Method | Path below `/proof` | Result |
| --- | --- | --- |
| GET | `/v1/me` | `api_version`, tenant `id`, plan limits, allowed verified wallets |
| GET | `/v1/requests` | `{data, next_cursor}` |
| POST | `/v1/requests` | request object, 201 |
| GET | `/v1/requests/{id}` | owned request |
| GET | `/v1/contacts` | bounded contact objects |
| POST | `/v1/contacts` | contact object, 201 |
| GET | `/v1/invoices` | bounded invoice objects |
| POST | `/v1/invoices` | invoice object, 201, no email |
| GET | `/v1/invoices/{id}` | owned invoice |
| POST | `/v1/invoices/{id}/send` | `{id, mail_status}`; approved mail queued only |
| GET | `/v1/events?after=0&limit=50` | `{data:[{cursor,event}],next_cursor}` |
| GET | `/openapi.json` | OpenAPI 3.1 reference |
| GET | `/developers` | developer documentation |

Resource lists accept `limit` 1–100 (default 50), and opaque `before=next_cursor`. Results are ordered by ID, not creation time. Keep cursors opaque. New entries may sort before or after your cursor; use events for reconciliation and re-poll the first page as needed. Events use increasing integer `after`. No unbounded list or bulk buyer-data export is available. CSV/PDF machine routes are not implemented; use the existing authenticated merchant exports. Resource IDs and contact/wallet references are always scoped to the bearer tenant; foreign resources return 404. Public invoice objects exclude buyer/issuer identity snapshots and private share capabilities. Contact lists disclose only that tenant's contacts in bounded pages. No key secrets appear in API lists or event payloads.

Request body: `wallet_id` from `/v1/me`, `amount_usdc` decimal string using existing USDC amount validation, `description` 3–350 characters, optional `customer_label` <=120, `expected_payer` valid network wallet, `valid_hours` integer 1–720 (trial expiry constrains it). A custom receiving wallet or arbitrary receiver is rejected. Requests expose `amount_atomic` as the **exact six-decimal transfer amount**, including the existing small unique matching delta; `quoted_amount_atomic` is the original requested value. Always show/pay the exact `amount_atomic / 1,000,000`, not a rounded amount. Events use integer atomic USDC values.

Contact body: `legal_name` required <=160, valid `email`, optional `address` <=600, `reference` <=120. No update/delete public contact API.

Invoice body: `customer_id`, `wallet_id`, `due_date` `YYYY-MM-DD`, `items` array of `{description,quantity,unit_usdc}` decimal strings; optional existing `tax_mode`, `tax_rate`, `tax_usdc`, `tax_notes`, `accounting` follow merchant invoice validations. `send_now` defaults to false and must remain false. Automatic reminder/receipt consent is managed in the dashboard. Creating an invoice irreversibly issues an immutable merchant document. Send email separately **only after obtaining actual user approval** with `{"user_approved":true}`. The API records this caller assertion, not an interactive approval ceremony. Email is only queued; transport acceptance is not inbox delivery. Do not falsely assert consent. API mutations cannot confirm blockchain payments, approve review attribution, alter invoice status or sign a wallet transaction.

Errors: 401 invalid/missing/inactive bearer or insufficient scope; 403 cookie/Origin/customer-access failure; 404 missing or foreign ID; 409 idempotency conflict or invalid retry state; 422 validation/quota failure; 429 burst throttle; 503 temporary service failure. JSON `{error:"..."}`; secrets are never included. Fetch latest resource state after a replay if required.

## Client examples

Set your key from a secret store. These snippets contain placeholders only.

```sh
export SKAVIO_PROOF_KEY='YOUR_ONE_TIME_PAYMENT_PROOF_KEY'
curl -H "Authorization: Bearer $SKAVIO_PROOF_KEY" https://www.skavio.eu/proof/v1/me
curl https://www.skavio.eu/proof/v1/requests \
  -H "Authorization: Bearer $SKAVIO_PROOF_KEY" -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: merchant-order-20261011-0001' \
  -d '{"wallet_id":"YOUR_VERIFIED_WALLET_ID","amount_usdc":"29.00","description":"Order 0001"}'
```

```python
import os, requests
base = 'https://www.skavio.eu/proof/v1'
headers = {'Authorization': 'Bearer ' + os.environ['SKAVIO_PROOF_KEY'],
           'Idempotency-Key': 'merchant-order-20261011-0001'}
# Persist this key with your order before sending. Reuse it on network retry.
r = requests.post(base + '/requests', headers=headers,
                  json={'wallet_id':'YOUR_VERIFIED_WALLET_ID',
                        'amount_usdc':'29.00','description':'Order 0001'}, timeout=15)
r.raise_for_status()
request_id = r.json()['id']
```

```js
const response=await fetch('https://www.skavio.eu/proof/v1/requests',{
 method:'POST',headers:{Authorization:`Bearer ${process.env.SKAVIO_PROOF_KEY}`,
 'Content-Type':'application/json','Idempotency-Key':'merchant-order-20261011-0001'},
 body:JSON.stringify({wallet_id:'YOUR_VERIFIED_WALLET_ID',amount_usdc:'29.00',description:'Order 0001'}),
 signal:AbortSignal.timeout(15000)
});
if(!response.ok)throw new Error(`Payment Proof HTTP ${response.status}`);
const paymentRequest=await response.json();
```

## Webhook events and delivery

Events: `payment_request.created` (direct or invoice-backed request), `invoice.issued`, `invoice.voided`, `payment.confirmed`, and `invoice.paid`. Creation/void events are transactional database triggers, with frozen JSON. Settlement triggers require a transition into PAID and matching verified transfer evidence. AWAITING, REVIEW, checkout/HTTP successes do not confirm payment. Duplicate watcher scans/PAID updates do not create new events. A linked invoice emits both `payment.confirmed` and `invoice.paid`; consume the appropriate event, not both as separate revenue.

Only tenants with a registered enabled endpoint create events. Fanout targets subscriptions registered when the event commits. Late registrations do not get history; `/v1/events` is a retained inspection stream, not delivery replay. Event/delivery history is retained for at least 30 days, with pending work retained until terminal. Worker GC is bounded. Idle tenants without endpoints generate no outbox rows. No buyer email, descriptions, signing secret, API key, evidence JSON or private share tokens appear in events.

Example (values are synthetic):

```json
{"id":"evt_example","api_version":"1.0","type":"payment.confirmed","occurred_at":1791720000,"data":{"request_id":"pr_example","network":"base","amount_atomic":29001234,"quoted_amount_atomic":29000000,"status":"PAID","tx_hash":"0x_SYNTHETIC","verified_at":1791720000}}
```

Invoice events carry `invoice_id`, `request_id`, `number`, `status`, `network`, `amount_atomic`, `tx_hash` (null before settlement). A request-created event carries request ID, network, exact/quoted amounts, status. Event body bytes never change, even after resource updates. Event ordering/delivery ordering is not guaranteed across endpoints; reconcile by GET when needed.

Headers: `X-Skavio-Timestamp` Unix seconds; `X-Skavio-Signature: v1=<hex>`; `X-Skavio-Event-Id`; `X-Skavio-Delivery-Id`; `X-Skavio-Key-Version`. HMAC SHA256 signs `timestamp + '.' + raw JSON bytes`, not parsed/reformatted JSON. Timestamp/signature refresh on retry; event and delivery IDs stay stable. Signing secrets are AES-GCM encrypted, with an HKDF-derived key from the existing strong `PROOF_SECRET`, authenticated to endpoint ID; replicas use the same master secret.

Use [Python verification](verify_webhook.py) or [Node verification](verify_webhook.js). Check HMAC with constant-time comparison and a five-minute replay window **before JSON parsing**. Verify that event ID in signed body matches the header. Deduplicate signed event IDs in durable storage with a unique constraint. Atomically commit the event ID and local business effect (or local processing outbox), then return 2xx promptly. Do not deduplicate solely in RAM or on a transient delivery ID. Keep your clock synchronized. Accept unknown additive fields safely; reject unsupported API versions and invalid resource/amount formats. Receivers must not treat arbitrary unverified incoming JSON as a paid order.

The independent worker claims SQLite leases; lost workers recover after 60 seconds. No HTTP in the payment watcher. Max five automatic attempts, delays 1 minute, 5 minutes, 20 minutes, 60 minutes. Retry 408/429/5xx and network timeouts; 2xx delivered; other status codes (including redirects) terminal failed. DNS/security rejection is terminal. Retry UI is allowed for failed deliveries with fewer than five attempts and an enabled endpoint. Manual retry preserves IDs and the remaining attempt budget. A timeout is ambiguous: receiver may have accepted, hence at-least-once semantics and deduplication are essential. No response body is stored or consumed.

URL policy: HTTPS public DNS name only, port 443, no IP literal, userinfo, query, fragment, private/loopback/link-local/multicast/reserved/translated destination or local hostname. Registration and delivery fail closed if any DNS answer is nonpublic. Each connection dials the validated numeric IP directly and verifies the original hostname using TLS SNI/certificates; no second destination lookup, proxies, redirects or arbitrary redirect targets. DNS resolver subprocess deadline 3 seconds; HTTP/TLS socket timeout 5 seconds and independent 8-second connection deadline; header count/line bounds and no response body read. Production egress restrictions are still required as defense in depth; deployer must enforce/review those separately. The compose overlay declares process/resource isolation but does **not** implement firewall policy. A public endpoint controlled by an attacker must still authenticate TLS. Secrets never enter URL/log/error records.

## Make.com, n8n and WooCommerce recipes

These are generic HTTP/webhook integration recipes, **not official native plugins**.

* Make.com: use its HTTP module for bearer requests with a saved order idempotency key. For events, deploy a public HTTPS receiver that verifies raw bytes/HMAC and durably deduplicates before forwarding validated minimal data to your Make scenario. The supplied destination policy rejects query-string credentials. Do not assume a generic Make custom webhook validates Skavio HMAC automatically.
* n8n: use HTTP Request credentials for your Payment Proof bearer key. Configure a public HTTPS Webhook receiver that preserves raw body bytes; verify HMAC in a controlled Node receiver (or suitably configured Code node with crypto access) before executing workflows. Put durable event deduplication in SQLite/Postgres or another transactional store. Forward only authenticated event data. n8n runtime raw-body/Code-module support varies; validate your installation instead of signing reserialized JSON.
* WooCommerce: a custom server-side extension uses an order-stable idempotency key to create a request and stores `request_id` on the order; direct the buyer to its payment URL. A custom HTTPS receiver verifies signatures, stores event IDs uniquely, maps the signed request ID to the original order and compares network/exact amount before marking it paid. Use `payment.confirmed`; reconcile with an authenticated GET if necessary. Do not mark paid on checkout or when creating a request. Follow WooCommerce's own order transaction/side-effect semantics. No official Skavio WooCommerce plugin is claimed.

Keep third-party credentials/PII in your own secure integration store; do not put credentials in webhook URLs. Separately scoped implementation services remain quoted under approved fixed-scope pricing. Public feature advertising must wait for independently confirmed deployment.
