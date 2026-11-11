import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools/trap_respawn_native.py"
spec = importlib.util.spec_from_file_location("trap_respawn_native", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class SourceLockedTrapAudit(unittest.TestCase):
    def test_real_blob_sha_fixture(self):
        self.assertEqual(mod.blob_sha(b"abc"),
                         "f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f")

    def test_exact_replace(self):
        self.assertEqual(mod.exact_replace("prefix KEY suffix", "KEY", "X", "key"),
                         "prefix X suffix")

    def test_missing_anchor_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "NONUNIQUE_OR_ABSENT"):
            mod.exact_replace("abc", "not here", "x", "missing")

    def test_duplicate_anchor_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "NONUNIQUE_OR_ABSENT"):
            mod.exact_replace("abc abc", "abc", "x", "duplicate")

    def test_fixed_source_pins(self):
        self.assertEqual(len(mod.RC), 40)
        self.assertEqual(len(mod.BLOBS), 6)
        for sha in mod.BLOBS.values():
            self.assertRegex(sha, r"^[a-f0-9]{40}$")

    def test_safety_mutants_unique(self):
        names = [m[0] for m in mod.MUTANTS]
        self.assertEqual(len(set(names)), 3)
        self.assertEqual(len(mod.MUTANTS), 3)
        self.assertIn("stale_seq_rejected_even_after_cooldown", mod.EXTRA_LUAU)
        self.assertIn("owner_exit_removes_trap_while_active", mod.EXTRA_LUAU)
        self.assertIn("old_character_slow_record_cleaned", mod.EXTRA_LUAU)

    def test_source_extension_is_not_production_change(self):
        self.assertIn("Players.PlayerAdded:Fire(pBlueBackup)", mod.EXTRA_LUAU)
        self.assertNotIn("DataStore", mod.EXTRA_LUAU)
        self.assertNotIn("HttpService", mod.EXTRA_LUAU)
        self.assertNotIn("FireServer", mod.EXTRA_LUAU)

    def test_gameplay_root_exact_only(self):
        self.assertEqual(mod.ROOT, "releases/P0D_S1_KIDS_RC01/")
        self.assertEqual(mod.RC, "1263a03701211a652b99b91d2339575dc8104eff")


if __name__ == "__main__":
    unittest.main()
