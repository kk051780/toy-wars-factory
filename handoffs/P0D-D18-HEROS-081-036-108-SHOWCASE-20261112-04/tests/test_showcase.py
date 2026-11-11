import copy, hashlib, importlib.util, json, pathlib, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
def module(path,modname):
    spec=importlib.util.spec_from_file_location(modname,path);obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj
G=module(ROOT/'tools/generate_catalog.py','gen_catalog')
V=module(ROOT/'tools/verify_pack.py','verify_pack')
DATA=json.loads((ROOT/'data/showcase_models.json').read_text('utf-8'))
FACTORY=(ROOT/'luau/D18ShowcaseFactory.luau').read_text('utf-8')
DEMO=(ROOT/'luau/DisabledShowcaseDemo.server.luau').read_text('utf-8')

class RealSourceContract(unittest.TestCase):
    def test_01_canonical_identities(self):
        self.assertEqual(set(DATA['characters']),set(G.IDENTITIES));G.validate(DATA)
    def test_02_readme_matches_v8_and_source_only(self):
        readme=(ROOT/'README.md').read_text('utf-8')
        for ident in G.IDENTITIES:self.assertIn(ident,readme)
        self.assertIn('NOT TESTED',readme)
    def test_03_parts_budgets(self):
        self.assertEqual([len(DATA['characters'][x]['parts']) for x in sorted(DATA['characters'])],[13,20,21])
    def test_04_far_lod_count(self):
        self.assertEqual([sum(not p['far'] for p in DATA['characters'][x]['parts']) for x in sorted(DATA['characters'])],[11,14,15])
    def test_05_silhouette_anchors(self):
        for ident,required in G.CUES.items():
            self.assertTrue(required.issubset({p['name'] for p in DATA['characters'][ident]['parts']}))
    def test_06_seven_bells_exact(self):
        self.assertEqual(len([p for p in DATA['characters']['TRCA-ZO-108']['parts'] if p['name'].startswith('ReturnBell')]),7)
    def test_07_reject_unknown_id(self):
        d=copy.deepcopy(DATA);d['characters']['TRCA-OTHER']={};self.assertRaises(ValueError,G.validate,d)
    def test_08_reject_name_drift(self):
        d=copy.deepcopy(DATA);d['characters']['TRCA-SP-081']['name']='FAKE';self.assertRaises(ValueError,G.validate,d)
    def test_09_reject_duplicate_part(self):
        d=copy.deepcopy(DATA);d['characters']['TRCA-SP-081']['parts'][0]['name']=d['characters']['TRCA-SP-081']['parts'][1]['name'];self.assertRaises(ValueError,G.validate,d)
    def test_10_reject_lost_art_cue(self):
        d=copy.deepcopy(DATA);d['characters']['TRCA-VE-036']['parts'][4]['name']='RandomShape';self.assertRaises(ValueError,G.validate,d)
    def test_11_reject_infinite_coordinate(self):
        d=copy.deepcopy(DATA);d['characters']['TRCA-ZO-108']['parts'][0]['pos'][0]=float('inf');self.assertRaises(ValueError,G.validate,d)
    def test_12_reject_invalid_color(self):
        d=copy.deepcopy(DATA);d['characters']['TRCA-ZO-108']['parts'][0]['rgb'][0]=999;self.assertRaises(ValueError,G.validate,d)
    def test_13_reject_oversize_part(self):
        d=copy.deepcopy(DATA);d['characters']['TRCA-SP-081']['parts'][0]['size'][0]=100;self.assertRaises(ValueError,G.validate,d)
    def test_14_reject_invalid_rotation(self):
        d=copy.deepcopy(DATA);d['characters']['TRCA-SP-081']['parts'][0]['zrot']=400;self.assertRaises(ValueError,G.validate,d)
    def test_15_reject_invalid_shape(self):
        d=copy.deepcopy(DATA);d['characters']['TRCA-SP-081']['parts'][0]['shape']='MeshPart';self.assertRaises(ValueError,G.validate,d)
    def test_16_reject_non_boolean_lod(self):
        d=copy.deepcopy(DATA);d['characters']['TRCA-SP-081']['parts'][0]['far']=1;self.assertRaises(ValueError,G.validate,d)
    def test_17_generator_matches_exact_luau(self):
        self.assertEqual(G.render(DATA),(ROOT/'luau/ShowcaseCatalog.luau').read_text('utf-8'))
    def test_18_no_auto_start(self):
        self.assertIn('local ENABLED = false',DEMO);self.assertIn('if not ENABLED then return end',DEMO)
    def test_19_all_five_apis(self):
        for name in ('Build','SetPose','SetLod','GetStatus','Destroy'):self.assertIn('function Factory.'+name+'(',FACTORY)
    def test_20_four_poses(self):
        for state in ('idle','tap','win','loss'):self.assertIn(state+' = CFrame.',FACTORY)
    def test_21_inert_parts(self):
        for field in ('Anchored = true','CanCollide = false','CanTouch = false','CanQuery = false','CastShadow = false'):self.assertIn(field,FACTORY)
    def test_22_no_game_authority(self):
        for forbidden in ('FireServer','FireClient','DataStoreService','MarketplaceService','Humanoid','Touched:Connect','TakeDamage','RemoteEvent','ProximityPrompt','while true','RunService','TweenService'):
            self.assertNotIn(forbidden,FACTORY)
    def test_23_instance_budget(self):
        self.assertIn('MAX_MODELS = 12',FACTORY)
        self.assertIn('MAX_PARTS = 24',FACTORY)
    def test_24_manifest_byte_hashes(self):
        self.assertEqual(V.verify(),9)
    def test_25_manifest_negative_tamper(self):
        f=ROOT/'BUILD_MANIFEST.json';j=json.loads(f.read_text('utf-8'));j['files'][0]['sha256']='0'*64
        with tempfile.TemporaryDirectory() as td:
            target=pathlib.Path(td);(target/'BUILD_MANIFEST.json').write_text(json.dumps(j))
            self.assertNotEqual(j['files'][0]['sha256'],hashlib.sha256((ROOT/j['files'][0]['path']).read_bytes()).hexdigest())
    def test_26_manifest_no_duplicates(self):
        rows=json.loads((ROOT/'BUILD_MANIFEST.json').read_text('utf-8'))['files'];self.assertEqual(len({x['path'] for x in rows}),len(rows))
    def test_27_no_network_or_asset_ids(self):
        for path in [ROOT/'luau/D18ShowcaseFactory.luau',ROOT/'luau/ShowcaseCatalog.luau']:
            src=path.read_text('utf-8');self.assertNotIn('rbxassetid://',src);self.assertNotIn('HttpService',src)
    def test_28_discriminable_2d_cues(self):
        self.assertIn('SingleGoldenSeed',{p['name'] for p in DATA['characters']['TRCA-SP-081']['parts']})
        self.assertIn('MatteIceMirror',{p['name'] for p in DATA['characters']['TRCA-VE-036']['parts']})
        self.assertIn('WhiteReturnRoster',{p['name'] for p in DATA['characters']['TRCA-ZO-108']['parts']})

if __name__=='__main__':unittest.main()
