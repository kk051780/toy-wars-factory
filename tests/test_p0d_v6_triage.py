import copy
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from p0d_v6_triage import evaluate

SHA = "a" * 40
BASE = {
    "schema": "P0D_V6_TRIAGE_V1", "base_rc_sha": SHA, "feature_id": "P0D-011",
    "mandatory_checks": {k: True for k in (
        "source_exact", "native_luau", "rojo", "same_head_ci",
        "no_authority_duplication", "rollback_verified", "original_claim_verified")},
    "findings": []
}
DEBT = {"id": "visual-1", "severity": "YELLOW", "domain": "cosmetic",
        "fb_id": "FB-015", "owner": "Original ART owner",
        "reproduction": "Tiny effect flash on attack",
        "impact": "Visual only; no collision change",
        "fix_trigger": "Next flagship studio art batch",
        "rollback": "Disable the optional effect switch", "feature_flag_off": True}


class TriageTest(unittest.TestCase):
    def test_green(self):
        self.assertEqual(evaluate(BASE)["lane"], "GREEN_REVIEW")

    def test_yellow_review_not_approval(self):
        p = copy.deepcopy(BASE); p["findings"] = [DEBT]
        r = evaluate(p)
        self.assertEqual(r["lane"], "YELLOW_TRACK_AND_REVIEW")
        self.assertFalse(r["official_rc_write_allowed"])
        self.assertFalse(r["product_pass"])

    def test_security_red_even_if_self_declared_yellow(self):
        p = copy.deepcopy(BASE); p["findings"] = [dict(DEBT, domain="security")]
        self.assertEqual(evaluate(p)["lane"], "HOLD_RED")

    def test_syntax_red(self):
        p = copy.deepcopy(BASE); p["findings"] = [dict(DEBT, domain="syntax")]
        self.assertEqual(evaluate(p)["lane"], "HOLD_RED")

    def test_missing_same_head_ci_red(self):
        p = copy.deepcopy(BASE); p["mandatory_checks"]["same_head_ci"] = False
        self.assertEqual(evaluate(p)["reason"], "HARD_GATE_MISSING")

    def test_missing_rollback_red(self):
        p = copy.deepcopy(BASE); p["findings"] = [dict(DEBT, rollback="")]
        self.assertEqual(evaluate(p)["lane"], "HOLD_RED")

    def test_active_core_yellow_red(self):
        p = copy.deepcopy(BASE); p["findings"] = [dict(DEBT, feature_flag_off=False)]
        self.assertEqual(evaluate(p)["lane"], "HOLD_RED")

    def test_active_noncore_yellow_review(self):
        p = copy.deepcopy(BASE)
        p["findings"] = [dict(DEBT, feature_flag_off=False, affects_core_gameplay=False)]
        self.assertEqual(evaluate(p)["lane"], "YELLOW_TRACK_AND_REVIEW")

    def test_unknown_severity_red(self):
        p = copy.deepcopy(BASE); p["findings"] = [dict(DEBT, severity="UNKNOWN")]
        self.assertEqual(evaluate(p)["lane"], "HOLD_RED")

    def test_duplicate_debt_red(self):
        p = copy.deepcopy(BASE); p["findings"] = [DEBT, DEBT]
        self.assertEqual(evaluate(p)["lane"], "HOLD_RED")

    def test_explicit_red(self):
        p = copy.deepcopy(BASE); p["findings"] = [dict(DEBT, severity="RED")]
        self.assertEqual(evaluate(p)["lane"], "HOLD_RED")

    def test_invalid_feature_red(self):
        p = copy.deepcopy(BASE); p["feature_id"] = "INVALID"
        self.assertEqual(evaluate(p)["lane"], "HOLD_RED")


if __name__ == "__main__":
    unittest.main()
