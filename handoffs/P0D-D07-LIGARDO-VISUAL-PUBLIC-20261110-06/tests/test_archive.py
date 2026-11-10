import hashlib
import io
import json
import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from verify_packet import verify


def make_zip(names=None, manifest=True, data=b'hello', symlink=False, spoof_sha=False):
    if names is None: names=['src/x.luau']
    contents={n:data for n in names}
    m={'format':'P0D_BUILD_MANIFEST_V1','files':[{'path':n,'size':len(contents[n]),'sha256':hashlib.sha256(contents[n]).hexdigest()} for n in names]}
    if spoof_sha and m['files']:m['files'][0]['sha256']='0'*64
    bio=io.BytesIO()
    with zipfile.ZipFile(bio,'w',zipfile.ZIP_DEFLATED) as z:
        for n in names:
            i=zipfile.ZipInfo(n)
            i.create_system=3
            i.external_attr=((stat.S_IFLNK if symlink else stat.S_IFREG)|0o644)<<16
            z.writestr(i,contents[n])
        if manifest:z.writestr('BUILD_MANIFEST.json',json.dumps(m))
    return bio.getvalue()


def run(raw,sha=None):
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'test.zip'
        p.write_bytes(raw)
        return verify(p,sha)

class ArchiveTests(unittest.TestCase):
    def test_safe(self):self.assertEqual(run(make_zip())['file_count'],1)
    def test_safe_sha(self):
        b=make_zip()
        self.assertEqual(run(b,hashlib.sha256(b).hexdigest())['zip_sha256'],hashlib.sha256(b).hexdigest())
    def test_wrong_sha_rejected(self):
        with self.assertRaisesRegex(ValueError,'ZIP_SHA_MISMATCH'):run(make_zip(),'0'*64)
    def test_missing_manifest(self):
        with self.assertRaisesRegex(ValueError,'MISSING_MANIFEST'):run(make_zip(manifest=False))
    def test_traversal(self):
        with self.assertRaisesRegex(ValueError,'ZIP_UNSAFE_PATH'):run(make_zip(['../leak']))
    def test_windows_drive(self):
        with self.assertRaisesRegex(ValueError,'ZIP_UNSAFE_PATH'):run(make_zip(['C:/evil.txt']))
    def test_windows_slash(self):
        with self.assertRaisesRegex(ValueError,'ZIP_UNSAFE_PATH'):run(make_zip([r'..\evil']))
    def test_symlink(self):
        with self.assertRaisesRegex(ValueError,'ZIP_NON_REGULAR'):run(make_zip(symlink=True))
    def test_case_collision(self):
        with self.assertRaisesRegex(ValueError,'ZIP_DUPLICATE_OR_CASE_CONFLICT'):run(make_zip(['Test.lua','test.lua']))
    def test_sha_mismatch(self):
        with self.assertRaisesRegex(ValueError,'FILE_SHA_OR_SIZE_MISMATCH'):run(make_zip(spoof_sha=True))
    def test_missing_file(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:
            z.writestr('BUILD_MANIFEST.json',json.dumps({'format':'P0D_BUILD_MANIFEST_V1','files':[{'path':'nope','size':0,'sha256':'a'}]}))
        with self.assertRaisesRegex(ValueError,'MANIFEST_MISSING_EXTRA'):run(b.getvalue())
    def test_empty_zip(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w'):pass
        with self.assertRaisesRegex(ValueError,'ZIP_ENTRY_COUNT'):run(b.getvalue())
    def test_bad_manifest_format(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:z.writestr('BUILD_MANIFEST.json','{}')
        with self.assertRaisesRegex(ValueError,'MANIFEST_FORMAT'):run(b.getvalue())
    def test_invalid_zip(self):
        with self.assertRaises(zipfile.BadZipFile):run(b'not a zip')

if __name__=='__main__':unittest.main()
