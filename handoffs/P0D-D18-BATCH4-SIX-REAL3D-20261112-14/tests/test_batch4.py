#!/usr/bin/env python3
"""D18 Batch4 original six tactical source-only models: strict validation and negative mutations."""
import copy
import json
import unittest
import importlib.util
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("generator", ROOT / "tools/generate_catalog.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
data = json.loads((ROOT / "data/six_pilot_geometry.json").read_text(encoding="utf-8"))
rules = json.loads((ROOT / "data/archetype_rules.json").read_text(encoding="utf-8"))
registry = json.loads((ROOT / "data/flagship72_registry.json").read_text(encoding="utf-8"))
queue = json.loads((ROOT / "data/next54_source_queue.json").read_text(encoding="utf-8"))
claims = json.loads((ROOT / "data/batch_claims.json").read_text(encoding="utf-8"))
IDS = {"TRCA-BE-036", "TRCA-SP-009", "TRCA-VE-009",
       "TRCA-WE-009", "TRCA-ZO-018", "TRCA-TR-027"}

def reject(mutator):
    a,b,c,d,e = map(copy.deepcopy, (data,rules,registry,queue,claims))
    mutator(a,b,c,d,e)
    with unittest.TestCase().assertRaises(ValueError):
        module.validate(a,b,c,d,e)

class D18Batch4(unittest.TestCase):
    def test_source_generation_and_six_ids(self):
        self.assertEqual(set(data["characters"]), IDS)
        self.assertTrue(module.validate(data,rules,registry,queue,claims))
        self.assertEqual(module.generate(),
                         (ROOT / "src/D18BatchCatalog.luau").read_text(encoding="utf-8"))
    def test_silhouettes_far_retain_tags(self):
        for c in data["characters"].values():
            far=[p for p in c["parts"] if p["far"]]
            self.assertLessEqual(len(c["parts"]),24)
            self.assertLessEqual(len(far),18)
            self.assertEqual(len(c["signature_tags"]),3)
            self.assertTrue(set(c["signature_tags"])<=set(x["signature_tag"] for x in far))
            self.assertEqual(set(c["pose_offsets"]),{"idle","tap","win","loss"})
    def test_72_exact_and_safe_budget(self):
        self.assertEqual(len(claims["previous_3d_source_ids"]),30)
        self.assertEqual(len(claims["new_3d_source_ids"]),6)
        self.assertEqual(queue["remaining_source_not_started_count"],36)
        self.assertEqual(len(registry["entries"]),72)
        src=(ROOT / "src/D18BatchFactory.luau").read_text()
        for required in ('not parent:IsA("WorldModel")','p.CanCollide = false',
            'p.CanQuery = false','p.CanTouch = false','Factory.Destroy','Factory.SetPose'):
            self.assertIn(required,src)
        self.assertIn("local ENABLED = false",
            (ROOT / "src/DisabledPilotDemo.client.luau").read_text())
    def test_reject_duplicate_old_character(self):
        reject(lambda a,b,c,d,e: e["new_3d_source_ids"].append(e["previous_3d_source_ids"][0]))
    def test_reject_missing_far_signature(self):
        def f(a,b,c,d,e):
            ch=a["characters"]["TRCA-BE-036"]
            for p in ch["parts"]:
                if p["signature_tag"] == ch["signature_tags"][0]: p["far"]=False
        reject(f)
    def test_reject_unclaimed_seventh_character(self):
        reject(lambda a,b,c,d,e: e["new_3d_source_ids"].append("TRCA-BE-045"))
    def test_reject_malicious_collision_in_part(self):
        reject(lambda a,b,c,d,e: a["characters"]["TRCA-TR-027"]["parts"][0].update({"CanCollide":True}))
    def test_reject_wrong_atlas(self):
        reject(lambda a,b,c,d,e: a.update({"source_atlas_sha256":"forged"}))
    def test_reject_oversize_part(self):
        reject(lambda a,b,c,d,e: a["characters"]["TRCA-VE-009"]["parts"][0].update({"size":[40,1,1]}))
    def test_reject_unsafe_pose(self):
        reject(lambda a,b,c,d,e: a["characters"]["TRCA-WE-009"]["pose_offsets"]["win"]["gem"].update({"dy":10}))

if __name__ == "__main__":
    unittest.main()
