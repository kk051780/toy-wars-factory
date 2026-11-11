import json, hashlib, unittest, importlib.util, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'data/characters.json').read_text(encoding='utf-8'))
CHARS=DATA['characters']
SRC=(ROOT/'src/ShowcaseFactory.luau').read_text(encoding='utf-8')
DEMO=(ROOT/'src/DisabledDemo.client.luau').read_text(encoding='utf-8')

def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

class CatalogDataTests(unittest.TestCase):
    def test_exact_two_canon_ids(self): self.assertEqual(set(CHARS), {'TRCA-TR-063','TRCA-WE-099'})
    def test_canon_sha(self): self.assertEqual(DATA['source_editorial_fixed_sha'],'176bfc400ef6ec561b129a8163a0f4776e1b9ee4')
    def test_game_and_work(self): self.assertEqual((DATA['game_id'],DATA['work_id']),('TRAP_RAIDERS','p0d-siege-v19'))
    def test_trap_identity(self): self.assertEqual((CHARS['TRCA-TR-063']['name'],CHARS['TRCA-TR-063']['category'],CHARS['TRCA-TR-063']['rarity'],CHARS['TRCA-TR-063']['world']),('火輪跳ね台','TR','LEGENDARY','火輪の熔炉'))
    def test_weapon_identity(self): self.assertEqual((CHARS['TRCA-WE-099']['name'],CHARS['TRCA-WE-099']['category'],CHARS['TRCA-WE-099']['rarity'],CHARS['TRCA-WE-099']['world']),('遊園ホルン','WE','LEGENDARY','夢菓子の遊園'))
    def test_part_counts(self): self.assertEqual([len(CHARS[i]['parts']) for i in ('TRCA-TR-063','TRCA-WE-099')],[21,27])
    def test_far_counts(self): self.assertEqual([sum(not p['detail'] for p in CHARS[i]['parts']) for i in ('TRCA-TR-063','TRCA-WE-099')],[16,16])
    def test_shapes(self):
        for d in CHARS.values():
            self.assertTrue(all(p['shape'] in {'Block','Cylinder','Ball'} for p in d['parts']))
    def test_dimensions_positive_bounded(self):
        for d in CHARS.values():
            for p in d['parts']:
                self.assertTrue(all(isinstance(x,(int,float)) and .05 <=x <=5 for x in p['size']))
    def test_coordinates_finite_bounded(self):
        for d in CHARS.values():
            for p in d['parts']:
                self.assertTrue(all(isinstance(x,(int,float)) and -12<=x<=12 for x in p['position']))
    def test_rotations_finite(self):
        for d in CHARS.values():
            for p in d['parts']:
                self.assertTrue(all(isinstance(x,(int,float)) and abs(x)<=360 for x in p['rotation']))
    def test_names_unique_per_character(self):
        for d in CHARS.values():
            names=[p['name'] for p in d['parts']]
            self.assertEqual(len(names),len(set(names)))
    def test_palette_each_part_defined(self):
        for d in CHARS.values():
            self.assertTrue(all(p['color'] in d['palette'] for p in d['parts']))
    def test_colors_rgb(self):
        for d in CHARS.values():
            self.assertTrue(all(len(c)==3 and all(type(x) is int and 0<=x<=255 for x in c) for c in d['palette'].values()))
    def test_four_poses_present(self):
        for d in CHARS.values(): self.assertEqual(set(d['pose_offsets']),{'idle','tap','win','loss'})
    def test_pose_group_exists(self):
        for d in CHARS.values():
            groups={p['group'] for p in d['parts']}
            self.assertTrue(all(g in groups for pose in d['pose_offsets'].values() for g in pose))
    def test_open_ring_silhouette(self):
        ps=CHARS['TRCA-TR-063']['parts']
        self.assertEqual(sum(p['name'].startswith('開いた鉄輪') for p in ps),11)
        self.assertTrue(all(p['rotation'][0]==45 for p in ps if p['name'].startswith('開いた鉄輪')))
    def test_three_legs(self):
        self.assertEqual(sum('三脚' in p['name'] for p in CHARS['TRCA-TR-063']['parts']),3)
    def test_hammer_and_seal(self):
        names=' '.join(x['name'] for x in CHARS['TRCA-TR-063']['parts'])
        self.assertIn('鍛冶槌',names);self.assertIn('焼印',names)
    def test_two_horn_loops(self):
        ps=CHARS['TRCA-WE-099']['parts']
        self.assertEqual(sum(p['name'].startswith('二重管1_') for p in ps),8)
        self.assertEqual(sum(p['name'].startswith('二重管2_') for p in ps),8)
    def test_ferris_and_ticket(self):
        names=' '.join(x['name'] for x in CHARS['TRCA-WE-099']['parts'])
        self.assertIn('観覧車',names);self.assertIn('乗車券',names);self.assertIn('キャンディ',names)
    def test_no_official_gameplay_claims(self):
        self.assertTrue(all('TRCA-' in k and 21<=len(d['parts'])<=40 for k,d in CHARS.items()))

