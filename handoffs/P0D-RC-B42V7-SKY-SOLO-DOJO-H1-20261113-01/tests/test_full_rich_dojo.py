"""Independent 45 source integrator QA for original authors' H1 dojo and prior 44 rich preview."""
from pathlib import Path
import hashlib,json,subprocess,sys,unittest

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
OLD=REPO/"handoffs/P0D-RC-B42V7-SKY-SOLO-20261113-01/dist/EGG_RAID_RUMBLE_B42_V7_SKYCASTLE_SOLO_UNPUBLISHED"
NEW=ROOT/"dist/P0D_B42_V7_SKYCASTLE_LATCH_AUDIT_DOJO_H1_PRIVATE"
ORIGINAL_DOJO="120bac439c979310c9ddeb2fcf2ffa002b6d1add"
SOLO="de0e0df12346de2b4e7b607c74eddaaac693dc99"
AUDIT="b09e5fa2b3374cb88cad789b2c4966d4c777b3ef"

def blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def source(root):
    return {p.relative_to(root/"src").as_posix():p.read_bytes()
            for p in (root/"src").rglob("*.luau")}

class RichDojoH1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=subprocess.run([sys.executable,"-B",str(ROOT/"tools/assemble.py"),"--assemble"],
                         cwd=REPO,capture_output=True,text=True)
        assert p.returncode==0,"FULL_BUILD_FAIL\n"+p.stdout+"\n"+p.stderr
        cls.old=source(OLD)
        cls.new=source(NEW)
        cls.receipt=json.loads((NEW/"SOURCE_LOCK.json").read_text("utf8"))

    def test_frozen_source_exact_45_and_unchanged_42(self):
        self.assertEqual(len(self.old),44)
        self.assertEqual(len(self.new),45)
        self.assertEqual(self.receipt["all_scripts"],45)
        self.assertEqual(self.receipt["base_scripts_unchanged"],42)
        changes=sorted(path for path in self.old if self.old[path]!=self.new[path])
        self.assertEqual(changes,["client/HUD.client.luau","server/Game.server.luau"])
        self.assertEqual(sorted(set(self.new)-set(self.old)),["server/DojoRules.luau"])
        for key,expected in self.receipt["blobs"].items():
            with self.subTest(key=key):
                self.assertEqual(blob(self.new[key]),expected)

    def test_original_author_dojo_and_studio_policy_exact(self):
        self.assertEqual(blob(self.new["server/DojoRules.luau"]),ORIGINAL_DOJO)
        self.assertEqual(blob(self.new["server/StudioSoloPreviewRules.luau"]),SOLO)
        self.assertEqual(blob(self.new["client/P0DStudioTrialAudit.client.luau"]),AUDIT)
        self.assertEqual(self.old["server/StudioSoloPreviewRules.luau"],
                         self.new["server/StudioSoloPreviewRules.luau"])
        self.assertEqual(self.old["client/P0DStudioTrialAudit.client.luau"],
                         self.new["client/P0DStudioTrialAudit.client.luau"])

    def test_single_game_and_authority_remain_unchanged(self):
        game=self.new["server/Game.server.luau"].decode("utf8")
        self.assertEqual(game.count('remote.OnServerEvent:Connect('),1)
        self.assertEqual(game.count('remote.Name = "TrapRaidersS1Remote"'),1)
        self.assertEqual(game.count('local function tickRound()'),1)
        self.assertEqual(game.count('local function resetRound()'),1)
        self.assertEqual(game.count("Dojo.tick("),1)
        self.assertEqual(game.count("Dojo.view("),1)
        self.assertEqual(game.count("Dojo.pveDamageMultiplier("),2)
        self.assertIn('studioSoloRoundStarted = StudioSolo.isSoloRound(',game)
        self.assertIn('studioSoloRoundStarted, count',game)
        self.assertIn('First90WaypointRules',game)
        self.assertIn('horde:tick(',game)
        self.assertIn('Evolution.nextEvolution(',game)
        self.assertIn('H2Score.deposit(',game)

    def test_original_gameplay_bytes_preserved_except_one_server_and_hud(self):
        for path in ["server/MusouHorde.luau","server/H1FunWorld.server.luau",
                     "server/First90WaypointRules.luau","server/First90GuideRules.luau",
                     "server/PersistentHatchStore.luau","client/P0DStudioTrialAudit.client.luau"]:
            with self.subTest(path=path):
                self.assertEqual(self.old[path],self.new[path])

    def test_server_authored_training_no_paid_or_saved(self):
        game=self.new["server/Game.server.luau"].decode("utf8")
        dojo=self.new["server/DojoRules.luau"].decode("utf8")
        self.assertIn('player:IsFriendsWith(other.UserId)',game)
        self.assertIn('dojoLastTick[player]=now',game)
        self.assertIn('if RunService:IsStudio() then',game)
        self.assertIn('and carry[player]==nil',game)
        self.assertIn('if dt>0 and alive and root and pads',game)
        self.assertIn('dojo=if RunService:IsStudio() then Dojo.view(',game)
        self.assertIn('PVE_BONUS_PER_LEVEL = 0.05',dojo)
        self.assertIn('Dojo.MAX_LEVEL = 5',dojo)
        self.assertIn('Dojo.MAX_SECONDS_PER_SKILL = 180',dojo)
        self.assertNotIn('DataStore',dojo)
        self.assertNotIn('MarketplaceService',dojo)
        self.assertNotIn('FireServer(',dojo)
        self.assertFalse(self.receipt["dojo_persistence"])
        self.assertFalse(self.receipt["paid"])
        self.assertFalse(self.receipt["six_disciplines_v4"])

    def test_mirrored_beast_weapon_dojo_and_hud_original_author_patch(self):
        game=self.new["server/Game.server.luau"].decode("utf8")
        hud=self.new["client/HUD.client.luau"].decode("utf8")
        self.assertIn('for _,side in ipairs({"RED","BLUE"})',game)
        self.assertIn('for _,kind in ipairs({"BEAST","WEAPON"})',game)
        self.assertIn('PRIVATE_AUTO_DOJO_',game)
        self.assertIn('dojoBadge.Visible=valid',hud)
        self.assertIn('training.friendBonus==true',hud)
        self.assertEqual(hud.count('remote:FireServer('),3)
        self.assertEqual(self.receipt["mirrored_pad_count"],4)
        self.assertEqual(self.receipt["pvp_bonus"],1)
        self.assertEqual(self.receipt["max_session_level"],5)

    def test_diagnostic_4_step_no_fake_fun_pass(self):
        audit=self.new["client/P0DStudioTrialAudit.client.luau"].decode("utf8")
        self.assertIn('if not RunService:IsStudio() then return end',audit)
        self.assertIn('SKY_WITH_EGG',audit)
        self.assertIn('SCORE_AFTER_SKY',audit)
        self.assertIn('continuity NOT_PROVEN',audit)
        self.assertNotIn('FireServer(',audit)
        self.assertEqual(audit.count('remote.OnClientEvent:Connect('),1)
        self.assertEqual(self.receipt["owner_fun"],"NOT_TESTED")
        self.assertFalse(self.receipt["official_rc_adopted"])

    def test_rojo_mappings_all_present(self):
        config=json.loads((NEW/"default.project.json").read_text("utf8"))
        self.assertEqual(config["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"],
                         "src/server")
        scripts=config["tree"]["StarterPlayer"]["StarterPlayerScripts"]
        self.assertEqual(scripts["P0DStudioTrialAudit"]["$path"],
                         "src/client/P0DStudioTrialAudit.client.luau")
        self.assertEqual(len([p for p in self.new if p.endswith(".server.luau")]),2)
        self.assertEqual(len([p for p in self.new if p.endswith(".client.luau")]),6)

if __name__=="__main__":
    unittest.main()
