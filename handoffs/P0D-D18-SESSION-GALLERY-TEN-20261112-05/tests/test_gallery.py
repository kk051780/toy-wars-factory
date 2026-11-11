from pathlib import Path
import unittest,json,math,re,subprocess,sys,hashlib,tempfile,shutil
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from verify_pack import verify
DATA=json.loads((ROOT/'data/gallery.json').read_text('utf8'))
E=DATA['entries']
def src(name):return (ROOT/'src'/name).read_text('utf8')

class TestD18Gallery(unittest.TestCase):
 def test_01_correct_scope(self):
  self.assertEqual(DATA['schema'],'P0D_D18_VIEWPORT_GALLERY_V1')
  self.assertEqual(DATA['game_id'],'TRAP_RAIDERS')
  self.assertEqual(DATA['work_id'],'p0d-siege-v19')
 def test_02_ten_unique_pinned_ids(self):
  self.assertEqual([e['id'] for e in E],['TRCA-BE-018','TRCA-ZO-054','TRCA-BE-072','TRCA-SP-027','TRCA-VE-090','TRCA-TR-009','TRCA-WE-045','TRCA-SP-081','TRCA-VE-036','TRCA-ZO-108'])
 def test_03_exact_names(self):
  self.assertEqual([e['name'] for e in E],['祖樹の角鹿','灯台のお迎え兵','月冠キリン','大地の共鳴','時帰りの砂船','星跳ねの発射台','雷鳥ホルン','黄金の種まき','永久晶観測台','七鈴の大隊長'])
 def test_04_categories(self):
  self.assertEqual({e['category'] for e in E},{'魔獣','魔法','乗り物','武器','ゾンビ','罠'})
 def test_05_exact_rarity(self):
  self.assertEqual([e['rarity'] for e in E],['ミシック','レジェンド','レジェンド','ミシック','レジェンド','ミシック','レジェンド','レジェンド','ミシック','レジェンド'])
 def test_06_complete_metadata(self):
  for e in E:
   for key in ('id','name','category','rarity','world','story','accent','parts'):self.assertIn(key,e)
   self.assertTrue(e['story'] and e['world'])
 def test_07_model_preview_budget(self):
  self.assertLessEqual(sum(len(e['parts']) for e in E),110)
  for e in E:self.assertTrue(5<=len(e['parts'])<=18,e['id'])
 def test_08_unique_part_names(self):
  for e in E:self.assertEqual(len({p['name'] for p in e['parts']}),len(e['parts']),e['id'])
 def test_09_part_fields(self):
  for e in E:
   for p in e['parts']:
    self.assertEqual(set(p),{'name','pos','size','color','shape','rot','far'})
    self.assertIn(p['shape'],('Block','Ball','Cylinder'))
    self.assertEqual(len(p['pos']),3);self.assertEqual(len(p['size']),3);self.assertEqual(len(p['rot']),3)
    self.assertEqual(len(p['color']),3);self.assertIsInstance(p['far'],bool)
 def test_10_positive_sizes(self):
  for e in E:
   for p in e['parts']:self.assertTrue(all(.08<=v<=4 for v in p['size']),(e['id'],p))
 def test_11_finite_coordinates(self):
  for e in E:
   for p in e['parts']:
    self.assertTrue(all(isinstance(x,(int,float)) and math.isfinite(x) and abs(x)<=8 for x in p['pos']))
    self.assertTrue(all(isinstance(x,(int,float)) and math.isfinite(x) and abs(x)<=360 for x in p['rot']))
 def test_12_colors(self):
  for e in E:
   for p in e['parts']:self.assertTrue(all(type(c)==int and 0<=c<=255 for c in p['color']))
 def test_13_catalog_generated_exact(self):
  p=subprocess.run([sys.executable,str(ROOT/'tools/generate_catalog.py'),'--check'],capture_output=True,text=True)
  self.assertEqual(p.returncode,0,p.stderr)
 def test_14_three_real_source_modules(self):
  for name in ('D18GalleryCatalog.luau','D18GalleryPreview.luau','D18GalleryController.luau'):self.assertGreater(len(src(name)),1000)
 def test_15_preview_worldmodel_only(self):
  s=src('D18GalleryPreview.luau')
  self.assertIn('Instance.new("WorldModel")',s)
  self.assertIn('Instance.new("Camera")',s)
  self.assertIn('model:GetBoundingBox()',s)
  self.assertIn('viewport.CurrentCamera = camera',s)
 def test_16_preview_safe_parts(self):
  s=src('D18GalleryPreview.luau')
  for token in ('part.Anchored = true','part.CanCollide = false','part.CanTouch = false','part.CanQuery = false','part.CastShadow = false'):self.assertIn(token,s)
 def test_17_camera_rotate(self):
  s=src('D18GalleryController.luau')
  self.assertIn('(state.yaw + 45) % 360',s)
  self.assertIn('Preview.render(viewport,row,state.yaw)',s)
 def test_18_mobile_constraints(self):
  s=src('D18GalleryController.luau')
  for token in ('UISizeConstraint','ScrollingFrame','AutomaticCanvasSize','UDim2.fromScale','TextWrapped = true'):self.assertIn(token,s)
 def test_19_category_tabs(self):
  s=src('D18GalleryController.luau')
  for category in ('すべて','魔獣','魔法','乗り物','武器','ゾンビ','罠'):self.assertIn(category,s)
 def test_20_no_inventory_claims(self):
  s=src('D18GalleryController.luau')
  for label in ('おためし','所持・解放状況ではありません','保存されません'):self.assertIn(label,s)
 def test_21_favorites_session_only(self):
  s=src('D18GalleryController.luau')
  self.assertIn('favorites = {}',s)
  self.assertIn('state.favorites[state.selected] = true',s)
  self.assertIn('state.favoriteOnly = not state.favoriteOnly',s)
 def test_22_controls_activated(self):
  s=src('D18GalleryController.luau')
  self.assertGreaterEqual(s.count('.Activated:Connect('),6)
 def test_23_empty_filtered_state(self):
  s=src('D18GalleryController.luau')
  self.assertIn('選べるキャラがありません',s)
  self.assertIn('state.selected = available[1] and available[1].id or ""',s)
 def test_24_close_cleanup(self):
  s=src('D18GalleryController.luau')
  self.assertIn('function state.destroy()',s)
  self.assertIn('gui:Destroy()',s)
 def test_25_demo_off(self):
  s=src('DisabledGalleryDemo.client.luau')
  self.assertIn('local ENABLED = false',s)
  self.assertIn('if not ENABLED then return end',s)
 def test_26_no_server_side_effects(self):
  for p in (ROOT/'src').glob('*.luau'):
   text=p.read_text('utf8')
   for forbidden in (r'FireServer\s*\(',r'InvokeServer\s*\(',r'DataStoreService',r'MarketplaceService',r'Instance\.new\s*\(\s*["\']RemoteEvent',r'game\.Workspace\s*=',r'workspace\s*:'):self.assertNotRegex(text,forbidden,p)
 def test_27_strict_manifest(self):self.assertEqual(verify(ROOT),10)
 def test_28_negative_manifest_tamper(self):
  with tempfile.TemporaryDirectory() as tmp:
   t=Path(tmp);shutil.copytree(ROOT,t/'pack');p=t/'pack/data/gallery.json';p.write_bytes(p.read_bytes()+b' ') 
   with self.assertRaises(AssertionError):verify(t/'pack')
 def test_29_negative_path_traversal(self):
  with tempfile.TemporaryDirectory() as tmp:
   t=Path(tmp);shutil.copytree(ROOT,t/'pack');m=t/'pack/BUILD_MANIFEST.json';obj=json.loads(m.read_text('utf8'));obj['files'][0]['path']='../bad';m.write_text(json.dumps(obj),encoding='utf8')
   with self.assertRaises(AssertionError):verify(t/'pack')
 def test_30_negative_duplicate_manifest(self):
  with tempfile.TemporaryDirectory() as tmp:
   t=Path(tmp);shutil.copytree(ROOT,t/'pack');m=t/'pack/BUILD_MANIFEST.json';obj=json.loads(m.read_text('utf8'));obj['files'].append(obj['files'][0]);m.write_text(json.dumps(obj),encoding='utf8')
   with self.assertRaises(AssertionError):verify(t/'pack')
 def test_31_source_files_no_external_assets(self):
  for e in E:
   for p in e['parts']:self.assertNotIn('assetId',p)
 def test_32_ten_doc_source_manifest_entries(self):
  obj=json.loads((ROOT/'BUILD_MANIFEST.json').read_text('utf8'))
  self.assertEqual(len(obj['files']),10)
 def test_33_10_no_unlock_games(self):
  self.assertIn('No game ownership or unlocking is displayed', (ROOT/'docs/INTEGRATION.md').read_text('utf8'))
 def test_34_canon_worlds(self):
  by={e['id']:e['world'] for e in E}
  self.assertEqual(by['TRCA-ZO-054'],'泡音の水都')
  self.assertEqual(by['TRCA-BE-018'],'苔灯の深森')
 def test_35_zero_existing_model_count_increment(self):
  txt=(ROOT/'README.md').read_text('utf8');self.assertIn('10/72 (13.89%) remains unchanged',txt)
if __name__=='__main__':unittest.main(verbosity=2)
