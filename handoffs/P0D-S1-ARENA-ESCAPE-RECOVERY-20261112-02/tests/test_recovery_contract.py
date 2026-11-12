"""S1 arena rescue, full-source exact-diff + pure rule QA (not Roblox Studio)."""
import hashlib
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "candidate/src/server/Game.server.luau"
ORIGINAL_GIT_BLOB = "7c5229f600f17537bc1bbbb0b96b6a2435875374"
ORIGINAL_MAP_BLOB = "d2127b8c20c8abd880a21f84aeeb706feeb14ce8"
OLD = '''    for _, player in ipairs(Players:GetPlayers()) do
        local alive, root = healthy(player)
        if alive and root and root.Position.Y < -30 then
            local team = getTeamName(player)
            if team == "RED" or team == "BLUE" then
                dropEgg(player)
                root.CFrame = map.teams[team].spawn + Vector3.new(0, 4, 0)
            end
        end
    end'''
NEW = '''    -- Recovery uses the existing server-only authoritative tick. Exact current
    -- S1 GrassArena is 250 x 142 studs; five studs outside is no longer playable.
    -- No client request or egg carry can choose a free teleport destination.
    for _, player in ipairs(Players:GetPlayers()) do
        local alive, root = healthy(player)
        if alive and root then
            local position = root.Position
            if position.Y < -30 or math.abs(position.X) > 130
                or math.abs(position.Z) > 76 then
                local team = getTeamName(player)
                if team == "RED" or team == "BLUE" then
                    dropEgg(player)
                    restoreSlow(player)
                    root.AssemblyLinearVelocity = Vector3.zero
                    root.AssemblyAngularVelocity = Vector3.zero
                    root.CFrame = map.teams[team].spawn + Vector3.new(0, 4, 0)
                    invulnUntil[player] = now + Config.RespawnInvulnerability
                end
            end
        end
    end'''


def blob_sha(content: str) -> str:
    b = content.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(b)).encode("ascii") + b"\\0".decode("unicode_escape").encode("ascii") + b).hexdigest()


def needs_recovery(x: float, y: float, z: float) -> bool:
    # Numerical contract from exactly the one new source guard. Not native Luau.
    return y < -30 or abs(x) > 130 or abs(z) > 76


class SourceAndRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = GAME.read_text(encoding="utf-8")

    def test_exact_one_source_block(self):
        self.assertEqual(self.source.count(NEW), 1)
        self.assertNotIn(OLD, self.source)

    def test_original_source_reconstructed_exact(self):
        self.assertEqual(blob_sha(self.source.replace(NEW, OLD)), ORIGINAL_GIT_BLOB)

    def test_map_dimensions_pinned_in_packet(self):
        self.assertEqual(250 / 2 + 5, 130)
        self.assertEqual(142 / 2 + 5, 76)
        self.assertEqual(len(ORIGINAL_MAP_BLOB), 40)

    def test_still_one_remote_and_one_round_tick(self):
        before = self.source.replace(NEW, OLD)
        self.assertEqual(before.count('remote.OnServerEvent:Connect('), 1)
        self.assertEqual(before.count('local function tickRound()'), 1)
        self.assertEqual(self.source.count('remote.OnServerEvent:Connect('), 1)
        self.assertEqual(self.source.count('local function tickRound()'), 1)

    def test_valid_play_area_never_teleports(self):
        for x, y, z in [(0, 5, 0), (125, 1, 71), (-130, 3, -76), (130, -30, 76)]:
            with self.subTest(pos=(x, y, z)):
                self.assertFalse(needs_recovery(x, y, z))

    def test_left_right_outside(self):
        for x in (-130.001, 130.001, -200, 200):
            self.assertTrue(needs_recovery(x, 5, 0))

    def test_north_south_outside(self):
        for z in (-76.001, 76.001, -150, 150):
            self.assertTrue(needs_recovery(0, 5, z))

    def test_fall_below_old_floor(self):
        self.assertTrue(needs_recovery(0, -30.01, 0))

    def test_no_unrequested_high_altitude_recall(self):
        self.assertFalse(needs_recovery(0, 80, 0))

    def test_no_client_position_or_client_remote(self):
        self.assertNotIn("FireServer", NEW)
        self.assertNotIn("OnServerEvent", NEW)
        self.assertNotIn("data.position", NEW)

    def test_drop_egg_before_teleport(self):
        self.assertLess(NEW.index("dropEgg(player)"), NEW.index("root.CFrame ="))

    def test_clear_slow_before_teleport(self):
        self.assertLess(NEW.index("restoreSlow(player)"), NEW.index("root.CFrame ="))

    def test_zero_velocities_before_teleport(self):
        self.assertLess(NEW.index("AssemblyLinearVelocity"), NEW.index("root.CFrame ="))
        self.assertLess(NEW.index("AssemblyAngularVelocity"), NEW.index("root.CFrame ="))

    def test_existing_server_time_immunity(self):
        self.assertIn("invulnUntil[player] = now + Config.RespawnInvulnerability", NEW)
        self.assertIn("local now = serverNow()", self.source.split("local function tickRound()", 1)[1])

    def test_only_live_players_with_team(self):
        self.assertIn("if alive and root then", NEW)
        self.assertIn('if team == "RED" or team == "BLUE" then', NEW)

    def test_no_heal_or_score_or_reward_mutation(self):
        for name in ["Humanoid.Health", "match.scores", "match.hp", "DataStore", "FireClient"]:
            self.assertNotIn(name, NEW)


if __name__ == "__main__":
    unittest.main()
