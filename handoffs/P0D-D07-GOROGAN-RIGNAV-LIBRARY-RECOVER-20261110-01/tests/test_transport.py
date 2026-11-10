import io,unittest,zipfile,json,hashlib,base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from tools.seal_handoff import seal,check_zip_bytes
from tools.verify_packet import verify_bytes

PACKET='P0D-D07-GOROGAN-RIG-NAV-DAMAGE-20261110-03'
def mini(entries):
    mem=io.BytesIO()
    with zipfile.ZipFile(mem,'w',zipfile.ZIP_DEFLATED) as z:
        for k,v in entries:z.writestr(k,v)
    return mem.getvalue()
def valid():
    content=b'TEST'
    manifest={'schema_version':1,'classification':'REFERENCE_ONLY','packet_id':PACKET,
       'files':{'a.txt':{'sha256':hashlib.sha256(content).hexdigest(),'size_bytes':len(content)}}}
    return mini([('a.txt',content),('BUILD_MANIFEST.json',json.dumps(manifest).encode())])
class TransportTests(unittest.TestCase):
    def setUp(self):self.blob=valid()
    def test_manifest_ok(self):self.assertTrue(verify_bytes(self.blob)['ok'])
    def test_packet_id(self):self.assertEqual(verify_bytes(self.blob)['packet_id'],PACKET)
    def test_zip_sha(self):self.assertEqual(verify_bytes(self.blob)['zip_sha256'],hashlib.sha256(self.blob).hexdigest())
    def test_zip_slip(self):
        with self.assertRaises(ValueError):check_zip_bytes(mini([('../evil',b'x')]))
    def test_absolute(self):
        with self.assertRaises(ValueError):check_zip_bytes(mini([('/private',b'x')]))
    def test_windows_drive(self):
        with self.assertRaises(ValueError):check_zip_bytes(mini([('C:shadow',b'x')]))
    def test_duplicate(self):
        with self.assertRaises(ValueError):check_zip_bytes(mini([('one',b'1'),('one',b'2')]))
    def test_case_collision(self):
        with self.assertRaises(ValueError):check_zip_bytes(mini([('Test',b'1'),('test',b'2')]))
    def test_corrupt_zip(self):
        with self.assertRaises(ValueError):verify_bytes(b'not a zip')
    def test_missing_manifest(self):
        with self.assertRaises(ValueError):verify_bytes(mini([('a.txt',b'a')]))
    def test_mismatch(self):
        with self.assertRaises(ValueError):verify_bytes(mini([('a.txt',b'FAKE'),('BUILD_MANIFEST.json',zipfile.ZipFile(io.BytesIO(self.blob)).read('BUILD_MANIFEST.json'))]))
    def test_seal_restore(self):
        key=b'k'*32;nonce=b'n'*12
        doc,secret=seal(self.blob,'TRAP_RAIDERS','p0d-siege-v19',PACKET,key,nonce)
        a=base64.b64decode(doc['aad_b64']);ct=base64.b64decode(''.join(doc['ciphertext_b64']))
        self.assertEqual(AESGCM(key).decrypt(nonce,ct,a),self.blob)
        self.assertEqual(len(base64.urlsafe_b64decode(secret+'='*((-len(secret))%4))),32)
    def test_wrong_key(self):
        doc,_=seal(self.blob,'TRAP_RAIDERS','p0d-siege-v19',PACKET,b'k'*32,b'n'*12)
        with self.assertRaises(Exception):AESGCM(b'q'*32).decrypt(b'n'*12,base64.b64decode(''.join(doc['ciphertext_b64'])),base64.b64decode(doc['aad_b64']))
    def test_modified_cipher(self):
        doc,_=seal(self.blob,'TRAP_RAIDERS','p0d-siege-v19',PACKET,b'k'*32,b'n'*12)
        raw=bytearray(base64.b64decode(''.join(doc['ciphertext_b64'])));raw[10]^=2
        with self.assertRaises(Exception):AESGCM(b'k'*32).decrypt(b'n'*12,bytes(raw),base64.b64decode(doc['aad_b64']))
    def test_modified_aad(self):
        doc,_=seal(self.blob,'TRAP_RAIDERS','p0d-siege-v19',PACKET,b'k'*32,b'n'*12)
        with self.assertRaises(Exception):AESGCM(b'k'*32).decrypt(b'n'*12,base64.b64decode(''.join(doc['ciphertext_b64'])),b'wrong')
    def test_invalid_key(self):
        with self.assertRaises(ValueError):seal(self.blob,'TRAP_RAIDERS','p0d-siege-v19',PACKET,b'k',b'n'*12)
    def test_invalid_id(self):
        with self.assertRaises(ValueError):seal(self.blob,'TRAP RAIDERS','p0d-siege-v19',PACKET,b'k'*32,b'n'*12)
