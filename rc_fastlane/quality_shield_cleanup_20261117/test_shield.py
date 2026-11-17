#!/usr/bin/env python3
"""Pure regression cases; true current31 Native/Rojo tested by main workflow."""
import unittest
from select_shield import BEFORE,AFTER,patch,unpatch

ORIGINAL='''function Replay.captureWalkBaseline(p:Player):number
 return 16
end
function Replay.resetHuman(p:Player,returnTo:Vector3,baseWalkSpeed:number?):()
 local ch=p.Character
'''+BEFORE+'''
 if hum then
  hum.WalkSpeed=16
 end
end
'''
class ShieldSourceTest(unittest.TestCase):
    def test_inverse_exact(self):
        changed=patch(ORIGINAL)
        self.assertEqual(unpatch(changed),ORIGINAL)
    def test_all_shields_only(self):
        changed=patch(ORIGINAL)
        self.assertIn('ipairs(ch:GetChildren())',changed)
        self.assertIn('effect.Name=="EGGRUMBLE_ItemShield"',changed)
        self.assertIn('effect:IsA("ForceField")',changed)
        self.assertIn('effect:Destroy()',changed)
        self.assertNotIn(BEFORE,changed)
    def test_nonduplicate_original(self):
        with self.assertRaisesRegex(ValueError,"DRIFT"):
            patch(ORIGINAL.replace(BEFORE,BEFORE+"\n"+BEFORE))
    def test_refuse_reapply(self):
        with self.assertRaisesRegex(ValueError,"DRIFT"):
            patch(patch(ORIGINAL))
    def test_refuse_unpatched_rollback(self):
        with self.assertRaisesRegex(ValueError,"DRIFT"):
            unpatch(ORIGINAL)
    def test_refuse_unowned_script(self):
        with self.assertRaisesRegex(ValueError,"OWNER"):
            patch(ORIGINAL.replace("Replay.resetHuman","Other.resetHuman"))
    def test_mutation_invalidates_inverse(self):
        updated=patch(ORIGINAL)
        mutant=updated.replace("effect:Destroy()","-- skip",1)
        with self.assertRaisesRegex(ValueError,"DRIFT"):
            unpatch(mutant)

if __name__=="__main__":
    unittest.main()
