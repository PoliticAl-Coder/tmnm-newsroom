import hashlib,json,sqlite3,tempfile,threading,unittest
from pathlib import Path
from tmnm_fb_publisher.adapter import ArticlePoolPublishAction,TMNM_PAGE_ID,payload_sha256
from tmnm_fb_publisher.core import Publisher

class MockMeta:
 def __init__(self,mode="ok"): self.calls=0; self.mode=mode; self.lock=threading.Lock()
 def publish(self,**kw):
  with self.lock:self.calls+=1
  if self.mode=="ok":return {"id":"POST1","permalink_url":"https://example.invalid/post"}
  if self.mode=="definite":raise Exception("META_DEFINITE: rejected")
  raise TimeoutError("timeout")
class NullAudit:
 def write(self,*a,**k):return None
def article(**kw):
 a={"article_guid":"TMNM-8766-TEST-0001","approved":True,"destination_page_id":TMNM_PAGE_ID,"message":"Phase 1 mock article"}
 a.update(kw); a["payload_sha256"]=payload_sha256(a); return a
def pub(db,meta): return Publisher(str(db),meta,NullAudit(),TMNM_PAGE_ID)
class T(unittest.TestCase):
 def test_approved(self):
  with tempfile.TemporaryDirectory() as d:
   m=MockMeta(); x=ArticlePoolPublishAction(pub(Path(d)/"x.db",m)); a=article(approved=False); a["payload_sha256"]=payload_sha256(a); r=x.publish(a); self.assertFalse(r.ok); self.assertEqual(m.calls,0)
 def test_guid_destination_hash(self):
  with tempfile.TemporaryDirectory() as d:
   for a in [article(article_guid="bad"),article(destination_page_id="WRONG"),article()]:
    m=MockMeta(); x=ArticlePoolPublishAction(pub(Path(d)/(str(id(a))+".db"),m))
    if a["article_guid"]!="bad" and a["destination_page_id"]==TMNM_PAGE_ID:a["payload_sha256"]="bad"
    self.assertFalse(x.publish(a).ok); self.assertEqual(m.calls,0)
 def test_one_write_duplicate_restart_receipt(self):
  with tempfile.TemporaryDirectory() as d:
   db=Path(d)/"x.db"; m=MockMeta(); a=article(); r=ArticlePoolPublishAction(pub(db,m)).publish(a); self.assertTrue(r.ok); self.assertEqual(r.state,"PUBLISHED"); self.assertEqual(m.calls,1); self.assertNotIn("token",json.dumps(r.receipt).lower())
   r2=ArticlePoolPublishAction(pub(db,m)).publish(a); self.assertEqual(m.calls,1); self.assertIn(r2.state,("PUBLISHED","HOLD"))
 def test_concurrent_one_write(self):
  with tempfile.TemporaryDirectory() as d:
   db=Path(d)/"x.db"; m=MockMeta(); a=article(); rs=[]; barrier=threading.Barrier(2)
   def f(): barrier.wait(); rs.append(ArticlePoolPublishAction(pub(db,m)).publish(a))
   ts=[threading.Thread(target=f) for _ in range(2)];[t.start() for t in ts];[t.join() for t in ts];self.assertEqual(m.calls,1)
 def test_pending_is_durable_before_transport(self):
  with tempfile.TemporaryDirectory() as d:
   db=Path(d)/"x.db"
   class Inspect(MockMeta):
    def publish(s,**kw):
     con=sqlite3.connect(db); states=[r[0] for r in con.execute("select state from publish_records")];con.close();self.assertIn("PENDING",states);return super().publish(**kw)
   self.assertTrue(ArticlePoolPublishAction(pub(db,Inspect())).publish(article()).ok)
 def test_definite_ambiguous_no_blind_retry(self):
  for mode,state in [("definite","FAILED_DEFINITE"),("ambiguous","AMBIGUOUS")]:
   with tempfile.TemporaryDirectory() as d:
    db=Path(d)/"x.db";m=MockMeta(mode);x=ArticlePoolPublishAction(pub(db,m));r=x.publish(article());self.assertIn(r.state,(state,"HOLD"));x.publish(article());self.assertEqual(m.calls,1)
if __name__=="__main__":unittest.main()
