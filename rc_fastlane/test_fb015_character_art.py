"""FB015 PREP source verification. Not an engine screenshot or art acceptance."""
import tempfile
import unittest
from pathlib import Path

from rc_fastlane import apply_fb015_character_art as art


class FB015ArtSource(unittest.TestCase):
    def test_exact_source_and_no_game_authority(self):
        source=art.source_safety()
        self.assertEqual(art.gitblob(source), art.BLOB)

    def test_disabling_keeps_even_unprepared_dist_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            sentinel=root/"unchanged"
            sentinel.write_bytes(b"FB015_NO_WRITE")
            self.assertFalse(art.apply(root, False))
            self.assertEqual(sentinel.read_bytes(), b"FB015_NO_WRITE")

    def test_reject_wrong_or_incomplete_game_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"src").mkdir()
            (root/"src"/"server").mkdir()
            (root/"src"/"server"/"Game.server.luau").write_text("mock", "utf8")
            with self.assertRaises(AssertionError):
                art.apply(root, True)

    def test_stage_has_multiple_distinct_character_kinds(self):
        s=art.source_safety().decode("utf8")
        for name in ("Gorogan_ServerRig", "ObsidianChestPlate",
                     "RuneEye_", "ObsidianBackSpike_", "RUNESTONE_TITAN"):
            self.assertIn(name,s)
        self.assertIn("CanQuery = false",s)
        self.assertNotIn("MUSOU_MINION_",s)
        self.assertNotIn("MUSOU_ELITE_TELEGRAPH",s)
        self.assertIn("humanoid.HealthChanged:Connect",s)
        self.assertIn("MAX_DECOR_PARTS = 64",s)
        self.assertNotIn("FireServer(",s)


if __name__ == "__main__":
    unittest.main()
