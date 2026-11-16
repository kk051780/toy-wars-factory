"""Pure structural and reversible-authority checks; real source SHA tested by CI."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from compose import ANCHOR, REPLACEMENT, compose, git_blob_sha


class DepositRefreshOverlayTest(unittest.TestCase):
    def setUp(self):
        self.source = (
            "local unrelated='FIELD/CHARACTER/NEUTRAL/ITEM/LOBBY/BALANCE'\n"
            "local session={}\n"
            "  prompt(deposit,\"卵を納入\",\"自分の城\",function(p)\n"
            "   if tostring(p.UserId)~=entry.id or not session.rules then return end\n"
            "   local c=session.rules.castles[entry.id]\n"
            + ANCHOR +
            "  end)\n"
            "local unrelated_after=true\n"
        ).encode()

    def test_on_changes_one_callback(self):
        out = compose(self.source, verify_blob=False)
        self.assertNotEqual(out, self.source)
        self.assertEqual(out.count(REPLACEMENT.encode()), 1)
        self.assertNotIn(ANCHOR.encode(), out)

    def test_rollback_off_byte_identical(self):
        self.assertEqual(compose(self.source, on=False, verify_blob=False), self.source)

    def test_off_does_not_allow_other_mutations(self):
        self.assertEqual(compose(b"random unknown bytes", on=False, verify_blob=False), b"random unknown bytes")

    def test_default_sha_lock_refuses_fixture(self):
        with self.assertRaisesRegex(ValueError, "ORIGINAL_HOST_SOURCE_DRIFT"):
            compose(self.source)

    def test_original_unchanged(self):
        before = self.source
        compose(self.source, verify_blob=False)
        self.assertEqual(before, self.source)

    def test_drift_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "ORIGINAL_HOST_SOURCE_DRIFT"):
            compose(self.source + b"-- drift")

    def test_duplicate_deposit_anchor_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "UNIQUE_DEPOSIT_CALLBACK"):
            compose(self.source + ANCHOR.encode(), verify_blob=False)

    def test_missing_anchor_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "UNIQUE_DEPOSIT_CALLBACK"):
            compose(self.source.replace(ANCHOR.encode(), b""), verify_blob=False)

    def test_double_apply_fails_closed(self):
        on = compose(self.source, verify_blob=False)
        with self.assertRaisesRegex(ValueError, "UNIQUE_DEPOSIT_CALLBACK"):
            compose(on, verify_blob=False)

    def test_unrelated_source_byte_exact(self):
        after = compose(self.source, verify_blob=False)
        self.assertEqual(after, self.source.replace(ANCHOR.encode(), REPLACEMENT.encode(), 1))

    def test_success_only_refresh_is_conditional(self):
        self.assertIn("if ok then session.refresh() end", REPLACEMENT)
        self.assertEqual(REPLACEMENT.count("session.refresh()"), 1)

    def test_git_blob_hash_format(self):
        self.assertEqual(git_blob_sha(b""), "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")


if __name__ == "__main__":
    unittest.main()
