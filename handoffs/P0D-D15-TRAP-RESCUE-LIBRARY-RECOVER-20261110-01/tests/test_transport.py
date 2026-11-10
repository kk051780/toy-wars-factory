"""Actual zip safety/crypto helpers tests. Does not exercise Roblox/Luau."""
import io
import json
import sys
import unittest
import zipfile
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from verify_packet import verify_bytes
from seal_handoff import seal


def archive(paths):
    with io.BytesIO() as out:
        with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
            for name, contents in paths.items():z.writestr(name,contents)
        return out.getvalue()


class TestTransport(unittest.TestCase):
    def test_unsafe_absolute_path_rejected(self):
        with self.assertRaises(ValueError):verify_bytes(archive({'/unsafe':'x'}))
    def test_parent_path_rejected(self):
        with self.assertRaises(ValueError):verify_bytes(archive({'../unsafe':'x'}))
    def test_backslash_rejected(self):
        with self.assertRaises(ValueError):verify_bytes(archive({'a\\b':'x'}))
    def test_drive_path_rejected(self):
        with self.assertRaises(ValueError):verify_bytes(archive({'C:bad':'x'}))
    def test_missing_manifest_rejected(self):
        with self.assertRaises(ValueError):verify_bytes(archive({'x.txt':'hi'}))
    def test_truncated_zip_rejected(self):
        with self.assertRaises(ValueError):verify_bytes(b'not-a-zip')
    def test_seal_rejects_invalid_work_id(self):
        with self.assertRaises(ValueError):seal(archive({'x.txt':'x'}),'TRAP_RAIDERS','unsafe/../../','PACK')
    def test_seal_rejects_bad_nonce(self):
        with self.assertRaises(ValueError):seal(archive({'x.txt':'x'}),'TRAP_RAIDERS','p0d-siege-v19','D15',nonce=b'a')
    def test_aes_wrong_key_fails(self):
        secret=b'A'*32
        payload=archive({'x.txt':'safe'})
        doc,key=seal(payload,'TRAP_RAIDERS','p0d-siege-v19','D15',key=secret,nonce=b'X'*12)
        import base64
        dec=lambda v:base64.b64decode(''.join(v) if isinstance(v,list) else v)
        ct=dec(doc['ciphertext_b64']);aad=dec(doc['aad_b64']);nonce=dec(doc['nonce_b64'])
        with self.assertRaises(Exception):AESGCM(b'B'*32).decrypt(nonce,ct,aad)
    def test_aes_tamper_rejected(self):
        payload=archive({'x.txt':'safe'})
        doc,key=seal(payload,'TRAP_RAIDERS','p0d-siege-v19','D15',key=b'A'*32,nonce=b'X'*12)
        import base64
        dec=lambda v:base64.b64decode(''.join(v) if isinstance(v,list) else v)
        ct=bytearray(dec(doc['ciphertext_b64']));ct[0]^=1
        with self.assertRaises(Exception):AESGCM(b'A'*32).decrypt(b'X'*12,bytes(ct),dec(doc['aad_b64']))
    def test_aad_binds_target_package(self):
        payload=archive({'x.txt':'safe'})
        doc,key=seal(payload,'TRAP_RAIDERS','p0d-siege-v19','D15',key=b'A'*32,nonce=b'X'*12)
        import base64
        dec=lambda v:base64.b64decode(''.join(v) if isinstance(v,list) else v)
        ct=dec(doc['ciphertext_b64']);self.assertEqual(AESGCM(b'A'*32).decrypt(b'X'*12,ct,dec(doc['aad_b64'])),payload)
        with self.assertRaises(Exception):AESGCM(b'A'*32).decrypt(b'X'*12,ct,b'another-id')

if __name__=='__main__':unittest.main()
