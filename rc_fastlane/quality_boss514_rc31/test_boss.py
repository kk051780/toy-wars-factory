#!/usr/bin/env python3
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from select_boss import ANCHOR,EXTRA,patch,unpatch
def parent():
    return ('function Replay.resetHuman(p:Player,returnTo:Vector3,baseWalkSpeed:number?):()\n'
            ' p:SetAttribute("EGGRUMBLE_Combo",0)\n'+ANCHOR+
            ' -- GQ8_MULTI_SHIELD_REPLAY_CLEANUP_BEGIN\nend\n')
class Contract(unittest.TestCase):
    def test_inverse_exact(self):
        self.assertEqual(unpatch(patch(parent())),parent())
    def test_single_boss_reset(self):
        x=patch(parent())
        self.assertEqual(x.count('p:SetAttribute("EGGRUMBLE_BossDefeats",0)'),1)
        self.assertEqual(x.count('p:SetAttribute("EGGRUMBLE_Combo",0)'),1)
        self.assertEqual(x.count('p:SetAttribute("EGGRUMBLE_BestCombo",0)'),1)
    def test_parent_missing_rejected(self):
        with self.assertRaises(ValueError):patch(parent().replace("GQ8_MULTI_SHIELD_REPLAY_CLEANUP_BEGIN","MISSING"))
    def test_combo_missing_rejected(self):
        with self.assertRaises(ValueError):patch(parent().replace('EGGRUMBLE_Combo','EGGRUMBLE_BadCombo'))
    def test_double_apply_rejected(self):
        with self.assertRaises(ValueError):patch(patch(parent()))
    def test_duplicate_anchor_rejected(self):
        with self.assertRaises(ValueError):patch(parent().replace(ANCHOR,ANCHOR*2))
    def test_wrong_inverse_rejected(self):
        with self.assertRaises(ValueError):unpatch(parent())
if __name__=="__main__":unittest.main()
