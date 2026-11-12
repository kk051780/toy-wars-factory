import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / "tools/run_v6_game_map_trap.py"
spec = importlib.util.spec_from_file_location("real_map_v6", PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class NativeSourceCompositionContracts(unittest.TestCase):
    def test_git_blob_reference(self):
        self.assertEqual(m.blob_sha(b"abc"), "f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f")

    def test_real_v6_rc_pin(self):
        self.assertEqual(m.OFFICIAL, "1263a03701211a652b99b91d2339575dc8104eff")

    def test_previous_real_map_test_is_frozen(self):
        self.assertEqual(m.UPSTREAM_QA, "b2ae7828b641ab5acccc279117d36c6c413b543b")
        self.assertRegex(m.UPSTREAM_SHA, r"^[a-f0-9]{40}$")

    def test_exactly_six_actual_sources(self):
        self.assertEqual(len(m.BLOBS), 6)
        self.assertIn("src/server/Game.server.luau", m.BLOBS)
        self.assertIn("src/server/MapBuilder.luau", m.BLOBS)
        self.assertIn("src/server/S1TrapRules.luau", m.BLOBS)

    def test_require_injection_strict(self):
        self.assertEqual(m.unique("old endpoint", "old", "new", "test"), "new endpoint")

    def test_missing_require_anchor_fails(self):
        with self.assertRaisesRegex(RuntimeError, "ANCHOR_NOT_EXACTLY_ONCE"):
            m.unique("one", "other", "new", "negative")

    def test_duplicate_require_anchor_fails(self):
        with self.assertRaisesRegex(RuntimeError, "ANCHOR_NOT_EXACTLY_ONCE"):
            m.unique("one one", "one", "new", "negative")

    def test_extra_real_world_trap_assertions(self):
        for k in ("v6_real_map_trap_folder", "v6_egg_clearance_uses_real_map",
                  "v6_real_map_enemy_slow", "v6_real_map_slow_restored"):
            self.assertIn(k, m.EXTRA)

    def test_mutants_nonduplicate(self):
        self.assertEqual(len(m.MUTATIONS), 5)
        self.assertEqual(len({x[0] for x in m.MUTATIONS}), 5)

    def test_nobody_may_publish_from_this_pack(self):
        self.assertNotIn("DataStoreService", m.EXTRA)
        self.assertNotIn("game:BindToClose", m.EXTRA)
        self.assertNotIn("FireServer(", m.EXTRA)


if __name__ == "__main__":
    unittest.main()
