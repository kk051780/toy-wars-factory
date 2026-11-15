"""Source-boundary regression for FB020 field glider (not engine acceptance).

Run from repository root:
python3 -m unittest quality_repair.test_fb020_field_glider -v
"""
from pathlib import Path
import re
import unittest

SRC = Path(__file__).with_name("P0DFieldGlider.server.luau").read_text(encoding="utf-8")

class FieldGliderSourceContract(unittest.TestCase):
    def test_private_default_off(self):
        self.assertIn('RunService:IsStudio()', SRC)
        self.assertIn('ServerStorage:GetAttribute("P0D_FIELD_GLIDER_ENABLED")', SRC)
    def test_no_duplicate_world(self):
        self.assertIn('world:FindFirstChild("P0D_FIELD_GLIDER_V1")', SRC)
    def test_four_pickup_stations(self):
        self.assertEqual(4, len(re.findall(r'Vector2\\.new\\(', SRC)))
    def test_mobile_and_pc_prompt(self):
        self.assertIn('Instance.new("ProximityPrompt")', SRC)
        self.assertIn('prompt.KeyboardKeyCode = Enum.KeyCode.E', SRC)
    def test_server_distance_authority(self):
        self.assertIn('(hrp.Position - stand.Position).Magnitude > 10', SRC)
    def test_authoritative_player_body(self):
        self.assertIn('player.Character', SRC)
        self.assertIn('tool.Parent ~= character', SRC)
        self.assertIn('humanoid.Health <= 0', SRC)
    def test_single_use(self):
        self.assertIn('if consumed or active[player]', SRC)
        self.assertIn('consumed = true', SRC)
        self.assertIn('tool.Enabled = false', SRC)
    def test_real_server_physics(self):
        self.assertIn('Instance.new("LinearVelocity")', SRC)
        self.assertIn('RunService.Heartbeat:Connect', SRC)
    def test_bounded_movement(self):
        self.assertIn('grass.Size.X * 0.5 - 8', SRC)
        self.assertIn('grass.Size.Z * 0.5 - 8', SRC)
    def test_connection_and_force_cleanup(self):
        for anchor in ('connection:Disconnect()', 'force:Destroy()', 'attachment:Destroy()'):
            self.assertIn(anchor, SRC)
    def test_no_second_damage_score_remote_authority(self):
        for forbidden in ('Instance.new("RemoteEvent")', 'DataStoreService', 'TakeDamage', 'SetAsync'):
            self.assertNotIn(forbidden, SRC)
    def test_no_permanent_hud(self):
        self.assertNotIn('ScreenGui', SRC)
        self.assertNotIn('BillboardGui', SRC)

if __name__ == "__main__":
    unittest.main()
