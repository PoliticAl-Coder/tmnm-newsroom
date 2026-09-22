import importlib.util,pathlib,sys,tempfile,unittest,urllib.parse
p=pathlib.Path(__file__).with_name("meta_connect.py");s=importlib.util.spec_from_file_location("meta_connect",p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
class T(unittest.TestCase):
 def test_exact_config_and_no_write(self):
  self.assertEqual(m.APP_ID,"1754274758914441");self.assertEqual(m.PAGE_ID,"1021402681056527")
  self.assertEqual(m.REDIRECT_URI,"http://localhost:8767/meta/callback")
  self.assertEqual(m.AUTH_ENDPOINT,"https://www.facebook.com/v26.0/dialog/oauth")
  self.assertEqual(m.SCOPES,("pages_show_list","pages_read_engagement","pages_manage_posts"))
  src=p.read_text();self.assertNotIn("requests.post",src);self.assertNotIn("/feed",src);self.assertNotIn("urlopen",src)
 def test_url_and_state(self):
  g=m.OAuthGuard();u=g.begin();q=urllib.parse.parse_qs(urllib.parse.urlsplit(u).query)
  self.assertEqual(q["client_id"],[m.APP_ID]);self.assertEqual(q["redirect_uri"],[m.REDIRECT_URI]);self.assertEqual(q["scope"],[",".join(m.SCOPES)])
  self.assertEqual(g.accept_callback("/meta/callback?state="+q["state"][0]+"&code=SYNTHETIC_CODE"),"SYNTHETIC_CODE")
 def test_callback_rejections(self):
  cases=[("/wrong?state={s}&code=x","UNEXPECTED_CALLBACK_PATH"),("/meta/callback?code=x","MISSING_STATE"),("/meta/callback?state=WRONG&code=x","STATE_MISMATCH"),("/meta/callback?state={s}","MISSING_AUTHORIZATION_RESULT"),("/meta/callback?state={s}&code=x&junk=y","MALFORMED_CALLBACK")]
  for target,msg in cases:
   g=m.OAuthGuard();u=g.begin();st=urllib.parse.parse_qs(urllib.parse.urlsplit(u).query)["state"][0]
   with self.assertRaisesRegex(ValueError,msg):g.accept_callback(target.format(s=st))
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
