"""Skavio Payment Proof SDK 1.0.0. No wallet signing or transfers."""
import hashlib
import hmac
import json
import math
import re
import time
import uuid
from typing import Any, Dict, Mapping, Optional, TypedDict
from urllib import request, error, parse

__version__ = '1.0.0'

class APIError(Exception):
    def __init__(self, status: int, code: Optional[str] = None, retry_after: Optional[str] = None):
        self.status, self.code, self.retry_after = status, code, retry_after
        super().__init__('Payment Proof HTTP %s' % status)

class RateLimitError(APIError):
    pass

class VerificationError(ValueError):
    pass

class TransportError(Exception):
    pass

class Page(TypedDict):
    data: list
    next_cursor: Any

# Complete schema-derived resource/input types are exported from types.py.
from .types import *

class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward credentials or replay a write through a redirect.

class PaymentProofClient:
    def __init__(self, base_url: str = 'https://www.skavio.eu/proof', api_key: str = '', timeout: float = 10):
        p = parse.urlsplit(base_url)
        if p.scheme not in ('https', 'http') or not p.hostname or p.username or p.password or p.query or p.fragment or (p.scheme == 'http' and p.hostname not in ('localhost', '127.0.0.1')):
            raise ValueError('HTTPS base URL required except localhost/127.0.0.1')
        if not isinstance(api_key, str) or not api_key.strip() or any(c.isspace() for c in api_key):
            raise ValueError('A nonempty bearer key is required')
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError('Positive finite timeout required')
        self.base_url, self.timeout = base_url.rstrip('/'), timeout
        self.__api_key = api_key
        self._opener = request.build_opener(_NoRedirect())

    def __repr__(self):
        return 'PaymentProofClient()'

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self.__api_key = ''

    def _call(self, method: str, path: str, body=None, query=None, idempotency_key=None) -> Any:
        if not self.__api_key:
            raise ValueError('Client is closed')
        headers = {'Authorization': 'Bearer ' + self.__api_key, 'Accept': 'application/json', 'Content-Type': 'application/json'}
        if method == 'POST':
            key = str(uuid.uuid4()) if idempotency_key is None else idempotency_key
            if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9_-]{16,80}', key):
                raise ValueError('Invalid idempotency key')
            headers['Idempotency-Key'] = key
        url = self.base_url + path
        if query:
            url += '?' + parse.urlencode({k: v for k, v in query.items() if v is not None})
        req = request.Request(url, data=None if body is None else json.dumps(body, allow_nan=False).encode(), headers=headers, method=method)
        try:
            response = self._opener.open(req, timeout=self.timeout)
        except error.HTTPError as exc:
            response = exc
        except (OSError, error.URLError):
            raise TransportError('Payment Proof transport failure') from None
        try:
            with response:
                status, raw, retry = response.code, response.read(), response.headers.get('Retry-After')
        except OSError:
            raise TransportError('Payment Proof transport failure') from None
        try:
            value = json.loads(raw) if raw else None
        except (ValueError, UnicodeError):
            value = None
            if 200 <= status < 300:
                raise APIError(status, 'invalid_json') from None
        if not 200 <= status < 300:
            code = value.get('error') if isinstance(value, dict) else None
            raise (RateLimitError if status == 429 else APIError)(status, code, retry)
        return value

    @staticmethod
    def _id(value: str) -> str:
        if not isinstance(value, str) or not value:
            raise ValueError('Resource ID required')
        return parse.quote(value, safe='')

    @staticmethod
    def _page(limit, before):
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError('limit must be 1–100')
        if before is not None and (not isinstance(before, str) or not before or len(before) > 100):
            raise ValueError('Invalid cursor')
        return {'limit': limit, 'before': before}

    def get_account(self) -> 'Me':
        return self._call('GET', '/v1/me')

    def list_requests(self, *, limit: int = 50, before: Optional[str] = None) -> 'RequestPage':
        return self._call('GET', '/v1/requests', query=self._page(limit, before))

    def create_request(self, body: 'RequestCreate', *, idempotency_key: Optional[str] = None) -> 'Request':
        return self._call('POST', '/v1/requests', body, idempotency_key=idempotency_key)

    def get_request(self, request_id: str) -> 'Request':
        return self._call('GET', '/v1/requests/' + self._id(request_id))

    def list_contacts(self, *, limit: int = 50, before: Optional[str] = None) -> 'ContactPage':
        return self._call('GET', '/v1/contacts', query=self._page(limit, before))

    def create_contact(self, body: 'ContactCreate', *, idempotency_key: Optional[str] = None) -> 'Contact':
        return self._call('POST', '/v1/contacts', body, idempotency_key=idempotency_key)

    def list_invoices(self, *, limit: int = 50, before: Optional[str] = None) -> 'InvoicePage':
        return self._call('GET', '/v1/invoices', query=self._page(limit, before))

    def create_invoice(self, body: 'InvoiceCreate', *, idempotency_key: Optional[str] = None) -> 'Invoice':
        if any(body.get(k, False) is not False for k in ('send_now', 'reminder_opt_in', 'customer_receipt_opt_in')):
            raise ValueError('Automatic email options must be false')
        return self._call('POST', '/v1/invoices', body, idempotency_key=idempotency_key)

    def get_invoice(self, invoice_id: str) -> 'Invoice':
        return self._call('GET', '/v1/invoices/' + self._id(invoice_id))

    def send_invoice(self, invoice_id: str, *, user_approved: bool = False, idempotency_key: Optional[str] = None) -> 'SendResult':
        if user_approved is not True:
            raise ValueError('Explicit user approval required')
        return self._call('POST', '/v1/invoices/' + self._id(invoice_id) + '/send', {'user_approved': True}, idempotency_key=idempotency_key)

    def list_events(self, *, after: int = 0, limit: int = 50) -> 'EventPage':
        self._page(limit, None)
        if type(after) is not int or after < 0:
            raise ValueError('after must be a nonnegative integer')
        return self._call('GET', '/v1/events', query={'after': after, 'limit': limit})


