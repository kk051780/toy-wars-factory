"""Pure source guardrails. These cannot prove Roblox Studio physics, HUD scaling or fun."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
CORE=ROOT/"src"/"ProgressionRules.luau"
VIEW=ROOT/"src"/"LevelJourneyView.luau"
SERVER=ROOT/"demo"/"LevelJourneyPreview.server.luau"
CLIENT=ROOT/"demo"/"LevelJourneyHUD.client.luau"
PROJECT=ROOT/"default.project.json"
def blob_sha(raw):
    return hashlib.sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest()

class LevelJourneyStatic(unittest.TestCase):
    def test_immutable_exact_orig_281_blob(self):
        self.assertEqual(blob_sha(CORE.read_bytes()),
          "a72830b039a46ca02d02f6aab7d6a4805bec8860")

    def test_wiring(self):
        p=json.loads(PROJECT.read_text())
        t=p["tree"]
        mapping=[
          t["ServerScriptService"]["ProgressionRules"]["$path"],
          t["ServerScriptService"]["LevelJourneyView"]["$path"],
          t["ServerScriptService"]["LevelJourneyPreview"]["$path"],
          t["StarterPlayer"]["StarterPlayerScripts"]["LevelJourneyHUD"]["$path"]
        ]
        self.assertEqual(len(set(mapping)),4)
        self.assertTrue(all((ROOT/x).exists() for x in mapping))

    def test_both_demo_scripts_studio_only(self):
        for f in (SERVER,CLIENT):
            self.assertIn("if not RunService:IsStudio() then return end",f.read_text())

    def test_no_store_purchase_or_live_core(self):
        for term in ("MarketplaceService","ProcessReceipt","DataStoreService","UpdateAsync",
                     "SetAsync","TakeDamage","TrapRaidersS1Remote","PublishAsync"):
            self.assertNotIn(term,SERVER.read_text()+CLIENT.read_text())

    def test_remote_only_server_outbound(self):
        self.assertNotIn(":FireServer(",CLIENT.read_text())
        self.assertIn("signal:FireClient(player,view)",SERVER.read_text())

    def test_view_does_not_award_xp(self):
        s=VIEW.read_text()
        for token in ("P.commit(","DataStoreService","p.owned[","MarketplaceService"):
            self.assertNotIn(token,s)
        self.assertIn("PREVIEW_ONLY",s)

    def test_policy_only_source_origin(self):
        s=SERVER.read_text()
        self.assertIn('P=require(script.Parent:WaitForChild("ProgressionRules"))',s)
        self.assertIn('View=require(script.Parent:WaitForChild("LevelJourneyView")).new(P)',s)
        self.assertIn('P.recordEvent(round,',s)
        self.assertIn('P.commit(record,round,"LOSS",60,true)',s)

    def test_duration_explicit_preview(self):
        s=SERVER.read_text()
        self.assertIn("virtual duration: DEMO ONLY",s)
        self.assertIn("not tied to any real egg actions",s)

    def test_old_and_new_milestones(self):
        s=VIEW.read_text()
        for step in (2,5,10,20,30,50):
            self.assertIn(str(step),s)
        self.assertIn('local MASTERY_STEPS={3,6,10}',s)

    def test_mobile_progress_and_celebration(self):
        s=CLIENT.read_text()
        self.assertIn("TweenService:Create(fill",s)
        self.assertIn('UDim2.fromScale(.025,.045)',s)
        self.assertIn('announce(text,lastRevision)',s)
        self.assertIn('if payload.playerLeveled then',s)

    def test_revision_rejects_stale(self):
        s=CLIENT.read_text()
        self.assertIn("payload.revision<=lastRevision",s)

    def test_no_stats_increases(self):
        s=VIEW.read_text()
        self.assertIn("gameplayStatsIncreased=false",s)
        self.assertIn("requiresPaidPurchase=false",s)

    def test_not_a_real_reward_claim(self):
        self.assertIn("NOT_GRANTED_BY_THIS_MODULE",VIEW.read_text())
        self.assertIn("実アカウントには保存されません",CLIENT.read_text())

    def test_single_action_server_loop_only(self):
        s=SERVER.read_text()
        self.assertIn('local actions={"DEPOSIT","DEFEND","PICKUP","EQUIP_USE","ESCORT","PICKUP"}',s)
        self.assertNotIn("signal.OnServerEvent",s)

if __name__=="__main__":
    unittest.main(verbosity=2)
