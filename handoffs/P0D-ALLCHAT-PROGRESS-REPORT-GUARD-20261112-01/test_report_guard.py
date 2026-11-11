import copy
import unittest

from report_guard import BadReport, render, validate


def sample():
    return {
        "game_id": "TRAP_RAIDERS", "work_id": "p0d-siege-v19", "date_jst": "2026-11-12 06:22 JST",
        "global": {
            "pct": None, "audit_status": "UNKNOWN_PENDING_GATE_AUDIT",
            "source_url": "https://github.com/kk051780/toy-wars-factory/issues/220",
            "previous_pct": None, "product_phase": "PRELAUNCH", "stage": "CHAT_ASSEMBLED",
            "studio_status": "NOT_FINAL_TESTED"
        },
        "lane": {"name": "CHAT-OPS-PROGRESS-GUARD", "accepted": 3, "total": 5,
                 "evidence_url": "https://github.com/kk051780/toy-wars-factory/issues/218",
                 "blockers": ["#220 official gate audit pending"], "next_acceptance": "Run isolated tests"}
    }


class ProgressGuardTest(unittest.TestCase):
    def reject(self, edit):
        p = sample()
        edit(p)
        with self.assertRaises(BadReport):
            validate(p)

    def test_default_reports_two_meters(self):
        s = render(sample())
        self.assertIn("UNKNOWN_PENDING_GATE_AUDIT", s)
        self.assertIn("60.0% (3/5)", s)
        self.assertIn("Studio", s)

    def test_lane_all_done_does_not_make_global_done(self):
        p = sample(); p["lane"].update(accepted=5, total=5)
        s = render(p)
        self.assertIn("自担当進捗率: 100.0%", s)
        self.assertIn("全体完成率（公式）: 未監査", s)

    def test_unknown_denominator_allowed(self):
        p = sample(); p["lane"].update(accepted=None, total=None)
        self.assertIn("受入分母未確定", render(p))

    def test_numeric_requires_full_audit(self):
        self.reject(lambda p: p["global"].update(pct=70))

    def test_numeric_rejects_bogus_source(self):
        self.reject(lambda p: p["global"].update(pct=70, audit_status="AUDITED", audit_points=70, audit_max_points=100,
                                                  last_rc_sha="a"*40, source_url="https://example.org/220#issuecomment-1"))

    def test_numeric_requires_rc_sha(self):
        self.reject(lambda p: p["global"].update(pct=70, audit_status="AUDITED", audit_points=70, audit_max_points=100,
                                                  source_url="https://github.com/kk051780/toy-wars-factory/issues/220#issuecomment-123"))

    def test_numeric_requires_points_match(self):
        self.reject(lambda p: p["global"].update(pct=70, audit_status="AUDITED", audit_points=75, audit_max_points=100,
                                                  last_rc_sha="a"*40, source_url="https://github.com/kk051780/toy-wars-factory/issues/220#issuecomment-123"))

    def test_numeric_valid_source_only_syntax_not_evidence(self):
        p = sample()
        p["global"].update(pct=70, audit_status="AUDITED", audit_points=70, audit_max_points=100,
                           last_rc_sha="a"*40, previous_pct=65,
                           source_url="https://github.com/kk051780/toy-wars-factory/issues/220#issuecomment-123")
        s = render(p)
        self.assertIn("70% (70/100", s)
        self.assertIn("+5pt", s)

    def test_no_fabricated_delta_when_unknown(self):
        self.reject(lambda p: p["global"].update(previous_pct=20))

    def test_invalid_numerator(self):
        self.reject(lambda p: p["lane"].update(accepted=6, total=5))

    def test_bad_denominator(self):
        self.reject(lambda p: p["lane"].update(accepted=0, total=0))

    def test_bool_not_int(self):
        self.reject(lambda p: p["lane"].update(accepted=True))

    def test_missing_lane_evidence(self):
        self.reject(lambda p: p["lane"].update(evidence_url=None))

    def test_wrong_game(self):
        self.reject(lambda p: p.update(game_id="TOY_WARS"))

    def test_wrong_phase(self):
        self.reject(lambda p: p["global"].update(product_phase="PRODUCTION_SUCCESS"))

    def test_missing_next(self):
        self.reject(lambda p: p["lane"].update(next_acceptance=""))

    def test_missing_blockers(self):
        self.reject(lambda p: p["lane"].pop("blockers"))

    def test_bad_studio_status(self):
        self.reject(lambda p: p["global"].update(studio_status="HUMAN_TEST_PASS"))

    def test_missing_source_url(self):
        self.reject(lambda p: p["global"].update(source_url=""))

    def test_unknown_with_different_issue(self):
        self.reject(lambda p: p["global"].update(source_url="https://github.com/kk051780/toy-wars-factory/issues/219"))


if __name__ == "__main__":
    unittest.main()
