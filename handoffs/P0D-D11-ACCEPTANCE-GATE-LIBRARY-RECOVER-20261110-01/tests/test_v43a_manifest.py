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
    # Reconstruct legacy ZIP using preserved original manifest & test bytes.
    import json
    original=(ROOT / 'docs/LEGACY_BUILD_MANIFEST.json').read_bytes()
    manifest=json.loads(original)
    names=[item['path'] for item in manifest['files']]
    with io.BytesIO() as buf:
        with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for name in names:
                content=(ROOT / 'docs/LEGACY_TEST_V43A_MANIFEST.py.txt').read_bytes() if name=='tests/test_v43a_manifest.py' else (ROOT/name).read_bytes()
                z.writestr(name,content)
            z.writestr('BUILD_MANIFEST.json',original)
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
