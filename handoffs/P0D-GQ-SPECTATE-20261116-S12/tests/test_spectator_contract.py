"""Static safety/interface contracts; real Studio/Android remains NOT_TESTED."""
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "EGGRUMBLE_EliminationSpectator.client.luau"
SOURCE = SCRIPT.read_text(encoding="utf-8")


class SpectatorSourceContracts(unittest.TestCase):
    def test_studio_v3_real_client_source(self):
        self.assertTrue(SCRIPT.name.endswith(".client.luau"))
        self.assertIn('Players.LocalPlayer', SOURCE)
        self.assertIn('WORLD_NAME = "EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW"', SOURCE)

    def test_server_owned_elimination_is_the_only_entry_gate(self):
        self.assertGreaterEqual(SOURCE.count('GetAttribute("EGGRUMBLE_Eliminated")'), 3)
        self.assertIn('~= true then return', SOURCE)
        self.assertNotIn('player:SetAttribute(', SOURCE)

    def test_only_own_mode_arena_and_participation(self):
        self.assertIn('mode ~= "TEAM" and mode ~= "BATTLE_ROYALE"', SOURCE)
        self.assertIn('mode .. "_Arena"', SOURCE)
        self.assertIn('arena:FindFirstChild("Castle_" .. tostring(player.UserId))', SOURCE)

    def test_fallen_castles_never_tracked(self):
        self.assertIn('local FALLEN_CORE = Color3.fromRGB(59, 54, 55)', SOURCE)
        self.assertIn('core.Color ~= FALLEN_CORE', SOURCE)
        self.assertIn('table.sort(castles,', SOURCE)

    def test_camera_is_only_client_owned_and_restored(self):
        for part in ('savedCameraType = camera.CameraType',
                     'savedCameraSubject = camera.CameraSubject',
                     'camera.CameraType = Enum.CameraType.Scriptable',
                     'camera.CameraType = savedCameraType or Enum.CameraType.Custom',
                     'if camera ~= ownedCamera then',
                     'if subject then camera.CameraSubject = subject end'):
            with self.subTest(part=part):
                self.assertIn(part, SOURCE)

    def test_cleanup_on_session_end_and_manual_exit(self):
        for part in ('if not currentArena() then return end',
                     'if not arena then', 'stop()', 'gui:Destroy()',
                     'dismissed = true', 'dismissed = false',
                     'GetAttributeChangedSignal("EGGRUMBLE_QueuedMode")',
                     'GetAttributeChangedSignal("EGGRUMBLE_Eliminated")'):
            with self.subTest(part=part):
                self.assertIn(part, SOURCE)

    def test_small_mobile_panel_and_two_real_views(self):
        self.assertIn('UDim2.fromOffset(266, 71)', SOURCE)
        self.assertIn('makeButton(panel, "次の城"', SOURCE)
        self.assertIn('makeButton(panel, "戦場"', SOURCE)
        self.assertIn('makeButton(panel, "観戦終了"', SOURCE)
        self.assertIn('TacticalBattlefield', SOURCE)
        self.assertIn('RenderStepped:Connect(refresh)', SOURCE)

    def test_cannot_grant_reward_or_modify_match(self):
        forbidden = ('RemoteEvent', 'FireServer(', 'InvokeServer(',
                     'DataStoreService', 'MarketplaceService', 'Purchase',
                     'Rules.damage', 'Rules.takeEggs', 'Rules.depositEggs',
                     'SwarmCombat.', 'SetAttribute(', 'TeleportService',
                     'Humanoid:TakeDamage', 'Destroy() -- castle')
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, SOURCE)

    def test_no_general_gameplay_overrides(self):
        self.assertNotIn('StarterGui:SetCore', SOURCE)
        self.assertNotIn('game.StarterPlayer', SOURCE)
        self.assertIn('if player:GetAttribute("EGGRUMBLE_Eliminated") ~= true then', SOURCE)


if __name__ == "__main__":
    unittest.main()
