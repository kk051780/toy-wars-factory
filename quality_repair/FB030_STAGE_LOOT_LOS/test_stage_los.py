"""Exact real source and negative-controls; not a Roblox Studio physics simulation."""
import hashlib, json, unittest, xml.etree.ElementTree as ET
from zipfile import ZipFile
import build_stage_los as b

class StageWallSafety(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.receipt=b.build()
  with ZipFile(b.PARENT) as z:
   cls.parent=z.read(next(n for n in z.namelist() if n.endswith('.rbxlx')))
   cls.old={k:v.text or '' for k,v in b.source_nodes(ET.fromstring(cls.parent)).items()}
  cls.binary=b.OUTPUT.read_bytes()
  cls.new={k:v.text or '' for k,v in b.source_nodes(ET.fromstring(cls.binary)).items()}
  cls.source=cls.new[b.TARGET]
  cls.lock=json.loads((b.HERE/'SOURCE_LOCK.json').read_text())
  cls.feature=json.loads((b.HERE/'RC_FEATURE_LOCK.json').read_text())
 def test_01_parent_identity(self):self.assertEqual(b.PARENT_SHA,b.sha(self.parent))
 def test_02_86_real_scripts(self):self.assertEqual((86,86),(len(self.new),self.lock['total_scripts']))
 def test_03_only_one_module_edited(self):
  self.assertEqual([b.TARGET],sorted(n for n in self.old if self.old[n]!=self.new[n]))
 def test_04_85_other_scripts_byte_exact(self):
  self.assertEqual(85,sum(a==self.new[n] for n,a in self.old.items() if n!=b.TARGET))
 def test_05_real_game_authority_not_changed(self):
  for n in ('Game','TrapRaidersHUD','MapBuilder','MusouHorde','SoloTeamBots','TrapperWarpService','UndeadSquad','SevenJobArmamentM1'):
   self.assertEqual(self.old[n],self.new[n])
 def test_06_prompt_still_mobile(self):
  self.assertIn('prompt.HoldDuration=.3',self.source)
  self.assertIn('prompt.MaxActivationDistance=9',self.source)
  self.assertIn('prompt.Triggered:Connect(function(player)',self.source)
 def test_07_physical_server_distance_enforced(self):
  self.assertIn('if (root.Position-base.Position).Magnitude>10 then return end',self.source)
 def test_08_pickup_requires_new_server_sight(self):
  self.assertIn('if not unobstructed(player,root.Position,',self.source)
  self.assertIn('base.Position+Vector3.new(0,1.3,0),model) then return end',self.source)
 def test_09_spear_reach_cannot_cross_wall(self):
  self.assertIn('if not unobstructed(player,origin,projected,nil) then return origin end',self.source)
  self.assertIn('return projected',self.source)
  self.assertNotIn('return if v.Magnitude>.01 then origin+v.Unit*buff.reach else origin',self.source)
 def test_10_respect_collision_and_ignore_source_character(self):
  self.assertIn('params.RespectCanCollide=true',self.source)
  self.assertIn('if player.Character then table.insert(excluded,player.Character) end',self.source)
  self.assertIn('if pickupModel then table.insert(excluded,pickupModel) end',self.source)
 def test_11_no_second_line_sight_owner(self):
  self.assertEqual(1,self.source.count('local function unobstructed('))
  self.assertEqual(1,self.source.count('workspace:Raycast('))
 def test_12_three_usable_weapon_effects_preserved(self):
  for code in ('SUN_BLADE','WIND_SPEAR','THUNDER_BOW'):
   self.assertIn(code,self.source)
  self.assertEqual(self.source.count('spawnPickup(folder,index,d[1],d[2],d[3])'),1)
 def test_13_server_1800ms_epoch_cleans(self):
  self.assertEqual(self.old[b.TARGET].count('StageLoot.clearPlayer(player)'),self.source.count('StageLoot.clearPlayer(player)'))
  self.assertIn('if capture==epoch and model.Parent then setVisible(pickup,true) end',self.source)
 def test_14_all_real_sha_source_locks_match(self):
  self.assertEqual(self.lock['blobs'],self.feature['source_gitblobs'])
  self.assertCountEqual([b.blob(x) for x in self.new.values()],self.lock['blobs'].values())
 def test_15_native_not_falsely_claimed(self):
  self.assertEqual('NOT_RUN',self.receipt['native_luau'])
  self.assertEqual('NO_GO',self.receipt['product'])
  self.assertFalse(self.receipt['official_rc_write'])
 def test_16_wrong_input_rejected(self):
  orig=b.PARENT_SHA
  try:
   b.PARENT_SHA='bad'
   with self.assertRaisesRegex(ValueError,'SOURCE_DRIFT_PARENT86'):b.build()
  finally:b.PARENT_SHA=orig
 def test_17_duplicate_patch_rejected(self):
  with self.assertRaisesRegex(ValueError,'SOURCE_DRIFT_'):
   b.patch(self.source)
 def test_18_stale_original_anchor_rejected(self):
  with self.assertRaisesRegex(ValueError,'SOURCE_DRIFT_'):
   b.patch(self.old[b.TARGET].replace('local function spawnPickup(parent,index,x,z,kind)','local function invalid_anchor(parent,index,x,z,kind)'))
 def test_19_duplicate_los_refused(self):
  with self.assertRaisesRegex(ValueError,'DUPLICATE_LOS'):
   b.patch(self.old[b.TARGET].replace('local function spawnPickup(parent,index,x,z,kind)',
     'local function unobstructed() return true end\nlocal function spawnPickup(parent,index,x,z,kind)'))
 def test_20_rebuild_deterministic(self):
  first=self.binary
  self.assertEqual(first,b.OUTPUT.read_bytes())
  self.assertEqual(first,(b.build() and b.OUTPUT.read_bytes()))
 def test_21_source_only_footprint_not_add_remote(self):
  self.assertEqual(self.old['Game'].count('remote.OnServerEvent:Connect('),1)
  self.assertEqual(self.new['Game'].count('remote.OnServerEvent:Connect('),1)
 def test_22_original_buffs_no_unauthorized_damage_edit(self):
  self.assertIn('return if buff then buff.damage else 1',self.source)
  self.assertEqual(self.old[b.TARGET].count('active[player]='),self.source.count('active[player]='))
 def test_23_xml_binary_and_receipt(self):
  self.assertEqual(self.receipt['bytes'],len(self.binary))
  self.assertEqual(self.receipt['place_sha256'],b.sha(self.binary))
 def test_24_los_fail_closed_when_blocked(self):
  # Source contract: both critical callers return before side effects on BLOCKED.
  claim=self.source.index('if not unobstructed(player,root.Position,')
  award=self.source.index('active[player]={kind=kind')
  self.assertLess(claim,award)
  block=self.source.index('if not unobstructed(player,origin,projected,nil) then return origin end')
  return_shifted=self.source.index('return projected')
  self.assertLess(block,return_shifted)

if __name__=='__main__':unittest.main(verbosity=2)
