"""SOURCE-only original-#484 composer integration negative tests, no engine claims."""
import unittest
from patch_ridge import HOST, ITEMS, NEW, OLD
from augment_current26 import patch_composed_host

class OriginalComposerOverlayTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host=HOST.read_text(encoding="utf-8")
        cls.item=ITEMS.read_text(encoding="utf-8")
        cls.quality="-- owner quality author source --"
        cls.ramp="\n -- Already composed original #484 CastleAccessRamp --"

    def compose(self,a,q):
        self.assertEqual(q,self.quality)
        return a+self.ramp

    def test_01_exact_original_composed_one_ridge_hunk(self):
        original=self.compose(self.host,self.quality)
        modified=patch_composed_host(original,self.host,self.quality,self.item,self.compose)
        self.assertEqual(modified.count(NEW),1)
        self.assertEqual(modified.replace(NEW,OLD),original)
        self.assertIn(self.ramp,modified)
        self.assertEqual(modified.count("CastleAccessRamp"),original.count("CastleAccessRamp"))

    def test_02_refuse_original_484_ramp_drift(self):
        original=self.compose(self.host,self.quality)
        with self.assertRaisesRegex(ValueError,"composed host drift"):
            patch_composed_host(original+"extra",self.host,self.quality,self.item,self.compose)

    def test_03_refuse_original_author_blob_change(self):
        original=self.compose(self.host,self.quality)
        with self.assertRaisesRegex(ValueError,"original #482 host Git blob changed"):
            patch_composed_host(original,self.host+"extra",self.quality,self.item,self.compose)

    def test_04_refuse_input_item_drift(self):
        original=self.compose(self.host,self.quality)
        with self.assertRaisesRegex(ValueError,"item site changed"):
            patch_composed_host(original,self.host,self.quality,
             self.item.replace('x=0,z=470,kind="SHIELD"','x=80,z=470,kind="SHIELD"'),self.compose)

    def test_05_refuse_reapplication(self):
        original=self.compose(self.host,self.quality)
        generated=patch_composed_host(original,self.host,self.quality,self.item,self.compose)
        with self.assertRaisesRegex(ValueError,"composed host drift"):
            patch_composed_host(generated,self.host,self.quality,self.item,self.compose)

    def test_06_untouched_7domain_sources_and_original_composer_mapping(self):
        original=self.compose(self.host,self.quality)
        result=patch_composed_host(original,self.host,self.quality,self.item,self.compose)
        for token in ['BotActors.start(session,Rules)','SwarmCombat.start(session)',
         'RaidItemIntake.start(session,root,FieldItems)','Rules.start(session.rules)',
         'SevenRoleCombat.equip(session,p,role)','ResultService.showIfFinished(session,queue,mode)']:
            self.assertEqual(original.count(token),result.count(token))
        self.assertEqual(original.count('CentralRidgeRight'),0)
        self.assertEqual(result.count('CentralRidgeRight'),1)

if __name__=="__main__":unittest.main()
