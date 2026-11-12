#!/usr/bin/env python3
"""Reproducible 37-file S1 seven-change REVIEW source audit; no Studio or publishing."""
from __future__ import annotations
import hashlib
import json
import pathlib
import re
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
ROOT = REPO / "releases" / "P0D_S1_KIDS_RC01"
EXPECTED = {
    "src/server/Game.server.luau": {
        "blob": "e684ca79b8f5ed279bcdf033f4118bf77d552abb",
        "sha256": "ce151d2b41026c454af4b7ac0954e67a0458d401498fbe487a4c9874f6346515",
    },
    "src/server/S1CanonicalRoundHost.luau": {
        "blob": "1808fa630b13ad2be2dfdac188823957530b9086",
        "sha256": "590dc48459cf2ef23cd8321dfba0334e36f638b99db94054d4e37ebe6e072e81",
    },
    "src/server/MapBuilder.luau": {"blob": "94655d019fdf9798fa24a350ebf49f8290465ac0"},
    "src/shared/FirstMinuteModel.luau": {"blob": "d8dda6b1781375612c123f8c83b6f23fe45d09f1", "sha256": "7ab192f4b1dc7a6ce6750d72ed57d4ed15a41cb85729025a043dd4b411b31d03"},
    "src/client/HUD.client.luau": {"blob": "b3d3996c40c690e19007a36a847d5b10fc6a1522"},
}
BASE_TRIPLE_REVIEW = "09e118c9af3a7f30c2763b956ab80c4056d2a09d"
OFFICIAL_RC_PARENT = "1263a03701211a652b99b91d2339575dc8104eff"

