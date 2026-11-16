#!/usr/bin/env python3
"""Synthetic 31-route selector-only tests, NOT an actual current RC31 build."""
from __future__ import annotations
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from select_current31 import COMBAT, COUNT, inspect, prepare, sha

DIR = Path(__file__).resolve().parent
ORIGINAL = Path("_gq_original482/handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_SevenRoleCombat.luau")


def fixture(base: Path):
    tree: dict = {"ServerScriptService": {}}
    original = ORIGINAL.read_bytes()
    combat = base / "EGGRUMBLE_SevenRoleCombat.luau"
    combat.write_bytes(original)
    tree["ServerScriptService"][COMBAT[-1]] = {"$path": combat.name}
    for i in range(COUNT - 1):
        key = "GQ618_SyntheticModule" + str(i).zfill(2)
        f = base / (key + ".luau")
        f.write_text("return {}\n")
        tree["ServerScriptService"][key] = {"$path": f.name}
    project = base / "SYNTHETIC31.project.json"
    project.write_text(json.dumps({"name": "GQ618-Synthetic-31-Not-Studio",
                                   "tree": tree}, indent=2) + "\n")
    return project, original


class Current31CandidateSelection(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gq618_31_")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.base, self.original = fixture(self.folder)
        self.runtime = DIR / "EGGRUMBLE_BeastEscort.luau"
        self.out = self.folder / "BEAST_SELECTED_SYNTHETIC31.project.json"

    def test_01_strict_31_unique_current_project(self):
        _, scripts = inspect(self.base)
        self.assertEqual(len(scripts), COUNT)
        self.assertIn(COMBAT, scripts)

    def test_02_select_only_one_live_combat(self):
        _, previous = inspect(self.base)
        prepare(self.base, self.out, self.runtime, sha(self.original))
        _, current = inspect(self.out)
        changed = [key for key in previous if previous[key].read_bytes() != current[key].read_bytes()]
        self.assertEqual(changed, [COMBAT])
        self.assertEqual(len(current), COUNT)
        self.assertEqual(self.out.parent, self.base.parent)
        self.assertIn("BeastEscort.begin(session,p,char,root,h,owner,",
                      current[COMBAT].read_text())
        receipt = json.loads((self.folder / "GQ618_CURRENT31_RECEIPT.json").read_text())
        self.assertEqual(receipt["source_count"], COUNT)
        self.assertTrue(receipt["original_30_scripts_byte_identical"])
        self.assertFalse(receipt["formal_rc_adopted"])

    def test_03_fail_closed_on_unpinned_sha(self):
        with self.assertRaisesRegex(ValueError, "RED_CURRENT_COMBAT_SOURCE_LOCK_SHA"):
            prepare(self.base, self.out, self.runtime, "0" * 64)

    def test_04_wrong_count_is_red(self):
        project = json.loads(self.base.read_text())
        project["tree"]["ServerScriptService"].pop("GQ618_SyntheticModule00")
        self.base.write_text(json.dumps(project))
        with self.assertRaisesRegex(ValueError, "RED_NOT_31_SINGLE_AUTHOR_NAMES"):
            inspect(self.base)

    def test_05_wrong_role_route_is_red(self):
        project = json.loads(self.base.read_text())
        project["tree"]["ServerScriptService"].pop(COMBAT[-1])
        project["tree"]["ServerScriptService"]["DifferentCombat"] = {"$path": "EGGRUMBLE_SevenRoleCombat.luau"}
        self.base.write_text(json.dumps(project))
        with self.assertRaisesRegex(ValueError, "RED_NO_SINGLE_COMBAT"):
            inspect(self.base)

    def test_06_refuse_mutating_base_project(self):
        with self.assertRaisesRegex(ValueError, "RED_NO_OVERWRITE_OR_FOREIGN_PROJECT"):
            prepare(self.base, self.base, self.runtime, sha(self.original))

    def test_07_missing_script_is_red(self):
        (self.folder / "GQ618_SyntheticModule00.luau").unlink()
        with self.assertRaises((ValueError, FileNotFoundError)):
            inspect(self.base)

    def test_08_duplicate_source_name_is_red(self):
        project = json.loads(self.base.read_text())
        project["tree"]["ServerScriptService"]["AnotherChild"] = project["tree"]["ServerScriptService"][COMBAT[-1]]
        self.base.write_text(json.dumps(project))
        with self.assertRaisesRegex(ValueError, "RED_NOT_31_SINGLE_AUTHOR_NAMES"):
            inspect(self.base)

    def test_09_refuse_output_overwrite(self):
        self.out.write_text("not available")
        with self.assertRaisesRegex(ValueError, "RED_NO_OVERWRITE_OR_FOREIGN_PROJECT"):
            prepare(self.base, self.out, self.runtime, sha(self.original))

if __name__ == "__main__":
    unittest.main()
