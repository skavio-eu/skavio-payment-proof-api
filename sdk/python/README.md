# Python Payment Proof 1.0.0

Python >=3.9; no runtime dependencies. From the repository root: `python -m pip install -e integration_docs/sdk/python`. See [release contract and safety](../README.md).

```python
import os
from skavio_payment_proof import PaymentProofClient, APIError, RateLimitError, verify_webhook

with PaymentProofClient(api_key=os.environ['SKAVIO_PROOF_KEY']) as client:
    account = client.get_account()
    # Persist this operation key before sending; this example is not executed by tests.
    proof = client.create_request(
        {'wallet_id': 'YOUR_VERIFIED_WALLET_ID', 'amount_usdc': '29.00',
         'description': 'Order 0001'},
        idempotency_key='merchant-order-20261011-0001')
```

Methods: get_account, list_requests, create_request, get_request, list_contacts, create_contact, list_invoices, create_invoice, get_invoice, send_invoice, list_events. Create methods accept a schema-typed body dictionary; decimal amounts are strings. List methods accept `limit=50,before=None`; events accept `after=0,limit=50`. Send requires `user_approved=True`, only after actual consent. `APIError` exposes `status`, `code`, `retry_after`; 429 raises `RateLimitError`. Invalid success JSON raises APIError with code `invalid_json`; empty responses return None. Transport/timeout errors raise `TransportError`, with no retry. Responses are closed, including error bodies. Context exit clears the in-memory bearer key. A key necessarily stays privately in memory while requests are possible; no persistent storage or logging occurs and repr omits it.

```python
# Inside your receiver, before parsing JSON:
event = verify_webhook(raw_bytes, request_headers, signing_secret)
# Now atomically dedup event['id'] and commit the business effect/outbox.
```

The durable recipe, HTTPS guard, stable key requirements and release limitations are in the parent README. No license grant is inferred; confirm terms before distribution.
