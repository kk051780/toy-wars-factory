"""EGGRUMBLE V3 source-only negative QA, not Roblox runtime proof."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
def issues(bot: str, lobby: str) -> list[str]:
    faults=[]
    checks={
      "bot wiring": "BotActors.start(session,Rules)" in lobby,
      "no timer ghost": "Rules.damageCastle(session.rules,target.id,bot.id,18)" not in lobby,
      "one actor controller": lobby.count("BotActors.start(session,Rules)")==1,
      "world walls visible": "params.FilterDescendantsInstances={model}" in bot,
      "collision filter": "params.RespectCanCollide=true" in bot,
      "wall stop": "if ahead~=nil then return false end" in bot,
      "floor support": "if support==nil or support.Normal.Y<.65 or not support.Instance.Anchored then return false end" in bot,
      "no unsafe side movement": "if resultPivot~=nil then model:PivotTo(resultPivot) end" in bot,
      "both side probes": "advanced=tryStep(lateral)" in bot and "advanced=tryStep(-lateral)" in bot,
      "front waypoint": "local front=enemyLoc+Vector3.new(0,3,-27)" in bot,
      "east flank waypoint": "local flank=enemyLoc+Vector3.new(20,3,-18)" in bot,
      "vault exterior waypoint": "local raid=enemyLoc+Vector3.new(20,3,9)" in bot,
      "front and flank reached": "stage==1 and planarDistance(here,front)<=9" in bot and "stage==2 and planarDistance(here,flank)<=9" in bot,
      "spatial action": "if actualDist<=ACTION_DISTANCE and (goHome or not hasEgg or raidStage[id]==3) then" in bot,
      "owner route reset": "raidTargetOwner[id]~=enemy.id" in bot,
      "balanced bot spawn": "home+Vector3.new(0,-3,-34)" in bot,
      "studio only": "assert(RunService:IsStudio()" in bot and "if not RunService:IsStudio() then return end" in lobby,
    }
    for key,ok in checks.items():
        if not ok: faults.append(key)
    return faults

class TestSpatialBot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bot=(ROOT/"EGGRUMBLE_BotActors.luau").read_text(encoding="utf-8")
        cls.lobby=(ROOT/"EGGRUMBLE_LobbyCastleModesPreview.server.luau").read_text(encoding="utf-8")
    def test_real_source_contract(self):
        self.assertEqual([],issues(self.bot,self.lobby))
    def test_ghost_timer_mutation(self):
        s=self.lobby+"\nRules.damageCastle(session.rules,target.id,bot.id,18)"
        self.assertIn("no timer ghost",issues(self.bot,s))
    def test_duplicate_ai_mutation(self):
        self.assertIn("one actor controller",issues(self.bot,self.lobby+"\nBotActors.start(session,Rules)"))
    def test_wall_ignored_mutation(self):
        s=self.bot.replace("params.FilterDescendantsInstances={model}","params.FilterDescendantsInstances={folder}")
        self.assertIn("world walls visible",issues(s,self.lobby))
    def test_blind_side_move_mutation(self):
        s=self.bot.replace("if resultPivot~=nil then model:PivotTo(resultPivot) end","model:PivotTo(CFrame.new(current))")
        self.assertIn("no unsafe side movement",issues(s,self.lobby))
    def test_floor_void_mutation(self):
        s=self.bot.replace("if support==nil or support.Normal.Y<.65 or not support.Instance.Anchored then return false end","-- no floor")
        self.assertIn("floor support",issues(s,self.lobby))
    def test_wall_probe_mutation(self):
        s=self.bot.replace("if ahead~=nil then return false end","-- ignore wall")
        self.assertIn("wall stop",issues(s,self.lobby))
    def test_direct_egg_mutation(self):
        s=self.bot.replace("local raid=enemyLoc+Vector3.new(20,3,9)","local raid=enemyLoc+Vector3.new(0,3,6)")
        self.assertIn("vault exterior waypoint",issues(s,self.lobby))
    def test_route_stage_bypass_mutation(self):
        s=self.bot.replace("if actualDist<=ACTION_DISTANCE and (goHome or not hasEgg or raidStage[id]==3) then","if actualDist<=ACTION_DISTANCE then")
        self.assertIn("spatial action",issues(s,self.lobby))
    def test_no_spawn_hover_mutation(self):
        s=self.bot.replace("home+Vector3.new(0,-3,-34)","home+Vector3.new(0,5,-34)")
        self.assertIn("balanced bot spawn",issues(s,self.lobby))
    def test_missing_actor_mutation(self):
        s=self.lobby.replace("BotActors.start(session,Rules)","-- not started")
        self.assertIn("bot wiring",issues(self.bot,s))

if __name__=="__main__":
    unittest.main()
