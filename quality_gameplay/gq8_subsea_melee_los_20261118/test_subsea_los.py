"""Fail closed on upstream source drift, bad LOS mutants and inverse mismatch."""
import os
import sys
import unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from patch_melee import apply,rollback,native_harness,git_blob_sha,UPSTREAM_BLOB,HELPER,OLD_MELEE,NEW_MELEE

class TestSubseaRealSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=os.environ.get("GQ8_SUBSEA_REALM_ORIGINAL")
        if not path:
            raise RuntimeError("RED_GQ8_SUBSEA_SOURCE_PATH_MISSING")
        cls.original=Path(path).read_bytes()
        if git_blob_sha(cls.original)!=UPSTREAM_BLOB:
            raise RuntimeError("RED_GQ8_SUBSEA_REAL_AUTHOR_BLOB_MISMATCH")

    def test_original_real_defect(self):
        src=self.original.decode()
        self.assertEqual(src.count(OLD_MELEE),1)
        self.assertIn('prompt(dive,"潜水する"',src)
        self.assertIn('prompt(flightPad,"戦闘機に搭乗"',src)
        self.assertIn('if h then h:TakeDamage(6) end',src)
        self.assertEqual(src.count(HELPER),0)

    def test_one_original_script_overlay_only(self):
        on=apply(self.original).decode()
        self.assertEqual(on.count(HELPER),1)
        self.assertEqual(on.count(NEW_MELEE),1)
        self.assertEqual(on.count("clearSubseaMeleePath(creature,nearest.Character,root)"),1)
        self.assertEqual(on.count("return Workspace:Raycast(from,delta,ray)==nil"),1)
        self.assertEqual(on.count("ray.RespectCanCollide=true"),1)
        self.assertEqual(on.count("ray.FilterDescendantsInstances={creature,targetCharacter}"),1)
        self.assertEqual(on.count('remote.OnServerEvent:Connect('),1)

    def test_off_original_blob_exact(self):
        self.assertEqual(rollback(apply(self.original)),self.original)

    def test_noninterference_land_air_ship_combat(self):
        before=self.original.decode()
        after=apply(self.original).decode().replace(HELPER,"",1).replace(NEW_MELEE,OLD_MELEE,1)
        self.assertEqual(after,before)
        for marker in ("local MAX_AIRCRAFT = 2","local MAX_SEA_CREATURES = 3",
                      'if weapon=="BOMB" then','if weapon=="HYDRO" then return end',
                      "function(dt)","core:SetAttribute(\"LightningWarning\",true)"):
            self.assertIn(marker,after)

    def test_wall_bypass_mutant_fail_closed(self):
        bad=apply(self.original).replace(b"return Workspace:Raycast(from,delta,ray)==nil",
                                           b"return true",1)
        with self.assertRaisesRegex(ValueError,"RED_GQ8_SUBSEA_SELECTED_DRIFT"):
            rollback(bad)

    def test_target_exclusion_mutant_fail_closed(self):
        bad=apply(self.original).replace(b"{creature,targetCharacter}",b"{creature,world}",1)
        with self.assertRaisesRegex(ValueError,"RED_GQ8_SUBSEA_SELECTED_DRIFT"):
            rollback(bad)

    def test_cooldown_and_hit_mutant_fail_closed(self):
        selected=apply(self.original)
        bad=selected.replace(b"data.lastHit=now\n       h:TakeDamage(6)",
                                           b"data.lastHit=now\n        h:TakeDamage(600)",1)
        self.assertNotEqual(selected,bad,"harmful mutation must actually change bytes")
        with self.assertRaisesRegex(ValueError,"RED_GQ8_SUBSEA_SELECTED_DRIFT"):
            rollback(bad)

    def test_old_author_drift_rejected(self):
        bad=self.original.replace(b"if h then h:TakeDamage(6) end",
                                  b"if h then h:TakeDamage(9) end",1)
        with self.assertRaisesRegex(ValueError,"RED_GQ8_SUBSEA_ORIGINAL_BLOB_DRIFT"):
            apply(bad)

    def test_double_apply_and_wrong_off_rejected(self):
        with self.assertRaises(ValueError):
            apply(apply(self.original))
        with self.assertRaises(ValueError):
            rollback(self.original)

    def test_executable_native_harness_uses_exact_source(self):
        s=native_harness(apply(self.original))
        self.assertIn(HELPER,s)
        self.assertIn("GQ8_SUBSEA_REAL_SOURCE_NATIVE_13_CASES_PASS",s)
        self.assertIn("data.lastHit=now",s)
        self.assertIn("h:TakeDamage(6)",s)
        self.assertIn("blocked second swing must not stamp cooldown",s)

if __name__=="__main__":
    unittest.main()
