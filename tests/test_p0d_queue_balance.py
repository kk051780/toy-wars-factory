"""Offline, no-network contract tests for p0d_queue_balance.py."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from p0d_queue_balance import InvalidSnapshot, balance

SHA = "a" * 40
HEAD = "b" * 40


def inbox(n=0):
    selected = [
        {"pr": 100 + i, "head": HEAD, "features": [f"READY_{i:02d}"],
         "status": "READY_FOR_SOLE_WRITER_REVIEW"}
        for i in range(n)
    ]
    return {"schema": "P0D_TWO_LANES_V1", "official_head": SHA,
            "selected": selected, "ready_count": n}


def catalog():
    return {"rows": [
        {"id": "P0D-001", "stage": "RC", "name": "already built", "group": "基本", "release": "S1"},
        {"id": "P0D-018", "stage": "SOURCE", "name": "Capture", "group": "戦闘", "release": "S2+"},
        {"id": "P0D-017", "stage": "SOURCE", "name": "Elite", "group": "戦闘", "release": "S2+"},
        {"id": "P0D-040", "stage": "SOURCE", "name": "XP", "group": "収集育成", "release": "S2+"},
        {"id": "P0D-050", "stage": "IDEA", "name": "More", "group": "世界", "release": "S2+"},
    ]}


class QueueBalanceTest(unittest.TestCase):
    def test_ready_zero_fills_two_source_targets(self):
        r = balance(inbox(0), catalog())
        self.assertEqual(r["queue_state"], "QUEUE_RED")
        self.assertEqual(r["target_work_split_pct"], {"A_PREP": 70, "B_INTEGRATOR": 30})
        self.assertEqual(r["a_suggested_feature_ids"], ["P0D-018", "P0D-017"])
        self.assertEqual(r["b_ready_prs"], [])
        self.assertTrue(r["no_auto_merge"])
        self.assertEqual(r["human_studio_fun"], "NOT_INFERRED")

    def test_low_ready_keeps_parallel_prep(self):
        r = balance(inbox(1), catalog())
        self.assertEqual(r["queue_state"], "QUEUE_LOW")
        self.assertEqual(r["target_work_split_pct"], {"A_PREP": 60, "B_INTEGRATOR": 40})
        self.assertEqual(len(r["a_suggested_feature_ids"]), 2)
        self.assertEqual(len(r["b_ready_prs"]), 1)

    def test_balanced_ready_only_one_prep_target(self):
        for n in (2, 3):
            with self.subTest(n=n):
                r = balance(inbox(n), catalog())
                self.assertEqual(r["queue_state"], "QUEUE_BALANCED")
                self.assertEqual(r["target_work_split_pct"], {"A_PREP": 50, "B_INTEGRATOR": 50})
                self.assertEqual(r["a_suggested_feature_ids"], ["P0D-018"])

    def test_stocked_ready_prioritizes_integration(self):
        r = balance(inbox(4), catalog())
        self.assertEqual(r["queue_state"], "QUEUE_STOCKED")
        self.assertEqual(r["target_work_split_pct"], {"A_PREP": 30, "B_INTEGRATOR": 70})
        self.assertEqual(len(r["b_ready_prs"]), 4)

    def test_external_claim_excludes_in_progress(self):
        r = balance(inbox(0), catalog(), ["P0D-018", "P0D-017"])
        self.assertEqual(r["a_suggested_feature_ids"], ["P0D-040"])
        self.assertEqual(r["blocked_by_external_claims"], ["P0D-017", "P0D-018"])

    def test_already_ready_feature_excluded(self):
        q = inbox(1)
        q["selected"][0]["features"] = ["P0D-018"]
        self.assertEqual(balance(q, catalog())["a_suggested_feature_ids"],
                         ["P0D-017", "P0D-040"])

    def test_idea_only_when_source_exhausted(self):
        c = catalog()
        for row in c["rows"]:
            if row["stage"] == "SOURCE":
                row["stage"] = "RC"
        r = balance(inbox(0), c)
        self.assertEqual(r["a_target_stage"], "IDEA_TO_REAL_SOURCE")
        self.assertEqual(r["a_suggested_feature_ids"], ["P0D-050"])

    def test_invalid_queue_and_mismatch_fail_closed(self):
        q = inbox(0)
        q["official_head"] = "not-a-sha"
        with self.assertRaises(InvalidSnapshot):
            balance(q, catalog())
        q = inbox(0)
        q["ready_count"] = 1
        with self.assertRaises(InvalidSnapshot):
            balance(q, catalog())
        q = inbox(1)
        q["selected"][0]["status"] = "DRAFT"
        with self.assertRaises(InvalidSnapshot):
            balance(q, catalog())

    def test_duplicate_ready_feature_fails(self):
        q = inbox(2)
        q["selected"][0]["features"] = ["P0D-018"]
        q["selected"][1]["features"] = ["P0D-018"]
        with self.assertRaises(InvalidSnapshot):
            balance(q, catalog())


    def test_workflow_regenerates_plan_on_all_official_rc_and_pr_updates(self):
        workflow = (Path(__file__).resolve().parents[1] /
                    ".github" / "workflows" / "p0d-two-lane-intake.yml").read_text(encoding="utf-8")
        self.assertIn("      - rc/p0d-s1-kids-rc01", workflow)
        self.assertIn("  pull_request:", workflow)
        self.assertIn("    types: [opened, synchronize, reopened, ready_for_review, edited]", workflow)
        self.assertIn("  workflow_dispatch: {}", workflow)
        self.assertNotIn("    paths:", workflow,
                         "path-filtered push would miss normal official RC feature adoption")
        self.assertNotIn("if: github.event_name == 'push'", workflow,
                         "PR-synced candidate replenishment must also generate a plan")
        self.assertIn("--out /tmp/p0d_two_lane/P0D_BALANCE_PLAN.json", workflow)
        self.assertIn("path: /tmp/p0d_two_lane/", workflow)
        self.assertIn("ref: rc/p0d-s1-kids-rc01", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("  contents: read", workflow)
        self.assertNotIn("  contents: write", workflow)
        self.assertNotIn("pull_request_target:", workflow)

    def test_invalid_claims_and_catalog_fail_closed(self):
        with self.assertRaises(InvalidSnapshot):
            balance(inbox(), catalog(), ["bad ID"])
        c = catalog()
        c["rows"].append(dict(c["rows"][0]))
        with self.assertRaises(InvalidSnapshot):
            balance(inbox(), c)


if __name__ == "__main__":
    unittest.main()
