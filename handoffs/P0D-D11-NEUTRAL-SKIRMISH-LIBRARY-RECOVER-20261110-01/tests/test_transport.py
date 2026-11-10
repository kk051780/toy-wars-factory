import base64
import hashlib
import io
import json
import tempfile
from pathlib import Path
import unittest
import zipfile
from cryptography.exceptions import InvalidTag
from tools.seal_handoff import seal
from tools.restore_handoff import restore
from tools.verify_packet import verify_bytes


def sample_zip():
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED) as z:
        data=b'hello\n'
        z.writestr('luau/sample.luau',data)
        z.writestr('BUILD_MANIFEST.json',json.dumps(dict(schema_version=1,classification='REFERENCE_ONLY',packet_id='a',
            files={'luau/sample.luau':dict(size_bytes=len(data),sha256=hashlib.sha256(data).hexdigest())})))
    return b.getvalue()

class TransportTests(unittest.TestCase):
    def test_verified_zip(self): self.assertTrue(verify_bytes(sample_zip())['ok'])
    def test_zip_digest(self): self.assertEqual(verify_bytes(sample_zip())['zip_sha256'],hashlib.sha256(sample_zip()).hexdigest())
    def test_roundtrip(self):
        src=sample_zip();doc,key=seal(src,'TRAP_RAIDERS','p0d-siege-v19','v43a')
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp); envelope=folder/'e.json'; envelope.write_text(json.dumps(doc));dest=folder/'restore.zip'
            self.assertEqual(restore(envelope,dest,key),hashlib.sha256(src).hexdigest())
            self.assertEqual(dest.read_bytes(),src)
    def test_bad_key(self):
        doc,key=seal(sample_zip(),'TRAP_RAIDERS','w','p')
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'e.json';a.write_text(json.dumps(doc))
            with self.assertRaises(InvalidTag): restore(a,Path(tmp)/'z.zip',base64.urlsafe_b64encode(b'Z'*32).decode().rstrip('='))
    def test_corrupt_ciphertext(self):
        doc,key=seal(sample_zip(),'TRAP_RAIDERS','w','p')
        doc['ciphertext_sha256']='f'*64
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'e.json';a.write_text(json.dumps(doc))
            with self.assertRaisesRegex(ValueError,'CIPHERTEXT_SHA_MISMATCH'):restore(a,Path(tmp)/'z.zip',key)
    def test_repeat_destination_rejected(self):
        doc,key=seal(sample_zip(),'TRAP_RAIDERS','w','p')
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'e.json';a.write_text(json.dumps(doc));b=Path(tmp)/'z.zip';b.write_bytes(b'x')
            with self.assertRaises(FileExistsError):restore(a,b,key)
    def test_bad_ids(self):
        with self.assertRaisesRegex(ValueError,'INVALID_ID'):seal(sample_zip(),'TRAP RAIDERS','w','p')
    def test_zip_slip_rejected_by_seal(self):
        src=io.BytesIO()
        with zipfile.ZipFile(src,'w') as z:z.writestr('../evil',b'data')
        with self.assertRaisesRegex(ValueError,'ZIP_UNSAFE_PATH'):seal(src.getvalue(),'g','w','p')
    def test_zip_slip_rejected_by_verify(self):
        src=io.BytesIO()
        with zipfile.ZipFile(src,'w') as z:z.writestr('../evil',b'data')
        with self.assertRaisesRegex(ValueError,'ZIP_UNSAFE_ENTRY'):verify_bytes(src.getvalue())
    def test_manifest_tamper(self):
        src=io.BytesIO()
        with zipfile.ZipFile(src,'w') as z:
            z.writestr('a',b'bad')
            z.writestr('BUILD_MANIFEST.json',json.dumps(dict(schema_version=1,classification='REFERENCE_ONLY',files={'a':{'sha256':'0'*64,'size_bytes':3}})))
        with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):verify_bytes(src.getvalue())

if __name__=='__main__':unittest.main()
