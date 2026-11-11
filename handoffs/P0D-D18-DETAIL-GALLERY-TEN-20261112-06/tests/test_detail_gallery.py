"""Real Python source/manifest negative and composition tests; NOT native Luau or Studio."""
import hashlib
import json
import pathlib
import re
import unittest
from copy import deepcopy

ROOT=pathlib.Path(__file__).resolve().parents[1]
EXPECTED_IDS=['TRCA-BE-018','TRCA-ZO-054','TRCA-BE-072','TRCA-SP-027','TRCA-VE-090','TRCA-TR-009','TRCA-WE-045','TRCA-SP-081','TRCA-VE-036','TRCA-ZO-108']
EXPECTED_COUNTS=[21,16,18,15,21,18,16,13,20,21]
EXPECTED_PINS={
  'Mascots':'b013f501e6af2b0f1f92ae6ba52e11b239918ac3',
  'Moon':'69c6ea5dac251bd4bc31d49d3738f6a6949305ee',
  'Resonance':'e17928f244fb2758bbc6f0d84a084de47d072335',
  'Star':'2c3bac3c6a24640205299175f289835d7de8c50b',
  'Trio':'bbecdf922de2d8b393c66a7bbb49a65e7aab6619',
}

def digest(data): return hashlib.sha256(data).hexdigest()

def asdict(path): return json.loads((ROOT/path).read_text('utf-8'))

def source(path): return (ROOT/path).read_text('utf-8')

class OriginalSourceProof(unittest.TestCase):
  def test_exact_ten_canonical_ids(self):
    catalog=source('src/D18GalleryCatalog.luau')
    detail=source('src/D18DetailedGalleryPreview.luau')
    self.assertEqual(re.findall(r'\["(TRCA-[A-Z]{2}-\d{3})"\] = \{"', detail),EXPECTED_IDS)
    self.assertEqual(set(re.findall(r'\["id"\]="(TRCA-[A-Z]{2}-\d{3})"',catalog)),set(EXPECTED_IDS))
  def test_expected_model_part_counts(self):
    s=source('src/D18DetailedGalleryPreview.luau')
    self.assertEqual([int(x) for x in re.findall(r'\["TRCA-[A-Z]{2}-\d{3}"\] = \{"[^"]+", "[^"]+", (\d+)\}',s)],EXPECTED_COUNTS)
  def test_immutable_original_source_bytes(self):
    receipts=asdict('docs/SOURCE_PROVENANCE.json')['source_files']
    self.assertEqual(len(receipts),10)
    for item in receipts:
      with self.subTest(file=item['path']):
        actual=(ROOT/item['path']).read_bytes()
        self.assertEqual(len(actual),item['bytes'])
        self.assertEqual(digest(actual),item['sha256'])
        folder=pathlib.Path(item['path']).parent.name
        if folder in EXPECTED_PINS:self.assertEqual(item['upstream_sha'],EXPECTED_PINS[folder])
  def test_one_gallery_catalog_same_original(self):
    receipt=next(x for x in asdict('docs/SOURCE_PROVENANCE.json')['source_files'] if x['path']=='src/D18GalleryCatalog.luau')
    self.assertEqual(receipt['upstream_sha'],'d8320307e0fbb9a19050cf38a8e6fed56ae900bd')
  def test_original_factories_unchanged_parent_module_imports(self):
    pairs=[('Mascots','MascotPreviewFactory','MascotPreviewCatalog'),('Resonance','ShowcaseFactory','ShowcaseCatalog'),('Star','D18ShowcaseFactory','ShowcaseCatalog'),('Trio','D18ShowcaseFactory','ShowcaseCatalog')]
    for group,f,c in pairs:
      with self.subTest(group=group):
        self.assertIn(c,source(f'src/D18DetailModels/{group}/{f}.luau'))
        self.assertTrue((ROOT/f'src/D18DetailModels/{group}/{c}.luau').is_file())
  def test_all_factories_have_lifecycle(self):
    for f in ROOT.glob('src/D18DetailModels/*/*Factory.luau'):
      for method in ['Build','SetPose','SetLod','GetStatus','Destroy']:
        self.assertRegex(f.read_text(),r'function\s+Factory\.'+method+r'\(')
    f=ROOT/'src/D18DetailModels/Moon/MoonGiraffeShowcase.luau'
    for method in ['Build','SetPose','SetLod','GetStatus','Destroy']:
      self.assertRegex(f.read_text(),r'function\s+Factory\.'+method+r'\(')
  def test_model_sources_no_network_or_pay(self):
    for p in (ROOT/'src/D18DetailModels').rglob('*.luau'):
      self.assertNotRegex(p.read_text(),r'(RemoteEvent|RemoteFunction|DataStoreService|MarketplaceService|FireServer|InvokeServer|HttpService|require\s*\(\s*\d+)')

