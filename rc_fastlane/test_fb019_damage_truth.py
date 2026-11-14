#!/usr/bin/env python3
"""QA for FB019: only acknowledge HIT after server-side effective HP reduction."""
import unittest
from pathlib import Path
from apply_fb019_server_ack import patch_game,blob,PIN_GAME
GAME = Path("/tmp/p0d_fb019_attack_gesture_dist/src/server/Game.server.luau")

class EffectiveHitResponseQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = GAME.read_bytes()
        cls.assertion_blob = blob(cls.raw)
        cls.source = patch_game(cls.raw).decode("utf8")
        start = cls.source.index("local function applyAttack(player: Player, data)")
        end = cls.source.index("-- H1 RAIDER wind:",start)
        cls.attack = cls.source[start:end]

    def test_original_game_authority_pinned(self):
        self.assertEqual(self.assertion_blob, PIN_GAME)
        self.assertEqual(self.source.count('remote.OnServerEvent:Connect('), 1)

    def test_player_damage_requires_actual_hp_change(self):
        s=self.attack
        self.assertIn("local beforeHealth = hum.Health",s)
        self.assertIn("if hum.Health < beforeHealth then",s)
        self.assertTrue(s.index("local beforeHealth") < s.index("hum:TakeDamage(") < s.index("hum.Health < beforeHealth") < s.index('attackResponse("HIT","PLAYER")'))
        self.assertIn('attackResponse("MISS","BLOCKED")',s)
        self.assertIn('elseif mobHits>0 then\n                attackResponse("HIT","MINION")',s)

    def test_bot_damage_requires_actual_hp_change(self):
        s=self.attack
        self.assertTrue(s.index("beforeBotHealth")<s.index("victim.hum:TakeDamage(")<s.index("victim.hum.Health < beforeBotHealth")<s.index('attackResponse("HIT","BOT")'))

    def test_castle_damage_requires_actual_hp_change(self):
        s=self.attack
        self.assertTrue(s.index("beforeCastleHealth")<s.index("match.hp[enemy] = math.max(")<s.index("match.hp[enemy] < beforeCastleHealth")<s.index('attackResponse("HIT","CASTLE")'))

    def test_no_new_authority_and_negative_states(self):
        s=self.attack
        self.assertEqual(s.count('remote:FireClient(player,{kind="P0D_ATTACK_RESULT"'),1)
        self.assertLess(s.index("Rules.validSeq"),s.index("Rules.canAttack"))
        self.assertLess(s.index("Rules.canAttack"),s.index('remote:FireClient(player,{kind="P0D_ATTACK_RESULT"'))
        self.assertEqual(s.count('attackResponse("HIT"'),6)
        self.assertEqual(s.count('attackResponse("MISS"'),6)
        self.assertNotIn('FireServer(',s)

    def test_invalid_source_drift_fails_closed(self):
        with self.assertRaises(AssertionError):
            patch_game(self.raw+b"\n-- UNTRUSTED SOURCE DRIFT")

if __name__=="__main__":
    unittest.main()
