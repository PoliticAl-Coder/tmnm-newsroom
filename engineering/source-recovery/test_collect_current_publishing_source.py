import importlib.util, os, pathlib, tempfile, unittest
from unittest.mock import patch

P=pathlib.Path(__file__).with_name("collect_current_publishing_source.py")
spec=importlib.util.spec_from_file_location("collector",P)
c=importlib.util.module_from_spec(spec); spec.loader.exec_module(c)

class CollectorTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(); self.root=pathlib.Path(self.t.name)/"TMNM"; self.root.mkdir()
  self.oldroot=c.ROOT; c.ROOT=self.root
 def tearDown(self): c.ROOT=self.oldroot; self.t.cleanup()
 def f(self,rel,text="print('ok')"):
  p=self.root/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding="utf-8"); return p
 def test_excludes_credentials_config_db_runtime_and_cache(self):
  for rel in ["ControlRoom/token.json","ControlRoom/config.json","ControlRoom/state/x.py","LocalWorker/logs/x.py","ControlRoom/cache/x.py","ControlRoom/db.sqlite"]:
   p=self.f(rel); self.assertTrue(c.excluded(p) or p.suffix.lower() not in c.ALLOWED)
 def test_allows_source_in_controlroom_and_localworker(self):
  self.assertFalse(c.excluded(self.f("ControlRoom/app.py")))
  self.assertFalse(c.excluded(self.f("LocalWorker/worker.py")))
 def test_sensitive_literal_patterns_block(self):
  samples=["refresh_token = 'abcdefghijklmnop'","Bearer "+"A"*30,"-----BEGIN PRIVATE KEY-----"]
  for s in samples: self.assertIsNotNone(c.SENSITIVE_LITERAL_RE.search(s),s)
 def test_relevance_patterns_cover_boundaries(self):
  for s in ["8766 owner console","facebook publisher","WorkflowStore payload_for","canonical_snapshot validate_actionable"]:
   self.assertIsNotNone(c.RELEVANT_RE.search(s),s)
 def test_non_windows_fails_closed_without_output(self):
  out=pathlib.Path.cwd()/"TMNM_CURRENT_PUBLISHING_SOURCE_ONLY.zip"
  if out.exists(): out.unlink()
  with patch.object(c.os,"name","posix"):
   self.assertEqual(c.main(),2)
  self.assertFalse(out.exists())

if __name__=="__main__": unittest.main(verbosity=2)
