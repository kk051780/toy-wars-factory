"""Independent source-derived 12-model extension regression, negative tests.
These are NOT Roblox native compilation or real Studio rendering tests.
"""
import hashlib, json, pathlib, re, subprocess, sys, tempfile, unittest, zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
NEW_IDS={'TRCA-TR-063','TRCA-WE-099'}
COUNTS={'TRCA-TR-063':21,'TRCA-WE-099':27}
CANON='176bfc400ef6ec561b129a8163a0f4776e1b9ee4'
UPSTREAM='98811a9af95e170d359a35647b4c1f22060e49ce'
OLD10_HASH='16ee8d2dc55b8ee7ebfdbff45b1f50d3a67743e065d29efd7c7745bb8ca7c701'
def text(p):return (ROOT/p).read_text('utf8')
def raw(p):return (ROOT/p).read_bytes()
def obj(p):return json.loads(text(p))
def sha(b):return hashlib.sha256(b).hexdigest()

class GalleryTwelve(unittest.TestCase):
 def test_12_exact_unique_gallery_ids(self):
  ids=[e['id'] for e in obj('data/gallery.json')['entries']]
  self.assertEqual(len(ids),12);self.assertEqual(len(set(ids)),12)
  self.assertEqual(set(ids[-2:]),NEW_IDS)
 def test_previous_ten_bytes_canonically_unchanged(self):
  old=obj('data/gallery.json')['entries'][:10]
  b=json.dumps(old,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf8')
  self.assertEqual(sha(b),OLD10_HASH)
 def test_new_names_world_rarity_faithful(self):
  a={x['id']:x for x in obj('data/gallery.json')['entries']}
  self.assertEqual((a['TRCA-TR-063']['name'],a['TRCA-TR-063']['category'],a['TRCA-TR-063']['rarity'],a['TRCA-TR-063']['world']),('火輪跳ね台','罠','レジェンド','火輪の熔炉'))
  self.assertEqual((a['TRCA-WE-099']['name'],a['TRCA-WE-099']['category'],a['TRCA-WE-099']['rarity'],a['TRCA-WE-099']['world']),('遊園ホルン','武器','レジェンド','夢菓子の遊園'))
 def test_metadata_not_fake_simplified_3d(self):
  self.assertEqual([x['parts'] for x in obj('data/gallery.json')['entries'][-2:]], [[],[]])
 def test_generated_gallery_catalog_all_12(self):
  s=text('src/D18GalleryCatalog.luau')
  self.assertEqual(len(re.findall(r'\["id"\]="TRCA-[A-Z]{2}-\d{3}"',s)),12)
  for i in NEW_IDS:self.assertIn(f'["id"]="{i}"',s)
 def test_deterministic_gallery_generator(self):
  p=subprocess.run([sys.executable,'tools/generate_catalog.py','--check'],cwd=ROOT,capture_output=True,text=True)
  self.assertEqual(p.returncode,0,p.stdout+p.stderr)
 def test_gallery_generator_rejects_tampered_copy(self):
  with tempfile.TemporaryDirectory() as d:
   r=pathlib.Path(d);(r/'tools').mkdir();(r/'data').mkdir();(r/'src').mkdir()
   (r/'tools/generate_catalog.py').write_bytes(raw('tools/generate_catalog.py'))
   payload=obj('data/gallery.json');payload['entries'][10]['name']='改ざん'
   (r/'data/gallery.json').write_text(json.dumps(payload,ensure_ascii=False),'utf8')
   (r/'src/D18GalleryCatalog.luau').write_bytes(raw('src/D18GalleryCatalog.luau'))
   p=subprocess.run([sys.executable,'tools/generate_catalog.py','--check'],cwd=r,capture_output=True,text=True)
   self.assertNotEqual(p.returncode,0)
 def test_exact_12_preview_map(self):
  source=text('src/D18DetailedGalleryPreview.luau')
  ids=re.findall(r'\["(TRCA-[A-Z]{2}-\d{3})"\] = \{"',source)
  self.assertEqual(ids,[e['id'] for e in obj('data/gallery.json')['entries']])
 def test_new_map_routes_to_original_factory(self):
  s=text('src/D18DetailedGalleryPreview.luau')
  for id,n in COUNTS.items():self.assertIn(f'["{id}"] = {{"FinalV8", "ShowcaseFactory", {n}}}',s)
 def test_final_sources_bit_exact_v8(self):
  rec=obj('docs/SOURCE_PROVENANCE.json')['source_files'];new=[x for x in rec if 'FinalV8/' in x['path']]
  self.assertEqual(len(new),2)
  for x in new:
   self.assertEqual(x['upstream_sha'],UPSTREAM)
   self.assertEqual(sha(raw(x['path'])),x['sha256'])
   self.assertEqual(len(raw(x['path'])),x['bytes'])
 def test_all_old_source_factory_hashes_still_same(self):
  for x in obj('docs/SOURCE_PROVENANCE.json')['source_files']:
   self.assertEqual(sha(raw(x['path'])),x['sha256'])
 def test_new_source_part_counts_and_shapes(self):
  source=obj('data/v8_last_two_geometry.json')['characters']
  self.assertEqual(set(source),NEW_IDS)
  for id,n in COUNTS.items():self.assertEqual(len(source[id]['parts']),n)
  tr=' '.join(x['name'] for x in source['TRCA-TR-063']['parts'])
  we=' '.join(x['name'] for x in source['TRCA-WE-099']['parts'])
  self.assertTrue('脚' in tr and ('輪' in tr or '鉄' in tr))
  self.assertTrue('輪' in we or 'ホルン' in we)
 def test_frozen_original_geo_catalog_is_readable(self):
  s=text('src/D18DetailModels/FinalV8/ShowcaseCatalog.luau')
  for id in NEW_IDS:self.assertIn(id,s)
  self.assertIn('function C.get(',s)
 def test_model_factory_has_full_safe_lifecycle(self):
  s=text('src/D18DetailModels/FinalV8/ShowcaseFactory.luau')
  for f in ['Build','SetPose','SetLod','GetStatus','Destroy']:self.assertRegex(s,r'function Factory\.'+f+r'\(')
  for x in ['Anchored = true','CanCollide = false','CanTouch = false','CanQuery = false','CastShadow = false','MAX_PREVIEWS = 12']:self.assertIn(x,s)
 def test_worldmodel_and_destroy_for_old_new(self):
  s=text('src/D18DetailedGalleryPreview.luau')
  for x in ['Instance.new("WorldModel")','stage.Parent=world','pcall(rec.factory.Destroy, rec.model)','factory.Build(stage,entry.id,CFrame.new())']:self.assertIn(x,s)
 def test_rojo_new_factory_and_catalog_siblings(self):
  d=obj('default.project.json')['tree']['StarterPlayer']['StarterPlayerScripts']['D18DetailModels']['FinalV8']
  self.assertEqual(d['ShowcaseFactory']['$path'],'src/D18DetailModels/FinalV8/ShowcaseFactory.luau')
  self.assertEqual(d['ShowcaseCatalog']['$path'],'src/D18DetailModels/FinalV8/ShowcaseCatalog.luau')
 def test_no_server_mappings_and_disabled_start(self):
  tree=obj('default.project.json')['tree']
  self.assertEqual(set(tree)-{'$className'},{'StarterPlayer'})
  self.assertIn('local ENABLED = false',text('src/DisabledGalleryDemo.client.luau'))
 def test_new_story_36_beats(self):
  steps=obj('data/story_beats.json')['steps']
  self.assertEqual(len(steps),12)
  self.assertEqual(sum(len(x['beats']) for x in steps),36)
  self.assertEqual(set(x['id'] for x in steps[-2:]),NEW_IDS)
 def test_new_original_story_plot_substance(self):
  a={x['id']:x['beats'] for x in obj('data/story_beats.json')['steps']}
  self.assertIn('帽子',a['TRCA-TR-063'][1]);self.assertIn('輪',a['TRCA-TR-063'][2]);self.assertIn('再会',a['TRCA-WE-099'][2])
 def test_generated_story_and_three_poses(self):
  s=text('src/D18StoryBeats.luau')
  for id in NEW_IDS:self.assertIn(f'["{id}"]',s)
  self.assertIn('local POSES = {"idle", "loss", "win"}',s)
  self.assertIn('return chapter % 3 + 1',s)
  p=subprocess.run([sys.executable,'tools/generate_story.py','--check'],cwd=ROOT,capture_output=True,text=True)
  self.assertEqual(p.returncode,0,p.stdout+p.stderr)
 def test_story_generator_rejects_duplicate_id(self):
  with tempfile.TemporaryDirectory() as d:
   r=pathlib.Path(d);(r/'tools').mkdir();(r/'data').mkdir();(r/'src').mkdir()
   (r/'tools/generate_story.py').write_bytes(raw('tools/generate_story.py'))
   payload=obj('data/story_beats.json');payload['steps'][11]['id']=payload['steps'][10]['id']
   (r/'data/story_beats.json').write_text(json.dumps(payload,ensure_ascii=False),'utf8')
   (r/'src/D18StoryBeats.luau').write_bytes(raw('src/D18StoryBeats.luau'))
   p=subprocess.run([sys.executable,'tools/generate_story.py','--check'],cwd=r,capture_output=True,text=True)
   self.assertNotEqual(p.returncode,0)
 def test_gui_12_labels_and_same_controls(self):
  s=text('src/D18GalleryController.luau')
  for x in ['12体を無料プレビュー','/12体 ／ ☆','storyNext.Activated','poseButton.Activated','lodButton.Activated','rotate.Activated','favoriteMode.Activated']:self.assertIn(x,s)
  self.assertNotIn('/10体 ／ ☆',s)
 def test_gui_no_fake_inventory_or_purchase(self):
  s='\n'.join(text(p) for p in ['src/D18GalleryController.luau','src/D18DetailedGalleryPreview.luau','src/D18StoryBeats.luau'])
  for forbidden in ['FireServer','InvokeServer','MarketplaceService','DataStoreService','RemoteEvent','game:GetService("ReplicatedStorage")','Humanoid:TakeDamage','while true do']:
   self.assertNotIn(forbidden,s)
 def test_safety_invalid_ids_rejected(self):
  src=text('src/D18DetailedGalleryPreview.luau')
  for x in ['UNKNOWN_CHARACTER_ID','SOURCE_REQUIRE_FAILED','SOURCE_PART_COUNT_DRIFT','SOURCE_SAFETY_REJECTED','INVALID_YAW','INVALID_LOD','INVALID_POSE']:self.assertIn(x,src)
 def test_no_duplicate_catalog_ids(self):
  ids=[x['id'] for x in obj('data/gallery.json')['entries']]
  self.assertEqual(len(ids),len(set(ids)))
 def test_packet_is_separate_from_S1(self):
  self.assertNotIn('releases/P0D_S1_KIDS_RC01',text('default.project.json'))
  self.assertNotIn('game:GetService("ServerScriptService")',text('src/DisabledGalleryDemo.client.luau'))
 def test_immutable_header_keyless_public(self):
  m=obj('BUILD_MANIFEST.json')
  self.assertEqual(set(m),{'files','format','game_id','packet_id','public_source_allowed','work_id'})
  self.assertTrue(m['public_source_allowed'])
  self.assertEqual(m['packet_id'],'P0D-D18-TWELVE-DETAIL-STORY-GALLERY-20261112-09')
 def test_source_manifest_rejects_tamper(self):
  m=obj('BUILD_MANIFEST.json')['files'][0]
  b=bytearray(raw(m['path']))
  b[0]=(b[0]+1)%256
  self.assertNotEqual(sha(bytes(b)),m['sha256'])

if __name__=='__main__':unittest.main()
