"""FB023 source-level invariants (not Studio/native Luau evidence)."""
import pathlib
import unittest

SOURCE = pathlib.Path(__file__).with_name('FieldPickups.server.luau').read_text(encoding='utf-8')


class FieldPickupSourceTests(unittest.TestCase):
    def test_three_functional_items(self):
        for item in ('HAMMER', 'SWIFT', 'SHIELD'):
            self.assertIn(f'id = "{item}"', SOURCE)
            self.assertIn(f'station.id == "{item}"', SOURCE)

    def test_only_server_owned_use(self):
        for word in ('ProximityPrompt', 'prompt.Triggered:Connect', 'tool.Activated:Connect',
                     'tool.Parent ~= char', 'HumanoidRootPart', 'MAX_PICKUP_DISTANCE',
                     'not available', 'available = false'):
            self.assertIn(word, SOURCE)

    def test_no_second_game_remote_or_score_owner(self):
        for forbidden in ('FireServer(', 'OnServerEvent', 'RemoteEvent.new(', '.Health = 0',
                          'leaderstats', 'DataStoreService', 'personalNeutralKOs'):
            self.assertNotIn(forbidden, SOURCE)

    def test_public_off_by_default(self):
        self.assertIn('RunService:IsStudio()', SOURCE)
        self.assertIn('game.PrivateServerId ~= ""', SOURCE)
        self.assertIn('P0D_PRIVATE_FIELD_ITEMS', SOURCE)
        self.assertIn('if not enabled then', SOURCE)

    def test_mobile_and_cleanup(self):
        self.assertIn('prompt.HoldDuration = 0.15', SOURCE)
        self.assertIn('prompt.MaxActivationDistance = 10', SOURCE)
        self.assertIn('Debris:AddItem(forceField, 4)', SOURCE)
        self.assertIn('task.delay(RESPAWN_SECONDS', SOURCE)
        self.assertIn('tool:Destroy()', SOURCE)
        self.assertIn('math.abs(hum.WalkSpeed - boosted)', SOURCE)
        self.assertIn('math.max(before, math.min(before + 8, 34))', SOURCE)

    def test_no_path_blocking(self):
        self.assertIn('pad.CanCollide = false', SOURCE)
        self.assertIn('pad.CanQuery = false', SOURCE)


if __name__ == '__main__':
    unittest.main()
