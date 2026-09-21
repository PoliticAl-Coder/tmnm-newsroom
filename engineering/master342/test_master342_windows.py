"""Engineering-only native Windows tests for the unchanged MASTER342 package.

Usage: python -B test_master342_windows.py <extracted MASTER342 directory>
No OAuth, Drive or Facebook calls. Synthetic fixture directories only.
Runs existing offline tests plus native parser, reporting and clipboard tests.
Does not establish live publishing readiness or test interactive CMD pause.
"""
import contextlib
import importlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


class NativeWindowsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.name != 'nt':
            raise RuntimeError('Native Windows required; emulation is not a PASS')

    def setUp(self):
        self.fixture = tempfile.TemporaryDirectory(prefix='TMNM synthetic tests ')
        self.base = Path(self.fixture.name)
        self.desktop = self.base / 'Redirected Desktop With Spaces'
        self.desktop.mkdir()
        self.logs = []

    def tearDown(self):
        self.fixture.cleanup()

    def test_real_parser_accepts_package(self):
        controller.parser_gate(package, self.logs)
        self.assertTrue(any('PARSER_PREFLIGHT=PASS' in x for x in self.logs))

    def test_real_parser_rejects_malformed_input_without_execution(self):
        root = self.base / 'Malformed Parser Fixture'
        root.mkdir()
        sentinel = root / 'MUST_NOT_EXIST.txt'
        (root / 'broken.ps1').write_text("Set-Content -LiteralPath '" + str(sentinel) + "' -Value 'executed'\nif (", encoding='ascii')
        with self.assertRaisesRegex(RuntimeError, 'PARSER_GATE_FAILED'):
            controller.parser_gate(root, self.logs)
        self.assertFalse(sentinel.exists())

    def test_real_parser_does_not_execute_valid_input(self):
        root = self.base / 'Valid Parser Fixture'
        root.mkdir()
        sentinel = root / 'MUST_NOT_EXIST.txt'
        (root / 'valid.ps1').write_text("Set-Content -LiteralPath '" + str(sentinel) + "' -Value 'executed'", encoding='ascii')
        controller.parser_gate(root, self.logs)
        self.assertFalse(sentinel.exists())

    def test_native_clipboard_roundtrip(self):
        p = self.base / 'Synthetic Clipboard Result.txt'
        p.write_text('TMNM SYNTHETIC RESULT\nUnicode: \u2014\n', encoding='utf-8')
        try:
            self.assertTrue(controller.clipboard(p), 'Native clipboard readback failed')
        finally:
            clear = controller.powershell("$ErrorActionPreference='Stop'; Set-Clipboard -Value $null")
            self.assertEqual(clear.returncode, 0, 'Runner clipboard cleanup failed')

    def validation_run(self, root):
        output = io.StringIO()
        with patch.object(controller, 'ROOT', root), \
             patch.object(controller, 'desktop_path', return_value=self.desktop), \
             patch.object(controller, 'clipboard', return_value=True), \
             patch.object(controller, 'transaction', side_effect=AssertionError('Operational branch entered')), \
             patch.dict(os.environ, {'TMNM_COMPLETION_MARKER': str(self.base / 'report.done')}), \
             contextlib.redirect_stdout(output):
            rc = controller.main(['--validate-only'])
        return rc, output.getvalue()

    def test_fresh_results_with_redirected_space_path(self):
        old = self.desktop / 'TMNM_MASTER338_RESULT.txt'
        old.write_text('STALE_RESULT_MUST_NOT_BE_DISPLAYED', encoding='ascii')
        for _ in range(2):
            rc, output = self.validation_run(package)
            self.assertEqual(rc, 0, output)
            self.assertNotIn('STALE_RESULT_MUST_NOT_BE_DISPLAYED', output)
            self.assertIn('OPERATIONAL_EXECUTION=NOT_PERFORMED', output)
        results = list(self.desktop.glob('TMNM_MASTER342_RESULT_*.txt'))
        self.assertEqual(len(results), 2)
        self.assertNotEqual(results[0].name, results[1].name)
        self.assertTrue((self.base / 'report.done').exists())

    def test_missing_file_has_fresh_visible_failure(self):
        copied = self.base / 'Incomplete Package With Spaces'
        shutil.copytree(package, copied)
        (copied / controller.PS_NAME).unlink()
        rc, output = self.validation_run(copied)
        self.assertNotEqual(rc, 0)
        self.assertIn('MANIFEST_FILE_SET_MISMATCH', output)
        self.assertIn('CONTROLLER_STATUS=FAIL', output)
        self.assertEqual(len(list(self.desktop.glob('TMNM_MASTER342_RESULT_*.txt'))), 1)


if __name__ == '__main__':
    if len(sys.argv) != 2 or os.name != 'nt':
        raise SystemExit('Usage on isolated native Windows: python -B test_master342_windows.py <package-dir>')
    package = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(package))
    controller = importlib.import_module('TMNM_MASTER342_CONTROLLER')
    controller.verify_manifest(package)
    offline = importlib.import_module('test_master342')
    suite = unittest.TestSuite([
        unittest.defaultTestLoader.loadTestsFromModule(offline),
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeWindowsTests),
    ])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print('NATIVE_WINDOWS_TESTS=' + ('PASS' if result.wasSuccessful() else 'FAIL'))
    print('LIVE_INTEGRATION=NOT_RUN; INTERACTIVE_CMD_PAUSE=NOT_TESTED')
    sys.exit(0 if result.wasSuccessful() else 1)
