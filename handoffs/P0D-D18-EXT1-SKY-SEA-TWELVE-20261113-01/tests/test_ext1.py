import copy,json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import verify_ext1 as V
class TwelveNewOriginalModels(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.d=json.loads((ROOT/"data/models.json").read_text(encoding="utf8"))
  cls.c=json.loads((ROOT/"data/collection_contract.json").read_text(encoding="utf8"))
 def test_source_count_84_and_12_new_original_3d(self):
  self.assertEqual(V.validate(self.d)["total"],84)
  self.assertEqual(len(self.d["characters"]),12)
 def test_strict_original_72_unchanged(self):
  a,b=V.load_legacy()
  self.assertEqual(len(a),72);self.assertEqual(len(b),72)
  self.assertFalse(a.intersection({x["id"] for x in self.d["characters"]}))
  self.assertFalse(b.intersection({x["name"] for x in self.d["characters"]}))
 def test_two_worlds_six_category_each(self):
  for w in V.WORLDS:
   items=[x for x in self.d["characters"] if x["world"]==w]
   self.assertEqual(len(items),6)
   self.assertEqual({x["category"] for x in items},set(V.CATS))
 def test_three_far_distinctions_every_character(self):
  for c in self.d["characters"]:
   far={p["signature_tag"] for p in c["parts"] if p["far"]}
   self.assertTrue(set(c["signature_tags"])<=far)
 def test_four_client_view_only_poses(self):
  for c in self.d["characters"]:
   self.assertEqual(set(c["pose_offsets"]),{"idle","tap","win","loss"})
 def test_original_model_budget(self):
  self.assertEqual(sum(len(c["parts"]) for c in self.d["characters"]),132)
  self.assertTrue(all(10<=len(c["parts"])<=24 for c in self.d["characters"]))
 def test_collection_contract_fair_and_not_live(self):
  self.assertTrue(V.validate_contract(self.c,self.d))
 def test_12_original_source_gitblobs(self):
  self.assertTrue(V.verify_manifest())
 def test_no_authority_ever_in_preview(self):
  for p in (ROOT/"src").glob("*.luau"):
   s=p.read_text(encoding="utf8")
   for x in ("RemoteEvent","OnServerEvent","FireServer","DataStoreService","MarketplaceService","ProcessReceipt","Humanoid.WalkSpeed"):
    self.assertNotIn(x,s,p.name)
 def test_gallery_studio_only_and_12_preview_models(self):
  g=(ROOT/"src/D18StudioGallery.client.luau").read_text(encoding="utf8")
  f=(ROOT/"src/D18Ext1Factory.luau").read_text(encoding="utf8")
  self.assertIn("if not RunService:IsStudio() then return end",g)
  self.assertIn('assert(#ids==12,"D18_X1_TWELVE_PREVIEW_ONLY")',g)
  for x in ('WorldModel','CanCollide=false','CanTouch=false','CanQuery=false','MAX_ACTIVE=12'):
   self.assertIn(x,f)
 def test_twelve_unsafe_source_mutants_rejected(self):
  def dup(d):d["characters"][1]["id"]=d["characters"][0]["id"]
  def duplicate_name(d):d["characters"][0]["name"]=d["characters"][1]["name"]
  def legacy_id(d):d["characters"][0]["id"]="TRCA-BE-108"
  def old_title(d):d["characters"][0]["name"]="七鈴の王獣"
  def far_lost(d):
   for p in d["characters"][0]["parts"]:
    if p["signature_tag"]==d["characters"][0]["signature_tags"][0]:p["far"]=False
  def wrong_world(d):d["characters"][1]["world"]=V.WORLDS[1]
  def large(d):d["characters"][0]["parts"][0]["size"]=[100,100,100]
  def neg(d):d["characters"][0]["parts"][0]["size"]=[-.1,.5,.5]
  def nan(d):d["characters"][0]["parts"][0]["position"]=[float("nan"),0,0]
  def shape(d):d["characters"][0]["parts"][0]["shape"]="MeshPart"
  def namepart(d):d["characters"][0]["parts"][1]["name"]=d["characters"][0]["parts"][0]["name"]
  def pose(d):d["characters"][0]["pose_offsets"]["tap"]={"not-a-real-group":{"dy":.1}}
  for mut in (dup,duplicate_name,legacy_id,old_title,far_lost,wrong_world,large,neg,nan,shape,namepart,pose):
   d=copy.deepcopy(self.d);mut(d)
   with self.subTest(mutation=mut.__name__),self.assertRaises(ValueError):
    V.validate(d)
 def test_fake_paid_ownership_or_equip_mutations_rejected(self):
  for field,value in [("implementedOwnedItems",1),("equippingImplemented",True),
                      ("realGameHatchingImplemented",True),("probabilityTablePresent",True),("noPayToWin",False)]:
   d=copy.deepcopy(self.c);d[field]=value
   with self.subTest(field=field),self.assertRaises(ValueError):V.validate_contract(d,self.d)
if __name__=="__main__":unittest.main()
