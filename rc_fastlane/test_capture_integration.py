"""Capture original Game integration path: static author preflight, not Studio test."""
import unittest
from pathlib import Path
SRC=(Path(__file__).resolve().parent/"apply_capture.py").read_text("utf8")
class TestCaptureIntegration(unittest.TestCase):
    def test_off_no_mutation(self):
        self.assertIn('if not enabled:\n        print("P0D018_CAPTURE_OFF',SRC)
    def test_expects_exact66_to67(self):
        self.assertIn("assert len(original)==66",SRC)
        self.assertIn("assert len(new)==67",SRC)
    def test_old_net_preserved(self):
        self.assertIn('elseif data.action == "NET_THROW" then applyNet(player,data)',SRC)
    def test_one_game_remote(self):
        self.assertIn("txt.count('remote.OnServerEvent:Connect(')==1",SRC)
    def test_server_target_los(self):
        self.assertIn("workspace:Raycast(root.Position,delta,params)",SRC)
    def test_trapper_only_skill(self):
        self.assertIn('if job=="TRAPPER" then tryTrapperCapture(player,root,team,now) end',SRC)
    def test_existing_speed_record(self):
        self.assertIn('slowed[nearest]={hum=nearestHum',SRC)
        self.assertIn("restoreSlow(nearest)",SRC)
    def test_close_lifecycle(self):
        for marker in ("Capture.clearRound()", "Capture.forget(player)",
                       "Capture.release(player)", "CharacterAdded:Connect",
                       "PlayerRemoving:Connect"):
            self.assertIn(marker,SRC)
    def test_native_mobile_rescue(self):
        self.assertIn('Instance.new("ProximityPrompt")',SRC)
        self.assertIn('prompt.ActionText="救出"',SRC)
    def test_other_trap_cannot_override_capture(self):
        self.assertIn('slowed[player].kind~="P0D_CAPTURE"',SRC)
    def test_wind_and_flag_off_restore(self):
        self.assertIn("stopWind(nearest)",SRC)
        self.assertIn('captureGate.Value~=true',SRC)
    def test_no_extra_heartbeat_or_paid(self):
        for forbidden in ("RunService.Heartbeat","task.spawn(function()",
                          "MarketplaceService","PromptProductPurchase"):
            self.assertNotIn(forbidden,SRC)
if __name__=="__main__":unittest.main()
