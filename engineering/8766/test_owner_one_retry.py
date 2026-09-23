import io,json,pathlib,tempfile,unittest,urllib.error,sys
sys.path.insert(0,str(pathlib.Path(__file__).parent));sys.path.insert(0,str(pathlib.Path(__file__).parents[1]/"master365"))
import owner_one_retry as o
from meta_connect import ProtectedTokenStore
from tmnm_fb_publisher.core import Store,payload_hash
class Resp:
 def __init__(self,obj):self.b=json.dumps(obj).encode()
 def __enter__(self):return self
 def __exit__(self,*a):pass
 def read(self):return self.b
class T(unittest.TestCase):
 def image(self):return pathlib.Path(__file__).parent/o.IMAGE_FILENAME
 def seed(self,p):
  s=Store(p/"publisher.sqlite3");aid,_=s.acquire(o.GUID,payload_hash(o.MESSAGE),o.PAGE_ID);s.set(o.GUID,"FAILED_DEFINITE",error="PRESERVED_FIRST_FAILURE");return s
 def test_bindings_and_photo_route(self):
  self.assertEqual(o.CANONICAL_PAYLOAD_SHA256,"F0B5CACFC131908D377D19BD358BDB250C25DBA35DA322F0498A66635DCEA959");self.assertEqual(o.sha256_file(self.image()),o.IMAGE_SHA256)
  seen={}
  def opener(req,timeout=0):
   seen["url"]=req.full_url;seen["ctype"]=req.headers.get("Content-type");seen["data"]=req.data
   return Resp({"id":"PHOTO_SYNTHETIC"})
  w=o.OneRetryPhotoTransport("SYNTHETIC_TOKEN",self.image(),opener);r=w.publish(page_id=o.PAGE_ID,message=o.MESSAGE,attempt_id="x")
  self.assertEqual(r["kind"],"success");self.assertEqual(w.write_count,1);self.assertTrue(seen["url"].endswith("/"+o.PAGE_ID+"/photos"));self.assertIn("multipart/form-data",seen["ctype"]);self.assertIn(b'name="source"',seen["data"]);self.assertIn(b'name="message"',seen["data"])
 def test_provider_error_capture(self):
  body=json.dumps({"error":{"message":"safe rejection","type":"OAuthException","code":190,"error_subcode":463,"fbtrace_id":"TRACE"}}).encode()
  e=urllib.error.HTTPError("x",400,"bad",{},io.BytesIO(body));x=o.safe_meta_error(e)
  for v in ("META_HTTP_STATUS=400","META_ERROR_TYPE=OAuthException","META_ERROR_CODE=190","META_ERROR_SUBCODE=463","SAFE_META_MESSAGE=safe rejection","FBTRACE_ID=TRACE"):self.assertIn(v,x)
 def test_explicit_retry_and_second_guard(self):
  p=pathlib.Path(tempfile.mkdtemp());ProtectedTokenStore(p/"meta_token.dpapi").save("SYNTHETIC");self.seed(p)
  class W:
   def __init__(self,tok,img):self.write_count=0
   def publish(self,**kw):self.write_count+=1;return {"kind":"success","post_id":"PHOTO_SYNTHETIC"}
  first,receipt,second,writes,blocked=o.run(p,pathlib.Path(__file__).parent,W)
  self.assertEqual(first.state,"PUBLISHED");self.assertEqual(writes,1);self.assertTrue(blocked);self.assertEqual(second.state,"PUBLISHED");self.assertEqual(receipt["state"],"PUBLISHED")
  a=Store(p/"publisher.sqlite3").retry_authorization(o.GUID);self.assertIsNotNone(a["consumed_at"])
if __name__=="__main__":unittest.main()
