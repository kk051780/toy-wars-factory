#!/usr/bin/env python3
"""Negative and reversible-source tests for exactly one Combat source delta."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent))
from compose import (
    AUTHOR_BLOB, CAST_OLD, COMBAT_NAME, HEAL_OLD, HELPER_ANCHOR,
    HIT_OLD, STATUS_OLD, git_blob, one, patch, run, undo,
)

ORIGINAL = (
    "--!strict\nlocal HeroCombat={}\n"
    + HELPER_ANCHOR + "\n" + HIT_OLD + "  return 0\nend\n"
    + "local function healAllies()\n" + HEAL_OLD + " end\n"
    + "local function secondaryEffect()\n" + STATUS_OLD + " end\n"
    + "local function execute(session:any,p:Player)\n" + CAST_OLD + "\nend\n"
)

class HumanCombatMembershipQA(unittest.TestCase):
    def test_single_original_four_replacements_and_exact_rollback(self):
        fixed = patch(ORIGINAL)
        self.assertEqual(undo(fixed), ORIGINAL)
        self.assertEqual(fixed.count("currentHumanMember(session,"), 4)
        self.assertEqual(fixed.count("local function currentHumanMember("), 1)
        self.assertIn("and currentHumanMember(session,enemyPlayer)", fixed)
        self.assertIn("and currentHumanMember(session,targetPlayer)", fixed)
        self.assertIn("and currentHumanMember(session,other)", fixed)
        self.assertIn("if not currentHumanMember(session,p) then return end", fixed)

    def test_no_duplicate_patch(self):
        fixed = patch(ORIGINAL)
        with self.assertRaises(ValueError):
            patch(fixed)

    def test_reject_stale_or_double_anchors(self):
        for old in (HIT_OLD, STATUS_OLD, HEAL_OLD, CAST_OLD):
            with self.subTest(needle=old[:30]):
                with self.assertRaises(ValueError):
                    patch(ORIGINAL.replace(old, "REMOVED"))
        with self.assertRaises(ValueError):
            patch(ORIGINAL.replace(HIT_OLD, HIT_OLD + HIT_OLD))

    def test_reject_non_strict_source(self):
        with self.assertRaises(ValueError):
            patch(ORIGINAL.replace("--!strict\n", ""))

    def test_guard_fails_closed_for_missing_or_bad_callback(self):
        text = patch(ORIGINAL)
        self.assertIn('if type(verify)~="function" then return false end', text)
        self.assertIn("local ok,allowed=pcall(verify,player)", text)
        self.assertIn("return ok and allowed==true", text)
        self.assertNotIn('session.isCurrentHuman=function', text)

    def test_existing_stealth_patch_can_stay_in_single_hit_branch(self):
        """Reuse #529 exact callsite, not a competing PvP stealth implementation."""
        existing = ORIGINAL.replace(
            HIT_OLD, HIT_OLD + "   and humanCombatTargetable(enemyState,enemyPlayer)\n"
        ).replace(
            STATUS_OLD, STATUS_OLD + "   and humanCombatTargetable(target,targetPlayer)\n"
        )
        fixed = patch(existing)
        self.assertEqual(undo(fixed), existing)
        self.assertEqual(fixed.count("humanCombatTargetable("), 2)

    def test_real_482_original_blob_and_recovery(self):
        source_file = os.getenv("GQ_ORIGINAL_COMBAT")
        if not source_file:
            self.skipTest("pinned author Combat provided in Actions")
        original_path = Path(source_file)
        raw = original_path.read_bytes()
        self.assertEqual(git_blob(raw), AUTHOR_BLOB)
        with tempfile.TemporaryDirectory() as tmp:
            report = run(original_path, Path(tmp))
            self.assertTrue(report["original_recovered_by_off"])
            fixed = (Path(tmp) / COMBAT_NAME).read_text()
            self.assertEqual(undo(fixed).encode(), raw)
            self.assertFalse(report["official_rc_adopted"])
            self.assertEqual(report["changed_gameplay_files"], [COMBAT_NAME])

    def test_lock_rejects_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "fake.luau"
            p.write_text(ORIGINAL)
            with self.assertRaisesRegex(ValueError, "blob drift"):
                run(p, Path(tmp) / "out")

if __name__ == "__main__":
    unittest.main()
