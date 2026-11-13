"""Guardrails only: static checks cannot establish genuine native Luau pass."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
DEX=(ROOT/"src"/"EvolutionFormDex.luau").read_text(encoding="utf-8")
ORIGINAL=(ROOT/"src"/"EvolutionRules.luau").read_text(encoding="utf-8")
NATIVE=(ROOT/"tests"/"run_native_formdex.py").read_text(encoding="utf-8")

class FormDexStatic(unittest.TestCase):
    def test_genuine_server_receipt_costs(self):
        self.assertIn("local EVOLVE_COST = { [1]=2, [2]=5, [3]=10 }",DEX)
        self.assertIn("local SWITCH_COST = 3",DEX)
        self.assertIn("receipt.cost~=expectedCost",DEX)
    def test_original_evolution_module_matches_receipt_cost_contract(self):
        self.assertIn("local COST = { [1]=2, [2]=5, [3]=10 }",ORIGINAL)
        self.assertIn("cost=next.fragmentCost",ORIGINAL)
        self.assertIn("cost=3",ORIGINAL)
    def test_fraudulent_double_evolve_stage_fails_closed(self):
        self.assertIn("local seenEvolveStages={}",DEX)
        self.assertIn("seenEvolveStages[uniqueStage]",DEX)
        self.assertIn('"DUPLICATE_STAGE_EVOLUTION"',DEX)
    def test_read_only_never_grants_rewards(self):
        self.assertIn("grantEntitlements=false",DEX)
        self.assertIn("canEquipDirectly=false",DEX)
        self.assertNotIn("profile.fragments-=",DEX)
        self.assertNotIn("profile.forms[itemId]=",DEX)
    def test_original_server_authority_instead_of_client(self):
        self.assertIn("evolution.form(profile,itemId,ownedItems)",DEX)
        self.assertIn("pairs(profile.evoReceipts)",DEX)
        self.assertNotIn("FireServer(",DEX)
        self.assertNotIn("DataStoreService",DEX)
    def test_three_attack_regressions_authored_in_native(self):
        self.assertIn("forged zero-cost evolution is not a discovery",NATIVE)
        self.assertIn("forged free branch switch is not a discovery",NATIVE)
        self.assertIn("duplicate stage2 permanent evolution rejected",NATIVE)
    def test_formdex_catalog_truth(self):
        self.assertIn("isCurrentPlayableId=original.isCurrentPlayableId==true",DEX)
        self.assertIn("totalPossibleForms=6",DEX)
    def test_preserves_old_form_history_on_respec(self):
        self.assertIn("discoveredByItem[receipt.itemId][receipt.formId]",DEX)
        self.assertIn("activeFormId=formId",DEX)

if __name__=="__main__":
    unittest.main(verbosity=2)