class GalleryComposition(unittest.TestCase):
  def test_factory_lookup_uses_exact_five_groups(self):
    p=source('src/D18DetailedGalleryPreview.luau')
    for x in EXPECTED_PINS:
      self.assertIn('"'+x+'"',p)
  def test_original_model_not_simplified_thumbnail(self):
    p=source('src/D18DetailedGalleryPreview.luau')
    self.assertIn('factory.Build(stage,entry.id,CFrame.new())',p)
    self.assertIn('factory.Build(stage,CFrame.new())',p)  # Moon special signature
    self.assertNotIn('for i, def in ipairs(entry.parts)',p)
    self.assertNotIn('PreviewFrame stand-ins',p)
  def test_parent_folder_worldmodel_valid(self):
    p=source('src/D18DetailedGalleryPreview.luau')
    self.assertIn('Instance.new("WorldModel")',p)
    self.assertIn('Instance.new("Folder")',p)
    self.assertIn('stage.Parent=world',p)
    self.assertNotIn('factory.Build(world,',p)
  def test_destroy_prevents_resonance_live_counter_leak(self):
    p=source('src/D18DetailedGalleryPreview.luau')
    self.assertIn('pcall(rec.factory.Destroy, rec.model)',p)
    self.assertIn('Preview.dispose(viewport)\n    if',p)
    self.assertIn('Preview.dispose(viewport)',source('src/D18GalleryController.luau'))
    self.assertEqual(source('src/D18GalleryController.luau').count('Preview.dispose(viewport)'),3)
  def test_render_safety_fail_closed(self):
    p=source('src/D18DetailedGalleryPreview.luau')
    for code in ('INVALID_ENTRY','UNKNOWN_CHARACTER_ID','INVALID_YAW','INVALID_POSE','INVALID_LOD','SOURCE_BUILD_FAILED','SOURCE_SAFETY_REJECTED','SOURCE_PART_COUNT_DRIFT','SOURCE_POSE_OR_LOD_REJECTED'):
      if code=='SOURCE_BUILD_FAILED': code='ORIGINAL_SOURCE_BUILD_FAILED'
      self.assertIn('"'+code+'"',p)
  def test_safety_flags_validated(self):
    p=source('src/D18DetailedGalleryPreview.luau')
    for fragment in ['not item.Anchored','item.CanCollide','item.CanTouch','item.CanQuery','model:IsDescendantOf(world)']:
      self.assertIn(fragment,p)
  def test_camera_tracks_actual_bounds_and_rotation(self):
    p=source('src/D18DetailedGalleryPreview.luau')
    self.assertGreaterEqual(p.count('model:GetBoundingBox()'),2)
    self.assertIn('model:PivotTo(turn*model:GetPivot())',p)
    self.assertIn('CFrame.lookAt(',p)
  def test_viewport_not_game_workspace(self):
    p=source('src/D18DetailedGalleryPreview.luau')
    self.assertNotIn('workspace.',p.lower())
    self.assertIn('world.Parent=viewport',p)
  def test_four_poses(self):
    p=source('src/D18GalleryController.luau')
    self.assertIn('local POSES = {"idle","tap","win","loss"}',p)
    self.assertIn('factory.SetPose',source('src/D18DetailedGalleryPreview.luau'))
  def test_lod_and_rotation_buttons(self):
    p=source('src/D18GalleryController.luau')
    self.assertIn('poseButton.Activated:Connect',p)
    self.assertIn('lodButton.Activated:Connect',p)
    self.assertIn('rotate.Activated:Connect',p)
    self.assertIn('state.far = not state.far',p)
    self.assertIn('state.yaw = (state.yaw + 45) % 360',p)
  def test_old_six_filters_and_session_favorites_retained(self):
    p=source('src/D18GalleryController.luau')
    for s in ['"魔獣", "魔法", "乗り物", "武器", "ゾンビ", "罠"','favoriteMode.Activated','state.favorites','Catalog.filter']:
      self.assertIn(s,p)
  def test_closed_state_cleanup_both_paths(self):
    p=source('src/D18GalleryController.luau')
    self.assertIn('close.Activated:Connect',p)
    self.assertIn('function state.destroy()',p)
    self.assertIn('Preview.dispose(viewport)\n        gui:Destroy()',p)
  def test_demo_is_opt_in_off_by_default(self):
    s=source('src/DisabledGalleryDemo.client.luau')
    self.assertIn('local ENABLED = false',s)
    self.assertIn('if not ENABLED then return end',s)
  def test_no_server_api_in_own_code(self):
    for name in ('src/D18DetailedGalleryPreview.luau','src/D18GalleryController.luau'):
      s=source(name)
      for bad in ('FireServer','InvokeServer','MarketplaceService','DataStoreService','Humanoid:TakeDamage','game:GetService("ReplicatedStorage")'):
        self.assertNotIn(bad,s)

