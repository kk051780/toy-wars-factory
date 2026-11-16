"""EGGRUMBLE animation and God form author contract (SOURCE, not Studio behavior proof)."""
from pathlib import Path
import json
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
ANIM=(ROOT/"EGGRUMBLE_ProceduralSkills.client.luau").read_text(encoding="utf-8")
MANTLE=(ROOT/"EGGRUMBLE_DivineMantle.luau").read_text(encoding="utf-8")
HERO=(ROOT/"EGGRUMBLE_SevenRoleCombat.luau").read_text(encoding="utf-8")
PROJECT=json.loads((ROOT/"EGGRUMBLE_V3_STUDIO.project.json").read_text())

class TrueCastAndDivineTests(unittest.TestCase):
    def test_only_authorized_server_skill_causes_cast_signature(self):
        cast=HERO.index('p:SetAttribute("EGGRUMBLE_SkillCastSignature",')
        authorized=HERO.index('if now-(perPlayer[key] or -10000)<cd then return end')
        self.assertLess(authorized,cast)
        self.assertIn('castSequence[p.UserId]=(castSequence[p.UserId] or 0)+1',HERO)
        self.assertIn('role..":"..slot..":"..tostring(castSequence[p.UserId])',HERO)
        self.assertIn('p:GetAttribute("EGGRUMBLE_Role")~=role',HERO)
        self.assertIn('if not owner or not owner.alive then return end',HERO)
        self.assertIn('if session.rules.phase~="ACTIVE" then return end',HERO)
        self.assertIn('if tool.Parent~=p.Character then return end',HERO)
        self.assertNotIn('RemoteEvent',HERO)

    def test_supports_avatar_joint_upgrade_and_r6_r15_without_overwriting_c0(self):
        for token in ('found:IsA("AnimationConstraint")','found:IsA("Motor6D")',
                      'RunService.PreSimulation:Connect(', 'joint.Transform=',
                      'RightShoulder','Right Shoulder','LeftShoulder',
                      'Left Shoulder','Waist','RootJoint',
                      'MAX_ANIMATED_AVATARS=16','MAX_VIEW_DISTANCE=130'):
            with self.subTest(token=token):
                self.assertIn(token,ANIM)
        self.assertNotIn('.C0=',ANIM)
        self.assertNotIn('.C1=',ANIM)
        self.assertNotIn('FireServer(',ANIM)
        self.assertNotIn('Instance.new("RemoteEvent")',ANIM)
        self.assertIn('if count>=MAX_ANIMATED_AVATARS and not active[player.UserId] then return end',ANIM)
        self.assertIn('if not character or not character.Parent or not hum or hum.Health<=0',ANIM)

    def test_all_seven_have_distinct_arm_and_waist_profiles(self):
        for role in ('WARRIOR','MAGE','NINJA','TRAPPER','BUILDER','BEAST','ZOMBIE'):
            self.assertIn('if role=="'+role+'" then' if role=='WARRIOR'
                          else 'elseif role=="'+role+'" then',ANIM)
        self.assertIn('local DURATION={A=.26,B=.48,C=.82}',ANIM)
        self.assertIn('if slot=="B" then',ANIM)
        self.assertIn('elseif slot=="C" then',ANIM)
        self.assertIn('EGGRUMBLE_SkillCastSignature',ANIM)

    def test_kami_is_true_six_second_character_bound_transformation(self):
        for token in ('DivineMantle.activate(p,6)', 'DivineMantle.cancel(p)',
                      'char:GetAttribute("EGGRUMBLE_KamiUntil")',
                      'char:GetAttribute("EGGRUMBLE_GiantFeedUntil")',
                      'current:SetAttribute("EGGRUMBLE_GiantFeedUntil",0)'):
            self.assertIn(token,HERO)
        for token in ('MAX_ACTIVE_MANTLES=8','PART_LIMIT_PER_MANTLE=6',
                      'EGGRUMBLE_DivineMantle','EGGRUMBLE_DivineVisualActive',
                      'char:SetAttribute("EGGRUMBLE_KamiUntil",untilTime)',
                      'DivineCircleBack','DivineFlameLeft','DivineFlameRight',
                      'DivineSealSun','DivineSealMoon','DivineSealStar',
                      'WeldConstraint','CanCollide=false','Massless=true',
                      'task.delay(duration,function()', 'if entry and entry.token==token then',
                      'Mantle.cancel(player)'):
            with self.subTest(token=token):
                self.assertIn(token,MANTLE)
        self.assertNotIn('p:SetAttribute("EGGRUMBLE_KamiUntil",now+6)',HERO)
        self.assertNotIn('p:SetAttribute("EGGRUMBLE_GiantFeedUntil",now+5)',HERO)
        self.assertIn('if num>=MAX_ACTIVE_MANTLES then return true end',MANTLE)
        self.assertIn('if parts>=PART_LIMIT_PER_MANTLE then return end',MANTLE)

    def test_studio_wires_local_and_server_separately(self):
        tree=PROJECT['tree']
        self.assertEqual(tree['ServerScriptService']['EGGRUMBLE_DivineMantle']['$path'],
                         'EGGRUMBLE_DivineMantle.luau')
        client=tree['StarterPlayer']['StarterPlayerScripts']
        self.assertEqual(client['EGGRUMBLE_ProceduralSkills']['$path'],
                         'EGGRUMBLE_ProceduralSkills.client.luau')
        self.assertEqual(client['EGGRUMBLE_CombatFeel']['$path'],
                         'EGGRUMBLE_CombatFeel.client.luau')
        self.assertNotIn('EGGRUMBLE_ProceduralSkills',tree['ServerScriptService'])
        self.assertNotIn('EGGRUMBLE_DivineMantle',client)

if __name__=="__main__":
    unittest.main()
