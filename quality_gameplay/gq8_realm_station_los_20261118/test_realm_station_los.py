#!/usr/bin/env python3
"""Original-blob source QA and rollback mutants; no fixture-only success."""
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from patch_realm_station_los import (
    FEATURE_ID, OLD, NEW, UPSTREAM_BLOB, apply, rollback, git_blob_sha,
)

class RealmStationLOSQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = os.environ.get("GQ8_REALM_SOURCE")
        if not path:
            raise RuntimeError("RED_MISSING_PINNED_REALM_AUTHOR_SOURCE")
        cls.actual = Path(path).read_bytes()
        if git_blob_sha(cls.actual) != UPSTREAM_BLOB:
            raise RuntimeError("RED_REALM_AUTHOR_BLOB_NOT_PINNED")

    def test_original_author_current_defect_is_real(self):
        src = self.actual.decode()
        self.assertEqual(src.count(OLD), 1)
        fn = src.split("local function prompt(", 1)[1].split(
            "local function damageMultiplier(", 1
        )[0]
        self.assertIn("RequiresLineOfSight=true", fn)
        self.assertNotIn("Workspace:Raycast", fn)
        self.assertIn('prompt(dive,"潜水する"', src)
        self.assertIn('prompt(rise,"浮上する"', src)
        self.assertIn('prompt(flightPad,"戦闘機に搭乗"', src)

    def test_exact_one_helper_overlay_and_reverse(self):
        selected = apply(self.actual)
        self.assertEqual(rollback(selected), self.actual)
        txt = selected.decode()
        self.assertEqual(txt.count(NEW), 1)
        self.assertEqual(txt.count("local function prompt("), 1)
        self.assertEqual(txt.count("callback(player,h)"), 1)
        self.assertEqual(txt.count("Workspace:Raycast(r.Position,sightTarget-r.Position,sightParams)"), 1)
        self.assertEqual(txt.count("if sightHit and sightHit.Instance~=p then return end"), 1)

    def test_no_other_realm_author_source_changed(self):
        before = self.actual.decode()
        after = apply(self.actual).decode()
        self.assertEqual(after.replace(NEW, OLD, 1), before)
        self.assertIn("if not eligible(p,mode,world) then return end", after)
        self.assertIn("local MAX_AIRCRAFT = 2", after)
        self.assertIn("local MAX_SEA_CREATURES = 3", after)

    def test_behind_wall_bypass_mutant_rejected(self):
        broken = apply(self.actual).decode().replace(
            "if sightHit and sightHit.Instance~=p then return end",
            "if false then return end", 1
        ).encode()
        with self.assertRaisesRegex(ValueError, "RED_REALM_LOS_SELECTED_SOURCE_DRIFT"):
            rollback(broken)

    def test_false_los_accept_mutant_rejected(self):
        broken = apply(self.actual).decode().replace(
            "sightParams.FilterDescendantsInstances={c}",
            "sightParams.FilterDescendantsInstances={p,c}", 1
        ).encode()
        with self.assertRaisesRegex(ValueError, "RED_REALM_LOS_SELECTED_SOURCE_DRIFT"):
            rollback(broken)

    def test_remote_distance_mutant_rejected(self):
        broken = self.actual.replace(b"Magnitude>16", b"Magnitude>1600", 1)
        with self.assertRaisesRegex(ValueError, "RED_REALM_LOS_PINNED_SOURCE_DRIFT"):
            apply(broken)

    def test_duplicate_and_unpatched_rollback_rejected(self):
        with self.assertRaisesRegex(ValueError, "RED_REALM_LOS_PINNED_SOURCE_DRIFT"):
            apply(apply(self.actual))
        with self.assertRaisesRegex(ValueError, "RED_REALM_LOS_SELECTED_SOURCE_DRIFT"):
            rollback(self.actual)

if __name__ == "__main__":
    unittest.main()
