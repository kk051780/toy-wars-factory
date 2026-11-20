"""Static regression tests for the EGGRUMBLE Studio-only bot collision contract.

SOURCE-level evidence only; these cannot establish Roblox Studio/Android quality.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "EGGRUMBLE_BotActors.luau"
LOBBY = ROOT / "EGGRUMBLE_LobbyCastleModesPreview.server.luau"
ROUTER = ROOT / "EGGRUMBLE_BotPathRouter.luau"


class TestBotWorldCollisionContract(unittest.TestCase):
    def test_bot_actor_wired_without_old_omnipresent_ai(self):
        src = LOBBY.read_text(encoding="utf-8")
        self.assertIn('BotActors.start(session,Rules)', src)
        self.assertIn('WaitForChild("EGGRUMBLE_BotActors")', src)
        self.assertNotIn('Rules.damageCastle(session.rules,target.id,bot.id,18)', src)
        self.assertNotIn('for _,bot in ipairs(roster) do', src)

    def test_castle_world_not_excluded_from_pathfinding(self):
        bot = BOT.read_text(encoding="utf-8")
        pathing = ROUTER.read_text(encoding="utf-8")
        self.assertIn('PathfindingService:CreatePath(', pathing)
        self.assertIn('params.FilterDescendantsInstances={actors}', pathing)
        self.assertIn('params.RespectCanCollide=true', pathing)
        self.assertIn('routeClear(here,here+direction*step,actors)', pathing)
        self.assertIn('Router.navigate(mode..":"..id,actor,goal,AI_TICK*slow,actors)', bot)
        self.assertNotIn('FilterDescendantsInstances={folder,model}', bot + pathing)

    def test_ai_actions_require_proximity_and_clear_path(self):
        src = BOT.read_text(encoding="utf-8")
        self.assertIn('if actualDist<=ACTION_DISTANCE and clearActionPath(actor,actors,actualTarget) then', src)
        self.assertIn('Rules.takeEggs(session.rules,id,1,enemy.id)', src)
        self.assertIn('Rules.depositEggs(session.rules,id,me.heldEggs)', src)
        self.assertIn('Rules.damageCastle(session.rules,enemy.id,id,26)', src)
        self.assertIn('tryHeroAttack(actor,me,session,lastHit)', src)

    def test_wall_and_height_protect_vault_deposit_and_siege(self):
        src = BOT.read_text(encoding="utf-8")
        self.assertIn('local function clearActionPath(', src)
        self.assertIn('math.abs(origin.Y-target.Y)>4.0', src)
        self.assertIn('params.FilterDescendantsInstances={actor,actors}', src)
        self.assertIn('params.RespectCanCollide=true', src)
        self.assertIn('delta.Unit*(delta.Magnitude-4)', src)
        self.assertIn('workspace:Raycast(origin+Vector3.new(0,0.4,0)', src)


if __name__ == "__main__":
    unittest.main()
