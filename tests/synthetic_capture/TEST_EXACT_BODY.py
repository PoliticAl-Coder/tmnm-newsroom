import unittest, tempfile, pathlib, hashlib
from EXACT_BODY_CAPTURE import capture, ROOT_NAMES
class Probe(unittest.TestCase):
 def setup(self, mutator=None):
  t=tempfile.TemporaryDirectory();root=pathlib.Path(t.name);expected={}
  for role,(rel,names) in ROOT_NAMES.items():
   f=root/rel;f.parent.mkdir(parents=True,exist_ok=True)
   name=names[0];s=f'def {name}(item):\n    if item == "approved":\n        return "accepted"\n    return "hold"\n'
   if mutator and role=='claim':s=mutator(s)
   f.write_bytes(s.encode('utf-8'));expected[role]=hashlib.sha256(f.read_bytes()).hexdigest()
  return t,root,expected
 def test_exact_code_present(self):
  t,r,e=self.setup();self.addCleanup(t.cleanup);v=capture(r,e);self.assertIn('if item == "approved"',v['files']['claim']['functions'][ROOT_NAMES['claim'][1][0]]['body'])
 def test_hash_mismatch(self):
  t,r,e=self.setup();self.addCleanup(t.cleanup);e['claim']='0'*64
  with self.assertRaisesRegex(ValueError,'HASH_MISMATCH'):capture(r,e)
 def test_secret_assignment_rejected(self):
  t,r,e=self.setup(lambda s:s.replace('return "accepted"','token = "abcdef"\n        return token'));self.addCleanup(t.cleanup)
  with self.assertRaisesRegex(ValueError,'SENSITIVE_SOURCE'):capture(r,e)
 def test_sensitive_credential_rejected(self):
  t,r,e=self.setup(lambda s:s.replace('return "accepted"','return "Bearer abcdefghijklmnop"'));self.addCleanup(t.cleanup)
  with self.assertRaisesRegex(ValueError,'SENSITIVE_SOURCE'):capture(r,e)
 def test_unknown_role_rejected(self):
  t,r,e=self.setup();self.addCleanup(t.cleanup);e['unknown']='0'*64
  with self.assertRaisesRegex(ValueError,'MANIFEST_ROLES'):capture(r,e)
 def test_symlink_rejected(self):
  t,r,e=self.setup();self.addCleanup(t.cleanup)
  f=r/ROOT_NAMES['claim'][0];f.unlink();f.symlink_to(r/ROOT_NAMES['consumer'][0])
  with self.assertRaisesRegex(ValueError,'MISSING_OR_LINK|SYMLINK'):capture(r,e)
 def test_function_length_bound(self):
  t,r,e=self.setup(lambda s:s+'\n'*220);self.addCleanup(t.cleanup)
  v=capture(r,e);self.assertIn('claim',v['files'])
if __name__=='__main__':unittest.main()
