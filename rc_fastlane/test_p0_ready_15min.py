"""Regression tests for P0 OWNER #361 patch. Real 66-source assembly runs in CI."""
from pathlib import Path
import tempfile
import unittest
from apply_p0_ready_15min import patch_game, patch_hud, patch_config, apply

GAME_FIXTURE = '''
local function snapshotFor(player: Player)
    return { kind = "SNAPSHOT", serial = match.serial }
end
local function stopRound(winner: string, reason: string)
    if match.phase ~= "ACTIVE" then return end
end
remote.OnServerEvent:Connect(function(player: Player, data)
    if type(data) ~= "table" then return end
    if data.action == "ATTACK" then applyAttack(player, data) end
end)
local function onJoin(player: Player)
    chooseTeam(player)
end
Players.PlayerRemoving:Connect(function(player)
    roles[player] = nil
end)
local function tickRound()
    if match.phase == "LOBBY" then
        rebalanceLobbyTeams()
        if StudioSolo.canStart(RunService:IsStudio(), count) then
            match.phase = "COUNTDOWN"
        end
    elseif match.phase == "COUNTDOWN" then
        if not StudioSolo.canStart(RunService:IsStudio(), count) then
            match.phase = "LOBBY"
        elseif now >= match.phaseUntil then resetRound() end
    elseif match.phase == "ACTIVE" then
        if now >= match.deadline then stopRound("DRAW", "TIME_LIMIT") end
    end
end
'''
HUD_FIXTURE = '''
local function action(kind: string, role: string?)
end
local function phaseText(s): string
    return "lobby"
end
remote.OnClientEvent:Connect(function(s)
    if s.kind ~= "SNAPSHOT" then return end
    status.Text = phaseText(s)
end)
'''

class CorePatchTests(unittest.TestCase):
    def test_15_minute_source_config(self):
        self.assertEqual(patch_config("return { MatchSeconds = 360, }"),
                         "return { MatchSeconds = 900, }")
        with self.assertRaises(AssertionError):
            patch_config("return { MatchSeconds = 900 }")

    def test_ready_round_server_owned_and_no_new_remote(self):
        result = patch_game(GAME_FIXTURE)
        self.assertEqual(result.count("remote.OnServerEvent:Connect("), 1)
        self.assertIn("ready = readyForMatch[player] == true", result)
        self.assertIn("readyForMatch[player] = false", result)
        self.assertIn("readyForMatch[participant] = false", result)
        self.assertIn("if allPlayersReadyForRound() then", result)
        self.assertIn("if not allPlayersReadyForRound() then", result)
        self.assertIn('data.action == "READY_TOGGLE"', result)
        self.assertIn("RunService:IsStudio() and readyForMatch[online[1]]", result)
        with self.assertRaises(AssertionError):
            patch_game(result)

    def test_lobby_control_and_numeric_combat_hud(self):
        result = patch_hud(HUD_FIXTURE)
        self.assertIn('action("READY_TOGGLE", nil)', result)
        self.assertIn('readyButton.Visible = s.phase == "LOBBY"', result)
        self.assertIn('s.ready == true', result)
        self.assertIn('selfHp.Text = string.format("HP %d/%d"', result)
        self.assertIn('top.Text = string.format("🔴城%d/%d', result)
        self.assertIn('status.Visible = s.carrying ~= ""', result)
        with self.assertRaises(AssertionError):
            patch_hud(result)

    def test_off_uses_no_scratch_dist(self):
        with tempfile.TemporaryDirectory() as folder:
            dist = Path(folder) / "missing"
            self.assertFalse(apply(dist, False))
            self.assertFalse(dist.exists())

if __name__ == "__main__":
    unittest.main()
