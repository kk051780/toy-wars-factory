"""H1 pure read-only advisor owner trial source lock: no new Game/Remote/Store writes."""
from pathlib import Path
import hashlib,json,subprocess,sys,unittest

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
BASE=REPO/"handoffs/P0D-RC-H1-DOJO-SKYV5-STRICT-20261113-01/dist/P0D_H1_DOJO_SKYV5_STRICT4_PRIVATE"
NEW=ROOT/"dist/P0D_H1_SKYV5_DOJO_RESULT7_STUDIO_PRIVATE"
ADVISOR="d212dae56b328d48bfed5dafa742caff9afe82c7"

def blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def sources(where):
    return {p.relative_to(where/"src").as_posix():p.read_bytes()
            for p in (where/"src").rglob("*.luau")}

class H1ResultAdvisor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r=subprocess.run([sys.executable,"-B",str(ROOT/"tools/assemble.py"),"--assemble"],
                         cwd=REPO,text=True,capture_output=True)
        assert r.returncode==0,"P0D_H1_REASSEMBLY_FAIL\n"+r.stdout+"\n"+r.stderr
        cls.old=sources(BASE)
        cls.new=sources(NEW)
        cls.lock=json.loads((NEW/"SOURCE_LOCK.json").read_text("utf8"))

    def test_actual_45_original_byte_exact_two_advisory_sources(self):
        self.assertEqual(len(self.old),45)
        self.assertEqual(len(self.new),47)
        for p in self.old:
            with self.subTest(p=p):self.assertEqual(self.old[p],self.new[p])
        self.assertEqual(sorted(set(self.new)-set(self.old)),
                         ["client/ResultNextStep.client.luau",
                          "shared/NextStepAdvisor.luau"])
        self.assertEqual(self.lock["original_45_unchanged"],45)
        self.assertEqual(self.lock["total_scripts"],47)
        for p,digest in self.lock["blobs"].items():
            with self.subTest(blob=p):self.assertEqual(blob(self.new[p]),digest)

    def test_original_advisor_source_exact_author_no_modification(self):
        s=self.new["shared/NextStepAdvisor.luau"]
        self.assertEqual(blob(s),ADVISOR)
        self.assertEqual(s,(ROOT/"src/NextStepAdvisor.luau").read_bytes())
        self.assertIn("function Advisor.build(",s.decode("utf8"))
        self.assertIn("availableSkills",s.decode("utf8"))
        self.assertIn("autoDismissSeconds = 7",s.decode("utf8"))
        self.assertIn("readOnly = true",s.decode("utf8"))

    def test_new_client_studio_only_passive_and_autohide(self):
        c=self.new["client/ResultNextStep.client.luau"].decode("utf8")
        self.assertIn('if not RunService:IsStudio() then return end',c)
        self.assertEqual(c.count('remote.OnClientEvent:Connect('),1)
        self.assertEqual(c.count('task.delay(7,'),1)
        self.assertEqual(c.count('close.MouseButton1Click:Connect('),1)
        self.assertIn('if phase ~= "RESULTS" then',c)
        self.assertIn('shownSerial == serial',c)
        self.assertIn('ticket == showTicket',c)
        self.assertIn('box.Active = false',c)
        self.assertIn('canHatch=false',c)
        self.assertIn('availableSkills={"beast", "weapon"}',c)

    def test_honest_snapshots_only_not_fake_kos_rescues_hatch(self):
        c=self.new["client/ResultNextStep.client.luau"].decode("utf8")
        self.assertIn('msg.scores[msg.team]',c)
        self.assertIn('チーム得点',c)
        self.assertIn('msg.evoCanUpgrade == true',c)
        self.assertIn('type(snapshot.dojo)',c)
        self.assertIn('dojo.friendBonus',c)
        self.assertNotIn('musouLastKOs',c)
        self.assertNotIn('neutralDefeats=',c)
        self.assertNotIn('rescues=',c)
        self.assertNotIn('canHatch=true',c)
        self.assertFalse(self.lock["individual_KOs_not_claimed"] is False)
        self.assertTrue(self.lock["hatch_readiness_not_claimed"])

    def test_one_original_game_remotes_stores_and_scene(self):
        for path in ("server/Game.server.luau",
                     "server/H1FunWorld.server.luau",
                     "server/MusouHorde.luau",
                     "server/DojoRules.luau",
                     "server/StudioSoloPreviewRules.luau",
                     "server/PersistentHatchStore.luau",
                     "client/HUD.client.luau",
                     "client/P0DStudioTrialAudit.client.luau"):
            self.assertEqual(self.old[path],self.new[path])
        g=self.new["server/Game.server.luau"].decode("utf8")
        self.assertEqual(g.count('remote.OnServerEvent:Connect('),1)
        self.assertEqual(g.count('remote.Name = "TrapRaidersS1Remote"'),1)
        self.assertEqual(g.count('Dojo.tick('),1)
        self.assertEqual(g.count('H2Score.deposit('),1)
        self.assertEqual(len([p for p in self.new if p.endswith(".server.luau")]),2)
        self.assertEqual(len([p for p in self.new if p.endswith(".client.luau")]),7)

    def test_rojo_both_new_local_and_shared_module_mapped(self):
        cfg=json.loads((NEW/"default.project.json").read_text("utf8"))
        self.assertEqual(cfg["tree"]["ReplicatedStorage"]["TrapRaidersShared"]["$path"],
                         "src/shared")
        scripts=cfg["tree"]["StarterPlayer"]["StarterPlayerScripts"]
        self.assertEqual(scripts["ResultNextStep"]["$path"],
                         "src/client/ResultNextStep.client.luau")
        self.assertEqual(scripts["P0DStudioTrialAudit"]["$path"],
                         "src/client/P0DStudioTrialAudit.client.luau")

    def test_no_user_privilege_or_gameplay_authoring(self):
        for p in ("shared/NextStepAdvisor.luau","client/ResultNextStep.client.luau"):
            s=self.new[p].decode("utf8")
            for forbid in ("FireServer(", "FireClient(", "OnServerEvent:Connect(",
                           "DataStoreService","GetDataStore(", "UpdateAsync(",
                           "MarketplaceService", "PromptProductPurchase("):
                with self.subTest(file=p,token=forbid):
                    self.assertNotIn(forbid,s)
        self.assertFalse(self.lock["published"])
        self.assertFalse(self.lock["paid"])
        self.assertFalse(self.lock["official_rc_adopted"])
        self.assertFalse(self.lock["six_skill_v4"])
        self.assertFalse(self.lock["dojo_persistence"])

    def test_engine_not_fabricated(self):
        for k in ("studio_1client","studio_2client","android","owner_fun"):
            self.assertEqual(self.lock[k],"NOT_TESTED")

if __name__=="__main__":
    unittest.main()
