// Node.js: verify the untouched body Buffer BEFORE JSON parsing.
const crypto=require('node:crypto');
function verify(secret,raw,timestamp,signature,now=Math.floor(Date.now()/1000)){
 if(!Buffer.isBuffer(raw)||typeof timestamp!=='string'||!/^\d{1,12}$/.test(timestamp)||Math.abs(now-Number(timestamp))>300||typeof signature!=='string')return false;
 const expected=Buffer.from('v1='+crypto.createHmac('sha256',secret).update(timestamp+'.').update(raw).digest('hex'),'ascii');
 const received=Buffer.from(signature,'ascii');
 return expected.length===received.length&&crypto.timingSafeEqual(expected,received);
}
module.exports={verify};
