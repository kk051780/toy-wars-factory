# Execute with: python3 -m unittest discover -s tests -v
import json, pathlib, re, unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT/'data'/'collection_contract.json').read_text(encoding='utf-8'))
SRC = (ROOT/'src'/'Ext2Catalog.luau').read_text(encoding='utf-8')
FACTORY = (ROOT/'src'/'Ext2Factory.luau').read_text(encoding='utf-8')
class Ext2ContractTest(unittest.TestCase):
 def test_counts(self):
  self.assertEqual((DATA['previousCanonical72'],DATA['previousExtension12'],DATA['newOriginal16'],DATA['totalSourcePrototypeCount']),(72,12,16,100))
  self.assertEqual(len(DATA['items']),16)
 def test_all_original_and_unique(self):
  items=DATA['items']; ids=[i['itemId'] for i in items]
  self.assertEqual(len(set(ids)),16)
  self.assertEqual(len(set(i['name'] for i in items)),16)
  self.assertTrue(all(re.fullmatch(r'TRCX-(BE|SP|VE|WE|ZO|TR)-00[3-6]',i) for i in ids))
 def test_four_worlds_and_categories(self):
  items=DATA['items']; worlds=set(i['world'] for i in items)
  self.assertEqual(len(worlds),4)
  self.assertTrue(all(sum(x['world']==w for x in items)==4 for w in worlds))
  self.assertEqual({k:sum(x['category']==k for x in items) for k in {'BEAST','SPELL','MOUNT','ITEM','ZOMBIE','TRAP'}},{'BEAST':4,'SPELL':3,'MOUNT':3,'ITEM':2,'ZOMBIE':2,'TRAP':2})
 def test_item_visual_quality_and_budget(self):
  for i in DATA['items']:
   self.assertEqual(len(i['threeSecondSilhouette']),3)
   self.assertGreaterEqual(len(i['accents']),6)
   self.assertLessEqual(len(i['accents']),9)
   self.assertTrue(all(len(s)==8 and 1<=s[7]<=4 and min(s[4:7])>0 for s in i['accents']))
   self.assertEqual(i['partBudgetMax'],20)
   self.assertEqual(set(i['palette']),{'main','accent','glow','shade'})
 def test_source_never_fake_entitlement(self):
  self.assertEqual(DATA['verifiedLiveOwnedOrEquippedCount'],0)
  self.assertFalse(DATA['noPaidOdds'] is False)
  self.assertTrue(all(i['sourceItemOnly'] and not i['playerOwned'] and not i['availableInLiveGame'] and not i['actualAbilityImplemented'] and i['raritySidegradeOnly'] for i in DATA['items']))
  self.assertTrue(all(i['counterplay'] and i['abilityConcept'] and i['freeStarterEquivalentRequired'] for i in DATA['items']))
 def test_source_id_mapping(self):
  # Every exact item id appears in the immutable source table.
  for i in DATA['items']:
   self.assertIn(i['itemId'],SRC)
  self.assertIn('RunService:IsStudio()',FACTORY)
  self.assertIn('CanCollide = false',FACTORY)
  self.assertIn('OVER_BUDGET',FACTORY)
 def test_no_game_authority(self):
  for k in ('DataStoreService','RemoteEvent','MarketplaceService','ProcessReceipt','SetAsync','UpdateAsync'):
   self.assertNotIn(k,FACTORY)
if __name__=='__main__': unittest.main()
