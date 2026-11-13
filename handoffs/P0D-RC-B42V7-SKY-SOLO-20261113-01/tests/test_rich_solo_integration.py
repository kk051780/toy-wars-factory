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
SOLO="22e7e22e8837dbf44c57fdfb30efd480457022fb"

def blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def files(root):
    return {p.relative_to(root/"src").as_posix():p.read_bytes()
        for p in (root/"src").rglob("*.luau")}

class RichSoloIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable,"-B",str(ROOT/"tools/assemble.py"),"--assemble"],
                       cwd=REPO,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        cls.old=files(UP)
        cls.new=files(DIST)
        cls.receipt=json.loads((DIST/"SOURCE_LOCK.json").read_text("utf8"))

    def test_script_counts_and_blobs(self):
        self.assertEqual(len(self.old),42)
        self.assertEqual(len(self.new),43)
        self.assertEqual(self.receipt["script_total"],43)
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
                         ["server/StudioSoloPreviewRules.luau"])
        self.assertEqual(sorted(p for p in self.old if p not in unchanged),
                         ["server/Game.server.luau"])

    def test_private_runservice_only(self):
        g=self.new["server/Game.server.luau"].decode("utf8")
        s=self.new["server/StudioSoloPreviewRules.luau"]
        self.assertEqual(blob(s),SOLO)
        self.assertEqual(g.count('local RunService = game:GetService("RunService")'),1)
        self.assertIn('StudioSolo.canStart(RunService:IsStudio(), count',g)
        self.assertIn('StudioSolo.emptyWinner(RunService:IsStudio(), count',g)
        self.assertIn('isStudio == true and count == 1',s.decode("utf8"))
        self.assertIn('red > 0 and blue > 0',s.decode("utf8"))
        self.assertFalse(self.receipt["published_min_players_unchanged"] is False)

    def test_single_game_remote_and_legacy_rules_intact(self):
        g=self.new["server/Game.server.luau"].decode("utf8")
        self.assertEqual(g.count('remote.OnServerEvent:Connect('),1)
        self.assertEqual(g.count('remote.Name = "TrapRaidersS1Remote"'),1)
        self.assertEqual(len([p for p in self.new if p.endswith("/Game.server.luau")]),1)
        self.assertEqual(len([p for p in self.new if p.endswith(".server.luau")]),2)
        self.assertEqual(len([p for p in self.new if p.endswith(".client.luau")]),5)
        self.assertIn('match.eggOwners',g)
        self.assertIn('First90WaypointRules',g)
        self.assertIn('horde:tick(',g)
        self.assertIn('Evolution.nextEvolution(',g)
        self.assertIn('Power.beginAwaken(',g)
        self.assertIn('EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio()',g)

    def test_no_other_source_writer_or_paid_rules(self):
        no=[p for p in self.new if p != "server/Game.server.luau" and self.old.get(p)!=self.new[p]]
        self.assertEqual(no,["server/StudioSoloPreviewRules.luau"])
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

if __name__=="__main__":unittest.main()
