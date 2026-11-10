import hashlib
import io
import json
import unittest
import zipfile
from tools.verify_packet import verify

PACKET='P0D-D14-RIDER-ATTACH-SAFETY-20261110-04'

def create(files=None,manifest=None,override_info=None):
    files={'a.txt':b'a','b/x.txt':b'b'} if files is None else files
    rows=[{'path':n,'size':len(data),'sha256':hashlib.sha256(data).hexdigest()} for n,data in files.items()]
    m=manifest or {'packet_id':PACKET,'files':rows}
    mem=io.BytesIO()
    with zipfile.ZipFile(mem,'w',zipfile.ZIP_DEFLATED) as archive:
        for n,data in files.items():
            info=zipfile.ZipInfo(n)
            if override_info and n in override_info:
                info.external_attr=override_info[n]
            archive.writestr(info,files[n])
        archive.writestr('BUILD_MANIFEST.json',json.dumps(m))
    return mem.getvalue()

class TestVerify(unittest.TestCase):
    def test_clean_zip(self):self.assertEqual(verify(create())['source_entries'],2)
    def test_abs_path(self):
        with self.assertRaisesRegex(ValueError,'UNSAFE_PATH'):verify(create({'/bad':b'x'}))
    def test_backslash(self):
        with self.assertRaisesRegex(ValueError,'UNSAFE_PATH'):verify(create({'a\\b':b'x'}))
    def test_parent_path(self):
        with self.assertRaisesRegex(ValueError,'UNSAFE_PATH'):verify(create({'a/../b':b'x'}))
    def test_drive_path(self):
        with self.assertRaisesRegex(ValueError,'UNSAFE_PATH'):verify(create({'C:a':b'x'}))
    def test_duplicate_casefold(self):
        with self.assertRaisesRegex(ValueError,'COLLISION'):verify(create({'a.txt':b'a','A.TXT':b'b'}))
    def test_missing_manifest(self):
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:z.writestr('a.txt',b'a')
        with self.assertRaisesRegex(ValueError,'MISSING_MANIFEST'):verify(out.getvalue())
    def test_duplicate_manifest_row(self):
        rows=[{'path':'a.txt','size':1,'sha256':hashlib.sha256(b'a').hexdigest()}]*2
        with self.assertRaisesRegex(ValueError,'MANIFEST_FILE'):verify(create({'a.txt':b'a','b.txt':b'b'},manifest={'packet_id':PACKET,'files':rows}))
    def test_tampered_hash(self):
        row={'path':'a.txt','size':1,'sha256':'0'*64}
        with self.assertRaisesRegex(ValueError,'MANIFEST_SHA'):verify(create({'a.txt':b'a'},manifest={'packet_id':PACKET,'files':[row]}))
    def test_bad_packet_id(self):
        with self.assertRaisesRegex(ValueError,'MANIFEST_ID'):verify(create({'a.txt':b'a'},manifest={'packet_id':'other','files':[{'path':'a.txt','size':1,'sha256':hashlib.sha256(b'a').hexdigest()}]}))
    def test_missing_extra_file(self):
        row={'path':'a.txt','size':1,'sha256':hashlib.sha256(b'a').hexdigest()}
        with self.assertRaisesRegex(ValueError,'MANIFEST_COUNT'):verify(create({'a.txt':b'a','b.txt':b'b'},manifest={'packet_id':PACKET,'files':[row]}))
    def test_symlink_entry(self):
        with self.assertRaisesRegex(ValueError,'SPECIAL_ENTRY'):verify(create({'a.txt':b'a'},override_info={'a.txt':0o120777<<16}))
    def test_corrupt(self):
        with self.assertRaises((ValueError,zipfile.BadZipFile)):verify(create()[:20])
    def test_oversize(self):
        with self.assertRaisesRegex(ValueError,'INPUT_LIMIT'):verify(b'0'*2_000_001)
    def test_duplicate_json_keys(self):
        bad='{"packet_id":"'+PACKET+'","packet_id":"'+PACKET+'","files":[]}'
        mem=io.BytesIO()
        with zipfile.ZipFile(mem,'w') as z:z.writestr('BUILD_MANIFEST.json',bad)
        with self.assertRaisesRegex(ValueError,'DUPLICATE_JSON'):verify(mem.getvalue())

if __name__=='__main__':unittest.main()
