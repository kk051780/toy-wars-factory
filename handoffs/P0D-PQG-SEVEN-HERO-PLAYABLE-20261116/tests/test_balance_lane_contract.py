"""Static quality gate for the isolated balance lane; native Luau spec is separate."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class TestBalanceLane(unittest.TestCase):
 def test_only_pure_luau_and_no_external_game_mutation(self):
  src=(ROOT/"EGGRUMBLE_BalanceMetrics.luau").read_text()
  for forbidden in ("DataStoreService","MarketplaceService","RemoteEvent","workspace:","Players:GetPlayers","game:GetService"):
   self.assertNotIn(forbidden,src)
 def test_coverage(self):
  src=(ROOT/"EGGRUMBLE_BalanceMetrics.luau").read_text()
  for required in ("function B.neutralBudget(","function B.siegeMultiplier(","function B.score(","function B.castleParity(","function B.evaluate(","B.OVERTIME_DAMAGE_CAP=1.35","B.MAX_CASTLE_BONUS=0.05"):
   self.assertIn(required,src)
 def test_native_spec_exists(self):
  src=(ROOT/"tests/EGGRUMBLE_BalanceMetrics.spec.luau").read_text()
  self.assertIn('EGGRUMBLE_BALANCE_NATIVE_SOURCE_PASS',src)
  self.assertIn('not B.castleParity(1000,51)',src)
  self.assertIn('not missing.modeCoverage',src)
if __name__=="__main__":unittest.main()
