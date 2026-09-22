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
  for x in ("updateContent","updateDeployment","createVersion","deleteDeployment"): self.assertNotIn(x,attrs)
  self.assertNotIn("scripts().run",SRC)
  self.assertNotIn("UrlFetchApp",SRC); self.assertNotIn("PropertiesService",SRC)
  self.assertNotIn("facebook.com",SRC.lower()); self.assertNotIn("graph.facebook",SRC.lower())
 def test_only_management_reads(self):
  self.assertIn("getContent",SRC); self.assertIn("deployments().get",SRC); self.assertIn("versions().get",SRC)
 def test_deterministic_hash(self):
  a={"files":[{"name":"b","type":"SERVER_JS","source":"2"},{"name":"a","type":"SERVER_JS","source":"1"}]}
  b={"files":list(reversed(a["files"]))}; self.assertEqual(m.content_hash(a),m.content_hash(b))
 def test_fail_closed_missing_credential(self):
  r,s,info=m.inspect(pathlib.Path("does-not-exist")); self.assertEqual(r["GOOGLE_AUTH"],"FAIL"); self.assertIsNone(s); self.assertIsNone(info)
 def test_synthetic_service_no_network(self):
  # Bypass DPAPI only in isolated test by patching loaders.
  with tempfile.TemporaryDirectory() as td:
   p=pathlib.Path(td)/"c"; p.write_bytes(b"x")
   old1,old2=m.dpapi_unprotect,m.decode_credential
   try:
    m.dpapi_unprotect=lambda b:b
    m.decode_credential=lambda b:{"refresh_token":"synthetic","scopes":["https://www.googleapis.com/auth/script.projects"]}
    r,s,info=m.inspect(p,service_factory=lambda info:Service())
    self.assertEqual(r["GOOGLE_AUTH"],"PASS"); self.assertEqual(r["CURRENT_DEPLOYED_VERSION"],24)
    self.assertEqual(r["MUTATIONS"],0); self.assertEqual(r["SCRIPTS_RUN"],0); self.assertEqual(r["META_CALLS"],0)
    self.assertIsNotNone(s)
   finally: m.dpapi_unprotect,m.decode_credential=old1,old2

 def test_persist_flag_exactly_one_write_path(self):
  with tempfile.TemporaryDirectory() as td:
   out=pathlib.Path(td)/"r.json"; cred=pathlib.Path(td)/"c"; cred.write_bytes(b"x"); calls=[]
   def ins(p):
    return {"GOOGLE_AUTH":"PASS","MUTATIONS":0,"SCRIPTS_RUN":0,"META_CALLS":0},{"head":{"hash":"h"}},{"scopes":["https://www.googleapis.com/auth/drive"]}
   def per(payload,info,title):
    calls.append((payload,info,title)); return {"drive_file_id":"FILE123","verified":True}
   rc=m.run(["--credential",str(cred),"--out",str(out),"--persist-drive"],inspect_fn=ins,persist_fn=per)
   data=json.loads(out.read_text())
   self.assertEqual(rc,0); self.assertEqual(len(calls),1)
   self.assertEqual(data["drive_persistence"]["status"],"PASS"); self.assertEqual(data["drive_persistence"]["drive_file_id"],"FILE123")
   self.assertNotIn("scopes",json.dumps(calls[0][0]))
 def test_without_persist_flag_zero_drive_writes(self):
  with tempfile.TemporaryDirectory() as td:
   out=pathlib.Path(td)/"r.json"; cred=pathlib.Path(td)/"c"; cred.write_bytes(b"x"); calls=[]
   def ins(p):
    return {"GOOGLE_AUTH":"PASS","MUTATIONS":0,"SCRIPTS_RUN":0,"META_CALLS":0},{"head":{"hash":"h"}},{"secret":"never-persist"}
   def per(*args): calls.append(args); raise AssertionError("must not write")
   rc=m.run(["--credential",str(cred),"--out",str(out)],inspect_fn=ins,persist_fn=per)
   data=json.loads(out.read_text())
   self.assertEqual(rc,0); self.assertEqual(calls,[]); self.assertEqual(data["drive_persistence"]["status"],"NOT_REQUESTED")
 def test_persistence_failure_holds_without_reinspection(self):
  with tempfile.TemporaryDirectory() as td:
   out=pathlib.Path(td)/"r.json"; cred=pathlib.Path(td)/"c"; cred.write_bytes(b"x"); n={"inspect":0,"persist":0}
   def ins(p):
    n["inspect"]+=1; return {"GOOGLE_AUTH":"PASS","MUTATIONS":0,"SCRIPTS_RUN":0,"META_CALLS":0},{"head":{"hash":"h"}},{"scopes":["https://www.googleapis.com/auth/drive"]}
   def per(*args): n["persist"]+=1; raise RuntimeError("drive fail")
   rc=m.run(["--credential",str(cred),"--out",str(out),"--persist-drive"],inspect_fn=ins,persist_fn=per)
   data=json.loads(out.read_text())
   self.assertEqual(rc,2); self.assertEqual(n,{"inspect":1,"persist":1}); self.assertEqual(data["drive_persistence"]["status"],"HOLD")
if __name__=="__main__": unittest.main(verbosity=2)
