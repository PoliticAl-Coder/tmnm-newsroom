import importlib.util, json, os, pathlib, tempfile, unittest, zipfile
from unittest.mock import patch

P=pathlib.Path(__file__).with_name("collect_current_publishing_source.py")
spec=importlib.util.spec_from_file_location("collector",P)
c=importlib.util.module_from_spec(spec); spec.loader.exec_module(c)

class CollectorTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(prefix="TMNM collector tests ")
  self.base=pathlib.Path(self.t.name)
  self.root=self.base/"Local App Data"/"TMNM"; self.root.mkdir(parents=True)
  (self.root/"ControlRoom").mkdir(); (self.root/"LocalWorker").mkdir()
  self.f("ControlRoom/app.py","print('control')")
  self.f("LocalWorker/worker.py","print('worker') # owner console 8766")
  self.f("ControlRoom/publisher.py","facebook publisher")
 def tearDown(self): self.t.cleanup()
 def f(self,rel,text=None,data=None):
  p=self.root/rel; p.parent.mkdir(parents=True,exist_ok=True)
  if data is not None:p.write_bytes(data)
  else:p.write_text(text or "print('ok')",encoding="utf-8")
  return p
 def test_same_captured_bytes_are_hashed_and_archived(self):
  cap=c.collect(self.root); rel,data=cap[0]; expected=c.digest(data)
  self.f(str(rel),"print('CHANGED_AFTER_CAPTURE')")
  out=self.base/"outside"; z=c.write_archive(cap,out)
  with zipfile.ZipFile(z) as a:
   archived=a.read(str(rel).replace("\\","/")); man=json.loads(a.read("SOURCE_MANIFEST.json"))
  self.assertEqual(archived,data); self.assertEqual(next(x["sha256"] for x in man["files"] if x["path"]==str(rel).replace("\\","/")),expected)
 def test_requires_absolute_localappdata(self):
  with self.assertRaisesRegex(c.CollectorError,"LOCALAPPDATA_NOT_ABSOLUTE"): c.absolute_localappdata({"LOCALAPPDATA":"relative"})
 def test_rejects_symlink_or_reparse_before_read(self):
  target=self.base/"outside.py"; target.write_text("print('x')")
  link=self.root/"ControlRoom"/"escape.py"
  try: os.symlink(target,link)
  except OSError: self.skipTest("symlink privilege unavailable")
  with self.assertRaisesRegex(c.CollectorError,"REPARSE_POINT_REJECTED"): c.collect(self.root)
 def test_prunes_excluded_directory_before_read(self):
  p=self.f("ControlRoom/logs/secret.py","api_key='REAL_SECRET_123456789'")
  with patch.object(pathlib.Path,"read_bytes",autospec=True,side_effect=lambda obj: (_ for _ in ()).throw(AssertionError("excluded read")) if obj==p else open(obj,"rb").read()):
   cap=c.collect(self.root)
  self.assertFalse(any(str(r).startswith("ControlRoom\\logs") or str(r).startswith("ControlRoom/logs") for r,_ in cap))
 def test_oversized_fails_not_omits(self):
  p=self.root/"ControlRoom"/"big.py"; p.write_bytes(b"x"*(c.MAX_BYTES+1))
  with self.assertRaisesRegex(c.CollectorError,"OVERSIZED"): c.collect(self.root)
 def test_unreadable_fails_not_omits(self):
  victim=self.root/"ControlRoom"/"app.py"; real=pathlib.Path.read_bytes
  with patch.object(pathlib.Path,"read_bytes",autospec=True,side_effect=lambda obj: (_ for _ in ()).throw(OSError("denied")) if obj==victim else real(obj)):
   with self.assertRaisesRegex(c.CollectorError,"UNREADABLE"): c.collect(self.root)
 def test_missing_required_source_fails(self):
  import shutil; shutil.rmtree(self.root/"LocalWorker")
  with self.assertRaisesRegex(c.CollectorError,"MISSING_REQUIRED_SOURCE:LocalWorker"): c.collect(self.root)
 def test_empty_required_source_fails(self):
  (self.root/"ControlRoom"/"app.py").unlink()
  with self.assertRaisesRegex(c.CollectorError,"MISSING_REQUIRED_SOURCE:ControlRoom"): c.collect(self.root)
 def test_undecodable_fails(self):
  self.f("ControlRoom/bad.py",data=b"\xff\xfe\x00\x80")
  with self.assertRaisesRegex(c.CollectorError,"UNDECODABLE"): c.collect(self.root)
 def test_secret_api_key_assignment_fails(self):
  self.f("ControlRoom/key.py","api_key='REAL_API_KEY_1234567890'")
  with self.assertRaisesRegex(c.CollectorError,"SECRET_ASSIGNMENT"): c.collect(self.root)
 def test_quoted_dictionary_api_key_fails(self):
  self.f("ControlRoom/dictkey.py",'x={"api_key": "abcdefgh12345678"}')
  with self.assertRaisesRegex(c.CollectorError,"SECRET_ASSIGNMENT"): c.collect(self.root)
 def test_traversal_error_callback_raises(self):
  def fake_walk(*a,**kw):
   kw["onerror"](OSError("walk denied")); return iter(())
  with patch.object(c.os,"walk",side_effect=fake_walk):
   with self.assertRaisesRegex(c.CollectorError,"TRAVERSAL_ERROR"): c.collect(self.root)
 def test_config_secret_filename_is_never_read(self):
  p=self.f("ControlRoom/config.json","client_secret='REAL_SECRET_123456789'")
  self.assertTrue(c.EXCLUDE_NAME_RE.search(p.name))
 def test_unique_output_never_deletes_existing_zip(self):
  cap=c.collect(self.root); out=self.base/"outside"; out.mkdir(); existing=out/"keep.zip"; existing.write_bytes(b"KEEP")
  a=c.write_archive(cap,out); b=c.write_archive(cap,out)
  self.assertNotEqual(a,b); self.assertEqual(existing.read_bytes(),b"KEEP")
 def test_partial_removed_on_archive_failure(self):
  cap=c.collect(self.root); out=self.base/"outside"
  with patch.object(zipfile.ZipFile,"writestr",side_effect=OSError("write fail")):
   with self.assertRaises(OSError): c.write_archive(cap,out)
  self.assertEqual(list(out.glob("*.partial")),[])
 def test_output_must_be_absolute(self):
  with self.assertRaisesRegex(c.CollectorError,"OUTPUT_DIR_NOT_ABSOLUTE"): c.write_archive(c.collect(self.root),pathlib.Path("relative"))

if __name__=="__main__": unittest.main(verbosity=2)
