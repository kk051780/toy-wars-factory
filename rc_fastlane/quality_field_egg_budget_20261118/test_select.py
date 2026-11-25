#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from select_current import CONST,BEFORE,AFTER,patch,unpatch,native

class EggBudgetSelectionTests(unittest.TestCase):
    def setUp(self):
        self.original = (
          "--!strict\nlocal M={}\n"
          + CONST
          + "M.MAX_HERO_SLOTS=16\n"
          + "function M.new(mode,roster,initialFieldEggs)\n"
          + " local m={fieldEggs=initialFieldEggs or M.DEFAULT_FIELD_EGGS}\n"
          + BEFORE+"\n"
          + " return m\nend\nreturn M\n"
        )

    def test_inverse_is_exact(self):
        selected=patch(self.original)
        self.assertEqual(unpatch(selected),self.original)
        self.assertIn(AFTER,selected)
        self.assertEqual(selected.count("M.MAX_FIELD_EGGS=512"),1)

    def test_double_patch_is_red(self):
        with self.assertRaises(ValueError):
            patch(patch(self.original))

    def test_unpatch_original_is_red(self):
        with self.assertRaises(ValueError):
            unpatch(self.original)

    def test_source_anchor_drift_is_red(self):
        with self.assertRaises(ValueError):
            patch(self.original.replace('"invalid egg count"','"drifted egg count"'))
        with self.assertRaises(ValueError):
            patch(self.original.replace(CONST,"M.DEFAULT_FIELD_EGGS=23\n"))

    def test_native_uses_exact_real_source(self):
        good=native(patch(self.original))
        bad=native(self.original)
        self.assertIn("mustReject(\"OVER_LIMIT_513\",513)",good)
        self.assertNotIn("M.MAX_FIELD_EGGS=512",bad)

if __name__=="__main__":
    unittest.main()
