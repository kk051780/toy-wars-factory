"""Static S1/D07 authority contract + pure Python negative oracle (NOT native Luau/Studio).
All pinned originals remain unchanged. We only audit the exact new Binding source.
"""
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD_ROOT = ROOT.parents[1] / "P0D-S1-CANONICAL-ROUND-HOST-20261111-01"
SRC = (ROOT / "src/S1GoroganLiveBindings.luau").read_text("utf-8")
DOC = (ROOT / "docs/INTEGRATION.md").read_text("utf-8")
ORIGINAL = {
    "ChaosEventCore": "f6d6901a8dcb61cec1095e383e485950144d39ea43737c9b33d4351a66e88726",
    "CanonicalEventBridge": "a54797ce97e433d3fc12e627c27f884b78bb148a3fbd506e0156fed7759aabd2",
    "TrustedGoroganActivationMapper": "46513abb081bfc27bf1354a060370ac817a4eaf714f211b74a5d95f369eadbea",
    "GoroganCombinedRuntime": "5f365839de76249c4477bf74a97591584fd0e09e328adbe4a05b00f81902786b",
    "GoroganServerAICore": "fa483be147f452434cf41847e41c576cc92d45e0e4ed1d9d7582a189106ea787",
    "GoroganRigDriver": "64a27dc2cab176749cc9a1f40bb47266cec9a32b280e78f8280b78eaf092e747",
    "GoroganDamageBoundary": "229cbee9a2b1b4d11d78fe065f18ee7b9eee3d5a8d1b9243c287883665dcca1e",
    "GoroganAttackReceiptWindow": "1284882c9c2c87cb2075345d01ccac7d722693499e0b2eaa0cf659267b488f45",
    "S1CanonicalRoundHost": "b7a02f03c3c93a9301bdfbcf4fff6dcf9a5e8692d12a3f460c61d29005e72672",
}
MATCH_SOURCE_SHA = "d7abfc3b6ae1412cad995873faec1c5e4a1a9df1c0971991cff919564a628f3f"
GAME_PATH = Path("releases/P0D_S1_KIDS_RC01/src/server/Game.server.luau")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

class RoundOracle:
    """Independent English-contract oracle; never claim it executes Luau code."""
    def __init__(self, serial=3, started=100, deadline=460):
        self.serial = serial
        self.started, self.deadline = started, deadline
        self.event = None
        self.issued = False
        self.closed = False
        self.hit_receipts = set()

    def live(self, serial, phase, now):
        return not self.closed and serial == self.serial and phase == "ACTIVE" and self.started <= now < self.deadline

    def mint(self, serial, phase, now, proven):
        if not self.live(serial, phase, now) or not proven or self.issued:
            return None
        self.issued = True
        self.event = f"G07_{self.serial}"
        return self.event

    def hit(self, serial, phase, now, event, attack, player, safe, immune, distance_sq, los):
        if not self.live(serial, phase, now) or event != self.event:
            return False
        if not isinstance(attack, int) or attack not in (1,2,3):
            return False
        if not isinstance(player, int) or player < 1 or safe or immune or not los:
            return False
        if distance_sq > 49 or distance_sq < 0:
            return False
        key = (attack,player)
        if key in self.hit_receipts:
            return False
        self.hit_receipts.add(key)
        return True

class PinnedOriginalTests(unittest.TestCase):
    def test_original_nine_modules_sha_exact(self):
        for name, expected in ORIGINAL.items():
            with self.subTest(name=name):
                self.assertEqual(sha(OLD_ROOT/"src"/f"{name}.luau"), expected)

    def test_original_s1_source_sha_exact(self):
        self.assertEqual(sha(GAME_PATH), MATCH_SOURCE_SHA)

    def test_original_s1_game_has_one_remote(self):
        game = GAME_PATH.read_text("utf-8")
        self.assertEqual(game.count('Instance.new("RemoteEvent")'),1)
        self.assertIn("match.serial",game)

    def test_requires_real_d07_four_siblings(self):
        for module in ("GoroganCombinedRuntime","GoroganRigDriver",
                       "GoroganDamageBoundary","GoroganAttackReceiptWindow"):
            self.assertIn(f'WaitForChild("{module}")',SRC)

    def test_exact_original_combined_has_single_receipt_window(self):
        combined=(OLD_ROOT/"src/GoroganCombinedRuntime.luau").read_text()
        self.assertIn("openFromCoreResult(cmd,a.roundId,a.eventId)",combined)
        self.assertIn("self.deps.damageGate:applyServerDamage(",combined)
        self.assertIn("w:close()",combined)

