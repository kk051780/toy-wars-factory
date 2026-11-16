#!/usr/bin/env python3
"""Source-only guard for the independent Studio observer; NOT Roblox engine tests."""
from pathlib import Path
import unittest

SCRIPT = (Path(__file__).resolve().parents[1] /
          "EGGRUMBLE_StudioLiveObserver.server.luau").read_text(encoding="utf-8")

class StudioObserverSourceContract(unittest.TestCase):
    def test_studio_only(self):
        self.assertIn('if not RunService:IsStudio() then return end', SCRIPT)
        self.assertIn('ServerStorage', SCRIPT)

    def test_single_json_observation_output(self):
        self.assertIn('EGGRUMBLE_StudioLiveObserver_JSON', SCRIPT)
        self.assertIn('HttpService:JSONEncode(data)', SCRIPT)
        self.assertIn('OBSERVATION_ONLY_PRODUCT_NO_GO', SCRIPT)

    def test_live_modes_and_world_counts(self):
        for token in ('TEAM_Arena', 'BATTLE_ROYALE_Arena', 'TacticalRoute_',
                      'Castle_', 'HordeSoldier', 'AI_Actor_', 'NEUTRAL_BOSS_STONE_GIANT',
                      'EGGRUMBLE_FieldItems', 'FieldEgg_', 'ReleasedEgg_'):
            with self.subTest(token=token):
                self.assertIn(token, SCRIPT)

    def test_actual_signals_not_fake_counts(self):
        for token in ('HealthChanged:Connect', 'Died:Connect', 'CanQuery',
                      'GetAttribute("EGGRUMBLE_NeutralKOs")',
                      'GetAttribute("EGGRUMBLE_SelectedRole")'):
            with self.subTest(token=token):
                self.assertIn(token, SCRIPT)

    def test_round_isolation_and_replay_no_carryover(self):
        self.assertIn("local activeArena: {[string]: Instance} = {}", SCRIPT)
        self.assertIn("roundSerial[mode] += 1", SCRIPT)
        self.assertIn("counters[mode] = newCounters()", SCRIPT)
        self.assertIn("return activeArena[mode] == arena and arena.Parent ~= nil", SCRIPT)
        self.assertIn('state = "NOT_STARTED", counts = counts, observedEvents = newCounters()', SCRIPT)
        self.assertIn("roundSequence = roundSerial[mode]", SCRIPT)
        # Every async event callback must reject stale round identity before credit.
        self.assertEqual(SCRIPT.count("if not fromCurrentRound(mode, arena) then return end"), 3)

    def test_replay_does_not_change_game_sources(self):
        self.assertNotIn("game:GetService(\"ReplicatedStorage\")", SCRIPT)
        self.assertNotIn("Humanoid:TakeDamage(", SCRIPT)
        self.assertNotIn("SetAttribute(", SCRIPT)
        self.assertNotIn("LoadCharacter(", SCRIPT)

    def test_no_game_authority_mutations(self):
        for token in ('TakeDamage(', 'Humanoid.Health =', 'WalkSpeed =',
                      'Rules.damageCastle(', 'Rules.takeFieldEgg(', 'Rules.depositEggs(',
                      'RemoteEvent', 'DataStoreService', ':PivotTo(', ':FireServer(',
                      'MarketplaceService', ':Kick('):
            with self.subTest(token=token):
                self.assertNotIn(token, SCRIPT)

    def test_explicit_unknowns_and_safety(self):
        for token in ('castleServerHP = "NOT_INSPECTED"',
                      'eggDepositScore = "NOT_INSPECTED"',
                      'androidFpsThermal = "NOT_TESTED"',
                      'ownerFunAndArt = "NOT_TESTED"',
                      'officialRCIntegration = "NOT_CLAIMED"'):
            self.assertIn(token, SCRIPT)

if __name__ == "__main__":
    unittest.main()
