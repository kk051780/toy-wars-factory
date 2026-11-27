"""Source-exact negative tests for real RC90 + FB033 role-specific attack FX."""
import unittest,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile
from build_fx import ROOT, PARENT, PARENT_NAME, PARENT_SHA, OUT, TARGET,read_scripts,sha,blob,patch,build

class TestRealRC90(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  with ZipFile(PARENT) as z:cls.parent=z.read(PARENT_NAME)
  cls.before=read_scripts(ET.fromstring(cls.parent))
  cls.receipt=build()
  cls.result=OUT.read_bytes()
  cls.after=read_scripts(ET.fromstring(cls.result))
  cls.src=cls.after[TARGET]['body']
  cls.old=cls.before[TARGET]['body']
 def test_01_true_parent(self):
  self.assertEqual(847767,len(self.parent));self.assertEqual(PARENT_SHA,sha(self.parent))
 def test_02_real_binary_xml(self):
  self.assertEqual(86,len(self.after));self.assertEqual(851781,len(self.result));self.assertEqual('723d0ea4fd7b5d8ae02c9e585dfa2eaafce09e62602c1548d0dc380076de2cd5',sha(self.result))
 def test_03_only_original_armament_changed(self):
  self.assertEqual([TARGET],[k for k in self.before if self.before[k]['body']!=self.after[k]['body']])
 def test_04_other_85_exact(self):
  for k in self.before:
   if k!=TARGET:self.assertEqual(self.before[k]['body'],self.after[k]['body'],k)
 def test_05_path_class_exact(self):
  self.assertEqual(set(self.before),set(self.after))
  self.assertTrue(all(self.before[k]['class']==self.after[k]['class'] for k in self.before))
 def test_06_real_three_stage_damage_untouched(self):
  a='local h,k=hitCallback(origin+dir*shot.s,dir,math.clamp(baseDamage*shot.m,1,40))'
  self.assertEqual(1,self.src.count(a));self.assertEqual(1,self.old.count(a))
  self.assertEqual(self.old[self.old.index('local PATTERNS='):self.old.index('local Debris=')],self.src[self.src.index('local PATTERNS='):self.src.index('local Debris=')])
 def test_07_seven_distinct_attack_fx(self):
  for ident in ('GREATSLASH','SPELL_ORB','SHADOW_X','PSY_SNARE','HAMMER_RIPPLE','SPEAR_LANCE','CURSED_SCYTHE'):
   self.assertIn(ident,self.src)
  self.assertEqual(1,self.src.count('local function roleImpact('))
 def test_08_three_job_and_stage_contract(self):
  self.assertIn('local heavy=stage==3',self.src)
  self.assertIn('prior.stage%3+1',self.src)
  self.assertIn('if not stages or stage<1 or stage>3',self.src)
 def test_09_noncolliding_mobile_fx(self):
  for s in ('p.CanCollide=false','p.CanTouch=false','p.CanQuery=false','p.CastShadow=false','p.Anchored=true'):
   self.assertIn(s,self.src)
  self.assertEqual(1,self.src.count('Debris:AddItem(p,lifetime+.08)'))
  self.assertIn('At most 3 animated shapes per hit, 9 per attack',self.src)
 def test_10_server_tween_no_extra_server_polling(self):
  self.assertEqual(1,self.src.count('TweenService:Create('))
  self.assertNotIn('RunService.Heartbeat',self.src)
  self.assertNotIn('remote:',self.src)
  self.assertNotIn('Players:',self.src)
 def test_11_correct_cframe_translation_primitive(self):
  self.assertIn('CFrame=at+shift',self.src)
  self.assertNotIn('at+CFrame.new(shift)',self.src)
 def test_12_original_game_and_horde_authority(self):
  for n in ('Game','MusouHorde','StagePickupLoot','TrapperWarpService','UndeadSquad','SoloTeamBots','TrapRaidersHUD'):
   matches=[k for k in self.before if k.endswith('/'+n)]
   self.assertEqual(1,len(matches),n)
   self.assertEqual(self.before[matches[0]]['body'],self.after[matches[0]]['body'])
  game=self.after['ServerScriptService/TrapRaidersS1/Game']['body']
  self.assertEqual(1,game.count('remote.OnServerEvent:Connect('))
 def test_13_manifests_exact_86(self):
  l=json.loads((ROOT/'SOURCE_LOCK.json').read_text())
  self.assertEqual(86,l['total_scripts'])
  for p,v in self.after.items():self.assertEqual({'class':v['class'],'blob':blob(v['body'])},l['scripts'][p])
 def test_14_receipt_not_product_go(self):
  self.assertFalse(self.receipt['official_rc_write'])
  self.assertEqual('NOT_RUN',self.receipt['studio'])
  self.assertEqual('NOT_RUN',self.receipt['native_luau'])
 def test_15_wrong_parent_fails_closed(self):
  broken=self.parent.replace(b'P0D_',b'X0D_',1)
  with self.assertRaises(ValueError):build(broken,write=False)
 def test_16_wrong_anchor_fails_closed(self):
  with self.assertRaises(ValueError):patch(self.old.replace('local Debris=game:GetService("Debris")','-- gone'))
 def test_17_duplicate_patch_fails_closed(self):
  with self.assertRaises(ValueError):patch(self.src)
 def test_18_deterministic_byte_for_byte(self):
  self.assertEqual(self.receipt,build())
  self.assertEqual(self.result,OUT.read_bytes())
 def test_19_original_seven_job_weapons_preserved(self):
  for title in ('GreatswordBlade','RuneStaff','ShadowBlade','TrapLauncher','SiegeHammerHead','BeastSpearShaft','NecroScytheShaft'):
   self.assertIn(title,self.src)
 def test_20_tween_shapes_nonblocking(self):
  self.assertIn('Enum.PartType.Cylinder',self.src)
  self.assertIn('Enum.PartType.Ball',self.src)
  self.assertIn('p.Parent=workspace',self.src)
  self.assertIn('TweenInfo.new(lifetime',self.src)

if __name__=='__main__':unittest.main(verbosity=2)
