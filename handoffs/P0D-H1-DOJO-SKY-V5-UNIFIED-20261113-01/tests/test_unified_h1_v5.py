"""Source-only H1 integration regression. Real Studio remains NOT_TESTED."""
import hashlib, json, math, pathlib, re, subprocess, sys, unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
BASE = REPO/"handoffs/P0D-RC-B42V7-SKY-SOLO-DOJO-H1-20261113-01/dist/P0D_B42_V7_SKYCASTLE_LATCH_AUDIT_DOJO_H1_PRIVATE"
NEW = ROOT/"dist/P0D_B42_V7_SOLO_AUDIT_DOJO_SKY_GROUNDDOCK_V5_PRIVATE"

def sources(path):
    return {p.relative_to(path/"src").as_posix():p.read_bytes()
            for p in (path/"src").rglob("*.luau")}
def blob(content):
    return hashlib.sha1(b"blob "+str(len(content)).encode()+b"\0"+content).hexdigest()

class OneWorldH1V5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        result=subprocess.run([sys.executable,"-B",str(ROOT/"tools/assemble.py"),"--assemble"],
                              cwd=REPO,capture_output=True,text=True)
        if result.returncode:
            raise AssertionError("FAILED ASSEMBLY:\n"+result.stdout+"\n"+result.stderr)
        cls.old=sources(BASE)
        cls.new=sources(NEW)
        cls.lock=json.loads((NEW/"SOURCE_LOCK.json").read_text("utf8"))

    def test_one_exact_v5_author_blob(self):
        self.assertEqual(blob(self.new["server/H1FunWorld.server.luau"]),
                         "7a90affd4eb7eebcdfba39d833a2875ff665d5cf")
        self.assertEqual(blob(self.old["server/H1FunWorld.server.luau"]),
                         "0a6360392f4384dc2f0ab1e9afc1d840d66a22b8")

    def test_full_source_45_and_only_one_diff(self):
        self.assertEqual(len(self.new),45)
        self.assertEqual(set(self.new),set(self.old))
        changed={k for k in self.new if self.old[k]!=self.new[k]}
        self.assertEqual(changed,{"server/H1FunWorld.server.luau"})
        self.assertEqual(self.lock["scripts_unchanged"],44)
        for p,data in self.new.items():
            with self.subTest(path=p):
                self.assertEqual(blob(data),self.lock["source_blobs"][p])

    def test_authority_and_scoring_unchanged(self):
        for key in ("server/Game.server.luau","client/HUD.client.luau",
                    "server/PersistentHatchStore.luau","server/MusouHorde.luau",
                    "server/DojoRules.luau","server/StudioSoloPreviewRules.luau",
                    "client/P0DStudioTrialAudit.client.luau"):
            with self.subTest(path=key):
                self.assertEqual(self.new[key],self.old[key])
        game=self.new["server/Game.server.luau"].decode("utf8")
        self.assertEqual(game.count("remote.OnServerEvent:Connect("),1)
        self.assertEqual(game.count('remote.Name = "TrapRaidersS1Remote"'),1)
        self.assertEqual(game.count("Dojo.tick("),1)
        self.assertFalse(self.lock["official_rc_adopted"])

    def test_four_real_solid_docks_and_symmetry(self):
        world=self.new["server/H1FunWorld.server.luau"].decode("utf8")
        pairs=[
          ("SKY_GROUND_BOOT_RED","SKY_GROUND_BOOT_BLUE"),
          ("SKY_SCORE_DOCK_RED","SKY_SCORE_DOCK_BLUE")]
        for left,right in pairs:
            self.assertEqual(world.count('path("'+left+'"'),1)
            self.assertEqual(world.count('path("'+right+'"'),1)
        self.assertIn('world:SetAttribute("GroundDocksPhysical",4)',world)
        self.assertIn("p.Anchored=true; p.CanCollide=solid",world)
        self.assertIn("p.CanQuery=solid",world)
        self.assertIn('if not RunService:IsStudio() then',world)

    def test_gradient_and_ground_contact_conservative(self):
        world=self.new["server/H1FunWorld.server.luau"].decode("utf8")
        pattern=re.compile(r'path\("(SKY_GROUND_BOOT_(?:RED|BLUE)|SKY_SCORE_DOCK_(?:RED|BLUE))",Vector3.new\(([-0-9,]+)\),Vector3.new\(([-0-9,]+)\),')
        m=pattern.findall(world)
        self.assertEqual(len(m),4)
        for name,p,q in m:
            a=[float(x) for x in p.split(",")]
            b=[float(x) for x in q.split(",")]
            horizontal=math.hypot(b[0]-a[0],b[2]-a[2])
            self.assertLessEqual(abs(b[1]-a[1])/horizontal,.135,name)
            self.assertEqual(min(a[1],b[1]),-2,name)
            self.assertEqual(max(a[1],b[1]),0,name)
        self.assertNotIn("MarketplaceService",world)
        self.assertNotIn("DataStoreService",world)

    def test_project_maps_existing_game_and_audit(self):
        cfg=json.loads((NEW/"default.project.json").read_text("utf8"))
        self.assertEqual(cfg["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"],"src/server")
        self.assertEqual(cfg["tree"]["StarterPlayer"]["StarterPlayerScripts"]["P0DStudioTrialAudit"]["$path"],
                         "src/client/P0DStudioTrialAudit.client.luau")
        self.assertEqual(sum(k.endswith(".server.luau") for k in self.new),2)
        self.assertEqual(sum(k.endswith(".client.luau") for k in self.new),6)

if __name__=="__main__":
    unittest.main()
