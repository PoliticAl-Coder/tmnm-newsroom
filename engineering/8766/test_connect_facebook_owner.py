import importlib.util,pathlib,sys,unittest
d=pathlib.Path(__file__).parent
sys.path.insert(0,str(d))
p=d/"connect_facebook_owner.py";s=importlib.util.spec_from_file_location("owner",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class T(unittest.TestCase):
 def test_reaches_browser_boundary_without_opening_browser(self):
  calls=[];a=m.ConnectFacebookOwnerAction(lambda u:calls.append(u));r=a.start(open_browser=False)
  self.assertEqual(calls,[]);self.assertEqual(r,{"status":"BROWSER_BOUNDARY_READY","facebook_write":0});self.assertIsNotNone(a.guard._state)
if __name__=="__main__":unittest.main()
