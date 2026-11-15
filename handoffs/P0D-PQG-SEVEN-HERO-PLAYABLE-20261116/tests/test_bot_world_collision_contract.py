"""Regression gate: Studio AI must not see through castle walls or attack at any range.

These tests are SOURCE-only, not proof of Roblox pathfinding or Studio play quality.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "EGGRUMBLE_BotActors.luau"
LOBBY = ROOT / "EGGRUMBLE_LobbyCastleModesPreview.server.luau"


class TestBotWorldCollisionContract(unittest.TestCase):
    def test_bot_actor_wired_without_old_omnipresent_ai(self):
        src = LOBBY.read_text(encoding="utf-8")
        self.assertIn('BotActors.start(session,Rules)', src)
        self.assertIn('WaitForChild("EGGRUMBLE_BotActors")', src)
        self.assertNotIn('Rules.damageCastle(session.rules,target.id,bot.id,18)', src)
        self.assertNotIn('for _,bot in ipairs(roster) do', src)

    def test_castle_world_not_excluded_from_raycasts(self):
        src = BOT.read_text(encoding="utf-8")
        self.assertIn('params.FilterDescendantsInstances={model}', src)
        self.assertIn('params.RespectCanCollide=true', src)
        self.assertNotIn('FilterDescendantsInstances={folder,model}', src)
        self.assertIn('workspace:Raycast(origin,direction*math.max(5,forwardDistance+2),params)', src)

    def test_ai_actions_require_approach(self):
        src = BOT.read_text(encoding="utf-8")
        self.assertIn('if actualDist<=ACTION_DISTANCE then', src)
        self.assertIn('Rules.takeEggs(session.rules,id,1,enemy.id)', src)
        self.assertIn('Rules.depositEggs(session.rules,id,me.heldEggs)', src)
        self.assertIn('Rules.damageCastle(session.rules,enemy.id,id,26)', src)
        self.assertIn('tryHeroAttack(actor,me,session,lastHit)', src)
        self.assertIn('local actualDist=', src)


if __name__ == "__main__":
    unittest.main()
