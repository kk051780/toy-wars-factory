import pathlib
import re
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class GuardianTrapSourceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game=(ROOT/"src/server/Game.server.luau").read_text(encoding="utf-8")
        cls.hud=(ROOT/"src/client/HUD.client.luau").read_text(encoding="utf-8")
        cls.trap=(ROOT/"src/server/S1TrapRules.luau").read_text(encoding="utf-8")
        cls.config=(ROOT/"src/shared/Config.luau").read_text(encoding="utf-8")
    def test_single_server_remote(self):
        self.assertEqual(self.game.count("OnServerEvent:Connect"),1)
    def test_trap_requires_trusted_server_sequence(self):
        self.assertIn("Rules.validSeq(data.seq, lastSeq[player] or 0)",self.game)
        self.assertIn('elseif data.action == "PLACE_TRAP" then placeTrap(player, data)',self.game)
    def test_no_client_coordinates(self):
        self.assertIn('action("PLACE_TRAP", nil)',self.hud)
        self.assertNotRegex(self.hud,r'FireServer\(\{[^}]*[Pp]osition')
    def test_guardian_only(self):
        self.assertIn('s.role ~= "GUARDIAN"',self.trap)
        self.assertIn('trapButton.Visible = s.phase == "ACTIVE" and s.role == "GUARDIAN"',self.hud)
    def test_boss_remains_gated(self):
        self.assertIn("local CANONICAL_S1_ENABLED = false",self.game)
        self.assertIn("local D07_D08_RELEASE_REVIEW_APPROVED = false",self.game)
    def test_zero_damage_or_entitlement(self):
        self.assertNotIn("TakeDamage",self.trap)
        self.assertNotIn("DataStore",self.trap)
        self.assertNotIn("RemoteEvent",self.trap)
    def test_round_cleanup(self):
        self.assertIn('clearTraps()',self.game)
        self.assertIn("now >= rec.expiresAt",self.game)
        self.assertIn("table.remove(traps, i)",self.game)
    def test_no_slow_stacking(self):
        self.assertIn("math.max(now + TrapRules.SLOW_SECONDS",self.game)
        self.assertIn("if current then current.untilAt else 0",self.game)
    def test_mobile_and_keyboard(self):
        self.assertIn('Enum.KeyCode.T',self.hud)
        self.assertIn('trapButton.MouseButton1Click',self.hud)
    def test_trap_cannot_block_attack_ray(self):
        self.assertIn("disc.CanCollide = false",self.game)
        self.assertIn("disc.CanQuery = false",self.game)
    def test_server_excludes_egg_and_spawn(self):
        self.assertIn("side.egg.Position, side.scorePad.Position",self.game)
        self.assertIn("side.core.Position, side.spawn.Position",self.game)
    def test_no_second_state_owner(self):
        self.assertEqual(self.game.count("local function tickRound()"),1)
        self.assertNotIn("FireServer",self.trap)
if __name__=="__main__": unittest.main()
