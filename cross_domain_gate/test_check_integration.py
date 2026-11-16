"""Synthetic validator unit tests only. NEVER gameplay/Studio/Android PASS evidence."""
import copy
import unittest
from cross_domain_gate.check_integration import CONTRACTS, check

RC = "a" * 40
PLACE = "b" * 64

def synthetic_report():
    return {"cases": {
        key: {
            "domains": sorted(contract["domains"]),
            "status": "PASS",
            "rc_sha": RC,
            "studio_place_sha256": PLACE,
            "device": "Android" if key == "GQ06" else "Studio",
            "observed_at": "2026-11-16T12:00:00+09:00",
            "evidence_url": "https://example.org/SYNTHETIC-UNIT-TEST-ONLY",
            "assertions": {name: True for name in contract["checks"]},
        } for key, contract in CONTRACTS.items()
    }}

class CrossDomainContractTest(unittest.TestCase):
    def assert_reject(self, report, fragment):
        errors = check(report, RC)
        self.assertTrue(any(fragment in issue for issue in errors), errors)

    def test_synthetic_example_passes_validator_only(self):
        self.assertEqual(check(synthetic_report(), RC), [])

    def test_missing_case_rejected(self):
        report = synthetic_report()
        del report["cases"]["GQ05"]
        self.assert_reject(report, "GQ05: missing case")

    def test_fail_case_is_not_ready(self):
        report = synthetic_report()
        report["cases"]["GQ03"]["status"] = "FAIL"
        self.assert_reject(report, "PRODUCT_NO_GO")

    def test_unrun_case_is_not_ready(self):
        report = synthetic_report()
        report["cases"]["GQ01"]["status"] = "NOT_RUN"
        self.assert_reject(report, "PRODUCT_NO_GO")

    def test_assertion_false_rejected(self):
        report = synthetic_report()
        report["cases"]["GQ02"]["assertions"]["multi_target_real_damage"] = False
        self.assert_reject(report, "behavior not verified")

    def test_assertion_absent_rejected(self):
        report = synthetic_report()
        del report["cases"]["GQ01"]["assertions"]["wall_pickup_blocked"]
        self.assert_reject(report, "missing or extra behavior assertions")

    def test_wrong_domains_rejected(self):
        report = synthetic_report()
        report["cases"]["GQ05"]["domains"] = ["lobby"]
        self.assert_reject(report, "domain contract mismatch")

    def test_duplicate_domains_rejected(self):
        report = synthetic_report()
        report["cases"]["GQ05"]["domains"].append("lobby")
        self.assert_reject(report, "domain contract mismatch")

    def test_invalid_cases_type_rejected(self):
        self.assertEqual(check({"cases": []}), ["cases must be object"])

    def test_invalid_domains_type_rejected(self):
        report = synthetic_report()
        report["cases"]["GQ02"]["domains"] = {"battle": True}
        self.assert_reject(report, "domain contract mismatch")

    def test_cross_case_rc_mismatch_rejected(self):
        report = synthetic_report()
        report["cases"]["GQ04"]["rc_sha"] = "c" * 40
        self.assert_reject(report, "cross-case RC SHA mismatch")

    def test_pinned_head_mismatch_rejected(self):
        report = synthetic_report()
        self.assertTrue(any("RC HEAD differs" in x for x in check(report, "c" * 40)))

    def test_cross_case_place_mismatch_rejected(self):
        report = synthetic_report()
        report["cases"]["GQ04"]["studio_place_sha256"] = "d" * 64
        self.assert_reject(report, "cross-case Place SHA mismatch")

    def test_android_only_rejected_for_gq06(self):
        report = synthetic_report()
        report["cases"]["GQ06"]["device"] = "Studio"
        self.assert_reject(report, "Android evidence required")

    def test_missing_time_zone_rejected(self):
        report = synthetic_report()
        report["cases"]["GQ02"]["observed_at"] = "2026-11-16T12:00:00"
        self.assert_reject(report, "timezone ISO8601")

    def test_untrusted_url_scheme_rejected(self):
        report = synthetic_report()
        report["cases"]["GQ02"]["evidence_url"] = "file:///tmp/fake"
        self.assert_reject(report, "must be https")

    def test_missing_place_checksum_rejected(self):
        report = synthetic_report()
        report["cases"]["GQ04"]["studio_place_sha256"] = ""
        self.assert_reject(report, "invalid studio_place_sha256")

if __name__ == "__main__":
    unittest.main()
