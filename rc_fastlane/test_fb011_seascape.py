"""FB-011 source geometry and locked RC66 -> private RC67 regression."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from apply_fb011_seascape import apply, blob, scripts, SRC_PATH, SCRIPT_BLOB, DEST

class Fb011Seascape(unittest.TestCase):
    def fake_full_rc66(self, dist: Path):
        src = dist / "src"
        names = ["server/Game.server.luau", "server/MapBuilder.luau",
                 "server/H1FunWorld.server.luau", "client/HUD.client.luau",
                 "shared/Config.luau"]
        names += [f"server/Original{i:02d}.luau" for i in range(61)]
        self.assertEqual(len(names), 66)
        for path in names:
            target = src / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"-- original {path}\nreturn true\n", "utf8")
        original = scripts(dist)
        pins = {path: blob(data) for path, data in sorted(original.items())}
        (dist / "SOURCE_LOCK.json").write_text(json.dumps({
            "total_scripts": 66, "blobs": pins}), "utf8")
        (dist / "RC_FEATURE_LOCK.json").write_text(json.dumps({
            "total_sources": 66, "source_gitblobs": pins, "feature_flags": {}}), "utf8")
        (dist / "default.project.json").write_text(json.dumps({
            "tree": {"ServerScriptService": {"TrapRaidersS1": {
                "$path": "src/server"}}}}), "utf8")
        return original

    def test_01_authored_seascape_is_real_luau_with_surf_water_coast(self):
        content = SRC_PATH.read_bytes()
        self.assertEqual(blob(content), SCRIPT_BLOB)
        text = content.decode("utf8")
        self.assertIn("Enum.Material.Water", text)
        self.assertIn("terra:FillBlock(", text)
        self.assertIn("TweenService:Create", text)
        self.assertIn("FISHING_BOAT_SAIL_", text)
        self.assertIn("SEA_BOARDWALK_DECK_", text)
        self.assertIn("FORESHORE_SAND_", text)
        self.assertIn("FB011_H1_SEA_ANCHOR_ABSENT_FAIL_CLOSED", text)
        self.assertIn("studio", text.lower())
        self.assertNotIn("RemoteEvent", text)
        self.assertNotIn("TakeDamage(", text)
        self.assertNotIn("UpdateAsync(", text)

    def test_02_off_does_not_touch_or_create_dist(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "missing"
            self.assertFalse(apply(path, False))
            self.assertFalse(path.exists())

    def test_03_exact_source_lock_and_66_originals_preserved(self):
        with TemporaryDirectory() as folder:
            dist = Path(folder)
            original = self.fake_full_rc66(dist)
            self.assertTrue(apply(dist, True))
            after = scripts(dist)
            self.assertEqual(len(after), 67)
            self.assertEqual(set(after) - set(original), {DEST})
            for path, data in original.items():
                self.assertEqual(data, after[path], path)
            lock = json.loads((dist / "SOURCE_LOCK.json").read_text("utf8"))
            self.assertEqual(lock["total_scripts"], 67)
            self.assertEqual(lock["blobs"], {path: blob(raw) for path, raw in sorted(after.items())})
            with self.assertRaises(AssertionError):
                apply(dist, True)

    def test_04_bad_preexisting_pin_fails_before_any_write(self):
        with TemporaryDirectory() as folder:
            dist = Path(folder)
            self.fake_full_rc66(dist)
            original_bytes = (dist / "src/server/Game.server.luau").read_bytes()
            (dist / "src/server/Game.server.luau").write_bytes(original_bytes + b"-- drift")
            old_lock = (dist / "SOURCE_LOCK.json").read_bytes()
            with self.assertRaises(AssertionError):
                apply(dist, True)
            self.assertFalse((dist / "src" / DEST).exists())
            self.assertEqual((dist / "SOURCE_LOCK.json").read_bytes(), old_lock)

    def test_05_partial_rc_fails_closed(self):
        with TemporaryDirectory() as folder:
            with self.assertRaises(AssertionError):
                apply(Path(folder), True)

if __name__ == "__main__":
    unittest.main()
