"""Project-level isolation and catalog truth, not native Luau/Roblox engine QA."""
from pathlib import Path
import json,unittest

ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/"src/EvolutionRules.luau").read_text(encoding="utf8")
SERVER=(ROOT/"demo/EvolutionGallery.server.luau").read_text(encoding="utf8")
CLIENT=(ROOT/"demo/EvolutionGalleryCamera.client.luau").read_text(encoding="utf8")
PROJECT=json.loads((ROOT/"default.project.json").read_text(encoding="utf8"))

class EvolutionBoundaries(unittest.TestCase):
    def test_project_maps_only_isolated_preview(self):
        t=PROJECT["tree"]
        self.assertEqual(t["ServerScriptService"]["EvolutionGallery"]["$path"],
            "demo/EvolutionGallery.server.luau")
        self.assertEqual(t["StarterPlayer"]["StarterPlayerScripts"]["EvolutionGalleryCamera"]["$path"],
            "demo/EvolutionGalleryCamera.client.luau")

    def test_studio_server_only(self):
        self.assertIn("if not RunService:IsStudio() then return end",SERVER)

    def test_studio_client_only(self):
        self.assertIn("if not RunService:IsStudio() then return end",CLIENT)

    def test_no_game_or_paid_remote_or_storage(self):
        forbidden=("RemoteEvent","FireServer","DataStoreService","UpdateAsync",
                   "MarketplaceService","ProcessReceipt","PublishAsync","PromptProductPurchase",
                   "TrapRaidersS1Remote")
        for x in forbidden:
            with self.subTest(x=x):
                self.assertNotIn(x,SRC+SERVER+CLIENT)

    def test_real_275_scout_ids_in_source(self):
        for item in ("starter_scout","forest_scout","star_scout"):
            self.assertIn(item,SRC)

    def test_six_categories_and_honest_live_flags(self):
        for c in ("BEAST","SPELL","MOUNT","ITEM","ZOMBIE","TRAP"):
            self.assertIn(c,SRC)
        self.assertIn("liveId=false",SRC)
        self.assertIn("actualCombatImplemented=false",SRC)

    def test_base_form_starts_at_zero(self):
        self.assertIn('return {stage=0,branch="NONE"}',SRC)

    def test_progression_gates(self):
        self.assertIn("local COST = { [1]=2, [2]=5, [3]=10 }",SRC)
        self.assertIn("local NEED_ACCOUNT_LV = { [1]=10, [2]=25, [3]=40 }",SRC)
        self.assertIn("local NEED_MASTERY_LV = { [1]=3, [2]=6, [3]=10 }",SRC)

    def test_no_client_auth(self):
        self.assertIn("serverConfirmed~=true",SRC)
        self.assertIn("itemOwned(ownedItems,itemId)",SRC)

    def test_award_finite_fragments(self):
        self.assertIn("E.MAX_FRAGMENTS = 100000",SRC)
        self.assertIn("local gain=realObjectiveCount>=2 and 2 or 1",SRC)
        self.assertIn("profile.roundReceipts[roundId]",SRC)

    def test_evolution_idempotent_receipts(self):
        self.assertIn("profile.evoReceipts[requestId]",SRC)
        self.assertIn('return false,"RECEIPT_CONFLICT"',SRC)

    def test_lobby_only(self):
        self.assertIn('phase~="LOBBY"',SRC)

    def test_earned_and_reversible_branch(self):
        self.assertIn("function E.switchBranch(",SRC)
        self.assertIn("profile.fragments-=3",SRC)

    def test_no_double_pvp_bonus_from_evolution(self):
        self.assertIn("additionalPvpStatMultiplier=0",SRC)
        self.assertIn("requiresPaidPurchase=false",SRC)

    def test_studio_exhibits_five_shapes(self):
        self.assertIn('name="幼体"',SERVER)
        self.assertIn('name="紅蓮進化"',SERVER)
        self.assertIn('name="蒼潮進化"',SERVER)
        self.assertIn('name="天龍神話体"',SERVER)
        self.assertIn('Instance.new("Model")',SERVER)
        self.assertIn("model:PivotTo",SERVER)

    def test_no_fake_claim_3d_ability(self):
        self.assertIn('modelId="NOT_INTEGRATED"',SRC)
        self.assertIn("NOT the actual H1/H2 Game",SERVER)

    def test_client_no_owned_mutations(self):
        self.assertNotIn("Owned",CLIENT)
        self.assertIn("STUDIO専用展示",CLIENT)

if __name__=="__main__":
    unittest.main(verbosity=2)
