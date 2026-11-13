"""Real Python tests for exact patcher preflight/rollback safety.
Works against original frozen B42 Game/HUD checked out by isolated Actions.
These tests DO NOT execute Roblox or prove actual current-RC native compatibility.
"""
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
BASE_REPO = Path(os.environ.get("P0D_RELAY_ORIGINAL_REPO", str(REPO / "_p0d_source")))
GAME_SOURCE = BASE_REPO / "handoffs/P0D-FIRST90-GUIDED-H1-20261113-01/inputs/Game.server.luau"
HUD_SOURCE = BASE_REPO / "handoffs/P0D-FIRST90-GUIDED-H1-20261113-01/inputs/HUD.client.luau"
POLICY_SOURCE = REPO / "handoffs/P0D-EGG-RELAY-PASS-POLICY-20261113-01/src/EggRelayPolicy.luau"
spec = importlib.util.spec_from_file_location("egg_relay_patch", ROOT / "tools/apply_relay.py")
assert spec is not None and spec.loader is not None
relay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(relay)


class RealOriginalPatchContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert GAME_SOURCE.is_file(), ("MISSING_PINNED_ORIGINAL_B42_GAME", GAME_SOURCE)
        assert HUD_SOURCE.is_file(), ("MISSING_PINNED_ORIGINAL_B42_HUD", HUD_SOURCE)
        assert POLICY_SOURCE.is_file(), ("MISSING_ORIGINAL_AUTHOR_POLICY", POLICY_SOURCE)
        cls.manifest = json.loads((ROOT / "PATCH_OPS.json").read_text("utf8"))
        assert relay.blob(GAME_SOURCE.read_bytes()) == cls.manifest["baseline_game_gitblob"]
        assert relay.blob(HUD_SOURCE.read_bytes()) == cls.manifest["baseline_hud_gitblob"]
        assert relay.blob(POLICY_SOURCE.read_bytes()) == cls.manifest["source_policy_gitblob"]

    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dist = Path(self.temp.name)
        self.src = self.dist / "src"
        (self.src / "server").mkdir(parents=True)
        (self.src / "client").mkdir(parents=True)
        (self.src / relay.GAME).write_bytes(GAME_SOURCE.read_bytes())
        (self.src / relay.HUD).write_bytes(HUD_SOURCE.read_bytes())

    def add_extra_55_sources(self):
        for i in range(55):
            p = self.src / ("server/IsolatedDummy%02d.luau" % i)
            p.write_text("return %d\n" % i, encoding="utf8")

    def lock_source(self):
        current = relay.source_bodies(self.src)
        pins = {p: relay.blob(b) for p, b in sorted(current.items())}
        (self.dist / "SOURCE_LOCK.json").write_text(
            json.dumps({"total_scripts": len(current), "blobs": pins}) + "\n", "utf8")
        (self.dist / "RC_FEATURE_LOCK.json").write_text(
            json.dumps({"total_sources": len(current), "source_gitblobs": pins,
                        "feature_flags": {"SAVED_BEAST_EVOLUTION": True}}) + "\n", "utf8")
        return current

    def snapshot(self):
        return {p.relative_to(self.dist).as_posix(): p.read_bytes()
                for p in sorted(self.dist.rglob("*")) if p.is_file()}

    def test_actual_pinned_original_static_anchors_exact(self):
        game = GAME_SOURCE.read_text("utf8")
        hud = HUD_SOURCE.read_text("utf8")
        self.assertEqual(len(self.manifest["game_ops"]), 9)
        self.assertEqual(len(self.manifest["hud_ops"]), 6)
        for operation in self.manifest["game_ops"]:
            self.assertEqual(game.count(operation["anchor"]), 1, operation["anchor"][:70])
            game = game.replace(operation["anchor"], operation["replace"], 1)
        for operation in self.manifest["hud_ops"]:
            self.assertEqual(hud.count(operation["anchor"]), 1, operation["anchor"][:70])
            hud = hud.replace(operation["anchor"], operation["replace"], 1)
        self.assertIn("local now = os.clock()", game)
        self.assertIn("(os.clock() - relayLastAt[carry[player]])", game)
        self.assertIn("relayButton.MouseButton1Click:Connect(fireClassicEggRelay)", hud)

    def test_small_original_one_Game_three_script_candidate(self):
        self.lock_source()
        relay.run(self.dist, POLICY_SOURCE)
        sources = relay.source_bodies(self.src)
        self.assertEqual(len(sources), 3)
        self.assertEqual(sources[relay.POLICY], POLICY_SOURCE.read_bytes())
        body = sources[relay.GAME].decode("utf8")
        self.assertEqual(body.count('remote.OnServerEvent:Connect('), 1)
        self.assertEqual(body.count('remote.Name = "TrapRaidersS1Remote"'), 1)
        self.assertEqual(body.count("match.eggOwners[egg]=target"), 1)
        self.assertEqual(body.count("carry[target]=egg"), 1)
        self.assertEqual(body.count("H2Score.deposit("),
                         GAME_SOURCE.read_text("utf8").count("H2Score.deposit("))

    def test_fifty_seven_stub_sources_increment_to_58_without_overwriting_55(self):
        self.add_extra_55_sources()
        before = self.lock_source()
        self.assertEqual(len(before), 57)
        relay.run(self.dist, POLICY_SOURCE)
        after = relay.source_bodies(self.src)
        self.assertEqual(len(after), 58)
        for path in before:
            if path not in (relay.GAME, relay.HUD):
                self.assertEqual(before[path], after[path], path)
        for fname, key in (("SOURCE_LOCK.json", "blobs"),
                            ("RC_FEATURE_LOCK.json", "source_gitblobs")):
            data = json.loads((self.dist / fname).read_text("utf8"))
            self.assertEqual(data[key], {p: relay.blob(b) for p, b in sorted(after.items())})
        self.assertEqual(json.loads((self.dist / "RC_FEATURE_LOCK.json").read_text())
                         ["feature_flags"]["SAVED_BEAST_EVOLUTION"], True)

    def test_corrupt_input_source_lock_fails_before_any_write(self):
        self.lock_source()
        p = self.src / relay.GAME
        p.write_bytes(p.read_bytes() + b"\n--drift")
        before = self.snapshot()
        with self.assertRaisesRegex(AssertionError, "SOURCE_LOCK_MISMATCH"):
            relay.run(self.dist, POLICY_SOURCE)
        self.assertEqual(before, self.snapshot())

    def test_corrupt_feature_source_lock_fails_before_any_write(self):
        self.lock_source()
        p = self.dist / "RC_FEATURE_LOCK.json"
        data = json.loads(p.read_text("utf8"))
        data["total_sources"] = 900
        p.write_text(json.dumps(data), "utf8")
        before = self.snapshot()
        with self.assertRaisesRegex(AssertionError, "STALE_FEATURE_COUNT"):
            relay.run(self.dist, POLICY_SOURCE)
        self.assertEqual(before, self.snapshot())

    def test_unmatched_anchor_fails_before_any_write(self):
        g = self.src / relay.GAME
        g.write_text(g.read_text("utf8").replace(
            "local First90Waypoint = require(script.Parent:WaitForChild(\"First90WaypointRules\"))",
            "--intentionally removed upstream anchor"), "utf8")
        self.lock_source()
        before = self.snapshot()
        with self.assertRaisesRegex(AssertionError, "ANCHOR_DRIFT"):
            relay.run(self.dist, POLICY_SOURCE)
        self.assertEqual(before, self.snapshot())

    def test_malformed_policy_source_fails_without_mutation(self):
        self.lock_source()
        tampered = self.dist / "fake_policy.luau"
        tampered.write_bytes(POLICY_SOURCE.read_bytes() + b"\n--tamper")
        before = self.snapshot()
        with self.assertRaisesRegex(AssertionError, "POLICY_BLOB_DRIFT"):
            relay.run(self.dist, tampered)
        self.assertEqual(before, self.snapshot())

    def test_duplicate_feature_lock_rejected_without_mutation(self):
        self.lock_source()
        p = self.dist / "RC_FEATURE_LOCK.json"
        d = json.loads(p.read_text("utf8"))
        d["feature_flags"][relay.FEATURE] = True
        p.write_text(json.dumps(d), "utf8")
        before = self.snapshot()
        with self.assertRaisesRegex(AssertionError, "FEATURE_DUPLICATE_ADMISSION"):
            relay.run(self.dist, POLICY_SOURCE)
        self.assertEqual(before, self.snapshot())

    def test_second_apply_refused_without_mutation(self):
        self.lock_source()
        relay.run(self.dist, POLICY_SOURCE)
        before = self.snapshot()
        with self.assertRaisesRegex(AssertionError, "UNSUPPORTED_BASE_SOURCE_COUNT"):
            relay.run(self.dist, POLICY_SOURCE)
        self.assertEqual(before, self.snapshot())

    def test_five_egg_mode_is_still_denied(self):
        self.lock_source()
        relay.run(self.dist, POLICY_SOURCE)
        g = (self.src / relay.GAME).read_text("utf8")
        self.assertIn('if not classicRelayEnabled() or EXPERIMENTAL_FIVE_EGG_MODE', g)
        self.assertIn('P0D_RC_ENABLE_EGG_RELAY_CLASSIC', g)
        self.assertIn('flag == nil or (flag:IsA("BoolValue") and flag.Value == true)', g)
        self.assertIn('relayEnabled = classicRelayEnabled()', g)
        self.assertIn('or match.phase ~= "ACTIVE"', g)
        self.assertEqual(g.count("H2Score.deposit("),
                         GAME_SOURCE.read_text("utf8").count("H2Score.deposit("))

    def test_no_extra_Game_Remote_Store_or_purchases(self):
        self.lock_source()
        relay.run(self.dist, POLICY_SOURCE)
        g = (self.src / relay.GAME).read_text("utf8")
        original = GAME_SOURCE.read_text("utf8")
        self.assertEqual(g.count('remote.OnServerEvent:Connect('),
                         original.count('remote.OnServerEvent:Connect('))
        self.assertEqual(g.count('DataStoreService:GetDataStore('),
                         original.count('DataStoreService:GetDataStore('))
        self.assertEqual(g.count('match.scores[team] += 1'),
                         original.count('match.scores[team] += 1'))


if __name__ == "__main__":
    unittest.main()
