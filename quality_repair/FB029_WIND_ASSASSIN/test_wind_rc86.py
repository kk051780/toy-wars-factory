"""FB029 source-identity / negative regression tests; NOT Studio engine evidence."""
import hashlib, json, unittest, xml.etree.ElementTree as ET
from zipfile import ZipFile
import build_wind_rc86 as b

class WindGameTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.receipt=b.build()
  with ZipFile(b.PARENT_ZIP) as z:
   cls.parent=z.read(next(n for n in z.namelist() if n.endswith('.rbxlx')))
   cls.before={k:v.text for k,v in b.source_nodes(ET.fromstring(cls.parent)).items()}
  cls.raw=b.OUTPUT.read_bytes()
  cls.now={k:v.text for k,v in b.source_nodes(ET.fromstring(cls.raw)).items()}
  cls.lock=json.loads((b.HERE/'SOURCE_LOCK.json').read_text())
  cls.feature=json.loads((b.HERE/'RC_FEATURE_LOCK.json').read_text())
 def test_01_parent_binary_exact(self):self.assertEqual(b.PARENT_SHA,b.sha(self.parent))
 def test_02_full_86_script_count(self):self.assertEqual((86,86),(len(self.now),self.lock['total_scripts']))
 def test_03_84_existing_script_bodies_unchanged(self):
  self.assertEqual(84,sum(self.now[n]==old for n,old in self.before.items() if n not in ('Game','TrapRaidersHUD')))
 def test_04_original_wind_rule_still_authoritative(self):
  self.assertEqual(self.now['S1RaiderWindRules'],self.before['S1RaiderWindRules'])
  self.assertEqual(1,self.now['Game'].count('WindRules.canActivate(windInput)'))
 def test_05_original_author_476_alias_exact(self):
  self.assertIn('sevenJobs[player] == "NINJA"',self.now['Game'])
  self.assertIn('sevenJobSelected[player] == true',self.now['Game'])
  self.assertIn('privateHordeTrialAllowed()',self.now['Game'])
 def test_06_studio_walkable_raycast(self):
  for p in ('workspace:Raycast(root.Position+Vector3.new(0,1,0)','ground.Normal.Y<0.65','ground.Instance.Anchored','ground.Instance.CanCollide'):
   self.assertIn(p,self.now['Game'])
 def test_07_keep_actual_original_field_bounds(self):
  self.assertIn('windInput.arenaMaxX=math.min(178,grass.Size.X*.5-5)',self.now['Game'])
  self.assertIn('windInput.arenaMaxZ=math.min(140,grass.Size.Z*.5-6)',self.now['Game'])
  self.assertNotIn('windInput.arenaMaxX=178\n',self.now['Game'])
 def test_08_hud_ninja_button_and_cooldown(self):
  for p in ('assassinWind=(s.jobStudioPvE==true and s.jobSelected==true','s.job=="NINJA"','(s.role=="RAIDER" or assassinWind)','windCooldown == 0'):
   self.assertIn(p,self.now['TrapRaidersHUD'])
 def test_09_trap_and_wind_touch_no_overlap(self):
  self.assertIn('UDim2.new(1,-260,1,-110)',self.now['TrapRaidersHUD'])
  self.assertIn('trapButton.Visible = s.phase == "ACTIVE" and s.role == "GUARDIAN"',self.now['TrapRaidersHUD'])
 def test_10_existing_three_stage_weapons_survive(self):
  self.assertEqual(self.now['StagePickupLoot'],self.before['StagePickupLoot'])
  self.assertIn('SevenJobs.StageLoot.damageMultiplier',self.now['Game'])
 def test_11_existing_three_undead_survive(self):
  self.assertEqual(self.now['UndeadSquad'],self.before['UndeadSquad'])
  self.assertEqual(1,self.now['Game'].count('SevenJobs.Undead.cast'))
 def test_12_castle_egg_solo_ai_untouched(self):
  for n in ('MapBuilder','SoloTeamBots','TrapperWarpService','SevenJobArmamentM1','MusouHorde'):
   self.assertEqual(self.now[n],self.before[n])
 def test_13_source_gitblobs_lock(self):
  self.assertEqual(self.lock['blobs'],self.feature['source_gitblobs'])
  self.assertCountEqual(list(self.lock['blobs'].values()),[b.blob(s) for s in self.now.values()])
 def test_14_single_remote_and_input(self):
  self.assertEqual(1,self.now['Game'].count('remote.OnServerEvent:Connect('))
  self.assertEqual(2,self.now['TrapRaidersHUD'].count('action("WIND_BURST", nil)'))
 def test_15_stage_loot_and_undead_unchanged_sha(self):
  self.assertEqual(self.receipt['original_loot_gitblob'],b.blob(self.before['StagePickupLoot']))
  self.assertEqual(self.receipt['original_undead_gitblob'],b.blob(self.before['UndeadSquad']))
 def test_16_source_duplicate_patch_fails_closed(self):
  with self.assertRaisesRegex(ValueError,'SOURCE_DRIFT_'):
   b.patch(self.now['Game'],self.now['TrapRaidersHUD'])
 def test_17_bad_parent_hash_fails_closed(self):
  old=b.PARENT_SHA
  try:
   b.PARENT_SHA='bad'
   with self.assertRaisesRegex(ValueError,'SOURCE_DRIFT_PARENT86'):b.build()
  finally:b.PARENT_SHA=old
 def test_18_reproducible_build(self):
  before=self.raw
  self.assertEqual(before,(b.build() and b.OUTPUT.read_bytes()))
 def test_19_no_unverified_product_pass(self):
  self.assertEqual(self.receipt['studio'],'NOT_RUN');self.assertEqual(self.receipt['product'],'NO_GO')
  self.assertFalse(self.receipt['official_rc_write'])
 def test_20_hud_no_new_remotes_or_on_frame_loop(self):
  self.assertEqual(self.now['TrapRaidersHUD'].count('remote:FireServer'),self.before['TrapRaidersHUD'].count('remote:FireServer'))
  self.assertEqual(self.now['TrapRaidersHUD'].count('RenderStepped'),self.before['TrapRaidersHUD'].count('RenderStepped'))
if __name__=='__main__':unittest.main(verbosity=2)
