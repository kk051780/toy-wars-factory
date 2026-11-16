"""A-PREP cross-domain castle egg / class WIND / bot melee contract; no Studio claim."""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BOT = (ROOT / "EGGRUMBLE_BotActors.luau").read_text(encoding="utf-8")
POLICY = (ROOT / "EGGRUMBLE_CarrierBotTargeting.luau").read_text(encoding="utf-8")
ROLE = (ROOT / "EGGRUMBLE_SevenRoleCombat.luau").read_text(encoding="utf-8")
RULES = (ROOT / "EGGRUMBLE_CastleMatchRules.luau").read_text(encoding="utf-8")
PROJECT = json.loads((ROOT / "EGGRUMBLE_V3_STUDIO.project.json").read_text(encoding="utf-8"))

class CarrierStealthContract(unittest.TestCase):
    def test_single_actual_author_bot_is_modified(self):
        self.assertEqual(BOT.count('local CarrierBotTargeting=require('), 1)
        self.assertEqual(BOT.count('CarrierBotTargeting.canStrike('), 1)
        self.assertNotIn('and os.clock()>=(player:GetAttribute("EGGRUMBLE_StealthUntil") or 0)', BOT)

    def test_authoritative_server_egg_count_not_local_attribute(self):
        self.assertIn('session.rules.castles[tostring(player.UserId)]', BOT)
        self.assertIn('CarrierBotTargeting.canStrike(pc.heldEggs,player:GetAttribute(', BOT)
        self.assertIn('if carriedEggs > 0 then', POLICY)
        self.assertNotIn('GetAttribute("EGGRUMBLE_CarriedEggs")', BOT)

    def test_original_combat_safety_survives(self):
        for token in ['pc.alive','pc.team~=my.team','(root.Position-at).Magnitude<11',
                      'clearHeroStrike(actor,character,','BOT_ATTACK_INTERVAL',
                      'h:TakeDamage(BOT_HERO_DAMAGE)']:
            self.assertIn(token, BOT, token)

    def test_original_wind_stealth_and_egg_rules_remain(self):
        self.assertIn('if owner.heldEggs==0 and safeMove(char,root,25)', ROLE)
        self.assertIn('p:SetAttribute("EGGRUMBLE_StealthUntil",now+3)', ROLE)
        self.assertIn('thief.heldEggs+=quantity', RULES)
        self.assertIn('actor.heldEggs+=1', RULES)
        self.assertIn('function M.depositEggs', RULES)

    def test_rojo_exact_one_module_and_same_host(self):
        server = PROJECT['tree']['ServerScriptService']
        self.assertEqual(server['EGGRUMBLE_CarrierBotTargeting']['$path'],
                         'EGGRUMBLE_CarrierBotTargeting.luau')
        self.assertEqual(server['EGGRUMBLE_BotActors']['$path'],
                         'EGGRUMBLE_BotActors.luau')
        self.assertEqual(sum(k == 'EGGRUMBLE_CarrierBotTargeting' for k in server), 1)

if __name__ == "__main__":
    unittest.main()