def verify_webhook(payload_raw: bytes, headers: Mapping[str, str], signing_secret: str, timestamp_tolerance_seconds: float = 300, now: Optional[float] = None) -> 'Event':
    if not isinstance(payload_raw, bytes) or not isinstance(signing_secret, str) or not signing_secret or not isinstance(headers, Mapping):
        raise VerificationError('Invalid verification inputs')
    current = time.time() if now is None else now
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in (current, timestamp_tolerance_seconds)) or timestamp_tolerance_seconds < 0:
        raise VerificationError('Invalid verification clock')
    hs = {k.lower(): v for k, v in headers.items() if isinstance(k, str)}
    stamp, signature, ident = (hs.get(k) for k in ('x-skavio-timestamp', 'x-skavio-signature', 'x-skavio-event-id'))
    if not isinstance(stamp, str) or not re.fullmatch(r'[0-9]{1,12}', stamp) or abs(current - int(stamp)) > timestamp_tolerance_seconds:
        raise VerificationError('Invalid or expired timestamp')
    if not isinstance(signature, str) or not re.fullmatch(r'v1=[0-9a-f]{64}', signature):
        raise VerificationError('Invalid signature')
    expected = 'v1=' + hmac.new(signing_secret.encode(), stamp.encode() + b'.' + payload_raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise VerificationError('Signature mismatch')
    try:
        event = json.loads(payload_raw)
    except (ValueError, UnicodeError):
        raise VerificationError('Invalid event JSON') from None
    if not isinstance(event, dict) or not isinstance(ident, str) or not ident or event.get('id') != ident or event.get('api_version') != '1.0':
        raise VerificationError('Invalid event identity or version')
    return event
