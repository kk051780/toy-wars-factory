#!/usr/bin/env python3
"""Fail closed on unwanted second authors, stale avatars, double-selection or mutation."""
import importlib.machinery
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
import select_original_carrier551 as s

AUTHOR=Path("_gq551_original_carrier/quality_gameplay/v3_carrier_stale_avatar_20261116/tools/compose.py")

class ExistingOriginal551Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.author=s.load_author(AUTHOR)
        cls.orig=cls.author.SOURCE.read_text(encoding="utf-8")
    def test_original_source_pinned(self):
        self.assertEqual(s.blob(self.orig.encode()),s.ORIGINAL_HOST_BLOB)
    def test_exact_one_author_guard(self):
        old,new=s.guards(self.author)
        self.assertIn("joined[player.UserId]~=mode",old)
        self.assertIn("player.Character~=character",new)
    def test_original_author_one_hunk_reversible(self):
        old,new=s.guards(self.author)
        after=self.author.patch(self.orig)
        self.assertEqual(after.replace(new,old,1),self.orig)
    def test_disallow_bad_author_script(self):
        with self.assertRaisesRegex(ValueError,"RED_GQ551_PINNED_AUTHOR_COMPOSER_DRIFT"):
            s.load_author(Path(__file__))
    def test_no_second_callback(self):
        with self.assertRaisesRegex(ValueError,"RED_HUMANOID_DIED_CALLBACK_DRIFT"):
            s.body(self.orig+self.orig)
    def test_bad_old_guard_rejected(self):
        old,_=s.guards(self.author)
        with self.assertRaisesRegex(ValueError,"RED_CURRENT_HOST_GUARD_DRIFT"):
            s.patch(self.orig.replace(old,"      if false then return end"),self.author)
    def test_already_adopted_rejected(self):
        with self.assertRaisesRegex(ValueError,"RED_ALREADY_ADOPTED"):
            s.patch(self.author.patch(self.orig),self.author)
    def test_previous_round_isolation_is_real(self):
        _,new=s.guards(self.author)
        for mark in ("sessions[mode]~=session","player.Character~=character",'session.rules.phase~="ACTIVE"'):
            self.assertIn(mark,new)
    def test_no_authoritative_parallel_game(self):
        self.assertEqual(self.orig.count("session.dropCarrierEggs(tostring(player.UserId),"),1)
    def test_only_exact_callback_guard(self):
        old,new=s.guards(self.author)
        self.assertEqual(self.author.patch(self.orig).replace(new,old,1),self.orig)

if __name__=="__main__": unittest.main()
