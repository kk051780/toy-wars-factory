"""Offline v43-A transport restore security regressions, no private game source."""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import restore_handoff_safe as m
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

WORK = 'p0d-siege-v19'
PACKET = 'v43A-neutral-skirmish-chatlead-20261110'
KEY = bytes(range(32))
SECRET = base64.urlsafe_b64encode(KEY).decode().rstrip('=')


def zip_bytes(files=None, symlink=False):
    files = files or {'README.txt': b'offline synthetic QA only', 'luau/core.luau': b'return true\n'}
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, contents in files.items():
            if symlink:
                info = zipfile.ZipInfo(name)
                info.create_system = 3
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                z.writestr(info, contents)
            else:
                z.writestr(name, contents)
    return out.getvalue()


def doc_for(blob=None):
    blob = zip_bytes() if blob is None else blob
    sha = hashlib.sha256(blob).hexdigest()
    aad = f'TRAP_RAIDERS|{WORK}|{PACKET}|zip_sha256={sha}'.encode()
    nonce = b'0123456789ab'
    ciphertext = AESGCM(KEY).encrypt(nonce, blob, aad)
    enc = lambda v: base64.b64encode(v).decode()
    return {'format': m.FORMAT, 'game_id': 'TRAP_RAIDERS', 'work_id': WORK,
            'packet_id': PACKET, 'zip_sha256': sha, 'nonce_b64': enc(nonce),
            'aad_b64': enc(aad), 'ciphertext_b64': [enc(ciphertext)],
            'ciphertext_sha256': hashlib.sha256(ciphertext).hexdigest(),
            'private_key_not_included': True}


def decode(doc, secret=SECRET, **kw):
    return m.decode_and_verify(doc, secret, expected_zip_sha256=kw.get('sha', doc['zip_sha256']),
                              expected_work_id=kw.get('work', WORK),
                              expected_packet_id=kw.get('packet', PACKET))


class DecodeTests(unittest.TestCase):
    def test_valid(self): self.assertTrue(decode(doc_for()).startswith(b'PK'))
    def test_wrong_key(self):
        with self.assertRaises(m.HandoffError): decode(doc_for(), base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip('='))
    def test_wrong_expect_sha(self):
        with self.assertRaises(m.HandoffError): decode(doc_for(), sha='0' * 64)
    def test_wrong_game(self):
        d=doc_for();d['game_id']='OTHER'
        with self.assertRaises(m.HandoffError): decode(d)
    def test_wrong_work(self):
        with self.assertRaises(m.HandoffError): decode(doc_for(), work='wrong-id')
    def test_wrong_packet(self):
        with self.assertRaises(m.HandoffError): decode(doc_for(), packet='wrong-id')
    def test_aad_tamper(self):
        d=doc_for();d['aad_b64']=base64.b64encode(b'fake').decode()
        with self.assertRaises(m.HandoffError): decode(d)
    def test_ciphertext_tamper(self):
        d=doc_for();d['ciphertext_b64']=['AAAA']
        with self.assertRaises(m.HandoffError): decode(d)
    def test_ciphertext_digest_tamper(self):
        d=doc_for();d['ciphertext_sha256']='0'*64
        with self.assertRaises(m.HandoffError): decode(d)
    def test_nonce_short(self):
        d=doc_for();d['nonce_b64']=base64.b64encode(b'xx').decode()
        with self.assertRaises(m.HandoffError): decode(d)
    def test_bad_key_chars(self):
        with self.assertRaises(m.HandoffError): decode(doc_for(), 'x!')
    def test_bad_envelope_format(self):
        d=doc_for();d['format']='BAD'
        with self.assertRaises(m.HandoffError): decode(d)
    def test_unsafe_parent_entry(self):
        d=doc_for(zip_bytes({'../escape':b'X'}))
        with self.assertRaises(m.HandoffError): decode(d)
    def test_case_collisions(self):
        d=doc_for(zip_bytes({'Foo':b'x','foo':b'y'}))
        with self.assertRaises(m.HandoffError): decode(d)
    def test_zip_symlink_entry(self):
        d=doc_for(zip_bytes({'link':b'../outside'}, symlink=True))
        with self.assertRaises(m.HandoffError): decode(d)
    def test_zip_expansion_cap(self):
        d=doc_for(zip_bytes({'huge.txt':b'0'*(m.MAX_ZIP+1)}))
        with self.assertRaises(m.HandoffError): decode(d)
    def test_many_entries(self):
        d=doc_for(zip_bytes({f'a/{i}':b'x' for i in range(513)}))
        with self.assertRaises(m.HandoffError): decode(d)
    def test_no_code_execution_on_decode(self):
        doc=doc_for(zip_bytes({'luau/core.luau':b'os.execute("bad")'}))
        self.assertIn(b'PK', decode(doc))
    def test_list_invalid(self):
        d=doc_for();d['ciphertext_b64']=['hi', 3]
        with self.assertRaises(m.HandoffError): decode(d)


