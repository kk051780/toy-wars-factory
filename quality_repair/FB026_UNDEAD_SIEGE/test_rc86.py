"""Real XML/source identity and attack/loot integration checks; not Studio runtime QA."""
import json,io,hashlib,unittest,xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile
import build_rc86 as b

class CompositeRC86Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.receipt=b.build();cls.raw=(b.HERE/b.OUT).read_bytes();cls.root=ET.fromstring(cls.raw)
  cls.current={n:s.text for n,(_,_,s) in b.sources(cls.root).items()}
  with ZipFile(b.PARENT) as z:
   with ZipFile(io.BytesIO(z.read(z.namelist()[0]))) as zz:
    cls.parent=zz.read([x for x in zz.namelist() if x.endswith('.rbxlx')][0]);cls.old={n:s.text for n,(_,_,s) in b.sources(ET.fromstring(cls.parent)).items()}
    cls.old_sl=json.loads(zz.read('SOURCE_LOCK.json'))
  cls.sl=json.loads((b.HERE/'SOURCE_LOCK.json').read_text());cls.fl=json.loads((b.HERE/'RC_FEATURE_LOCK.json').read_text());cls.game=cls.current['Game'];cls.undead=cls.current['UndeadSquad'];cls.loot=cls.current['StagePickupLoot']
 def test_01_exact_parent_sha(self):self.assertEqual(b.PARENT_SHA,b.digest(self.parent))
 def test_02_exact_86_scripts(self):self.assertEqual((86,86,86),(len(self.current),self.sl['total_scripts'],self.fl['total_sources']))
 def test_03_84_old_byte_exact(self):
  self.assertEqual(84,sum(self.current[k]==s for k,s in self.old.items() if k!='Game'))
 def test_04_game_changed_only(self):self.assertNotEqual(self.game,self.old['Game'])
 def test_05_original_stage_loot_module_exact(self):self.assertEqual(self.loot,self.old['StagePickupLoot'])
 def test_06_true_stage_weapons(self):
  for k in ('SUN_BLADE','WIND_SPEAR','THUNDER_BOW','ProximityPrompt','DURATION=18','RESPAWN=15'):self.assertIn(k,self.loot)
 def test_07_stage_buff_survives_real_game_m1(self):
  for k in ('SevenJobs.StageLoot.start(map.model','SevenJobs.StageLoot.damageMultiplier','SevenJobs.StageLoot.hitOrigin','SevenJobs.StageLoot.endRound()'):self.assertIn(k,self.game)
 def test_08_stage_cleanup_and_private_gate(self):
  self.assertEqual(2,self.game.count('SevenJobs.StageLoot.endRound()'))
  self.assertIn('P0D_PRIVATE_STAGE_WEAPON_LOOT',self.loot)
  self.assertIn('game.PrivateServerId',self.loot)
 def test_09_3_actual_undead(self):
  for k in ('COUNT = 3','buildZombie','P0D_UNDEAD_SOLDIER_','MAX_TICKS = 240','ATTACK_INTERVAL = 1.45'):self.assertIn(k,self.undead)
 def test_10_undead_cast_command_modes(self):
  for k in ('SevenJobs.Undead.cast','SevenJobs.Undead.clear','sevenJobStrike(player,position,dir,dmg)'):self.assertIn(k,self.game)
  for k in ('"ATTACK"','"GUARD"','"FOLLOW"','ctx.hit(position, aim.Unit, 8)'):self.assertIn(k,self.undead)
 def test_11_undead_wall_and_enemy_ray(self):
  self.assertIn('workspace:Raycast(',self.undead)
  self.assertIn('lineHit.Instance:IsDescendantOf(neutral.model)',self.undead)
  self.assertIn('never blink through',self.undead)
 def test_12_both_modules_single_game_authority(self):
  self.assertEqual(1,self.game.count('require(script.Parent:WaitForChild("StagePickupLoot"))'))
  self.assertEqual(1,self.game.count('require(script.Parent:WaitForChild("UndeadSquad"))'))
  self.assertEqual(1,len([n for n in self.current if n=='Game']))
 def test_13_egg_score_bot_gate_preservation(self):
  for n in ('MapBuilder','SoloTeamBots','TrapperWarpService','SevenJobArmamentM1','MusouHorde'):
   self.assertEqual(self.current[n],self.old[n],n)
  self.assertIn('5.2',self.current['MapBuilder'])
  self.assertIn('GetServerTimeNow()',self.current['MapBuilder'])
 def test_14_complete_gitblob_lock(self):
  self.assertEqual(self.sl['blobs'],self.fl['source_gitblobs'])
  self.assertCountEqual([b.blob(s) for s in self.current.values()],list(self.sl['blobs'].values()))
 def test_15_deterministic_rebuild(self):
  original=self.raw;receipt=b.build();self.assertEqual(original,(b.HERE/b.OUT).read_bytes());self.assertEqual(receipt['place_sha256'],b.digest(original))
 def test_16_fails_stale_game_anchor(self):
  with self.assertRaisesRegex(ValueError,'SOURCE_DRIFT_'):
   b.up.patch_game(self.old['Game'].replace('sevenJobDelayedStrike(player,job,match.serial,root.Position,-facing,14,.8)','',1))
 def test_17_fails_double_undead_patch(self):
  with self.assertRaisesRegex(ValueError,'SOURCE_DRIFT_'):
   b.up.patch_game(self.game)
 def test_18_fails_source_drift_parent(self):
  old=b.PARENT_SHA
  try:
   b.PARENT_SHA='bad'
   with self.assertRaisesRegex(ValueError,'SOURCE_DRIFT_PARENT_LOOT85'):b.build()
  finally:b.PARENT_SHA=old
 def test_19_no_second_remote_or_persist(self):
  for text in ('RemoteEvent.new','Instance.new("RemoteEvent")','DataStoreService','UpdateAsync','ReplicatedStorage'):
   self.assertNotIn(text,self.undead)
 def test_20_game_source_features_same_85_parent(self):
  for text in ('SevenJobs.StageLoot.start(map.model','SevenJobs.StageLoot.damageMultiplier','SevenJobs.StageLoot.hitOrigin'):
   self.assertEqual(self.game.count(text),self.old['Game'].count(text))
 def test_21_undead_authentication(self):
  for text in ('sevenJobs[player]=="NECROMANCER"','match.serial==castSerial','carry[player]==nil','sevenJobPickAckSeq[player]==castAck','player.Character==castAvatar'):
   self.assertIn(text,self.game)
 def test_22_receipt_flags_no_fake_pass(self):
  self.assertFalse(self.receipt['official_rc_write']);self.assertFalse(self.receipt['owner_accepted'])
  self.assertEqual('NOT_RUN',self.receipt['studio']);self.assertEqual('NO_GO',self.receipt['product'])
 def test_23_anti_horde_duplicated_game(self):
  self.assertEqual(1,list(self.current).count('Game'))
  self.assertEqual(1,self.game.count('SevenJobs.Undead.cast'))
 def test_24_86_module_paths_under_same_server(self):
  self.assertIn('server/StagePickupLoot.luau',self.sl['blobs'])
  self.assertIn('server/UndeadSquad.luau',self.sl['blobs'])
if __name__=='__main__':unittest.main(verbosity=2)
