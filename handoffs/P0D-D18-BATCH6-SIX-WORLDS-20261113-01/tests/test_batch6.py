#!/usr/bin/env python3
"""D18 Batch6 actual source and adversarial validation; do not call Roblox Studio tested."""
import copy
import importlib.util
import json
import pathlib
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("generator",ROOT/"tools/generate_catalog.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
PATHS=("data/six_pilot_geometry.json","data/archetype_rules.json","data/flagship72_registry.json",
       "data/next54_source_queue.json","data/batch_claims.json")
IDS=["TRCA-BE-099","TRCA-SP-108","TRCA-TR-072","TRCA-VE-054","TRCA-WE-018","TRCA-ZO-099"]
def docs():
    return [json.loads((ROOT/p).read_text(encoding="utf-8")) for p in PATHS]
def reject(mutator):
    a,b,c,d,e=map(copy.deepcopy,docs())
    mutator(a,b,c,d,e)
    with unittest.TestCase().assertRaises(ValueError):
        mod.validate(a,b,c,d,e)
class Batch6(unittest.TestCase):
    def test_canon_and_exact_six(self):
        data,rules,reg,queue,claims=docs()
        self.assertEqual(set(data["characters"]),set(IDS))
        self.assertEqual(set(claims["new_3d_source_ids"]),set(IDS))
        self.assertEqual(len(claims["previous_3d_source_ids"]),42)
        self.assertEqual(claims["estimated_total_source_after_batch"],48)
        self.assertEqual(queue["remaining_source_not_started_count"],24)
        self.assertTrue(mod.validate(data,rules,reg,queue,claims))
    def test_generated_luau_byte_exact(self):
        self.assertEqual(mod.generate(),(ROOT/"src/D18BatchCatalog.luau").read_text(encoding="utf-8"))
    def test_far_retains_all_unique_signature_roles(self):
        data,*_=docs()
        for ch in data["characters"].values():
            far=[p for p in ch["parts"] if p["far"]]
            self.assertEqual(len(ch["signature_tags"]),3)
            self.assertLessEqual(len(ch["parts"]),24)
            self.assertLessEqual(len(far),18)
            self.assertTrue(set(ch["signature_tags"]) <= set(p["signature_tag"] for p in far))
            self.assertEqual(set(ch["pose_offsets"]),{"idle","tap","win","loss"})
    def test_safe_worldmodel_factory_and_off_demo(self):
        luau=(ROOT/"src/D18BatchFactory.luau").read_text(encoding="utf-8")
        for key in ('not parent:IsA("WorldModel")','p.Anchored = true',
                    'p.CanCollide = false','p.CanQuery = false','p.CanTouch = false',
                    'MAX_ACTIVE = 12','Factory.SetLod','Factory.SetPose','Factory.Destroy'):
            self.assertIn(key,luau)
        self.assertIn("local ENABLED = false",(ROOT/"src/DisabledPilotDemo.client.luau").read_text(encoding="utf-8"))
    def test_reject_old_source_duplication(self):
        reject(lambda a,b,c,d,e:e["new_3d_source_ids"].append(e["previous_3d_source_ids"][0]))
    def test_reject_far_silhouette_erasure(self):
        def change(a,b,c,d,e):
            ch=a["characters"]["TRCA-SP-108"]
            for p in ch["parts"]:
                if p["signature_tag"]=="seven_bells":p["far"]=False
        reject(change)
    def test_reject_extra_collision_field(self):
        reject(lambda a,b,c,d,e:a["characters"]["TRCA-TR-072"]["parts"][0].update({"CanCollide":True}))
    def test_reject_fake_original_name(self):
        reject(lambda a,b,c,d,e:a["characters"]["TRCA-BE-099"].update({"name":"fake"}))
    def test_reject_source_atlas_forgery(self):
        reject(lambda a,b,c,d,e:a.update({"source_atlas_sha256":"forged"}))
    def test_reject_too_large_geometry(self):
        reject(lambda a,b,c,d,e:a["characters"]["TRCA-VE-054"]["parts"][0].update({"size":[99,1,1]}))
    def test_reject_extra_unclaimed_seventh_model(self):
        reject(lambda a,b,c,d,e:e["new_3d_source_ids"].append("TRCA-BE-063"))
    def test_reject_puppet_pose_outside_safe_range(self):
        def change(a,b,c,d,e):
            a["characters"]["TRCA-ZO-099"]["pose_offsets"]["tap"]["hat"]["rz"]=99
        reject(change)
if __name__=="__main__":unittest.main()
