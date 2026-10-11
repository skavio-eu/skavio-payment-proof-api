export interface Error {
  error: string;
}
export interface RequestCreate {
  wallet_id: string;
  amount_usdc: string;
  description: string;
  customer_label?: string;
  expected_payer?: string;
  valid_hours?: number;
}
export interface Request {
  id: string;
  wallet_id?: string;
  network: string;
  receiver_address?: string;
  customer_label?: string;
  description?: string;
  status: string;
  url: string;
  amount_atomic: number;
  quoted_amount_atomic?: number;
  expected_payer?: string | null;
  created_at?: number;
  expires_at?: number;
  tx_hash?: string | null;
  verified_at?: number | null;
}
export interface ContactCreate {
  legal_name: string;
  email: string;
  address?: string;
  reference?: string;
}
export interface Contact {
  id: string;
  legal_name: string;
  email: string;
  address?: string;
  reference?: string;
}
export interface Item {
  description: string;
  quantity: string;
  unit_usdc: string;
}
export interface InvoiceCreate {
  customer_id: string;
  wallet_id: string;
  due_date: string;
  items: Array<Item>;
  tax_mode?: string;
  tax_rate?: string;
  tax_usdc?: string;
  tax_notes?: string;
  accounting?: Record<string, unknown>;
  send_now?: false;
  reminder_opt_in?: false;
  customer_receipt_opt_in?: false;
}
export interface Invoice {
  id: string;
  customer_id?: string;
  request_id: string;
  number?: string;
  status: string;
  network?: string;
  receiver?: string;
  issued_at?: number;
  due_at?: number;
  total_atomic?: number;
  payment_atomic: number;
  tax_atomic?: number;
  items?: Array<Record<string, unknown>>;
}
export interface Me {
  api_version?: "1.0";
  id: string;
  plan: Record<string, unknown>;
  wallets: Array<Record<string, unknown>>;
}
export interface Event {
  id: string;
  api_version: "1.0";
  type: "payment_request.created" | "invoice.issued" | "invoice.voided" | "payment.confirmed" | "invoice.paid";
  occurred_at: number;
  data: Record<string, unknown>;
}
export interface SendApproval {
  user_approved: true;
}
export interface SendResult {
  id: string;
  mail_status: string;
}
export interface Page<T> { data: T[]; next_cursor: string | null }
export interface EventPage { data: Array<{cursor: number; event: Event}>; next_cursor: number }
export interface PageOptions { limit?: number; before?: string }
export interface WriteOptions { idempotencyKey?: string }
export class APIError extends Error { status: number; code: string | null; retryAfter: string | null; constructor(status: number, code?: string | null, retryAfter?: string | null) }
export class RateLimitError extends APIError {}
export class VerificationError extends Error {}
export class TransportError extends Error {}
export class PaymentProofClient {
 constructor(options: { baseUrl?: string; apiKey: string; fetchImplementation?: typeof fetch; timeoutMs?: number });
 close(): void;
 getAccount(): Promise<Me>;
 listRequests(options?: PageOptions): Promise<Page<Request>>;
 createRequest(body: RequestCreate, options?: WriteOptions): Promise<Request>;
 listContacts(options?: PageOptions): Promise<Page<Contact>>;
 createContact(body: ContactCreate, options?: WriteOptions): Promise<Contact>;
 listInvoices(options?: PageOptions): Promise<Page<Invoice>>;
 createInvoice(body: InvoiceCreate, options?: WriteOptions): Promise<Invoice>;
 getRequest(id: string): Promise<Request>;
 getInvoice(id: string): Promise<Invoice>;
 getInvoices(options?: PageOptions): Promise<Page<Invoice>>;
 sendInvoice(id: string, options: WriteOptions & {userApproved: true}): Promise<SendResult>;
 listEvents(options?: {after?: number; limit?: number}): Promise<EventPage>;
}
import type { Buffer } from 'node:buffer';
export function verifyWebhookSignature(payloadRaw: Buffer, headers: Record<string,string>, signingSecret: string, options?: {timestampToleranceSeconds?: number; now?: number}): Event;
