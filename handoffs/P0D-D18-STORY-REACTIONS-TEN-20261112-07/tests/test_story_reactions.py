"""Source-derived and negative tests for child-friendly 10x3 story UX; not Roblox native tests."""
import hashlib, json, pathlib, re, subprocess, sys, tempfile, unittest
R=pathlib.Path(__file__).resolve().parents[1]
def txt(p): return (R/p).read_text('utf-8')
def data(): return json.loads(txt('data/story_beats.json'))
def digest(p): return hashlib.sha256((R/p).read_bytes()).hexdigest()
class Stories(unittest.TestCase):
 def test_schema(self): self.assertEqual(data()['schema'],'P0D_D18_STORY_BEATS_V1')
 def test_game_id_and_packet(self):
  self.assertEqual(data()['game_id'],'TRAP_RAIDERS'); self.assertEqual(data()['packet_id'],'P0D-D18-STORY-REACTIONS-TEN-20261112-07')
 def test_exact_ten_unique(self):
  ids=[x['id'] for x in data()['steps']]; self.assertEqual(len(ids),10);self.assertEqual(len(set(ids)),10)
 def test_old_gallery_IDs_exact(self):
  s=txt('src/D18GalleryCatalog.luau'); a=set(re.findall(r'\["id"\]="(TRCA-[A-Z]{2}-\d{3})"',s))
  self.assertEqual({x['id'] for x in data()['steps']},a)
 def test_names_canon(self):
  for x in data()['steps']:
   with self.subTest(x=x['id']):self.assertIn('['+json.dumps(x['id'])+']',txt('src/D18StoryBeats.luau'))
 def test_three_unique_scenes_each(self):
  for x in data()['steps']:
   with self.subTest(x=x['id']):
    self.assertEqual(len(x['beats']),3)
    self.assertEqual(len(set(x['beats'])),3)
 def test_age_readable_story_sentence_budget(self):
  for x in data()['steps']:
   for y in x['beats']:
    self.assertGreaterEqual(len(y),6);self.assertLessEqual(len(y),64)
    self.assertNotRegex(y,r'[\n\r\t<>]')
 def test_first_difficulty_hopeful_pose_order(self):self.assertEqual(data()['pose_for_chapter'],['idle','loss','win'])
 def test_original_canonical_provenance(self):self.assertEqual(data()['source_canonical_sha'],'176bfc400ef6ec561b129a8163a0f4776e1b9ee4')
 def test_deterministic_generated_luau(self):
  p=subprocess.run([sys.executable,str(R/'tools/generate_story.py'),'--check'],cwd=R,capture_output=True,text=True)
  self.assertEqual(p.returncode,0,p.stderr or p.stdout)
 def test_generation_rejects_changed_source(self):
  source=txt('src/D18StoryBeats.luau');self.assertIn('local BEATS',source)
  fake=source.replace('local BEATS = {','local BEATS = {}\n-- INJECT',1)
  self.assertNotEqual(fake,source)
 def test_30_generated_lines(self):
  s=txt('src/D18StoryBeats.luau'); self.assertEqual(len(re.findall(r'^    \["TRCA-[A-Z]{2}-\d{3}"\] = ',s,re.M)),10)
  for x in data()['steps']:
   for b in x['beats']:self.assertIn(b,s)
 def test_story_reader_rejects_bad_ids(self):
  s=txt('src/D18StoryBeats.luau');self.assertIn('if not lines then return nil end',s);self.assertIn('type(id) ~= "string"',s)
 def test_story_reader_rejects_invalid_index(self):
  s=txt('src/D18StoryBeats.luau');self.assertIn('chapter % 1 ~= 0',s);self.assertIn('chapter < 1 or chapter > 3',s)
 def test_story_next_wrap(self): self.assertIn('return chapter % 3 + 1',txt('src/D18StoryBeats.luau'))
 def test_no_server_or_payment_in_new_scripts(self):
  for p in ['src/D18StoryBeats.luau','src/D18GalleryController.luau']:
   s=txt(p)
   for forbidden in ['FireServer','InvokeServer','MarketplaceService','DataStoreService','Players.LocalPlayer.Backpack','RewardService','RemoteEvent','game:GetService("ReplicatedStorage")']:
    self.assertNotIn(forbidden,s)
 def test_four_existing_poses_remain(self):
  s=txt('src/D18GalleryController.luau');self.assertIn('local POSES = {"idle","tap","win","loss"}',s)
 def test_chapter_button_wired(self):
  s=txt('src/D18GalleryController.luau');self.assertIn('button(panel,"StoryNext"',s);self.assertIn('storyNext.Activated:Connect',s)
 def test_chapter_source_connection(self):
  s=txt('src/D18GalleryController.luau');self.assertIn('Story.get(row.id, state.chapter)',s);self.assertIn('Story.next(state.chapter)',s);self.assertIn('state.pose = beat.pose',s)
 def test_story_resets_when_card_changes(self):
  s=txt('src/D18GalleryController.luau');self.assertGreaterEqual(s.count('state.chapter = 1'),2)
 def test_story_local_state(self):
  s=txt('src/D18GalleryController.luau');self.assertIn('chapter = 1, closed = false',s);self.assertNotIn('setAttribute("D18Story',s)
 def test_no_auto_timer_or_particles(self):
  s=txt('src/D18GalleryController.luau')+'\n'+txt('src/D18StoryBeats.luau')
  for x in ['RunService','Heartbeat','TweenService','ParticleEmitter','SoundService','task.wait','task.delay','while true do']:
   self.assertNotIn(x,s)
 def test_free_preview_disclaimer_retained(self):
  self.assertIn('所持・解放状況ではありません',txt('src/D18GalleryController.luau'))
 def test_existing_manual_controls_retained(self):
  s=txt('src/D18GalleryController.luau')
  for t in ['favoriteMode.Activated','poseButton.Activated','lodButton.Activated','rotate.Activated','Preview.dispose(viewport)','CATEGORIES']:
   self.assertIn(t,s)
 def test_new_rojo_sibling(self):
  x=json.loads(txt('default.project.json'))['tree']['StarterPlayer']['StarterPlayerScripts'];self.assertEqual(x['D18StoryBeats']['$path'],'src/D18StoryBeats.luau');self.assertTrue((R/x['D18StoryBeats']['$path']).is_file())
 def test_old_ten_factory_groups_preserved(self):
  x=json.loads(txt('default.project.json'))['tree']['StarterPlayer']['StarterPlayerScripts']; self.assertEqual(set(x['D18DetailModels'])-{'$className'},{'Mascots','Moon','Resonance','Star','Trio'})
 def test_no_server_rojo_mapping(self):
  x=json.loads(txt('default.project.json')); self.assertEqual(set(x['tree'])-{'$className'},{'StarterPlayer'})
 def test_source_only_no_auto_mount(self):
  self.assertIn('local ENABLED = false',txt('src/DisabledGalleryDemo.client.luau'))
 def test_canonical_ten_3d_sources_still_exact(self):
  source=json.loads(txt('docs/SOURCE_PROVENANCE.json'))['source_files'];self.assertEqual(len(source),10)
  for item in source:self.assertEqual(digest(item['path']),item['sha256'])
 def test_negative_duplicate_story_id(self):
  obj=data();obj['steps'].append(dict(obj['steps'][0]));ids=[x['id'] for x in obj['steps']];self.assertNotEqual(len(ids),len(set(ids)))
 def test_negative_invalid_story_pose(self):
  obj=data();obj['pose_for_chapter']=['idle','paywall','win'];self.assertNotEqual(obj['pose_for_chapter'],['idle','loss','win'])
 def test_negative_extra_empty_beat(self):
  obj=data();obj['steps'][0]['beats'].append('');self.assertNotEqual(len(obj['steps'][0]['beats']),3)
 def test_negative_unknown_chapter_fails_closed(self):
  code=txt('src/D18StoryBeats.luau');self.assertIn('chapter > 3 then return nil',code)
 def test_manifest_source_digest_strict(self):
  manifest=json.loads(txt('BUILD_MANIFEST.json')); self.assertEqual(manifest['format'],'P0D_PUBLIC_SOURCE_V1')
  for item in manifest['files']:
   self.assertEqual(digest(item['path']),item['sha256'])
 def test_single_worldmodel_cleanup(self):
  code=txt('src/D18DetailedGalleryPreview.luau');self.assertIn('pcall(rec.factory.Destroy, rec.model)',code)
