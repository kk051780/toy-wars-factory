"""GQ last-stud AI route-ray source QA; not a substitute for Studio physics."""
from __future__ import annotations
import os
from pathlib import Path
import unittest

from source_patch import BEFORE, AFTER, ORIGINAL_BLOB, SourceDrift, git_blob_sha, overlay
from make_native_ray_harness import build, function_from


class FullStepSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw_path = os.getenv("GQ_ROUTE_ORIGINAL")
        cls.original = Path(raw_path).read_bytes() if raw_path else None

    def test_source_hunk_is_exact_and_reversible(self):
        if self.original is None:
            self.skipTest("original #484 source fetched by CI only")
        self.assertEqual(git_blob_sha(self.original), ORIGINAL_BLOB)
        patched = overlay(self.original)
        self.assertEqual(patched.decode().replace(AFTER, BEFORE), self.original.decode())
        self.assertEqual(patched.decode().count(AFTER), 1)
        self.assertEqual(patched.decode().count("local MAX_COMPUTES_IN_FLIGHT=2"), 1)
        self.assertEqual(patched.decode().count("function Router.navigate("), 1)

    def test_native_harness_uses_actual_function_not_a_reimplementation(self):
        if self.original is None:
            self.skipTest("original #484 source fetched by CI only")
        original = self.original.decode()
        patched = overlay(self.original).decode()
        current = function_from(original)
        fixed = function_from(patched)
        self.assertIn(BEFORE,current)
        self.assertIn(AFTER,fixed)
        self.assertEqual(fixed.replace(AFTER,BEFORE),current)
        self.assertIn('EXPECT_TAIL_CLEAR', __import__('make_native_ray_harness').SUFFIX)
        self.assertIn('GQ_NATIVE_PATCH_FULLSTEP_RAY',build(patched,patched=True))

    def test_drift_is_red(self):
        raw = b"-- not current author" + BEFORE.encode()
        with self.assertRaises(SourceDrift):
            overlay(raw)

    def test_duplicate_replacement_anchor_is_red(self):
        if self.original is None:
            self.skipTest("original #484 source fetched by CI only")
        with self.assertRaises(SourceDrift):
            overlay(self.original+BEFORE.encode(),locked=False)

    def test_no_physical_authority_replaced(self):
        self.assertNotIn("Router.navigate(", AFTER)
        self.assertNotIn("workspace:PivotTo(", AFTER)
        self.assertNotIn("TakeDamage",AFTER)


if __name__ == "__main__":
    unittest.main()
