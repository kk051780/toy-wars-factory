"""Source-locked negative regression for #764 Leviathan melee, not Studio proof."""
import os
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from patch_leviathan import OLD, NEW, ORIGINAL_BLOB, SOURCE_PATH, git_blob, patch, restore

class TestLeviathanMeleeLOS(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original = Path(os.environ.get("REALM_ORIGINAL", "_realm764/" + SOURCE_PATH))
        cls.original = original.read_bytes().decode("utf-8")
        cls.updated = patch(cls.original)

    def test_immutable_original_blob(self):
        self.assertEqual(git_blob(self.original.encode()), ORIGINAL_BLOB)

    def test_only_one_melee_block_is_changed(self):
        self.assertEqual(self.original.count(OLD), 1)
        self.assertEqual(self.updated.count(NEW), 1)
        self.assertEqual(self.updated.replace(NEW, OLD, 1), self.original)

    def test_off_is_original_byte_exact(self):
        self.assertEqual(restore(self.updated).encode(), self.original.encode())

    def test_damage_behind_obstacle_fails_closed(self):
        self.assertIn("local obstacle=Workspace:Raycast(origin,root.Position-origin,params)", NEW)
        self.assertIn("if not obstacle then", NEW)
        self.assertLess(NEW.index("if not obstacle then"), NEW.index("TakeDamage(6)"))
        self.assertIn("params.RespectCanCollide=true", NEW)
        self.assertIn("{creature,nearest.Character}", NEW)

    def test_unchanged_cooldown_and_server_authority(self):
        self.assertIn("now-data.lastHit>=2", NEW)
        self.assertEqual(NEW.count("data.lastHit=now"), 1)
        self.assertEqual(self.updated.count('remote.OnServerEvent:Connect'), self.original.count('remote.OnServerEvent:Connect'))
        self.assertEqual(self.updated.count('RunService.Heartbeat:Connect'), self.original.count('RunService.Heartbeat:Connect'))
        self.assertEqual(self.updated.count("Instance.new(\"RemoteEvent\")"), self.original.count("Instance.new(\"RemoteEvent\")"))
        self.assertEqual(self.updated.count("TakeDamage(6)"), self.original.count("TakeDamage(6)"))

    def test_mutated_author_source_is_red(self):
        with self.assertRaisesRegex(ValueError, "blob drift"):
            patch(self.original.replace("GUN_INTERVAL = .20", "GUN_INTERVAL = .19"))
        with self.assertRaisesRegex(ValueError, "blob drift"):
            patch(self.original + "-- fake verifier input\n")

    def test_rollback_corruption_is_red(self):
        with self.assertRaisesRegex(ValueError, "rollback"):
            restore(self.updated.replace("if not obstacle then", "if obstacle then"))
        with self.assertRaisesRegex(ValueError, "non-unique"):
            restore(self.updated + NEW)

    def test_overlay_contains_only_original_neutral_damage(self):
        self.assertIn("for creature,data in pairs(state.creatures) do", self.updated)
        self.assertIn("nearest.Character:FindFirstChildOfClass", self.updated)
        self.assertNotIn("new RemoteEvent", NEW)
        self.assertNotIn("SetAttribute(\"RealmHP\"", NEW)

if __name__ == "__main__":
    unittest.main()
