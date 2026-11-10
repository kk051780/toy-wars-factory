import io
import json
import unittest
import zipfile
import os
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from seal_handoff import seal, check_zip_bytes
from verify_packet import verify_bytes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import hashlib,base64


def sample_zip():
    manifest={'schema_version':1,'classification':'REFERENCE_ONLY','packet_id':'P0D-D17-COSMETIC-CATALOG-20261110-01','files':{'a.txt':{'sha256':hashlib.sha256(b'example').hexdigest(),'size_bytes':7}}}
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('a.txt',b'example')
        z.writestr('BUILD_MANIFEST.json',json.dumps(manifest))
    return b.getvalue()

class TransportTest(unittest.TestCase):
    def test_verify_valid(self):self.assertTrue(verify_bytes(sample_zip())['ok'])
    def test_verify_manifest_filecount(self):self.assertEqual(verify_bytes(sample_zip())['file_count'],1)
    def test_verify_missing_manifest(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:z.writestr('a','b')
        with self.assertRaises(ValueError):verify_bytes(b.getvalue())
    def test_verify_path_escape(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:z.writestr('../escape','b')
        with self.assertRaises(ValueError):verify_bytes(b.getvalue())
    def test_verify_duplicate_entry(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:
            z.writestr('a','1');z.writestr('a','2')
        with self.assertRaises(ValueError):verify_bytes(b.getvalue())
    def test_verify_sha_mismatch(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:
            z.writestr('a.txt','CHANGED');z.writestr('BUILD_MANIFEST.json',json.dumps({'schema_version':1,'classification':'REFERENCE_ONLY','files':{'a.txt':{'sha256':'x','size_bytes':7}}}))
        with self.assertRaises(ValueError):verify_bytes(b.getvalue())
    def test_zip_corruption(self):
        with self.assertRaises(Exception):verify_bytes(b'not a zip')
    def test_key_length_32(self):
        doc,key=seal(sample_zip(),'TRAP_RAIDERS','p0d-siege-v19','P0D-D17-COSMETIC-CATALOG-20261110-01')
        self.assertEqual(len(base64.urlsafe_b64decode(key+'=')),32)
    def test_encrypted_roundtrip(self):
        plain=sample_zip();doc,key=seal(plain,'TRAP_RAIDERS','p0d-siege-v19','P0D-D17-COSMETIC-CATALOG-20261110-01')
        rawkey=base64.urlsafe_b64decode(key+'=')
        got=AESGCM(rawkey).decrypt(base64.b64decode(doc['nonce_b64']),base64.b64decode(''.join(doc['ciphertext_b64'])),base64.b64decode(doc['aad_b64']))
        self.assertEqual(got,plain)
    def test_bad_key_fails(self):
        plain=sample_zip();doc,key=seal(plain,'TRAP_RAIDERS','p0d-siege-v19','P0D-D17-COSMETIC-CATALOG-20261110-01')
        with self.assertRaises(Exception):AESGCM(os.urandom(32)).decrypt(base64.b64decode(doc['nonce_b64']),base64.b64decode(''.join(doc['ciphertext_b64'])),base64.b64decode(doc['aad_b64']))
    def test_tamper_fails(self):
        doc,key=seal(sample_zip(),'TRAP_RAIDERS','p0d-siege-v19','P0D-D17-COSMETIC-CATALOG-20261110-01')
        data=bytearray(base64.b64decode(''.join(doc['ciphertext_b64'])));data[5]^=1
        with self.assertRaises(Exception):AESGCM(base64.urlsafe_b64decode(key+'=')).decrypt(base64.b64decode(doc['nonce_b64']),bytes(data),base64.b64decode(doc['aad_b64']))
    def test_aad_identity(self):
        doc,_=seal(sample_zip(),'TRAP_RAIDERS','p0d-siege-v19','P0D-D17-COSMETIC-CATALOG-20261110-01')
        self.assertIn(b'P0D-D17-COSMETIC-CATALOG',base64.b64decode(doc['aad_b64']))
    def test_secret_not_in_doc(self):
        doc,key=seal(sample_zip(),'TRAP_RAIDERS','p0d-siege-v19','P0D-D17-COSMETIC-CATALOG-20261110-01')
        self.assertNotIn(key,json.dumps(doc))
    def test_check_zip_bytes_rejects_unsafe(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:z.writestr('a/../b','x')
        with self.assertRaises(ValueError):check_zip_bytes(b.getvalue())
