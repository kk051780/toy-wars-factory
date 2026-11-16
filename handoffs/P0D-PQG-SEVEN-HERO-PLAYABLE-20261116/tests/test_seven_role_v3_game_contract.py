"""Regression: seven unique class-action pathways in the same V3 round.

CI checks source structure and wiring. Real Roblox Studio, performance, animation,
all-vs-human PvP, and art remain NO_GO until genuine engine validation.
"""
from pathlib import Path
import json
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
HERO=(ROOT/"EGGRUMBLE_SevenRoleCombat.luau").read_text(encoding="utf-8")
V3=(ROOT/"EGGRUMBLE_LobbyCastleModesPreview.server.luau").read_text(encoding="utf-8")
GUARD=(ROOT/"EGGRUMBLE_InteractionGuard.luau").read_text(encoding="utf-8")
BOTS=(ROOT/"EGGRUMBLE_BotActors.luau").read_text(encoding="utf-8")
PROJECT=json.loads((ROOT/"EGGRUMBLE_V3_STUDIO.project.json").read_text())

class TestSevenRolesSameV3Match(unittest.TestCase):
 def test_7_roles_and_21_named_skills(self):
  ids=("WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE")
  for role in ids:
   self.assertIn(role+'={name=',HERO)
   self.assertIn('if role=="'+role+'" then' if role=="WARRIOR"
                 else 'elseif role=="'+role+'" then',HERO)
  skills=re.findall(r'^\s*(?:WARRIOR|MAGE|NINJA|TRAPPER|BUILDER|BEAST|ZOMBIE)=\{name="[^"]+",color=.*?skills=\{(".*?")\}\},?$',
                    HERO,re.M)
  self.assertEqual(len(skills),7)
  self.assertEqual(sum(len(re.findall(r'"[^"]+"',x)) for x in skills),21)
  self.assertIn('WARRIOR={name="武神"',HERO)
  self.assertIn('NINJA={name="暗殺者"',HERO)
 def test_3_actions_are_real_tools_not_inert_labels(self):
  for token in ('CombatBalance.skill(role,slot)',
                'for index,slot in ipairs({"A","B","C"})',
                'Instance.new("Tool")','tool.Activated:Connect(function()',
                'execute(session,p,role,slot)','if tool.Parent~=p.Character then return end',
                'if session.rules.phase~="ACTIVE" then return end',
                'if not owner or not owner.alive then return end',
                'p:GetAttribute("EGGRUMBLE_Role")~=role',
                'EGGRUMBLE_SKILL_'):
   with self.subTest(token=token): self.assertIn(token,HERO)
 def test_same_horde_and_ai_damage_pipeline(self):
  for token in ('session.swarm.damageFromPlayer(',
                'hitBotHeroes(','h:TakeDamage(damage*duel*mark)',
                'lineClear(', 'ray.RespectCanCollide=true',
                'session.mode~="TEAM" or target.team~=state.team',
                'if owner.heldEggs==0','session.rules.phase=="ACTIVE"',
                'p.Character==char and h.Health>0'):
   with self.subTest(token=token): self.assertIn(token,HERO)
  self.assertIn('EGGRUMBLE_KamiUntil',HERO)
  self.assertIn('EGGRUMBLE_StealthUntil',HERO)
  self.assertIn('EGGRUMBLE_SlowUntil',HERO)
  self.assertIn('player:GetAttribute("EGGRUMBLE_StealthUntil")',BOTS)
  self.assertIn('AI_TICK*slow',BOTS)
 def test_lobby_binds_role_selection_and_respawn_and_death(self):
  for token in ('for i,role in ipairs(SevenRoleCombat.roleOrder())',
                'prompt(stand,"職業選択",data.name,function(p)',
                'chosenRole[p.UserId]=role',
                'SevenRoleCombat.equip(session,p,role)',
                'SevenRoleCombat.clear(player)',
                'p.CharacterAdded:Connect(function(character)',
                'SevenRoleCombat.clear(p)'):
   with self.subTest(token=token): self.assertIn(token,V3)
  self.assertIn('["職業選択"]=0.4',GUARD)
  self.assertNotIn('EGGRUMBLE_TestBlade',V3)
 def test_one_authoritative_server_script_and_six_modules(self):
  tree=PROJECT["tree"]["ServerScriptService"]
  self.assertIn('EGGRUMBLE_SevenRoleCombat',tree)
  self.assertEqual(tree['EGGRUMBLE_SevenRoleCombat']['$path'],
                   'EGGRUMBLE_SevenRoleCombat.luau')
  self.assertGreaterEqual(len(tree)-1,7) # independent other writers may add sibling modules
  self.assertEqual(sum(k.endswith('Preview') for k in tree if k!='$className'),1)
  self.assertIn('if not RunService:IsStudio() then return end',V3)
  for source in (V3,HERO):
   for banned in ('MarketplaceService','DataStoreService','RemoteEvent','TeleportService'):
    self.assertNotIn(banned,source)

if __name__=="__main__":
 unittest.main()
