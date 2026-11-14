"""Tests for benchmark provenance and mobile-vs-PC visual thresholds."""
import copy
import json
import unittest
from pathlib import Path
import check_reference_benchmarks as bench

ROOT=Path(__file__).resolve().parent
BASE=json.loads((ROOT/"REFERENCE_BENCHMARKS_V2.json").read_text("utf8"))

class Benchmarks(unittest.TestCase):
    def test_four_owner_clips_are_not_claimed_watched(self):
        r=bench.audit_registry(BASE)
        self.assertTrue(r["registry_valid"],r["errors"])
        self.assertEqual(r["owner_video_count"],4)
        self.assertEqual(r["full_video_reviewed"],0)
    def test_tampered_video_watched_without_proof(self):
        x=copy.deepcopy(BASE)
        x["user_referenced_clips"][0]["full_video_watched"]=True
        self.assertFalse(bench.audit_registry(x)["registry_valid"])
    def test_target_must_stay_45(self):
        x=copy.deepcopy(BASE)
        x["overall_grade_goal"]=4
        self.assertIn("ART_TARGET_BELOW_4_5",bench.audit_registry(x)["errors"])
    def test_blank_human_review_rejected(self):
        self.assertEqual(bench.audit_human_review(BASE,None)["review_status"],"MISSING")
    def test_pc45_android4_are_distinct_thresholds(self):
        script=(ROOT/"check_reference_benchmarks.py").read_text("utf8")
        self.assertIn('minimum = 4.5 if device == "pc" else 4.0',script)
        self.assertIn('device == "pc" and p0d < ref - 0.25',script)
    def test_catalog_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(x["weight"] for x in BASE["grade_dimensions"]),1)

if __name__=="__main__":
    unittest.main()
