import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'tools'))
import verify_manifest as m

class ManifestTests(unittest.TestCase):
    def test_local_good(self):
        self.assertGreaterEqual(m.verify(ROOT),10)
    def test_unsafe_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            doc=json.loads((ROOT/'BUILD_MANIFEST.json').read_text())
            doc['files'][0]['path']='../secret'
            (root/'BUILD_MANIFEST.json').write_text(json.dumps(doc))
            with self.assertRaisesRegex(ValueError,'unsafe path'):m.verify(root)
    def test_duplicate_casefold(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            doc=json.loads((ROOT/'BUILD_MANIFEST.json').read_text())
            doc['files'].append(copy.deepcopy(doc['files'][0]))
            (root/'BUILD_MANIFEST.json').write_text(json.dumps(doc))
            with self.assertRaises(ValueError):m.verify(root)
    def test_manifest_wrong_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);doc=json.loads((ROOT/'BUILD_MANIFEST.json').read_text())
            doc['packet_id']='OTHER';(root/'BUILD_MANIFEST.json').write_text(json.dumps(doc))
            with self.assertRaises(ValueError):m.verify(root)
