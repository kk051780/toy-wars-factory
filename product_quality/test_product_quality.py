import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("product_quality_check", ROOT / "check_product_quality.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ProductQualityTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((ROOT / "CANDIDATE_TEMPLATE.json").read_text(encoding="utf-8"))

    def test_template_fails_closed(self):
        r = module.evaluate(self.record)
        self.assertEqual("PRODUCT_NO_GO", r["decision"])
        self.assertIsNone(r["total_score"])
        self.assertIn("PRODUCT_SCORE_UNKNOWN", r["problems"])

    def test_all_measurements_need_manual_evidence_and_owner(self):
        o = copy.deepcopy(self.record)
        o["major_blockers"] = []
        o["candidate"]["official_rc_head"] = "a" * 40
        o["candidate"]["source_head"] = "b" * 40
        for k, w in module.WEIGHTS.items():
            o["measurements"][k].update(score=w, reviewer="named-person", evidence_urls=["https://example.org/real-capture"], measured_on="2026-11-15", benchmark_compared=True)
        for k in o["readiness"]:
            o["readiness"][k] = True
        r = module.evaluate(o)
        self.assertEqual(100, r["total_score"])
        self.assertEqual("PRODUCT_NO_GO", r["decision"])
        self.assertIn("MANDATORY_GATE_MISSING:owner_accepted", r["problems"])

    def test_can_be_reviewable_only_with_complete_declarations(self):
        o = copy.deepcopy(self.record)
        o["major_blockers"] = []
        o["candidate"]["official_rc_head"] = "a" * 40
        o["candidate"]["source_head"] = "b" * 40
        for k, w in module.WEIGHTS.items():
            o["measurements"][k].update(score=w, reviewer="named-person", evidence_urls=["https://example.org/test-report"], measured_on="2026-11-15", benchmark_compared=True)
        for key in o["readiness"]:
            o["readiness"][key] = True
        for key in o["operational_gates"]:
            o["operational_gates"][key] = True
        r = module.evaluate(o)
        self.assertEqual("PRODUCT_GO_REVIEWABLE", r["decision"])
        # Even this state is *reviewable* and does not publish / modify canonical RC.

    def test_core_failure_even_when_total_high(self):
        o = copy.deepcopy(self.record)
        o["major_blockers"] = []
        o["candidate"]["official_rc_head"] = "a" * 40
        o["candidate"]["source_head"] = "b" * 40
        for k, w in module.WEIGHTS.items():
            o["measurements"][k].update(score=w, reviewer="named-person", evidence_urls=["https://example.org/report"], measured_on="2026-11-15", benchmark_compared=True)
        o["measurements"]["field_freedom"]["score"] = 10
        for key in o["readiness"]:
            o["readiness"][key] = True
        for key in o["operational_gates"]:
            o["operational_gates"][key] = True
        r = module.evaluate(o)
        self.assertGreaterEqual(r["total_score"], 80)
        self.assertEqual("PRODUCT_NO_GO", r["decision"])
        self.assertIn("CORE_BELOW_70_PERCENT:field_freedom", r["problems"])

if __name__ == "__main__":
    unittest.main()