class StaticBindingTests(unittest.TestCase):
    def test_luau_source_has_strict_mode(self):
        self.assertTrue(SRC.startswith("--!strict"))

    def test_only_exports_binding_module(self):
        self.assertTrue(SRC.rstrip().endswith("return Binding"))
        self.assertNotIn("task.spawn",SRC)
        self.assertNotIn("RunService",SRC)

    def test_no_duplicate_event_chooser(self):
        for bad in ('Instance.new("RemoteEvent")','OnServerEvent',
                    "math.random(", "CanonicalEventBridge", "ChaosEventCore"):
            with self.subTest(bad=bad): self.assertNotIn(bad,SRC)

    def test_no_client_side_or_secondary_damage(self):
        for bad in (":FireServer(", ":TakeDamage(", ":FireAllClients(", "BindToRenderStep"):
            self.assertNotIn(bad,SRC)

    def test_real_humanoid_and_server_membership(self):
        self.assertIn("Players:GetPlayers()",SRC)
        self.assertIn("Players:GetPlayerByUserId(n)",SRC)
        self.assertIn('player.Parent ~= Players',SRC)
        self.assertIn('FindFirstChild("HumanoidRootPart")',SRC)

    def test_match_epoch_phase_deadline_bound(self):
        for term in ("m.phase ~= \"ACTIVE\"","m.serial ~= self.serial",
                     "m.startedAt ~= self.startedAt","m.deadline ~= self.deadline",
                     "t < self.deadline"):
            self.assertIn(term,SRC)

    def test_current_server_approved_only(self):
        self.assertIn("deps.approvedByOwner == true",SRC)
        self.assertIn("mapper:isCanonicalActivation(activation)",SRC)
        self.assertIn('if me.attempted or not liveMatch(me)',SRC)
        self.assertRegex(SRC,r"me\\.activeEventId = \"G07_\"")
        self.assertIn("return nil",SRC)

    def test_precise_source_game_match_id(self):
        self.assertIn('"S1_" .. tostring(m.serial)',SRC)
        self.assertIn('"G07_" .. tostring(me.serial)',SRC)
        self.assertIn("m.serial < 1024",SRC)

    def test_original_d07_stomp_receipt_not_reimplemented(self):
        self.assertIn("window:attests(roundId, eventId, attackId)",SRC)
        self.assertIn("window:center(roundId, eventId, attackId)",SRC)
        self.assertIn('isCanonicalAttackReceipt = function',SRC)

    def test_spawn_and_respawn_protection_fails_closed(self):
        for term in ("inSpawnSafeZone(self, player)",
                     "protectedByRespawn(self, player)",
                     "if not ok or not finite(expiration) or not now then return true",
                     "return (root.Position - side.spawn.Position).Magnitude < 14"):
            self.assertIn(term,SRC)

    def test_geometry_real_world_raycast_and_map(self):
        for term in ("workspace:Raycast(origin, Vector3.new(0, -18, 0)",
                     "hit.Instance:IsDescendantOf(self.deps.map.model)",
                     "workspace:Raycast(source, v, params)",
                     "hit.Instance:IsDescendantOf(player.Character)",
                     "raycastIgnore = ignoredModel"):
            self.assertIn(term,SRC)

    def test_valid_stage_and_boss_anchor(self):
        self.assertIn('stage == "S1"',SRC)
        self.assertIn('Vector3.new(0, 0, 0)',SRC)
        self.assertIn("math.abs(p.X) > 52",SRC)
        self.assertIn("math.abs(p.Z) > 40",SRC)

    def test_callback_does_not_build_second_authority(self):
        self.assertIn("getPlayerTeam",SRC)
        self.assertIn("getInvulnerableUntil",SRC)
        self.assertIn("getNow = function()",SRC)
        self.assertIn("isRealRoundEvent = function(roundId, eventId)",SRC)
        self.assertNotIn("RemoteFunction",SRC)

    def test_original_driver_server_network_ownership(self):
        original=(OLD_ROOT/"src/GoroganRigDriver.luau").read_text()
        self.assertIn("root:SetNetworkOwner(nil)",original)
        self.assertIn("PathfindingService",original)

    def test_abort_closes_all_layers_and_rejects_residual_rig(self):
        for term in ("self.combined:stop(roundId, eventId)",
                     "self.window:close()","self.gate:stop(roundId, self.gate.eventId)",
                     "self.driver:stop(roundId, self.driver.eventId)",
                     "self.combined and self.combined.active then success = false",
                     "self.driver and self.driver.model then success = false",
                     "clearEvent(self)", "self.closed = true"):
            self.assertIn(term,SRC)

    def test_studio_false_explicit(self):
        self.assertIn("verifiedInRobloxStudio = false",SRC)
        self.assertIn("STUDIO NOT TESTED",DOC)
        self.assertIn("SINGLE Chat integrator",DOC)

