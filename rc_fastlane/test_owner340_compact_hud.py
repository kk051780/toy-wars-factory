"""Owner #340 compact-HUD PREP contract tests; Python only, not Studio QA."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "owner340_adapter", ROOT / "apply_owner340_compact_hud.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def make_dist(root: Path) -> Path:
    dist = root / "dist"
    src = dist / "src"
    (src / "server").mkdir(parents=True)
    (src / "client").mkdir(parents=True)
    (src / "server/Game.server.luau").write_bytes(
        b'-- single original Game\nremote.OnServerEvent:Connect(function() end)\n')
    (src / "client/HUD.client.luau").write_bytes(
        b'-- existing original HUD, do not alter\n')
    for i in range(63):
        (src / f"server/Other{i:02d}.luau").write_bytes(
            f"-- immutable original {i}\nreturn true\n".encode())
    originals = mod.sources(dist)
    assert len(originals) == 65
    pins = {name: mod.blob(value) for name, value in sorted(originals.items())}
    (dist / "SOURCE_LOCK.json").write_text(json.dumps({
        "total_scripts": 65, "blobs": pins}), "utf8")
    (dist / "RC_FEATURE_LOCK.json").write_text(json.dumps({
        "total_sources": 65, "source_gitblobs": pins, "feature_flags": {}}), "utf8")
    (dist / "default.project.json").write_text(json.dumps({
        "tree": {
            "ServerScriptService": {"TrapRaidersS1": {"$path": "src/server"}},
            "StarterPlayer": {"StarterPlayerScripts": {
                "HUD": {"$path": "src/client/HUD.client.luau"}}}}}), "utf8")
    return dist


def snapshot(dist: Path):
    return {p.relative_to(dist).as_posix(): p.read_bytes()
            for p in sorted(dist.rglob("*")) if p.is_file()}


class CompactHUDPrepTests(unittest.TestCase):
    def test_off_is_byte_exact_all_65_and_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            dist = make_dist(Path(folder))
            original = snapshot(dist)
            self.assertEqual(mod.apply(dist, enabled=False)["scripts"], 65)
            self.assertEqual(snapshot(dist), original)

    def test_on_adds_only_one_client_not_a_second_game(self):
        with tempfile.TemporaryDirectory() as folder:
            dist = make_dist(Path(folder))
            original = mod.sources(dist)
            result = mod.apply(dist, enabled=True)
            after = mod.sources(dist)
            self.assertEqual(result["scripts"], 66)
            self.assertEqual(len(after), 66)
            self.assertEqual(after["server/Game.server.luau"],
                             original["server/Game.server.luau"])
            self.assertEqual(after["client/HUD.client.luau"],
                             original["client/HUD.client.luau"])
            self.assertTrue(all(after[key] == data for key, data in original.items()))
            self.assertEqual(after["client/CompactHUD.client.luau"],
                             mod.SCRIPT.read_bytes())
            self.assertEqual(mod.blob(after["client/CompactHUD.client.luau"]),
                             mod.SCRIPT_BLOB)
            cfg = json.loads((dist / "default.project.json").read_text("utf8"))
            self.assertEqual(
                cfg["tree"]["StarterPlayer"]["StarterPlayerScripts"]["CompactHUD"]["$path"],
                "src/client/CompactHUD.client.luau")
            lock = json.loads((dist / "SOURCE_LOCK.json").read_text("utf8"))
            self.assertEqual(lock["total_scripts"], 66)
            self.assertEqual(lock["blobs"],
                             {name: mod.blob(data) for name, data in sorted(after.items())})

    def test_drifting_lock_fails_without_any_output(self):
        with tempfile.TemporaryDirectory() as folder:
            dist = make_dist(Path(folder))
            lock = dist / "SOURCE_LOCK.json"
            data = json.loads(lock.read_text("utf8"))
            data["blobs"]["server/Game.server.luau"] = "0" * 40
            lock.write_text(json.dumps(data), "utf8")
            original = snapshot(dist)
            with self.assertRaisesRegex(AssertionError, "BASE_SOURCE_SHA_MISMATCH"):
                mod.apply(dist, enabled=True)
            self.assertEqual(snapshot(dist), original)

    def test_second_game_remote_authority_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            dist = make_dist(Path(folder))
            game = dist / "src/server/Game.server.luau"
            game.write_bytes(game.read_bytes() +
                             b'\nremote.OnServerEvent:Connect(function() end)\n')
            original = snapshot(dist)
            with self.assertRaises(AssertionError):
                mod.apply(dist, enabled=True)
            self.assertEqual(snapshot(dist), original)


if __name__ == "__main__":
    unittest.main()
