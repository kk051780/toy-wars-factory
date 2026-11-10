import io
import json
import unittest
import zipfile
from tools.verify_packet import BadPacket, verify_bytes


def archive(items):
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
        for key,val in items:
            z.writestr(key,val)
    return stream.getvalue()


class ArchiveTest(unittest.TestCase):
    def setUp(self):
        self.manifest=json.dumps({'packet_id':'P0D-D14-CART-RAFT-VISUAL-20261110-02','entries':{}},sort_keys=True).encode()

    def check_bad(self, files):
        with self.assertRaises(BadPacket):verify_bytes(archive(files))

    def test_empty_rejected(self):
        with self.assertRaises(BadPacket):verify_bytes(b'')

    def test_corrupt_rejected(self):
        with self.assertRaises(BadPacket):verify_bytes(b'not-zip')

    def test_no_manifest_rejected(self):self.check_bad([('README.md',b'a')])
    def test_mismatch_manifest_rejected(self):self.check_bad([('README.md',b'a'),('BUILD_MANIFEST.json',self.manifest)])
    def test_traversal_rejected(self):self.check_bad([('../evil',b'x'),('BUILD_MANIFEST.json',self.manifest)])
    def test_absolute_rejected(self):self.check_bad([('/evil',b'x'),('BUILD_MANIFEST.json',self.manifest)])
    def test_backslash_rejected(self):self.check_bad([('a\\b',b'x'),('BUILD_MANIFEST.json',self.manifest)])
    def test_colon_rejected(self):self.check_bad([('C:evil',b'x'),('BUILD_MANIFEST.json',self.manifest)])
    def test_duplicate_rejected(self):self.check_bad([('A',b'x'),('a',b'x'),('BUILD_MANIFEST.json',self.manifest)])
    def test_duplicate_manifest_json_key(self):
        m=b'{"packet_id":"P0D-D14-CART-RAFT-VISUAL-20261110-02","packet_id":"evil","entries":{}}'
        self.check_bad([('BUILD_MANIFEST.json',m)])
    def test_wrong_packet(self):
        m=json.dumps({'packet_id':'WRONG','entries':{}}).encode()
        self.check_bad([('BUILD_MANIFEST.json',m)])
    def test_missing_sha(self):
        m=json.dumps({'packet_id':'P0D-D14-CART-RAFT-VISUAL-20261110-02','entries':{'A':{'bytes':1,'sha256':'x'}}}).encode()
        self.check_bad([('A',b'a'),('BUILD_MANIFEST.json',m)])
    def test_oversize_archive(self):
        with self.assertRaises(BadPacket):verify_bytes(b'A'*2_000_001)

    def test_oversize_single_file(self):
        self.check_bad([('BIG.bin',b'A'*512_001),('BUILD_MANIFEST.json',self.manifest)])

    def test_safe_good(self):
        import hashlib
        m=json.dumps({'packet_id':'P0D-D14-CART-RAFT-VISUAL-20261110-02',
                      'entries':{'A.txt':{'bytes':1,'sha256':hashlib.sha256(b'a').hexdigest()}}}).encode()
        self.assertEqual(verify_bytes(archive([('A.txt',b'a'),('BUILD_MANIFEST.json',m)]))['packet_id'],'P0D-D14-CART-RAFT-VISUAL-20261110-02')

if __name__=='__main__':unittest.main()
