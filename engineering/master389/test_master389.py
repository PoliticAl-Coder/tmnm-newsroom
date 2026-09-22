import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import tmnm_master389_exact_file_recovery as m
class T(unittest.TestCase):
 def fixture(self,p):
  p.write_text(json.dumps({"result":{"GOOGLE_AUTH":"FAIL","SCRIPTS_RUN":0,"META_CALLS":0,"error":"Bearer SECRET"},"snapshot":None,"drive_persistence":{"status":"HOLD","drive_file_id":None}}))
 def test_alt(self):
  self.assertEqual(m.run(["--input","C:\\wrong.json"],persist_fn=lambda*a:None),2)
 def test_exact_unchanged_one_persist(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"r.json"; self.fixture(p); b=p.read_bytes(); calls=[]
   with patch.object(m,"EXACT_INPUT",p):
    rc=m.run(["--input",str(p)],persist_fn=lambda payload,info:(calls.append(payload) or {"id":"X"}),credential_loader=lambda p:{"scopes":["https://www.googleapis.com/auth/drive"]})
   self.assertEqual(rc,0); self.assertEqual(p.read_bytes(),b); self.assertEqual(len(calls),1); self.assertNotIn("SECRET",json.dumps(calls))
 def test_bad_json(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"r.json"; p.write_text("{")
   with patch.object(m,"EXACT_INPUT",p): self.assertEqual(m.run(["--input",str(p)],persist_fn=lambda*a:None,credential_loader=lambda p:{}),2)
 def test_bad_schema(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"r.json"; p.write_text('{"evil":1}')
   with patch.object(m,"EXACT_INPUT",p): self.assertEqual(m.run(["--input",str(p)],persist_fn=lambda*a:None,credential_loader=lambda p:{}),2)
 def test_persist_fail_no_retry(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"r.json"; self.fixture(p); n=[]
   def fail(*a): n.append(1); raise RuntimeError("drive")
   with patch.object(m,"EXACT_INPUT",p): self.assertEqual(m.run(["--input",str(p)],persist_fn=fail,credential_loader=lambda p:{}),2)
   self.assertEqual(len(n),1)
 def test_static_forbidden(self):
  s=Path(m.__file__).read_text().lower()
  for x in ["scripts().run","scripts.run","projects().getcontent","deployments().get","versions().get","start-scheduledtask","facebook","graph.facebook","publish-now","preflight"]: self.assertNotIn(x,s)
if __name__=="__main__":unittest.main()