class FileTests(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def test_new_file_success(self):
        p=self.root/'output.zip';m.write_new_file_only(p,b'new');self.assertEqual(p.read_bytes(),b'new')
    def test_existing_regular_unmodified(self):
        p=self.root/'output.zip';p.write_bytes(b'original')
        with self.assertRaises(FileExistsError): m.write_new_file_only(p,b'new')
        self.assertEqual(p.read_bytes(),b'original')
    def test_existing_symlink_not_followed(self):
        target=self.root/'target';target.write_bytes(b'original')
        p=self.root/'output.zip'
        try: p.symlink_to(target)
        except (OSError, NotImplementedError): self.skipTest('symlinks unavailable')
        with self.assertRaises((FileExistsError,OSError)): m.write_new_file_only(p,b'new')
        self.assertEqual(target.read_bytes(),b'original')
    def test_parent_symlink_rejected(self):
        p=self.root/'parent';p.mkdir();q=self.root/'alias'
        try:q.symlink_to(p,target_is_directory=True)
        except (OSError, NotImplementedError):self.skipTest('symlinks unavailable')
        with self.assertRaises(m.HandoffError):m.write_new_file_only(q/'out',b'new')
    def test_missing_parent_rejected(self):
        with self.assertRaises(m.HandoffError):m.write_new_file_only(self.root/'missing'/'out',b'new')
    def test_existing_output_before_restore_unchanged(self):
        env=self.root/'env.json';env.write_text(json.dumps(doc_for()))
        out=self.root/'out.zip';out.write_bytes(b'preserved')
        with self.assertRaises(FileExistsError):m.restore(env,out,SECRET,expected_zip_sha256=doc_for()['zip_sha256'],expected_work_id=WORK,expected_packet_id=PACKET)
        self.assertEqual(out.read_bytes(),b'preserved')
    def test_restore_new_digest(self):
        doc=doc_for();env=self.root/'env.json';env.write_text(json.dumps(doc))
        out=self.root/'out.zip'
        self.assertEqual(m.restore(env,out,SECRET,expected_zip_sha256=doc['zip_sha256'],expected_work_id=WORK,expected_packet_id=PACKET),doc['zip_sha256'])
        self.assertEqual(hashlib.sha256(out.read_bytes()).hexdigest(),doc['zip_sha256'])
    def test_json_duplicate_field(self):
        path=self.root/'env.json';path.write_text('{"x":1,"x":2}')
        with self.assertRaises(m.HandoffError):m._read_envelope(path)
    def test_envelope_oversize(self):
        path=self.root/'env.json';path.write_bytes(b' '* (m.MAX_ENVELOPE+1))
        with self.assertRaises(m.HandoffError):m._read_envelope(path)
    def test_json_input_symlink(self):
        orig=self.root/'orig.json';orig.write_text(json.dumps(doc_for())); alias=self.root/'alias.json'
        try:alias.symlink_to(orig)
        except (OSError,NotImplementedError):self.skipTest('symlinks unavailable')
        with self.assertRaises(m.HandoffError):m._read_envelope(alias)
    def test_fail_does_not_create_output(self):
        d=doc_for();p=self.root/'env.json';p.write_text(json.dumps(d))
        out=self.root/'out.zip'
        with self.assertRaises(m.HandoffError):m.restore(p,out,'bad',expected_zip_sha256=d['zip_sha256'],expected_work_id=WORK)
        self.assertFalse(out.exists())
    def test_race_exclusive_create(self):
        # A concurrent winner creating the output before our O_EXCL cannot be overwritten.
        out=self.root/'out.zip';out.write_bytes(b'winner')
        with self.assertRaises(FileExistsError):m.write_new_file_only(out,b'loser')
        self.assertEqual(out.read_bytes(),b'winner')

if __name__=='__main__':unittest.main()
