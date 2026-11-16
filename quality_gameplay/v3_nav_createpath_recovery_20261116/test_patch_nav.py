"""Negative regression tests for original-author-locked CreatePath recovery overlay.

These are source/contract tests, NOT native Luau or actual Studio tests.
"""
from __future__ import annotations
import os
from pathlib import Path
import unittest

from patch_nav import BEFORE, AFTER, ORIGINAL_BLOB, SourceDrift, blob_sha, overlay


class NavFailureRecoveryPatchTests(unittest.TestCase):
    def test_exact_single_hunk_and_unchanged_20plus_owner_behaviors(self):
        # Synthetic only: actual original source is tested separately from the Git ref.
        sample = (
            '--!strict\nlocal MAX_COMPUTES_IN_FLIGHT=2\n'
            + 'function Router.navigate(\n'
            + BEFORE
            + '  state.inFlight=false\n  if ok and path.Status==Enum.PathStatus.Success then\n'
        ).encode()
        fixed = overlay(sample, locked=False).decode()
        self.assertEqual(fixed.count(AFTER), 1)
        self.assertIn('local candidate=PathfindingService:CreatePath({', fixed)
        self.assertIn('candidate:ComputeAsync(surfaceAt(at,actors),surfaceAt(expectedTarget,actors))', fixed)
        self.assertIn('inFlight=math.max(0,inFlight-1)', fixed)
        self.assertEqual(fixed.count('MAX_COMPUTES_IN_FLIGHT=2'), 1)
        self.assertIn('if ok and path.Status==Enum.PathStatus.Success then', fixed)
        self.assertNotIn(BEFORE, fixed)
        self.assertEqual(fixed.replace(AFTER, BEFORE), sample.decode())

    def test_non_original_source_rejected_without_override(self):
        data = ('local MAX_COMPUTES_IN_FLIGHT=2\nfunction Router.navigate(\n' + BEFORE).encode()
        with self.assertRaises(SourceDrift):
            overlay(data)

    def test_duplicate_source_anchor_fails_closed(self):
        raw = ('local MAX_COMPUTES_IN_FLIGHT=2\nfunction Router.navigate(\n' + BEFORE + BEFORE).encode()
        with self.assertRaises(SourceDrift):
            overlay(raw, locked=False)

    def test_changed_author_call_fails_closed(self):
        raw = ('local MAX_COMPUTES_IN_FLIGHT=2\nfunction Router.navigate(\n' +
               BEFORE.replace('PathfindingService:CreatePath', 'OtherNavigation:CreatePath')).encode()
        with self.assertRaises(SourceDrift):
            overlay(raw, locked=False)

    def test_overlay_is_not_idempotent_without_new_author_lock(self):
        raw = ('local MAX_COMPUTES_IN_FLIGHT=2\nfunction Router.navigate(\n' + BEFORE).encode()
        with self.assertRaises(SourceDrift):
            overlay(overlay(raw, locked=False), locked=False)

    def test_error_branch_releases_global_budget_before_any_return(self):
        src = AFTER
        self.assertLess(src.index('inFlight=math.max(0,inFlight-1)'), src.index('if not path then'))
        self.assertIn('if states[id]==state then', src)
        self.assertIn('state.inFlight=false', src)
        self.assertIn('state.retryAt=os.clock()+RECOMPUTE_SECONDS', src)
        self.assertIn('state.failed=(state.failed or 0)+1', src)

    def test_original_unprotected_createpath_must_not_remain(self):
        self.assertEqual(AFTER.count('PathfindingService:CreatePath'), 1)
        self.assertEqual(AFTER.count('local ok=pcall(function()'), 1)
        self.assertLess(AFTER.index('local ok=pcall(function()'), AFTER.index('PathfindingService:CreatePath'))

    @unittest.skipUnless(os.getenv("GQ_NAV_ORIGINAL_SOURCE"), "pinned author source must be provided by CI")
    def test_actual_original_blob_and_one_hunk(self):
        original = Path(os.environ["GQ_NAV_ORIGINAL_SOURCE"]).read_bytes()
        self.assertEqual(blob_sha(original), ORIGINAL_BLOB)
        updated = overlay(original).decode()
        original_decoded = original.decode()
        self.assertEqual(updated.replace(AFTER, BEFORE), original_decoded)
        self.assertIn('local candidate=PathfindingService:CreatePath({', updated)
        self.assertEqual(updated.count('inFlight=math.max(0,inFlight-1)'), 1)


if __name__ == "__main__":
    unittest.main()