class BuildWiringAndManifest(unittest.TestCase):
  def test_rojo_file_paths_exist(self):
    project=asdict('default.project.json')
    tree=project['tree']['StarterPlayer']['StarterPlayerScripts']
    mappings=[]
    def visit(obj):
      for k,v in obj.items():
        if k=='$path': mappings.append(v)
        elif isinstance(v,dict): visit(v)
    visit(tree)
    self.assertEqual(len(mappings),13)
    self.assertEqual(len(set(mappings)),len(mappings))
    for path in mappings:self.assertTrue((ROOT/path).is_file(),path)
  def test_rojo_group_factories_not_name_colliding(self):
    tree=asdict('default.project.json')['tree']['StarterPlayer']['StarterPlayerScripts']['D18DetailModels']
    self.assertEqual(set(k for k in tree if not k.startswith('$')),set(EXPECTED_PINS))
    for grp in EXPECTED_PINS:
      self.assertEqual(tree[grp]['$className'],'Folder')
  def test_strict_manifest_schema(self):
    m=asdict('BUILD_MANIFEST.json')
    self.assertEqual(set(m),{'files','format','game_id','packet_id','public_source_allowed','work_id'})
    self.assertEqual(m['format'],'P0D_PUBLIC_SOURCE_V1')
    self.assertEqual(m['game_id'],'TRAP_RAIDERS')
    self.assertEqual(m['work_id'],'p0d-siege-v19')
    self.assertEqual(m['public_source_allowed'],True)
  def test_manifest_hash_size(self):
    m=asdict('BUILD_MANIFEST.json')
    self.assertEqual(len(m['files']),len(set(x['path'] for x in m['files'])))
    for f in m['files']:
      with self.subTest(path=f['path']):
        raw=(ROOT/f['path']).read_bytes()
        self.assertEqual(len(raw),f['size'])
        self.assertEqual(digest(raw),f['sha256'])
  def test_manifest_rejects_negative_tamper_in_memory(self):
    m=asdict('BUILD_MANIFEST.json');f=m['files'][0]
    bad=bytearray((ROOT/f['path']).read_bytes());bad[0]=(bad[0]+1)%256
    self.assertNotEqual(digest(bytes(bad)),f['sha256'])
  def test_manifest_has_all_files_but_self(self):
    m=asdict('BUILD_MANIFEST.json')
    all_files={str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in str(p)}
    self.assertEqual({x['path'] for x in m['files']},all_files-{'BUILD_MANIFEST.json'})

if __name__=='__main__': unittest.main()
