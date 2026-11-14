"""P0D-018 PREP source/authority smoke checks (NOT native/Studio/RC QA)."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parent/"features"/"capture"
SRC=(ROOT/"CapturePolicy.luau").read_text("utf8")
NATIVE=(ROOT/"CaptureNative.luau").read_text("utf8")
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
if __name__=="__main__":
    unittest.main()
