#!/usr/bin/env python3
import hashlib
import os
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from patch_nearest import (apply, git_blob, ORIGINAL_AI_GIT_BLOB,
                           original_member_overlay, MEMBER_AFTER, MEMBER_BEFORE,
                           START, END, REPLACEMENT)

AI_ORIGINAL=Path(os.environ.get("GQ_ORIGINAL_AI", "_author484/handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_BotActors.luau"))

class NearestEligibleHuman(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=AI_ORIGINAL.read_bytes()
        assert git_blob(cls.raw)==ORIGINAL_AI_GIT_BLOB
        cls.member=original_member_overlay(cls.raw)

    def test_source_lock_composition_and_exact_off(self):
        selected, off=apply(self.member)
        self.assertEqual(off,self.member)
        self.assertNotEqual(selected,off)
        self.assertEqual(selected.decode().replace(REPLACEMENT,
                         self.member.decode().split(START,1)[1].split(END,1)[0]
                         if False else self.original_span(),1),self.member.decode())
        self.assertEqual(selected.decode().count("targetHumanoid:TakeDamage(BOT_HERO_DAMAGE)"),1)
        self.assertEqual(selected.decode().count("nearestHumanoid:TakeDamage(BOT_HERO_DAMAGE)"),1)

    def original_span(self):
        s=self.member.decode()
        return s[s.index(START):s.index(END)]

    def test_expected_member_and_original_sha(self):
        self.assertEqual(git_blob(self.member.replace(MEMBER_AFTER.encode(),
                                       MEMBER_BEFORE.encode(),1)),ORIGINAL_AI_GIT_BLOB)

    def test_fail_closed_wrong_original(self):
        with self.assertRaises(ValueError):
            original_member_overlay(self.raw+b"-- unpinned\n")

    def test_fail_closed_other_derived_bot(self):
        with self.assertRaises(ValueError):
            apply(self.member+b"-- foreign patch\n")

    def test_fail_closed_missing_member_guard(self):
        with self.assertRaises(ValueError):
            apply(self.raw)

    def test_fail_closed_double_patch(self):
        on,_=apply(self.member)
        with self.assertRaises(ValueError):
            apply(on)

    def test_fail_closed_missing_pvp_hit(self):
        with self.assertRaises(ValueError):
            apply(self.member.replace(b"h:TakeDamage(BOT_HERO_DAMAGE)",b"h:TakeDamage(0)",1))

    def test_preserve_original_ai_duel_geometry_and_state(self):
        on,_=apply(self.member)
        s=on.decode()
        for anchor in ("for targetId,targetActor in pairs(bots)",
                       "targetHumanoid:TakeDamage(BOT_HERO_DAMAGE)",
                       "session.isCurrentHuman(player)",
                       "clearHeroStrike(actor,character",
                       'os.clock()>=(player:GetAttribute("EGGRUMBLE_StealthUntil") or 0)'):
            self.assertIn(anchor,s)
        self.assertLess(s.index("nearestHumanoid:TakeDamage"),s.index("for targetId,targetActor"))

if __name__=="__main__":
    unittest.main()
