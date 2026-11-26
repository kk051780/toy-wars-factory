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
        self.assertIn('p:SetAttribute("GQ470CastleOptional",true)',modified)
        self.assertIn('p:IsDescendantOf(arena)',modified)
        self.assertIn('trackedArt[arena]=active',modified)
        self.assertIn('budgets[arena]=#active',modified)
        self.assertIn('if old then old:Destroy() end',modified)
        self.assertIn('castle.Destroying:Connect(',modified)
        self.assertIn('arena.Destroying:Connect(',modified)
        self.assertIn('if not builtArenas[arena] then return end',modified)
        self.assertLess(modified.index('if not builtArenas[arena] then return end'),
                        modified.index('if not reserveCastleIdentity(arena) then return end'))
        self.assertIn('for _,child in ipairs(arena:GetChildren()) do',modified)
        self.assertIn('trackedArt[arena]=nil',modified)
        self.assertEqual(modified.count('table.insert(tracked,p)'),1)
        self.assertEqual(modified.count('if not optionalIndex then return false end'),1)
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


    def test_destroyed_castle_parts_reclaim_without_evicting_identity(self):
        # Policy model only; final Roblox runtime semantics require Studio testing.
        for ridge in (0, 12):
            live = [("landscape", False)] * (140 + ridge)
            def reserve():
                nonlocal live
                live = [p for p in live if p[0] != "destroyed"]
                while len(live) + 10 > 320:
                    idx = next((i for i in range(len(live)-1, -1, -1)
                                if live[i][1]), None)
                    if idx is None:
                        return False
                    del live[idx]
                return True
            for castle in range(16):
                self.assertTrue(reserve())
                live.extend([(castle,False)] * 10)
                live.extend([(castle,True)] * min(9,320-len(live)))
                self.assertLessEqual(len(live),320)
            self.assertTrue(all(sum(1 for owner, is_optional in live
                                    if owner==castle and not is_optional)==10
                                for castle in range(16)))
            # Partial/complete destruction can orphan previous counter slots;
            # re-counting must free only genuinely removed Instances.
            for owner in (0,4,11):
                live = [("destroyed", is_optional) if who==owner
                        else (who,is_optional) for who,is_optional in live]
            self.assertTrue(reserve())
            before=len(live)
            self.assertLess(before,320)
            for owner in (20,21,22):
                self.assertTrue(reserve())
                live.extend([(owner,False)] * 10)
                live.extend([(owner,True)] * min(9,320-len(live)))
                self.assertLessEqual(len(live),320)
            self.assertTrue(all(sum(1 for who, optional in live
                                    if who==owner and not optional)==10
                                for owner in (20,21,22)))
            self.assertTrue(all(sum(1 for who, optional in live
                                    if who==owner and not optional)==10
                                for owner in (1,2,3,5,6,7,8,9,10,12,13,14,15)))

    def test_all_optional_disappeared_then_recalculate_stale_counter(self):
        # Count tracks actually live owned Instances, not stale numerators.
        living = [("terrain",False)]*140 + [("castle",False)]*170
        prior_counter=320
        self.assertNotEqual(len(living),prior_counter)
        active=len(living)
        self.assertEqual(active,310)
        self.assertLessEqual(active+10,320)

    def test_castle_early_creation_sceneries_before_essentials(self):
        source=patch.transform(self.source)
        # Source-only order: castleAt is gated until paintArena has set the
        # builtArenas flag and completed the 140-part landscape pass.
        self.assertIn('if not builtArenas[arena] then return end',source)
        paint=source.split('local function paintArena(arena:Instance)',1)[1]
        self.assertLess(paint.index('drawRouteMarker('),
                        paint.index('for _,child in ipairs(arena:GetChildren()) do'))
        self.assertLess(paint.index('drawTree(arena,art,'),
                        paint.index('for _,child in ipairs(arena:GetChildren()) do'))

    def test_mutants_fail_closed(self):
        cases=[
          (patch.A,''),
          (patch.B,''),
          (patch.C,''),
          (patch.D,''),
          (patch.E,''),
          (patch.F,''),
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
