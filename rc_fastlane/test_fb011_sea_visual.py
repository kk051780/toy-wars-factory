"""Source-only FB-011 sea visual PREP gates; never claim Studio FUN PASS."""
import tempfile
import unittest
from pathlib import Path

from rc_fastlane import apply_fb011_sea_visual as feature


class SeaVisualSourceContract(unittest.TestCase):
    def test_authored_exact_gitblob_and_no_authority(self):
        body = feature.verify_source()
        self.assertEqual(feature.gitblob(body), feature.SOURCE_BLOB)

    def test_off_is_byte_identical_and_needs_no_source_dir(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = root / "untouched.txt"
            state.write_text("unchanged", encoding="utf8")
            self.assertIs(feature.apply(root, False), False)
            self.assertEqual(state.read_text("utf8"), "unchanged")
            self.assertEqual([p.name for p in root.iterdir()], ["untouched.txt"])

    def test_enabled_rejects_unpinned_or_missing_game(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "src").mkdir()
            (root / "src" / "Game.server.luau").write_text("invalid", "utf8")
            with self.assertRaises(AssertionError):
                feature.apply(root, True)

    def test_scene_has_distinct_water_and_original_route_preserved(self):
        body = feature.verify_source().decode("utf8")
        self.assertIn("Workspace.Terrain:FillBlock(", body)
        self.assertIn("Enum.Material.Water", body)
        self.assertIn('"SEA_LOW_CAUSEWAY"', body)
        self.assertIn("CanCollide = false", body)
        self.assertNotIn("Instance.new(\"RemoteEvent\")", body)
        self.assertIn('"NOT_TESTED"', body)


if __name__ == "__main__":
    unittest.main()
