#!/usr/bin/env python3
"""Mutation-oriented tests for the additive 26->28 private script overlay."""
from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("defense_composer", ROOT / "compose_private28.py")
composer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(composer)

VALID = """
local BotActors=require(script.Parent:WaitForChild("EGGRUMBLE_BotActors"))
session.closeRound=function(abandoned:boolean?)
if session.world.Parent then session.world:Destroy() end
BotActors.start(session,Rules)
SwarmCombat.start(session)
SevenRoleCombat.equip(session,p,role)
SevenRoleCombat.equip(session,p,role)
RaidItemIntake.start(session,root,FieldItems)
NeutralStoneGiant.spawn(session.world,
"""

class TestDefensiveOverlay(unittest.TestCase):
    def test_single_stable_optional_hook(self):
        result = composer.patch_host(VALID)
        self.assertEqual(result.count("CastleDefense.start(session)"), 1)
        self.assertEqual(result.count("BotActors.start(session,Rules)"), 1)
        self.assertEqual(result.count("SwarmCombat.start(session)"), 1)
        self.assertIn("local DEFENSE_V1_ENABLED=true", result)
        self.assertEqual(result.count("session.castleDefenseStop()"), 2)
        self.assertIn("pcall(function() CastleDefense.start(session) end)", result)
        self.assertIn("YELLOW_OPTIONAL", result)

    def test_same_source_reapplication_rejected(self):
        with self.assertRaises(AssertionError):
            composer.patch_host(composer.patch_host(VALID))

    def test_must_not_overwrite_changed_author_state(self):
        for marker in ("BotActors.start(session,Rules)", "session.closeRound=function(abandoned:boolean?)",
                       "RaidItemIntake.start(session,root,FieldItems)",
                       "NeutralStoneGiant.spawn(session.world,"):
            with self.subTest(marker=marker):
                with self.assertRaises(AssertionError):
                    composer.patch_host(VALID.replace(marker, "ALTERED_API"))

    def test_duplicate_game_authority_or_loop_rejected(self):
        with self.assertRaises(AssertionError):
            composer.patch_host(VALID + "\nBotActors.start(session,Rules)")
        with self.assertRaises(AssertionError):
            composer.patch_host(VALID + "\nSwarmCombat.start(session)")

    def test_no_invented_new_game_remote_shop_or_ui(self):
        result = composer.patch_host(VALID)
        for unsafe in ("RemoteEvent.new", "DataStoreService", "MarketplaceService",
                       "Instance.new(\"ScreenGui\")", "SpawnLocation.new"):
            self.assertNotIn(unsafe, result)

    def test_removed_owner_cleanup_is_blocked(self):
        with self.assertRaises(AssertionError):
            composer.patch_host(VALID.replace(
                "if session.world.Parent then session.world:Destroy() end", "session.world:Destroy()"))

    def test_mapping_count_contract(self):
        self.assertEqual(composer.BASE_COUNT, 26)
        self.assertEqual(set(composer.ADDED), {
            "EGGRUMBLE_CastleDefensePolicy","EGGRUMBLE_CastleDefenseLive"})

if __name__ == "__main__":
    unittest.main()
