import io,zipfile,hashlib,json,re,xml.etree.ElementTree as ET,unittest
from pathlib import Path
from build_arsenal import HERE,build,blob,extract,PARENT
JOBS=('WARRIOR','MAGE','NINJA','TRAPPER','BUILDER','BEAST_TAMER','NECROMANCER')
class TestArsenal(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.receipt=build()
  cls.source=(HERE/'SevenJobArmamentM1.luau').read_text()
  cls.xml=(HERE/'P0D_ROLE7_REAL_ARMAMENT_M1_PRIVATE83.rbxlx').read_bytes()
  _,items=extract(cls.xml)
  cls.sources={n:t.text for n,(_,_,t) in items.items()}
  with zipfile.ZipFile(PARENT) as outer,zipfile.ZipFile(io.BytesIO(outer.read(outer.namelist()[0]))) as z:
   src=z.read([n for n in z.namelist() if n.endswith('.rbxlx')][0]);_,it=extract(src)
  cls.parent={n:t.text for n,(_,_,t) in it.items()}
 def test_83(self):self.assertEqual(len(self.sources),83)
 def test_new_only_one(self):self.assertEqual(set(self.sources)-set(self.parent),{'SevenJobArmamentM1'})
 def test_original_81_exact(self):
  self.assertTrue(all(self.sources[k]==v for k,v in self.parent.items() if k!='Game'))
 def test_module_exact(self):self.assertEqual(self.source,self.sources['SevenJobArmamentM1'])
 def test_dual_locks(self):
  l=json.loads((HERE/'SOURCE_LOCK.json').read_text());f=json.loads((HERE/'RC_FEATURE_LOCK.json').read_text())
  self.assertEqual(l['blobs'],f['source_gitblobs']);self.assertEqual(l['total_scripts'],83)
  self.assertEqual({blob(s) for s in self.sources.values()},{*l['blobs'].values()})
 def test_game_has_one_remote(self):
  self.assertEqual(self.sources['Game'].count('Instance.new("RemoteEvent")'),1)
 def test_role_selection_does_real_equipping(self):
  s=self.sources['Game'];self.assertLess(s.index('sevenJobPickAckSeq[player]=data.seq'),s.index('SevenJobs.ArmamentM1.equip(player.Character,job)'))
 def test_rebalance_revoke(self):
  s=self.sources['Game'];self.assertLess(s.index('sevenJobSelected[player]=false'),s.index('SevenJobs.ArmamentM1.clear(player.Character)'))
 def test_respawn(self):self.assertIn('SevenJobs.ArmamentM1.equip(character,sevenJobs[player])',self.sources['Game'])
 def test_public_fallback(self):
  s=self.sources['Game'];self.assertIn('touched,defeated=horde:hit(root.Position,look,',s)
  self.assertIn('and ServerStorage:GetAttribute("P0D_RC_ENABLE_SEVEN_JOBS_PVE")~=false then',s)
 def test_server_damage_authority_only(self):
  self.assertIn('return horde:hit(pos,dir,damage,now,player.Character)',self.sources['Game'])
  self.assertNotIn('TakeDamage(',self.source)
  self.assertNotIn('Instance.new("RemoteEvent")',self.source)
 def test_7_job_models(self):
  for k in JOBS:
   with self.subTest(job=k):self.assertIn(k+'=',self.source)
 def test_7_distinct_patterns(self):
  for k in JOBS:
   with self.subTest(job=k):self.assertRegex(self.source,r'(?m)^ '+k+r'=\{\{\{a=')
 def test_third_stage_multi_hit(self):
  for k in JOBS:
   pattern=r'(?ms)^ '+k+r'=\{\{\{a=.*?\}\},\{\{a=.*?\}\},\{\{a=(.*?)\}\}\}'
   self.assertRegex(self.source,pattern)
 def test_no_client_controlled_hit(self):
  self.assertNotIn('data.damage',self.sources['Game']);self.assertNotIn('data.weapon',self.sources['Game'])
 def test_egg_authority_same(self):
  b='for _, team in ipairs({"RED", "BLUE"}) do\n    map.teams[team].eggPrompt.Triggered:Connect'
  e='\n-- P0D_SAVED_PVE_MASTERY_V1:'
  self.assertEqual(self.parent['Game'].split(b)[1].split(e)[0],self.sources['Game'].split(b)[1].split(e)[0])
 def test_no_hud_change(self):self.assertEqual(self.sources['TrapRaidersHUD'],self.parent['TrapRaidersHUD'])
 def test_no_horde_change(self):self.assertEqual(self.sources['MusouHorde'],self.parent['MusouHorde'])
 def test_receipt_digest(self):self.assertEqual(self.receipt['place_sha256'],hashlib.sha256(self.xml).hexdigest())
 def test_rejected_mutant(self):
  from build_arsenal import patch_game
  with self.assertRaisesRegex(ValueError,'SOURCE_DRIFT'):
   patch_game(self.sources['Game'])
 def test_unique_module_referent(self):
  root=ET.fromstring(self.xml);refs=[x.get('referent') for x in root.iter('Item')];self.assertEqual(len(refs),len(set(refs)))
if __name__=='__main__':unittest.main()
