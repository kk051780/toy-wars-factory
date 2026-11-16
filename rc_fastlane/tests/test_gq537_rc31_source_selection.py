#!/usr/bin/env python3
"""Negative and exact rollback tests for original #537 in canonical V3 31-Host."""
import importlib.util
import unittest
from pathlib import Path
MODULE=Path(__file__).resolve().parents[1]/"select_gq537_original_castle_deposit.py"
spec=importlib.util.spec_from_file_location("selector537",MODULE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class OriginalAuthorReuseTests(unittest.TestCase):
    def source(self):
        return (
            "--!strict\n"
            "session.isCurrentHuman=function(p) return true end\n"
            "gqDualBudget=GQDualBudget.new(123)\n"
            "local function q() RoundReplay.leaveWaitingQueue(1) end\n"
            "local function q2() RoundReplay.leaveWaitingQueue(2) end\n"
            "local function go() RoundReplay.canStartCountdown(1) end\n"
            "local function hit() Rules.damageCastle(1) end\n"
            "local function steal() Rules.takeEggs(1) end\n"
            "local function field() Rules.takeFieldEgg(1) end\n"
            "local function carrier() session.dropCarrierEggs(1) end\n"
            +mod.ANCHOR+"return true\n")
    def test_real_callback_one_select(self):
        output=mod.patch_host(self.source())
        self.assertIn("if ok then session.refresh() end",output)
        self.assertEqual(output.count("Rules.depositEggs("),1)
    def test_byte_exact_rollback(self):
        s=self.source()
        patched=mod.patch_host(s)
        self.assertEqual(patched.replace(mod.REPLACEMENT,mod.ANCHOR,1),s)
    def test_missing_original_refused(self):
        with self.assertRaisesRegex(ValueError,"ANCHOR"):
            mod.patch_host(self.source().replace(mod.ANCHOR,""))
    def test_duplicate_source_refused(self):
        with self.assertRaisesRegex(ValueError,"ANCHOR"):
            mod.patch_host(self.source()+mod.ANCHOR)
    def test_double_install_refused(self):
        with self.assertRaisesRegex(ValueError,"ANCHOR"):
            mod.patch_host(mod.patch_host(self.source()))
    def test_missing_current_human_refused(self):
        with self.assertRaisesRegex(ValueError,"CONTROL"):
            mod.patch_host(self.source().replace("session.isCurrentHuman=function","session.unknown=function"))
    def test_queue_lifecycle_must_stay_2_callsites(self):
        with self.assertRaisesRegex(ValueError,"CONTROL"):
            mod.patch_host(self.source().replace("RoundReplay.leaveWaitingQueue(2)","other(2)"))
    def test_shared_neutral_budget_required(self):
        with self.assertRaisesRegex(ValueError,"CONTROL"):
            mod.patch_host(self.source().replace("gqDualBudget=GQDualBudget.new(","gqDualBudget=Other.new("))
    def test_same_host_no_score_or_game_writes(self):
        s=self.source()
        a=mod.patch_host(s)
        self.assertEqual(a.count("Rules.damageCastle("),s.count("Rules.damageCastle("))
        self.assertEqual(a.count("Rules.takeEggs("),s.count("Rules.takeEggs("))
        self.assertEqual(a.count("Rules.takeFieldEgg("),s.count("Rules.takeFieldEgg("))
    def test_source_has_pinned_author_git_blobs(self):
        self.assertEqual(len(mod.ORIGINAL_482_HOST_BLOB),40)
        self.assertEqual(len(mod.AUTHOR_537_COMPOSER_BLOB),40)
        self.assertNotEqual(mod.ORIGINAL_482_HOST_BLOB,mod.AUTHOR_537_COMPOSER_BLOB)

if __name__=="__main__":
    unittest.main()
