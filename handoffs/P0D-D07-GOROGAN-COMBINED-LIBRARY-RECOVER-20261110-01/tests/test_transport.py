import unittest, pathlib, sys, io, zipfile, json, copy
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from verify_packet import verify,PACKET_ID,sha


def rezip(values):
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED) as z:
        for k,v in values:z.writestr(k,v)
    return b.getvalue()

def original():
    # Verify the exact legacy ZIP source list. PUBLIC_SOURCE_V1 uses a new root
    # manifest, so reconstruct the old ZIP input from its preserved manifest.
    legacy=(ROOT/'docs/LEGACY_BUILD_MANIFEST.json').read_bytes()
    old=json.loads(legacy)
    entries={name:(ROOT/name).read_bytes() for name in old['files']}
    # Preserve the byte-identical original test as legacy source reference.
    entries['tests/test_transport.py']=(ROOT/'docs/LEGACY_TEST_TRANSPORT.py.txt').read_bytes()
    entries['BUILD_MANIFEST.json']=legacy
    return entries

class Transport(unittest.TestCase):
    def setUp(self):
        self.data=original()
        self.assertIn('BUILD_MANIFEST.json',self.data)
    def test_canonical_package(self):
        r=verify(rezip(self.data.items()));self.assertTrue(r['ok'])
    def test_identity(self):self.assertEqual(PACKET_ID,'P0D-D07-GOROGAN-COMBINED-WIRING-20261110-04')
    def test_sha_digest(self):self.assertEqual(len(sha(b'hello')),64)
    def test_bytes_rejected(self):
        with self.assertRaises(ValueError):verify('not bytes')
    def test_empty_rejected(self):
        with self.assertRaises(ValueError):verify(b'')
    def test_traversal(self):
        d=dict(self.data);d['../outside.txt']=b'x'
        with self.assertRaises(ValueError):verify(rezip(d.items()))
    def test_absolute(self):
        d=dict(self.data);d['/escape.txt']=b'x'
        with self.assertRaises(ValueError):verify(rezip(d.items()))
    def test_windows_slash(self):
        d=dict(self.data);d['..\\escape.txt']=b'x'
        with self.assertRaises(ValueError):verify(rezip(d.items()))
    def test_corrupt_source(self):
        d=dict(self.data);d['luau/GoroganCombinedRuntime.luau']=b'dangerous forged file'
        with self.assertRaises(ValueError):verify(rezip(d.items()))
    def test_manifest_wrong_id(self):
        d=dict(self.data);j=json.loads(d['BUILD_MANIFEST.json']);j['packet_id']='other';d['BUILD_MANIFEST.json']=json.dumps(j).encode()
        with self.assertRaises(ValueError):verify(rezip(d.items()))
    def test_missing_manifest(self):
        d=dict(self.data);del d['BUILD_MANIFEST.json']
        with self.assertRaises(ValueError):verify(rezip(d.items()))
    def test_extra_unlisted(self):
        d=dict(self.data);d['foo']=b'x'
        with self.assertRaises(ValueError):verify(rezip(d.items()))
    def test_bad_zip(self):
        with self.assertRaises(zipfile.BadZipFile):verify(b'garbage')
    def test_zip_oversize(self):
        with self.assertRaises(ValueError):verify(b'a'*1_000_001)
    def test_duplicate_name(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED) as z:
            for k,v in self.data.items():z.writestr(k,v)
            z.writestr('README.md',b'duplicate')
        with self.assertRaises(ValueError):verify(b.getvalue())

if __name__=='__main__':unittest.main()
