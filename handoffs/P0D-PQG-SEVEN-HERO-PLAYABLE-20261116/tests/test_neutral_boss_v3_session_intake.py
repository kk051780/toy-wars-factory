"""Original StoneGiant, NOT a cloned boss, into same V3 session with strict fences.

Python source assertions are not Studio combat proof. Native Luau smoke exercises
Fence.active/mayEngage with real TEAM and BR simultaneous state.
"""
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BOSS=(ROOT/"EGGRUMBLE_NeutralStoneGiant.luau").read_text(encoding="utf-8")
FENCE=(ROOT/"EGGRUMBLE_BossSessionFence.luau").read_text(encoding="utf-8")
HOST=(ROOT/"EGGRUMBLE_LobbyCastleModesPreview.server.luau").read_text(encoding="utf-8")
HERO=(ROOT/"EGGRUMBLE_SevenRoleCombat.luau").read_text(encoding="utf-8")
PROJECT=json.loads((ROOT/"EGGRUMBLE_V3_STUDIO.project.json").read_text(encoding="utf-8"))

class BossV3SourceIntake(unittest.TestCase):
 def test_original_source_reused_not_new_boss_or_standalone_world(self):
  self.assertIn('NeutralStoneGiant.spawn(session.world,',HOST)
  self.assertEqual(HOST.count('NeutralStoneGiant.spawn(session.world,'),1)
  self.assertIn('local NeutralStoneGiant=require(script.Parent:WaitForChild("EGGRUMBLE_NeutralStoneGiant"))',HOST)
  self.assertIn('local BossSessionFence=require(script.Parent:WaitForChild("EGGRUMBLE_BossSessionFence"))',HOST)
  self.assertIn('Boss.spawn(workspace', (ROOT/"EGGRUMBLE_NeutralBossPreview.server.luau").read_text())
  self.assertIn('function Boss.spawn(parent:Instance,at:Vector3,options:any?):any',BOSS)
  self.assertIn('function Boss.spawn(',BOSS)

 def test_boss_aoe_does_not_cross_into_other_mode_or_finished_match(self):
  for required in (
   'and sessions[mode]==session',
   'and session.rules.phase=="ACTIVE" and session.rules.winner==nil',
   'if joined[userId]~=mode then return false end',
   'local owner=session.rules.castles[tostring(userId)]',
   'return owner~=nil and owner.alive==true',
   'if eliminated or not Fence.active(',
  ):
   self.assertIn(required,FENCE)
  self.assertIn('if not authorized(player) then continue end',BOSS)
  self.assertIn('while active and model.Parent and sessionActive() do',BOSS)
  self.assertIn('if not active or not sessionActive() then break end',BOSS)
  self.assertIn('isMatchActive=function()',HOST)
  self.assertIn('return BossSessionFence.active(mode,session,sessions)',HOST)
  self.assertIn('return BossSessionFence.mayEngage(mode,session,sessions,joined,',HOST)
  self.assertIn('player:GetAttribute("EGGRUMBLE_Eliminated")==true',HOST)
  self.assertIn('h:TakeDamage(28)',BOSS)

 def test_all_7_skill_attacks_reach_real_boss_weakpoint_not_fake_ko(self):
  for token in (
   'local boss=session.boss',
   'local weakpoint=boss and boss.weakpoint',
   'AttackGeometry.allowed(root.Position,center,weakpoint.Position,area,spec.shape)',
   'lineClear(root.Position+Vector3.new(0,1.5,0),weakpoint.Position,char,boss.model)',
   'boss.damageFrom(p,math.min(100,amount*boost),true)',
   'if validBossHit then',
   'ImpactFeedback.hit(boss.model,role)',
  ):
   self.assertIn(token,HERO)
  self.assertIn('local maxReach=if fromAuthorizedSkill==true then 36 else 14',BOSS)
  self.assertIn('local MIN_HIT_INTERVAL=.22',BOSS)
  self.assertIn('lastStrike[player.UserId]=now',BOSS)
  self.assertIn('model:SetAttribute("EGGRUMBLE_BossHealth",health)',BOSS)
  self.assertIn('session.bossDefeats=(session.bossDefeats or 0)+1',HOST)
  self.assertIn('player:SetAttribute("EGGRUMBLE_BossDefeats",total+1)',HOST)
  self.assertNotIn('session.neutralTotal+=1',HOST)
  self.assertNotIn('credit(id)',BOSS)
  self.assertIn('if options and options.onDefeat then',BOSS)

 def test_optional_boss_failure_never_destroys_core_round(self):
  self.assertIn('local bossOK,bossOrError=pcall(function()',HOST)
  self.assertIn('session.bossStatus="YELLOW_BOSS_OPTIONAL"',HOST)
  self.assertIn('if orphan then orphan:Destroy() end',HOST)
  self.assertIn('session.bossStatus="READY"',HOST)
  self.assertIn('BotActors.start(session,Rules)',HOST)
  self.assertIn('SwarmCombat.start(session)',HOST)
  self.assertIn('RaidItemIntake.start(session,root,FieldItems)',HOST)
  self.assertIn('return {model=model,weakpoint=eye,damageFrom=damageFrom,',BOSS)

 def test_one_boss_module_and_one_real_match_script_in_rojo(self):
  server=PROJECT["tree"]["ServerScriptService"]
  self.assertEqual(server["EGGRUMBLE_NeutralStoneGiant"]["$path"],"EGGRUMBLE_NeutralStoneGiant.luau")
  self.assertEqual(server["EGGRUMBLE_BossSessionFence"]["$path"],"EGGRUMBLE_BossSessionFence.luau")
  self.assertNotIn("EGGRUMBLE_NeutralBossPreview",server)
  self.assertEqual(sum(k=="EGGRUMBLE_LobbyCastleModesPreview" for k in server),1)
  for bad in ('DataStoreService','MarketplaceService','TeleportService','Instance.new("RemoteEvent")'):
   for src in (HOST,BOSS,FENCE,HERO):
    self.assertNotIn(bad,src)

if __name__=="__main__":
 unittest.main()
