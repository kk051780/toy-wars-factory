#!/usr/bin/env python3
"""P0D D18 Batch5 fixed source-only 3D model acceptance and adversarial tests."""
import copy
import importlib.util
import json
import pathlib
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location("d18_generator",ROOT/"tools/generate_catalog.py")
g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)
paths=("data/six_pilot_geometry.json","data/archetype_rules.json",
 "data/flagship72_registry.json","data/next54_source_queue.json","data/batch_claims.json")
def load():return [json.loads((ROOT/p).read_text(encoding="utf8")) for p in paths]
IDS=["TRCA-BE-045","TRCA-SP-054","TRCA-TR-099","TRCA-VE-018","TRCA-WE-072","TRCA-ZO-090"]
def fail_mutation(fn):
 a,b,c,d,e=map(copy.deepcopy,load());fn(a,b,c,d,e)
 with unittest.TestCase().assertRaises(ValueError):g.validate(a,b,c,d,e)
class D18Batch5(unittest.TestCase):
 def test_pinned_exact_new_six_and_claim(self):
  a,b,c,d,e=load()
  self.assertEqual(set(a["characters"]),set(IDS))
  self.assertEqual(len(e["previous_3d_source_ids"]),36)
  self.assertEqual(len(e["new_3d_source_ids"]),6)
  self.assertEqual(d["remaining_source_not_started_count"],30)
  self.assertTrue(g.validate(a,b,c,d,e))
 def test_deterministic_original_luau(self):
  self.assertEqual(g.generate(),(ROOT/"src/D18BatchCatalog.luau").read_text(encoding="utf8"))
 def test_three_visible_signature_cues_per_character(self):
  a,*_=load()
  for ch in a["characters"].values():
   self.assertLessEqual(len(ch["parts"]),24)
   far=[p for p in ch["parts"] if p["far"]]
   self.assertLessEqual(len(far),18)
   self.assertEqual(len(ch["signature_tags"]),3)
   self.assertTrue(set(ch["signature_tags"])<=set(x["signature_tag"] for x in far))
   self.assertEqual(set(ch["pose_offsets"]),{"idle","tap","win","loss"})
 def test_worldmodel_only_off_by_default(self):
  src=(ROOT/"src/D18BatchFactory.luau").read_text(encoding="utf8")
  for key in ('not parent:IsA("WorldModel")','p.CanCollide = false','p.CanTouch = false','p.CanQuery = false','Factory.SetPose','Factory.Destroy'):
   self.assertIn(key,src)
  self.assertIn("local ENABLED = false",(ROOT/"src/DisabledPilotDemo.client.luau").read_text())
 def test_reject_past_claim_collision(self):
  fail_mutation(lambda a,b,c,d,e:e["new_3d_source_ids"].append(e["previous_3d_source_ids"][0]))
 def test_reject_missing_far_signature(self):
  def f(a,b,c,d,e):
   ch=a["characters"]["TRCA-BE-045"]
   for p in ch["parts"]:
    if p["signature_tag"]=="bolt_mane":p["far"]=False
  fail_mutation(f)
 def test_reject_extra_unsafe_field(self):
  fail_mutation(lambda a,b,c,d,e:a["characters"]["TRCA-TR-099"]["parts"][0].update({"CanCollide":True}))
 def test_reject_canon_name_change(self):
  fail_mutation(lambda a,b,c,d,e:a["characters"]["TRCA-SP-054"].update({"name":"偽の魔法"}))
 def test_reject_wrong_source_atlas_sha(self):
  fail_mutation(lambda a,b,c,d,e:a.update({"source_atlas_sha256":"fake"}))
 def test_reject_seventh_unauthorized_id(self):
  fail_mutation(lambda a,b,c,d,e:e["new_3d_source_ids"].append("TRCA-BE-063"))
if __name__=="__main__":unittest.main()
