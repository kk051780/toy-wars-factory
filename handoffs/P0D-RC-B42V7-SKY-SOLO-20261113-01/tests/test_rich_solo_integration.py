"""Genuine rich-game source integration, exact original Game 1 / Remote 1, 41 unchanged."""
from pathlib import Path
import hashlib, json, subprocess, sys, unittest

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
DIST=ROOT/"dist/EGG_RAID_RUMBLE_B42_V7_SKYCASTLE_SOLO_UNPUBLISHED"
UP=REPO/"handoffs/P0D-B42-V7-SKYCASTLE-20261113-01/dist/EGG_RAID_RUMBLE_FIRST90_V7_SKYCASTLE_PRIVATE"
GAME="21b866e801a53ba7ebd66132ae55fe28608750d6"
HORDE="fc6ca46d36bb81ce5f1cd3d327ad2ab714b4be38"
SKY="0a6360392f4384dc2f0ab1e9afc1d840d66a22b8"
SOLO="de0e0df12346de2b4e7b607c74eddaaac693dc99"
AUDIT="b09e5fa2b3374cb88cad789b2c4966d4c777b3ef"

def blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def files(root):
    return {p.relative_to(root/"src").as_posix():p.read_bytes()
        for p in (root/"src").rglob("*.luau")}

class RichSoloIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        proc=subprocess.run([sys.executable,"-B",str(ROOT/"tools/assemble.py"),"--assemble"],
                            cwd=REPO,capture_output=True,text=True)
        assert proc.returncode==0, "RICH_BUILDER_FAILED\n"+proc.stdout+"\n"+proc.stderr
        cls.old=files(UP)
        cls.new=files(DIST)
        cls.receipt=json.loads((DIST/"SOURCE_LOCK.json").read_text("utf8"))

    def test_script_counts_and_blobs(self):
        self.assertEqual(len(self.old),42)
        self.assertEqual(len(self.new),44)
        self.assertEqual(self.receipt["script_total"],44)
        self.assertEqual(self.receipt["unchanged_original_h1_scripts"],41)
        for p,expected in self.receipt["blobs"].items():
            with self.subTest(p=p):self.assertEqual(blob(self.new[p]),expected)

    def test_frozen_original_author_game_world_horde(self):
        self.assertEqual(blob(self.old["server/Game.server.luau"]),GAME)
        self.assertEqual(blob(self.old["server/H1FunWorld.server.luau"]),SKY)
        self.assertEqual(blob(self.old["server/MusouHorde.luau"]),HORDE)

    def test_only_original_game_hunk_plus_single_new_module(self):
        unchanged=[p for p in self.old if self.old[p]==self.new[p]]
        self.assertEqual(len(unchanged),41)
        self.assertEqual(sorted(set(self.new)-set(self.old)),
                         ["client/P0DStudioTrialAudit.client.luau",
                          "server/StudioSoloPreviewRules.luau"])
        self.assertEqual(sorted(p for p in self.old if p not in unchanged),
                         ["server/Game.server.luau"])

    def test_private_runservice_only(self):
        g=self.new["server/Game.server.luau"].decode("utf8")
        s=self.new["server/StudioSoloPreviewRules.luau"]
        self.assertEqual(blob(s),SOLO)
        self.assertEqual(g.count('local RunService = game:GetService("RunService")'),1)
        self.assertIn('StudioSolo.canStart(RunService:IsStudio(), count',g)
        self.assertIn('studioSoloRoundStarted = StudioSolo.isSoloRound(',g)
        self.assertIn('StudioSolo.emptyWinner(RunService:IsStudio(),',g)
        self.assertIn('studioSoloRoundStarted, count',g)
        self.assertTrue(self.receipt["solo_latched_at_round_start"])
        self.assertTrue(self.receipt["studio_2client_exit_still_ends"])
        self.assertIn('isStudio == true and count == 1',s.decode("utf8"))
        self.assertIn('red > 0 and blue > 0',s.decode("utf8"))
        self.assertFalse(self.receipt["published_min_players_unchanged"] is False)

    def test_single_game_remote_and_legacy_rules_intact(self):
        g=self.new["server/Game.server.luau"].decode("utf8")
        self.assertEqual(g.count('remote.OnServerEvent:Connect('),1)
        self.assertEqual(g.count('remote.Name = "TrapRaidersS1Remote"'),1)
        self.assertEqual(len([p for p in self.new if p.endswith("/Game.server.luau")]),1)
        self.assertEqual(len([p for p in self.new if p.endswith(".server.luau")]),2)
        self.assertEqual(len([p for p in self.new if p.endswith(".client.luau")]),6)
        self.assertIn('match.eggOwners',g)
        self.assertIn('First90WaypointRules',g)
        self.assertIn('horde:tick(',g)
        self.assertIn('Evolution.nextEvolution(',g)
        self.assertIn('Power.beginAwaken(',g)
        self.assertIn('EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio()',g)

    def test_no_other_source_writer_or_paid_rules(self):
        no=[p for p in self.new if p != "server/Game.server.luau" and self.old.get(p)!=self.new[p]]
        self.assertEqual(no,["client/P0DStudioTrialAudit.client.luau",
                             "server/StudioSoloPreviewRules.luau"])
        self.assertNotIn('Instance.new("RemoteEvent")',
                         self.new["server/StudioSoloPreviewRules.luau"].decode("utf8"))
        self.assertFalse(self.receipt["official_rc_adopted"])
        self.assertFalse(self.receipt["published"])
        self.assertEqual(self.receipt["owner_fun"],"NOT_TESTED")

    def test_project_maintains_one_original_game_and_world(self):
        p=json.loads((DIST/"default.project.json").read_text("utf8"))
        self.assertEqual(p["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"],
                         "src/server")
        self.assertEqual(len([z for z in self.new if z=="server/H1FunWorld.server.luau"]),1)
        self.assertEqual(len([z for z in self.new if z=="server/StudioSoloPreviewRules.luau"]),1)
        self.assertEqual(len([z for z in self.new if z=="client/P0DStudioTrialAudit.client.luau"]),1)
        self.assertEqual(
            p["tree"]["StarterPlayer"]["StarterPlayerScripts"]["P0DStudioTrialAudit"]["$path"],
            "src/client/P0DStudioTrialAudit.client.luau")

    def test_author_exact_readonly_client_diagnostics(self):
        script=self.new["client/P0DStudioTrialAudit.client.luau"]
        self.assertEqual(blob(script),AUDIT)
        self.assertEqual(self.receipt["audit_original_author_blob"],AUDIT)
        self.assertTrue(self.receipt["audit_readonly_studio_only"])
        self.assertEqual(
            script,
            (ROOT/"src/P0DStudioTrialAudit.client.luau").read_bytes()
        )
        text=script.decode("utf8")
        self.assertIn('if not RunService:IsStudio() then return end',text)
        self.assertIn('[P0D_STUDIO_FUN_CHECK]',text)
        for marker in ("PHASE", "FIRST90", "EGG_CARRIED",
                       "SCORE_CONFIRMED", "RESULT", "SKY_SOURCE", "BLOCKED",
                       "SKY_WITH_EGG", "SCORE_AFTER_SKY"):
            with self.subTest(marker=marker):
                self.assertIn('"'+marker+'"',text)
        for forbidden in ('FireServer(', 'OnServerEvent:Connect(',
                          'Instance.new(', 'MarketplaceService', 'DataStoreService'):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden,text)
        self.assertEqual(text.count('remote.OnClientEvent:Connect('),1)
        self.assertIn('if n>=110 then return end',text)
        self.assertIn('4/4',text)
        self.assertIn('HumanoidRootPart',text)
        self.assertIn('hum.FloorMaterial~=Enum.Material.Air',text)
        self.assertIn('activeSerial==lastSerial',text)
        self.assertIn('skyWithEggSerial==serial and activeSerial==serial',text)
        self.assertIn('continuity NOT_PROVEN',text)
        self.assertEqual(self.receipt["audit_stage_checklist"],
                         ["ACTIVE","EGG_CARRIED","SKY_WITH_EGG","SCORE_AFTER_SKY"])
        self.assertEqual(text.count('Instance.new("ScreenGui")'),1)
        self.assertIn('if not RunService:IsStudio() then return end',text)

    def test_old_hud_and_world_remain_byte_identical(self):
        for path in ["client/HUD.client.luau","server/H1FunWorld.server.luau",
                     "server/MusouHorde.luau","server/First90GuideRules.luau",
                     "server/First90WaypointRules.luau"]:
            with self.subTest(path=path):
                self.assertEqual(self.new[path],self.old[path])


if __name__=="__main__":unittest.main()
