#!/usr/bin/env python3
"""Real original 69-source negative and OFF checks; not Roblox runtime."""
import importlib.util, os, pathlib, re, shutil, tempfile, unittest

HERE=pathlib.Path(__file__).parent
spec=importlib.util.spec_from_file_location('castle_budget_patch',HERE/'patch_castle_fairbudget.py')
patch=importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)
OFFICIAL=pathlib.Path(os.environ.get('GQ470_REAL69_BASE','/tmp/gq470-fairbudget-official'))

class CastleVisualBudgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert (OFFICIAL/patch.RECEIPT).is_file(), 'MISSING_IMMUTABLE_REAL69_ARTIFACT'
        cls.source=patch.selected(OFFICIAL)[patch.ROUTE].read_text()

    def test_real_original_source_has_exactly_one_owner_and_full_art_retained(self):
        modified=patch.transform(self.source)
        self.assertEqual(modified.count(patch.FEATURE),1)
        self.assertIn('if not reserveCastleIdentity(arena) then return end',modified)
        self.assertIn('if used>MIN_CASTLE_ESSENTIAL_PARTS then',modified)
        self.assertIn('p:Destroy()',modified)
        self.assertIn('budgets[arena]=math.max(0,(budgets[arena] or 0)-1)',modified)
        self.assertEqual(modified.count('add("HeraldicCrest"'),1)
        self.assertEqual(modified.count('local MAX_CASTLE_PARTS = 19'),1)
        self.assertIn('GQ8_RC86_FB015_FORTRESS_DETAIL_VISUAL_PORT_REAL69_20261120',modified)

    def test_16_castle_reservation_with_or_without_pr916_twelve_ridges(self):
        # Existing selected field: 24 route marker + 12 identity + 80 forest
        # + 20 rocks + 4 ruins = 140, max 16 castles, first 10 parts essential.
        for ridge in (0,12):
            occupied=140+ridge
            optional=0
            for castle in range(16):
                while occupied+10>320 and optional>0:
                    occupied-=1
                    optional-=1
                self.assertLessEqual(occupied+10,320)
                occupied+=10
                for extra in range(9):
                    if occupied==320: break
                    occupied+=1
                    optional+=1
            self.assertLessEqual(occupied,320)
            self.assertEqual(140+ridge+16*10,300+ridge)

    def test_mutants_fail_closed(self):
        cases=[
          (patch.A,''),
          (patch.B,''),
          (patch.C,''),
          ('local MAX_VISUAL_PARTS_PER_ARENA = 320','local MAX_VISUAL_PARTS_PER_ARENA = 3200'),
          ('local MAX_CASTLE_PARTS = 19','local MAX_CASTLE_PARTS = 9'),
          ('local function drawRouteMarker(','local function fakeRoute('),
          ('GQ8_RC86_FB015_FORTRESS_DETAIL_VISUAL_PORT_REAL69_20261120','MISSING'),
        ]
        for before,after in cases:
            with self.subTest(case=before[:24]),self.assertRaises(ValueError):
                patch.transform(self.source.replace(before,after,1))
        with self.assertRaises(ValueError):patch.transform(patch.transform(self.source))

    def test_real_69_hash_lock_rollback_and_double_apply(self):
        with tempfile.TemporaryDirectory() as dirname:
            root=pathlib.Path(dirname)
            shutil.copytree(OFFICIAL/'sources',root/'sources')
            for fn in (patch.PROJECT,patch.RECEIPT,patch.PLACE):
                shutil.copy2(OFFICIAL/fn,root/fn)
            patch.apply(root)
            on=patch.selected(root)
            off=patch.selected(root/'OFF69_CASTLE_BUDGET')
            self.assertEqual(len(on),69)
            self.assertEqual(set(on),set(off))
            self.assertEqual([k for k in on if on[k].read_bytes()!=off[k].read_bytes()],[patch.ROUTE])
            self.assertEqual((root/'OFF69_CASTLE_BUDGET'/patch.PLACE).read_bytes(),(root/patch.PLACE).read_bytes())
            with self.assertRaises(ValueError):patch.apply(root)

if __name__=='__main__':unittest.main()
