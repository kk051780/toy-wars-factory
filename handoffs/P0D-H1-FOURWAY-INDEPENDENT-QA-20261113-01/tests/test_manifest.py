"""Exact delivered independent QA source SHA / immutable original #255 author lock."""
import hashlib
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve()
ROOT=HERE.parents[1]
REPO=HERE.parents[3]
MANIFEST=ROOT/"BUILD_MANIFEST.json"
def sha(b):return hashlib.sha256(b).hexdigest()
def blob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

class TestH1IndependentQABuildReceipt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(MANIFEST.read_text(encoding="utf-8"))
    def test_origin_stays_original_fixed_h1(self):
        self.assertEqual(self.data["audited_h1_immutable_commit"],"1498c2d344ede2d9da6c2bfdd025ebc1a15ec48b")
        self.assertEqual(self.data["packet_id"],"P0D-H1-FOURWAY-INDEPENDENT-QA-20261113-01")
    def test_scope_never_claims_official_studio(self):
        for v in ("official_RC_writer","source_changes_original_game","owner_studio_2client_pass","published"):
            self.assertIs(self.data[v],False,v)
        self.assertEqual(self.data["native_luau_CI_execution"],"NOT_VERIFIED_AT_CREATION")
    def test_five_source_files_exact_byte_and_two_hashes(self):
        receipts=self.data["files"]
        self.assertEqual(len(receipts),5)
        self.assertEqual(len({f["path"] for f in receipts}),5)
        for f in receipts:
            content=(REPO/f["path"]).read_bytes()
            self.assertEqual(len(content),f["size"],f["path"])
            self.assertEqual(sha(content),f["sha256"],f["path"])
            self.assertEqual(blob(content),f["git_blob"],f["path"])
    def test_prevent_nonoriginal_source_entry(self):
        self.assertEqual(self.data["expected_game_source_count"],28)
        self.assertEqual(self.data["original_wind_blob"],"7d5706774b874759e7ab994dc0654c3ae9a46502")
        self.assertEqual(self.data["original_trap_blob"],"feabd705e4cfa5483d440e506277080f226343ef")
        self.assertEqual(self.data["original_d18_guide_rule_blob"],"328b8a4d70261e633f163a5e166822a29d7eb1ba")
if __name__=="__main__":
    unittest.main()
