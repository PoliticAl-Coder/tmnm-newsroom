import importlib.util,json,sqlite3,tempfile,threading,unittest,sys
from pathlib import Path
from tmnm_fb_publisher.core import Publisher
_here=Path(__file__).with_name("article_pool_publish.py")
_spec=importlib.util.spec_from_file_location("article_pool_publish",_here); ap=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=ap;_spec.loader.exec_module(ap)
ArticlePoolPublishAction=ap.ArticlePoolPublishAction; TMNM_PAGE_ID=ap.TMNM_PAGE_ID; payload_sha256=ap.payload_sha256
class MockMeta:
 def __init__(self,mode="ok"): self.calls=0; self.mode=mode; self.lock=threading.Lock()
 def publish(self,**kw):
  with self.lock:self.calls+=1
  if self.mode=="ok":return {"kind":"success","post_id":"POST1"}
  if self.mode=="definite":return {"kind":"definite_failure","error":"rejected"}
  raise TimeoutError("timeout")
class NullAudit:
 def write(self,*a,**k):return None
def article(**kw):
 a={"article_guid":"TMNM-8766-TEST-0001","approved":True,"destination_page_id":TMNM_PAGE_ID,"message":"Phase 1 mock article"};a.update(kw);a["payload_sha256"]=payload_sha256(a);return a
from tmnm_fb_publisher.core import Store
def pub(db,meta):return Publisher(Store(db),meta)
class T(unittest.TestCase):
 def test_approved(self):
  with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
   m=MockMeta();x=ArticlePoolPublishAction(pub(Path(d)/"x.db",m));a=article(approved=False);a["payload_sha256"]=payload_sha256(a);self.assertFalse(x.publish(a).ok);self.assertEqual(m.calls,0)
 def test_guid_destination_hash(self):
  with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
   cases=[article(article_guid="bad"),article(destination_page_id="WRONG"),article()];cases[2]["payload_sha256"]="bad"
   for i,a in enumerate(cases):
    m=MockMeta();x=ArticlePoolPublishAction(pub(Path(d)/(str(i)+".db"),m));self.assertFalse(x.publish(a).ok);self.assertEqual(m.calls,0)
 def test_one_write_duplicate_restart_receipt(self):
  with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
   db=Path(d)/"x.db";m=MockMeta();a=article();r=ArticlePoolPublishAction(pub(db,m)).publish(a);self.assertTrue(r.ok);self.assertEqual(r.state,"PUBLISHED");self.assertEqual(m.calls,1);self.assertNotIn("token",json.dumps(r.receipt).lower());ArticlePoolPublishAction(pub(db,m)).publish(a);self.assertEqual(m.calls,1)
 def test_concurrent_one_write(self):
  with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
   db=Path(d)/"x.db";m=MockMeta();a=article();barrier=threading.Barrier(2)
   def f():barrier.wait();ArticlePoolPublishAction(pub(db,m)).publish(a)
   ts=[threading.Thread(target=f) for _ in range(2)];[t.start() for t in ts];[t.join() for t in ts];self.assertEqual(m.calls,1)
 def test_pending_is_durable_before_transport(self):
  with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
   db=Path(d)/"x.db"; outer=self
   class Inspect(MockMeta):
    def publish(s,**kw):
     con=sqlite3.connect(db);states=[r[0] for r in con.execute("select state from publication")];con.close();outer.assertIn("PENDING",states);return super().publish(**kw)
   self.assertTrue(ArticlePoolPublishAction(pub(db,Inspect())).publish(article()).ok)
 def test_definite_ambiguous_no_blind_retry(self):
  for mode in ("definite","ambiguous"):
   with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
    db=Path(d)/"x.db";m=MockMeta(mode);x=ArticlePoolPublishAction(pub(db,m));x.publish(article());x.publish(article());self.assertEqual(m.calls,1)
if __name__=="__main__":unittest.main()
