import hashlib,io,json,pathlib,sys,unittest,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.verify_packet import verify

def zip_with(items):
    if 'BUILD_MANIFEST.json' not in items:
        items=dict(items)
        items['BUILD_MANIFEST.json']=json.dumps({'format':'P0D_D16_MANIFEST_V1','packet_id':'P0D-D16-SCALE-FX-20261110-01',
                     'files':{p:hashlib.sha256(v).hexdigest() for p,v in items.items()}}).encode()
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,blob in items.items():z.writestr(name,blob)
    return b.getvalue()

class Integrity(unittest.TestCase):
    def test_good(self):self.assertEqual(verify(zip_with({'README.md':b'hi'}))['files'],1)
    def test_traversal(self):
        with self.assertRaisesRegex(ValueError,'UNSAFE'):verify(zip_with({'../evil':b'evil'}))
    def test_windows_backslash(self):
        with self.assertRaisesRegex(ValueError,'UNSAFE'):verify(zip_with({'x\\y':b'evil'}))
    def test_absolute(self):
        with self.assertRaisesRegex(ValueError,'UNSAFE'):verify(zip_with({'/root/a':b'evil'}))
    def test_modified_content(self):
        z=zip_with({'README.md':b'good'});a={}
        with zipfile.ZipFile(io.BytesIO(z)) as src:
            for name in src.namelist(): a[name]=src.read(name)
        a['README.md']=b'bad'
        with self.assertRaisesRegex(ValueError,'MANIFEST_HASH_MISMATCH'):verify(zip_with(a))
    def test_bad_id(self):
        z=zip_with({'README.md':b'hi'});a={}
        with zipfile.ZipFile(io.BytesIO(z)) as src:
            for name in src.namelist(): a[name]=src.read(name)
        a['BUILD_MANIFEST.json']=a['BUILD_MANIFEST.json'].replace(b'20261110-01',b'20261110-00')
        with self.assertRaisesRegex(ValueError,'MANIFEST_ID_MISMATCH'):verify(zip_with(a))
    def test_missing_manifest(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:z.writestr('README.md','hi')
        with self.assertRaisesRegex(ValueError,'DUPLICATE_OR_NO_MANIFEST'):verify(b.getvalue())
    def test_unbounded_zip(self):
        with self.assertRaisesRegex(ValueError,'ZIP_SIZE'):verify(b'0'*(2_000_001))

if __name__=='__main__':unittest.main()
