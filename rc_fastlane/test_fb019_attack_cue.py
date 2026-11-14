#!/usr/bin/env python3
"""FB019 local attempted attack cue source-lock, rollback and negative tests."""
from __future__ import annotations
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("fb019", HERE / "apply_fb019_attack_cue.py")
assert spec and spec.loader
fb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fb)

HUD = (
    'local player = Players.LocalPlayer\n'
    'local attack = button(gui, "Attack", "Attack", foo, bar, baz)\n'
    '    b.Text = text\n'
    'local function action(kind: string, role: string?)\n'
    '    seq += 1\n'
    '    remote:FireServer({action = kind, role = role, seq = seq})\n'
    'end\n'
    'attack.MouseButton1Click:Connect(function() action("ATTACK", nil) end)\n'
)
FLAGS = {
    "FB018_ACTION_BUTTON_TEXT_INIT": True,
    "FB017_NO_PERSISTENT_BATTLE_GUIDES": True,
    "FB016_FOLIAGE_PASSAGE_20261114": True
}

def fixture(root: Path):
    src = root / "src"
    (src / "client").mkdir(parents=True)
    (src / "server").mkdir(parents=True)
    (src / fb.TARGET).write_text(HUD, "utf8")
    (src / "server/Game.server.luau").write_text("-- original one Game\n", "utf8")
    for i in range(78):
        (src / "server" / f"Fixture{i:02}.luau").write_text(f"-- existing source {i}\n", "utf8")
    source = fb.source_map(root)
    assert len(source) == 80
    pins = {p: fb.blob(raw) for p, raw in source.items()}
    (root / "SOURCE_LOCK.json").write_text(json.dumps({"total_scripts": 80, "blobs": pins}) + "\n", "utf8")
    (root / "RC_FEATURE_LOCK.json").write_text(json.dumps({
        "total_sources": 80, "source_gitblobs": pins, "feature_flags": dict(FLAGS)
    }) + "\n", "utf8")
    (root / "default.project.json").write_text('{"name":"Fixture"}\n', "utf8")

class TestFB019(unittest.TestCase):
    def test_single_source_patch_and_rollback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = root / "original"
            base.mkdir()
            fixture(base)
            before = fb.source_map(base)
            off = root / "off"
            self.assertFalse(fb.apply(base, off, False))
            self.assertFalse(off.exists())
            out = root / "candidate"
            self.assertTrue(fb.apply(base, out, True))
            after = fb.source_map(out)
            changed = {k for k in before if before[k] != after[k]}
            self.assertEqual(changed, {fb.TARGET})
            self.assertEqual(len(after), 80)
            self.assertEqual(fb.source_map(base), before)
            body = after[fb.TARGET].decode("utf8")
            self.assertEqual(body.count(fb.FIRE_SERVER), 1)
            self.assertEqual(body.count(fb.ATTACK_CONNECT), 1)
            self.assertIn('if kind == "ATTACK" then fb019ShowAttemptedSwing() end', body)
            self.assertIn("if not attack.Visible then return end", body)
            self.assertNotIn("TakeDamage(", body)
            self.assertNotIn("ScreenGui", body)
            self.assertNotIn("Instance.new(\"RemoteEvent\")", body)
            self.assertTrue(json.loads((out / "RC_FEATURE_LOCK.json").read_text())["feature_flags"][fb.FEATURE])
            self.assertEqual(json.loads((out / "SOURCE_LOCK.json").read_text())["blobs"],
                             {p: fb.blob(raw) for p, raw in after.items()})
            self.assertFalse((root / "off").exists())

    def test_drift_rejected(self):
        with self.assertRaises(AssertionError):
            fb.patch(HUD.replace(fb.ATTACK_CONNECT, "").encode())
        with self.assertRaises(AssertionError):
            fb.patch(HUD.replace(fb.FIRE_SERVER, "").encode())
        with self.assertRaises(AssertionError):
            fb.patch(HUD.replace("    b.Text = text\n", "").encode())
        with self.assertRaises(AssertionError):
            fb.patch(fb.patch(HUD.encode()))

    def test_lock_drift_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = root / "original"
            base.mkdir()
            fixture(base)
            f = base / "src" / fb.TARGET
            f.write_bytes(f.read_bytes() + b"-- unsafe drift\n")
            with self.assertRaises(AssertionError):
                fb.apply(base, root / "candidate", True)

if __name__ == "__main__":
    unittest.main()
