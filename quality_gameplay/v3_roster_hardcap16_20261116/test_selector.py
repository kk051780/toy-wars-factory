"""No-overlap original Luau two-guard mutation and byte-exact rollback tests."""
import importlib.util
import sys
import unittest
from pathlib import Path

target = Path(__file__).with_name("select_roster16.py")
spec = importlib.util.spec_from_file_location("roster_selector", target)
selector = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = selector
spec.loader.exec_module(selector)

SOURCE = """--!strict
local M={}
M.MAX_HERO_SLOTS=16
function M.makeRoster(limit:number)
 assert(limit>=2 and limit<=32,"invalid preview slot cap")
 return limit
end
function M.new(roster:any)
 assert(#roster>=2 and #roster<=32,"invalid roster size")
 return roster
end
return M
"""


class RosterTest(unittest.TestCase):
    def test_exactly_two_gameplay_guards_replaced(self):
        patch = selector.patch_source(SOURCE)
        self.assertEqual(patch.count("<=M.MAX_HERO_SLOTS"), 2)
        self.assertEqual(patch.count("<=32"), 0)

    def test_off_returns_byte_exact_original(self):
        patch = selector.patch_source(SOURCE)
        undo = patch.replace(selector.NEW[0], selector.OLD[0], 1)
        undo = undo.replace(selector.NEW[1], selector.OLD[1], 1)
        self.assertEqual(undo, SOURCE)

    def test_mutated_original_guard_rejected(self):
        altered = SOURCE.replace("limit<=32", "limit<=31")
        with self.assertRaisesRegex(ValueError, "two-hunk"):
            selector.patch_source(altered)

    def test_duplicate_guard_rejected(self):
        altered = SOURCE.replace(selector.OLD[0], selector.OLD[0]+"\n "+selector.OLD[0])
        with self.assertRaisesRegex(ValueError, "two-hunk"):
            selector.patch_source(altered)

    def test_not_silently_adding_another_module(self):
        p = selector.patch_source(SOURCE)
        self.assertEqual(p.count("local M={}"), 1)
        self.assertEqual(p.count("return M"), 1)
        self.assertEqual(p.count("function M."), SOURCE.count("function M."))

    def test_native_true_and_false_differential_in_generated_source(self):
        patched = selector.patch_source(SOURCE)
        old_case = selector.native_harness(SOURCE, True)
        new_case = selector.native_harness(patched, False)
        self.assertIn("canMake17==true", old_case)
        self.assertIn("canStart17==false", new_case)
        self.assertIn("ROSTER16_NATIVE_PASS", new_case)

    def test_source_cap_constant_must_exist(self):
        with self.assertRaisesRegex(ValueError, "invariant"):
            selector.patch_source(SOURCE.replace("M.MAX_HERO_SLOTS=16", "M.MAX_HERO_SLOTS=32"))


if __name__ == "__main__":
    unittest.main()
