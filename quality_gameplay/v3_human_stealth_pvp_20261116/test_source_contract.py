#!/usr/bin/env python3
import unittest
from pathlib import Path
from build_candidate import (AUTHOR,SOURCE_BLOB,git_blob,patch,HELPER,HIT_NEW,HIT_OLD,STATUS_NEW,STATUS_OLD,harness)

class RealOriginalContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data=AUTHOR.read_bytes()
        cls.source=data.decode("utf-8")
        cls.fixed=patch(cls.source)
        assert git_blob(data)==SOURCE_BLOB

    def test_only_two_human_targeting_calls_modified(self):
        restored=self.fixed.replace(HELPER,"",1).replace(HIT_NEW,HIT_OLD,1).replace(STATUS_NEW,STATUS_OLD,1)
        self.assertEqual(self.source,restored)
        self.assertEqual(self.fixed.count("humanCombatTargetable("),3)

    def test_all_eight_gameplay_domains_are_byte_unmodified(self):
        self.assertIn("function HeroCombat.equip",self.fixed)
        self.assertIn("local function hitBotHeroes",self.fixed)
        self.assertIn("local function neutralAndBotHit",self.fixed)
        self.assertIn("local function healAllies",self.fixed)
        self.assertIn("local function secondaryEffect",self.fixed)
        self.assertIn("local function execute",self.fixed)
        self.assertIn('local ORDER={"WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE"}',self.fixed)
        self.assertEqual(self.fixed.count("h:TakeDamage"),self.source.count("h:TakeDamage"))

    def test_real_code_native_harness_has_original_negative(self):
        fixed=harness(self.fixed,True)
        broken=harness(self.source,False)
        for token in ("HIDDEN_HUMAN_WAS_DAMAGED","EGG_CARRIER_INVULNERABILITY","BR_HOSTILE_DUEL_REGRESSION","FALLEN_CASTLE_ATTACK_REGRESSION"):
            self.assertIn(token,fixed)
            self.assertIn(token,broken)
        self.assertIn("humanCombatTargetable(enemyState,enemyPlayer)",fixed)
        self.assertNotIn("humanCombatTargetable(enemyState,enemyPlayer)",broken)

    def test_source_has_existing_ai_stealth_no_game_duplication(self):
        bot=AUTHOR.with_name("EGGRUMBLE_BotActors.luau").read_text(encoding="utf-8")
        self.assertIn('player:GetAttribute("EGGRUMBLE_StealthUntil")',bot)
        self.assertNotIn("RemoteEvent",HELPER)
        self.assertNotIn("DataStore",HELPER)

if __name__=="__main__":
    unittest.main()