def git_blob(b: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\x00" + b).hexdigest()

class FullGameReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "BUILD_MANIFEST.json").read_text("utf-8"))
        cls.game = (ROOT / "src/server/Game.server.luau").read_text("utf-8")
        cls.host = (ROOT / "src/server/S1CanonicalRoundHost.luau").read_text("utf-8")
        cls.map = (ROOT / "src/server/MapBuilder.luau").read_text("utf-8")
        cls.hud = (ROOT / "src/client/HUD.client.luau").read_text("utf-8")
        cls.coach = (ROOT / "src/shared/FirstMinuteModel.luau").read_text("utf-8")

    def test_manifest_entries_37_no_duplicate_paths(self):
        entries = self.manifest["files"]
        self.assertEqual(len(entries), 37)
        self.assertEqual(len({x["path"] for x in entries}), 37)

    def test_all_manifest_file_bytes_and_sha256(self):
        for entry in self.manifest["files"]:
            with self.subTest(path=entry["path"]):
                rel = pathlib.PurePosixPath(entry["path"])
                self.assertNotIn("..", rel.parts)
                self.assertFalse(rel.is_absolute())
                raw = (ROOT / rel).read_bytes()
                self.assertEqual(len(raw), entry["size"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), entry["sha256"])

    def test_seven_sources_pinned_exact_blob(self):
        for path, truth in EXPECTED.items():
            with self.subTest(path=path):
                raw = (ROOT / path).read_bytes()
                self.assertEqual(git_blob(raw), truth["blob"])
                if "sha256" in truth:
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), truth["sha256"])

    def test_s1_single_server_authority(self):
        self.assertEqual(self.game.count('remote.OnServerEvent:Connect('), 1)
        self.assertEqual(self.game.count('local function tickRound()'), 1)
        self.assertEqual(self.game.count('CanonicalHost.new('), 1)
        self.assertIn('local CANONICAL_S1_ENABLED = false', self.game)
        self.assertIn('local D07_D08_RELEASE_REVIEW_APPROVED = false', self.game)

    def test_server_snapshot_is_monotonic_across_rounds(self):
        self.assertEqual(self.game.count("local snapshotUpdateId = 0"), 1)
        self.assertEqual(self.game.count("snapshotUpdateId += 1"), 1)
        self.assertIn('updateId = snapshotUpdateId, -- view ordering only, not gameplay authority', self.game)
        self.assertEqual(self.game.count('remote.OnServerEvent:Connect('), 1)
        self.assertNotIn('snapshotUpdateId = 0\\n', self.game.split('local function resetRound',1)[-1])

    def test_child_coach_rejects_stale_snapshot_id(self):
        self.assertIn('lastUpdateId: number,', self.coach)
        self.assertIn('serial = -1, lastUpdateId = -1', self.coach)
        self.assertIn('if not wholeNumber(id) or id <= state.lastUpdateId then return false end', self.coach)
        self.assertIn('elseif state.lastUpdateId >= 0 then', self.coach)
        self.assertIn('if id ~= nil then state.lastUpdateId = id end', self.coach)
        self.assertLess(self.coach.index('state.latest = packet'),
                        self.coach.index('if id ~= nil then state.lastUpdateId = id end'))

    def test_both_new_source_surfaces_remain_disabled_for_combat_control(self):
        self.assertEqual(self.game.count('local CANONICAL_S1_ENABLED = false'), 1)
        self.assertEqual(self.game.count('local D07_D08_RELEASE_REVIEW_APPROVED = false'), 1)
        self.assertNotIn('Instance.new("RemoteEvent")', self.coach)
        self.assertNotIn('FireServer', self.coach)

    def test_player_removing_both_event_orders_safe(self):
        # Same Game source also preserves the separate X/Z recovery patch.
        block = self.game.split("Players.PlayerRemoving:Connect(function(player)", 1)[1].split("\nend)", 1)[0]
        self.assertEqual(block.count("if match.phase == \"ACTIVE\""), 1)
        self.assertIn("other ~= player and getTeamName(other) == side", block)
        self.assertIn("if teammates == 0 then", block)
        self.assertIn('stopRound(Rules.opponent(side), "OPPONENT_LEFT")', block)
        self.assertNotIn("teamCount(side) <= 1", block)
        self.assertEqual(self.game.count('remote.OnServerEvent:Connect('), 1)
        self.assertIn("math.abs(position.X) > 130", self.game)

    def test_server_arena_eligible_recovery(self):
        self.assertIn('position.Y < -30', self.game)
        self.assertIn('math.abs(position.X) > 130', self.game)
        self.assertIn('math.abs(position.Z) > 76', self.game)
        self.assertIn('if alive and root then', self.game)
        self.assertIn('if team == "RED" or team == "BLUE" then', self.game)

    def test_server_arena_egg_and_safe_spawn(self):
        block = self.game.split('-- Recovery uses the existing server-only authoritative tick.',1)[1]
        self.assertLess(block.index("dropEgg(player)"), block.index('root.CFrame ='))
        self.assertLess(block.index("restoreSlow(player)"), block.index('root.CFrame ='))
        self.assertLess(block.index("AssemblyLinearVelocity = Vector3.zero"), block.index('root.CFrame ='))
        self.assertLess(block.index("AssemblyAngularVelocity = Vector3.zero"), block.index('root.CFrame ='))
        self.assertIn('invulnUntil[player] = now + Config.RespawnInvulnerability', block)

    def test_host_heartbeat_rejects_abnormal_return(self):
        self.assertIn('if not good or reason ~= nil\n            or (cmd ~= nil and type(cmd) ~= "table") then', self.host)
        self.assertIn('self:stop("D07_HEARTBEAT_FAILED")', self.host)
        self.assertNotIn('if not good or reason == "HEARTBEAT_FAIL_CLOSED" then', self.host)

    def test_child_facing_three_variants(self):
        self.assertIn('UDim2.new(1, -140, 1, -110)', self.hud)
        self.assertIn('GuardianTrap', self.hud)
        self.assertIn('GUARDIAN', self.coach)
        self.assertIn('罠', self.coach)
        self.assertRegex(self.map, 'お城|たまご|納品')

    def test_no_new_clients_can_claim_damage_or_teleport(self):
        self.assertEqual(self.hud.count('remote:FireServer'), 1)
        recovery = self.game.split('-- Recovery uses the existing server-only authoritative tick.',1)[1].split('\nend\n',1)[0]
        for forbidden in ('OnServerEvent', 'FireServer', 'data.position', 'match.scores', 'match.hp', 'DataStore'):
            self.assertNotIn(forbidden, recovery)

    def test_no_published_or_paid_feature_from_review(self):
        self.assertNotIn("DataStoreService", self.game)
        self.assertNotIn("MarketplaceService", self.game)
        self.assertNotIn("Publish", self.game)

    def test_geometry_negative_oracle(self):
        def escaped(x, y, z):
            return y < -30 or abs(x) > 130 or abs(z) > 76
        for case, expected in [
            ((0,5,0),False), ((130,-30,76),False), ((-130,0,-76),False),
            ((130.01,5,0),True), ((-130.01,5,0),True),
            ((0,5,76.01),True), ((0,5,-76.01),True),
            ((0,-30.01,0),True), ((0,90,0),False),
        ]:
            self.assertEqual(escaped(*case), expected, case)

    def test_mutation_oracle_no_ghost_remote(self):
        mutated = self.game.replace('remote.OnServerEvent:Connect(', 'remote.OnServerEvent:Connect(\nremote.OnServerEvent:Connect(', 1)
        self.assertNotEqual(mutated.count('remote.OnServerEvent:Connect('), 1)
        self.assertEqual(self.game.count('remote.OnServerEvent:Connect('), 1)

if __name__ == "__main__":
    unittest.main(verbosity=2)
