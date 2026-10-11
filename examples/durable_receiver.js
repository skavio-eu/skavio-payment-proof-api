// Receiver-owned synchronous SQLite adapter (prepare/run + transaction).
// Supply an existing adapter such as better-sqlite3; this example installs nothing.
// Initialize tables once. A local outbox consumer validates saved order mapping,
// exact network/amount and performs idempotent business effects before fulfillment.
const {verify}=require('./verify_webhook');
const schema=`CREATE TABLE IF NOT EXISTS received_events(id TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS local_outbox(event_id TEXT PRIMARY KEY REFERENCES received_events(id),
body TEXT NOT NULL, processed INTEGER NOT NULL DEFAULT 0);`;
function acknowledge(db,secret,raw,headers,now){
 if(!verify(secret,raw,headers['x-skavio-timestamp'],headers['x-skavio-signature'],now))return 401;
 let event;
 try {event=JSON.parse(raw.toString('utf8'));}catch{return 400;}
 if(!event||event.api_version!=='1.0'||typeof event.id!=='string'||!event.id||event.id!==headers['x-skavio-event-id'])return 400;
 // transaction throws on failure: caller must return non-2xx so sender retries.
 db.transaction(()=>{
  const inserted=db.prepare('INSERT OR IGNORE INTO received_events(id) VALUES(?)').run(event.id);
  if(inserted.changes)db.prepare('INSERT INTO local_outbox(event_id,body) VALUES(?,?)').run(event.id,raw.toString('utf8'));
 })();
 return 204;
}
module.exports={schema,acknowledge};
