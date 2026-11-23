"""Negative and positive contract tests for the REAL69 art receipt gate."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from quality_gameplay.gq470_art_pr_provenance_20261121.guard import (
    CANONICAL_BRANCH, CANONICAL_REF, LEGACY_REF, verify_receipt,
)

RC = "a" * 40
MERGE = "b" * 40
AUTHOR = "c" * 40
OLD = "d" * 40
NUMBER = 977


def pr_case():
    return (
        {"build_head": MERGE, "canonical_build": False},
        {"GITHUB_SHA": MERGE, "GITHUB_REF": f"refs/pull/{NUMBER}/merge", "GITHUB_EVENT_NAME": "pull_request"},
        {"number": NUMBER, "pull_request": {
            "base": {"ref": CANONICAL_BRANCH, "sha": RC},
            "head": {"sha": AUTHOR}}},
        RC,
    )


class ReceiptProvenanceTest(unittest.TestCase):
    def test_live_pr_synthetic_merge_stays_nonformal(self):
        self.assertEqual(verify_receipt(*pr_case()), "PR_CANDIDATE")

    def test_actual_canonical_push_only(self):
        receipt = {"build_head": RC, "canonical_build": True}
        env = {"GITHUB_SHA": RC, "GITHUB_REF": CANONICAL_REF, "GITHUB_EVENT_NAME": "push"}
        self.assertEqual(verify_receipt(receipt, env, {}, RC), "OFFICIAL")

    def test_canonical_dispatch_only_on_live_head(self):
        receipt = {"build_head": RC, "canonical_build": True}
        env = {"GITHUB_SHA": RC, "GITHUB_REF": CANONICAL_REF, "GITHUB_EVENT_NAME": "workflow_dispatch"}
        self.assertEqual(verify_receipt(receipt, env, {}, RC), "OFFICIAL")
        with self.assertRaisesRegex(ValueError, "RED_FORMAL_HEAD_MOVED"):
            verify_receipt(receipt, env, {}, OLD)

    def test_formal_flag_cannot_be_forged_on_pr(self):
        receipt, env, event, live = pr_case()
        receipt["canonical_build"] = True
        with self.assertRaisesRegex(ValueError, "RED_FALSE_FORMAL_BUILD_CLASSIFICATION"):
            verify_receipt(receipt, env, event, live)

    def test_formal_receipt_cannot_omit_truthy_boolean(self):
        receipt, env, event, live = pr_case()
        receipt["canonical_build"] = "false"
        with self.assertRaisesRegex(ValueError, "RED_CANONICAL_FLAG_NOT_BOOLEAN"):
            verify_receipt(receipt, env, event, live)

    def test_stale_pr_base_is_red(self):
        receipt, env, event, live = pr_case()
        with self.assertRaisesRegex(ValueError, "RED_PR_BASE_NOT_LIVE_FORMAL_HEAD"):
            verify_receipt(receipt, env, event, OLD)

    def test_pr_branch_mismatch_is_red(self):
        receipt, env, event, live = pr_case()
        event["pull_request"]["base"]["ref"] = "main"
        with self.assertRaisesRegex(ValueError, "RED_WRONG_PR_TARGET_BRANCH"):
            verify_receipt(receipt, env, event, live)

    def test_pr_merge_ref_mismatch_is_red(self):
        receipt, env, event, live = pr_case()
        env["GITHUB_REF"] = "refs/heads/feature"
        with self.assertRaisesRegex(ValueError, "RED_NOT_ACTUAL_PR_MERGE_REF"):
            verify_receipt(receipt, env, event, live)

    def test_no_candidate_head_shortcut(self):
        receipt, env, event, live = pr_case()
        receipt["build_head"] = AUTHOR
        with self.assertRaisesRegex(ValueError, "RED_RECEIPT_NOT_SAME_CHECKOUT_HEAD"):
            verify_receipt(receipt, env, event, live)

    def test_no_missing_pr_head(self):
        receipt, env, event, live = pr_case()
        event["pull_request"]["head"]["sha"] = ""
        with self.assertRaisesRegex(ValueError, "RED_BAD_PR_HEAD_SHA"):
            verify_receipt(receipt, env, event, live)

    def test_pr_number_must_match_merge_ref(self):
        receipt, env, event, live = pr_case()
        event["number"] = NUMBER + 1
        with self.assertRaisesRegex(ValueError, "RED_NOT_ACTUAL_PR_MERGE_REF"):
            verify_receipt(receipt, env, event, live)

    def test_unknown_source_not_silently_green(self):
        receipt, env, event, live = pr_case()
        env["GITHUB_EVENT_NAME"] = "schedule"
        with self.assertRaisesRegex(ValueError, "RED_UNSUPPORTED_RUN_PROVENANCE"):
            verify_receipt(receipt, env, event, live)

    def test_legacy_branch_only_original_pinned_official(self):
        receipt = {"build_head": AUTHOR, "canonical_build": False}
        env = {
            "GITHUB_SHA": AUTHOR, "GITHUB_REF": LEGACY_REF,
            "GITHUB_EVENT_NAME": "push", "EXPECTED_OFFICIAL": RC,
        }
        self.assertEqual(verify_receipt(receipt, env, {}, RC), "LEGACY_CANDIDATE")
        with self.assertRaisesRegex(ValueError, "RED_LEGACY_AUTHOR_OR_FORMAL_DRIFT"):
            verify_receipt(receipt, env, {}, OLD)

    def test_bad_sha_provenance_fails(self):
        receipt, env, event, live = pr_case()
        env["GITHUB_SHA"] = "short"
        with self.assertRaisesRegex(ValueError, "RED_BAD_RUN_SHA"):
            verify_receipt(receipt, env, event, live)


if __name__ == "__main__":
    unittest.main()
