import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from compose_dash import AUTHOR_BLOB, AUTHOR_PATH, DASH_ANCHOR, compose, git_blob_sha

class SourceExactDashTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = Path(AUTHOR_PATH).read_bytes()

    def test_original_git_blob_pinned(self):
        self.assertEqual(git_blob_sha(self.raw), AUTHOR_BLOB)

    def test_flag_off_is_byte_identical(self):
        self.assertEqual(compose(self.raw, False), self.raw)

    def test_on_one_import_one_hook(self):
        patched = compose(self.raw, True).decode()
        self.assertEqual(patched.count("local DashLease=require"), 1)
        self.assertEqual(patched.count("DashLease.apply("), 1)
        self.assertEqual(patched.count("local Items={}"), 1)

    def test_preserves_other_item_authority(self):
        orig = self.raw.decode()
        patch = compose(self.raw, True).decode()
        for token in ('kind=="HEAL"', 'kind=="SHIELD"', 'consumed[id]=true',
                      'session.itemStop=function()', 'prompt.Triggered:Connect'):
            self.assertIn(token, orig)
            self.assertIn(token, patch)

    def test_exact_rollback_is_original_blob(self):
        self.assertEqual(git_blob_sha(compose(self.raw, False)), AUTHOR_BLOB)

    def test_mutation_of_original_is_rejected(self):
        with self.assertRaises(ValueError):
            compose(self.raw + b" ", True)

    def test_hunk_missing_is_rejected_even_in_exact_model(self):
        self.assertEqual(self.raw.decode().count(DASH_ANCHOR), 1)

if __name__ == "__main__":
    unittest.main()
