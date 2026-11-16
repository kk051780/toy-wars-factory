"""GQ V3: source-safe queue timer overlay and repeated entry regression."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from compose import BEFORE, AFTER, MARKER, compose, blob_sha

def fixture() -> bytes:
    return ("local abc=1\n" + BEFORE + "\nlocal xyz=2\n").encode()

class QueueCountdownTests(unittest.TestCase):
    def test_one_original_anchor(self):
        out = compose(fixture(), verify=False)
        self.assertEqual(out.decode().count(MARKER), 1)
        self.assertEqual(out.decode().replace(AFTER, BEFORE), fixture().decode())
    def test_off_exact_rollback(self):
        src = fixture()
        self.assertIs(compose(src, enabled=False, verify=False), src)
        self.assertEqual(compose(src, enabled=False, verify=False), src)
    def test_reject_source_drift(self):
        with self.assertRaisesRegex(ValueError, "drift"):
            compose(fixture(), enabled=True, verify=True)
    def test_reject_mutated_anchor(self):
        with self.assertRaisesRegex(ValueError, "anchor"):
            compose(fixture().replace(b"table.find(q,p)", b"table.find(q,other)"), verify=False)
    def test_reject_duplicate_anchor(self):
        with self.assertRaisesRegex(ValueError, "anchor"):
            compose(fixture()+fixture(), verify=False)
    def test_reject_double_apply(self):
        with self.assertRaisesRegex(ValueError, "anchor"):
            compose(compose(fixture(), verify=False), verify=False)
    def test_no_unrelated_source_write(self):
        out = compose(fixture(), verify=False)
        self.assertTrue(out.startswith(b"local abc=1\n"))
        self.assertTrue(out.endswith(b"\nlocal xyz=2\n"))
    def test_only_empty_queue_revokes(self):
        self.assertIn("if #q==0 then queueEpoch[mode]+=1 end", AFTER)
        self.assertIn("if idx then", AFTER)
        self.assertIn("table.remove(q,idx)", AFTER)
    def test_pinned_blob_contract(self):
        self.assertEqual(len(blob_sha(fixture())), 40)

if __name__ == "__main__":
    unittest.main()