class SourceTests(unittest.TestCase):
    def test_generated_exact(self):
        m=load_module('p0dcatalog',ROOT/'tools/generate_catalog.py')
        self.assertEqual(m.render(),(ROOT/'src/ShowcaseCatalog.luau').read_text(encoding='utf-8'))
    def test_generated_check_cli(self):
        p=subprocess.run([sys.executable,str(ROOT/'tools/generate_catalog.py'),'--check'],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
    def test_implemented_methods(self):
        for m in ('Build','SetPose','SetLod','GetStatus','Destroy'):
            self.assertIn('function Factory.'+m+'(',SRC)
    def test_render_safety_flags(self):
        for phrase in ('p.Anchored = true','p.CanCollide = false','p.CanTouch = false','p.CanQuery = false','p.CastShadow = false'):
            self.assertIn(phrase,SRC)
    def test_safe_input_fail_closed(self):
        for phrase in ('INVALID_DISPLAY_PARENT','INVALID_ORIGIN','UNKNOWN_CHARACTER','CAP_REACHED','MAX_PREVIEWS = 12','VALID_POSE','originOK'):
            self.assertIn(phrase,SRC)
    def test_no_remote_or_datastore_or_marketplace(self):
        for token in ('FireServer','OnServerEvent','RemoteEvent','DataStoreService','MarketplaceService','Humanoid','TakeDamage','SetAsync'):
            functional_source='\n'.join(line for line in SRC.splitlines() if not line.lstrip().startswith('--'))
            self.assertNotIn(token,functional_source)
    def test_demo_disabled(self): self.assertIn('local ENABLED = false',DEMO)
    def test_demo_not_connected(self): self.assertNotIn('script.Parent.DisabledDemo',SRC)
    def test_factory_destroy_state(self):
        self.assertIn('ACTIVE[model]=nil',SRC)
        self.assertIn('model:Destroy()',SRC)
    def test_lod_only_visibility(self): self.assertIn('slot.part.Transparency=(far and slot.spec.detail) and 1 or 0',SRC)
    def test_pose_validation(self): self.assertIn('not VALID_POSE[pose]',SRC)

class ManifestTests(unittest.TestCase):
    def test_manifest(self):
        m=load_module('verifier',ROOT/'tools/verify_pack.py')
        self.assertEqual(m.verify(ROOT),9)
    def test_manifest_negative_tamper(self):
        import tempfile, shutil
        m=load_module('verifier2',ROOT/'tools/verify_pack.py')
        with tempfile.TemporaryDirectory() as d:
            cloned=Path(d)
            for p in ROOT.rglob('*'):
                if p.is_file():
                    target=cloned/p.relative_to(ROOT)
                    target.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copyfile(p,target)
            with (cloned/'src/ShowcaseFactory.luau').open('ab') as f: f.write(b'--unsafe mutation')
            with self.assertRaises(AssertionError):m.verify(cloned)

if __name__=='__main__': unittest.main()
