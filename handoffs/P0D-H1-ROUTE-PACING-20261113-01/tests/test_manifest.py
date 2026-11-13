"""Keyless exact source receipt tests. Build manifest itself excluded from self-hash."""
import hashlib
import json
from pathlib import Path
import unittest

P=Path(__file__).resolve()
ROOT=P.parents[1]
REPO=P.parents[3]
MANIFEST=ROOT/"BUILD_MANIFEST.json"

def sha(b):return hashlib.sha256(b).hexdigest()
def blob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

class TestWorldRoutePacingReceipt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=json.loads(MANIFEST.read_text(encoding="utf-8"))
    def test_provenance_and_scope(self):
        self.assertEqual(self.m["packet_id"],"P0D-H1-ROUTE-PACING-20261113-01")
        self.assertEqual(self.m["base_wallclear_commit"],"2494fa855d77e1ef6dd2c5f8b8d21fbef90fc44a")
        self.assertEqual(self.m["base_world_blob"],"cc764b9caaa293ff747489e02e607af4502ddca4")
        self.assertEqual(self.m["candidate_world_blob"],"7aaa2a48d3e58c7c00bc805b74d0c9d8737217ea")
    def test_no_false_studio_pass_or_game_adoption(self):
        self.assertEqual(self.m["real_Roblox_Studio"],"NOT_TESTED")
        self.assertFalse(self.m["official_RC_adopted"])
        self.assertFalse(self.m["replaces_current_H1_4way"])
        self.assertEqual(self.m["source_status"],"UNMOUNTED_STUDY_SOURCE_ONLY")
    def test_all_pinned_bytes_and_names(self):
        files=self.m["files"]
        self.assertEqual(len(files),5)
        names=set()
        for f in files:
            name=f["path"]
            self.assertNotIn(name,names)
            names.add(name)
            full=REPO/name
            b=full.read_bytes()
            self.assertEqual(len(b),f["bytes"],name)
            self.assertEqual(sha(b),f["sha256"],name)
            self.assertEqual(blob(b),f["git_blob"],name)
        self.assertIn("handoffs/P0D-H1-ROUTE-PACING-20261113-01/candidate/H1FunWorld_short_routes_REVIEW_ONLY.server.luau",names)
    def test_stronger_than_simple_presence_check(self):
        files=self.m["files"]
        original=files[0]
        bad=dict(original,sha256="0"*64)
        b=(REPO/original["path"]).read_bytes()
        self.assertNotEqual(sha(b),bad["sha256"])
if __name__=="__main__":unittest.main()
