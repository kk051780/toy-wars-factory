import tempfile,unittest
from pathlib import Path
from rc_fastlane import apply_p0_lobby_rebalance78 as m
from rc_fastlane import test_p0_lobby_rebalance78_native as native

ORIGINAL='''local LobbyIsland = require(script.Parent:WaitForChild("LobbyDojoIsland"))
local function resetRound()
end
local function tickRound()
end
local function rebalanceLobbyTeams()
    if match.phase ~= "LOBBY" then return end
    local planned = LobbyTeamRecovery.plan(roster)
    for _,move in ipairs(planned) do
        if player and player.Parent==Players then
            dropEgg(player)
            player.Team = teamInstances[move.to]
            if alive and root then
                root.CFrame = map.teams[move.to].spawn + Vector3.new(0, 2, 0)
            end
        end
    end
end
local function assignSpawn()
end
remote.OnServerEvent:Connect(function() end)
'''

class LobbyRebalance78(unittest.TestCase):
    def test_one_original_game_only_and_one_targeted_replacement(self):
        changed=m.patch_game(ORIGINAL)
        self.assertIn("LobbyIsland.spawn(move.to)",changed)
        self.assertIn("RunService:IsStudio()",changed)
        self.assertEqual(changed.count("remote.OnServerEvent:Connect("),1)
        self.assertEqual(changed.count("local function rebalanceLobbyTeams()"),1)
        self.assertEqual(changed.count(m.FEATURE),1)
        # In the normal player/arena setup and all other game logic no source changed.
        self.assertEqual(changed.split("local function rebalanceLobbyTeams()")[0],
                         ORIGINAL.split("local function rebalanceLobbyTeams()")[0])
        self.assertEqual(changed.split("local function assignSpawn(")[1],
                         ORIGINAL.split("local function assignSpawn(")[1])

    def test_native_real_function_extract_from_patched_game(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/"game.luau"
            path.write_text(m.patch_game(ORIGINAL),"utf8")
            native_script=native.generate(path)
            self.assertIn("LOBBY_BALANCE_TELEPORTED_TO_COMBAT_FIELD",native_script)
            self.assertIn("P0_PRIVATE78_LOBBY_TEAM_REBALANCE_NATIVE_7_CASES_PASS",native_script)
            self.assertIn("LobbyIsland.spawn(move.to)",native_script)

    def test_self_repeat_fails_and_anchor_fails_closed(self):
        candidate=m.patch_game(ORIGINAL)
        with self.assertRaisesRegex(AssertionError,"TEAM_REBALANCE_ALREADY_FIXED"):
            m.patch_game(candidate)
        with self.assertRaisesRegex(AssertionError,"REBALANCE_FIELD_TELEPORT_SOURCE_DRIFT"):
            m.patch_game(ORIGINAL.replace(m.OLD,"root.CFrame=not_the_expected_original"))

    def test_off_zero_write_and_invalid78_never_publishes_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.assertFalse(m.apply(root/"none",root/"out",False))
            self.assertFalse((root/"out").exists())
            (root/"bad").mkdir()
            with self.assertRaises(AssertionError):
                m.apply(root/"bad",root/"out",True)
            self.assertFalse((root/"out").exists())

if __name__=="__main__":unittest.main()
