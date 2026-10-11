# Payment Proof integration quickstart

Implementation artifacts only: no deployed connector or real payment/email E2E claim.
API and webhooks are included: Starter 9 native USDC / 30 days (1 key/1 hook),
Business 19 (3/3), Pro 29 (10/10); seven-day trial 1/1. Existing quotas apply.

1. Verify your receiving wallet and save your business profile in the dashboard.
2. Create a least-privilege Payment Proof key in Integrations. Store the one-time
   secret server-side. REST `/proof/v1/*` uses `Authorization: Bearer skp_…`,
   independent of dashboard cookies and Processing API credentials.
3. Persist an order-specific `Idempotency-Key` (16–80 letters/digits/underscore/hyphen)
   before POST `/proof/v1/requests` with `wallet_id`, `amount_usdc` decimal string,
   and `description`. Reuse exactly that key/payload on retry; 409 means conflict.
   Response includes `id`, `url`, `network`, `amount_atomic`, `quoted_amount_atomic`,
   `status`. Display/pay the exact `amount_atomic / 1000000` including matching delta.
4. Register your public HTTPS port-443 receiver and save its one-time signing secret.
   Verify `X-Skavio-Signature: v1=<hex>` using HMAC SHA256 over
   `X-Skavio-Timestamp + '.' + untouched body bytes`; reject timestamps outside
   ±300 seconds, use constant-time comparison and match signed `id` to
   `X-Skavio-Event-Id`. `X-Skavio-Delivery-Id` is stable on retry;
   `X-Skavio-Key-Version` identifies rotation. Never verify reserialized JSON.
5. Use `durable_receiver.py` or `durable_receiver.js` with a receiver-owned database.
   Atomically insert the signed event ID and a local processing outbox record,
   then acknowledge 2xx. A separate local worker maps the request to its saved order,
   validates network/exact amount and applies the business effect idempotently.
   Only `payment.confirmed` represents matching verified transfer evidence;
   checkout, request creation and HTTP success do not represent settlement.

Deliveries are at least once, up to five attempts (60/300/1200/3600-second delays).
Timeouts, 408, 429 and 5xx retry; redirects fail. Disabled destinations still
consume a destination slot until deleted. No historical delivery replay.

Make: HTTP module for REST; forward events through your verified, durable receiver.
n8n: HTTP Request credentials for REST; preserve raw webhook bytes and verify/dedup
before workflows. WooCommerce: custom server-side extension stores order/request
mapping and exact amount, then consumes verified confirmation. These are generic
HTTP recipes, not official Skavio plugins/connectors. Installation details vary.

See `API_V1.md` for every route, privacy, limits, pagination and consent details;
`openapi.json` for endpoint shapes. Invoice creation queues no mail; explicit
`POST /v1/invoices/{id}/send` requires actual approval and `{user_approved:true}`.
No example performs real network requests or payments by itself.
