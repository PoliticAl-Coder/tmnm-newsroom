import pathlib,secrets,time,tempfile,unittest
from meta_connect import ProtectedTokenStore, read_only_preflight, PAGE_ID
class Gate:
 def __init__(self,ttl=60): self.ttl=ttl;self.tx={};self.h={};self.exchange_calls=0
 def begin(self): t=secrets.token_urlsafe(24);s=secrets.token_urlsafe(32);self.tx[t]=(s,time.time()+self.ttl);return t,s
 def callback(self,t,state,exchange):
  if t not in self.tx: raise ValueError("TX")
  s,e=self.tx.pop(t)
  if time.time()>e: raise ValueError("EXPIRED_TX")
  if not state or not secrets.compare_digest(s,state): raise ValueError("STATE")
  self.exchange_calls+=1
  token=exchange()
  if not isinstance(token,str) or not token: raise ValueError("EXCHANGE")
  hid=secrets.token_urlsafe(32);self.h[hid]=(token,t,time.time()+self.ttl);return "http://localhost:8767/meta/callback?handoff="+hid+"&tx="+t,hid
 def redeem(self,h,t,server_error=False):
  if server_error: raise RuntimeError("SERVER")
  if h not in self.h: raise ValueError("HANDOFF")
  token,b,e=self.h.pop(h)
  if time.time()>e: raise ValueError("EXPIRED_HANDOFF")
  if b!=t: raise ValueError("BINDING")
  return token
class T(unittest.TestCase):
 def good_graph(self,path,fields,token):
  self.assertEqual(path,"/me/accounts");return {"data":[{"id":PAGE_ID,"name":"TMNM","access_token":"synthetic-page","tasks":["CREATE_CONTENT"]}]}
 def test_full_success(self):
  g=Gate();t,s=g.begin();url,h=g.callback(t,s,lambda:"synthetic-user-token");self.assertEqual(g.exchange_calls,1);self.assertNotIn("synthetic-user-token",url)
  tok=g.redeem(h,t);self.assertNotIn(h,g.h)
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/"x.dpapi";ProtectedTokenStore(p).save(tok);self.assertNotIn(tok.encode(),p.read_bytes());loaded=ProtectedTokenStore(p).load()
   r=read_only_preflight(loaded,self.good_graph);self.assertEqual(r["status"],"READY");self.assertEqual(r["facebook_write"],0)
  with self.assertRaises(ValueError):g.redeem(h,t)
 def test_state_failures(self):
  for bad in ("wrong",""):
   g=Gate();t,s=g.begin()
   with self.assertRaises(ValueError):g.callback(t,bad,lambda:"x")
 def test_expired_tx(self):
  g=Gate(-1);t,s=g.begin()
  with self.assertRaises(ValueError):g.callback(t,s,lambda:"x")
 def test_exchange_failures(self):
  for fn in (lambda:(_ for _ in ()).throw(RuntimeError("server")),lambda:""):
   g=Gate();t,s=g.begin()
   with self.assertRaises(Exception):g.callback(t,s,fn)
 def test_handoff_failures(self):
  g=Gate();t,s=g.begin()
  with self.assertRaises(ValueError):g.redeem("guess",t)
  url,h=g.callback(t,s,lambda:"x")
  with self.assertRaises(ValueError):g.redeem(h,"wrong")
  with self.assertRaises(ValueError):g.redeem(h,t)
  g=Gate();t,s=g.begin();url,h=g.callback(t,s,lambda:"x")
  with self.assertRaises(RuntimeError):g.redeem(h,t,True)
 def test_expired_handoff(self):
  g=Gate();t,s=g.begin();url,h=g.callback(t,s,lambda:"x");tok,b,e=g.h[h];g.h[h]=(tok,b,time.time()-1)
  with self.assertRaises(ValueError):g.redeem(h,t)
 def test_wrong_page_and_access(self):
  def wrong(path,fields,token): return {"data":[{"id":"wrong","tasks":["CREATE_CONTENT"]}]}
  def access(path,fields,token): return {"data":[{"id":PAGE_ID,"tasks":[]}]}
  self.assertEqual(read_only_preflight("x",wrong)["status"],"HOLD")
  self.assertEqual(read_only_preflight("x",access)["status"],"HOLD")
 def test_static_scope(self):
  src=(pathlib.Path(__file__).parent/"oauth_exchange_protocol.md").read_text().lower()
  for forbidden in ("/feed","article payload","localworker","8775","scheduler","publishing queue"):
   self.assertNotIn(forbidden,src)
if __name__=="__main__":unittest.main()
