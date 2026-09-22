import importlib.util,pathlib,sys,tempfile,unittest,urllib.parse
p=pathlib.Path(__file__).with_name("meta_connect.py");s=importlib.util.spec_from_file_location("meta_connect",p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
class T(unittest.TestCase):
 def test_exact_config_and_no_write(self):
  self.assertEqual(m.APP_ID,"1754274758914441");self.assertEqual(m.PAGE_ID,"1021402681056527")
  self.assertEqual(m.META_REDIRECT_URI,m.EXCHANGE_BASE)
  self.assertEqual(m.AUTH_ENDPOINT,"https://www.facebook.com/v26.0/dialog/oauth")
  self.assertEqual(m.SCOPES,("pages_show_list","pages_read_engagement","pages_manage_posts"))
  src=p.read_text();self.assertNotIn("requests.post",src);self.assertNotIn("/feed",src);self.assertNotIn("method=\"POST\"",src.split("def _graph_get",1)[1])
 def test_url_and_state(self):
  state="SYNTHETIC_STATE";u=m.build_authorization_url(state);parts=urllib.parse.urlsplit(u);self.assertEqual(parts.scheme,"https");self.assertEqual(parts.netloc,"www.facebook.com");self.assertEqual(parts.path,"/v26.0/dialog/oauth");q=urllib.parse.parse_qs(parts.query)
  self.assertEqual(q["client_id"],[m.APP_ID]);self.assertEqual(q["redirect_uri"],[m.META_REDIRECT_URI]);self.assertEqual(q["scope"],[",".join(m.SCOPES)]);self.assertEqual(q["state"],[state]);self.assertEqual(q["response_type"],["code"])
 def test_default_poll_ttl(self):
  import inspect
  self.assertEqual(inspect.signature(m.poll_handoff).parameters["timeout"].default,300)
 def test_exchange_contract(self):
  calls=[]
  def post(url,fields):
   calls.append(fields.copy())
   if fields["action"]=="register":return {"status":"PASS"}
   if fields["action"]=="poll":return {"status":"PASS","handoff":"OPAQUE_HANDOFF_123456"}
   if fields["action"]=="redeem":return {"status":"PASS","credential":"SYNTHETIC"}
  m.register_transaction("TX_1234567890123456","STATE_1234567890123456",post)
  self.assertEqual(m.poll_handoff("TX_1234567890123456",post,timeout=1,interval=0),"OPAQUE_HANDOFF_123456")
  self.assertEqual(m.redeem_handoff("OPAQUE_HANDOFF_123456","TX_1234567890123456",post),"SYNTHETIC")
  self.assertEqual([x["action"] for x in calls],["register","poll","redeem"])
 def test_complete_simulated_chain(self):
  events=[]
  def post(url,fields):
   a=fields["action"];events.append(a)
   if a=="register":return {"status":"PASS"}
   if a=="redeem":return {"status":"PASS","credential":"SYNTHETIC_SECRET"}
  def poll(tx,postfn):events.extend(["GOOGLE_CALLBACK_ENTERED","CODE_EXCHANGE_STARTED","CODE_EXCHANGE_PASS","HANDOFF_READY"]);return "OPAQUE_HANDOFF_123456"
  class Store:
   def __init__(self,path):pass
   def save(self,t):events.append("DPAPI_PASS");self.t=t
   def load(self):return "SYNTHETIC_SECRET"
  def get(path,params,t):events.append("ME_ACCOUNTS_PASS");self.assertEqual(path,"/me/accounts");return {"data":[{"id":m.PAGE_ID,"tasks":["CREATE_CONTENT"]}]}
  old=m.ProtectedTokenStore;m.ProtectedTokenStore=Store
  try:
   r=m.connect_facebook("x",open_browser=lambda u: events.append("BROWSER_OPEN_REQUESTED") or True,post=post,graph_get=get,poll=poll)
   self.assertEqual(r.TMNM_PAGE_ID_MATCH,"PASS");events.append("PAGE_MATCH_PASS")
   for x in ("BROWSER_OPEN_REQUESTED","GOOGLE_CALLBACK_ENTERED","CODE_EXCHANGE_STARTED","CODE_EXCHANGE_PASS","HANDOFF_READY","redeem","DPAPI_PASS","ME_ACCOUNTS_PASS","PAGE_MATCH_PASS"):self.assertIn(x,events)
  finally:m.ProtectedTokenStore=old
 def test_real_connect_register_signature_regression(self):
  calls=[]
  def post(url,fields):
   calls.append(fields.copy())
   if fields["action"]=="register":return {"status":"PASS","state":"GOOGLE_STATE_TOKEN"}
   if fields["action"]=="redeem":return {"status":"PASS","credential":"SYNTHETIC_SECRET"}
  def poll(tx,postfn):return "OPAQUE_HANDOFF_123456"
  class Store:
   def __init__(self,path):pass
   def save(self,t):self.t=t
   def load(self):return "SYNTHETIC_SECRET"
  old=m.ProtectedTokenStore;m.ProtectedTokenStore=Store
  try:
   r=m.connect_facebook("x",open_browser=lambda u:True,post=post,graph_get=lambda *x:{"data":[{"id":m.PAGE_ID,"tasks":["CREATE_CONTENT"]}]},poll=poll)
   self.assertEqual(r.META_AUTH,"PASS")
   self.assertEqual(calls[0]["action"],"register")
   self.assertEqual(set(calls[0]),{"action","tx","state"})
  finally:m.ProtectedTokenStore=old
 def test_preflight_binding(self):
  calls=[]
  def get(path,params,t):calls.append((path,params));return {"data":[{"id":m.PAGE_ID,"access_token":"SYNTHETIC_PAGE_SECRET","tasks":["CREATE_CONTENT"]}]}
  r=m.read_only_preflight("SYNTHETIC_USER_SECRET",get);self.assertEqual(r.as_dict(),{"META_AUTH":"PASS","TMNM_PAGE_ID_MATCH":"PASS","REQUIRED_ACCESS":"PASS","FACEBOOK_WRITE":0})
  self.assertEqual(calls,[("/me/accounts",{"fields":"name,access_token,tasks"})])
 def test_wrong_page(self):
  r=m.read_only_preflight("SYNTHETIC",lambda *x:{"data":[]});self.assertEqual(r.TMNM_PAGE_ID_MATCH,"HOLD")
 def test_dpapi_synthetic(self):
  if sys.platform!="win32":self.skipTest("native Windows gate")
  with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
   q=pathlib.Path(d)/"meta_token.dpapi";st=m.ProtectedTokenStore(str(q));secret="SYNTHETIC_SECRET_ONLY_8766"
   st.save(secret);self.assertEqual(st.load(),secret);self.assertNotIn(secret,q.read_bytes().decode("latin1"))
if __name__=="__main__":unittest.main()

