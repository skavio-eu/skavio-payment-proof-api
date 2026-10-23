# Accept USDC payments without Stripe — Skavio Payment Proof

**Audience:** independent developers, freelancers, online sellers and small businesses whose customers want to pay in native Circle USDC.

[Start the 7-day Payment Proof trial](https://www.skavio.eu/proof/?utm_source=github&utm_medium=guide&utm_campaign=usdc_merchant_launch_20261023) · [See current prices](https://www.skavio.eu/pricing/?utm_source=github&utm_medium=guide&utm_campaign=usdc_merchant_launch_20261023) · [Developer API](https://www.skavio.eu/proof/developers?utm_source=github&utm_medium=guide&utm_campaign=usdc_merchant_launch_20261023)

## The actual merchant workflow

1. Create a merchant account, verify the account email, and start the seven-day trial.
2. Register a **receiving wallet you control**. Supported merchant receipt networks are Base, Polygon PoS, Arbitrum and Solana. Never share a private key or seed phrase.
3. Create a payment request or a numbered sales invoice. The customer receives a link with network and exact native-USDC amount.
4. The customer authorizes a transfer from their own wallet. Payment Proof does not custody funds or automatically withdraw from wallets.
5. Wait for verified on-chain settlement. Track payment status and download an invoice, separate blockchain evidence or accounting CSV as appropriate.

**The invoice and evidence PDF are not the same document.** You remain responsible for country-specific legal and tax requirements.

## Plans paid in native Circle USDC

| Plan | USDC / 30 days | Requests and invoices |
| --- | ---: | --- |
| Trial | Free for 7 days | 12 total requests and 12 invoices |
| Starter | 9 USDC | 50 requests / 50 invoices per period |
| Business | 19 USDC | 200 / 200 per period |
| Pro | 29 USDC | No fixed monthly request/invoice limit, subject to other quotas and fair-use guards |

Other limits apply to emails, wallets, API keys and schedules; see the [current product](https://www.skavio.eu/proof/?utm_source=github&utm_medium=guide&utm_campaign=usdc_merchant_launch_20261023) for details. Manual wallet approval is required for subscription renewals; this is not an automatically debited subscription.

## Using it in an existing application

The [developer quickstart](../docs/quickstart.md) walks through merchant-specific REST keys, idempotent requests and signed webhooks. Python and TypeScript SDKs are available in this repository. Use a server-side key and always check final transfer status before fulfilling an order.

Skavio does not claim that every country’s invoicing or crypto regulations are automatically satisfied. Independent real-business transaction acceptance and operational checks should be performed before relying on unattended settlement.

**Get started:** [Open Payment Proof](https://www.skavio.eu/proof/?utm_source=github&utm_medium=guide&utm_campaign=usdc_merchant_launch_20261023) or [ask about a limited USDC integration pilot](mailto:work@skavio.eu?subject=USDC%20business%20integration%20pilot).

Skavio LLC — October 2026.
