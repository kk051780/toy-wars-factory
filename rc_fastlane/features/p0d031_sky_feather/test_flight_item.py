import json
import tempfile
import unittest
from pathlib import Path
from apply_private_stage import stage, blob

SOURCE = Path(__file__).with_name("P0DSkyFeather.server.luau")


class FlightItemTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dist = Path(self.tmp.name)
        (self.dist / "src/server").mkdir(parents=True)
        main = b"--!strict\nprint('REAL_ORIGINAL_AUTHOR_GAME')\n"
        (self.dist / "src/server/Game.server.luau").write_bytes(main)
        self.base = main
        self.cfg = {"name": "TEST", "tree": {"ServerScriptService": {
            "Game": {"$path": "src/server/Game.server.luau"}}}}
        self.lock = {"total_scripts": 1, "blobs": {"server/Game.server.luau": blob(main)}}
        self.save()

    def save(self):
        (self.dist / "default.project.json").write_text(json.dumps(self.cfg))
        (self.dist / "SOURCE_LOCK.json").write_text(json.dumps(self.lock))

    def test_source_implements_real_roblox_item_and_mobile_action(self):
        s = SOURCE.read_text()
        for token in ("ProximityPrompt", "prompt.Triggered:Connect", "Tool",
                      "tool.Activated:Connect", "LinearVelocity", "Humanoid",
                      "grass.CFrame:PointToWorldSpace", "tool.Parent = backpack",
                      "Players.PlayerRemoving", "task.delay(RESPAWN_SECONDS",
                      "RunService.Heartbeat:Connect", "cleanup()"):
            self.assertIn(token, s)
        self.assertEqual(s.count("Vector2.new("), 4)

    def test_public_and_cheat_authority_are_closed(self):
        s = SOURCE.read_text()
        self.assertIn('game.PrivateServerId == ""', s)
        self.assertIn('script:GetAttribute("EnablePrivatePreview") ~= true', s)
        self.assertIn('root.Position - orb.Position).Magnitude > 12', s)
        self.assertIn('not insideArena(root.Position)', s)
        for token in ("OnServerEvent:Connect", "RemoteEvent", "TakeDamage(",
                      "DataStoreService", "MarketplaceService", "GetDataStore("):
            self.assertNotIn(token, s)

    def test_adds_one_real_source_without_mutating_original_game(self):
        report = stage(self.dist, SOURCE)
        self.assertEqual(report["total"], 2)
        self.assertTrue(report["existing_byte_exact"])
        self.assertEqual((self.dist / "src/server/Game.server.luau").read_bytes(), self.base)
        after = json.loads((self.dist / "SOURCE_LOCK.json").read_text())
        self.assertEqual(len(after["blobs"]), 2)
        self.assertEqual(after["total_scripts"], 2)
        self.assertEqual(after["p0d031_private_stage"]["new_blob"], blob(SOURCE.read_bytes()))
        cfg = json.loads((self.dist / "default.project.json").read_text())
        self.assertEqual(cfg["tree"]["ServerScriptService"]["P0DSkyFeather"],
                         {"$path": "src/server/P0DSkyFeather.server.luau"})

    def test_rejects_duplicate_stage(self):
        stage(self.dist, SOURCE)
        with self.assertRaisesRegex(ValueError, "SOURCE_COUNT_MISMATCH|FEATURE_ALREADY_STAGED"):
            stage(self.dist, SOURCE)

    def test_rejects_forged_original_source_lock_without_write(self):
        self.lock["blobs"]["server/Game.server.luau"] = "000000"
        self.save()
        with self.assertRaisesRegex(ValueError, "SOURCE_LOCK_MISMATCH"):
            stage(self.dist, SOURCE)
        self.assertFalse((self.dist / "src/server/P0DSkyFeather.server.luau").exists())

    def test_rejects_wrong_count_and_missing_game(self):
        self.lock["total_scripts"] = 2
        self.save()
        with self.assertRaisesRegex(ValueError, "SOURCE_COUNT_MISMATCH"):
            stage(self.dist, SOURCE)

    def test_rejects_authority_escalation(self):
        attacker = self.dist / "evil.luau"
        attacker.write_text(SOURCE.read_text() + '\nInstance.new("RemoteEvent")\n')
        with self.assertRaisesRegex(ValueError, "AUTHORITY_COLLISION"):
            stage(self.dist, attacker)

    def test_rejects_server_mapping_collision(self):
        self.cfg["tree"]["ServerScriptService"]["P0DSkyFeather"] = {"$path": "evil"}
        self.save()
        with self.assertRaisesRegex(ValueError, "ROJO_SERVER_NAMESPACE_CONFLICT"):
            stage(self.dist, SOURCE)


if __name__ == "__main__":
    unittest.main()
