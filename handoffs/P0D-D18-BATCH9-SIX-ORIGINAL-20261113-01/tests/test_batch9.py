import json,pathlib,unittest
R=pathlib.Path(__file__).resolve().parents[1]
class TestBatch9(unittest.TestCase):
 def setUp(self):
  self.data=json.loads((R/'data/models.json').read_text(encoding='utf8'))
  self.cs=self.data['characters']
 def test_count(self):
  self.assertEqual(len(self.cs),6)
  self.assertEqual({c['category'] for c in self.cs},set('BE SP VE WE ZO TR'.split()))
 def test_ids_and_world(self):
  self.assertEqual(len({c['id'] for c in self.cs}),6)
  self.assertTrue(all(c['name'] and c['world'] and c['rarity'] for c in self.cs))
 def test_parts_unique(self):
  for c in self.cs:
   self.assertTrue(8<=len(c['parts'])<=24)
   self.assertEqual(len({p['name'] for p in c['parts']}),len(c['parts']))
 def test_far_signatures(self):
  for c in self.cs:
   far=[p for p in c['parts'] if p['far']]
   self.assertLessEqual(len(far),18)
   self.assertTrue(set(c['signature_tags'])<=set(p['signature_tag'] for p in far))
 def test_limited_coordinates(self):
  for c in self.cs:
   for p in c['parts']:
    self.assertTrue(all(.06<=x<=6 for x in p['size']))
    self.assertTrue(all(-8<=x<=8 for x in p['position']))
    self.assertIn(p['shape'],('Ball','Block','Cylinder'))
    self.assertIn(p['color'],c['palette'])
 def test_safe_preview(self):
  s=(R/'src/D18Batch9Factory.luau').read_text(encoding='utf8')
  for w in ('WorldModel','CanCollide=false','CanTouch=false','CanQuery=false','MAX_ACTIVE=12'):
   self.assertIn(w,s)
  self.assertIn('local ENABLED=false',(R/'src/DisabledPreview.client.luau').read_text(encoding='utf8'))
  gallery=(R/'src/D18StudioGallery.client.luau').read_text(encoding='utf8')
  for w in ('RunService:IsStudio()', 'ViewportFrame', 'WorldModel', 'Factory.Build', 'Factory.SetPose', 'Factory.SetYaw', 'Catalog.ids()'):
   self.assertIn(w,gallery)
 def test_catalog_includes_every_id(self):
  s=(R/'src/D18Batch9Catalog.luau').read_text(encoding='utf8')
  for c in self.cs:self.assertIn(c['id'],s)
 def test_no_authority(self):
  for p in (R/'src').glob('*.luau'):
   s=p.read_text(encoding='utf8')
   for bad in ('DataStoreService','MarketplaceService','RemoteEvent','Humanoid','PlayerAdded','OnServerEvent'):
    self.assertNotIn(bad,s)
if __name__=='__main__':unittest.main()