class OracleNegativeTests(unittest.TestCase):
    def setUp(self):
        self.o=RoundOracle()

    def test_legitimate_one_event(self):
        self.assertEqual(self.o.mint(3,"ACTIVE",120,True),"G07_3")
        self.assertIsNone(self.o.mint(3,"ACTIVE",121,True))

    def test_no_unproven_client_event(self):
        self.assertIsNone(self.o.mint(3,"ACTIVE",120,False))

    def test_no_lobby_or_result(self):
        self.assertIsNone(self.o.mint(3,"LOBBY",120,True))
        self.assertIsNone(self.o.mint(3,"RESULTS",120,True))

    def test_round_id_replay_denied(self):
        self.assertIsNone(self.o.mint(4,"ACTIVE",120,True))
        self.assertIsNone(self.o.mint(3,"ACTIVE",461,True))

    def test_round_time_start_boundary(self):
        self.assertIsNone(self.o.mint(3,"ACTIVE",99,True))
        self.assertEqual(self.o.mint(3,"ACTIVE",100,True),"G07_3")

    def test_safe_damage_once(self):
        eid=self.o.mint(3,"ACTIVE",120,True)
        args=(3,"ACTIVE",125,eid,1,42,False,False,40,True)
        self.assertTrue(self.o.hit(*args))
        self.assertFalse(self.o.hit(*args))

    def test_attack_id_or_wrong_event_denied(self):
        eid=self.o.mint(3,"ACTIVE",120,True)
        for attack in (-1,0,4,2.5):
            self.assertFalse(self.o.hit(3,"ACTIVE",130,eid,attack,42,False,False,10,True))
        self.assertFalse(self.o.hit(3,"ACTIVE",130,"forged",1,42,False,False,10,True))

    def test_spawn_protection(self):
        eid=self.o.mint(3,"ACTIVE",120,True)
        self.assertFalse(self.o.hit(3,"ACTIVE",125,eid,1,42,True,False,10,True))
        self.assertFalse(self.o.hit(3,"ACTIVE",125,eid,1,42,False,True,10,True))

    def test_hard_geometry_limit(self):
        eid=self.o.mint(3,"ACTIVE",120,True)
        self.assertFalse(self.o.hit(3,"ACTIVE",125,eid,1,42,False,False,50,True))
        self.assertTrue(self.o.hit(3,"ACTIVE",125,eid,1,42,False,False,49,True))

    def test_no_los(self):
        eid=self.o.mint(3,"ACTIVE",120,True)
        self.assertFalse(self.o.hit(3,"ACTIVE",125,eid,1,42,False,False,25,False))

    def test_no_cross_round_damage(self):
        eid=self.o.mint(3,"ACTIVE",120,True)
        self.assertFalse(self.o.hit(4,"ACTIVE",125,eid,1,42,False,False,25,True))

    def test_expired_round_no_damage(self):
        eid=self.o.mint(3,"ACTIVE",120,True)
        self.assertFalse(self.o.hit(3,"ACTIVE",460,eid,1,42,False,False,25,True))

    def test_results_no_damage(self):
        eid=self.o.mint(3,"ACTIVE",120,True)
        self.assertFalse(self.o.hit(3,"RESULTS",200,eid,1,42,False,False,25,True))

    def test_explicit_close_revokes_damage(self):
        eid=self.o.mint(3,"ACTIVE",120,True)
        self.o.closed=True
        self.assertFalse(self.o.hit(3,"ACTIVE",125,eid,1,42,False,False,25,True))

if __name__=="__main__":
    unittest.main()
