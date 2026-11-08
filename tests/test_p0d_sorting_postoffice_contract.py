"""Static contract checks only; these do not replace a Roblox Studio playtest."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "examples" / "p0d_sorting_postoffice" / "RobotPostOffice.server.lua"


class PostOfficeContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SCRIPT.read_text(encoding="utf-8")

    def test_isolated_nonproduction_world(self):
        for marker in (
            'ROOT_NAME = "P0D_RobotPostOffice_TrialOnly"',
            'Workspace:FindFirstChild(ROOT_NAME)',
            'world.Parent = Workspace',
        ):
            self.assertIn(marker, self.source)
        self.assertNotIn("Workspace:ClearAllChildren", self.source)

    def test_three_colors_are_exact(self):
        for color in ('id = "RED"', 'id = "BLUE"', 'id = "YELLOW"'):
            self.assertIn(color, self.source)
        self.assertEqual(self.source.count('id = "'), 3)

    def test_server_owns_sorting_and_resets(self):
        for behavior in (
            'detector.MouseClick:Connect(onClick)',
            'state.selected ~= binId',
            'state.count = state.count + 1',
            'state.count == 3',
            'state.count = 0',
            'state.selected = nil',
            'Players.PlayerRemoving:Connect',
        ):
            self.assertIn(behavior, self.source)

    def test_actual_user_ui_and_visible_game_objects(self):
        for behavior in (
            'Instance.new("ScreenGui")',
            'Instance.new("ClickDetector")',
            'Instance.new("BillboardGui")',
            '"Parcel_" .. parcelId',
            '"DeliveryBin_" .. parcelId',
            '"ReplayPillar"',
            'objective.TextWrapped = true',
        ):
            self.assertIn(behavior, self.source)

    def test_no_persistence_external_network_or_monetization(self):
        for forbidden in (
            "DataStoreService", "HttpService", "InsertService",
            "MarketplaceService", "TeleportService",
            "MessagingService", "PurchasePrompt", "PublishAsync",
            "require(", "loadstring(", "game:HttpGet(",
        ):
            self.assertNotIn(forbidden, self.source)


if __name__ == "__main__":
    unittest.main()
