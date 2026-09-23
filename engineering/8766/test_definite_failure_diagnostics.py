import io,json,pathlib,sys,tempfile,unittest,urllib.error
sys.path.insert(0,str(pathlib.Path(__file__).parent));sys.path.insert(0,str(pathlib.Path(__file__).parents[1]/"master365"))
import owner_first_write as o
class Opener:
 def __call__(self,req,timeout=30):
  body=json.dumps({"error":{"message":"(#200) Requires pages_manage_posts permission","type":"OAuthException","code":200,"error_subcode":2018028}}).encode()
  raise urllib.error.HTTPError(req.full_url,403,"Forbidden",{},io.BytesIO(body))
class T(unittest.TestCase):
 def test_safe_meta_error_capture_no_live_write(self):
  w=o.OneWriteMetaTransport("SYNTHETIC_TOKEN",Opener())
  r=w.publish(page_id=o.PAGE_ID,message=o.MESSAGE,attempt_id="x")
  self.assertEqual(w.write_count,1);self.assertEqual(r["kind"],"definite_failure")
  self.assertIn("META_HTTP_STATUS=403",r["error"]);self.assertIn("META_ERROR_CODE=200",r["error"]);self.assertIn("META_ERROR_SUBCODE=2018028",r["error"])
  self.assertNotIn("SYNTHETIC_TOKEN",r["error"])
 def test_result_surfaces_receipt_error(self):
  class X: state="FAILED_DEFINITE";post_id=None;error="META_HTTP_STATUS=403"
  txt=o.safe_result(X(),{"state":"FAILED_DEFINITE","error":"META_HTTP_STATUS=403"},1,True)
  self.assertIn("ERROR=META_HTTP_STATUS=403",txt)
if __name__=="__main__":unittest.main()
