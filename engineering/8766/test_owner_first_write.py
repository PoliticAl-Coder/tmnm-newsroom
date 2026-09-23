import pathlib,tempfile,unittest,sys
sys.path.insert(0,str(pathlib.Path(__file__).parent));sys.path.insert(0,str(pathlib.Path(__file__).parents[1]/"master365"))
import owner_first_write as o
from meta_connect import ProtectedTokenStore
class W:
 def __init__(self,token): self.write_count=0
 def publish(self,**kw): self.write_count+=1; return {"kind":"success","post_id":"1021402681056527_SYNTHETIC"}
class T(unittest.TestCase):
 def test_exact_owner_path(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d); ProtectedTokenStore(p/"meta_token.dpapi").save("SYNTHETIC")
   first,receipt,second,writes,blocked=o.run(p,W)
   self.assertEqual(first.state,"PUBLISHED");self.assertEqual(writes,1);self.assertTrue(blocked);self.assertEqual(second.state,"PUBLISHED");self.assertEqual(receipt["page_id"],o.PAGE_ID)
 def test_bindings(self):
  a=o.article();self.assertEqual(a["article_guid"],o.GUID);self.assertEqual(a["destination_page_id"],o.PAGE_ID);self.assertEqual(a["payload_sha256"].upper(),o.EXPECTED_HASH)
if __name__=="__main__":unittest.main()
