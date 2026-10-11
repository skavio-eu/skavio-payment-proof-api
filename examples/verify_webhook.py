"""Framework-neutral receiver verification. Use untouched request body bytes."""
import hashlib,hmac,time

def verify(secret,raw,timestamp,signature,now=None):
    if not isinstance(raw,bytes) or not isinstance(timestamp,str) or not timestamp.isascii() or not timestamp.isdecimal() or len(timestamp)>12:return False
    if abs((int(time.time()) if now is None else now)-int(timestamp))>300:return False
    expected='v1='+hmac.new(secret.encode(),timestamp.encode()+b'.'+raw,hashlib.sha256).hexdigest()
    return isinstance(signature,str) and hmac.compare_digest(expected,signature)
