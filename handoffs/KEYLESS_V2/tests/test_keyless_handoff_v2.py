import base64
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile

PATH=Path(__file__).resolve().parents[1]/'tools'/'keyless_handoff_v2.py'
spec=importlib.util.spec_from_file_location('handoff',PATH)
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)


def make_zip(path,name='one.txt',body=b'hello'):
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:z.writestr(name,body)


class KeylessHandoffTests(unittest.TestCase):
    def setUp(self):
        self.d=tempfile.TemporaryDirectory();self.addCleanup(self.d.cleanup)
        self.root=Path(self.d.name)
        self.identity=self.root/'secret'/'identity.json'
        self.public=self.root/'public.json'
        self.z=self.root/'input.zip'
        self.envelope=self.root/'packet.json'
        self.out=self.root/'restored.zip'
        make_zip(self.z)
        self.kid=h.enroll(self.identity,self.public)
        self.packet='D07-TRIAL'
    def seal(self):return h.seal(self.z,self.public,self.packet,self.envelope)
    def restore(self):return h.restore(self.envelope,self.identity,self.out,expected_zip_sha=h.sha(self.z.read_bytes()),expected_packet_id=self.packet)
    def test_enroll_file_permissions_posix(self):
        self.assertEqual(h.read_json(self.public)['recipient_key_id'],self.kid)
        self.assertTrue(self.identity.exists())
        if os.name!='nt':self.assertEqual(self.identity.stat().st_mode&0o777,0o600)
    def test_no_manual_key_required(self):
        m=self.seal();r=self.restore()
        self.assertEqual(m,r);self.assertEqual(self.z.read_bytes(),self.out.read_bytes())
        self.assertNotIn('private_key_b64',self.envelope.read_text())
    def test_no_reenroll_clobber(self):
        with self.assertRaises(FileExistsError):h.enroll(self.identity,self.public)
    def test_no_restore_clobber(self):
        self.seal();self.restore()
        with self.assertRaises(FileExistsError):self.restore()
    def test_wrong_local_identity_rejected(self):
        self.seal();identity2=self.root/'two.json';pub2=self.root/'two-public.json';h.enroll(identity2,pub2)
        with self.assertRaises(ValueError):h.restore(self.envelope,identity2,self.out)
    def test_wrong_packet_rejected(self):
        self.seal()
        with self.assertRaises(ValueError):h.restore(self.envelope,self.identity,self.out,expected_packet_id='OTHER')
    def test_wrong_zip_sha_rejected(self):
        self.seal()
        with self.assertRaises(ValueError):h.restore(self.envelope,self.identity,self.out,expected_zip_sha='0'*64)
    def test_ciphertext_tamper_rejected(self):
        self.seal();j=h.read_json(self.envelope);raw=bytearray(h.unb64(j['ciphertext_b64']));raw[-1]^=1;j['ciphertext_b64']=h.b64(bytes(raw));self.envelope.write_bytes(h.canonical(j))
        with self.assertRaises(Exception):self.restore()
    def test_aad_tamper_rejected(self):
        self.seal();j=h.read_json(self.envelope);j['meta']['zip_sha256']='0'*64;self.envelope.write_bytes(h.canonical(j))
        with self.assertRaises(Exception):self.restore()
    def test_ephemeral_tamper_rejected(self):
        self.seal();j=h.read_json(self.envelope);j['ephemeral_public_key_b64']=h.b64(b'1'*32);self.envelope.write_bytes(h.canonical(j))
        with self.assertRaises(Exception):self.restore()
    def test_nonce_tamper_rejected(self):
        self.seal();j=h.read_json(self.envelope);j['nonce_b64']=h.b64(b'0'*12);self.envelope.write_bytes(h.canonical(j))
        with self.assertRaises(Exception):self.restore()
    def test_bad_recipient_fingerprint(self):
        j=h.read_json(self.public);j['recipient_key_id']='0'*32;self.public.write_bytes(h.canonical(j))
        with self.assertRaises(ValueError):self.seal()
    def test_bad_packet_id(self):
        with self.assertRaises(ValueError):h.seal(self.z,self.public,'../../evil',self.envelope)
    def test_encrypted_blob_different_each_time(self):
        self.seal();a=self.envelope.read_bytes();new=self.root/'new.json';h.seal(self.z,self.public,self.packet,new)
        self.assertNotEqual(a,new.read_bytes())
    def test_safe_zip_valid(self):
        self.assertEqual(h.verify_zip(self.z.read_bytes())['members'],1)
    def test_zip_slip_rejected(self):
        make_zip(self.z,'../out.txt')
        with self.assertRaises(ValueError):self.seal()
    def test_zip_windows_path_rejected(self):
        make_zip(self.z,r'..\steal.txt')
        with self.assertRaises(ValueError):self.seal()
    def test_zip_duplicate_member_rejected(self):
        with zipfile.ZipFile(self.z,'w') as z:
            z.writestr('a','1');z.writestr('a','2')
        with self.assertRaises(ValueError):self.seal()
    def test_directory_trailing_slash_allowed(self):
        with zipfile.ZipFile(self.z,'w') as z:
            z.writestr('folder/','');z.writestr('folder/a','x')
        self.seal();self.restore()
    def test_reject_invalid_zip(self):
        self.z.write_bytes(b'not a zip')
        with self.assertRaises(zipfile.BadZipFile):self.seal()
    def test_reject_large_input(self):
        with self.assertRaises(ValueError):h.unb64('a'*(h.MAX_ZIP_BYTES*2+1))
    def test_no_plaintext_in_envelope(self):
        make_zip(self.z,body=b'PRIVATE_SOURCE_SENTINEL_12345')
        self.seal()
        self.assertNotIn('PRIVATE_SOURCE_SENTINEL_12345',self.envelope.read_text())

if __name__=='__main__':unittest.main()
