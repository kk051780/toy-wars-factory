"""EGGRUMBLE battle feel: actual-hit proof, 7 weapon silhouettes, local camera limits.

Source contract only. Native Luau / real Studio and Android must still be run.
"""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HERO=(ROOT/"EGGRUMBLE_SevenRoleCombat.luau").read_text(encoding="utf-8")
SWARM=(ROOT/"EGGRUMBLE_SwarmCombat.luau").read_text(encoding="utf-8")
IMPACT=(ROOT/"EGGRUMBLE_ImpactFeedback.luau").read_text(encoding="utf-8")
CLIENT=(ROOT/"EGGRUMBLE_CombatFeel.client.luau").read_text(encoding="utf-8")
WEAPONS=(ROOT/"EGGRUMBLE_WeaponSilhouettes.luau").read_text(encoding="utf-8")
FX=(ROOT/"EGGRUMBLE_SkillFX.luau").read_text(encoding="utf-8")
PROJECT=json.loads((ROOT/"EGGRUMBLE_V3_STUDIO.project.json").read_text())

class CombatFeelQuality(unittest.TestCase):
    def test_human_and_ai_contact_only_after_actual_take_damage(self):
        first=HERO.index("h:TakeDamage(damage*duel*mark)")
        marker=HERO.index("ImpactFeedback.hit(enemy,")
        self.assertLess(first,marker)
        human=HERO.index("enemyHum:TakeDamage(damage*duel*mark)")
        human_marker=HERO.index("ImpactFeedback.hit(enemyChar,")
        self.assertLess(human,human_marker)
        self.assertIn("ImpactFeedback.attacker(p,role,slot,hits)",HERO)
        self.assertIn("if actualHits<=0 or not player.Parent then return false end",IMPACT)
        self.assertIn("ImpactFeedback.clear(p)",HERO)

    def test_mob_hit_and_ko_fx_require_real_server_health_change(self):
        for token in ('h.Died:Connect(function()', 'ImpactFeedback.ko(all,m,',
                      'h:TakeDamage(damage)', 'ImpactFeedback.hit(model,',
                      'h:GetAttribute("LastAttackerId")'):
            with self.subTest(token=token): self.assertIn(token,SWARM)
        self.assertLess(SWARM.index('h:TakeDamage(damage)'),SWARM.index('ImpactFeedback.hit(model,'))
        self.assertIn('if actualHits<=0',IMPACT)
        self.assertNotIn('RemoteEvent',IMPACT)
        self.assertNotIn('MarketplaceService',IMPACT)

    def test_hit_fx_budgets_enforced_even_when_110_mobs_hit(self):
        for token in ('MAX_FEEDBACK_PER_SEC=18','MAX_LIVE_HIGHLIGHTS=10',
                      'MAX_KO_BURSTS_PER_SEC=6','ATTACKER_FEEDBACK_CD=.16',
                      'if hitCount>=MAX_FEEDBACK_PER_SEC then return false end',
                      'or highlights>=MAX_LIVE_HIGHLIGHTS',
                      'if koCount>=MAX_KO_BURSTS_PER_SEC then return false end',
                      'DepthMode=Enum.HighlightDepthMode.Occluded',
                      'EGGRUMBLE_HitFlashActive','Debris:AddItem(hl,.13)',
                      'Debris:AddItem(ring,.32)'):
            with self.subTest(token=token): self.assertIn(token,IMPACT)

    def test_phone_camera_small_reduced_motion_and_no_fake_hit(self):
        for token in ('EGGRUMBLE_ImpactSequence','GetAttributeChangedSignal(',
                      'EGGRUMBLE_ImpactWeight','EGGRUMBLE_ReducedEffects',
                      'MAX_ANGLE=.006','MAX_PUSH=.06','IMPACT_WINDOW=.115',
                      'if reduced() then return end',
                      'Enum.RenderPriority.Camera.Value+1',
                      'UnbindFromRenderStep(',
                      'gui.ResetOnSpawn=false','gui.IgnoreGuiInset=true',
                      'mark.Visible=false'):
            with self.subTest(token=token): self.assertIn(token,CLIENT)
        self.assertNotIn('Instance.new("RemoteEvent")',CLIENT)
        self.assertNotIn("FireServer(",CLIENT)
        self.assertNotIn("Humanoid:TakeDamage(",CLIENT)

    def test_7_distinct_visible_weapons_weld_to_real_avatar(self):
        for token in ('PART_BUDGET_PER_AVATAR=8','EGGRUMBLE_ClassWeapon',
                      'EGGRUMBLE_SafeGrip','Instance.new("WeldConstraint")',
                      'p.Massless=true','p.CanCollide=false','p.CanTouch=false',
                      'p.CanQuery=false','if count>=PART_BUDGET_PER_AVATAR then return end',
                      'RightHand','Right Arm','OdachiBlade','PrismHeart',
                      'TwinDaggerFar','PsiCore','RailGunBarrelLeft',
                      'TamingHorn','SoulCage'):
            with self.subTest(token=token): self.assertIn(token,WEAPONS)
        self.assertIn("WeaponSilhouettes.attach(p,role)",HERO)
        self.assertIn("WeaponSilhouettes.clear(p)",HERO)
        for role in ("WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE"):
            self.assertIn('if role=="'+role+'" then' if role=="WARRIOR"
                          else 'elseif role=="'+role+'" then',WEAPONS)

    def test_ultimate_vfx_seven_named_signatures_and_ceiling(self):
        for name in ("ULTIMATE_WarGod_DivineHalo","ULTIMATE_Mage_StormPillar",
                     "ULTIMATE_Assassin_ShadowCross","ULTIMATE_Esper_GravitySingularity",
                     "ULTIMATE_Scientist_OverdriveCore","ULTIMATE_Beast_TitanShadow",
                     "ULTIMATE_Curse_SoulGate"):
            self.assertIn(name,FX)
        self.assertIn('if slot=="C" then',FX)
        self.assertIn("ACTIVE_LIMIT=72",FX)
        self.assertIn("MAX_NEW_PER_PULSE=6",FX)
        self.assertIn("if active>=ACTIVE_LIMIT then return nil end",FX)

    def test_studio_wiring_server_and_local_are_not_doubled(self):
        tree=PROJECT["tree"]
        server=tree["ServerScriptService"]
        for name in ("EGGRUMBLE_ImpactFeedback","EGGRUMBLE_WeaponSilhouettes"):
            self.assertIn(name,server)
            self.assertEqual(server[name]["$path"],name+".luau")
        client=tree["StarterPlayer"]["StarterPlayerScripts"]["EGGRUMBLE_CombatFeel"]
        self.assertEqual(client["$path"],"EGGRUMBLE_CombatFeel.client.luau")
        self.assertEqual(sum(1 for k in server if k=="EGGRUMBLE_LobbyCastleModesPreview"),1)

if __name__=="__main__":
    unittest.main()
