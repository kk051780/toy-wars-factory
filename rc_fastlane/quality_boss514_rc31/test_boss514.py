import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location("boss",Path(__file__).with_name("select_boss.py"))
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
def fixture():
    return ('function Replay.resetHuman(p:Player,returnTo:Vector3,baseWalkSpeed:number?):()\n'
            ' p:SetAttribute("EGGRUMBLE_NeutralKOs",0)\n'
            ' p:SetAttribute("EGGRUMBLE_Combo",0)\n'
            ' p:SetAttribute("EGGRUMBLE_BestCombo",0)\n'
            ' -- GQ8_MULTI_SHIELD_REPLAY_CLEANUP_BEGIN\nend\n')
class OriginalBossCreditIntake(unittest.TestCase):
    def test_original_author_source_scope(self):
        self.assertEqual(mod.AUTHOR_PR,514)
        self.assertEqual(mod.AUTHOR_HEAD,"0d1be13be6d895bea460ba54aaa91ef346684d7f")
    def test_single_patch_inverse_and_historical_combo_preserved(self):
        s=fixture()
        self.assertEqual(mod.unpatch(mod.patch(s)),s)
        self.assertEqual(mod.patch(s).count(mod.INSERT),1)
        self.assertIn("EGGRUMBLE_Combo",mod.patch(s))
    def test_repeat_application_rejected(self):
        with self.assertRaises(ValueError):mod.patch(mod.patch(fixture()))
    def test_missing_prior_combo_rejected(self):
        with self.assertRaises(ValueError):
            mod.patch(fixture().replace(' p:SetAttribute("EGGRUMBLE_Combo",0)\n',''))
    def test_stale_shield_parent_rejected(self):
        with self.assertRaises(ValueError):
            mod.patch(fixture().replace("GQ8_MULTI_SHIELD_REPLAY_CLEANUP_BEGIN","stale"))
    def test_duplicate_source_anchor_rejected(self):
        with self.assertRaises(ValueError):mod.patch(fixture()+mod.ANCHOR)
    def test_wrong_owner_rejected(self):
        with self.assertRaises(ValueError):mod.patch(fixture().replace("Replay.resetHuman","fake.resetHuman"))
    def test_mutant_removing_boss_reset_rejected(self):
        live=mod.patch(fixture())
        with self.assertRaises(ValueError):mod.unpatch(live.replace(mod.INSERT,""))
if __name__=="__main__":unittest.main()
