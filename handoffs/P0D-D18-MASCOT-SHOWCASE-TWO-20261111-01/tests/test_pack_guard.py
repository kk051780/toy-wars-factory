"""Manifest hard-stop behavior including tamper and secret scan."""
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import verify_handoff as pack

class PackGuardTests(unittest.TestCase):
    def test_main_manifest_matches_source(self):
        m=pack.manifest_for(ROOT)
        saved=json.loads((ROOT/'BUILD_MANIFEST.json').read_text(encoding='utf-8'))
        self.assertEqual(m,saved)

    def test_rejects_secret(self):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/'a.md';p.write_text('ghp_'+'x'*30,encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'secret-like'):
                pack.collect(pathlib.Path(d))

    def test_rejects_hidden_file(self):
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d)/'.env').write_text('no',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'unsafe source path'):
                pack.collect(pathlib.Path(d))

    def test_rejects_binary(self):
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d)/'file.json').write_bytes(b'\xff')
            with self.assertRaises(UnicodeDecodeError):
                pack.collect(pathlib.Path(d))

    def test_manifest_detects_tamper(self):
        import shutil
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)
            shutil.copytree(ROOT,p/'a')
            s=p/'a'
            (s/'README.md').write_text('changed')
            with self.assertRaisesRegex(ValueError,'manifest mismatch'):
                pack.do('verify',s)
