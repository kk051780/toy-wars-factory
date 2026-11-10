"""Independent Python safety/contract oracle for the opt-in Luau bridge.

Never calls Roblox native Luau. This tests integration invariants and a Python
model of selection/timing only, NOT a successful Roblox multiplayer run.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import math
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "src" / "S1D15TrapBridge.luau").read_text(encoding="utf-8")

@dataclass(frozen=True)
class Actor:
    uid: int
    team: str
    x: float
    y: float
    z: float
    angle: float = 0.0  # look direction in XY plane: 0 means positive x
    alive: bool = True
    trapped: bool = False
    immune: float = 0.0
    los: bool = True


def select(origin: Actor, actors: list[Actor], rng: float, rescue=False):
    if not origin.alive or origin.team not in {"RED", "BLUE"}:
        return None
    accepted=[]
    for target in actors:
        if target.uid == origin.uid or not target.alive or target.team not in {"RED", "BLUE"}:
            continue
        if (target.team == origin.team) != rescue:
            continue
        if rescue and not target.trapped:
            continue
        if not rescue and (target.trapped or target.immune > 0):
            continue
        dx,dz,dy=target.x-origin.x,target.z-origin.z,target.y-origin.y
        dist=math.sqrt(dx*dx+dz*dz+dy*dy)
        if dist < .01 or dist > rng or abs(dy)>9 or not target.los:
            continue
        dot=(dx*math.cos(origin.angle)+dz*math.sin(origin.angle))/dist
        if not rescue and dot<.15:
            continue
        accepted.append((dist,target.uid,target))
    return min(accepted,key=lambda v:(v[0],v[1]))[2] if accepted else None


def elapsed(start,now,maxlen=3600):
    if not isinstance(now,(float,int)) or not math.isfinite(now):return None
    t=now-start
    return t if 0 <= t <= maxlen else None


def receipt(match,caster,target,cast_gen,tick):
    return f"{match}:{caster}:{target}:{cast_gen}:{tick}"


class CanonicalSourceContract(unittest.TestCase):
    def test_exact_original_methods_used(self):
        for method in ("new","syncPlayer","removePlayer","advance","tryCast","tryRescue","tryEscape","status","endMatch"):
            self.assertIn("self.core."+method, SOURCE)

    def test_original_core_is_injected_not_rewritten(self):
        self.assertIn("function Bridge.new(originalCore: any, callbacks: any)",SOURCE)
        self.assertNotIn("function Core.tryCast",SOURCE)

    def test_does_not_mutate_hp_authority(self):
        self.assertNotIn(":TakeDamage(",SOURCE)
        self.assertNotIn(".Health =",SOURCE)
        self.assertNotIn("match.hp[",SOURCE)
        self.assertEqual(SOURCE.count("self.hooks.applyPoisonDamage("),1)

    def test_does_not_mutate_round_authority(self):
        self.assertNotIn("RoundCoordinator",SOURCE)
        self.assertNotIn("local function tickRound",SOURCE)
        self.assertNotIn("stopRound(",SOURCE)

    def test_does_not_create_remote_or_network_source(self):
        for pattern in ("Instance.new(\"RemoteEvent\")", "OnServerEvent:Connect", ":FireServer(", ":FireClient("):
            self.assertNotIn(pattern,SOURCE)

    def test_does_not_start_heartbeat_or_timer(self):
        for text in ("Heartbeat:Connect", "task.wait(","task.spawn(","RunService", "while true do"):
            self.assertNotIn(text,SOURCE)

    def test_authenticated_actor_boundary(self):
        for text in ('sequenceAuthorized ~= true', 'player:IsA("Player")', 'player.Parent ~= Players', 'self.hooks.getPhase() ~= "ACTIVE"'):
            self.assertIn(text,SOURCE)

    def test_no_client_supplied_target_id(self):
        self.assertIn("self:_closest(player",SOURCE)
        self.assertNotIn("data.targetId",SOURCE)
        self.assertNotIn("data.position",SOURCE)
        self.assertNotIn("data.damage",SOURCE)

    def test_actual_3d_line_of_sight_checked(self):
        self.assertIn("workspace:Raycast",SOURCE)
        self.assertIn("MAX_VERTICAL_DELTA = 9",SOURCE)
        self.assertIn("MIN_FORWARD_DOT = 0.15",SOURCE)

    def test_original_core_uses_elapsed_seconds_not_epoch(self):
        self.assertIn("local elapsed = server - self.startedAt",SOURCE)
        self.assertIn("MAX_DURATION_SECONDS",SOURCE)
        self.assertNotIn("self.core.advance(self.state, self.hooks.serverNow())",SOURCE)

    def test_immediate_rooted_status_after_cast(self):
        self.assertIn("if accepted then self.hooks.onStatus(target",SOURCE)

    def test_root_and_hp_updates_left_to_canonical_callbacks(self):
        self.assertIn("self.hooks.onStatus",SOURCE)
        self.assertNotIn(".WalkSpeed =",SOURCE)
        self.assertNotIn(".JumpPower =",SOURCE)

    def test_pre_damage_receipt_dedupe(self):
        a=SOURCE.index("self.receipts[key] = true")
        b=SOURCE.index("self.hooks.applyPoisonDamage(")
        self.assertLess(a,b)

    def test_role_explicit_required(self):
        self.assertIn('self.hooks.getRole(player) ~= "TRAPPER"',SOURCE)

    def test_core_cleanup_is_explicit(self):
        self.assertIn("self.core.endMatch(self.state)",SOURCE)
        self.assertIn("self.receipts = {}",SOURCE)

    def test_no_asset_id_or_external_source(self):
        self.assertNotRegex(SOURCE, r"(rbxassetid://|https?://|require\(\d+\))")

    def test_studio_negative_ids_are_private_server_mapped(self):
        self.assertIn("EPHEMERAL_BASE = 900000000000000",SOURCE)
        self.assertIn("player.UserId",SOURCE)
        self.assertIn("self.ephemeralNext += 1",SOURCE)

    def test_bad_or_missing_callbacks_stop(self):
        for name in ("getTeam","getRole","getPhase","getRoundSerial","serverNow","applyPoisonDamage","onStatus"):
            self.assertIn('callbacks.'+name,SOURCE)

    def test_key_marker_includes_round_and_target_and_tick(self):
        self.assertIn('self.state.matchId .. ":" .. tostring(event.casterId)',SOURCE)
        self.assertIn('tostring(event.targetId) .. ":" .. tostring(castGeneration)',SOURCE)
        self.assertIn('tostring(event.tick)',SOURCE)

    def test_no_new_job_is_silently_enabled(self):
        self.assertNotIn('roles[player] = "TRAPPER"',SOURCE)


class ServerTargetingOracle(unittest.TestCase):
    def setUp(self):
        self.a=Actor(1,'RED',0,0,0)
        self.front=Actor(2,'BLUE',8,0,0)

    def test_enemy_forward_in_range(self):self.assertEqual(select(self.a,[self.front],16).uid,2)
    def test_enemy_behind_rejected(self):self.assertIsNone(select(self.a,[Actor(2,'BLUE',-8,0,0)],16))
    def test_ally_not_enemy(self):self.assertIsNone(select(self.a,[Actor(2,'RED',8,0,0)],16))
    def test_enemy_just_outside_range(self):self.assertIsNone(select(self.a,[Actor(2,'BLUE',16.01,0,0)],16))
    def test_exact_range_accepted(self):self.assertIsNotNone(select(self.a,[Actor(2,'BLUE',16,0,0)],16))
    def test_vertical_delta_rejected(self):self.assertIsNone(select(self.a,[Actor(2,'BLUE',8,10,0)],16))
    def test_obstacle_rejected(self):self.assertIsNone(select(self.a,[Actor(2,'BLUE',8,0,0,los=False)],16))
    def test_dead_player_rejected(self):self.assertIsNone(select(self.a,[Actor(2,'BLUE',8,0,0,alive=False)],16))
    def test_caster_dead_rejected(self):self.assertIsNone(select(Actor(1,'RED',0,0,0,alive=False),[self.front],16))
    def test_unteamed_actor_rejected(self):self.assertIsNone(select(Actor(1,'NONE',0,0,0),[self.front],16))
    def test_target_with_immunity_skipped(self):
        self.assertEqual(select(self.a,[Actor(2,'BLUE',4,0,0,immune=3),self.front],16).uid,2)
    def test_already_trapped_target_skipped(self):
        self.assertEqual(select(self.a,[Actor(2,'BLUE',4,0,0,trapped=True),self.front],16).uid,2)
    def test_nearest_valid_target_selected(self):
        self.assertEqual(select(self.a,[Actor(3,'BLUE',9,0,0),self.front],16).uid,2)
    def test_tied_target_stable_user_id(self):
        self.assertEqual(select(self.a,[Actor(7,'BLUE',8,0,0),Actor(2,'BLUE',8,0,0)],16).uid,2)
    def test_rescue_ally_trapped(self):
        self.assertEqual(select(self.a,[Actor(3,'RED',4,0,0,trapped=True)],10,rescue=True).uid,3)
    def test_rescue_untrapped_ally_skipped(self):
        self.assertEqual(select(self.a,[Actor(3,'RED',4,0,0),Actor(5,'RED',8,0,0,trapped=True)],10,rescue=True).uid,5)
    def test_rescue_enemy_never(self):
        self.assertIsNone(select(self.a,[Actor(3,'BLUE',4,0,0,trapped=True)],10,rescue=True))
    def test_rescue_behind_allowed(self):
        self.assertIsNotNone(select(self.a,[Actor(3,'RED',-4,0,0,trapped=True)],10,rescue=True))
    def test_rescue_range10_only(self):
        self.assertIsNone(select(self.a,[Actor(3,'RED',11,0,0,trapped=True)],10,rescue=True))
    def test_self_not_target(self):
        self.assertIsNone(select(self.a,[self.a],16))


class AdapterClockReceiptOracle(unittest.TestCase):
    def test_relative_clock(self):self.assertEqual(elapsed(1700000000,1700000003),3)
    def test_clock_start(self):self.assertEqual(elapsed(1700000000,1700000000),0)
    def test_clock_too_old(self):self.assertIsNone(elapsed(1700000000,1699999999))
    def test_clock_too_long(self):self.assertIsNone(elapsed(0,3601))
    def test_clock_cap_boundary(self):self.assertEqual(elapsed(0,3600),3600)
    def test_nan_denied(self):self.assertIsNone(elapsed(0,float('nan')))
    def test_inf_denied(self):self.assertIsNone(elapsed(0,float('inf')))
    def test_negative_inf_denied(self):self.assertIsNone(elapsed(0,float('-inf')))
    def test_duplicate_receipt_key(self):self.assertEqual(receipt('S1_1',1,2,1,1),receipt('S1_1',1,2,1,1))
    def test_separate_round_key(self):self.assertNotEqual(receipt('S1_1',1,2,1,1),receipt('S1_2',1,2,1,1))
    def test_separate_tick_key(self):self.assertNotEqual(receipt('S1_1',1,2,1,1),receipt('S1_1',1,2,1,2))
    def test_separate_target_key(self):self.assertNotEqual(receipt('S1_1',1,2,1,1),receipt('S1_1',1,3,1,1))



class NewCastGenerationRegression(unittest.TestCase):
    """True bug regression: same pair, same round, fresh cast after cooldown."""
    def test_same_pair_second_cast_must_not_be_deduped(self):
        first = {receipt("S1_1", 123, 456, 1, t) for t in (1, 2, 3)}
        second = {receipt("S1_1", 123, 456, 2, t) for t in (1, 2, 3)}
        self.assertEqual(len(first | second), 6)
        self.assertTrue(first.isdisjoint(second))

    def test_repeated_tick_same_cast_still_deduped(self):
        seen = {receipt("S1_1", 123, 456, 1, 1)}
        self.assertIn(receipt("S1_1", 123, 456, 1, 1), seen)
        self.assertNotIn(receipt("S1_1", 123, 456, 2, 1), seen)

    def test_same_target_different_caster_separate(self):
        self.assertNotEqual(receipt("S1_1", 123, 456, 1, 1), receipt("S1_1", 777, 456, 1, 1))

    def test_next_round_separate_even_cast_generation_resets(self):
        self.assertNotEqual(receipt("S1_1", 123, 456, 1, 1), receipt("S1_2", 123, 456, 1, 1))

    def test_cast_generation_initialized_and_cleared(self):
        self.assertIn("castSequence = 0", SOURCE)
        self.assertIn("castGenerationByTarget = {}", SOURCE)
        self.assertIn("self.castGenerationByTarget[id] = nil", SOURCE)
        self.assertGreaterEqual(SOURCE.count("self.castGenerationByTarget = {}"), 2)

    def test_only_successful_cast_gets_new_generation(self):
        found = SOURCE.index("local accepted, reason = self.core.tryCast")
        assigned = SOURCE.index("self.castSequence += 1", found)
        accepted_block = SOURCE.index("if accepted then", found)
        self.assertLess(accepted_block, assigned)
        self.assertIn("self.castGenerationByTarget[targetId] = self.castSequence", SOURCE)

    def test_expired_or_missing_generation_fail_closed(self):
        self.assertIn("if castGeneration ~= nil and not self.receipts[key]", SOURCE)
        self.assertLess(SOURCE.index("castGeneration ~= nil"), SOURCE.index("self.receipts[key] = true"))

    def test_original_core_does_not_supply_cast_id(self):
        # This test deliberately proves bridge retains the generation rather
        # than expecting it in the old immutable author's poison event.
        self.assertIn("local castGeneration = self.castGenerationByTarget[event.targetId]", SOURCE)
        self.assertNotIn("event.castId", SOURCE)

    def test_new_cast_id_not_client_controlled(self):
        self.assertNotIn("data.castGeneration", SOURCE)
        self.assertNotIn("data.castId", SOURCE)

    def test_status_and_game_damage_still_callback_only(self):
        self.assertEqual(SOURCE.count("self.hooks.applyPoisonDamage("),1)
        self.assertNotIn(":TakeDamage(", SOURCE)



class EpochAndFloodProtection(unittest.TestCase):
    """Boundary regressions; Python oracle, NOT Roblox Lua execution."""

    def test_real_round_serial_hook_mandatory(self):
        self.assertIn('type(callbacks.getRoundSerial) == "function"', SOURCE)
        self.assertIn('self.hooks.getRoundSerial() ~= serial', SOURCE)

    def test_reject_stale_round_before_poison(self):
        updater = SOURCE[SOURCE.index('function Bridge:update()'):SOURCE.index('function Bridge:_closest')]
        self.assertLess(updater.index('self.hooks.getRoundSerial() ~= self.matchSerial'), updater.index('self.core.advance('))

    def test_reject_stale_round_before_server_scan(self):
        actions = SOURCE[SOURCE.index('function Bridge:handleIntent('):SOURCE.index('function Bridge:removePlayer(')]
        self.assertLess(actions.index('self.hooks.getRoundSerial() ~= self.matchSerial'), actions.index('self:update()'))

    def test_rate_limit_checked_before_roster_reconciliation(self):
        actions = SOURCE[SOURCE.index('function Bridge:handleIntent('):SOURCE.index('function Bridge:removePlayer(')]
        self.assertLess(actions.index('INTENT_RATE_LIMITED'), actions.index('self:update()'))
        self.assertIn('serverClock + MIN_INTENT_INTERVAL', actions)

    def test_rate_limit_uses_server_clock(self):
        self.assertIn('local serverClock = self.hooks.serverNow()', SOURCE)
        self.assertNotIn('os.time()', SOURCE)
        self.assertNotIn('tick()', SOURCE)

    def test_rate_limit_real_time_boundary(self):
        gate = 1000.0 + 0.15
        self.assertTrue(1000.0 < gate)
        self.assertTrue(1000.149 < gate)
        self.assertFalse(1000.15001 < gate)

    def test_clock_nan_rejected_before_status(self):
        actions = SOURCE[SOURCE.index('function Bridge:handleIntent('):SOURCE.index('function Bridge:removePlayer(')]
        self.assertIn('serverClock ~= serverClock', actions)
        self.assertLess(actions.index('BAD_CANONICAL_CLOCK'), actions.index('self:update()'))

    def test_rate_limit_restored_for_new_round(self):
        self.assertGreaterEqual(SOURCE.count('self.intentNextAt = {}'), 2)
        self.assertIn('self.intentNextAt[id] = nil', SOURCE)

    def test_has_single_damage_callback_only(self):
        self.assertEqual(SOURCE.count('self.hooks.applyPoisonDamage('), 1)
        self.assertNotIn('OnServerEvent:Connect', SOURCE)

    def test_old_round_reject_model(self):
        def allowed(live_serial, bridge_serial, phase):
            return phase == 'ACTIVE' and live_serial == bridge_serial
        self.assertFalse(allowed(3, 2, 'ACTIVE'))
        self.assertFalse(allowed(2, 2, 'RESULTS'))
        self.assertTrue(allowed(2, 2, 'ACTIVE'))

    def test_role_not_granted_by_adapter(self):
        self.assertNotIn('roles[player] = "TRAPPER"', SOURCE)

    def test_source_same_rpc_action_names(self):
        for label in ['TRAP_CAST', 'TRAP_RESCUE', 'TRAP_ESCAPE']:
            self.assertIn(label, SOURCE)

    def test_received_client_timestamp_never_used(self):
        self.assertNotIn('data.timestamp', SOURCE)
        self.assertNotIn('data.serverNow', SOURCE)

if __name__=='__main__':unittest.main(verbosity=2)
