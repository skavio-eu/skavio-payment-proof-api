"""Receiver-owned SQLite outbox example; no network I/O or payment side effects.
Create schema once during receiver setup. acknowledge() returns 204 only on commit.
Your local consumer must map request IDs, validate exact amount/network and apply
business effects idempotently. Keep this database separate from Payment Proof.
"""
import json
from verify_webhook import verify

SCHEMA = '''
CREATE TABLE IF NOT EXISTS received_events(id TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS local_outbox(
 event_id TEXT PRIMARY KEY REFERENCES received_events(id),body TEXT NOT NULL,
 processed INTEGER NOT NULL DEFAULT 0);
'''

def acknowledge(connection, secret, raw, headers, now=None):
    if not verify(secret, raw, headers.get('X-Skavio-Timestamp'),
                  headers.get('X-Skavio-Signature'), now):
        return 401
    try:
        event = json.loads(raw)
        if (not isinstance(event, dict) or event.get('api_version') != '1.0'
                or not isinstance(event.get('id'), str) or not event['id']
                or event['id'] != headers.get('X-Skavio-Event-Id')):
            return 400
    except (ValueError, UnicodeError):
        return 400
    # Use a dedicated idle connection. Failure rolls back both dedup and outbox.
    with connection:
        connection.execute('BEGIN IMMEDIATE')
        inserted = connection.execute(
            'INSERT OR IGNORE INTO received_events(id) VALUES(?)', (event['id'],)).rowcount
        if inserted:
            connection.execute('INSERT INTO local_outbox(event_id,body) VALUES(?,?)',
                               (event['id'], raw.decode('utf-8')))
    return 204
