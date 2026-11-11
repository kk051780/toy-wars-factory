"""Actual offline contracts for this source-only D18 packet, not Roblox QA."""
import hashlib
import importlib.util
import json
import pathlib
import re
import shutil
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT/'data/showcase_models.json').read_text(encoding='utf-8'))
LUA = (ROOT/'luau/D18ShowcaseFactory.luau').read_text(encoding='utf-8')
DEMO = (ROOT/'luau/DisabledShowcaseDemo.server.luau').read_text(encoding='utf-8')
GEN = (ROOT/'tools/generate_catalog.py').read_text(encoding='utf-8')


def import_by_path(module_name, relative):
    path=ROOT/relative
    spec=importlib.util.spec_from_file_location(module_name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class V8Canon(unittest.TestCase):
    def test_public_source_provenance(self):
        self.assertEqual(DATA['canon_editorial_commit'],'176bfc400ef6ec561b129a8163a0f4776e1b9ee4')
        self.assertEqual(DATA['source_type'],'NEW_ORIGINAL_SOURCE_FROM_V8_EDITORIAL')
        self.assertEqual(DATA['game_id'],'TRAP_RAIDERS')

    def test_exact_two_ids_and_names(self):
        self.assertEqual([(x['id'],x['name']) for x in DATA['models']], [('TRCA-TR-009','星跳ねの発射台'),('TRCA-WE-045','雷鳥ホルン')])

    def test_category_rarity_and_world(self):
        a,b=DATA['models']
        self.assertEqual((a['category'],a['rarity'],a['world']),('TR','MYTHIC','星屑の廃都'))
        self.assertEqual((b['category'],b['rarity'],b['world']),('WE','LEGENDARY','雷鳥の空庭'))

    def test_distinct_silhouettes_and_signature_parts(self):
        a,b=[{p['name'] for p in x['parts']} for x in DATA['models']]
        self.assertTrue({'MoonBaseLeft','MoonBaseCenter','TelescopeArm','StarButton','RibbonBlue'}<=a)
        self.assertTrue({'HornZigLower','HornZigMid','HornZigUpper','OpenWing','ClosedWing','HornBellCloud','FeatherTag'}<=b)
        self.assertFalse(a & b)

    def test_part_budgets(self):
        self.assertEqual([len(x['parts']) for x in DATA['models']],[18,16])
        self.assertTrue(all(0<len(x['parts'])<=24 for x in DATA['models']))

    def test_far_lod_preserves_signature(self):
        for x in DATA['models']:
            near={p['name'] for p in x['parts']}
            far={p['name'] for p in x['parts'] if not p['far_detail']}
            self.assertTrue(0<len(far)<len(near))
            self.assertTrue(far<=near)
        a,b=DATA['models']
        visibleA={p['name'] for p in a['parts'] if not p['far_detail']}
        visibleB={p['name'] for p in b['parts'] if not p['far_detail']}
        self.assertTrue({'MoonBaseCenter','TelescopeArm','StarButton','RibbonBlue'}<=visibleA)
        self.assertTrue({'HornZigLower','HornZigUpper','OpenWing','ClosedWing','HornBellCloud'}<=visibleB)


class GeometrySafety(unittest.TestCase):
    def test_names_unique(self):
        for m in DATA['models']:
            names=[p['name'] for p in m['parts']]
            self.assertEqual(len(names),len(set(names)))

    def test_dimensions_bounded_and_finite(self):
        import math
        for m in DATA['models']:
            for p in m['parts']:
                self.assertTrue(all(math.isfinite(v) and 0.05<=v<=3 for v in p['size']))
                self.assertTrue(all(math.isfinite(v) and abs(v)<=5 for v in p['position']))
                self.assertTrue(math.isfinite(p['rotation_z']) and abs(p['rotation_z'])<=90)

    def test_valid_colors_and_primitive_shapes(self):
        for m in DATA['models']:
            for p in m['parts']:
                self.assertIn(p['shape'],('Block','Ball'))
                self.assertTrue(all(isinstance(v,int) and 0<=v<=255 for v in p['color']))
                self.assertIsInstance(p['far_detail'],bool)

    def test_no_external_assets_or_scripts_in_art_data(self):
        txt=(ROOT/'data/showcase_models.json').read_text(encoding='utf-8')
        for word in ('rbxassetid://','https://','require(', 'DataStore','RemoteEvent'):
            self.assertNotIn(word,txt)

    def test_anchored_no_collisions_in_factory(self):
        for phrase in ('p.Anchored = true','p.CanCollide = false','p.CanTouch = false','p.CanQuery = false','p.CastShadow = false','p.Material = Enum.Material.SmoothPlastic'):
            self.assertIn(phrase,LUA)

    def test_no_server_authority_or_payment(self):
        bad_patterns=(r'\bFireServer\b',r'\bFireClient\b',r'\bOnServerEvent\b',r'\bDataStoreService\b',r'\bMarketplaceService\b',r'\bHumanoid\b',r'\bRunService\b',r'\bUserInputService\b',r'\bRemoteEvent\b',r'\bTakeDamage\b',r'\bTouched\b')
        for pat in bad_patterns:
            self.assertIsNone(re.search(pat,LUA),pat)

    def test_safe_lookup_and_module_exit(self):
        for code in ('if design == nil', 'return nil','local MAX_PARTS = 24','return Factory', 'if not owned(model)', 'if not model:IsA("Model")'):
            self.assertIn(code,LUA)

    def test_four_target_poses_and_status(self):
        for pose in ('idle','tap','win','loss'):
            self.assertRegex(LUA,rf'\b{pose}\s*=')
        for method in ('Build','SetPose','SetLod','GetStatus','Destroy'):
            self.assertIn('function Factory.'+method,LUA)

    def test_demo_disabled_and_not_triggering(self):
        self.assertIn('local ENABLED = false',DEMO)
        self.assertIn('if not ENABLED then return end',DEMO)
        self.assertNotIn('require(',LUA.split('local Factory = {}')[1])


class GeneratorAndPackage(unittest.TestCase):
    def test_catalog_reproducible(self):
        tool=import_by_path('test_generator','tools/generate_catalog.py')
        expected=tool.render(DATA)
        actual=(ROOT/'luau/ShowcaseCatalog.luau').read_text(encoding='utf-8')
        self.assertEqual(expected,actual)
        self.assertIn('TRCA-WE-045',actual)

    def test_generator_output_has_exact_json_part_count(self):
        output=(ROOT/'luau/ShowcaseCatalog.luau').read_text(encoding='utf-8')
        self.assertEqual(output.count('shape='),34)

    def test_verifier_accepts_real_package(self):
        verify=import_by_path('test_verify','tools/verify_pack.py')
        self.assertEqual(verify.verify(ROOT),9)

    def test_reject_tampered_bytes(self):
        verify=import_by_path('test_verify_tamper','tools/verify_pack.py')
        with tempfile.TemporaryDirectory() as d:
            testroot=pathlib.Path(d)/'copy'
            shutil.copytree(ROOT,testroot,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            file=testroot/'data/showcase_models.json'
            file.write_bytes(file.read_bytes()+b'X')
            with self.assertRaisesRegex(ValueError,'bytes/hash mismatch'): verify.verify(testroot)

    def test_reject_fake_manifest(self):
        verify=import_by_path('test_verify_mismatch','tools/verify_pack.py')
        with tempfile.TemporaryDirectory() as d:
            testroot=pathlib.Path(d)/'copy'
            shutil.copytree(ROOT,testroot,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            file=testroot/'BUILD_MANIFEST.json'
            manifest=json.loads(file.read_text(encoding='utf-8'))
            manifest['public_source_allowed']=False
            file.write_text(json.dumps(manifest),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'format flag'): verify.verify(testroot)

    def test_reject_untracked(self):
        verify=import_by_path('test_verify_untracked','tools/verify_pack.py')
        with tempfile.TemporaryDirectory() as d:
            testroot=pathlib.Path(d)/'copy'
            shutil.copytree(ROOT,testroot,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            (testroot/'SECRET.bin').write_bytes(b'fake')
            with self.assertRaisesRegex(ValueError,'untracked files'): verify.verify(testroot)


if __name__=='__main__':
    unittest.main()
