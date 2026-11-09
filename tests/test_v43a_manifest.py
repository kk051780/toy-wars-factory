import io
import sys
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import verify_manifest


def make_zip():
    import json
    manifest = json.loads((ROOT / 'BUILD_MANIFEST.json').read_text())
    names = [item['path'] for item in manifest['files']] + ['BUILD_MANIFEST.json']
    with io.BytesIO() as buf:
        with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            for name in names:
                z.writestr(name, (ROOT / name).read_bytes())
        return buf.getvalue()


class ManifestGuardTests(unittest.TestCase):
    def test_self_contained_zip_verified(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / 'handoff.zip'
            path.write_bytes(make_zip())
            self.assertTrue(verify_manifest.verify_zip(path))

    def test_duplicate_case_path_rejected(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bad.zip'
            with zipfile.ZipFile(io.BytesIO(make_zip())) as src:
                payloads = [(n, src.read(n)) for n in src.namelist()]
            with zipfile.ZipFile(path, 'w') as z:
                for name, payload in payloads:
                    z.writestr(name, payload)
                z.writestr('README.MD', b'bad')
            with self.assertRaises(ValueError):
                verify_manifest.verify_zip(path)