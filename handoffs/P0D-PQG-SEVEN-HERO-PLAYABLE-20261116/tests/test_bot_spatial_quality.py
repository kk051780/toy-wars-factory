"""EGGRUMBLE V3 bot exterior-raid regression — static source guards, not Studio."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]

def defects(bot: str, lobby: str, router: str) -> list[str]:
    needs={
      "single AI controller":lobby.count("BotActors.start(session,Rules)")==1,
      "no ghost siege": "Rules.damageCastle(session.rules,target.id,bot.id,18)" not in lobby,
      "author pathfinder retained":'local Router=require(script.Parent:WaitForChild("EGGRUMBLE_BotPathRouter"))' in bot and "Router.navigate(mode.." in bot,
      "pathfinder actually computes": "PathfindingService:CreatePath" in router and "path:ComputeAsync" in router,
      "no wall phasing": "if not routeClear(here,here+direction*step,actors) then" in router,
      "server LOS retained": "clearActionPath(actor,actors,actualTarget)" in bot,
      "front waypoint": "local front=enemyLoc+Vector3.new(0,3,-27)" in bot,
      "flank waypoint": "local flank=enemyLoc+Vector3.new(20,3,-18)" in bot,
      "external vault": "local raid=enemyLoc+Vector3.new(20,3,9)" in bot,
      "no interior egg waypoint": "enemyLoc+Vector3.new(0,3,6)" not in bot and "enemyLoc+Vector3.new(0,3,-2)" not in bot,
      "front reached": "stage==1 and planarDistance(here,front)<=9" in bot,
      "flank reached": "stage==2 and planarDistance(here,flank)<=9" in bot,
      "real distance and stage": "actualDist<=ACTION_DISTANCE" in bot and "raidStage[id]==3" in bot,
      "goal reset": "raidTargetOwner[id]~=enemy.id" in bot and "raidStage[id]=nil;raidTargetOwner[id]=nil" in bot,
      "grounded spawn": "home+Vector3.new(0,-3,-34)" in bot and "pos+Vector3.new(0,-3,-34)" in bot,
      "Studio only": "assert(RunService:IsStudio()" in bot and "if not RunService:IsStudio() then return end" in lobby,
    }
    return [key for key,passes in needs.items() if not passes]

class ExteriorBotRouteSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bot=(ROOT/"EGGRUMBLE_BotActors.luau").read_text(encoding="utf-8")
        cls.lobby=(ROOT/"EGGRUMBLE_LobbyCastleModesPreview.server.luau").read_text(encoding="utf-8")
        cls.router=(ROOT/"EGGRUMBLE_BotPathRouter.luau").read_text(encoding="utf-8")
    def check(self, bot=None, lobby=None, router=None):
        return defects(self.bot if bot is None else bot, self.lobby if lobby is None else lobby,self.router if router is None else router)
    def test_clean_candidate(self):
        self.assertEqual([],self.check())
    def test_old_ghost_siege(self):
        self.assertIn("no ghost siege",self.check(lobby=self.lobby+"\nRules.damageCastle(session.rules,target.id,bot.id,18)"))
    def test_remove_pathfinding(self):
        self.assertIn("author pathfinder retained",self.check(bot=self.bot.replace("Router.navigate(mode..", "no_router(mode..")))
    def test_no_path_compute(self):
        self.assertIn("pathfinder actually computes",self.check(router=self.router.replace("path:ComputeAsync","fakePathCompute")))
    def test_walk_through_wall(self):
        self.assertIn("no wall phasing",self.check(router=self.router.replace("if not routeClear(here,here+direction*step,actors) then","if false then")))
    def test_disable_line_of_sight(self):
        self.assertIn("server LOS retained",self.check(bot=self.bot.replace("clearActionPath(actor,actors,actualTarget)","true")))
    def test_old_core_goal(self):
        self.assertIn("no interior egg waypoint",self.check(bot=self.bot+"\n-- regression enemyLoc+Vector3.new(0,3,6)"))
    def test_remove_flank(self):
        self.assertIn("flank waypoint",self.check(bot=self.bot.replace("local flank=enemyLoc+Vector3.new(20,3,-18)","local flank=enemyLoc")))
    def test_early_vault_steal(self):
        self.assertIn("real distance and stage",self.check(bot=self.bot.replace("raidStage[id]==3","true")))
    def test_target_reset(self):
        self.assertIn("goal reset",self.check(bot=self.bot.replace("raidTargetOwner[id]~=enemy.id","false")))
    def test_hovering_spawn(self):
        self.assertIn("grounded spawn",self.check(bot=self.bot.replace("home+Vector3.new(0,-3,-34)","home+Vector3.new(0,5,-34)")))
    def test_invisible_ai_loop(self):
        self.assertIn("single AI controller",self.check(lobby=self.lobby.replace("BotActors.start(session,Rules)","-- never started")))

if __name__=="__main__":
    unittest.main()
