import io,hashlib,json,unittest,zipfile
from tools.verify_packet import verify,digest,PACKET_ID

def make_zip(files=None):
    files=files or {'src/test.luau':b'return true\n'}
    manifest=dict(format='P0D_D16_VISUAL_MANIFEST_V1',packet_id=PACKET_ID,game_id='TRAP_RAIDERS',work_id='p0d-siege-v19',files={p:digest(data) for p,data in files.items()})
    files=dict(files,**{'BUILD_MANIFEST.json':json.dumps(manifest).encode()})
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:
        for name,data in files.items():z.writestr(name,data)
    return out.getvalue()

class IntegrityTests(unittest.TestCase):
    def test_valid(self):self.assertEqual(verify(make_zip())['files'],1)
    def test_path_traversal(self):
        for name in ('../evil','/abs','C:evil','bad\\path','dir//x','./x','dir/../x'):
            with self.subTest(name=name),self.assertRaises(ValueError):verify(make_zip({name:b'secret'}))
    def test_tampered_digest(self):
        data=make_zip().replace(b'return true',b'return xxxx')
        with self.assertRaises((ValueError,zipfile.BadZipFile)):verify(data)
    def test_no_manifest(self):
        z=io.BytesIO()
        with zipfile.ZipFile(z,'w') as o:o.writestr('a',b'1')
        with self.assertRaises(ValueError):verify(z.getvalue())
    def test_corrupt_bytes(self):
        with self.assertRaises((ValueError,zipfile.BadZipFile)):verify(b'bad')
    def test_size_guard(self):
        with self.assertRaises(ValueError):verify(b'X'*(2_000_001))
    def test_reject_different_packet(self):
        data=make_zip().replace(PACKET_ID.encode(),b'NOT-A-CURRENT-PACKET')
        with self.assertRaises((ValueError,zipfile.BadZipFile)):verify(data)

if __name__=='__main__':unittest.main()
