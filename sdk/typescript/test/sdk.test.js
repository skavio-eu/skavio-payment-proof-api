import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHmac} from 'node:crypto';
import {inspect} from 'node:util';
import {PaymentProofClient,APIError,RateLimitError,TransportError,verifyWebhookSignature,VerificationError} from '../src/index.js';
const ex=JSON.parse(readFileSync(new URL('../../contract_examples.json',import.meta.url)));
const spec=JSON.parse(readFileSync(new URL('../../../openapi.json',import.meta.url)));
const response=(body,status=200,headers={})=>new Response(status===204?null:typeof body==='string'?body:JSON.stringify(body),{status,headers});
const make=fetchImplementation=>new PaymentProofClient({apiKey:'synthetic-only',fetchImplementation});
for(const [method,shape,path,args] of [ ['getAccount','Me','/v1/me',[]],['createRequest','Request','/v1/requests',[ex.RequestCreate]],['createContact','Contact','/v1/contacts',[ex.ContactCreate]],['createInvoice','Invoice','/v1/invoices',[ex.InvoiceCreate]],['getRequest','Request','/v1/requests/synthetic',['synthetic']],['getInvoice','Invoice','/v1/invoices/synthetic',['synthetic']],['sendInvoice','SendResult','/v1/invoices/synthetic/send',['synthetic',{userApproved:true}]]]) {
 test(`contract ${method}`,async()=>{let call;const c=make(async(url,opts)=>{call={url,opts};return response(ex[shape]);});assert.deepEqual(await c[method](...args),ex[shape]);assert.ok(call.url.endsWith(path));assert.equal(call.opts.headers.Authorization,'Bearer synthetic-only');assert.equal(call.opts.redirect,'manual');
 for(const key of spec.components.schemas[shape].required)assert.ok(key in ex[shape]);
 });
}
for(const status of [401,403,404,409,422,429,500,503])test(`HTTP ${status}`,async()=>{
 const c=make(async()=>response({error:'synthetic_error'},status,{'Retry-After':'9'}));
 await assert.rejects(c.getAccount(),e=>e instanceof APIError && e.status===status && e.code==='synthetic_error' && e.retryAfter==='9' && (status!==429 || e instanceof RateLimitError));
});
test('pagination',async()=>{const urls=[];const c=make(async url=>{urls.push(url);return response({data:[],next_cursor:null});});for(const m of ['listRequests','listContacts','listInvoices','getInvoices'])await c[m]({limit:7,before:'opaque+cursor'});await c.listEvents({after:12,limit:8});assert.ok(urls.slice(0,4).every(u=>new URL(u).searchParams.get('before')==='opaque+cursor'));assert.equal(new URL(urls[4]).searchParams.get('after'),'12');});
test('input guards',()=>{const c=make(()=>{});for(const limit of [0,101,1.5])assert.throws(()=>c.listRequests({limit}));assert.throws(()=>c.listEvents({after:-1}));assert.throws(()=>c.sendInvoice('id'));assert.throws(()=>c.sendInvoice('id',{userApproved:1}));assert.throws(()=>c.createInvoice({...ex.InvoiceCreate,send_now:true}));});
test('HTTPS guard',()=>{for(const baseUrl of ['http://example.test','ftp://localhost','https://user:pass@example.test','https://example.test?q=1'])assert.throws(()=>new PaymentProofClient({baseUrl,apiKey:'synthetic'}));for(const baseUrl of ['http://localhost:123/proof','http://127.0.0.1:123/proof'])new PaymentProofClient({baseUrl,apiKey:'synthetic'});});
test('private token and close',async()=>{const c=make(()=>{});assert.ok(!inspect(c).includes('synthetic-only'));c.close();await assert.rejects(c.getAccount());});
test('empty and invalid JSON',async()=>{assert.equal(await make(async()=>response('',204)).getAccount(),null);await assert.rejects(make(async()=>response('html')).getAccount(),e=>e.code==='invalid_json');await assert.rejects(make(async()=>response('html',503)).getAccount(),e=>e.status===503&&e.code===null);});
test('UUID and stable override',async()=>{const keys=[];const c=make(async(u,o)=>{keys.push(o.headers['Idempotency-Key']);return response(ex.Contact);});await c.createContact(ex.ContactCreate);await c.createContact(ex.ContactCreate,{idempotencyKey:'stable-synthetic-key'});assert.match(keys[0],/^[a-f0-9-]{36}$/);assert.equal(keys[1],'stable-synthetic-key');await assert.rejects(c.createContact(ex.ContactCreate,{idempotencyKey:'short'}));});
test('timeout no write retry',async()=>{let calls=0;const c=new PaymentProofClient({apiKey:'synthetic',timeoutMs:5,fetchImplementation:async(u,o)=>{calls++;return new Promise((r,j)=>o.signal.addEventListener('abort',()=>j(new Error('synthetic'))));}});await assert.rejects(c.createContact(ex.ContactCreate),TransportError);assert.equal(calls,1);});
test('synthetic creation replay and conflict',async()=>{const saved=new Map();let count=0;const c=make(async(u,o)=>{const key=o.headers['Idempotency-Key'],payload=o.body,old=saved.get(key);if(old)return old.payload===payload?response(old.result,201):response({error:'conflict'},409);const result={...JSON.parse(payload),id:`synthetic-${++count}`};saved.set(key,{payload,result});return response(result,201);});for(const [m,b] of [['createContact',ex.ContactCreate],['createRequest',ex.RequestCreate],['createInvoice',ex.InvoiceCreate]]){const opts={idempotencyKey:`stable-synthetic-${m}`};assert.deepEqual(await c[m](b,opts),await c[m](b,opts));await assert.rejects(c[m]({...b,description:'changed'},opts),e=>e.status===409);}assert.equal(count,3);});
const raw=Buffer.from(JSON.stringify(ex.Event)),stamp='000000001000';
const headers={'X-Skavio-Timestamp':stamp,'X-Skavio-Signature':'v1='+createHmac('sha256','synthetic').update(stamp+'.').update(raw).digest('hex'),'X-Skavio-Event-Id':ex.Event.id};
test('webhook exact raw timestamp',()=>assert.deepEqual(verifyWebhookSignature(raw,headers,'synthetic',{now:1000}),ex.Event));
test('webhook tamper',()=>assert.throws(()=>verifyWebhookSignature(Buffer.concat([raw,Buffer.from(' ')]),headers,'synthetic',{now:1000}),VerificationError));
test('webhook replay window and future',()=>{for(const now of [699,1301])assert.throws(()=>verifyWebhookSignature(raw,headers,'synthetic',{now}),VerificationError);});
test('webhook identity bound',()=>assert.throws(()=>verifyWebhookSignature(raw,{...headers,'X-Skavio-Event-Id':'other'},'synthetic',{now:1000}),VerificationError));
test('webhook invalid inputs',()=>{for(const secret of ['',null])assert.throws(()=>verifyWebhookSignature(raw,headers,secret,{now:1000}),VerificationError);assert.throws(()=>verifyWebhookSignature('text',headers,'synthetic',{now:1000}),VerificationError);});
test('webhook malformed signature',()=>assert.throws(()=>verifyWebhookSignature(raw,{...headers,'X-Skavio-Signature':'v1=bad'},'synthetic',{now:1000}),VerificationError));
test('native global fetch can be mocked',async()=>{const original=globalThis.fetch;globalThis.fetch=async()=>response(ex.Me);try{assert.deepEqual(await new PaymentProofClient({apiKey:'synthetic'}).getAccount(),ex.Me);}finally{globalThis.fetch=original;}});
for(const reason of ['bad','revoked','expired','write-only'])test(`synthetic ${reason} credential rejected`,async()=>{await assert.rejects(make(async()=>response({error:`synthetic_${reason}`},401)).getAccount(),e=>e.status===401);});
