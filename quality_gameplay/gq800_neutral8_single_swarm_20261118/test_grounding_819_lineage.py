"""Original #819 terrain safety source selection, preserved in latest #815 singleton."""
from pathlib import Path
import unittest

ROOT=Path(__file__).parent
COMPOSER=(ROOT/"compose_real43.py").read_text(encoding="utf-8")
CHARM=(ROOT/"compose_charm44.py").read_text(encoding="utf-8")

class TerrainSourceIntegration(unittest.TestCase):
    def test_exact_upstream_819_grounded_step(self):
        for marker in (
            "NEUTRAL_ACTUAL_TERRAIN_GROUNDING",
            "workspace:Raycast(next+Vector3.new(0,3,0),Vector3.new(0,-8,0),params)",
            "ground.Normal.Y>=.72",
            "math.abs(desiredY-at.Y)<=1.4",
            "m:PivotTo(CFrame.lookAt(grounded,grounded+near.Unit))",
        ):
            self.assertIn(marker,COMPOSER)
        self.assertEqual(COMPOSER.count('"NEUTRAL_ACTUAL_TERRAIN_GROUNDING"'),1)
    def test_charmed_followers_get_identical_ground_safety(self):
        for marker in (
            "ground.Normal.Y>=.72",
            "math.abs(desiredY-root.Position.Y)<=1.4",
            "workspace:Raycast(next+Vector3.new(0,3,0),Vector3.new(0,-8,0),ray)",
            "model:PivotTo(CFrame.lookAt(grounded,grounded+delta.Unit))",
        ):
            self.assertIn(marker,CHARM)
    def test_real43_ground_before_44_curse_selection(self):
        self.assertIn('original=flatten(original43)',CHARM)
        self.assertIn('selected=patch(baseline)',CHARM)
        self.assertIn('if len(original)!=43',CHARM)
        self.assertIn('if len(selected_paths)!=44',CHARM)
        self.assertIn('before[SWARM].read_text',COMPOSER)
    def test_single_owner_and_immutable_upstream(self):
        self.assertIn('"KoFence.mayCredit(session,id,m,all)"',COMPOSER)
        self.assertIn('"neutralBudget:acquire"',COMPOSER)
        self.assertIn('"SpawnPacing.step"',COMPOSER)
        self.assertIn('"EncounterFair"',COMPOSER)
        self.assertIn('AUTHOR_FINISHER_BLOB="42f512c4aaa389e0027be774c327e1f5a106aabf"',COMPOSER)
        self.assertIn('CHARM_BLOB="0bd81a807ff6a935642a660b9fe9e0fd05ef484c"',CHARM)

if __name__=="__main__":
    unittest.main()
