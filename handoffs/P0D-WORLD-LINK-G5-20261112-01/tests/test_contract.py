"""WF-G5 source-only safety/route/advertising contracts; not Roblox physics."""
import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
ROUTES=(ROOT/"src/WorldLinkRoutes.luau").read_text("utf-8")
SCENE=(ROOT/"src/WorldLinkScene.luau").read_text("utf-8")
BOOT=(ROOT/"src/WorldLinkDemo.server.luau").read_text("utf-8")
PROMO=json.loads((ROOT/"docs/WORLD_LINK_TACTIC_AND_PROMO.json").read_text("utf-8"))
EXPECTED={"SEA_BRIDGE","SEA_BUBBLE_A","SEA_BUBBLE_B","SKY_RAINBOW_A","SKY_RAINBOW_B"}

class Contract(unittest.TestCase):
    def test_scope(self):
        self.assertEqual(PROMO["game_id"],"TRAP_RAIDERS")
        self.assertEqual(PROMO["source_mode"],"ORIGINAL_DESIGN_AND_3D_SOURCE_ONLY")
        self.assertTrue(PROMO["zero_pay_advantage"])

    def test_five_kid_route_cards(self):
        self.assertEqual({r["id"] for r in PROMO["records"]},EXPECTED)
        self.assertEqual(len(PROMO["records"]),5)
        for record in PROMO["records"]:
            for key in ("child_action","role_item_tactic","counterplay",
                        "marketing_hook_7s","marketing_script_15s","H0","H1",
                        "failure_recovery","test_metric","status"):
                self.assertGreater(len(record[key]),5,(record["id"],key))
            self.assertEqual(record["status"],"SOURCE_ONLY_NOT_STUDIO_TESTED")

    def test_original_land_sea_sky_nodes(self):
        for term in ('LAND =','SEA_DOCK =','SEA_CASTLE =','SKY_CASTLE ='):
            self.assertIn(term,ROUTES)
        self.assertIn('Routes.reachable',ROUTES)
        self.assertIn('Routes.validate',ROUTES)

    def test_route_labels_source_match_card(self):
        for id in EXPECTED:
            self.assertIn('id="'+id+'"',ROUTES)
            self.assertIn(id,SCENE)
        self.assertEqual(len(re.findall(r'\{id="[A-Z_]+", from=',ROUTES)),5)

    def test_free_both_way_and_kid_cues(self):
        self.assertEqual(ROUTES.count('free=true'),5)
        self.assertEqual(ROUTES.count('direction="both"'),5)
        self.assertEqual(ROUTES.count('counterplay='),5)
        self.assertEqual(ROUTES.count('child_cue='),5)

    def test_two_sea_paths_and_two_sky_paths(self):
        for term in ("SEA_BRIDGE_FreePortWalk", "SEA_BUBBLE_A_DryRamp",
                     "SEA_BUBBLE_B_DryRamp","SKY_RAINBOW_A_Lower",
                     "SKY_RAINBOW_A_Upper","SKY_RAINBOW_B_Lower",
                     "SKY_RAINBOW_B_Upper"):
            self.assertIn(term,SCENE)

    def test_walkable_slope_bounds(self):
        self.assertIn('math.abs(dy/dx)<0.32',SCENE)
        self.assertIn('WF-G5 walk slope too steep',SCENE)
        self.assertIn('p.CanCollide=solid',SCENE)
        self.assertIn('p.Anchored=true',SCENE)

    def test_water_is_not_claimed_physics(self):
        self.assertIn("SEA_VisualWaterOnly",SCENE)
        self.assertIn("Enum.Material.Glass,false,0.79",SCENE)
        self.assertNotIn("Terrain:FillBlock",SCENE)
        self.assertNotIn("Enum.Material.Water",SCENE)

    def test_landing_and_spawn_path(self):
        self.assertIn('Instance.new("SpawnLocation")',SCENE)
        self.assertIn("start.Neutral=true",SCENE)
        self.assertIn('SEA_CASTLE_',SCENE)
        self.assertIn('SKY_CASTLE_',SCENE)

    def test_server_only_no_game_authority(self):
        for code in (SCENE,ROUTES,BOOT):
            for forbidden in ("OnServerEvent","RemoteEvent","DataStoreService",
                              "MarketplaceService","PublishAsync",
                              "workspace.Gravity =","SetNetworkOwner("):
                self.assertNotIn(forbidden,code)

    def test_demo_disabled_and_existing_s1_guard(self):
        self.assertIn("ENABLE_WORLD_G5_DEMO = false",BOOT)
        self.assertIn("if not ENABLE_WORLD_G5_DEMO then return end",BOOT)
        self.assertIn('"TRAP_RAIDERS_S1"',SCENE)
        self.assertIn('"NO_S1_MAP_OVERLAP"',SCENE)

    def test_missing_review_or_live_claim_rejected(self):
        self.assertIn("real S1 score",PROMO["not_implemented"])
        self.assertIn("sea swim physics",PROMO["not_implemented"])
        self.assertIn('WF_SourceMode","SOURCE_ONLY_NO_STUDIO_QA"',SCENE)
        self.assertIn("NOT_SET",SCENE)

    def test_negative_walking_role_restriction(self):
        def valid(text):
            return text.count('free=true')==5
        self.assertTrue(valid(ROUTES))
        self.assertFalse(valid(ROUTES.replace("free=true","free=false",1)))

    def test_negative_default_enable(self):
        def safe(text):
            return "ENABLE_WORLD_G5_DEMO = false" in text
        self.assertTrue(safe(BOOT))
        self.assertFalse(safe(BOOT.replace("ENABLE_WORLD_G5_DEMO = false",
                                          "ENABLE_WORLD_G5_DEMO = true")))

    def test_negative_collision_removal(self):
        def safe(text):
            return 'p.CanCollide=solid' in text
        self.assertTrue(safe(SCENE))
        self.assertFalse(safe(SCENE.replace('p.CanCollide=solid','p.CanCollide=false')))

if __name__=="__main__":
    unittest.main()
