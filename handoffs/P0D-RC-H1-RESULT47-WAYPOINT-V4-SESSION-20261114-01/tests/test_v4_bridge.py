import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
DIST=ROOT/"dist/P0D_RICH47_WAYPOINT_V4_6SKILL_SESSION_PRIVATE"
BASE=REPO/"handoffs/P0D-RC-H1-SKYV5-DOJO-RESULT-20261113-01/dist/P0D_H1_SKYV5_DOJO_RESULT7_STUDIO_PRIVATE"

def git_blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def source_map(base):
    return {p.relative_to(base/"src").as_posix():p.read_bytes() for p in (base/"src").rglob("*.luau")}

class TestV4Rich51Bridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sys import path
        path.insert(0,str(ROOT/"tools"))
        from assemble import build
        if not DIST.exists():
            build()
        cls.before=source_map(BASE)
        cls.after=source_map(DIST)
        cls.receipt=json.loads((DIST/"SOURCE_LOCK.json").read_text("utf8"))

    def test_exact_original_47(self):
        self.assertEqual(len(self.before),47)
        self.assertEqual(set(self.before)-set(self.after),set())
        self.assertTrue(all(self.before[x]==self.after[x] for x in self.before))

    def test_studio_waypoint_and_original_result_advisor_are_preserved(self):
        client=self.after["client/ResultNextStep.client.luau"].decode()
        self.assertIn('pointToInstalledPad(',client)
        self.assertIn('expected = "PRIVATE_AUTO_DOJO_"..team.."_"..skill',client)
        self.assertIn('task.delay(20, function()',client)
        self.assertIn('if phase == "ACTIVE" and marker then clearTrainingMarker() end',client)
        self.assertTrue(self.receipt["previous_h1_waypoint_preserved"])
        self.assertEqual(self.receipt["v4_six_skills_physically_mirrored_total"],12)
        self.assertEqual(
            git_blob(self.after["client/ResultNextStep.client.luau"]),
            "03898fa5d84096f2209e4afacef6e50a96682196")

    def test_new_adapter_has_only_eight_extra_preview_pads_and_twelve_total(self):
        c=self.after["server/V4TrainingBridge.server.luau"].decode()
        self.assertIn('folder:SetAttribute("NewPadsCount",8)',c)
        self.assertIn('for _,side in ipairs({"RED","BLUE"})',c)
        self.assertIn('for skill,display in pairs(labels) do',c)
        self.assertIn('BEAST={56,-15}, WEAPON={56,15}',c)
        self.assertIn('NoCombatBuff',c)
        self.assertIn('NoSavedXP',c)
        self.assertFalse(self.receipt["v4_persistent_xp"])
        self.assertFalse(self.receipt["v4_paid_chooser"])

    def test_only_four_additions(self):
        self.assertEqual(len(self.after),51)
        self.assertEqual(set(self.after)-set(self.before),{
            "server/FocusTrainingScheduler.luau",
            "server/SessionSixSkillXPPreview.luau",
            "server/V4TrainingBridge.server.luau",
            "client/V4TrialOverlay.client.luau",
        })

    def test_exact_v4_author_sources(self):
        self.assertEqual(git_blob(self.after["server/FocusTrainingScheduler.luau"]),"a00caf954aacfca03c92a75b0165c1bafd4de8fd")
        self.assertEqual(git_blob(self.after["server/SessionSixSkillXPPreview.luau"]),"ceb8f4f6caca37954cb3d61ef3e1756368b966e0")

    def test_no_second_game_or_server_remote(self):
        game=self.after["server/Game.server.luau"].decode()
        self.assertEqual(game.count('remote.OnServerEvent:Connect('),1)
        self.assertEqual(game.count('remote.Name = "TrapRaidersS1Remote"'),1)
        self.assertEqual(sum(x.endswith("/Game.server.luau") for x in self.after),1)
        self.assertEqual(sum(x.endswith(".server.luau") for x in self.after),3)

    def test_no_original_combat_dojo_store_patch(self):
        for path in ("server/Game.server.luau","server/DojoRules.luau",
                     "server/PersistentHatchStore.luau",
                     "server/H1FunWorld.server.luau",
                     "client/HUD.client.luau",
                     "client/ResultNextStep.client.luau"):
            self.assertEqual(self.before[path],self.after[path],path)

    def test_no_paid_no_durable_authority(self):
        for p in set(self.after)-set(self.before):
            s=self.after[p].decode()
            for bad in ("GetDataStore(","UpdateAsync(","FireServer(","OnServerEvent:Connect(",
                        "MarketplaceService","PromptProductPurchase("):
                self.assertNotIn(bad,s,p)
        server=self.after["server/V4TrainingBridge.server.luau"].decode()
        self.assertIn('if not RunService:IsStudio() then return end',server)
        self.assertIn('NoSavedXP',server)
        self.assertIn('NoCombatBuff',server)

    def test_original_models_used_in_adapter(self):
        server=self.after["server/V4TrainingBridge.server.luau"].decode()
        self.assertIn('Scheduler.settle(',server)
        self.assertIn('Model.apply(',server)
        self.assertIn('Scheduler.selectSkill(',server)
        self.assertIn('player:IsFriendsWith(other.UserId)',server)

    def test_symmetric_all_six_pads(self):
        server=self.after["server/V4TrainingBridge.server.luau"].decode()
        self.assertIn('{"RED","BLUE"}',server)
        self.assertIn('NewPadsCount",8',server)
        for s in ("BEAST","MAGIC","WEAPON","ZOMBIE","VEHICLE","BUILDING"):
            self.assertIn(s,server)
        self.assertIn('skill or ""',server)

    def test_ui_discloses_trial_and_is_hideable(self):
        ui=self.after["client/V4TrialOverlay.client.luau"].decode()
        self.assertIn('保存なし / 対戦強化なし / 課金なし',ui)
        self.assertIn('MouseButton1Click:Connect',ui)
        self.assertIn('if not RunService:IsStudio() then return end',ui)

    def test_receipt_and_config_fail_closed(self):
        v=self.receipt
        self.assertEqual(v["original_47_byte_identical"],47)
        self.assertEqual(v["total_scripts"],51)
        for key in ("official_rc_adopted","v4_persistent_xp","v4_daily_quota_persistent",
                    "v4_combat_buffs","v4_paid_chooser","published"):
            self.assertIs(v[key],False,key)
        self.assertEqual(v["studio_2client"],"NOT_TESTED")
        self.assertEqual(v["blobs"],{p:git_blob(raw) for p,raw in self.after.items()})
        cfg=json.loads((DIST/"default.project.json").read_text("utf8"))
        self.assertEqual(cfg["tree"]["StarterPlayer"]["StarterPlayerScripts"]["V4TrialOverlay"]["$path"],"src/client/V4TrialOverlay.client.luau")

if __name__=="__main__":
    unittest.main()
