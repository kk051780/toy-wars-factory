#!/usr/bin/env python3
"""Fail-closed source-mutation/ownership tests. NOT a Roblox runtime simulation."""
from __future__ import annotations
import difflib
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
LANE = HERE.parent
sys.path.insert(0, str(LANE / "tools"))
from compose import AUTHOR_REL, AUTHOR_BLOB, ANCHOR, PATCH, compose, git_blob_sha  # noqa: E402

ROOT = LANE.parents[1]
SOURCE = ROOT / AUTHOR_REL

class DeadCasterFence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = SOURCE.read_bytes()
        cls.patched = compose(cls.original)

    def test_01_original_pinned(self):
        self.assertEqual(git_blob_sha(self.original), AUTHOR_BLOB)

    def test_02_off_is_byte_identical(self):
        self.assertEqual(compose(self.original, enabled=False), self.original)

    def test_03_one_exact_insertion(self):
        before = self.original.decode()
        after = self.patched.decode()
        self.assertEqual(before.count(ANCHOR), 1)
        self.assertEqual(after.count(PATCH), 1)
        self.assertEqual(after.replace(PATCH, ANCHOR), before)

    def test_04_inserted_inside_single_execute(self):
        text = self.patched.decode()
        self.assertEqual(text.count("GQ_DEAD_CASTER_FENCE:"), 1)
        self.assertLess(text.index("local function execute"), text.index("GQ_DEAD_CASTER_FENCE:"))
        self.assertLess(text.index("GQ_DEAD_CASTER_FENCE:"), text.index("perPlayer[key]=now"))

    def test_05_precedes_cast_signature_and_all_skill_branches(self):
        text = self.patched.decode()
        offset = text.index("GQ_DEAD_CASTER_FENCE:")
        for marker in ['EGGRUMBLE_SkillCastSignature', 'if role=="WARRIOR"', 'elseif role=="MAGE"',
                       'elseif role=="NINJA"', 'elseif role=="TRAPPER"', 'elseif role=="BUILDER"',
                       'elseif role=="BEAST"', 'elseif role=="ZOMBIE"']:
            self.assertLess(offset, text.index(marker, offset))

    def test_06_healing_and_blast_existing_authority_unchanged(self):
        text = self.patched.decode()
        self.assertIn("else healAllies(session,p,root);blast() end", text)
        self.assertIn('if session.rules.phase~="ACTIVE" then return end', text)
        self.assertIn('if p:GetAttribute("EGGRUMBLE_Eliminated")==true then return end', text)
        self.assertIn('if p:GetAttribute("EGGRUMBLE_Role")~=role then return end', text)

    def test_07_reject_any_unpinned_base_even_if_anchor_same(self):
        mutant = self.original.replace(b"EGGRUMBLE V3:", b"EGGRUMBLE V4:", 1)
        with self.assertRaisesRegex(ValueError, "RED_SOURCE_LOCK"):
            compose(mutant)

    def test_08_reject_already_patched_source(self):
        with self.assertRaisesRegex(ValueError, "RED_SOURCE_LOCK"):
            compose(self.patched)

    def test_09_reject_corrupted_source(self):
        with self.assertRaises(ValueError):
            compose(self.original[:-1])

    def test_10_stays_single_combat(self):
        text = self.patched.decode()
        self.assertEqual(text.count("local function execute(session:any,p:Player,role:string,slot:string)"), 1)
        self.assertEqual(text.count("return HeroCombat"), 1)

    def test_11_scope_no_other_source_patch(self):
        lines = list(difflib.unified_diff(self.original.decode().splitlines(),
                                          self.patched.decode().splitlines()))
        additions = [s for s in lines if s.startswith("+") and not s.startswith("+++")]
        removals = [s for s in lines if s.startswith("-") and not s.startswith("---")]
        self.assertEqual(len(additions), 2)
        self.assertEqual(removals, [])
        self.assertTrue(all("GQ_DEAD_CASTER_FENCE" in x or "if h.Health<=0" in x for x in additions))

    def test_12_living_only_and_down_state(self):
        gate = self.patched.decode().split("GQ_DEAD_CASTER_FENCE:", 1)[1].split("\n", 1)[1]
        self.assertIn('h.Health<=0', gate)
        self.assertIn('char:GetAttribute("EGGRUMBLE_Downed")==true', gate)
        self.assertIn('then return end', gate)

if __name__ == "__main__":
    unittest.main(verbosity=2)
