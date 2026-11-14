"""Offline contract tests for #340 compact HUD PREP overlay. Real Luau/Rojo runs in Actions."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from apply_compact_hud import HUD, START, apply, gitblob, inventory

HUD_SOURCE = """local gui = Instance.new("ScreenGui")
gui.Name = "TrapRaidersS1HUD"
local top = label(gui)
local status = label(gui)
local instructions = label(gui)
local function layoutRelayTouch() end
relayButton.MouseButton1Click:Connect(fireClassicEggRelay)
remote.OnClientEvent:Connect(function(s) end)
"""

class CompactHudTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dist = Path(self.tmp.name)
        (self.dist / "src/client").mkdir(parents=True)
        (self.dist / "src/server").mkdir(parents=True)
        (self.dist / "src" / HUD).write_text(HUD_SOURCE, encoding="utf8")
        (self.dist / "src/server/Game.server.luau").write_text(
            'remote.OnServerEvent:Connect(function() end)\n', encoding="utf8"
        )
        for i in range(63):
            (self.dist / "src/server" / f"Fake{i:02}.luau").write_text(
                f"return {i}\n", encoding="utf8"
            )
        self.before = inventory(self.dist)
        self.assertEqual(len(self.before), 65)
        pins = {path: gitblob(raw) for path, raw in self.before.items()}
        (self.dist / "SOURCE_LOCK.json").write_text(json.dumps({
            "total_scripts": 65, "blobs": pins,
        }), encoding="utf8")
        (self.dist / "RC_FEATURE_LOCK.json").write_text(json.dumps({
            "total_sources": 65, "source_gitblobs": pins,
        }), encoding="utf8")
        self.untouched = {p.name: hashlib.sha256(p.read_bytes()).digest()
                          for p in self.dist.rglob("*") if p.is_file()}

    def test_off_is_exactly_no_write(self):
        self.assertFalse(apply(self.dist, False))
        now = {p.name: hashlib.sha256(p.read_bytes()).digest()
               for p in self.dist.rglob("*") if p.is_file()}
        self.assertEqual(self.untouched, now)

    def test_on_changes_only_one_of_65(self):
        self.assertTrue(apply(self.dist, True))
        after = inventory(self.dist)
        self.assertEqual(len(after), 65)
        self.assertEqual([p for p in self.before if self.before[p] != after[p]], [HUD])
        self.assertEqual(self.before["server/Game.server.luau"], after["server/Game.server.luau"])

    def test_lock_matches_exact_written_sources(self):
        apply(self.dist, True)
        after = inventory(self.dist)
        pins = {path: gitblob(raw) for path, raw in after.items()}
        lock = json.loads((self.dist / "SOURCE_LOCK.json").read_text("utf8"))
        feature = json.loads((self.dist / "RC_FEATURE_LOCK.json").read_text("utf8"))
        self.assertEqual(lock["blobs"], pins)
        self.assertEqual(feature["source_gitblobs"], pins)
        self.assertEqual(lock["prep_compact_hud"]["official_rc_adopted"], False)

    def test_help_is_hidden_with_bounded_timer(self):
        apply(self.dist, True)
        raw = inventory(self.dist)[HUD].decode("utf8")
        self.assertEqual(raw.count(START), 1)
        self.assertIn("instructions.Visible = false", raw)
        self.assertIn("task.delay(5,", raw)
        self.assertIn("helpGeneration == generation", raw)
        self.assertIn('compactHelp.Text = "?"', raw)
        self.assertNotIn('Instance.new("RemoteEvent")', raw)

    def test_duplicate_patch_rejected(self):
        apply(self.dist, True)
        with self.assertRaisesRegex(ValueError, "DUPLICATE_COMPACT_HUD_PATCH"):
            apply(self.dist, True)

    def test_changed_hud_preimage_rejected(self):
        p = self.dist / "src" / HUD
        p.write_text(p.read_text("utf8") + "-- race\n", encoding="utf8")
        with self.assertRaisesRegex(ValueError, "SOURCE_LOCK_DRIFT"):
            apply(self.dist, True)

    def test_missing_legacy_control_refused(self):
        p = self.dist / "src" / HUD
        txt = p.read_text("utf8").replace(
            'relayButton.MouseButton1Click:Connect(fireClassicEggRelay)', ""
        )
        p.write_text(txt, encoding="utf8")
        pins = {key: gitblob(raw) for key, raw in inventory(self.dist).items()}
        for name, key in [("SOURCE_LOCK.json", "blobs"), ("RC_FEATURE_LOCK.json", "source_gitblobs")]:
            q = self.dist / name
            obj = json.loads(q.read_text("utf8"))
            obj[key] = pins
            q.write_text(json.dumps(obj), encoding="utf8")
        with self.assertRaisesRegex(ValueError, "REQUIRED_HUD_ANCHOR"):
            apply(self.dist, True)

    def test_no_server_writer_added(self):
        apply(self.dist, True)
        after = inventory(self.dist)
        self.assertEqual(sum(p == "server/Game.server.luau" for p in after), 1)
        self.assertEqual(sum(b"OnServerEvent:Connect(" in raw for raw in after.values()), 1)

if __name__ == "__main__":
    unittest.main()
