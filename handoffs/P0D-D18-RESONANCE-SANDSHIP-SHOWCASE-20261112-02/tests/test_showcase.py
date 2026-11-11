import copy
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from generate_catalog import valid, render

DATA=json.loads((ROOT/'data/characters.json').read_text(encoding='utf8'))
CATALOG=(ROOT/'luau/ShowcaseCatalog.luau').read_text(encoding='utf8')
FACTORY=(ROOT/'luau/ShowcaseFactory.luau').read_text(encoding='utf8')
DEMO=(ROOT/'luau/ShowcaseDemo.server.luau').read_text(encoding='utf8')

class TestRealShowcaseSource(unittest.TestCase):
    def test_01_canon_full_names_worlds(self):
        self.assertEqual(set(DATA['characters']),{'TRCA-SP-027','TRCA-VE-090'})
        self.assertEqual(DATA['characters']['TRCA-SP-027']['displayName'],'大地の共鳴')
        self.assertEqual(DATA['characters']['TRCA-SP-027']['rarity'],'MYTHIC')
        self.assertEqual(DATA['characters']['TRCA-VE-090']['displayName'],'時帰りの砂船')
        self.assertEqual(DATA['characters']['TRCA-VE-090']['rarity'],'LEGENDARY')
        self.assertEqual(DATA['source_commit'],'176bfc400ef6ec561b129a8163a0f4776e1b9ee4')
    def test_02_exact_luau_from_json(self):
        valid(DATA)
        self.assertEqual(render(DATA),CATALOG)
    def test_03_actual_generator_check(self):
        p=subprocess.run([sys.executable,str(ROOT/'tools/generate_catalog.py'),'--check'],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
    def test_04_silhouette_components(self):
        s=DATA['characters']['TRCA-SP-027']['parts']
        v=DATA['characters']['TRCA-VE-090']['parts']
        self.assertEqual(len(s),15)
        self.assertEqual(len(v),21)
        self.assertEqual(sum(not p['farDetail'] for p in s),12)
        self.assertEqual(sum(not p['farDetail'] for p in v),15)
        self.assertEqual(len([p for p in s if p['name'].startswith('ChippedGearRing')]),7)
        self.assertEqual(len([p for p in s if p['name'].startswith('ResonancePillar')]),3)
        self.assertEqual(len([p for p in v if p['name'].startswith('KeyholeCrown')]),8)
        self.assertIn('SquareClockWindow',{p['name'] for p in v})
    def test_05_actual_roblox_source_api(self):
        for token in ('function Factory.Build(', 'function Factory.SetPose(', 'function Factory.SetLod(', 'function Factory.GetStatus(', 'function Factory.Destroy(', 'model:PivotTo(', 'Enum.PartType.Ball', 'Instance.new("WedgePart")'):
            self.assertIn(token,FACTORY)
        self.assertIn('local ENABLED = false',DEMO)
        self.assertIn('if not ENABLED then return end',DEMO)
    def test_06_hard_noncombat_safety(self):
        for token in ('Anchored = true','CanCollide = false','CanTouch = false','CanQuery = false','CastShadow = false','MAX_INSTANCES = 16'):
            self.assertIn(token,FACTORY)
        for source in (FACTORY,DEMO,CATALOG):
            for forbidden in ('FireServer','FireClient','OnServerEvent','DataStoreService','MarketplaceService','Humanoid','RenderStepped','Heartbeat','TweenService','Touched:Connect','RemoteEvent',':TakeDamage('):
                self.assertNotIn(forbidden,source)
    def test_07_geometry_numeric_and_negative(self):
        mutant=copy.deepcopy(DATA)
        mutant['characters']['TRCA-SP-027']['parts'][0]['size'][0]=float('nan')
        with self.assertRaises(ValueError): valid(mutant)
        mutant=copy.deepcopy(DATA)
        mutant['characters']['TRCA-VE-090']['parts'][0]['shape']='RemoteEvent'
        with self.assertRaises(ValueError): valid(mutant)
        mutant=copy.deepcopy(DATA)
        mutant['characters']['TRCA-VE-090']['parts'][0]['name']=mutant['characters']['TRCA-VE-090']['parts'][1]['name']
        with self.assertRaises(ValueError): valid(mutant)
    def test_08_identity_tamper_rejected(self):
        mutant=copy.deepcopy(DATA)
        mutant['characters']['TRCA-VE-090']['displayName']='Time Travel Free Ride'
        with self.assertRaises(ValueError): valid(mutant)
        mutant=copy.deepcopy(DATA)
        mutant['characters']['TRCA-BE-018']=mutant['characters'].pop('TRCA-SP-027')
        with self.assertRaises(ValueError): valid(mutant)
    def test_09_complete_manifest_bytes_hashes(self):
        manifest=json.loads((ROOT/'BUILD_MANIFEST.json').read_text(encoding='utf8'))
        self.assertEqual(set(manifest),{'format','files','game_id','work_id','packet_id','public_source_allowed'})
        self.assertEqual(manifest['format'],'P0D_PUBLIC_SOURCE_V1')
        self.assertTrue(manifest['public_source_allowed'])
        self.assertEqual(manifest['packet_id'],DATA['packet_id'])
        actual={str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and p.name!='BUILD_MANIFEST.json' and '__pycache__' not in p.parts}
        self.assertEqual({f['path'] for f in manifest['files']},actual)
        self.assertEqual(len(manifest['files']),len(actual))
        for f in manifest['files']:
            b=(ROOT/f['path']).read_bytes()
            self.assertEqual(len(b),f['size'])
            self.assertEqual(hashlib.sha256(b).hexdigest(),f['sha256'])
    def test_10_no_random_paid_unlock_claims(self):
        self.assertNotIn('game:GetService',CATALOG)
        self.assertNotIn('FireServer',FACTORY)
        self.assertNotIn('Robux',FACTORY)
        self.assertNotIn('MarketplaceService',FACTORY)
        self.assertNotIn('purchase',FACTORY.lower())
    def test_11_lod_and_pose_guards(self):
        self.assertIn('VALID_POSES[pose] ~= true',FACTORY)
        self.assertIn('type(far)~="boolean"',FACTORY)
        self.assertIn('registry[model] = nil',FACTORY)
        self.assertIn('model:Destroy()',FACTORY)
    def test_12_readme_scope_and_canonical_triple(self):
        readme=(ROOT/'README.md').read_text('utf8')
        self.assertIn('NOT a Roblox Studio Play',readme)
        self.assertIn('TRCA-SP-027',readme)
        self.assertIn('TRCA-VE-090',readme)
        self.assertIn('176bfc400ef6ec561b129a8163a0f4776e1b9ee4',readme)

if __name__=='__main__':unittest.main()
