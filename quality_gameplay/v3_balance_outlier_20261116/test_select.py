"""Exact-source guard and mutation checks, local Python stdlib only."""
import os
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent))
from select_balance import ORIGINAL_GIT_BLOB, EDITS, git_blob_sha, select

class SourceSelectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = os.environ["P0D_ORIGINAL_BALANCE"]
        cls.source = Path(path).read_bytes()

    def test_original_blob_is_pinned(self):
        self.assertEqual(git_blob_sha(self.source), ORIGINAL_GIT_BLOB)

    def test_patch_only_three_anchors(self):
        selected = select(self.source)
        self.assertNotEqual(selected, self.source)
        expected = self.source.decode()
        for old, new in EDITS:
            self.assertEqual(expected.count(old), 1)
            expected = expected.replace(old, new, 1)
        self.assertEqual(selected, expected.encode())

    def test_fail_closed_on_drift(self):
        mutated = self.source.replace(b"B.MAX_SECONDS", b"1300", 1)
        with self.assertRaisesRegex(ValueError, "RED"):
            select(mutated)

    def test_original_off_is_byte_exact(self):
        before = self.source
        _ = select(before)
        self.assertEqual(self.source, before)
        self.assertEqual(git_blob_sha(before), ORIGINAL_GIT_BLOB)

if __name__ == "__main__":
    unittest.main()
