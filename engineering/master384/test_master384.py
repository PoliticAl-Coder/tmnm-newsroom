import ast, importlib.util, json, os, pathlib, tempfile, unittest
HERE=pathlib.Path(__file__).parent
SRC=(HERE/"tmnm_master384_readonly_inspector.py").read_text(encoding="utf-8")
spec=importlib.util.spec_from_file_location("m",HERE/"tmnm_master384_readonly_inspector.py"); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
class FakeExec:
 def __init__(self,v): self.v=v
 def execute(self): return self.v
class Versions:
 def get(self,**kw): return FakeExec({"files":[{"name":"Code","type":"SERVER_JS","source":"x"}]})
class Deployments:
 def get(self,**kw): return FakeExec({"deploymentConfig":{"versionNumber":24},"updateTime":"x"})
class Projects:
 def getContent(self,**kw): return FakeExec({"files":[{"name":"Code","type":"SERVER_JS","source":"x"}]})
 def deployments(self): return Deployments()
 def versions(self): return Versions()
class Service:
 def projects(self): return Projects()
class Tests(unittest.TestCase):
 def test_static_no_scripts_run_or_mutation_api(self):
  tree=ast.parse(SRC)
  attrs={n.attr for n in ast.walk(tree) if isinstance(n,ast.Attribute)}
  self.assertNotIn("run",attrs)
  for x in ("updateContent","create","update","delete"): self.assertNotIn(x,attrs)
  self.assertNotIn("UrlFetchApp",SRC); self.assertNotIn("PropertiesService",SRC)
  self.assertNotIn("facebook.com",SRC.lower()); self.assertNotIn("graph.facebook",SRC.lower())
 def test_only_management_reads(self):
  self.assertIn("getContent",SRC); self.assertIn("deployments().get",SRC); self.assertIn("versions().get",SRC)
 def test_deterministic_hash(self):
  a={"files":[{"name":"b","type":"SERVER_JS","source":"2"},{"name":"a","type":"SERVER_JS","source":"1"}]}
  b={"files":list(reversed(a["files"]))}; self.assertEqual(m.content_hash(a),m.content_hash(b))
 def test_fail_closed_missing_credential(self):
  r,s=m.inspect(pathlib.Path("does-not-exist")); self.assertEqual(r["GOOGLE_AUTH"],"FAIL"); self.assertIsNone(s)
 def test_synthetic_service_no_network(self):
  # Bypass DPAPI only in isolated test by patching loaders.
  with tempfile.TemporaryDirectory() as td:
   p=pathlib.Path(td)/"c"; p.write_bytes(b"x")
   old1,old2=m.dpapi_unprotect,m.decode_credential
   try:
    m.dpapi_unprotect=lambda b:b
    m.decode_credential=lambda b:{"refresh_token":"synthetic","scopes":["https://www.googleapis.com/auth/script.projects"]}
    r,s=m.inspect(p,service_factory=lambda info:Service())
    self.assertEqual(r["GOOGLE_AUTH"],"PASS"); self.assertEqual(r["CURRENT_DEPLOYED_VERSION"],24)
    self.assertEqual(r["MUTATIONS"],0); self.assertEqual(r["SCRIPTS_RUN"],0); self.assertEqual(r["META_CALLS"],0)
    self.assertIsNotNone(s)
   finally: m.dpapi_unprotect,m.decode_credential=old1,old2
if __name__=="__main__": unittest.main(verbosity=2)
