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


    @staticmethod
    def _mock_assembled(tmp: Path, with_minion: bool) -> Path:
        src = tmp / "src"
        server = src / "server"
        server.mkdir(parents=True)
        entries = {
            "server/Game.server.luau": b"-- original Game single authority",
            "server/MusouHorde.luau": b"-- original neutral Horde",
            "server/GoroganRigDriver.luau": b"-- original giant rig",
            "client/HUD.client.luau": b"-- original HUD",
        }
        if with_minion:
            # The pinned #374 blob must be exact; an invented replacement must
            # be refused before any source/lock/project writes.
            entries["server/ArtMinionSilhouette.server.luau"] = b"-- wrong blob"
        for i in range(62):
            entries["server/Pad%02d.luau" % i] = b"-- mock source " + str(i).encode()
        for k, v in entries.items():
            dest = src / k
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(v)
        count = len(entries)
        import json
        lock = {p: art.gitblob(d) for p, d in sorted(entries.items())}
        (tmp / "SOURCE_LOCK.json").write_text(json.dumps({
            "total_scripts": count, "blobs": lock
        }), "utf8")
        (tmp / "RC_FEATURE_LOCK.json").write_text(json.dumps({
            "total_sources": count, "source_gitblobs": lock,
            "feature_flags": {"ART_MINION_THREE_SILHOUETTES_V1": True} if with_minion else {}
        }), "utf8")
        (tmp / "default.project.json").write_text(json.dumps({
            "tree": {"StarterPlayer": {"StarterPlayerScripts": {
                "HUD": {"$path": "src/client/HUD.client.luau"}
            }}}
        }), "utf8")
        return tmp

    def test_66_base_can_add_beast_without_touching_game(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._mock_assembled(Path(tmp), False)
            before = art.sources(root)
            self.assertEqual(len(before), 66)
            self.assertTrue(art.apply(root, True))
            after = art.sources(root)
            self.assertEqual(len(after), 67)
            self.assertEqual({k: after[k] for k in before}, before)
            self.assertIn(art.DEST, after)

    def test_67_source_unknown_minion_blob_is_rejected_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._mock_assembled(Path(tmp), True)
            prior = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            with self.assertRaises(AssertionError):
                art.apply(root, True)
            self.assertEqual(prior, {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()})


if __name__ == "__main__":
    unittest.main()
