"""Independent review repair beats new work; malformed evidence never picks a PR."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from repair_queue import choose_action

RUN = "b3b2766a-3548-832f-abf1-725336d75c18"
AUTHOR = "8d9d3375-a74c-8332-ae42-78607b1c88cc"
REVIEWER = "2d695844-ba1c-8328-af7d-bb02c9c493c3"
HEAD = "a57961e42bbda115659f67bfa4a6fe5a1540d473"
SNAPSHOT = "cc627c25eb6284e726b0d067108b521940530f02"


def fixtures(policy=None, number=67, head=HEAD, author=AUTHOR, request_id="pr67_mobile_guide_selector_overlap"):
    """Historical PR67 findings, normalized for replay, NOT current PR facts.

    IDs/head/verdict/roles/reviewed_at come from the independently fetched
    coordinator request and ops/reviews/PR0067_a57961e4.json at SNAPSHOT.
    Pull metadata is pinned to the historical reviewed head for unit replay.
    The live PR67 moved to edfe101c... during this run, so that live head must
    not select this old request. Synthetic variants below are clearly tests.
    """
    policy = deepcopy(policy) if policy is not None else json.loads((ROOT / "config/autonomous_repair.json").read_text())
    repo = policy["repository"]
    branch = policy["branch_prefix"] + author
    pr = {"number": number, "branch": branch, "repository": repo, "base_repository": repo,
          "state": "open", "merged": False, "head": head, "ci": "success", "ci_head": head,
          "author_task_id": policy["task_id"], "author_run_id": author}
    def source(path):
        return {"provider": "GitHub", "repository": repo, "branch": policy["coordination"]["branch"],
                "path": path, "commit": SNAPSHOT, "observed_at": "2026-10-26T13:23:43Z"}
    review_path = str(Path(policy["coordination"]["state_path"]).parent / "reviews" / f"PR{number:04d}_{head[:8]}.json")
    request = {"schema": 1, "id": request_id, "kind": "PR_REGRESSION_UI_LAYOUT", "priority": "P1",
               "repository": repo, "pr": number, "branch": branch, "head": head,
               "status": "OPEN", "assigned_role": "WORKER",
               "source": source(policy["integration"]["repair_requests"]),
               "review": {"schema": 1, "repository": repo, "pr": number, "branch": branch, "head": head,
                          "verdict": "REQUEST_CHANGES", "reviewer_kind": "REVIEWER",
                          "reviewer_task_id": policy["integration"]["task_id"], "reviewer_run_id": REVIEWER,
                          "author_task_id": policy["task_id"], "author_run_id": author,
                          "work_request_id": request_id, "reviewed_at": "2026-10-26T11:02:40.640Z",
                          "source": source(review_path)}}
    return policy, [pr], [request]


class ReviewRepairQueueTests(unittest.TestCase):
    def setUp(self):
        self.policy, self.pulls, self.requests = fixtures()

    def decide(self, requests=None, pulls=None):
        value = choose_action(self.policy, self.pulls if pulls is None else pulls, RUN,
                              trusted_review_requests=self.requests if requests is None else requests)
        self.assertFalse(value["change_scheduler"])
        return value

    def assert_wait(self, requests=None, pulls=None):
        value = self.decide(requests, pulls)
        self.assertEqual(value["action"], "WAIT_METADATA", value)
        self.assertNotIn("pr", value)
        self.assertNotIn("branch", value)

    def test_historical_green_pr67_request_changes_repairs_exact_existing_head(self):
        value = self.decide()
        self.assertEqual(value["action"], "REPAIR_REVIEW")
        self.assertEqual((value["pr"], value["branch"], value["head"]), (67, self.pulls[0]["branch"], HEAD))
        self.assertEqual(value["request_id"], self.requests[0]["id"])

    def test_old_three_argument_api_and_explicit_empty_input_remain_unchanged(self):
        legacy = choose_action(self.policy, self.pulls, RUN)
        self.assertEqual(legacy["action"], "START")
        self.assertEqual(legacy, self.decide(requests=[]))
        full = deepcopy(self.policy)
        full["max_open_prs"] = 1
        self.assertEqual(choose_action(full, self.pulls, RUN)["action"], "WAIT_REVIEW")
        self.assertEqual(choose_action(full, self.pulls, RUN, self.requests)["action"], "REPAIR_REVIEW")

    def test_failed_ci_keeps_precedence_even_over_malformed_request(self):
        for state in ("failure", "cancelled", "timed_out", "action_required"):
            with self.subTest(ci=state):
                self.pulls[0]["ci"] = state
                value = self.decide(requests=[{"schema": "bad"}])
                self.assertEqual((value["action"], value["pr"]), ("REPAIR_CI", 67))

    def test_pending_ci_keeps_existing_wait_behavior(self):
        for state in (None, "pending", "in_progress"):
            self.pulls[0]["ci"] = state
            self.assertEqual(self.decide()["action"], "WAIT_CI")

    def test_live_updated_pr67_head_cannot_reuse_historical_request(self):
        self.pulls[0].update(head="edfe101cda1b9f36e14afe5b8d1f2fccc85a346c", ci_head="edfe101cda1b9f36e14afe5b8d1f2fccc85a346c")
        self.assert_wait()

    def test_review_head_or_request_head_cannot_be_replayed(self):
        for target in ("request", "review"):
            p, pulls, reqs = fixtures()
            if target == "request":
                reqs[0]["head"] = "b" * 40
            else:
                reqs[0]["review"]["head"] = "b" * 40
            self.assert_wait(reqs, pulls)

    def test_closed_merged_missing_and_other_pr_are_rejected(self):
        self.assert_wait(pulls=[])
        for change in ({"state": "closed"}, {"merged": True}, {"number": 68}, {"state": None}):
            with self.subTest(change=change):
                pulls = deepcopy(self.pulls)
                pulls[0].update(change)
                self.assert_wait(pulls=pulls)

    def test_foreign_head_repo_or_foreign_base_repo_is_rejected(self):
        for key in ("repository", "base_repository"):
            pulls = deepcopy(self.pulls)
            pulls[0][key] = "foreign/fork"
            self.assert_wait(pulls=pulls)
        self.requests[0]["repository"] = "foreign/fork"
        self.assert_wait()

    def test_duplicate_pr_number_even_with_foreign_shadow_is_rejected(self):
        self.assert_wait(pulls=self.pulls + deepcopy(self.pulls))
        shadow = deepcopy(self.pulls[0])
        shadow["repository"] = "foreign/fork"
        self.assert_wait(pulls=self.pulls + [shadow])

    def test_duplicate_request_number_id_or_branch_is_rejected(self):
        self.assert_wait(requests=self.requests + deepcopy(self.requests))
        duplicate = deepcopy(self.requests[0])
        duplicate["id"] = "different_request"
        duplicate["review"]["work_request_id"] = duplicate["id"]
        self.assert_wait(requests=self.requests + [duplicate])

    def test_all_requests_are_validated_before_selecting_smallest_pr(self):
        _, p2, r2 = fixtures(self.policy, number=91, author="00000000-0000-4000-8000-000000000001", request_id="second_request")
        self.assertEqual(self.decide(self.requests + r2, self.pulls + p2)["pr"], 67)
        self.assertEqual(self.decide(r2 + self.requests, p2 + self.pulls)["pr"], 67)
        r2[0]["review"]["reviewer_kind"] = "WORKER"
        self.assert_wait(self.requests + r2, self.pulls + p2)

    def test_forged_role_task_verdict_and_author_identity_are_rejected(self):
        for key, value in (("reviewer_kind", "CONTROLLER"), ("reviewer_task_id", self.policy["task_id"]),
                           ("author_task_id", "wrong-task"), ("author_run_id", RUN),
                           ("verdict", "APPROVE"), ("work_request_id", "other_request")):
            with self.subTest(key=key):
                reqs = deepcopy(self.requests)
                reqs[0]["review"][key] = value
                self.assert_wait(reqs)

    def test_reviewer_cannot_be_author_or_current_run(self):
        for run in (AUTHOR, RUN, "not-a-uuid"):
            reqs = deepcopy(self.requests)
            reqs[0]["review"]["reviewer_run_id"] = run
            self.assert_wait(reqs)
        self.policy["integration"]["task_id"] = self.policy["task_id"]
        self.assert_wait()

    def test_unbound_pull_author_ci_head_or_branch_is_rejected(self):
        for key, value in (("author_task_id", "unknown"), ("author_run_id", RUN),
                           ("ci_head", "b" * 40), ("branch", self.policy["branch_prefix"] + RUN)):
            pulls = deepcopy(self.pulls)
            pulls[0][key] = value
            self.assert_wait(pulls=pulls)

    def test_missing_review_or_source_cannot_be_replaced_by_trusted_boolean(self):
        for key in ("review", "source"):
            reqs = deepcopy(self.requests)
            del reqs[0][key]
            reqs[0]["trusted"] = True
            self.assert_wait(reqs)
        for key in ("reviewer_run_id", "author_run_id", "source"):
            reqs = deepcopy(self.requests)
            del reqs[0]["review"][key]
            self.assert_wait(reqs)

    def test_wrong_provider_repo_branch_path_and_commit_are_rejected(self):
        for target in ("source", "review"):
            for key, value in (("provider", "PR_BODY"), ("repository", "foreign/repo"),
                               ("branch", "main"), ("path", "../untrusted.json"), ("commit", "unknown")):
                reqs = deepcopy(self.requests)
                source = reqs[0]["source"] if target == "source" else reqs[0]["review"]["source"]
                source[key] = value
                self.assert_wait(reqs)

    def test_different_coordinator_snapshots_or_old_observation_are_rejected(self):
        self.requests[0]["review"]["source"]["commit"] = "f" * 40
        self.assert_wait()
        self.policy, self.pulls, self.requests = fixtures()
        for value in ("unknown", "2026-10-26T13:00:00", "2026-10-26T10:00:00Z"):
            reqs = deepcopy(self.requests)
            reqs[0]["source"]["observed_at"] = value
            self.assert_wait(reqs)

    def test_bad_schema_container_ids_and_extra_authority_fields_fail_closed(self):
        for requests in (None, {}, "REQUEST_CHANGES", [None], [True]):
            value = choose_action(self.policy, self.pulls, RUN, trusted_review_requests=requests)
            self.assertEqual(value["action"], "WAIT_METADATA")
        for key, value in (("schema", True), ("schema", 2), ("pr", True), ("pr", 0),
                           ("id", "../secret"), ("id", "token\nsecret"), ("head", "short")):
            reqs = deepcopy(self.requests)
            reqs[0][key] = value
            self.assert_wait(reqs)
        self.requests[0]["automatic_merge_authorized"] = True
        self.assert_wait()

    def test_non_p1_worker_open_review_request_is_not_admitted(self):
        for key, value in (("assigned_role", "META"), ("status", "RESOLVED"),
                           ("priority", "P0"), ("kind", "ARBITRARY_EDIT")):
            reqs = deepcopy(self.requests)
            reqs[0][key] = value
            self.assert_wait(reqs)

    def test_disabled_or_missing_registered_review_identity_fails_closed(self):
        self.policy["integration"]["enabled"] = False
        self.assert_wait()
        self.policy["integration"]["enabled"] = True
        self.policy["task_id"] = None
        self.pulls[0]["author_task_id"] = None
        self.requests[0]["review"]["author_task_id"] = None
        self.assert_wait()

    def test_distinct_prs_with_duplicate_request_id_fail_closed(self):
        _, pulls, requests = fixtures(self.policy, number=91, author="00000000-0000-4000-8000-000000000001")
        self.assert_wait(self.requests + requests, self.pulls + pulls)

    def test_distinct_requests_from_different_shared_snapshots_fail_closed(self):
        _, pulls, requests = fixtures(self.policy, number=91, author="00000000-0000-4000-8000-000000000001", request_id="second_request")
        requests[0]["source"]["commit"] = "e" * 40
        requests[0]["review"]["source"]["commit"] = "e" * 40
        self.assert_wait(self.requests + requests, self.pulls + pulls)

    def test_malformed_pull_container_cannot_choose_an_editor(self):
        for pulls in ({}, [None], ["PR_BODY"]):
            self.assert_wait(pulls=pulls)

    def test_disabled_policy_and_noncanonical_caller_keep_old_contract(self):
        self.policy["enabled"] = False
        self.assertEqual(self.decide()["action"], "DISABLED")
        self.policy["enabled"] = True
        with self.assertRaises(ValueError):
            choose_action(self.policy, self.pulls, "unknown", self.requests)

    def test_generic_other_repository_task_branch_and_pr_number_work(self):
        policy = deepcopy(self.policy)
        policy.update(repository="example/space-racer", task_id="worker-game-two", branch="old/worker", branch_prefix="auto/game-two-")
        policy["integration"].update(task_id="reviewer-game-two", repair_requests="coord/WORK_REQUESTS.json")
        policy["coordination"].update(branch="game-two-ledger", state_path="coord/LEASE.json")
        policy, pulls, requests = fixtures(policy, number=1234, request_id="game_two_repair")
        value = choose_action(policy, pulls, RUN, requests)
        self.assertEqual((value["action"], value["pr"]), ("REPAIR_REVIEW", 1234))

    def test_inputs_are_unchanged_and_output_order_is_deterministic(self):
        before = deepcopy((self.policy, self.pulls, self.requests))
        self.assertEqual(self.decide(), self.decide())
        self.assertEqual((self.policy, self.pulls, self.requests), before)

    def test_cli_new_optional_field_and_legacy_input_both_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "input.json"
            data = {"run_id": RUN, "pulls": self.pulls, "trusted_review_requests": self.requests}
            path.write_text(json.dumps(data))
            cmd = [sys.executable, str(ROOT / "tools/repair_queue.py"), "--input", str(path),
                   "--policy", str(ROOT / "config/autonomous_repair.json")]
            proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(proc.stdout)["action"], "REPAIR_REVIEW")
            del data["trusted_review_requests"]
            path.write_text(json.dumps(data))
            proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(proc.stdout)["action"], "START")


if __name__ == "__main__":
    unittest.main()
