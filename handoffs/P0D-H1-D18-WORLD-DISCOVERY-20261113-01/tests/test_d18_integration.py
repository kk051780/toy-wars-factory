"""Source tests only: true physical Studio proximity/render/performance untested."""
import json,pathlib,subprocess,sys,unittest
R=pathlib.Path(__file__).resolve().parents[1]
SRC=R/"dist/TRAP_RAIDERS_H1_D18_WORLD_DISCOVERY_STUDIO_ONLY"
def verify_client(s):
    checks=["RunService:IsStudio()","MAX_NEARBY_MODELS=2","CanCollide=false",
      "CanTouch=false","CanQuery=false","KeyboardKeyCode=Enum.KeyCode.E",
      "ProximityPrompt","local discovered={}","discoveredCount+=1",
      "x=-58,z=30","x=58,z=30","x=-58,z=-35","x=58,z=-35",
      "TRCA-BE-108","TRCA-TR-090","model:Destroy()"]
    for c in checks:
        if c not in s:raise AssertionError("D18_CLIENT_CONTRACT_MISSING:"+c)
    import re
    if not re.search(r"MAX_NEARBY_MODELS=2(?=\s|$)",s):
        raise AssertionError("D18_INSTANCE_CAP_CHANGED")
    for field in ("CanCollide=false","CanTouch=false","CanQuery=false"):
        if s.count(field)!=2:
            raise AssertionError("D18_BOTH_PART_AND_PROMPT_ANCHOR_MUST_BE_NONCOLLIDING:"+field)
    for forbidden in ["FireServer","RemoteEvent","DataStoreService","MarketplaceService",
      "TakeDamage","GetAsync","SetAsync","ProcessReceipt","Humanoid.WalkSpeed"]:
        if forbidden in s:raise AssertionError("D18_CLIENT_AUTHORITY_VIOLATION:"+forbidden)
    return True
class D18H1RealSourceIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=(SRC/"src/client/D18PairRouteDiscover.client.luau").read_text(encoding="utf-8")
        cls.receipt=json.loads((SRC/"SOURCE_RECEIPT.json").read_text(encoding="utf-8"))
    def test_new_landmark_source_contract(self):
        self.assertTrue(verify_client(self.s))
    def test_game_30_sources_exact(self):
        self.assertEqual(len(self.receipt["original_game_sources_sha1"]),30)
        self.assertEqual(self.receipt["total_luau_sources"],32)
    def test_original_official_game_not_replaced(self):
        txt=(SRC/"src/server/Game.server.luau").read_text(encoding="utf-8")
        self.assertEqual(txt.count('remote.Name = "TrapRaidersS1Remote"'),1)
        self.assertIn('elseif data.action == "WIND_BURST"',txt)
    def test_six_paths_unchanged_in_existing_game(self):
        path=(SRC/"src/server/H1FunWorld.server.luau").read_text(encoding="utf-8")
        for name in ["SKY_RAMP_RED","SKY_WALKWAY","SKY_RAMP_BLUE",
                     "SEA_ENTRY_RED","SEA_LOW_CAUSEWAY","SEA_ENTRY_BLUE"]:
            self.assertIn(name,path)
    def test_existing_mascot_and_joy_retained(self):
        paths=[p.name for p in (SRC/"src/client").glob("*.luau")]
        for name in ["D18MascotGuide.client.luau","EggJoy.client.luau",
                     "HUD.client.luau","D18Batch10Catalog.luau",
                     "D18PairRouteDiscover.client.luau"]:
            self.assertIn(name,paths)
    def test_ten_hostile_variants_rejected(self):
        cases=[
          ("Studio guard removed","RunService:IsStudio()","RunService:IsRunning()"),
          ("collision allowed","CanCollide=false","CanCollide=true"),
          ("touch allowed","CanTouch=false","CanTouch=true"),
          ("query allowed","CanQuery=false","CanQuery=true"),
          ("too many","MAX_NEARBY_MODELS=2","MAX_NEARBY_MODELS=200"),
          ("no discovery prompt","ProximityPrompt","FakePrompt"),
          ("no mobile E prompt","KeyboardKeyCode=Enum.KeyCode.E","KeyboardKeyCode=Enum.KeyCode.Unknown"),
          ("non symmetric blue","x=58,z=30","x=63,z=30"),
          ("wrong original asset","TRCA-TR-090","TRCA-TR-089"),
          ("no model cleanup","model:Destroy()","print(m)"),
        ]
        for label,needle,replace in cases:
            self.assertIn(needle,self.s)
            with self.subTest(label=label),self.assertRaises(AssertionError):
                verify_client(self.s.replace(needle,replace,1))
    def test_two_exact_original_assets_only(self):
        self.assertEqual(self.receipt["new_d18_visual_models"],["TRCA-BE-108","TRCA-TR-090"])
        self.assertEqual(self.receipt["mirrored_local_landmarks"],4)
        self.assertEqual(self.receipt["max_nearby_models_per_client"],2)
    def test_no_score_change_or_fake_earning(self):
        for k in ["game_server_mutated","gameplay_scoring_changed",
                  "reward_inventory_monetization","multiegg_feature_integrated",
                  "official_rc_adopted","published"]:
            self.assertFalse(self.receipt[k],k)
if __name__=="__main__": unittest.main()
