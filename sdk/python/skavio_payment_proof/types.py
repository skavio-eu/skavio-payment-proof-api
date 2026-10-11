from typing import TypedDict, List, Dict, Any, Optional, Literal

class _ErrorRequired(TypedDict):
    error: str
class Error(_ErrorRequired, total=False):
    pass
class _RequestCreateRequired(TypedDict):
    wallet_id: str
    amount_usdc: str
    description: str
class RequestCreate(_RequestCreateRequired, total=False):
    customer_label: str
    expected_payer: str
    valid_hours: int
class _RequestRequired(TypedDict):
    id: str
    network: str
    status: str
    url: str
    amount_atomic: int
class Request(_RequestRequired, total=False):
    wallet_id: str
    receiver_address: str
    customer_label: str
    description: str
    quoted_amount_atomic: int
    expected_payer: Optional[str]
    created_at: int
    expires_at: int
    tx_hash: Optional[str]
    verified_at: Optional[int]
class _ContactCreateRequired(TypedDict):
    legal_name: str
    email: str
class ContactCreate(_ContactCreateRequired, total=False):
    address: str
    reference: str
class _ContactRequired(TypedDict):
    id: str
    legal_name: str
    email: str
class Contact(_ContactRequired, total=False):
    address: str
    reference: str
class _ItemRequired(TypedDict):
    description: str
    quantity: str
    unit_usdc: str
class Item(_ItemRequired, total=False):
    pass
class _InvoiceCreateRequired(TypedDict):
    customer_id: str
    wallet_id: str
    due_date: str
    items: List[Item]
class InvoiceCreate(_InvoiceCreateRequired, total=False):
    tax_mode: str
    tax_rate: str
    tax_usdc: str
    tax_notes: str
    accounting: Dict[str, Any]
    send_now: Literal[False]
    reminder_opt_in: Literal[False]
    customer_receipt_opt_in: Literal[False]
class _InvoiceRequired(TypedDict):
    id: str
    request_id: str
    status: str
    payment_atomic: int
class Invoice(_InvoiceRequired, total=False):
    customer_id: str
    number: str
    network: str
    receiver: str
    issued_at: int
    due_at: int
    total_atomic: int
    tax_atomic: int
    items: List[Dict[str, Any]]
class _MeRequired(TypedDict):
    id: str
    plan: Dict[str, Any]
    wallets: List[Dict[str, Any]]
class Me(_MeRequired, total=False):
    api_version: Literal['1.0']
class _EventRequired(TypedDict):
    id: str
    api_version: Literal['1.0']
    type: str
    occurred_at: int
    data: Dict[str, Any]
class Event(_EventRequired, total=False):
    pass
class _SendApprovalRequired(TypedDict):
    user_approved: Literal[True]
class SendApproval(_SendApprovalRequired, total=False):
    pass
class _SendResultRequired(TypedDict):
    id: str
    mail_status: str
class SendResult(_SendResultRequired, total=False):
    pass
class RequestPage(TypedDict):
    data: List[Request]
    next_cursor: Optional[str]
class ContactPage(TypedDict):
    data: List[Contact]
    next_cursor: Optional[str]
class InvoicePage(TypedDict):
    data: List[Invoice]
    next_cursor: Optional[str]
class EventEntry(TypedDict):
    cursor: int
    event: Event
class EventPage(TypedDict):
    data: List[EventEntry]
    next_cursor: int
