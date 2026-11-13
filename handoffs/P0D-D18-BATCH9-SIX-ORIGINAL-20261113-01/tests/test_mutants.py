import copy,json,pathlib,sys,unittest
R=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/"tools"))
import verify_batch9 as V

class TestBatch9Safety(unittest.TestCase):
 def setUp(self):
  self.d=json.loads((R/"data/models.json").read_text(encoding="utf-8"))
 def test_all_valid(self):
  self.assertTrue(V.validate_models(self.d))
 def test_frozen_source_manifest(self):
  self.assertTrue(V.verify_manifest())
 def test_six_untaken_id_against_prior60(self):
  repo=R.parents[1]
  root=repo/"handoffs"
  c6=json.loads((root/"P0D-D18-BATCH6-SIX-WORLDS-20261113-01/data/batch_claims.json").read_text(encoding="utf-8"))
  c7=json.loads((root/"P0D-D18-BATCH7-SIX-CHILD-EXPLORE-20261113-01/data/models.json").read_text(encoding="utf-8"))
  c8=json.loads((root/"P0D-D18-BATCH8-SIX-ORIGINAL-DISPLAY-20261113-01/data/models.json").read_text(encoding="utf-8"))
  before=set(c6["previous_3d_source_ids"]+c6["new_3d_source_ids"]+
             [x["id"] for x in c7["characters"]]+[x["id"] for x in c8["characters"]])
  self.assertEqual(len(before),60)
  newer={x["id"] for x in self.d["characters"]}
  self.assertFalse(before & newer)
  self.assertEqual(len(before|newer),66)
  register=json.loads((root/"P0D-D18-BATCH6-SIX-WORLDS-20261113-01/data/flagship72_registry.json").read_text(encoding="utf-8"))
  canon={x["id"]:x for x in register["entries"]}
  self.assertEqual(len(canon),72)
  self.assertTrue(newer <= canon.keys())
  for m in self.d["characters"]:
   e=canon[m["id"]]
   self.assertEqual((m["name"],m["world"],m["rarity"]),
        (e["name"],e["world"],e["rarity"]))
 def test_ten_hostile_data_mutants_fail_closed(self):
  def duplicated(d):d["characters"][1]["id"]=d["characters"][0]["id"]
  def identity(d):d["characters"][0]["name"]="他IPを使ったコピー"
  def missing_far_tag(d):
   for p in d["characters"][0]["parts"]:
    if p["signature_tag"]==d["characters"][0]["signature_tags"][1]:p["far"]=False
  def oversize(d):d["characters"][0]["parts"][0]["size"]=[200,200,200]
  def tiny(d):d["characters"][1]["parts"][0]["size"]=[0,0.1,0.1]
  def new_color(d):d["characters"][2]["parts"][0]["color"]="unknown"
  def bad_shape(d):d["characters"][3]["parts"][0]["shape"]="MeshPart"
  def missing_pose(d):d["characters"][4]["pose_offsets"].pop("win")
  def fake_group(d):d["characters"][5]["pose_offsets"]["tap"]={"ghost":{"dy":0.1}}
  def duplicate_part(d):d["characters"][0]["parts"][1]["name"]=d["characters"][0]["parts"][0]["name"]
  for f in [duplicated,identity,missing_far_tag,oversize,tiny,new_color,bad_shape,missing_pose,fake_group,duplicate_part]:
   d=copy.deepcopy(self.d);f(d)
   with self.subTest(f=f.__name__),self.assertRaises(ValueError):
    V.validate_models(d)
 def test_no_role_or_reward_or_paid_authority(self):
  for p in (R/"src").glob("*.luau"):
   txt=p.read_text(encoding="utf-8")
   for s in ["DataStoreService","MarketplaceService","RemoteEvent",
             "OnServerEvent","Players.PlayerAdded","Humanoid.WalkSpeed","FireServer"]:
    self.assertNotIn(s,txt)
  self.assertIn("local ENABLED=false",(R/"src/DisabledPreview.client.luau").read_text(encoding="utf-8"))

if __name__=="__main__":unittest.main()
