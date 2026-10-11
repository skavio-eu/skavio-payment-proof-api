import { createHmac, timingSafeEqual, randomUUID } from 'node:crypto';
export class APIError extends Error {
  constructor(status, code = null, retryAfter = null) {
    super(`Payment Proof HTTP ${status}`); this.name = 'APIError';
    this.status = status; this.code = code; this.retryAfter = retryAfter;
  }
}
export class RateLimitError extends APIError {}
export class VerificationError extends Error {}
export class TransportError extends Error {}
export class PaymentProofClient {
  #apiKey; #fetch;
  constructor({baseUrl = 'https://www.skavio.eu/proof', apiKey, fetchImplementation = globalThis.fetch, timeoutMs = 10000} = {}) {
    const u = new URL(baseUrl);
    if (!['https:', 'http:'].includes(u.protocol) || u.username || u.password || u.search || u.hash || (u.protocol === 'http:' && !['localhost','127.0.0.1'].includes(u.hostname))) throw new TypeError('HTTPS base URL required except loopback');
    if (typeof apiKey !== 'string' || !apiKey || /\s/.test(apiKey)) throw new TypeError('Bearer key required');
    if (!Number.isFinite(timeoutMs) || timeoutMs <= 0 || typeof fetchImplementation !== 'function') throw new TypeError('Invalid transport options');
    this.baseUrl = baseUrl.replace(/\/$/, ''); this.timeoutMs = timeoutMs; this.#apiKey = apiKey; this.#fetch = fetchImplementation;
  }
  close() { this.#apiKey = ''; }
  async _call(method, path, body, query, idempotencyKey) {
    if (!this.#apiKey) throw new TypeError('Client is closed');
    const headers = {Authorization: `Bearer ${this.#apiKey}`, Accept: 'application/json', 'Content-Type': 'application/json'};
    if (method === 'POST') {
      const key = idempotencyKey === undefined ? randomUUID() : idempotencyKey;
      if (typeof key !== 'string' || !/^[A-Za-z0-9_-]{16,80}$/.test(key)) throw new TypeError('Invalid idempotency key');
      headers['Idempotency-Key'] = key;
    }
    const url = new URL(this.baseUrl + path);
    for (const [k,v] of Object.entries(query || {})) if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);
    try {
      let response, raw;
      try {
        response = await this.#fetch(url.toString(), {method, headers, body: body === undefined ? undefined : JSON.stringify(body), signal: controller.signal, redirect: 'manual'});
        raw = await response.text();
      } catch { throw new TransportError('Payment Proof transport failure'); }
      let value = null;
      try { value = raw ? JSON.parse(raw) : null; }
      catch { if (response.ok) throw new APIError(response.status, 'invalid_json'); }
      if (!response.ok) throw new (response.status === 429 ? RateLimitError : APIError)(response.status, value?.error ?? null, response.headers.get('Retry-After'));
      return value;
    } finally { clearTimeout(timer); }
  }
  _id(id) { if (typeof id !== 'string' || !id) throw new TypeError('Resource ID required'); return encodeURIComponent(id); }
  _page({limit = 50, before} = {}) {
    if (!Number.isInteger(limit) || limit < 1 || limit > 100 || (before !== undefined && (typeof before !== 'string' || !before || before.length > 100))) throw new TypeError('Invalid pagination');
    return {limit, before};
  }
  getAccount() { return this._call('GET', '/v1/me'); }
  listRequests(options) { return this._call('GET', '/v1/requests', undefined, this._page(options)); }
  createRequest(body, {idempotencyKey} = {}) { return this._call('POST', '/v1/requests', body, undefined, idempotencyKey); }
  getRequest(id) { return this._call('GET', '/v1/requests/' + this._id(id)); }
  listContacts(options) { return this._call('GET', '/v1/contacts', undefined, this._page(options)); }
  createContact(body, {idempotencyKey} = {}) { return this._call('POST', '/v1/contacts', body, undefined, idempotencyKey); }
  listInvoices(options) { return this._call('GET', '/v1/invoices', undefined, this._page(options)); }
  getInvoices(options) { return this.listInvoices(options); }
  createInvoice(body, {idempotencyKey} = {}) {
    if (['send_now','reminder_opt_in','customer_receipt_opt_in'].some(k => body[k] !== undefined && body[k] !== false)) throw new TypeError('Automatic email options must be false');
    return this._call('POST', '/v1/invoices', body, undefined, idempotencyKey);
  }
  getInvoice(id) { return this._call('GET', '/v1/invoices/' + this._id(id)); }
  sendInvoice(id, {userApproved = false, idempotencyKey} = {}) {
    if (userApproved !== true) throw new TypeError('Explicit user approval required');
    return this._call('POST', '/v1/invoices/' + this._id(id) + '/send', {user_approved: true}, undefined, idempotencyKey);
  }
  listEvents({after = 0, limit = 50} = {}) {
    this._page({limit}); if (!Number.isInteger(after) || after < 0) throw new TypeError('Invalid event cursor');
    return this._call('GET', '/v1/events', undefined, {after, limit});
  }
}
export function verifyWebhookSignature(payloadRaw, headers, signingSecret, {timestampToleranceSeconds = 300, now = Date.now()/1000} = {}) {
  const fail = message => { throw new VerificationError(message); };
  if (!Buffer.isBuffer(payloadRaw) || typeof signingSecret !== 'string' || !signingSecret || !headers || typeof headers !== 'object' || !Number.isFinite(now) || !Number.isFinite(timestampToleranceSeconds) || timestampToleranceSeconds < 0) fail('Invalid verification inputs');
  const hs = Object.fromEntries(Object.entries(headers).map(([k,v]) => [k.toLowerCase(),v]));
  const stamp = hs['x-skavio-timestamp'], signature = hs['x-skavio-signature'], id = hs['x-skavio-event-id'];
  if (typeof stamp !== 'string' || !/^[0-9]{1,12}$/.test(stamp) || Math.abs(now - Number(stamp)) > timestampToleranceSeconds) fail('Invalid or expired timestamp');
  if (typeof signature !== 'string' || !/^v1=[0-9a-f]{64}$/.test(signature)) fail('Invalid signature');
  const expected = createHmac('sha256', signingSecret).update(stamp + '.').update(payloadRaw).digest();
  if (!timingSafeEqual(expected, Buffer.from(signature.slice(3),'hex'))) fail('Signature mismatch');
  let event; try { event = JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(payloadRaw)); } catch { fail('Invalid event JSON'); }
  if (!event || Array.isArray(event) || typeof id !== 'string' || !id || event.id !== id || event.api_version !== '1.0') fail('Invalid event identity or version');
  return event;
}
