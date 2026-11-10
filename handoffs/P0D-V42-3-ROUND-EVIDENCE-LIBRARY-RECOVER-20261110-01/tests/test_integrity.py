import hashlib
import io
import json
import pathlib
import tempfile
import unittest
import zipfile
from verify_packet import verify

ROOT=pathlib.Path(__file__).resolve().parents[1]
FILES=[p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='PACKET_MANIFEST.json']

class IntegrityTests(unittest.TestCase):
    def pack(self, transform=None, extra=None):
        blobs={str(p.relative_to(ROOT)).replace('\\','/'): p.read_bytes() for p in FILES}
        if transform: transform(blobs)
        mf={'game_id':'TRAP_RAIDERS','work_id':'p0d-siege-v19','studio_qa':'NOT_TESTED','release_ready':False,
            'files':{k:{'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()} for k,v in sorted(blobs.items())}}
        with tempfile.NamedTemporaryFile(suffix='.zip',delete=False) as tmp:
            path=pathlib.Path(tmp.name)
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
            for k,v in blobs.items(): z.writestr(k,v)
            z.writestr('PACKET_MANIFEST.json',json.dumps(mf))
            if extra: z.writestr(extra,'junk')
        self.addCleanup(path.unlink)
        return path

    def test_clean_packet(self):
        self.assertTrue(verify(self.pack())['ok'])

    def test_hash_mismatch_detected(self):
        p=self.pack()
        with zipfile.ZipFile(p) as z:
            blobs={n:z.read(n) for n in z.namelist()}
        blobs['README.md']=b'tampered'
        with zipfile.ZipFile(p,'w') as z:
            for k,v in blobs.items(): z.writestr(k,v)
        with self.assertRaisesRegex(ValueError,'HASH_MISMATCH'):
            verify(p)

    def test_zip_slip_rejected(self):
        with self.assertRaisesRegex(ValueError,'BAD_ZIP_ENTRIES'):
            verify(self.pack(extra='../evil.txt'))

    def test_surplus_file_rejected(self):
        with self.assertRaisesRegex(ValueError,'UNEXPECTED_OR_MISSING_FILES'):
            verify(self.pack(extra='surprise.lua'))

    def test_missing_file_rejected(self):
        p=self.pack()
        with zipfile.ZipFile(p) as z:
            blobs={n:z.read(n) for n in z.namelist() if n!='README.md'}
        with zipfile.ZipFile(p,'w') as z:
            for k,v in blobs.items(): z.writestr(k,v)
        with self.assertRaisesRegex(ValueError,'UNEXPECTED_OR_MISSING_FILES'):
            verify(p)

if __name__=='__main__':unittest.main()
