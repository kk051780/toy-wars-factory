import hashlib, json, pathlib, re, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
LU=(ROOT/'src/MoonGiraffeShowcase.luau').read_text(encoding='utf-8')
ED=json.loads((ROOT/'data/editorial_reference.json').read_text(encoding='utf-8'))

class ShowcaseContract(unittest.TestCase):
    def test_canon(self):
        self.assertEqual(ED['id'],'TRCA-BE-072')
        self.assertEqual(ED['name_ja'],'月冠キリン')
        self.assertEqual(ED['rarity'],'LEGENDARY')
        self.assertEqual(len(ED['source_sha']),40)
        self.assertIn(ED['id'],LU)
        self.assertIn(ED['name_ja'],LU)
    def test_exports(self):
        for name in ['Build','SetPose','SetLod','GetStatus','Destroy']:
            with self.subTest(name=name): self.assertIn('function Factory.'+name+'(',LU)
    def test_distinct_pose_names(self):
        for name in ['idle','tap','win','loss']:
            with self.subTest(name=name): self.assertRegex(LU,r'\b'+name+r' = \{yaw')
    def test_geometry_count(self):
        area=LU.split('local PLAN = {',1)[1].split('\n}',1)[0]
        entries=re.findall(r'^\s*\{"([^\"]+)",',area,flags=re.M)
        self.assertEqual(len(entries),18)
        self.assertEqual(len(set(entries)),18)
        for required in ['NeckLower','NeckUpper','SingleWhiteSock','StitchedCape','MoonArcTop','MoonArcTip']:
            self.assertIn(required,entries)
    def test_lod_count(self):
        area=LU.split('local PLAN = {',1)[1].split('\n}',1)[0]
        self.assertEqual(len(re.findall(r', true,',area)),3)
        self.assertEqual(18-3,15)
    def test_security_flags(self):
        for s in ['part.Anchored = true','part.CanCollide = false','part.CanTouch = false',
                  'part.CanQuery = false','part.CastShadow = false']:
            self.assertIn(s,LU)
        for forbidden in ['FireServer','DataStoreService','MarketplaceService','Humanoid',
                          'RemoteEvent','RemoteFunction','RunService','ClickDetector','Touched:Connect',
                          'PromptProductPurchase']:
            with self.subTest(forbidden=forbidden): self.assertNotIn(forbidden,LU)
    def test_optional_not_autostart(self):
        self.assertTrue(LU.rstrip().endswith('return Factory'))
        self.assertIn('model.Parent = parent',LU)
        self.assertIn('model.WorldPivot = CFrame.new()', LU)
        self.assertIn('model:Destroy()',LU)
        self.assertNotIn('Factory.Build(workspace',LU)
    def test_manifest_exact(self):
        manifest=json.loads((ROOT/'BUILD_MANIFEST.json').read_text(encoding='utf-8'))
        self.assertEqual(set(manifest),{'files','format','game_id','packet_id','public_source_allowed','work_id'})
        self.assertEqual(manifest['format'],'P0D_PUBLIC_SOURCE_V1')
        self.assertTrue(manifest['public_source_allowed'])
        self.assertEqual(manifest['game_id'],'TRAP_RAIDERS')
        self.assertEqual(manifest['work_id'],'p0d-siege-v19')
        self.assertEqual(manifest['packet_id'],'P0D-D18-MOON-GIRAFFE-SHOWCASE-20261112-01')
        seen=set()
        for f in manifest['files']:
            p=f['path']; self.assertNotIn('..',p); self.assertNotIn('\\',p)
            self.assertNotIn(p,seen);seen.add(p)
            data=(ROOT/p).read_bytes()
            self.assertEqual(len(data),f['size'])
            self.assertEqual(hashlib.sha256(data).hexdigest(),f['sha256'])
        actual={str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and p.name!='BUILD_MANIFEST.json' and '__pycache__' not in p.parts}
        self.assertEqual(seen,actual)

if __name__=='__main__': unittest.main()
