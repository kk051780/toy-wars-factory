import copy,json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from verify_batch7 import validate_models,verify_manifest
class TestBatch7Negative(unittest.TestCase):
 def setUp(self):
  self.d=json.loads((ROOT/"data/models.json").read_text(encoding="utf8"))
 def mutate(self,fn):
  d=copy.deepcopy(self.d);fn(d)
  with self.assertRaises(ValueError):validate_models(d)
 def test_positive(self):self.assertTrue(validate_models(self.d))
 def test_source_receipt(self):self.assertTrue(verify_manifest())
 def test_reject_fake_id(self):self.mutate(lambda d:d["characters"][0].update(id="TRCA-BE-999"))
 def test_reject_wrong_world(self):self.mutate(lambda d:d["characters"][0].update(world="NONCANON"))
 def test_reject_signature_loss(self):
  def bad(d):
   c=d["characters"][0];tag=c["signature_tags"][0]
   for p in c["parts"]:
    if p["signature_tag"]==tag:p["far"]=False
  self.mutate(bad)
 def test_reject_duplicate_parts(self):
  self.mutate(lambda d:d["characters"][0]["parts"][1].update(name=d["characters"][0]["parts"][0]["name"]))
 def test_reject_illegal_gameplay_part(self):
  self.mutate(lambda d:d["characters"][0]["parts"][0].update(CanCollide=True))
 def test_reject_oversize(self):
  self.mutate(lambda d:d["characters"][0]["parts"][0].update(size=[99,1,1]))
 def test_reject_fake_atlas(self):self.mutate(lambda d:d.update(source_atlas_sha256="0"*64))
 def test_reject_unknown_pose_group(self):
  self.mutate(lambda d:d["characters"][0]["pose_offsets"]["tap"].update(serverHP={"dy":.2}))
if __name__=="__main__":unittest.main()
