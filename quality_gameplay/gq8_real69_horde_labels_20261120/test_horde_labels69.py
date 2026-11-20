#!/usr/bin/env python3
"""Run with: python -m unittest discover -s DIR -p 'test_*.py'"""
import unittest
import os
from pathlib import Path
from patch_horde_labels69 import ANCHOR, MARKER, REPLACEMENT, patch, sha, verified_package


class HordeVisualFixTests(unittest.TestCase):
    def setUp(self):
        value = os.getenv("EGGRUMBLE_REAL69_ZIP", "")
        self.path = Path(value) if value else None

    def test_no_extra_gui_or_authority_and_source_marker(self):
        self.assertEqual(REPLACEMENT.count(MARKER), 1)
        self.assertIn("h.NameDisplayDistance=0", REPLACEMENT)
        self.assertIn("h.HealthDisplayDistance=22", REPLACEMENT)
        self.assertNotIn('Instance.new("BillboardGui")', REPLACEMENT)
        self.assertNotIn("FireServer(", REPLACEMENT)
        self.assertNotIn("TakeDamage(", REPLACEMENT)

    def test_real69_artifact_source_inverse_and_negative(self):
        if not self.path or not self.path.is_file():
            self.skipTest("set EGGRUMBLE_REAL69_ZIP to official same-head ZIP")
        raw, head = verified_package(self.path)
        self.assertEqual(len(head), 40)
        updated = patch(raw)
        self.assertEqual(updated.count(MARKER.encode()), 1)
        self.assertEqual(updated.replace(REPLACEMENT.encode(), ANCHOR.encode()), raw)
        self.assertNotEqual(sha(updated), sha(raw))
        for changed in (raw + b" ", raw.replace(ANCHOR.encode(), b""), updated):
            with self.assertRaises(ValueError):
                patch(changed)


if __name__ == "__main__":
    unittest.main()
