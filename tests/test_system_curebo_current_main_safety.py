"""PR98 regression: CUREBO stays playable with latest accepted main protections.

These are static boundary checks, not Roblox engine or Play testing.
Full canonical Lua run still required in Actions. Previous published
status and progress-save code must not be replaced with an older snapshot.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "src/ToyWarsServer.server.lua"
HUD = ROOT / "src/ToyWarsHUD.client.lua"
BALANCE = ROOT / "src/ToyWarsBalance.lua"


class CureboCurrentMainSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = SERVER.read_text(encoding="utf-8")
        cls.hud = HUD.read_text(encoding="utf-8")
        cls.balance = BALANCE.read_text(encoding="utf-8")

    def test_old_save_lease_and_close_regression_cannot_return(self):
        for marker in (
            "stopExpiredProgressLease(state)",
            'if type(game.BindToClose) == "function" then',
            "shuttingDown",
            "finalizeProgress(player,state",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.server)

    def test_authoritative_loss_and_victory_results_preserved(self):
        for marker in (
            'outcome.Name="RoundOutcome"',
            'state.roundOutcome.Value="VICTORY"',
            'state.roundOutcome.Value="LOSS"',
            'state.wave.Value=1',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.server)

    def test_late_replication_and_outcome_client_remain_nonblocking(self):
        for marker in (
            'status:FindFirstChild("RoundOutcome")',
            "status.ChildAdded:Connect(bindOutcome)",
            'outcome.Changed:Connect(refresh)',
            'outcome.Value=="VICTORY"',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.hud)

    def test_existing_four_toy_content_survives_transplant(self):
        for marker in ('elseif id == "curebo" then', "local function repairAlly(",
                       "data.repairAmount", '"curebo",x+32,-28'):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.server)
        self.assertIn("curebo = {name = \"CUREBO\"", self.balance)
        self.assertIn('B.PLAYABLE_IDS = {"pon", "guardon", "tankuru", "curebo"}', self.balance)
        self.assertIn("ToyPageNavigation", self.hud)
        self.assertIn("visibleIds[slot]", self.hud)


if __name__ == "__main__":
    unittest.main()
