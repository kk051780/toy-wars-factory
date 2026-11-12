"""Only source, not claims of real Roblox physics. Native source is exercised by CI separately."""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
POLICY=(ROOT/"src/RareEncounterPolicy.luau").read_text("utf-8")
MODELS=(ROOT/"src/RareEncounterModels.luau").read_text("utf-8")
DEMO=(ROOT/"src/RareEncounterPreview.server.luau").read_text("utf-8")
DOC=json.loads((ROOT/"docs/DiscoveryAndPromos.json").read_text("utf-8"))
PROJECT=json.loads((ROOT/"default.project.json").read_text("utf-8"))

class SourceContracts(unittest.TestCase):
    def test_unique_four_worlds_and_clues(self):
        self.assertEqual({x["id"] for x in DOC["creatures"]},
                         {"SPACE","CELESTIAL","EMBER","ECLIPSE"})
        self.assertEqual(len(DOC["creatures"]),4)
        for x in DOC["creatures"]:
            for field in ("name","visible_behavior","child_one_action",
                          "class_item_tactic_hypothesis","defender_counterplay",
                          "promo_7s","promo_15s"):
                self.assertGreater(len(x[field]),6,(x["id"],field))

    def test_truthful_no_reward_no_canon(self):
        self.assertFalse(DOC["rewards"])
        self.assertFalse(DOC["d18_canonical_collection"])
        self.assertFalse(DOC["actual_gameplay_implemented"])
        self.assertEqual(DOC["observed_true_spawn_rates"],"NOT_MEASURED")

    def test_exact_previous_world_reuse(self):
        tree=PROJECT["tree"]["ServerScriptService"]
        self.assertEqual({k for k in tree if k!="$className"},
            {"RareRealmCatalog","RareRealmScene",
             "RareEncounterPolicy","RareEncounterModels","RareEncounterPreview"})
        self.assertIn("../P0D-WORLD-RARE-4REALMS-3D",tree["RareRealmCatalog"]["$path"])
        self.assertIn("../P0D-WORLD-RARE-4REALMS-3D",tree["RareRealmScene"]["$path"])

    def test_disabled_studio_only(self):
        self.assertIn("ENABLE_RARE_NEUTRAL_STUDIO_PREVIEW = false",DEMO)
        self.assertIn("if not ENABLE_RARE_NEUTRAL_STUDIO_PREVIEW then return end",DEMO)
        self.assertIn("RunService:IsStudio()",DEMO)
        self.assertIn('FindFirstChild("TRAP_RAIDERS_S1")',DEMO)

    def test_no_remote_p2w_rewards(self):
        for text in (POLICY,MODELS,DEMO):
            for forbidden in ("RemoteEvent","OnServerEvent","FireServer",
                    "DataStoreService","MarketplaceService","TeleportService",
                    "SetNetworkOwner(", "workspace.Gravity =","Humanoid:TakeDamage",
                    "PublishAsync","awardCoins","giveLoot","DropChanceForRobux"):
                self.assertNotIn(forbidden,text)

    def test_source_probability_bounded_and_never_guaranteed(self):
        self.assertIn("P.SPAWN_CHANCE = 0.12",POLICY)
        self.assertIn("P.MAX_ACTIVE = 1",POLICY)
        self.assertIn("P.WINDOW_SECONDS = 45",POLICY)
        self.assertIn("P.LIFETIME_SECONDS = 28",POLICY)
        self.assertIn("P.TELEGRAPH_SECONDS = 2",POLICY)
        self.assertIn("draw>=P.SPAWN_CHANCE",POLICY)
        self.assertIn("window<=s.lastWindow",POLICY)

    def test_finite_rejects_corrupt_client_like_values(self):
        self.assertIn("n==n",POLICY)
        self.assertIn("n>-math.huge and n<math.huge",POLICY)
        self.assertIn("draw>=1",POLICY)
        self.assertIn('kind="RNG_INVALID"',POLICY)

    def test_actual_models_move_not_just_sculptures(self):
        self.assertIn("Instance.new(\"Model\")",MODELS)
        self.assertIn("encounter.model:PivotTo(CFrame.new(destination))",MODELS)
        self.assertIn("model.PrimaryPart=body",MODELS)
        self.assertIn("Models.update",DEMO)

    def test_physics_safe_parts_and_bounded_count(self):
        self.assertIn("pieces<=12",MODELS)
        self.assertIn("p.CanCollide=false",MODELS)
        self.assertIn("p.CanTouch=false",MODELS)
        self.assertIn("p.CanQuery=false",MODELS)
        self.assertIn("p.Anchored=true",MODELS)

    def test_child_cue_and_real_prompt(self):
        self.assertIn('Instance.new("ProximityPrompt")',MODELS)
        self.assertIn('prompt.ActionText="みつけた！"',MODELS)
        self.assertIn("prompt.HoldDuration=0.4",MODELS)
        self.assertIn("prompt.MaxActivationDistance=12",MODELS)
        self.assertIn("prompt.Triggered:Connect",DEMO)
        self.assertIn("validPlayerNear(player,current.encounter.body)",DEMO)

    def test_server_only_one_active(self):
        self.assertIn('assert(current==nil,"NEUTRAL_SINGLE_GLOBAL_ACTIVE")',DEMO)
        self.assertIn("Policy.step(stepState,now,rng:NextNumber())",DEMO)
        self.assertIn("removeCurrent()",DEMO)
        self.assertIn("Players.PlayerRemoving:Connect",DEMO)
        self.assertIn("game:BindToClose",DEMO)

    def test_discovery_no_reward_or_upload(self):
        self.assertIn("no_reward=true",DEMO)
        self.assertIn("rewards=NONE",DEMO)
        self.assertIn("LOCAL_STUDIO_ONLY",DEMO)
        self.assertNotIn("HttpService",DEMO)

    def test_negative_auto_enable(self):
        def safe(v): return "ENABLE_RARE_NEUTRAL_STUDIO_PREVIEW = false" in v
        self.assertTrue(safe(DEMO))
        self.assertFalse(safe(DEMO.replace("ENABLE_RARE_NEUTRAL_STUDIO_PREVIEW = false",
                                           "ENABLE_RARE_NEUTRAL_STUDIO_PREVIEW = true",1)))

    def test_negative_paid_prompt(self):
        def safe(v):return 'prompt.ActionText="みつけた！"' in v
        self.assertTrue(safe(MODELS))
        self.assertFalse(safe(MODELS.replace('prompt.ActionText="みつけた！"',
                                              'prompt.ActionText="Pay Robux"',1)))

    def test_negative_unsafely_guaranteed_spawn(self):
        def safe(v):return "P.SPAWN_CHANCE = 0.12" in v
        self.assertTrue(safe(POLICY))
        self.assertFalse(safe(POLICY.replace("P.SPAWN_CHANCE = 0.12",
                                              "P.SPAWN_CHANCE = 1",1)))

if __name__=="__main__":
    unittest.main()
