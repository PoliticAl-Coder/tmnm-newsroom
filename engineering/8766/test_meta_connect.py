import importlib.util, pathlib, sys, unittest
p=pathlib.Path(__file__).with_name("meta_connect.py");s=importlib.util.spec_from_file_location("meta_connect",p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
class T(unittest.TestCase):
 def test_current_app_and_no_write(self):
  self.assertEqual(m.APP_ID,"1754274758914441");self.assertEqual(m.PAGE_ID,"1021402681056527")
  src=p.read_text();self.assertNotIn("requests.post",src);self.assertNotIn("/feed",src)
 def test_url(self):
  u=m.make_authorize_url("http://localhost:8767/meta/callback","STATE");self.assertIn("1754274758914441",u);self.assertIn("pages_manage_posts",u);self.assertIn("STATE",u)
 def test_preflight_pass(self):
  def g(path,params,t):return {"data":[{"id":m.PAGE_ID,"access_token":"SECRET","tasks":["CREATE_CONTENT","MANAGE"]}]}
  r=m.read_only_preflight("SECRET",g);self.assertEqual(r.as_dict(),{"META_AUTH":"PASS","TMNM_PAGE_ID_MATCH":"PASS","REQUIRED_ACCESS":"PASS","FACEBOOK_WRITE":0})
 def test_wrong_page(self):
  r=m.read_only_preflight("SECRET",lambda *x:{"data":[]});self.assertEqual(r.TMNM_PAGE_ID_MATCH,"HOLD")
if __name__=="__main__":unittest.main()
