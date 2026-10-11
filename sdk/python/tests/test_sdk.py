import hashlib,hmac,io,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError,URLError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from skavio_payment_proof import *
ROOT=Path(__file__).resolve().parents[2]
EX=json.loads((ROOT/'contract_examples.json').read_text())
class Response(io.BytesIO):
 def __init__(self,body=b'{}',status=200,headers=None):
  super().__init__(body);self.code=status;self.headers=headers or {}
class SDKTests(unittest.TestCase):
 def setUp(self):
  self.client=PaymentProofClient(api_key='synthetic-only')
  self.calls=[]
 def transport(self,req,timeout):
  self.calls.append((req,timeout));return Response(json.dumps(EX['Me']).encode())
 def test_account_headers_timeout_close(self):
  r=Response(json.dumps(EX['Me']).encode())
  with patch.object(self.client._opener,'open',return_value=r) as p:
   self.assertEqual(self.client.get_account(),EX['Me']);req=p.call_args.args[0]
   self.assertEqual(req.get_header('Authorization'),'Bearer synthetic-only');self.assertEqual(p.call_args.kwargs['timeout'],10)
  self.assertTrue(r.closed)
 def test_context_and_repr(self):
  self.assertNotIn('synthetic-only',repr(self.client))
  with self.client:pass
  with self.assertRaises(ValueError):self.client.get_account()
 def test_secure_urls(self):
  for url in ('http://example.test','ftp://localhost','https://user:pass@example.test','https://example.test?x=1','https://example.test#x'):
   with self.subTest(url=url),self.assertRaises(ValueError):PaymentProofClient(url,'synthetic')
  for url in ('http://localhost:123/proof','http://127.0.0.1:123/proof'):PaymentProofClient(url,'synthetic')
 def test_invalid_options(self):
  for timeout in (0,-1,True,float('nan')):
   with self.assertRaises(ValueError):PaymentProofClient(api_key='synthetic',timeout=timeout)
  with self.assertRaises(ValueError):PaymentProofClient(api_key='')
 def test_all_routes_and_contract(self):
  cases=[('get_account',[],{},'Me','/v1/me'),('create_request',[EX['RequestCreate']],{},'Request','/v1/requests'),('create_contact',[EX['ContactCreate']],{},'Contact','/v1/contacts'),('create_invoice',[EX['InvoiceCreate']],{},'Invoice','/v1/invoices'),('get_request',['synthetic'],{},'Request','/v1/requests/synthetic'),('get_invoice',['synthetic'],{},'Invoice','/v1/invoices/synthetic'),('send_invoice',['synthetic'],{'user_approved':True},'SendResult','/v1/invoices/synthetic/send')]
  for name,args,kwargs,shape,path in cases:
   with self.subTest(name=name),patch.object(self.client._opener,'open',return_value=Response(json.dumps(EX[shape]).encode())) as p:
    self.assertEqual(getattr(self.client,name)(*args,**kwargs),EX[shape]);self.assertTrue(p.call_args.args[0].full_url.endswith(path))
 def test_pagination(self):
  for name in ('list_requests','list_contacts','list_invoices'):
   with patch.object(self.client._opener,'open',side_effect=self.transport):getattr(self.client,name)(limit=7,before='opaque+cursor')
   self.assertIn('limit=7&before=opaque%2Bcursor',self.calls[-1][0].full_url)
  with patch.object(self.client._opener,'open',side_effect=self.transport):self.client.list_events(after=12,limit=8)
  self.assertIn('after=12&limit=8',self.calls[-1][0].full_url)
 def test_bad_pagination(self):
  for limit in (0,101,True,1.5):
   with self.assertRaises(ValueError):self.client.list_requests(limit=limit)
  with self.assertRaises(ValueError):self.client.list_events(after=-1)
 def test_uuid_and_override(self):
  with patch.object(self.client._opener,'open',side_effect=self.transport):
   self.client.create_contact(EX['ContactCreate']);self.client.create_contact(EX['ContactCreate'],idempotency_key='stable-business-key-123')
  self.assertRegex(self.calls[0][0].get_header('Idempotency-key'),r'^[0-9a-f-]{36}$')
  self.assertEqual(self.calls[1][0].get_header('Idempotency-key'),'stable-business-key-123')
 def test_invalid_idempotency(self):
  with self.assertRaises(ValueError):self.client.create_contact(EX['ContactCreate'],idempotency_key='short')
 def test_send_guard(self):
  for value in (False,1,'true'):
   with self.assertRaises(ValueError):self.client.send_invoice('id',user_approved=value)
 def test_invoice_guard(self):
  with self.assertRaises(ValueError):self.client.create_invoice(dict(EX['InvoiceCreate'],send_now=True))
 def test_errors(self):
  for status in (401,403,404,409,422,429,500,503):
   r=HTTPError('https://example.test',status,'error',{'Retry-After':'9'},io.BytesIO(b'{"error":"synthetic_error"}'))
   with self.subTest(status=status),patch.object(self.client._opener,'open',side_effect=r),self.assertRaises(APIError) as ctx:self.client.get_account()
   self.assertEqual(ctx.exception.status,status);self.assertEqual(ctx.exception.code,'synthetic_error');self.assertEqual(ctx.exception.retry_after,'9')
   self.assertEqual(isinstance(ctx.exception,RateLimitError),status==429)
 def test_empty_and_nonjson(self):
  for raw,status,result in ((b'',204,None),(b'',200,None)):
   with patch.object(self.client._opener,'open',return_value=Response(raw,status)):self.assertEqual(self.client.get_account(),result)
  with patch.object(self.client._opener,'open',return_value=Response(b'html')),self.assertRaises(APIError):self.client.get_account()
 def test_nonjson_error(self):
  with patch.object(self.client._opener,'open',return_value=Response(b'html',503)),self.assertRaises(APIError) as c:self.client.get_account()
  self.assertIsNone(c.exception.code)
 def test_timeout_no_retry(self):
  with patch.object(self.client._opener,'open',side_effect=URLError('synthetic-only')) as p,self.assertRaises(TransportError):self.client.create_contact(EX['ContactCreate'])
  self.assertEqual(p.call_count,1)
 def test_redirect_blocked(self):
  from skavio_payment_proof import _NoRedirect
  self.assertIsNone(_NoRedirect().redirect_request(None,None,302,'',{},'https://example.test'))
 def webhook(self,raw=None,stamp='000000001000'):
  raw=json.dumps(EX['Event']).encode() if raw is None else raw
  headers={'X-Skavio-Timestamp':stamp,'X-Skavio-Signature':'v1='+hmac.new(b'synthetic',stamp.encode()+b'.'+raw,hashlib.sha256).hexdigest(),'X-Skavio-Event-Id':EX['Event']['id']}
  return raw,headers
 def test_webhook_raw_timestamp(self):
  raw,hs=self.webhook();self.assertEqual(verify_webhook(raw,hs,'synthetic',now=1000),EX['Event'])
 def test_webhook_tamper(self):
  raw,hs=self.webhook()
  with self.assertRaises(VerificationError):verify_webhook(raw+b' ',hs,'synthetic',now=1000)
 def test_webhook_expired_future(self):
  raw,hs=self.webhook()
  for now in (699,1301):
   with self.assertRaises(VerificationError):verify_webhook(raw,hs,'synthetic',now=now)
 def test_webhook_id(self):
  raw,hs=self.webhook();hs['X-Skavio-Event-Id']='other'
  with self.assertRaises(VerificationError):verify_webhook(raw,hs,'synthetic',now=1000)
 def test_webhook_bad_inputs(self):
  raw,hs=self.webhook()
  for payload,secret in ((raw,''),('text','synthetic'),(raw,None)):
   with self.assertRaises(VerificationError):verify_webhook(payload,hs,secret,now=1000)
 def test_webhook_bad_json_and_version(self):
  for raw in (b'not-json',b'{"id":"synthetic","api_version":"2"}'):
   raw,hs=self.webhook(raw)
   with self.assertRaises(VerificationError):verify_webhook(raw,hs,'synthetic',now=1000)
 def test_webhook_signature_format(self):
  raw,hs=self.webhook();hs['X-Skavio-Signature']='v1=nope'
  with self.assertRaises(VerificationError):verify_webhook(raw,hs,'synthetic',now=1000)
