"""Adversarial pure-classifier regressions; no provider calls or credentials."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from system_host_write_triage import classify

RUN = "11111111-1111-4111-8111-111111111111"
OTHER = "22222222-2222-4222-8222-222222222222"
NOW = "2026-10-26T11:10:00Z"
AT = "2026-10-26T11:09:00Z"
A, B, C = "a" * 40, "b" * 40, "c" * 40


def fixtures():
    config = {"repository": "example/second-game", "task_id": "worker-2",
              "control_branch": "shared-control", "max_age_seconds": 300,
              "max_lease_seconds": 1800, "required_jobs": ["check", "hold"],
              "registered_tasks": {"WORKER": "worker-2", "META": "meta-2", "REVIEWER": "review-2"},
              "providers": {"service": "service-api", "lock": "github-api", "pr": "github-api",
                            "ci": "github-api", "operation": "connector-host"}}

    def wrap(kind, locator, data):
        return {"source": {"kind": kind, "provider": config["providers"][kind],
                           "locator": locator, "observed_at": AT}, "data": data}

    repo = config["repository"]
    e = {"schema": 1, "repository": repo, "task_id": "worker-2", "run_id": RUN,
         "work_branch": "repair/second-game",
         "service": wrap("service", "task/worker-2", {
             "task_id": "worker-2", "last_run": {"id": RUN, "recorded_status": "completed",
             "started_at": "2026-10-26T11:00:00Z", "completed_at": "2026-10-26T11:08:00Z"},
             "latest_result": None}),
         "lock": wrap("lock", repo + "/git/ref/heads/shared-control", {
             "repository": repo, "branch": "shared-control", "head": B, "epoch": 4, "holder": None}),
         "pr": wrap("pr", repo + "/pulls/3", {"repository": repo, "number": 3, "state": "open",
             "head": C, "base": A, "branch": "repair/second-game", "producing_run_id": RUN,
             "latest_qa_run_id": 5, "latest_qa_attempt": 1}),
         "ci": wrap("ci", repo + "/actions/runs/5", {"repository": repo, "pr_number": 3,
             "id": 5, "head": C, "base": A, "attempt": 1, "status": "completed", "conclusion": "success",
             "jobs": [{"name": name, "status": "completed", "conclusion": "success",
                       "run_id": 5, "attempt": 1, "head": C} for name in ("check", "hold")]}),
         "operation": None}
    return e, config


def holder(e, expired=False):
    if expired:
        e["service"]["data"]["last_run"]["started_at"] = "2026-10-26T10:30:00Z"
    e["lock"]["data"]["holder"] = {
        "kind": "WORKER", "task_id": "worker-2", "owner_id": RUN, "epoch": 4,
        "acquired_at": "2026-10-26T10:35:00Z" if expired else "2026-10-26T11:00:00Z",
        "expires_at": "2026-10-26T11:05:00Z" if expired else "2026-10-26T11:30:00Z",
        "work_branch": e["work_branch"]}


def operation(e, stage="update_ref", outcome="success", layer="github", code="OK"):
    e["operation"] = {"source": {"provider": "connector-host", "kind": "operation",
        "locator": e["lock"]["source"]["locator"], "observed_at": "2026-10-26T11:08:30Z"},
        "data": {"repository": e["repository"], "branch": "shared-control", "task_id": e["task_id"],
        "run_id": e["run_id"], "stage": stage, "outcome": outcome, "layer": layer, "code": code,
        "at": "2026-10-26T11:07:00Z", "force": False, "parent_sha": A,
        "expected_sha": A, "parent_shas": [A], "commit_sha": B, "epoch": 4}}


def observed_worker_incident():
    """Normalized real Oct26 peek/ref/PR/QA snapshot, NOT a raw host error.

    Peek task 6adbf0d6a7d881918ce181dff2468867 was fetched 11:23Z;
    observed_at is the post-collection clock bound actually read at 11:24:49Z.
    its matching result reports a denial but contains no original tool response.
    ref 952411e5... remained epoch71/null before this META acquired epoch72.
    PR67/QA40311284080 predates this service run: do not attribute its success
    to a repair that produced zero commits. Values are historical test evidence.
    """
    e, c = fixtures()
    repo, task = "kk051780/toy-wars-factory", "6adbf0d6a7d881918ce181dff2468867"
    run = "1c159542-ffdc-8327-9850-892b1a78843e"
    c.update(repository=repo, task_id=task, control_branch="twf-repair-coordinator",
             required_jobs=["offline", "compile_hold"])
    c["registered_tasks"]["WORKER"] = task
    c["registered_tasks"].update(META="6add445e4138819197d9cf2b1a02534d", REVIEWER="6add6aaceb4c8191b1666fe15f97cd88")
    c["providers"] = {"service": "automations.peek", "lock": "github.fetch",
                      "pr": "github.fetch", "ci": "github.fetch_workflow_run_jobs",
                      "operation": "github.connector_result"}
    e.update(repository=repo, task_id=task, run_id=run,
             work_branch="auto/twf-game-repair-8d9d3375-a74c-8332-ae42-78607b1c88cc")
    for value in (e["lock"], e["pr"], e["ci"]):
        value["data"]["repository"] = repo
    for value in (e["service"], e["lock"], e["pr"], e["ci"]):
        value["source"]["observed_at"] = "2026-10-26T11:24:49Z"
        value["source"]["provider"] = c["providers"][value["source"]["kind"]]
    e["service"]["source"]["locator"] = "task/" + task
    e["service"]["data"] = {"task_id": task, "last_run": {"id": run,
        "recorded_status": "completed", "started_at": "2026-10-26T11:06:07.152359Z",
        "completed_at": "2026-10-26T11:08:47.958965Z"}, "latest_result": {
        "run_id": run, "created_at": "2026-10-26T11:08:47.203260Z",
        "reported_state": "BLOCKED_HOST_WRITE", "raw_host_error_available": False}}
    e["lock"]["source"]["locator"] = repo + "/git/ref/heads/twf-repair-coordinator"
    e["lock"]["data"].update(branch="twf-repair-coordinator", epoch=71,
        head="952411e5e33c240d8d3170251977d1630fdc09c7")
    e["pr"]["source"]["locator"] = repo + "/pulls/67"
    e["pr"]["data"].update(number=67, branch=e["work_branch"],
        head="a57961e42bbda115659f67bfa4a6fe5a1540d473",
        base="09c08ddde66188fc0bd820ff1984c64f743d8144",
        producing_run_id="8d9d3375-a74c-8332-ae42-78607b1c88cc", latest_qa_run_id=40311284080)
    e["ci"]["source"]["locator"] = repo + "/actions/runs/40311284080"
    e["ci"]["data"].update(id=40311284080, pr_number=67,
        head=e["pr"]["data"]["head"], base=e["pr"]["data"]["base"])
    e["ci"]["data"]["jobs"] = [{"name": name, "status": "completed", "conclusion": "success",
        "run_id": 40311284080, "attempt": 1, "head": e["ci"]["data"]["head"]}
        for name in ("offline", "compile_hold")]
    return e, c


class HostWriteTriageTests(unittest.TestCase):
    def setUp(self):
        self.e, self.c = fixtures()

    def check_state(self, state, reason=None, e=None, c=None, now=NOW):
        value = classify(self.e if e is None else e, self.c if c is None else c, now)
        self.assertEqual(value["state"], state, value)
        if reason:
            self.assertEqual(value["reason"], reason)
        for flag in ("write_authorized", "takeover_allowed", "start_now_allowed"):
            self.assertIs(value[flag], False)
        return value

    def test_idle_terminal_current_run_head_all_jobs_can_wait_next_schedule(self):
        self.assertTrue(self.check_state("SAFE_TO_NEXT_SCHEDULE")["safe_to_next_schedule"])

    def test_active_lease_requires_join_and_cannot_be_stolen(self):
        holder(self.e)
        self.assertFalse(self.check_state("ACTIVE_LEASE")["claim_verified"])

    def test_claim_requires_ref_success_and_matching_reread(self):
        holder(self.e)
        operation(self.e)
        self.assertTrue(self.check_state("ACTIVE_LEASE")["claim_verified"])
        self.e["lock"]["data"]["head"] = C
        self.assertFalse(self.check_state("ACTIVE_LEASE")["claim_verified"])

    def test_commit_creation_alone_is_never_a_claim(self):
        operation(self.e, stage="create_commit")
        self.assertFalse(self.check_state("INDETERMINATE")["claim_verified"])
        holder(self.e)
        self.assertFalse(self.check_state("ACTIVE_LEASE")["claim_verified"])

    def test_ref_success_with_no_holder_is_not_a_claim(self):
        operation(self.e)
        self.check_state("INDETERMINATE")

    def test_claim_receipt_older_than_current_acquisition_is_not_confirmation(self):
        holder(self.e)
        operation(self.e)
        self.e["lock"]["data"]["holder"]["acquired_at"] = "2026-10-26T11:08:00Z"
        self.e["lock"]["data"]["holder"]["expires_at"] = "2026-10-26T11:38:00Z"
        self.assertFalse(self.check_state("ACTIVE_LEASE")["claim_verified"])

    def test_claim_must_match_epoch_owner_task_and_work_branch(self):
        holder(self.e)
        operation(self.e)
        original = deepcopy(self.e)
        for key, value in (("epoch", 3), ("run_id", OTHER), ("task_id", "other")):
            with self.subTest(key=key):
                e = deepcopy(original)
                e["operation"]["data"][key] = value
                self.assertFalse(classify(e, self.c, NOW)["claim_verified"])
        self.e["lock"]["data"]["holder"]["work_branch"] = "other"
        self.assertFalse(self.check_state("ACTIVE_LEASE")["claim_verified"])

    def test_expiry_alone_is_not_terminal_evidence(self):
        holder(self.e, expired=True)
        self.check_state("INDETERMINATE")

    def test_exact_owner_terminal_after_acquisition_identifies_orphan_only(self):
        holder(self.e, expired=True)
        self.e["holder_service"] = deepcopy(self.e["service"])
        self.check_state("WRITER_EXITED_WITHOUT_RELEASE")

    def test_orphan_wrong_owner_stale_generation_and_in_progress_rejected(self):
        holder(self.e, expired=True)
        self.e["holder_service"] = deepcopy(self.e["service"])
        for changes in ({"id": OTHER}, {"completed_at": "2026-10-26T10:34:59Z"},
                        {"recorded_status": "in_progress", "completed_at": None}):
            e = deepcopy(self.e)
            e["holder_service"]["data"]["last_run"].update(changes)
            self.check_state("INDETERMINATE", e=e)

    def test_reused_run_uuid_old_completion_cannot_release_new_generation(self):
        holder(self.e, expired=True)
        self.e["holder_service"] = deepcopy(self.e["service"])
        self.e["lock"]["data"]["holder"].update(acquired_at="2026-10-26T11:08:01Z", expires_at="2026-10-26T11:09:00Z")
        self.check_state("INDETERMINATE")

    def test_unknown_controller_expiry_cannot_be_recovered(self):
        holder(self.e, expired=True)
        self.e["lock"]["data"]["holder"].update(kind="CONTROLLER", task_id=None)
        self.check_state("INDETERMINATE")

    def test_in_progress_no_lease_never_starts_another_run(self):
        self.e["service"]["data"]["last_run"].update(recorded_status="in_progress", completed_at=None)
        self.check_state("INDETERMINATE", "SERVICE_IN_PROGRESS_DO_NOT_START_DUPLICATE")

    def test_host_denial_requires_direct_provider_operation(self):
        operation(self.e, outcome="failure", layer="host", code="HOST_WRITE_DENIED")
        self.check_state("HOST_WRITE_DENIED")

    def test_narrative_and_403_do_not_prove_host_rejection(self):
        self.e["service"]["data"]["latest_result"] = {
            "run_id": RUN, "created_at": AT, "reported_state": "BLOCKED_HOST_WRITE"}
        self.check_state("INDETERMINATE", "HOST_WRITE_REPORTED_RAW_PROVIDER_ERROR_UNAVAILABLE")
        operation(self.e, outcome="failure", layer="github", code="403")
        self.check_state("INDETERMINATE", "UNRECOGNIZED_OPERATION_FAILURE")

    def test_real_worker_report_keeps_raw_error_unavailable(self):
        e, c = observed_worker_incident()
        self.check_state("INDETERMINATE", "HOST_WRITE_REPORTED_RAW_PROVIDER_ERROR_UNAVAILABLE",
                         e=e, c=c, now="2026-10-26T11:25:00Z")

    def test_ref_race_requires_mismatched_expected_head(self):
        operation(self.e, outcome="failure", code="EXPECTED_SHA_MISMATCH")
        self.check_state("REF_RACE")
        self.e["lock"]["data"]["head"] = A
        self.check_state("INDETERMINATE")

    def test_unknown_errors_fail_closed_instead_of_retrying(self):
        operation(self.e, outcome="failure", layer="host", code="NEW_UNKNOWN_ERROR token=secret")
        value = self.check_state("INDETERMINATE")
        self.assertNotIn("secret", json.dumps(value))

    def test_force_or_different_parent_denies_all_operation_outcomes(self):
        operation(self.e, outcome="failure", layer="host", code="HOST_WRITE_DENIED")
        for key, value in (("force", True), ("force", 0), ("parent_sha", C), ("parent_shas", [A, C])):
            e = deepcopy(self.e)
            e["operation"]["data"][key] = value
            self.check_state("INDETERMINATE", e=e)

    def test_post_operation_reread_is_mandatory(self):
        operation(self.e, outcome="failure", layer="host", code="HOST_WRITE_DENIED")
        self.e["lock"]["source"]["observed_at"] = "2026-10-26T11:06:59Z"
        self.check_state("INDETERMINATE")

    def test_operation_after_service_completion_is_not_current_run_evidence(self):
        operation(self.e, outcome="failure", layer="host", code="HOST_WRITE_DENIED")
        self.e["operation"]["data"]["at"] = "2026-10-26T11:08:01Z"
        self.check_state("INDETERMINATE")

    def test_owner_service_starting_after_claim_is_not_terminal_proof(self):
        holder(self.e, expired=True)
        self.e["holder_service"] = deepcopy(self.e["service"])
        self.e["holder_service"]["data"]["last_run"]["started_at"] = "2026-10-26T10:35:01Z"
        self.check_state("INDETERMINATE")

    def test_forged_provider_kind_locator_or_trusted_flag_is_rejected(self):
        for name in ("service", "lock", "pr", "ci"):
            for key in ("provider", "kind", "locator"):
                with self.subTest(name=name, key=key):
                    e = deepcopy(self.e)
                    e[name]["source"][key] = "attacker"
                    e[name]["trusted"] = True
                    self.check_state("INDETERMINATE", e=e)

    def test_host_code_from_wrong_provider_is_not_a_host_receipt(self):
        operation(self.e, outcome="failure", layer="host", code="HOST_WRITE_DENIED")
        self.e["operation"]["source"]["provider"] = "assistant-report"
        self.check_state("INDETERMINATE")

    def test_missing_sources_timestamps_and_records_fail_closed(self):
        for name in ("service", "lock", "pr", "ci"):
            for key in ("source", "data"):
                e = deepcopy(self.e)
                del e[name][key]
                self.check_state("INDETERMINATE", e=e)
            e = deepcopy(self.e)
            del e[name]["source"]["observed_at"]
            self.check_state("INDETERMINATE", e=e)

    def test_old_future_naive_and_malformed_observations_fail_closed(self):
        for value in ("2026-10-26T11:04:59Z", "2026-10-26T11:10:01Z", "2026-10-26T11:09:00", "token-secret"):
            e = deepcopy(self.e)
            e["lock"]["source"]["observed_at"] = value
            self.check_state("INDETERMINATE", e=e)

    def test_previous_or_pre_retry_result_is_not_latest_run_output(self):
        for run, at in ((OTHER, AT), (RUN, "2026-10-26T10:59:59Z")):
            self.e["service"]["data"]["latest_result"] = {"run_id": run, "created_at": at}
            self.check_state("INDETERMINATE")

    def test_old_head_base_or_other_producing_run_cannot_reuse_green_ci(self):
        for component, key, value in (("ci", "head", A), ("ci", "base", B), ("pr", "producing_run_id", OTHER)):
            e = deepcopy(self.e)
            e[component]["data"][key] = value
            if key == "head":
                for job in e["ci"]["data"]["jobs"]:
                    job["head"] = value
            self.check_state("INDETERMINATE", e=e)

    def test_previous_run_or_attempt_job_cannot_be_borrowed(self):
        for key, value in (("run_id", 4), ("attempt", 2), ("head", A)):
            e = deepcopy(self.e)
            e["ci"]["data"]["jobs"][0][key] = value
            self.check_state("INDETERMINATE", e=e)
        self.e["pr"]["data"]["latest_qa_attempt"] = 2
        self.check_state("INDETERMINATE")

    def test_boolean_attempt_and_qa_identifiers_are_not_integers(self):
        for component, key in (("pr", "latest_qa_attempt"), ("ci", "attempt")):
            e = deepcopy(self.e)
            e[component]["data"][key] = True
            self.check_state("INDETERMINATE", e=e)
        self.e["ci"]["data"]["jobs"][0]["attempt"] = True
        self.check_state("INDETERMINATE")

    def test_current_run_head_pending_ci_is_wait_ci(self):
        for state in ("queued", "in_progress"):
            self.e["ci"]["data"].update(status=state, conclusion=None, jobs=[])
            self.check_state("WAIT_CI")

    def test_missing_duplicate_extra_failing_or_skipped_job_is_not_success(self):
        original = deepcopy(self.e["ci"]["data"]["jobs"])
        for jobs in ([], original[:1], original + original[:1],
                     original + [{**original[0], "name": "extra", "conclusion": "failure"}],
                     [{**j, "conclusion": "skipped"} for j in original]):
            self.e["ci"]["data"]["jobs"] = jobs
            self.check_state("INDETERMINATE")

    def test_unknown_service_state_and_ci_failure_do_not_mean_safe(self):
        self.e["service"]["data"]["last_run"]["recorded_status"] = "unknown"
        self.check_state("INDETERMINATE")
        self.e, _ = fixtures()
        self.e["ci"]["data"]["conclusion"] = "failure"
        self.check_state("INDETERMINATE")

    def test_input_is_not_mutated_and_output_is_deterministic(self):
        original = deepcopy(self.e)
        self.assertEqual(classify(self.e, self.c, NOW), classify(self.e, self.c, NOW))
        self.assertEqual(self.e, original)

    def test_seven_unsafe_mutations_are_caught_by_behavior_regressions(self):
        source = (ROOT / "tools/system_host_write_triage.py").read_text()
        mutations = [
            ("expiry_only_takeover", '    if holder is not None:\n        if now < expires:',
             '    if holder is not None:\n        if now >= expires:\n            return result("SAFE_TO_NEXT_SCHEDULE", "MUTANT", next_schedule=True)\n        if now < expires:',
             "test_expiry_alone_is_not_terminal_evidence"),
            ("commit_is_claim", 'return result("INDETERMINATE", "COMMIT_OR_REF_RESPONSE_WITHOUT_CONFIRMED_CLAIM")',
             'return result("ACTIVE_LEASE", "MUTANT", claim=True)', "test_commit_creation_alone_is_never_a_claim"),
            ("unknown_error_is_denial", 'return result("INDETERMINATE", "UNRECOGNIZED_OPERATION_FAILURE")',
             'return result("HOST_WRITE_DENIED", "MUTANT")', "test_unknown_errors_fail_closed_instead_of_retrying"),
            ("borrow_old_qa", 'if producer != run or ci["head"] != head or ci["base"] != base:',
             "if False:", "test_old_head_base_or_other_producing_run_cannot_reuse_green_ci"),
            ("narrative_is_receipt", 'return result("INDETERMINATE", "HOST_WRITE_REPORTED_RAW_PROVIDER_ERROR_UNAVAILABLE")',
             'return result("HOST_WRITE_DENIED", "MUTANT")', "test_real_worker_report_keeps_raw_error_unavailable"),
            ("spoof_provider", 'require(source["provider"] == c["providers"][kind])',
             "pass", "test_forged_provider_kind_locator_or_trusted_flag_is_rejected"),
            ("start_during_run", 'if svc["last_run"]["recorded_status"] == "in_progress":',
             "if False:", "test_in_progress_no_lease_never_starts_another_run"),
        ]
        for name, old, new, method in mutations:
            with self.subTest(mutation=name):
                self.assertEqual(source.count(old), 1)
                module = types.ModuleType(name)
                exec(compile(source.replace(old, new), name, "exec"), module.__dict__)
                with patch.object(sys.modules[__name__], "classify", module.classify):
                    outcome = unittest.TestResult()
                    HostWriteTriageTests(method).run(outcome)
                self.assertTrue(outcome.failures, name)
                self.assertFalse(outcome.errors, name)

    def test_malformed_types_boolean_ids_and_uuid_fail_closed(self):
        for key, value in (("run_id", "BAD-UUID"), ("schema", True), ("repository", "other/repo")):
            e = deepcopy(self.e)
            e[key] = value
            self.check_state("INDETERMINATE", e=e)
        for bad in (None, [], "secret", 1):
            self.check_state("INDETERMINATE", e=bad, c=[])
        self.e["pr"]["data"]["number"] = True
        self.check_state("INDETERMINATE")

    def test_cli_outputs_only_safe_keys_and_no_error_or_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            evidence, config = path / "e.json", path / "c.json"
            self.e["raw_error"] = "Authorization: Bearer supersecret\npassword=hidden"
            evidence.write_text(json.dumps(self.e))
            config.write_text(json.dumps(self.c))
            cmd = [sys.executable, str(ROOT / "tools/system_host_write_triage.py"),
                   "--evidence", str(evidence), "--config", str(config), "--now", NOW]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stderr, "")
            self.assertNotIn("secret", proc.stdout)
            self.assertNotIn("hidden", proc.stdout)
            evidence.write_text('{"schema":1,"schema":1,"token":"supersecret"}')
            proc = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            self.assertEqual(json.loads(proc.stdout)["state"], "INDETERMINATE")
            self.assertNotIn("supersecret", proc.stdout + proc.stderr)
            proc = subprocess.run(cmd + ["--unexpected", "Bearer supersecret"], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            self.assertEqual(json.loads(proc.stdout)["state"], "INDETERMINATE")
            self.assertNotIn("supersecret", proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
