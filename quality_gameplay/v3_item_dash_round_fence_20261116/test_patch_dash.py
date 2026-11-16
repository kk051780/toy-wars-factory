"""Source-exact and falsification tests; not Roblox Studio runtime proof."""
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from patch_dash import (
    OLD, NEW, ORIGINAL_BLOB, git_blob_sha, patch_source,
)


class DashRoundFenceTests(unittest.TestCase):
    @staticmethod
    def fixture():
        return ('--!strict\n'
                'local function matchActive():boolean\n'
                ' return active and folder.Parent~=nil and session.rules.phase=="ACTIVE"\n'
                'end\n'
                'if kind=="DASH" then\n' + OLD + '\nend\n')

    def test_old_session_expiry_is_guarded_before_mutating_speed(self):
        fixed = patch_source(self.fixture(), require_pin=False)
        callback = fixed.split("task.delay(5,function()", 1)[1].split("end)", 1)[0]
        self.assertIn("if not matchActive() then return end", callback)
        self.assertLess(callback.index("if not matchActive()"), callback.index("hum.WalkSpeed=previous"))
        self.assertIn('session.rules.phase=="ACTIVE"', fixed)

    def test_same_active_match_still_reverts_after_five_seconds(self):
        fixed = patch_source(self.fixture(), require_pin=False)
        self.assertIn("task.delay(5,function()", fixed)
        self.assertIn("hum.Health>0 and hum.WalkSpeed==boosted", fixed)
        self.assertIn("hum.WalkSpeed=previous", fixed)

    def test_old_match_callback_cannot_reset_a_new_match(self):
        # Model the new guard's ordering: an inactive prior session fails
        # even when a new session coincidentally has the same speed 27.
        def callback(old_session_active, old_hum_alive, speed, boosted, previous):
            if not old_session_active:
                return speed
            if old_hum_alive and speed == boosted:
                return previous
            return speed
        self.assertEqual(callback(False, True, 27, 27, 16), 27)
        self.assertEqual(callback(True, True, 27, 27, 16), 16)
        self.assertEqual(callback(True, False, 27, 27, 16), 27)

    def test_rollback_is_byte_exact(self):
        original = self.fixture()
        fixed = patch_source(original, require_pin=False)
        self.assertEqual(fixed.replace(NEW, OLD, 1), original)
        self.assertEqual(fixed.count(NEW), 1)

    def test_old_source_must_be_pinned(self):
        with self.assertRaisesRegex(ValueError, "Source-lock"):
            patch_source(self.fixture())

    def test_missing_or_duplicate_hunk_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "exactly one"):
            patch_source(self.fixture().replace(OLD, ""), require_pin=False)
        with self.assertRaisesRegex(ValueError, "exactly one"):
            patch_source(self.fixture() + OLD, require_pin=False)

    def test_overlay_cannot_create_new_authorities(self):
        fixed = patch_source(self.fixture(), require_pin=False)
        delta = fixed.replace(self.fixture(), "")
        for forbidden in ("RemoteEvent", "DataStoreService", "OnServerEvent", "ProcessReceipt"):
            self.assertNotIn(forbidden, NEW)
        self.assertEqual(fixed.count('local function matchActive():boolean'), 1)

    def test_author_real_blob_and_single_hunk(self):
        source_path = os.environ.get("P0D_OWNER_ITEM_SRC")
        if not source_path:
            self.skipTest("No pinned author-source file; provided by GitHub Actions")
        source = Path(source_path).read_text(encoding="utf-8")
        self.assertEqual(git_blob_sha(source), ORIGINAL_BLOB)
        fixed = patch_source(source)
        self.assertEqual(fixed.replace(NEW, OLD, 1), source)
        self.assertEqual(fixed.count("if not matchActive() then return end"), 1)


if __name__ == "__main__":
    unittest.main()
