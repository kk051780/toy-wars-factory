#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path
from compose_core34 import compose,get_files,LSS,SERVER,CLIENT,STUDIO_GATE

ROOT=Path(__file__).resolve().parent

class RealmCoreContract(unittest.TestCase):
 def test_actual_runtime_sources_exist(self):
  for p in (LSS,SERVER,CLIENT):
   self.assertTrue(p.is_file(),p)
  source=SERVER.read_text(encoding="utf-8")
  client=CLIENT.read_text(encoding="utf-8")
  self.assertIn('local MAX_AIRCRAFT = 2',source)
  self.assertIn('local MAX_SEA_CREATURES = 3',source)
  self.assertIn('local function eligible(',source)
  self.assertIn('seat.Occupant~=h',source)
  self.assertIn('mode~="BATTLE_ROYALE"',source)
  self.assertIn('damageMultiplier(element,underwater)',source)
  self.assertIn('element=="FIRE" then return .15',source)
  self.assertIn('element=="LIGHTNING" then return 1.35',source)
  for s in ('FIGHTER','GUN','BOMB','CANNON','BREATH','HYDRO','THUNDER','LEVIATHAN'):
   self.assertIn(s,source)
  self.assertIn('RealmBattleIntent_V1',source)
  self.assertIn('RealmBattleIntent_V1',client)
  self.assertNotIn('RunService:IsStudio()',source)
  self.assertIn('MaxActivationDistance=13',source)
  self.assertIn('local GUN_INTERVAL = .20',source)
  self.assertIn('local BOMB_INTERVAL = 8',source)
  self.assertIn('original_31_byte_exact', (ROOT/"compose_core34.py").read_text())
 def test_hydro_mount_remote_is_rejected_before_cooldown(self):
  source=SERVER.read_text(encoding="utf-8")
  fire=source.split("local function fire(player,weapon)",1)[1].split("local controlConnection",1)[0]
  diver=fire.index("if state.divers[player] then")
  mounted=fire.index("local model,kind=findCurrentMount(player)")
  delays=fire.index("local delays={")
  guard='if weapon=="HYDRO" then return end'
  self.assertEqual(fire.count(guard),1)
  self.assertLess(diver,fire.index(guard))
  self.assertLess(fire.index(guard),mounted)
  self.assertLess(mounted,delays)
  # Removing this guard lets non-divers reach nil delays[weapon].
  mutated=fire.replace(guard,"-- HYDRO guard removed",1)
  self.assertNotIn(guard,mutated)
  self.assertIn("now-(last[weapon] or -100)<delays[weapon]",mutated)
 def make31(self,path):
  path.mkdir(parents=True,exist_ok=True)
  tree={'ServerScriptService':{}}
  names=['EGGRUMBLE_LobbyCastleModesPreview','EGGRUMBLE_SwarmCombat']
  names+=['Source%02d'%i for i in range(29)]
  for name in names:
   f=path/(name+'.server.luau');f.write_text('print("'+name+'")\n',encoding='utf-8')
   tree['ServerScriptService'][name]={'$path':f.name}
  proj=path/'V3_31.project.json'
  proj.write_text(json.dumps({'name':'fixture','tree':tree}),encoding='utf-8')
  return proj
 def test_core34_and_off31_real_paths(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory)
   original=self.make31(root/'source')
   on=root/'outputs'/'ON34.project.json'
   off=root/'outputs'/'OFF31.project.json'
   compose(original,on)
   compose(original,off,True)
   _,base=get_files(original)
   _,added=get_files(on)
   _,restored=get_files(off)
   self.assertEqual((len(base),len(added),len(restored)),(31,34,31))
   for route,file in base.items():
    self.assertEqual(added[route].read_bytes(),file.read_bytes())
    self.assertEqual(restored[route].read_bytes(),file.read_bytes())
   k=next(path for path in added if path[-1]=='EGGRUMBLE_LandSeaSkyTraversal')
   self.assertNotIn(STUDIO_GATE,added[k].read_text())
   self.assertIn(STUDIO_GATE,LSS.read_text())
   self.assertEqual(json.loads(on.with_suffix('.receipt.json').read_text())['source_count'],34)
   self.assertEqual(json.loads(off.with_suffix('.receipt.json').read_text())['source_count'],31)
 def test_reject_wrong_base(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory)
   original=self.make31(root/'source')
   model=json.loads(original.read_text())
   del model['tree']['ServerScriptService']['EGGRUMBLE_SwarmCombat']
   original.write_text(json.dumps(model))
   with self.assertRaisesRegex(ValueError,'RED_NOT_31'):
    compose(original,root/'outputs'/'ON34.project.json')
 def test_no_legacy_authority_override(self):
  source=SERVER.read_text(encoding="utf-8")
  for forbidden in ('DataStoreService','SetAsync','UpdateAsync','EGGRUMBLE_ScoreBalance',
                    'EGGRUMBLE_NeutralKOs', 'EGGRUMBLE_Combo'):
   self.assertNotIn(forbidden,source)
  self.assertIn('new underwater neutral only',source)

if __name__=='__main__':
 unittest.main()
