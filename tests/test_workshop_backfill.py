"""Offline source contract for recovering a workshop slot after a player leaves.

This is a static regression, not a Roblox Studio multiplayer runtime test.
"""
import unittest
from pathlib import Path

SERVER = (Path(__file__).resolve().parents[1] / "src/ToyWarsServer.server.lua").read_text(encoding="utf-8")
JOIN = SERVER.split("local function join(player)", 1)[1].split("selectEvent.OnServerEvent:Connect", 1)[0]
LEAVE = SERVER.split("Players.PlayerRemoving:Connect(function(player)", 1)[1].split("for _,player in ipairs(Players:GetPlayers())", 1)[0]


class WorkshopBackfillTests(unittest.TestCase):
    def test_capacity_remains_four_and_full_join_does_not_allocate(self):
        self.assertIn("local MAX_PLOTS = 4", SERVER)
        self.assertLess(JOIN.index("if not slot then"), JOIN.index("occupied[slot]=player"))

    def test_join_rejects_players_who_left_and_duplicate_sessions(self):
        self.assertIn("if player.Parent ~= Players or sessions[player] then return end", JOIN)

    def test_slot_is_freed_before_waiting_player_is_admitted(self):
        self.assertLess(LEAVE.index("occupied[state.slot]=nil"), LEAVE.index("join(waiting)"))
        self.assertLess(LEAVE.index("sessions[player]=nil"), LEAVE.index("join(waiting)"))

    def test_only_connected_players_without_sessions_are_backfilled(self):
        self.assertIn("for _,waiting in ipairs(Players:GetPlayers()) do", LEAVE)
        self.assertIn("waiting ~= player and waiting.Parent == Players and not sessions[waiting]", LEAVE)
        self.assertIn("join(waiting)\n            break", LEAVE)


if __name__ == "__main__":
    unittest.main()
