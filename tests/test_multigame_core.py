"""Adversarial tests for the portable, read-only multi-game control plane."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from studio_autopilot.core import InvalidProject, evaluate, load_portfolio, plan, validate_project

ROOT = Path(__file__).resolve().parents[1]
PORTFOLIO = "studio_autopilot/portfolio.json"
GOOD_SHA = "a" * 40
BAD_SHA = "b" * 40


class MultiGameControlPlaneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.projects = load_portfolio(ROOT, PORTFOLIO)
        cls.toy = cls.projects[0]
        cls.demo = cls.projects[1]

    def observation(self, **updates):
        data = {
            "repository": "kk051780/toy-wars-factory",
            "main_head": GOOD_SHA,
            "main_qa_head": GOOD_SHA,
            "main_qa": "success",
            "worker_run": "completed",
            "reviewer_run": "completed",
            "meta_run": "no_update",
            "lease": None,
            "open_prs": [],
        }
        data.update(updates)
        return data

    def portfolio_with(self, projects):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        root.joinpath("studio_autopilot/projects").mkdir(parents=True)
        paths = []
        for i, p in enumerate(projects):
            name = f"studio_autopilot/projects/p{i}.json"
            (root / name).write_text(json.dumps(p), encoding="utf-8")
            paths.append(name)
        (root / "portfolio.json").write_text(json.dumps({"schema": 1, "projects": paths}), encoding="utf-8")
        return tmp, root

    def test_two_genres_and_template_is_not_active(self):
        self.assertEqual({x["game_id"] for x in self.projects},
                         {"toy-wars-factory", "skyline-parkour-template"})
        self.assertNotEqual(self.toy["game_design"]["genre"], self.demo["game_design"]["genre"])
        self.assertEqual(self.demo["phase"], "UNBOUND_TEMPLATE")
        self.assertIsNone(self.demo["repository"])
        self.assertEqual(self.demo["quality"]["engine"], "NOT_RUN")

    def test_no_observations_never_authorize_work(self):
        decisions = plan(ROOT, PORTFOLIO)
        self.assertEqual([x["action"] for x in decisions],
                         ["HOLD_NO_OBSERVATION", "UNBOUND_TEMPLATE"])
        self.assertTrue(all(not x["release_eligible"] and x["mode"] == "ADVISORY_ONLY" for x in decisions))

    def test_meta_no_update_is_visible_but_does_not_steal_worker_lane(self):
        result = evaluate(self.toy, self.observation())
        self.assertEqual(result["action"], "CANDIDATE_DRAFT_ONLY")
        self.assertEqual(result["alerts"], ["META_NO_UPDATE"])

    def test_stale_main_qa_blocks_execution(self):
        result = evaluate(self.toy, self.observation(main_qa_head=BAD_SHA))
        self.assertEqual(result["action"], "WAIT_EXACT_MAIN_QA")

    def test_main_failure_precedes_new_features(self):
        result = evaluate(self.toy, self.observation(main_qa="failure"))
        self.assertEqual(result["action"], "REPAIR_MAIN_FIRST")

    def test_pending_main_qa_blocks(self):
        self.assertEqual(evaluate(self.toy, self.observation(main_qa="pending"))["action"], "WAIT_MAIN_QA")

    def test_any_existing_lease_prevents_parallel_editing(self):
        result = evaluate(self.toy, self.observation(lease={"kind": "REVIEWER"}))
        self.assertEqual(result["action"], "JOIN_EXISTING_LEASE")

    def test_exact_head_review_candidate(self):
        result = evaluate(self.toy, self.observation(open_prs=[
            {"head_sha": GOOD_SHA, "ci_head_sha": GOOD_SHA, "ci": "success"}]))
        self.assertEqual(result["action"], "REQUEST_INDEPENDENT_REVIEW")

    def test_stale_pr_ci_is_not_review_evidence(self):
        result = evaluate(self.toy, self.observation(open_prs=[
            {"head_sha": GOOD_SHA, "ci_head_sha": BAD_SHA, "ci": "success"}]))
        self.assertEqual(result["action"], "CANDIDATE_DRAFT_ONLY")

    def test_full_pr_capacity_cannot_add_a_new_pr(self):
        prs = [{"head_sha": GOOD_SHA, "ci_head_sha": BAD_SHA, "ci": "pending"}] * 3
        self.assertEqual(evaluate(self.toy, self.observation(open_prs=prs))["action"], "WAIT_PR_CAPACITY")
        prs.append({})
        self.assertEqual(evaluate(self.toy, self.observation(open_prs=prs))["action"], "HOLD_PR_CAPACITY_BREACH")

    def test_missing_pr_queue_fails_closed(self):
        self.assertEqual(evaluate(self.toy, self.observation(open_prs="")).get("action"),
                         "HOLD_INVALID_PR_QUEUE")

    def test_worker_no_update_requires_diagnosis(self):
        result = evaluate(self.toy, self.observation(worker_run="no_update"))
        self.assertEqual(result["action"], "DIAGNOSE_WORKER")
        self.assertIn("WORKER_NO_UPDATE", result["alerts"])

    def test_reviewer_no_update_is_reported(self):
        result = evaluate(self.toy, self.observation(reviewer_run="no_update"))
        self.assertIn("REVIEWER_NO_UPDATE", result["alerts"])

    def test_foreign_repo_cannot_reuse_a_toy_observation(self):
        self.assertEqual(evaluate(self.toy, self.observation(repository="other/secret"))["action"],
                         "HOLD_FOREIGN_REPOSITORY")

    def test_missing_head_fails_closed(self):
        self.assertEqual(evaluate(self.toy, self.observation(main_head="latest"))["action"],
                         "HOLD_MISSING_HEAD")

    def test_quality_status_cannot_overrule_public_release_block(self):
        game = copy.deepcopy(self.toy)
        game["quality"] = {key: "PASS" for key in game["quality"]}
        result = evaluate(game, self.observation())
        self.assertFalse(result["release_eligible"])

    def test_template_cannot_claim_any_task_or_repo(self):
        game = copy.deepcopy(self.demo)
        game["roles"]["author"] = self.toy["roles"]["author"]
        with self.assertRaises(InvalidProject):
            validate_project(game)
        game = copy.deepcopy(self.demo)
        game["repository"] = self.toy["repository"]
        with self.assertRaises(InvalidProject):
            validate_project(game)

    def test_weakening_safety_gates_is_rejected(self):
        for key, value in (("draft_only", False),
                           ("independent_review", False),
                           ("exact_head_ci", False),
                           ("post_merge_main_qa", False),
                           ("auto_publish", True),
                           ("external_inference", True),
                           ("daily_external_budget_usd", 0.01),
                           ("max_open_prs", 100)):
            with self.subTest(field=key):
                game = copy.deepcopy(self.toy)
                game["safety"][key] = value
                with self.assertRaises(InvalidProject):
                    validate_project(game)

    def test_wrong_or_duplicate_task_ids_are_rejected(self):
        for key, value in (("reviewer", self.toy["roles"]["author"]),
                           ("reviewer", "not-a-uuid")):
            game = copy.deepcopy(self.toy)
            game["roles"][key] = value
            with self.assertRaises(InvalidProject):
                validate_project(game)

    def test_game_registry_rejects_duplicate_repository(self):
        second = copy.deepcopy(self.toy)
        second["game_id"] = "separate-game"
        second["roles"]["author"] = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        second["roles"]["reviewer"] = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
        second["roles"]["meta"] = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
        tmp, root = self.portfolio_with([self.toy, second])
        try:
            with self.assertRaises(InvalidProject):
                load_portfolio(root, "portfolio.json")
        finally:
            tmp.cleanup()

    def test_game_registry_rejects_cross_game_task_identity(self):
        second = copy.deepcopy(self.toy)
        second["game_id"] = "second-independent-game"
        second["repository"] = "example/second-independent-game"
        second["roles"]["reviewer"] = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
        second["roles"]["meta"] = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
        tmp, root = self.portfolio_with([self.toy, second])
        try:
            with self.assertRaises(InvalidProject):
                load_portfolio(root, "portfolio.json")
        finally:
            tmp.cleanup()

    def test_registry_rejects_duplicate_game_id(self):
        tmp, root = self.portfolio_with([self.toy, self.toy])
        try:
            with self.assertRaises(InvalidProject):
                load_portfolio(root, "portfolio.json")
        finally:
            tmp.cleanup()

    def test_traversal_or_absolute_manifest_path_rejected(self):
        for path in ("../secret.json", "/etc/passwd", r"..\private.json", "./../secret.json"):
            tmp = tempfile.TemporaryDirectory()
            try:
                root = Path(tmp.name)
                (root / "portfolio.json").write_text(
                    json.dumps({"schema": 1, "projects": [path]}), encoding="utf-8")
                with self.assertRaises(InvalidProject):
                    load_portfolio(root, "portfolio.json")
            finally:
                tmp.cleanup()

    def test_unknown_observation_game_rejected(self):
        tmp = tempfile.TemporaryDirectory()
        try:
            root = Path(tmp.name)
            (root / "observation.json").write_text(
                json.dumps({"schema": 1, "projects": {"foreign-game": {}}}), encoding="utf-8")
            with self.assertRaises(InvalidProject):
                plan(ROOT, PORTFOLIO, str(root / "observation.json"))
        finally:
            tmp.cleanup()

    def test_unknown_schema_fields_rejected(self):
        game = copy.deepcopy(self.toy)
        game["api_key"] = "should not be stored in manifests"
        with self.assertRaises(InvalidProject):
            validate_project(game)


if __name__ == "__main__":
    unittest.main()
