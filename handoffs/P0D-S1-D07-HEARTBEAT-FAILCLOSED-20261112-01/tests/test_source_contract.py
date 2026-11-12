"""Source-locked offline contract checks. NOT native Luau/Roblox Studio execution."""
from __future__ import annotations

import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "candidate/src/server/S1CanonicalRoundHost.luau"
ORIGINAL_GIT_BLOB = "61501c982619e54db6a09cf11b188ef872c1666e"
OLD = 'if not good or reason == "HEARTBEAT_FAIL_CLOSED" then'
NEW = ('if not good or reason ~= nil\n'
       '            or (cmd ~= nil and type(cmd) ~= "table") then')


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\\x00".decode("unicode_escape").encode() + data).hexdigest()


def rejected(ok: bool, cmd: object | None, reason: str | None) -> bool:
    """Python truth-table reference for the 1-guard Luau contract; not a Lua VM."""
    return (not ok) or reason is not None or (cmd is not None and not isinstance(cmd, dict))


class HeartbeatGuardSourceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = CANDIDATE.read_text(encoding="utf-8")

    def test_source_present(self):
        self.assertTrue(self.candidate.startswith("--!strict"))

    def test_exact_single_new_guard(self):
        self.assertEqual(self.candidate.count(NEW), 1)
        self.assertNotIn(OLD, self.candidate)

    def test_reversible_one_guard_only_against_git_blob(self):
        before = self.candidate.replace(NEW, OLD)
        self.assertEqual(git_blob(before.encode("utf-8")), ORIGINAL_GIT_BLOB)

    def test_guard_covers_existing_combined_heartbeat_call(self):
        self.assertIn("local good, cmd, reason = pcall(function() return self.combined:heartbeat() end)", self.candidate)
        self.assertIn("if self.combinedActive and not self.closed then", self.candidate)

    def test_error_branch_stops_existing_host(self):
        after = self.candidate.split(NEW, 1)[1][:230]
        self.assertIn('self:stop("D07_HEARTBEAT_FAILED")', after)
        self.assertIn('return false, reason or "D07_HEARTBEAT_FAILED"', after)

    def test_clean_idle_result_is_accepted(self):
        self.assertFalse(rejected(True, None, None))

    def test_real_move_command_is_accepted(self):
        self.assertFalse(rejected(True, {"kind": "MOVE"}, None))

    def test_real_end_command_is_accepted(self):
        self.assertFalse(rejected(True, {"kind": "END"}, None))

    def test_return_inactive_fails_closed(self):
        self.assertTrue(rejected(True, None, "INACTIVE"))
        self.assertFalse("INACTIVE" == "HEARTBEAT_FAIL_CLOSED")  # old guard omitted it

    def test_return_reentrant_fails_closed(self):
        self.assertTrue(rejected(True, None, "REENTRANT_HEARTBEAT"))

    def test_return_actual_fatal_fails_closed(self):
        self.assertTrue(rejected(True, None, "HEARTBEAT_FAIL_CLOSED"))

    def test_invalid_non_table_command_fails_closed(self):
        self.assertTrue(rejected(True, False, None))
        self.assertTrue(rejected(True, "MOVE", None))

    def test_error_with_command_fails_closed(self):
        self.assertTrue(rejected(True, {"kind": "MOVE"}, "SOME_ERROR"))

    def test_pcall_exception_fails_closed(self):
        self.assertTrue(rejected(False, "exception", None))


if __name__ == "__main__":
    unittest.main()
