"""Fail-closed static RC preflight: no misleading Android/FUN/owner PASS."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_live_intake import static_release_preflight_issues


def report():
    return {
        "decision": "SOURCE_REVIEW_READY_ONLY",
        "product_go": False,
        "runtime_activation": {
            "source_guard_inspection": "COMPLETE",
            "guard_count": 0,
            "production_runtime": "NOT_VERIFIED_FAIL_CLOSED",
        },
        "full26_runtime_activation": {
            "static_source_read": "PASS",
            "selected_script_count": 26,
            "guard_count": 0,
            "gameplay_server_activation": "NOT_VERIFIED_REQUIRES_REAL_NONSTUDIO_2CLIENT",
            "art_nonstudio_visual_activation": "NOT_VERIFIED_REQUIRES_ANDROID_VISUAL_QA",
            "product_go": False,
        },
    }


class StaticReleasePreflightTest(unittest.TestCase):
    def test_guard_free_source_still_product_no_go(self):
        r=report()
        self.assertEqual(static_release_preflight_issues(r),[])
        self.assertFalse(r["product_go"])
        self.assertFalse(r["full26_runtime_activation"]["product_go"])

    def test_art4_studio_guards_block_even_if_old5_are_clean(self):
        r=report()
        r["full26_runtime_activation"]["guard_count"]=4
        r["full26_runtime_activation"]["art_nonstudio_visual_activation"]="STUDIO_ONLY_VISUALS_DETECTED"
        self.assertTrue(any("selected_26_source_studio" in x for x in static_release_preflight_issues(r)))

    def test_stale_samehead_ci_must_block(self):
        r=report()
        r["decision"]="SOURCE_RECONCILIATION_REQUIRED"
        self.assertIn("latest26_source_or_samehead_ci_not_ready",static_release_preflight_issues(r))

    def test_missing_full26_evidence_must_block(self):
        r=report()
        del r["full26_runtime_activation"]
        self.assertIn("actual_26_source_runtime_scan_missing",static_release_preflight_issues(r))

    def test_game_host_guard_blocks(self):
        r=report()
        r["full26_runtime_activation"]["gameplay_server_activation"]="BLOCKED_PREVIEW_HOST"
        self.assertIn("nonstudio_gameplay_activation_blocked_or_unknown",
                      static_release_preflight_issues(r))

    def test_unavailable_report_is_fail_closed(self):
        self.assertGreater(len(static_release_preflight_issues(None)),0)


if __name__=="__main__":
    unittest.main()
