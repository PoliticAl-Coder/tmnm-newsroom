import secrets,time,unittest
class ExecExchange:
 def __init__(self,ttl=600): self.tx={};self.h={};self.ttl=ttl;self.stages=[]
 def mark(self,n):self.stages.append(n)
 def register(self,t,s):
  if not t or not s:raise ValueError("REGISTER")
  self.tx[t]={"state":s,"expires":time.time()+self.ttl,"status":"WAIT"}
 def callback(self,state,code,adapter,redirect_uri):
  self.mark("EXEC_CALLBACK_ENTERED")
  matches=[(t,r) for t,r in self.tx.items() if r["status"]=="WAIT" and secrets.compare_digest(r["state"],state or "")]
  if len(matches)!=1:raise ValueError("STATE")
  t,r=matches[0]
  if time.time()>r["expires"]:raise ValueError("EXPIRED_TX")
  if not code:raise ValueError("CODE")
  r["status"]="EXCHANGING";self.mark("CODE_EXCHANGE_STARTED")
  token=adapter(code,redirect_uri);self.mark("CODE_EXCHANGE_PASS")
  if not token:raise ValueError("EXCHANGE")
  hid=secrets.token_urlsafe(32);self.h[hid]=(token,t,time.time()+self.ttl);r["status"]="READY";r["handoff"]=hid;self.mark("HANDOFF_READY");return hid
 def redeem(self,h,t):
  if h not in self.h:raise ValueError("HANDOFF")
  token,b,e=self.h.pop(h)
  if time.time()>e or b!=t:raise ValueError("BINDING")
  self.mark("REDEEM_PASS");return token
class T(unittest.TestCase):
 def setUp(self):self.x=ExecExchange();self.t=secrets.token_urlsafe(24);self.s=secrets.token_urlsafe(32);self.x.register(self.t,self.s)
 def test_success_single_redeem_redirect(self):
  seen=[]
  h=self.x.callback(self.s,"code",lambda c,r:seen.append((c,r)) or "token","https://x/exec")
  self.assertEqual(seen,[("code","https://x/exec")]);self.assertEqual(self.x.redeem(h,self.t),"token")
  with self.assertRaises(ValueError):self.x.redeem(h,self.t)
  self.assertEqual(self.x.stages,["EXEC_CALLBACK_ENTERED","CODE_EXCHANGE_STARTED","CODE_EXCHANGE_PASS","HANDOFF_READY","REDEEM_PASS"])
 def test_state_mismatch_missing(self):
  for s in ("wrong",""):
   y=ExecExchange();t=secrets.token_urlsafe(24);good=secrets.token_urlsafe(32);y.register(t,good)
   with self.assertRaises(ValueError):y.callback(s,"code",lambda c,r:"token","https://x/exec")
 def test_replay_fails_closed(self):
  self.x.callback(self.s,"code",lambda c,r:"token","https://x/exec")
  with self.assertRaises(ValueError):self.x.callback(self.s,"code2",lambda c,r:"token2","https://x/exec")
 def test_expiry(self):
  y=ExecExchange(-1);t="t";s="s";y.register(t,s)
  with self.assertRaises(ValueError):y.callback(s,"code",lambda c,r:"token","https://x/exec")
 def test_exchange_failure(self):
  with self.assertRaises(Exception):self.x.callback(self.s,"code",lambda c,r:(_ for _ in ()).throw(RuntimeError()),"https://x/exec")
if __name__=="__main__":unittest.main()
