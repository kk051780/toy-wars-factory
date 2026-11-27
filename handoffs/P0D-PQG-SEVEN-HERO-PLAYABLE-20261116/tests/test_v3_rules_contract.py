"""Source-level contract tests for EGGRUMBLE V3; real Roblox/Luau engine tests still required."""
import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def contents(name):
    return (ROOT/name).read_text(encoding="utf-8")

MODEL_FILE=ROOT/"tools/eggrumble_capacity_model.py"
spec=importlib.util.spec_from_file_location("eggrumble_capacity_model",MODEL_FILE)
model=importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name]=model
spec.loader.exec_module(model)

class TestEGGRUMBLEV3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules=contents("EGGRUMBLE_CastleMatchRules.luau")
        cls.preview=contents("EGGRUMBLE_LobbyCastleModesPreview.server.luau")
        cls.shop=contents("EGGRUMBLE_CastleShopCatalog.luau")
        cls.design=contents("EGGRUMBLE_V3_CASTLE_ELIMINATION_MULTI_EGGS_GAME_MODES_CAPACITY.md")

    def test_modes_and_elimination_logic_exist(self):
        for name in ('MODE_TEAM="TEAM"','MODE_ROYALE="BATTLE_ROYALE"',
                     'if count<=1 then','m.phase="FINISHED"',
                     'c.hp=0;c.alive=false',
                     'm.fieldEggs+=released',
                     'released=c.vaultEggs+c.heldEggs',
                     'assert(c.alive and attacker.alive',
                     "friendly fire blocked"):
            with self.subTest(name=name): self.assertIn(name,self.rules)

    def test_multi_egg_and_castle_owner_only(self):
        for name in ('EGGS_PER_CASTLE=3','DEFAULT_FIELD_EGGS=24',
                     'thief.heldEggs+quantity<=3',
                     'assert(c.id==tostring(actorId)',
                     'MAX_HOUSE_PIECES=48','collidable=false',
                     'function M.depositEggs','function M.takeEggs'):
            with self.subTest(name=name): self.assertIn(name,self.rules)

    def test_defense_budget_safety(self):
        for name in ('CASTLE_HP=1000','MAX_DEFENSE_SLOTS=3','DEFENSE_POINTS=10',
                     'c.shield=if used.HARDENED then 50 else 0',
                     'c.repairCharge=if used.REPAIR then 50 else 0',
                     'durability stacking forbidden','MAX_EFFECTIVE_EXTRA_ENDURANCE=50',
                     'PAID_POWER_MULTIPLIER=1','noPaidRandomDefense=true',
                     'freeEqualMaxBudget=true'):
            with self.subTest(name=name): self.assertIn(name,self.rules+self.shop)
        for forbidden in ('MarketplaceService','PromptProductPurchase','ProcessReceipt',
                          'DataStoreService'):
            self.assertNotIn(forbidden,self.shop+self.rules)

    def test_portals_and_ai_fill_and_game_presentation(self):
        for name in ('TEAM_PORTAL','BATTLE_ROYALE_PORTAL','MODE_SEATS=16',
                     'Rules.makeRoster(mode,humans,MODE_SEATS)',
                     'Rules.damageCastle(state,entry.id,from,120)',
                     'Rules.takeEggs(session.rules','Rules.depositEggs(session.rules',
                     'session.releaseEggs','getCastlePoint','session.rules.winner'):
            with self.subTest(name=name): self.assertIn(name,self.preview)
        self.assertIn('if not RunService:IsStudio() then return end',self.preview)
        self.assertNotIn('TeleportService',self.preview)

    def test_capacity_math_targets_and_sensitivity(self):
        self.assertTrue(model.model(12,4,240).within_assumed_budget)
        self.assertAlmostEqual(model.model(12,4,240).script_ms,8.48)
        self.assertAlmostEqual(model.model(16,0,240).script_ms,8.00)
        self.assertAlmostEqual(model.model(20,4,220).script_ms,9.80)
        self.assertAlmostEqual(model.model(24,0,240).script_ms,9.56)
        self.assertFalse(model.model(28,4,160).within_assumed_budget)
        self.assertFalse(model.model(32,0,160).within_assumed_budget)
        self.assertAlmostEqual(model.kills_per_second(10000),10000/900)
        self.assertAlmostEqual(model.kills_per_second(30000),30000/900)
        self.assertAlmostEqual(model.max_mean_neutral_lifetime(240,30000),7.2)
        self.assertIn("ASSUMPTIONS, NOT ENGINE MEASUREMENTS",self.design)

if __name__=="__main__":
    unittest.main()
