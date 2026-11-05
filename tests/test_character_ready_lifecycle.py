"""Offline contract: deferred character teleport must reject stale sessions.

Static source-order check only; NOT a Roblox Studio respawn or multiplayer test.
"""
import unittest
from pathlib import Path

SERVER = (Path(__file__).resolve().parents[1] / "src/ToyWarsServer.server.lua").read_text(encoding="utf-8")
CALLBACK = SERVER.split("local function characterReady(character)", 1)[1].split("player.CharacterAdded:Connect", 1)[0]


class CharacterReadyLifecycleTests(unittest.TestCase):
    def test_wait_must_precede_fresh_lifecycle_guard(self):
        wait = CALLBACK.index("task.wait(0.1)")
        guard = CALLBACK.index("if not state.active or sessions[player] ~= state")
        teleport = CALLBACK.index("character:PivotTo(")
        self.assertLess(wait, guard)
        self.assertLess(guard, teleport)

    def test_guard_rejects_disconnected_player_and_replaced_character(self):
        guard = CALLBACK.split("task.wait(0.1)", 1)[1].split("character:PivotTo(", 1)[0]
        for check in ("not state.active", "sessions[player] ~= state",
                      "player.Parent ~= Players", "player.Character ~= character"):
            with self.subTest(check=check):
                self.assertIn(check, guard)


if __name__ == "__main__":
    unittest.main()
