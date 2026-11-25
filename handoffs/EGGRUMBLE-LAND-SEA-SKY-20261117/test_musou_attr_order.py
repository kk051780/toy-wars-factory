#!/usr/bin/env python3
"""Fail-closed source tests for confirmed KO+Combo event ordering.

Pure source assertions do not certify Studio gameplay; native Luau is required.
"""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

HERE=Path(__file__).resolve().parent
SOURCE=(HERE/"EGGRUMBLE_LandSeaSkyTraversal.server.luau").read_text()
spec=importlib.util.spec_from_file_location(
    "musou_native_source",HERE/"make_musou_attr_order_native.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class RealKOMilestoneOrdering(unittest.TestCase):
    def test_only_one_lss_and_existing_single_swarm(self):
        self.assertIn('if not RunService:IsStudio() then return end',SOURCE)
        self.assertIn('world:FindFirstChild("NeutralHorde")',SOURCE)
        for forbidden in ('TakeDamage(', 'Instance.new("RemoteEvent")',
                          'SetAttribute("EGGRUMBLE_NeutralKOs"',
                          'SetAttribute("EGGRUMBLE_Combo"'):
            self.assertNotIn(forbidden,SOURCE)

    def test_both_real_server_attribute_signals(self):
        self.assertEqual(
            SOURCE.count('player:GetAttributeChangedSignal("EGGRUMBLE_Combo")'),1)
        self.assertEqual(
            SOURCE.count('player:GetAttributeChangedSignal("EGGRUMBLE_NeutralKOs")'),1)
        self.assertIn('lastKOAdvanceAt[userId]=now',SOURCE)
        self.assertIn('lastComboAdvanceAt[userId]=now',SOURCE)
        self.assertIn('lastShownCombo[userId]=combo',SOURCE)
        self.assertNotIn('if ko<=last then return end',SOURCE)

    def test_per_user_round_reset_and_cleanup(self):
        for marker in (
            'if ko<oldKO or combo<oldCombo then',
            'lastKOAdvanceAt[userId]=nil',
            'lastComboAdvanceAt[userId]=nil',
            'lastShownCombo[userId]=nil',
            'for _,conn in ipairs(pair) do conn:Disconnect() end',
            'for player in pairs(combatConnections) do unwatchCombo(player) end',
            'table.clear(lastComboAdvanceAt)',
            'table.clear(lastKOAdvanceAt)',
            'table.clear(lastShownCombo)',
            'MUSOU_MAX_BURSTS_PER_SEC = 2',
            'MUSOU_EFFECT_TTL = 0.46',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker,SOURCE)

    def test_pulse_confirmation_follows_runtime_guards(self):
        block=SOURCE.split(" local function onCombatCombo(player)",1)[1].split(
            " local function unwatchCombo(player)",1)[0]
        # No milestone is marked spent until it has passed a live current
        # session, actual alive character, locality and rate-limit checks.
        for earlier in ("matchHuman(player,mode,world,nil)",
                        "MUSOU_BEACON_RADIUS",
                        "MUSOU_MAX_BURSTS_PER_SEC",
                        "lastSurgeAt[player.UserId]"):
            with self.subTest(earlier=earlier):
                self.assertLess(block.index(earlier),
                                block.index("lastShownCombo[userId]=combo"))
        self.assertLess(block.index("lastShownCombo[userId]=combo"),
                        block.index('Instance.new("Part")'))
        self.assertIn("Debris:AddItem(wave,MUSOU_EFFECT_TTL)",block)

    def test_source_derived_native_harness_and_mutant(self):
        with TemporaryDirectory() as tmp:
            folder=Path(tmp)
            valid=folder/"valid.luau"
            mutant=folder/"mutant.luau"
            module.make(valid,mutant)
            a,b=valid.read_text(),mutant.read_text()
            self.assertIn('check("ko_then_combo"',a)
            self.assertIn('check("combo_then_ko"',a)
            self.assertIn('check("repeat_same_combo"',a)
            self.assertIn('or shown==combo',a)
            self.assertNotIn('or shown==combo',b)
            self.assertIn('or false',b)
            self.assertEqual(a.count('local function musouConfirmedMilestone'),1)
            self.assertEqual(b.count('local function musouConfirmedMilestone'),1)

if __name__=="__main__":
    unittest.main()
