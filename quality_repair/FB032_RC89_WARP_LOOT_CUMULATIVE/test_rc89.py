#!/usr/bin/env python3
import unittest, hashlib, json, tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile
import build_rc89 as b

class ActualRC89Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec=b.build()
        cls.out=b.OUTPUT.read_bytes()
        cls.root=ET.fromstring(cls.out)
        cls.d=b.scan(cls.root)
        cls.lock=json.loads((b.HOME/'SOURCE_LOCK.json').read_text())
        with ZipFile(b.PARENT) as z:
            cls.parent=z.read(b.PARENT_FILE)
        cls.old=b.scan(ET.fromstring(cls.parent))
        cls.src=cls.d[b.STAGE_PATH]['body']
    def test_01_parent_sha_exact(self):self.assertEqual(b.sha256(self.parent),b.PARENT_SHA)
    def test_02_parent_86_scripts(self):self.assertEqual(len(self.old),86)
    def test_03_real_output_86_scripts(self):self.assertEqual(len(self.d),86)
    def test_04_parent_and_output_script_paths_same(self):self.assertEqual(set(self.old),set(self.d))
    def test_05_parent_and_output_script_classes_same(self):
        self.assertTrue(all(self.old[k]['class']==self.d[k]['class'] for k in self.old))
    def test_06_85_other_sources_exact(self):
        self.assertEqual([k for k in self.old if self.old[k]['body']!=self.d[k]['body']],[b.STAGE_PATH])
    def test_07_original_trapper_widefield_unchanged(self):
        k='ServerScriptService/TrapRaidersS1/TrapperWarpService'
        self.assertEqual(self.old[k]['body'],self.d[k]['body'])
        self.assertEqual(b.gitblob(self.d[k]['body']),'ef41f1d00ad418a2afe07cdb4cad2eeb3650290d')
    def test_08_original_game_hud_and_egg_ai_unchanged(self):
        for s in ['Game','MapBuilder','SoloTeamBots','TrapRaidersHUD','SevenJobArmamentM1','UndeadSquad']:
            p=next(p for p in self.d if p.endswith('/'+s))
            self.assertEqual(self.old[p]['body'],self.d[p]['body'])
    def test_09_stage_original_blob_frozen(self):self.assertEqual(b.gitblob(self.old[b.STAGE_PATH]['body']),b.ORIGINAL_BLOB)
    def test_10_real_stage_los_helper_once(self):
        self.assertEqual(self.src.count('local function unobstructed('),1)
        self.assertEqual(self.src.count('workspace:Raycast('),1)
    def test_11_castle_wall_keeps_spear_origin(self):
        self.assertIn('if not unobstructed(player,origin,projected,nil) then return origin end',self.src)
        self.assertIn('params.RespectCanCollide=true',self.src)
    def test_12_castle_wall_forbids_pickup(self):
        self.assertIn('if not unobstructed(player,root.Position,',self.src)
        self.assertLess(self.src.index('if not unobstructed(player,root.Position,'),self.src.index('active[player]={kind=kind'))
    def test_13_no_new_authority(self):
        self.assertEqual(self.d['ServerScriptService/TrapRaidersS1/Game']['body'].count('remote.OnServerEvent:Connect('),1)
        self.assertNotIn('Instance.new("RemoteEvent")',self.src)
        self.assertNotIn('DataStoreService',self.src)
    def test_14_unchanged_pickup_experience(self):
        for term in ['SUN_BLADE','WIND_SPEAR','THUNDER_BOW','DURATION=18','MaxActivationDistance=9','ProximityPrompt']:
            self.assertIn(term,self.src)
    def test_15_existing_three_undead_preserved(self):
        self.assertTrue(any(k.endswith('/UndeadSquad') for k in self.d))
    def test_16_gitblob_manifest_86_exact(self):
        self.assertEqual(self.lock['total_scripts'],86)
        self.assertEqual({k:b.gitblob(v['body']) for k,v in self.d.items()},
                         {k:v['blob'] for k,v in self.lock['scripts'].items()})
    def test_17_receipt_hash_matches_real_place(self):
        self.assertEqual(len(self.out),self.rec['place_bytes'])
        self.assertEqual(b.sha256(self.out),self.rec['place_sha256'])
    def test_18_deterministic_rebuild(self):
        again=b.build()
        self.assertEqual(again['place_sha256'],self.rec['place_sha256'])
        self.assertEqual(b.OUTPUT.read_bytes(),self.out)
    def test_19_wrong_parent_rejected(self):
        with self.assertRaisesRegex(ValueError,'WRONG_NATIVE_RC88_PARENT'):
            b.build(self.parent+b'corrupt')
    def test_20_stage_double_patch_rejected(self):
        with self.assertRaisesRegex(ValueError,'SOURCE_DRIFT_PICKUP_NOT_THROUGH_WALL'):
            b.patch(self.src)
    def test_21_stale_source_rejected(self):
        with self.assertRaisesRegex(ValueError,'SOURCE_DRIFT_PICKUP_NOT_THROUGH_WALL'):
            b.patch(self.old[b.STAGE_PATH]['body'].replace('Magnitude>10','Magnitude>9'))
    def test_22_stale_hit_origin_rejected(self):
        with self.assertRaisesRegex(ValueError,'SOURCE_DRIFT_HIT_ORIGIN_NOT_THROUGH_GATE'):
            b.patch(self.old[b.STAGE_PATH]['body'].replace('v.Magnitude>.01','v.Magnitude>.02'))
    def test_23_no_false_runtime_claim(self):
        self.assertEqual(self.rec['studio'],'NOT_RUN')
        self.assertEqual(self.rec['native_luau'],'NOT_RUN')
        self.assertEqual(self.rec['rojo'],'NOT_RUN')
        self.assertFalse(self.rec['official_rc_write'])
        self.assertFalse(self.rec['owner_accepted'])
    def test_24_output_real_xml_class_path(self):
        self.assertEqual(self.d[b.STAGE_PATH]['class'],'ModuleScript')
        self.assertEqual(self.d['ServerScriptService/TrapRaidersS1/Game']['class'],'Script')
    def test_25_reach_wall_and_pickup_wall_both_preserved(self):
        self.assertEqual(self.src.count('if not unobstructed('),2)
        self.assertTrue(self.src.count('return origin')>=3)

if __name__=='__main__':unittest.main()
