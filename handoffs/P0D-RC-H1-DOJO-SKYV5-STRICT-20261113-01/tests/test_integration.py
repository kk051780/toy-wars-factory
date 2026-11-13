"""Independent on-source integration gate for H1 dojo+physical ground dock V5+strict V4 observer."""
import json,hashlib,subprocess,sys,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
UP=REPO/"handoffs/P0D-RC-B42V7-SKY-SOLO-DOJO-H1-20261113-01"
OLD=UP/"dist/P0D_B42_V7_SKYCASTLE_LATCH_AUDIT_DOJO_H1_PRIVATE"
NEW=ROOT/"dist/P0D_H1_DOJO_SKYV5_STRICT4_PRIVATE"
NEW_WORLD="7a90affd4eb7eebcdfba39d833a2875ff665d5cf"
NEW_AUDIT="ee96518a7eeaaaba98d2a8e2aff6dad780fae8c7"
OLD_WORLD="0a6360392f4384dc2f0ab1e9afc1d840d66a22b8"
OLD_AUDIT="b09e5fa2b3374cb88cad789b2c4966d4c777b3ef"

def blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def sources(root):
    return {p.relative_to(root/"src").as_posix():p.read_bytes()
            for p in (root/"src").rglob("*.luau")}

class H1AcceptedCrossAuthor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        x=subprocess.run([sys.executable,"-B",str(ROOT/"tools/assemble.py"),"--assemble"],
                         cwd=REPO,capture_output=True,text=True)
        assert x.returncode==0,"REBUILDER_FAIL\n"+x.stdout+"\n"+x.stderr
        cls.old=sources(OLD)
        cls.new=sources(NEW)
        cls.receipt=json.loads((NEW/"SOURCE_LOCK.json").read_text("utf8"))

    def test_45_real_original_scripts_and_only_two_new_file_bodies(self):
        self.assertEqual(len(self.old),45)
        self.assertEqual(len(self.new),45)
        self.assertEqual(set(self.old),set(self.new))
        changed=sorted(p for p in self.old if self.old[p]!=self.new[p])
        self.assertEqual(changed,
                         ["client/P0DStudioTrialAudit.client.luau",
                          "server/H1FunWorld.server.luau"])
        self.assertEqual(self.receipt["identical_to_previous"],43)
        self.assertEqual(self.receipt["total_scripts"],45)
        for p,x in self.receipt["blobs"].items():
            with self.subTest(p=p):self.assertEqual(blob(self.new[p]),x)

    def test_world_and_observer_author_immutable(self):
        self.assertEqual(blob(self.old["server/H1FunWorld.server.luau"]),OLD_WORLD)
        self.assertEqual(blob(self.old["client/P0DStudioTrialAudit.client.luau"]),OLD_AUDIT)
        self.assertEqual(blob(self.new["server/H1FunWorld.server.luau"]),NEW_WORLD)
        self.assertEqual(blob(self.new["client/P0DStudioTrialAudit.client.luau"]),NEW_AUDIT)
        self.assertEqual(self.new["server/H1FunWorld.server.luau"],
                         (ROOT/"src/H1FunWorld_SKYCASTLE_GROUNDDOCK_V5.server.luau").read_bytes())
        self.assertEqual(self.new["client/P0DStudioTrialAudit.client.luau"],
                         (ROOT/"src/P0DStudioTrialAudit_STRICT_V4.client.luau").read_bytes())

    def test_all_game_and_dojo_authority_sources_unchanged(self):
        for p in ("server/Game.server.luau","client/HUD.client.luau",
                  "server/DojoRules.luau","server/MusouHorde.luau",
                  "server/StudioSoloPreviewRules.luau",
                  "server/MapBuilder.luau","server/PersistentHatchStore.luau",
                  "server/First90GuideRules.luau","server/First90WaypointRules.luau"):
            with self.subTest(p=p):self.assertEqual(self.old[p],self.new[p])
        c=self.new["server/Game.server.luau"].decode("utf8")
        self.assertEqual(c.count('remote.OnServerEvent:Connect('),1)
        self.assertEqual(c.count('remote.Name = "TrapRaidersS1Remote"'),1)
        self.assertEqual(c.count('Dojo.tick('),1)
        self.assertEqual(c.count('Dojo.pveDamageMultiplier('),2)
        self.assertIn('H2Score.deposit(',c)
        self.assertIn('Evolution.nextEvolution(',c)

    def test_four_new_physically_solid_route_sources(self):
        c=self.new["server/H1FunWorld.server.luau"].decode("utf8")
        for name in ["SKY_GROUND_BOOT_RED","SKY_GROUND_BOOT_BLUE",
                     "SKY_SCORE_DOCK_RED","SKY_SCORE_DOCK_BLUE"]:
            self.assertEqual(c.count('path("'+name+'"'),1)
        self.assertIn('world:SetAttribute("GroundDocksPhysical",4)',c)
        self.assertIn('p.Anchored=true; p.CanCollide=solid',c)
        self.assertEqual(c.count('local world=Instance.new("Folder")'),1)
        self.assertEqual(c.count('local fort=box("FLOATING_SKY_ISLAND"'),1)

    def test_strict_same_egg_and_reset_based_actual_client(self):
        c=self.new["client/P0DStudioTrialAudit.client.luau"].decode("utf8")
        for keyword in ('qualifiesSkyScore(', 'invalidatesSkyRoute(',
                        'previousCarry==skyEgg','population==1',
                        'workspace:Raycast(', 'HumanoidRootPart',
                        'ROUTE_RESET','SCORE_NOT_QUALIFIED','SKY_WITH_EGG',
                        'SCORE_AFTER_SKY','if not RunService:IsStudio() then return end'):
            with self.subTest(keyword=keyword):self.assertIn(keyword,c)
        for forbidden in ('FireServer(', 'OnServerEvent:Connect(',
                          'Instance.new("RemoteEvent")','GetDataStore(', 'UpdateAsync('):
            self.assertNotIn(forbidden,c)
        self.assertEqual(c.count('remote.OnClientEvent:Connect('),1)
        self.assertEqual(c.count('Instance.new("ScreenGui")'),1)

    def test_one_live_game_remote_and_original_dojo(self):
        self.assertEqual(len([p for p in self.new if p.endswith(".server.luau")]),2)
        self.assertEqual(len([p for p in self.new if p.endswith(".client.luau")]),6)
        self.assertIn('Dojo.MAX_LEVEL = 5',
                      self.new["server/DojoRules.luau"].decode("utf8"))
        self.assertEqual(self.receipt["world_ground_docks"],4)
        self.assertTrue(self.receipt["original_dojo_beast_weapon"])
        self.assertTrue(self.receipt["original_studio_solo_latch"])
        self.assertFalse(self.receipt["six_skill_v4"])
        self.assertFalse(self.receipt["dojo_persistence"])
        self.assertFalse(self.receipt["paid"])
        self.assertFalse(self.receipt["published"])
        self.assertFalse(self.receipt["official_rc_adopted"])

    def test_rojo_explicit_mapping_includes_original_author_observer(self):
        project=json.loads((NEW/"default.project.json").read_text("utf8"))
        self.assertEqual(project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"],
                         "src/server")
        self.assertEqual(project["tree"]["StarterPlayer"]["StarterPlayerScripts"]["P0DStudioTrialAudit"]["$path"],
                         "src/client/P0DStudioTrialAudit.client.luau")

    def test_no_engine_truth_claim_in_receipt(self):
        for k in ("real_ground_walkability","strict_view_4of4_engine",
                  "owner_fun","studio_1client","studio_2client","android"):
            self.assertEqual(self.receipt[k],"NOT_TESTED")

if __name__=="__main__":
    unittest.main()
