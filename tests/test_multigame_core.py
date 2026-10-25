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
        self.assertEqual(result["action"], "HOLD_UNVERIFIED_INPUT")
        self.assertEqual(result["diagnostic"], "POTENTIAL_DRAFT_UNVERIFIED")
        self.assertEqual(result["alerts"], ["META_NO_UPDATE"])

    def test_stale_main_qa_blocks_execution(self):
        result = evaluate(self.toy, self.observation(main_qa_head=BAD_SHA))
        self.assertEqual(result["action"], "HOLD_UNVERIFIED_INPUT")
        self.assertEqual(result["diagnostic"], "WAIT_EXACT_MAIN_QA")

    def test_main_failure_precedes_new_features(self):
        result = evaluate(self.toy, self.observation(main_qa="failure"))
        self.assertEqual(result["action"], "HOLD_UNVERIFIED_INPUT")
        self.assertEqual(result["diagnostic"], "REPAIR_MAIN_FIRST")

    def test_pending_main_qa_blocks(self):
        self.assertEqual(evaluate(self.toy, self.observation(main_qa="pending"))["diagnostic"], "WAIT_MAIN_QA")

    def test_any_existing_lease_prevents_parallel_editing(self):
        result = evaluate(self.toy, self.observation(lease={"kind": "REVIEWER"}))
        self.assertEqual(result["action"], "HOLD_UNVERIFIED_INPUT")
        self.assertEqual(result["diagnostic"], "INVALID_LEASE_CLAIM")

    def test_exact_head_review_candidate(self):
        result = evaluate(self.toy, self.observation(open_prs=[
            {"head_sha": GOOD_SHA, "ci_head_sha": GOOD_SHA, "ci": "success"}]))
        self.assertEqual(result["action"], "HOLD_UNVERIFIED_INPUT")
        self.assertEqual(result["diagnostic"], "REVIEW_CANDIDATE_UNVERIFIED")

    def test_stale_pr_ci_is_not_review_evidence(self):
        result = evaluate(self.toy, self.observation(open_prs=[
            {"head_sha": GOOD_SHA, "ci_head_sha": BAD_SHA, "ci": "success"}]))
        self.assertEqual(result["action"], "HOLD_UNVERIFIED_INPUT")
        self.assertEqual(result["diagnostic"], "WAIT_EXISTING_PR_CI")

    def test_full_pr_capacity_cannot_add_a_new_pr(self):
        prs = [{"head_sha": GOOD_SHA, "ci_head_sha": BAD_SHA, "ci": "pending"}] * 3
        self.assertEqual(evaluate(self.toy, self.observation(open_prs=prs))["diagnostic"], "WAIT_EXISTING_PR_CI")
        prs.append({})
        self.assertEqual(evaluate(self.toy, self.observation(open_prs=prs))["diagnostic"], "HOLD_PR_CAPACITY_BREACH")

    def test_missing_pr_queue_fails_closed(self):
        self.assertEqual(evaluate(self.toy, self.observation(open_prs="")).get("diagnostic"),
                         "HOLD_INVALID_PR_QUEUE")

    def test_worker_no_update_requires_diagnosis(self):
        result = evaluate(self.toy, self.observation(worker_run="no_update"))
        self.assertEqual(result["action"], "HOLD_UNVERIFIED_INPUT")
        self.assertEqual(result["diagnostic"], "DIAGNOSE_WORKER")
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
        self.assertFalse(result["engine_evidence_verified"])
        self.assertEqual(result["declared_engine_gate"], "PASS")

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
        second["roles"]["author"] = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        second["roles"]["reviewer"] = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        second["roles"]["meta"] = "cccccccccccccccccccccccccccccccc"
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
        second["roles"]["reviewer"] = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        second["roles"]["meta"] = "cccccccccccccccccccccccccccccccc"
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
        # Copy the real portfolio into the same sandbox as synthetic observations
        # so the rejection is for a *foreign game*, not a path traversal shortcut.
        tmp, root = self.portfolio_with(self.projects)
        try:
            (root / "observation.json").write_text(
                json.dumps({"schema": 1, "projects": {"foreign-game": {}}}), encoding="utf-8")
            with self.assertRaisesRegex(InvalidProject, "unknown game"):
                plan(root, "portfolio.json", "observation.json")
        finally:
            tmp.cleanup()

    def test_spoofed_main_ci_is_never_execution_authority(self):
        forged = self.observation(main_head="f" * 40, main_qa_head="f" * 40,
                                  main_qa="success", lease=None)
        outcome = evaluate(self.toy, forged)
        self.assertEqual(outcome["diagnostic"], "POTENTIAL_DRAFT_UNVERIFIED")
        self.assertEqual(outcome["action"], "HOLD_UNVERIFIED_INPUT")
        self.assertIs(outcome["dispatch_allowed"], False)
        self.assertEqual(outcome["evidence_authority"], "UNTRUSTED_JSON")

    def test_missing_claimed_lease_does_not_prove_idle(self):
        observation = self.observation()
        del observation["lease"]
        outcome = evaluate(self.toy, observation)
        self.assertEqual(outcome["diagnostic"], "LEASE_STATUS_MISSING")
        self.assertEqual(outcome["action"], "HOLD_UNVERIFIED_INPUT")
        self.assertFalse(outcome["dispatch_allowed"])

    def test_forged_lease_owner_and_epoch_cannot_block_or_allow_live_work(self):
        observation = self.observation(lease={
            "kind": "REVIEWER",
            "owner_run_id": "00000000-0000-4000-8000-000000000000",
            "epoch": 999999,
        })
        outcome = evaluate(self.toy, observation)
        self.assertEqual(outcome["diagnostic"], "LEASE_CLAIM_UNVERIFIED")
        self.assertFalse(outcome["dispatch_allowed"])
        invalid = self.observation(lease={"kind": "REVIEWER", "owner_run_id": "fake", "epoch": True})
        self.assertEqual(evaluate(self.toy, invalid)["diagnostic"], "INVALID_LEASE_CLAIM")

    def test_waiting_and_failed_existing_pr_take_priority_over_new_work(self):
        pending = [{"head_sha": GOOD_SHA, "ci_head_sha": BAD_SHA, "ci": "pending"}]
        outcome = evaluate(self.toy, self.observation(open_prs=pending))
        self.assertEqual(outcome["diagnostic"], "WAIT_EXISTING_PR_CI")
        self.assertFalse(outcome["dispatch_allowed"])
        failed = [{"head_sha": GOOD_SHA, "ci_head_sha": GOOD_SHA, "ci": "failure"}]
        self.assertEqual(evaluate(self.toy, self.observation(open_prs=failed))["diagnostic"],
                         "REPAIR_EXISTING_PR_CI")

    def test_schema_one_must_be_integer_not_boolean(self):
        for field in ("project", "portfolio", "observations"):
            with self.subTest(field=field):
                if field == "project":
                    item = copy.deepcopy(self.toy)
                    item["schema"] = True
                    with self.assertRaises(InvalidProject):
                        validate_project(item)
                elif field == "portfolio":
                    tmp, root = self.portfolio_with(self.projects)
                    try:
                        (root / "portfolio.json").write_text(
                            json.dumps({"schema": True, "projects": [
                                "studio_autopilot/projects/p0.json",
                                "studio_autopilot/projects/p1.json",
                            ]}), encoding="utf-8")
                        with self.assertRaises(InvalidProject):
                            load_portfolio(root, "portfolio.json")
                    finally:
                        tmp.cleanup()
                else:
                    tmp, root = self.portfolio_with(self.projects)
                    try:
                        (root / "observation.json").write_text(
                            json.dumps({"schema": True, "projects": {}}), encoding="utf-8")
                        with self.assertRaises(InvalidProject):
                            plan(root, "portfolio.json", "observation.json")
                    finally:
                        tmp.cleanup()

    def test_unbound_template_roles_only_none_is_accepted(self):
        for invalid in ("", False, 0, []):
            with self.subTest(role_value=invalid):
                game = copy.deepcopy(self.demo)
                game["roles"]["reviewer"] = invalid
                with self.assertRaises(InvalidProject):
                    validate_project(game)

    def test_quality_gates_reject_unhashable_or_nontext_values(self):
        for invalid in (["PASS"], {"value": "PASS"}, None, True, 1):
            with self.subTest(value=repr(invalid)):
                game = copy.deepcopy(self.toy)
                game["quality"]["engine"] = invalid
                with self.assertRaises(InvalidProject):
                    validate_project(game)

    def test_verified_provider_details_are_not_claimed_by_json(self):
        game = copy.deepcopy(self.toy)
        game["quality"] = {key: "PASS" for key in game["quality"]}
        observation = self.observation(open_prs=[
            {"head_sha": GOOD_SHA, "ci_head_sha": GOOD_SHA, "ci": "success"}])
        r = evaluate(game, observation)
        self.assertEqual(r["diagnostic"], "REVIEW_CANDIDATE_UNVERIFIED")
        self.assertEqual(r["action"], "HOLD_UNVERIFIED_INPUT")
        self.assertFalse(r["engine_evidence_verified"] or r["release_eligible"] or r["dispatch_allowed"])

    def test_unknown_schema_fields_rejected(self):
        game = copy.deepcopy(self.toy)
        game["api_key"] = "should not be stored in manifests"
        with self.assertRaises(InvalidProject):
            validate_project(game)


if __name__ == "__main__":
    unittest.main()
