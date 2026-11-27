#!/usr/bin/env python3
"""Source-exact FB034 tests. These do NOT claim Roblox Studio runtime playtesting."""
import unittest,json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile
from unittest.mock import patch as mock_patch
import build_fb034 as b

class RC91GenuineM1Receipt(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.receipt=b.build()
  cls.output=b.OUT.read_bytes()
  cls.tree=ET.fromstring(cls.output)
  cls.scripts=b.scripts(cls.tree)
  with ZipFile(b.PARENT) as z:
   cls.parent=z.read(b.PARENT_FILE)
  cls.old=b.scripts(ET.fromstring(cls.parent))
  cls.code=cls.scripts[b.TARGET]['text']
  cls.old_code=cls.old[b.TARGET]['text']
 def test_01_parent_sha(self):self.assertEqual(b.PARENT_SHA,b.sha(self.parent))
 def test_02_parent_bytes(self):self.assertEqual(b.PARENT_BYTES,len(self.parent))
 def test_03_new_place_sha(self):self.assertEqual(self.receipt['place_sha256'],b.sha(self.output))
 def test_04_new_place_bytes(self):self.assertEqual(self.receipt['place_bytes'],len(self.output))
 def test_05_still86_scripts(self):self.assertEqual(86,len(self.scripts))
 def test_06_original_85_byte_exact(self):
  changed=[k for k in self.old if self.old[k]['text']!=self.scripts[k]['text']]
  self.assertEqual([b.TARGET],changed)
  self.assertEqual(85,len(self.old)-len(changed))
 def test_07_paths_classes_exact(self):
  self.assertEqual(set(self.old),set(self.scripts))
  self.assertTrue(all(self.old[k]['class']==self.scripts[k]['class'] for k in self.old))
 def test_08_one_original_game(self):
  self.assertEqual(1,sum(x.endswith('/Game') for x in self.scripts))
  self.assertEqual(self.old['ServerScriptService/TrapRaidersS1/Game']['text'],self.scripts['ServerScriptService/TrapRaidersS1/Game']['text'])
 def test_09_one_original_remote(self):
  self.assertEqual(1,self.scripts['ServerScriptService/TrapRaidersS1/Game']['text'].count('remote.OnServerEvent:Connect('))
 def test_10_original_combat_callback_unchanged(self):
  token='hitCallback(origin+dir*shot.s,dir,math.clamp(baseDamage*shot.m,1,40))'
  self.assertEqual(1,self.code.count(token))
  self.assertEqual(1,self.old_code.count(token))
  self.assertIn('touched+=h\n        kos+=k',self.code)
 def test_11_real_hit_nonzero_only(self):
  self.assertIn('if touched>0 then\n        realHitReceipt(job,stage,origin,touched,kos)',self.code)
  self.assertEqual(1,self.code.count('realHitReceipt(job,stage,origin,touched,kos)'))
 def test_12_ko_staged_only(self):
  self.assertIn('if defeated>0 and stage==3 then',self.code)
  self.assertEqual(1,self.code.count('transientFx("REAL_KO_FINISH"'))
 def test_13_no_alwayson_overlay(self):
  self.assertIn('bubble.AlwaysOnTop=false',self.code)
  self.assertIn('bubble.MaxDistance=48',self.code)
  self.assertIn('Debris:AddItem(marker,.48)',self.code)
  self.assertNotIn('ScreenGui',self.code)
 def test_14_server_only_noncollision(self):
  self.assertIn('marker.CanCollide=false',self.code)
  self.assertIn('marker.CanQuery=false',self.code)
  self.assertIn('marker.CanTouch=false',self.code)
 def test_15_saved_role_and_stage_visuals(self):
  for s in ('WARRIOR','MAGE','NINJA','TRAPPER','BUILDER','BEAST_TAMER','NECROMANCER'):
   self.assertEqual(self.old_code.count(s+'='),self.code.count(s+'='),s)
  self.assertIn('roleImpact(job,stage,impact,dir,shot.a)',self.code)
 def test_16_no_new_remote_or_loop(self):
  self.assertNotIn('RunService.Heartbeat',self.code)
  self.assertNotIn('OnServerEvent',self.code)
  self.assertNotIn('GetDataStore(',self.code)
  self.assertNotIn('SetAsync(',self.code)
 def test_17_exact_source_lock(self):
  lock=json.loads((b.ROOT/'SOURCE_LOCK.json').read_text())
  self.assertEqual(86,lock['total_scripts'])
  self.assertEqual({k:{'blob':b.gitblob(v['text']),'class':v['class']} for k,v in self.scripts.items()},lock['scripts'])
 def test_18_exact_feature_lock(self):
  lock=json.loads((b.ROOT/'RC_FEATURE_LOCK.json').read_text())
  self.assertEqual(86,lock['total_sources'])
  exp={'/'.join(k.split('/')[2:]):b.gitblob(v['text']) for k,v in self.scripts.items()}
  self.assertEqual(exp,lock['source_gitblobs'])
 def test_19_builder_deterministic(self):
  self.assertEqual(self.receipt,b.build(write=False))
 def test_20_wrong_parent_fails_closed(self):
  damaged=bytearray(self.parent);damaged[-4]=ord('a') if damaged[-4]!=ord('a') else ord('b')
  with self.assertRaisesRegex(ValueError,'WRONG_PARENT'):b.build(bytes(damaged),write=False)
 def test_21_double_patch_rejected(self):
  with self.assertRaisesRegex(ValueError,'ANCHOR_DRIFT|DUPLICATE_FX'):b.patch(self.code)
 def test_22_anchor_drift_rejected(self):
  with self.assertRaisesRegex(ValueError,'ANCHOR_DRIFT'):b.patch(self.old_code.replace('local function unitFacing(', 'local function unitDir('))
 def test_23_receipt_explicit_nonacceptance(self):
  self.assertEqual('NOT_RUN',self.receipt['native_luau'])
  self.assertEqual('NOT_RUN',self.receipt['studio'])
  self.assertFalse(self.receipt['owner_accepted'])
  self.assertFalse(self.receipt['official_rc_write'])
 def test_24_true_horde_damage_score_untouched(self):
  for name in ['MusouHorde','SevenJobsRules','StagePickupLoot','TrapperWarpService','UndeadSquad','SoloTeamBots','MapBuilder']:
   p='ServerScriptService/TrapRaidersS1/'+name
   self.assertEqual(self.old[p]['text'],self.scripts[p]['text'])
 def test_25_previous_M1_hit_patterns_unmodified(self):
  prefix=self.old_code.split('local Debris=game:GetService("Debris")')[0]
  self.assertTrue(self.code.startswith(prefix))
  self.assertIn('baseDamage*shot.m',self.code)

if __name__=='__main__': unittest.main(verbosity=2)
