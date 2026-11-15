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

    def add_complete_engine_declarations(self, doc):
        # Synthetic declarations only; the checker cannot authenticate videos.
        doc["source_evidence"].update(
            source_lock="c" * 64,
            device_models=["Android handset", "PC Studio"],
            studio_recordings=["https://example.org/studio-capture", "https://example.org/studio-evidence"],
            competitor_timecodes=["https://example.org/gameplay?t=35"],
            official_build=dict(
                official_rc_head="a" * 40, run_id=123456, conclusion="success",
                run_url="https://github.com/example/project/actions/runs/123456",
                artifact_zip_bytes=243612, place_bytes=772452, source_count=82,
                place_sha256="d" * 64),
        )
        doc["source_evidence"]["core_scenarios"] = [
            dict(id=key, result="PASS", official_rc_head="a" * 40,
                 recording_url="https://example.org/studio-evidence", device=("Android handset" if key == "mobile_unobstructed_hud" else "PC Studio"),
                 reviewer="human-reviewer", measured_on="2026-11-15",
                 observed_effect="observed actual engine behavior",
                 **({"display_name": "暗殺者", "internal_role": "NINJA"}
                    if key == "assassin_stealth_and_ambush" else {}))
            for key in module.REQUIRED_SCENARIOS
        ]
        return doc

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
        o["candidate"]["base_rc"] = "a" * 40
        o["candidate"]["feature_ids"] = ["P0D-008", "P0D-011"]
        self.add_complete_engine_declarations(o)
        r = module.evaluate(o)
        self.assertEqual(15, r["core_scenarios_declared"])
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

    def test_all_fifteen_scenarios_are_required(self):
        o = copy.deepcopy(self.record)
        o["candidate"]["official_rc_head"] = "a" * 40
        self.add_complete_engine_declarations(o)
        o["source_evidence"]["core_scenarios"].pop()
        r = module.evaluate(o)
        self.assertIn("MISSING_ENGINE_PROOF:manual_ready_after_replay", r["problems"])
        self.assertEqual(14, r["core_scenarios_declared"])

    def test_old_ninja_alias_and_unpinned_source_fail(self):
        o = copy.deepcopy(self.record)
        o["candidate"]["official_rc_head"] = "a" * 40
        self.add_complete_engine_declarations(o)
        assassin = next(x for x in o["source_evidence"]["core_scenarios"]
                        if x["id"] == "assassin_stealth_and_ambush")
        assassin["display_name"] = "忍者"
        o["source_evidence"]["source_lock"] = "NOT_A_SHA256"
        r = module.evaluate(o)
        self.assertIn("INVALID_ENGINE_PROOF:assassin_stealth_and_ambush", r["problems"])
        self.assertIn("UNPINNED_SOURCE_LOCK_SHA256", r["problems"])

    def test_old_rc_proof_and_malformed_input_fail_closed(self):
        o = copy.deepcopy(self.record)
        o["candidate"]["official_rc_head"] = "a" * 40
        self.add_complete_engine_declarations(o)
        o["source_evidence"]["core_scenarios"][0]["official_rc_head"] = "b" * 40
        r = module.evaluate(o)
        self.assertIn("INVALID_ENGINE_PROOF:seven_jobs_select_and_dismiss", r["problems"])
        malformed = {"candidate": [], "operational_gates": "YES", "readiness": False}
        self.assertEqual("PRODUCT_NO_GO", module.evaluate(malformed)["decision"])
        self.assertEqual("PRODUCT_NO_GO", module.evaluate(None)["decision"])

    def test_false_string_and_missing_url_not_evidence(self):
        o = copy.deepcopy(self.record)
        entry = o["measurements"]["field_freedom"]
        entry.update(score=20, reviewer="owner", measured_on="2026-11-15",
                     benchmark_compared="false", evidence_urls=["https://example.org/capture"])
        self.assertIn("NO_VERIFIABLE_REVIEW:field_freedom", module.evaluate(o)["problems"])
        entry["benchmark_compared"] = True
        entry.pop("evidence_urls")
        self.assertEqual("PRODUCT_NO_GO", module.evaluate(o)["decision"])


    def test_foreign_build_receipt_and_unlisted_footage_are_rejected(self):
        o = copy.deepcopy(self.record)
        o["candidate"].update(official_rc_head="a" * 40, source_head="b" * 40)
        self.add_complete_engine_declarations(o)
        o["source_evidence"]["official_build"]["official_rc_head"] = "e" * 40
        o["source_evidence"]["core_scenarios"][0]["recording_url"] = "https://example.org/not-in-manifest"
        r = module.evaluate(o)
        self.assertIn("OFFICIAL_BUILD_HEAD_MISMATCH", r["problems"])
        self.assertIn("INVALID_ENGINE_PROOF:seven_jobs_select_and_dismiss", r["problems"])

    def test_mobile_hud_must_have_android_device(self):
        o = copy.deepcopy(self.record)
        o["candidate"]["official_rc_head"] = "a" * 40
        self.add_complete_engine_declarations(o)
        hud = next(x for x in o["source_evidence"]["core_scenarios"]
                   if x["id"] == "mobile_unobstructed_hud")
        hud["device"] = "PC Studio"
        r = module.evaluate(o)
        self.assertIn("INVALID_ENGINE_PROOF:mobile_unobstructed_hud", r["problems"])

    def test_malformed_feature_ids_and_fake_build_bytes_are_rejected(self):
        o = copy.deepcopy(self.record)
        o["candidate"]["official_rc_head"] = "a" * 40
        o["candidate"]["feature_ids"] = ["P0D-011", "P0D-011"]
        self.add_complete_engine_declarations(o)
        o["source_evidence"]["official_build"]["artifact_zip_bytes"] = True
        o["source_evidence"]["official_build"]["run_id"] = False
        r = module.evaluate(o)
        self.assertIn("INVALID_OR_MISSING_FEATURE_IDS", r["problems"])
        self.assertIn("OFFICIAL_BUILD_INVALID:artifact_zip_bytes", r["problems"])
        self.assertIn("OFFICIAL_BUILD_CI_UNVERIFIED", r["problems"])


if __name__ == "__main__":
    unittest.main()
