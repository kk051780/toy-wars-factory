"""Offline regression of the fail-closed trial evidence decision, NOT Studio QA."""
import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("audit", ROOT / "tools" / "assess_trial_result.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def valid_candidate(name="B42_FIRST90"):
    if name == "B42_FIRST90":
        filename = "TRIAL_RESULT_TEMPLATE.json"
    else:
        filename = "A40_COMPARISON_TRIAL_TEMPLATE.json"
    d = json.loads((ROOT / filename).read_text(encoding="utf-8"))
    d["candidate"]["place_sha256"] = "a" * 64
    d["observed"].update(owner_tested="PASS", tested_at_jst="2026-11-13T21:40:00+09:00",
                         actual_clients=2, logs_or_screenshots=["actual-manual-qa-log.txt"],
                         first15="OBSERVED", first35="OBSERVED",
                         first60="OBSERVED", first90="OBSERVED")
    d["hard_gates"] = {key: "PASS" for key in audit.GATES}
    d["scores_out_of_5"] = {key: 4 for key in audit.SCORES}
    d["owner_fun_decision"] = "FUN_GO"
    return d


class ReportTests(unittest.TestCase):
    def test_unfilled_template_b42_is_blocked(self):
        p = json.loads((ROOT / "TRIAL_RESULT_TEMPLATE.json").read_text(encoding="utf-8"))
        self.assertEqual(audit.evaluate(p)["status"], "WAITING_EVIDENCE")

    def test_unfilled_template_a40_is_blocked(self):
        p = json.loads((ROOT / "A40_COMPARISON_TRIAL_TEMPLATE.json").read_text(encoding="utf-8"))
        self.assertEqual(audit.evaluate(p)["status"], "WAITING_EVIDENCE")

    def test_self_report_sufficient_only_for_review_candidate(self):
        r = audit.evaluate(valid_candidate())
        self.assertEqual(r["status"], "PRODUCT_DRI_REVIEW_CANDIDATE")
        self.assertFalse(r["studio_verified_by_tool"])
        self.assertFalse(r["official_rc_adopted"])

    def test_a40_still_requires_manual_selection(self):
        r = audit.evaluate(valid_candidate("A40_V6"))
        self.assertEqual(r["status"], "PRODUCT_DRI_REVIEW_CANDIDATE")

    def test_single_client_cannot_pass(self):
        p = valid_candidate()
        p["observed"]["actual_clients"] = 1
        self.assertEqual(audit.evaluate(p)["status"], "WAITING_EVIDENCE")

    def test_hard_gate_fail_overrides_high_fun(self):
        p = valid_candidate()
        p["hard_gates"]["terrain_traversal"] = "FAIL"
        self.assertEqual(audit.evaluate(p)["status"], "REVISE_BLOCKED")

    def test_missing_android_proof_cannot_pass(self):
        p = valid_candidate()
        p["hard_gates"]["android_actual"] = "NOT_TESTED"
        self.assertEqual(audit.evaluate(p)["status"], "WAITING_EVIDENCE")

    def test_missing_human_log_cannot_pass(self):
        p = valid_candidate()
        p["observed"]["logs_or_screenshots"] = []
        self.assertEqual(audit.evaluate(p)["status"], "WAITING_EVIDENCE")

    def test_incorrect_sha_rejected(self):
        p = valid_candidate()
        p["candidate"]["source_sha"] = "0" * 40
        self.assertEqual(audit.evaluate(p)["status"], "INVALID_INPUT")

    def test_no_auto_official_adoption(self):
        p = valid_candidate()
        p["official_rc_integrated"] = True
        self.assertEqual(audit.evaluate(p)["status"], "INVALID_INPUT")

    def test_invalid_place_hash_waits(self):
        p = valid_candidate()
        p["candidate"]["place_sha256"] = "not-a-hash"
        self.assertEqual(audit.evaluate(p)["status"], "WAITING_EVIDENCE")

    def test_average_below_four_requires_revision(self):
        p = valid_candidate()
        p["scores_out_of_5"]["distinctive_play_60"] = 0
        self.assertEqual(audit.evaluate(p)["status"], "REVISE_FUN")

    def test_rematch_score_below_four_requires_revision(self):
        p = valid_candidate()
        p["scores_out_of_5"]["rematch_desire"] = 3
        self.assertEqual(audit.evaluate(p)["status"], "REVISE_FUN")

    def test_boolean_score_not_counted(self):
        p = valid_candidate()
        p["scores_out_of_5"]["rematch_desire"] = True
        self.assertEqual(audit.evaluate(p)["status"], "WAITING_EVIDENCE")

    def test_unknown_candidate_rejected(self):
        p = valid_candidate()
        p["candidate"]["id"] = "B42_RICH45_UNSELECTED"
        self.assertEqual(audit.evaluate(p)["status"], "INVALID_INPUT")


if __name__ == "__main__":
    unittest.main()
