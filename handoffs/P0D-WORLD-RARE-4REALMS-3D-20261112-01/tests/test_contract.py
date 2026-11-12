"""Source-only contract checks; actual original Scene native test is a separate CI job."""
from pathlib import Path
import json,re,unittest
ROOT=Path(__file__).resolve().parents[1]
C=(ROOT/"src/RareRealmCatalog.luau").read_text("utf-8")
S=(ROOT/"src/RareRealmScene.luau").read_text("utf-8")
B=(ROOT/"src/RareRealmDemo.server.luau").read_text("utf-8")
P=(ROOT/"src/RareRealmCycle.luau").read_text("utf-8")
J=json.loads((ROOT/"docs/TacticsAndTrailers.json").read_text("utf-8"))
PROJ=json.loads((ROOT/"default.project.json").read_text("utf-8"))
class OriginalFourRealmContract(unittest.TestCase):
    def test_tactical_json_four_original_worlds(self):
        self.assertEqual({a["id"] for a in J["scenes"]},
            {"SPACE","CELESTIAL","EMBER","ECLIPSE"})
        self.assertEqual(len(J["scenes"]),4)
    def test_game_and_truth_guard(self):
        self.assertEqual(J["scope"],"SCENE_SOURCE_ONLY_S2PLUS")
        self.assertTrue(J["permanently_free_access"])
        for key in ("real_npc_ai_count","rare_drop_count","in_game_egg_system_count","real_zero_g_count"):
            self.assertEqual(J[key],0)
        self.assertEqual(J["hypothesis_controls"]["measurement"],"NOT_MEASURED")
    def test_each_realm_has_tactic_defender_child_video(self):
        for a in J["scenes"]:
            for key in ("mechanic","child","job","counter","npc","clip7","clip15","future"):
                self.assertGreater(len(a[key]),10,(a["id"],key))
    def test_eight_usable_routes(self):
        routes=["SPACE_STAR_BRIDGE","SPACE_CRATER_PATH","SKY_GOLD_RAMP",
                "SKY_PEARL_ROAD","EMBER_STONE_BRIDGE","EMBER_SHADOW_PATH",
                "ECLIPSE_SUN_PATH","ECLIPSE_MOON_PATH"]
        for a in routes:
            self.assertIn(a,C)
        self.assertEqual(C.count('forward = "'),4)
        self.assertEqual(C.count('side = "'),4)
        self.assertIn('if w.forward==w.side',C)
    def test_no_hidden_power_or_game_authority(self):
        for t in (C,S,B,P):
            for k in ("RemoteEvent","OnServerEvent","FireServer","MarketplaceService",
                      "DataStoreService","PublishAsync","workspace.Gravity =",
                      "Humanoid:TakeDamage","SetNetworkOwner("):
                self.assertNotIn(k,t)
    def test_demo_studio_opt_in(self):
        self.assertIn("ENABLE_FOUR_RARE_REALMS_DEMO = false",B)
        self.assertIn("if not ENABLE_FOUR_RARE_REALMS_DEMO then return end",B)
        self.assertIn("RunService:IsStudio()",B)
        self.assertIn('FindFirstChild("TRAP_RAIDERS_S1")',B)
    def test_rare_creatures_not_npc_rigs(self):
        self.assertIn('NO_AI_OR_DROP_ONLY_SCULPTURE',S)
        self.assertIn('_RARE_SCULPTURE_BODY',S)
        self.assertIn('_RARE_ONLY_SCULPTURE_NOTE',S)
        self.assertIn('NOT_INSTALLED_REQUIRE_WF13_SEPARATE_QA',S)
        self.assertNotIn('Instance.new("Humanoid")',S)
    def test_walkable_dual_road(self):
        self.assertIn('item:SetAttribute("FreeToAllJobs",true)',S)
        self.assertIn('item:SetAttribute("BackAndForth",true)',S)
        self.assertIn('assert(length>=60 and length<=200',S)
        self.assertIn('REALM_ROUTE_TOO_STEEP',S)
        self.assertIn('p.Anchored',S) if 'p.Anchored' in S else self.assertIn('item.Anchored=true',S)
    def test_ember_safe_visual(self):
        self.assertIn('DecorativeSafeNoDamage',S)
        self.assertIn('EMBER_GEAR_RELIC_DECORATIVE',S)
    def test_eclipse_only_noncolliding_color(self):
        self.assertIn('sun.Transparency=',B)
        self.assertIn('moon.Transparency=',B)
        self.assertIn('ColorCycleAffectsCollision',S)
        self.assertIn('Cycle.PERIOD_SECONDS = 30',P)
    def test_no_global_lighting_and_single_map(self):
        self.assertIn('REALM_DUPLICATE_DENIED',S)
        self.assertIn('REALM_NEVER_OVERLAP_OFFICIAL_S1',S)
        for t in (S,B):
            self.assertNotIn('game:GetService("Lighting")',t)
            self.assertNotIn('Lighting.ClockTime',t)
    def test_project_declares_exact_scripts(self):
        tree=PROJ["tree"]["ServerScriptService"]
        self.assertEqual({k for k in tree if k!="$className"},
            {"RareRealmDemo","RareRealmCatalog","RareRealmCycle","RareRealmScene"})
    def test_negative_autoenable(self):
        def guard(s):return "ENABLE_FOUR_RARE_REALMS_DEMO = false" in s
        self.assertTrue(guard(B))
        self.assertFalse(guard(B.replace("ENABLE_FOUR_RARE_REALMS_DEMO = false","ENABLE_FOUR_RARE_REALMS_DEMO = true")))
    def test_negative_free_access(self):
        def guard(s):return 'item:SetAttribute("FreeToAllJobs",true)' in s
        self.assertTrue(guard(S))
        self.assertFalse(guard(S.replace('item:SetAttribute("FreeToAllJobs",true)',
                                        'item:SetAttribute("FreeToAllJobs",false)')))
    def test_bounded_part_budget(self):
        self.assertIn("Catalog.MAX_SCENE_PARTS = 220",C)
        self.assertIn('assert(count<=Catalog.MAX_SCENE_PARTS',S)
if __name__=="__main__":unittest.main()
