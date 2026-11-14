"""Offline contract tests for PREP compact HUD (not Studio runtime tests)."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).with_name("apply_owner_hud_compact.py")
spec = importlib.util.spec_from_file_location("hudpatch", MODULE)
hudpatch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hudpatch)

HUD = '''local top = label(gui, "Score", UDim2.fromOffset(100,60), nil, nil, 20)
local status = label(gui, "Status", UDim2.fromOffset(100,30), nil, nil, 20)
local instructions = label(gui, "Instructions", UDim2.fromOffset(100,60), nil, nil, 20)
instructions.Text = "長い説明"
local attack = button(gui, "Attack", "攻撃", nil, nil, nil)
remote.OnClientEvent:Connect(function(s)
    if s.kind ~= "SNAPSHOT" then return end
    attack.Visible = s.phase == "ACTIVE"
end)
'''


def make_rc(root):
    dist = root / "game"
    source = dist / "src"
    (source / "client").mkdir(parents=True)
    (source / "server").mkdir()
    (source / "client/HUD.client.luau").write_text(HUD, "utf8")
    (source / "server/Game.server.luau").write_text(
        'remote.Name = "TrapRaidersS1Remote"\nremote.OnServerEvent:Connect(function() end)\n', "utf8")
    (source / "server/PersistentHatchStore.luau").write_text('return {}\n', "utf8")
    for idx in range(62):
        (source / "server" / f"Fake{idx:02}.luau").write_text(f"return {idx}\n", "utf8")
    scripts = hudpatch.inventory(dist)
    assert len(scripts) == 65
    pins = {p: hudpatch.gitblob(v) for p, v in scripts.items()}
    (dist / "SOURCE_LOCK.json").write_text(
        json.dumps({"total_scripts": 65, "blobs": pins}) + "\n", "utf8")
    (dist / "RC_FEATURE_LOCK.json").write_text(
        json.dumps({"total_sources": 65, "source_gitblobs": pins, "feature_flags": {}}) + "\n", "utf8")
    (dist / "default.project.json").write_text("{}\n", "utf8")
    return dist


class OwnerCompactHudTests(unittest.TestCase):
    def test_one_hud_only_and_same_source_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist = make_rc(Path(tmp))
            before = hudpatch.inventory(dist)
            self.assertTrue(hudpatch.run(dist, True))
            after = hudpatch.inventory(dist)
            self.assertEqual(len(after), 65)
            self.assertEqual([k for k in before if before[k] != after[k]], ["client/HUD.client.luau"])
            self.assertIn(b"OWNER_COMPACT_HUD_BEGIN", after["client/HUD.client.luau"])
            self.assertIn(b"compactHelp.Visible = s.phase", after["client/HUD.client.luau"])
            self.assertEqual(before["server/Game.server.luau"], after["server/Game.server.luau"])
            self.assertEqual(before["server/PersistentHatchStore.luau"],
                             after["server/PersistentHatchStore.luau"])
            lock = json.loads((dist / "SOURCE_LOCK.json").read_text("utf8"))
            self.assertEqual(lock["blobs"],
                             {k: hudpatch.gitblob(v) for k, v in after.items()})

    def test_off_preserves_every_byte(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist = make_rc(Path(tmp))
            before = {p.relative_to(dist): p.read_bytes() for p in dist.rglob("*") if p.is_file()}
            self.assertFalse(hudpatch.run(dist, False))
            self.assertEqual(before, {p.relative_to(dist): p.read_bytes()
                                      for p in dist.rglob("*") if p.is_file()})

    def test_missing_unique_anchor_fails_before_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist = make_rc(Path(tmp))
            path = dist / "src/client/HUD.client.luau"
            path.write_text(HUD.replace('instructions.Text = "長い説明"', ""), "utf8")
            scripts = hudpatch.inventory(dist)
            pins = {p: hudpatch.gitblob(v) for p, v in scripts.items()}
            lockpath = dist / "SOURCE_LOCK.json"
            featurepath = dist / "RC_FEATURE_LOCK.json"
            lock = json.loads(lockpath.read_text("utf8"))
            feature = json.loads(featurepath.read_text("utf8"))
            lock["blobs"] = pins
            feature["source_gitblobs"] = pins
            lockpath.write_text(json.dumps(lock), "utf8")
            featurepath.write_text(json.dumps(feature), "utf8")
            snapshot = {p.relative_to(dist): p.read_bytes() for p in dist.rglob("*") if p.is_file()}
            with self.assertRaises(AssertionError):
                hudpatch.run(dist, True)
            self.assertEqual(snapshot, {p.relative_to(dist): p.read_bytes()
                                        for p in dist.rglob("*") if p.is_file()})

    def test_double_application_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist = make_rc(Path(tmp))
            hudpatch.run(dist, True)
            with self.assertRaises(AssertionError):
                hudpatch.run(dist, True)


if __name__ == "__main__":
    unittest.main()
