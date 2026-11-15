"""EGGRUMBLE V3 castle gate/physical support quality contract, source-only."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

def defects(bot,router,lobby):
    guards={
      "PathfindingService preserved": "PathfindingService:CreatePath" in router and "path:ComputeAsync" in router,
      "no fake AI siege timer": "Rules.damageCastle(session.rules,target.id,bot.id,18)" not in lobby,
      "single AI actor controller": lobby.count("BotActors.start(session,Rules)")==1,
      "interior vault via front gate": "enemyLoc+Vector3.new(0,3,-2)" in bot and "enemyLoc+Vector3.new(0,3,6)" in bot,
      "no obsolete exterior vault": "local raid=enemyLoc+Vector3.new(20,3,9)" not in bot,
      "open gate": "door.CanCollide=false" in lobby,
      "physical access ramp": '"CastleAccessRamp"' in lobby and "Vector3.new(11,.8,20)" in lobby,
      "sloped 4.5-stud rise": "CFrame.Angles(-math.atan(4.5/20),0,0)" in lobby,
      "correct bot spawn height": "pos+Vector3.new(0,-1.5,-34)" in bot and "home+Vector3.new(0,-1.5,-34)" in bot,
      "ground candidate may fail": "local function walkableSurface(pos:Vector3,actors:Instance):Vector3?" in router,
      "no missing floor": "if grounded==nil then" in router,
      "no cliff wall": "if rise>2.25 or rise< -5.5 then" in router,
      "no steep/noncolliding support": "result.Normal.Y<.65" in router and "not result.Instance.CanCollide" in router,
      "guard before move": router.find("if grounded==nil then")>=0 and router.find("model:PivotTo(CFrame.lookAt(smoothed,smoothed+direction))")>router.find("if grounded==nil then"),
      "visible world walls": "params.FilterDescendantsInstances={actors}" in router and "params.RespectCanCollide=true" in router,
      "no instant wall phase": "if not routeClear(here,here+direction*step,actors) then" in router,
      "server egg/siege LOS": "clearActionPath(actor,actors,actualTarget)" in bot and "actualDist<=ACTION_DISTANCE" in bot,
      "same mode isolation": 'Router.navigate(mode..":"..id,actor,goal,AI_TICK,actors)' in bot,
      "Studio-only": 'assert(RunService:IsStudio()' in router and "if not RunService:IsStudio() then return end" in lobby,
    }
    return [name for name,passes in guards.items() if not passes]

class TestCastleGroundedMovement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bot=(ROOT/"EGGRUMBLE_BotActors.luau").read_text(encoding="utf-8")
        cls.router=(ROOT/"EGGRUMBLE_BotPathRouter.luau").read_text(encoding="utf-8")
        cls.lobby=(ROOT/"EGGRUMBLE_LobbyCastleModesPreview.server.luau").read_text(encoding="utf-8")

    def broken(self, bot=None,router=None,lobby=None):
        return defects(self.bot if bot is None else bot,self.router if router is None else router,self.lobby if lobby is None else lobby)

    def test_candidate_pass(self):
        self.assertEqual([],self.broken())
    def test_no_ramp(self):
        self.assertIn("physical access ramp",self.broken(lobby=self.lobby.replace('"CastleAccessRamp"','"MissingRamp"')))
    def test_flat_ramp(self):
        self.assertIn("sloped 4.5-stud rise",self.broken(lobby=self.lobby.replace("-math.atan(4.5/20)","0")))
    def test_closed_gate(self):
        self.assertIn("open gate",self.broken(lobby=self.lobby.replace("door.CanCollide=false","door.CanCollide=true")))
    def test_hovering_bot(self):
        self.assertIn("correct bot spawn height",self.broken(bot=self.bot.replace("pos+Vector3.new(0,-1.5,-34)","pos+Vector3.new(0,5,-34)")))
    def test_void_cross(self):
        self.assertIn("no missing floor",self.broken(router=self.router.replace("if grounded==nil then","if false then")))
    def test_cliff_phase(self):
        self.assertIn("no cliff wall",self.broken(router=self.router.replace("if rise>2.25 or rise< -5.5 then","if false then")))
    def test_too_steep_surface(self):
        self.assertIn("no steep/noncolliding support",self.broken(router=self.router.replace("result.Normal.Y<.65","false")))
    def test_no_pathfinder(self):
        self.assertIn("PathfindingService preserved",self.broken(router=self.router.replace("path:ComputeAsync","noCompute")))
    def test_old_ghost_siege(self):
        self.assertIn("no fake AI siege timer",self.broken(lobby=self.lobby+"\\nRules.damageCastle(session.rules,target.id,bot.id,18)"))
    def test_missing_actor_loop(self):
        self.assertIn("single AI actor controller",self.broken(lobby=self.lobby.replace("BotActors.start(session,Rules)","-- missing")))
    def test_bad_exterior_vault_target(self):
        self.assertIn("no obsolete exterior vault",self.broken(bot=self.bot+"\\nlocal raid=enemyLoc+Vector3.new(20,3,9)"))
    def test_ignore_world_walls(self):
        self.assertIn("visible world walls",self.broken(router=self.router.replace("params.FilterDescendantsInstances={actors}","params.FilterDescendantsInstances={session.world}")))
    def test_disable_attack_los(self):
        self.assertIn("server egg/siege LOS",self.broken(bot=self.bot.replace("clearActionPath(actor,actors,actualTarget)","true")))

if __name__=="__main__":
    unittest.main()
