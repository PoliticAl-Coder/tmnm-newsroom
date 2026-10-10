import unittest
from EXACT_BODY_CAPTURE import _privacy_check

class Privacy(unittest.TestCase):
 def assertHold(self,src):
  with self.assertRaises(ValueError):_privacy_check('def audited():\n'+''.join('    '+line+'\n' for line in src.splitlines()))
 def test_recovery(self):self.assertHold("recovery_code='PUBLIC_FAKE'")
 def test_nested(self):self.assertHold("if True:\n    backup_code='PUBLIC_FAKE'")
 def test_indirect(self):self.assertHold("x=getattr(os, 'en'+'viron')")
 def test_obfuscated(self):self.assertHold("x='rec' + 'overy' + '_code'")
 def test_env(self):self.assertHold("x=os.environ['MOCK_VALUE']")
 def test_env_call(self):self.assertHold("x=os.getenv('MOCK_VALUE')")
 def test_encoded_identifier(self):self.assertHold("x='\\x72ecovery_code'")
 def test_secret_pattern(self):self.assertHold("x='Bearer ABCDEFGHIJKLMNO123456789'")
 def test_route_constant(self):_privacy_check("def allowed():\n    route='/api/packages'\n    field='status'\n    if field == 'status':\n        return route\n")
 def test_typical_logic(self):_privacy_check("def allowed():\n    stage='IN_PRODUCTION'\n    return stage == 'IN_PRODUCTION'\n")
 def test_keyword_rejection_without_echo(self):
  try:_privacy_check("def f():\n    recovery_code='FAKE_CANARY_VALUE'\n")
  except ValueError as e:self.assertNotIn('FAKE_CANARY_VALUE',str(e))
  else:self.fail('not rejected')
if __name__=='__main__':unittest.main()
