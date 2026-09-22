import secrets,time,unittest
class Exchange:
 def __init__(self,ttl=600): self.tx={};self.h={};self.ttl=ttl;self.stages=[]
 def mark(self,name): self.stages.append(name)
 def begin(self): 
  t=secrets.token_urlsafe(24);s=secrets.token_urlsafe(32);self.tx[t]=(s,time.time()+self.ttl);return t,s
 def callback(self,t,state,adapter):
  self.mark("GOOGLE_CALLBACK_ENTERED")
  if t not in self.tx: raise ValueError("TX")
  s,e=self.tx.pop(t)
  if time.time()>e: raise ValueError("EXPIRED_TX")
  if not state or not secrets.compare_digest(s,state): raise ValueError("STATE")
  self.mark("CODE_EXCHANGE_STARTED");token=adapter();self.mark("CODE_EXCHANGE_PASS")
  if not isinstance(token,str) or not token: raise ValueError("EXCHANGE")
  hid=secrets.token_urlsafe(32);self.h[hid]=(token,t,time.time()+self.ttl);self.mark("HANDOFF_READY");return hid
 def redeem(self,hid,t):
  if hid not in self.h: raise ValueError("HANDOFF")
  token,b,e=self.h.pop(hid);self.mark("REDEEM_PASS")
  if time.time()>e: raise ValueError("EXPIRED_HANDOFF")
  if b!=t: raise ValueError("BINDING")
  return token
class T(unittest.TestCase):
 def test_ttl_and_safe_stages(self):
  x=Exchange();self.assertEqual(x.ttl,600);t,state=x.begin();h=x.callback(t,state,lambda:"synthetic");self.assertEqual(x.redeem(h,t),"synthetic");self.assertEqual(x.stages,["GOOGLE_CALLBACK_ENTERED","CODE_EXCHANGE_STARTED","CODE_EXCHANGE_PASS","HANDOFF_READY","REDEEM_PASS"])
 def test_success_single_use(self):
  x=Exchange();t,s=x.begin();h=x.callback(t,s,lambda:"synthetic");self.assertEqual(x.redeem(h,t),"synthetic")
  with self.assertRaises(ValueError):x.redeem(h,t)
 def test_wrong_missing_state(self):
  for s2 in ("wrong",""):
   x=Exchange();t,s=x.begin()
   with self.assertRaises(ValueError):x.callback(t,s2,lambda:"synthetic")
 def test_expired_transaction(self):
  x=Exchange(-1);t,s=x.begin()
  with self.assertRaises(ValueError):x.callback(t,s,lambda:"synthetic")
 def test_exchange_fail_malformed(self):
  for f in (lambda:(_ for _ in ()).throw(RuntimeError()),lambda:""):
   x=Exchange();t,s=x.begin()
   with self.assertRaises(Exception):x.callback(t,s,f)
 def test_unknown_expired_binding(self):
  x=Exchange();t,s=x.begin()
  with self.assertRaises(ValueError):x.redeem("guess",t)
  x=Exchange(-1);t,s=x.begin()
  with self.assertRaises(ValueError):x.callback(t,s,lambda:"synthetic")
  x=Exchange();t,s=x.begin();h=x.callback(t,s,lambda:"synthetic")
  with self.assertRaises(ValueError):x.redeem(h,"wrong")
if __name__=="__main__":unittest.main()
