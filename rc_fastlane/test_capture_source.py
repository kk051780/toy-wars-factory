"""P0D-018 PREP source/authority and pinned-blob regression checks."""
from pathlib import Path
import unittest, json, hashlib
ROOT=Path(__file__).resolve().parent/"features"/"capture"
SRC=(ROOT/"CapturePolicy.luau").read_text("utf8")
NATIVE=(ROOT/"CaptureNative.luau").read_text("utf8")
MANIFEST=json.loads((ROOT/"PREP_SOURCE_LOCK.json").read_text("utf8"))
def gitblob(b):
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\x00"+b).hexdigest()
class SourceChecks(unittest.TestCase):
    def test_policy(self):
        self.assertIn("function Capture.begin(",SRC)
        self.assertIn("function Capture.rescue(",SRC)
    def test_caps(self):
        self.assertIn("Capture.DURATION=4",SRC)
        self.assertIn("Capture.COOLDOWN=18",SRC)
        self.assertIn("Capture.RESCUE_RANGE=7",SRC)
    def test_server_gates(self):
        self.assertIn("s.serverLineOfSight~=true",SRC)
        self.assertIn("s.serverDistance>Capture.RANGE",SRC)
        self.assertIn('s.phase~="ACTIVE"',SRC)
    def test_lifecycle(self):
        for fn in ("status","release","clearRound","forget"):
            self.assertIn("function Capture."+fn+"(",SRC)
    def test_no_second_authority(self):
        for forbidden in ("RemoteEvent","OnServerEvent","FireServer(",
                          "DataStore","TakeDamage(","Humanoid","WalkSpeed =",
                          "MarketplaceService","PromptProductPurchase("):
            self.assertNotIn(forbidden,SRC)
    def test_native_fixture(self):
        self.assertEqual(NATIVE.count("check(")-1,18)
        self.assertIn("assert(tests==18",NATIVE)
    def test_lock_identifies_unique_id(self):
        self.assertEqual(MANIFEST["feature_id"],"P0D-018")
        self.assertFalse(MANIFEST["game_wired"])
        self.assertEqual(MANIFEST["phase"],"SOURCE_ONLY_NOT_READY")
    def test_exact_source_pins(self):
        self.assertEqual(gitblob(SRC.encode("utf8")),MANIFEST["module_blob"])
        self.assertEqual(gitblob(NATIVE.encode("utf8")),MANIFEST["native_blob"])
    def test_exact_build_generator(self):
        gen=(ROOT/"build_capture_native.py").read_text("utf8")
        self.assertIn('assert git_blob(policy)==manifest["module_blob"]',gen)
        self.assertIn('assert git_blob(native)==manifest["native_blob"]',gen)
    def test_single_team_limit(self):
        self.assertIn("c.ownerTeam==s.attackerTeam",SRC)
        self.assertIn('return false,"TEAM_LIMIT"',SRC)
if __name__=="__main__":
    unittest.main()
