"""Issue72 terminal-outcome regression, canonical CLI and retained safety fences."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import repair_control
import system_host_write_triage as legacy
import system_host_write_triage_v2 as triage
from test_system_host_write_triage import (
    fixtures, holder, operation, observed_worker_incident, NOW, RUN, A, B, OTHER,
)


class TriageV2Tests(unittest.TestCase):
    def check_safe_flags(self, value):
        for flag in ("write_authorized", "start_now_allowed", "takeover_allowed"):
            self.assertIs(value[flag], False)
        self.assertEqual(set(value), {
            "schema", "state", "reason", "claim_verified",
            "safe_to_next_schedule", "start_now_allowed",
            "takeover_allowed", "write_authorized",
        })

    def test_failed_green_exact_head_is_not_safe(self):
        e, c = fixtures()
        e["service"]["data"]["last_run"]["recorded_status"] = "failed"
        value = triage.classify(e, c, NOW)
        self.assertEqual(value["state"], "INDETERMINATE")
        self.assertEqual(value["reason"], "SERVICE_NOT_SUCCESSFULLY_COMPLETED")
        self.assertFalse(value["safe_to_next_schedule"])
        self.check_safe_flags(value)

    def test_no_update_green_exact_head_is_not_safe(self):
        e, c = fixtures()
        e["service"]["data"]["last_run"]["recorded_status"] = "no_update"
        value = triage.classify(e, c, NOW)
        self.assertEqual(value["state"], "INDETERMINATE")
        self.assertEqual(value["reason"], "SERVICE_NOT_SUCCESSFULLY_COMPLETED")
        self.assertFalse(value["safe_to_next_schedule"])
        self.check_safe_flags(value)

    def test_completed_matches_accepted_idle_result(self):
        e, c = fixtures()
        value = triage.classify(e, c, NOW)
        self.assertEqual(value, legacy.classify(e, c, NOW))
        self.assertEqual(value["state"], "SAFE_TO_NEXT_SCHEDULE")
        self.check_safe_flags(value)

    def test_terminal_orphan_diagnosis_is_preserved(self):
        for state in ("completed", "failed", "no_update"):
            with self.subTest(state=state):
                e, c = fixtures()
                holder(e, expired=True)
                e["service"]["data"]["last_run"]["recorded_status"] = state
                e["holder_service"] = deepcopy(e["service"])
                value = triage.classify(e, c, NOW)
                self.assertEqual(value, legacy.classify(e, c, NOW))
                self.assertEqual(value["state"], "WRITER_EXITED_WITHOUT_RELEASE")
                self.check_safe_flags(value)

    def test_active_lease_is_not_hidden_by_terminal_guard(self):
        for state in ("failed", "no_update"):
            e, c = fixtures()
            holder(e)
            e["service"]["data"]["last_run"]["recorded_status"] = state
            value = triage.classify(e, c, NOW)
            self.assertEqual(value["state"], "ACTIVE_LEASE")
            self.assertFalse(value["claim_verified"])
            self.check_safe_flags(value)

    def test_expiry_alone_is_not_recovery_or_takeover(self):
        e, c = fixtures()
        holder(e, expired=True)
        e["holder_service"] = deepcopy(e["service"])
        e["holder_service"]["data"]["last_run"].update(
            recorded_status="in_progress", completed_at=None)
        value = triage.classify(e, c, NOW)
        self.assertEqual(value["state"], "INDETERMINATE")
        self.assertEqual(value["reason"], "EXPIRY_IS_NOT_TAKEOVER_EVIDENCE")
        self.check_safe_flags(value)

    def test_in_progress_never_allows_duplicate_start(self):
        e, c = fixtures()
        e["service"]["data"]["last_run"].update(
            recorded_status="in_progress", completed_at=None)
        value = triage.classify(e, c, NOW)
        self.assertEqual(value["state"], "INDETERMINATE")
        self.assertEqual(value["reason"], "SERVICE_IN_PROGRESS_DO_NOT_START_DUPLICATE")
        self.check_safe_flags(value)

    def test_commit_without_ref_reread_is_not_claim(self):
        e, c = fixtures()
        operation(e, stage="create_commit")
        value = triage.classify(e, c, NOW)
        self.assertEqual(value["state"], "INDETERMINATE")
        self.assertFalse(value["claim_verified"])
        self.check_safe_flags(value)

    def test_known_host_ref_race_and_unknown_errors_stay_distinct(self):
        cases = [
            ("host", "HOST_WRITE_DENIED", "HOST_WRITE_DENIED"),
            ("github", "EXPECTED_SHA_MISMATCH", "REF_RACE"),
            ("host", "unknown token=secret", "INDETERMINATE"),
        ]
        for layer, code, expected in cases:
            with self.subTest(layer=layer, code=code):
                e, c = fixtures()
                operation(e, outcome="failure", layer=layer, code=code)
                value = triage.classify(e, c, NOW)
                self.assertEqual(value["state"], expected)
                self.assertNotIn("secret", json.dumps(value))
                self.check_safe_flags(value)

    def test_pending_ci_and_failed_ci_keep_existing_diagnosis(self):
        e, c = fixtures()
        e["ci"]["data"].update(status="in_progress", conclusion=None, jobs=[])
        self.assertEqual(triage.classify(e, c, NOW)["state"], "WAIT_CI")
        e, c = fixtures()
        e["ci"]["data"]["conclusion"] = "failure"
        self.assertEqual(triage.classify(e, c, NOW)["state"], "INDETERMINATE")

    def test_same_run_head_base_and_attempt_cannot_borrow_qa(self):
        for component, key, bad in (
            ("pr", "producing_run_id", OTHER), ("ci", "head", A),
            ("ci", "base", B), ("ci", "attempt", 2),
        ):
            e, c = fixtures()
            e[component]["data"][key] = bad
            self.assertEqual(triage.classify(e, c, NOW)["state"], "INDETERMINATE")

    def test_forged_or_missing_provider_and_time_fail_closed(self):
        for component in ("service", "lock", "pr", "ci"):
            for key, bad in (("provider", "forged"), ("observed_at", "unknown")):
                e, c = fixtures()
                e[component]["source"][key] = bad
                self.assertEqual(triage.classify(e, c, NOW)["state"], "INDETERMINATE")
            e, c = fixtures()
            del e[component]["source"]
            self.assertEqual(triage.classify(e, c, NOW)["state"], "INDETERMINATE")

    def test_unknown_missing_and_malformed_service_fail_closed(self):
        for bad in (None, "unknown", True, [], {}):
            e, c = fixtures()
            e["service"]["data"]["last_run"]["recorded_status"] = bad
            self.assertEqual(triage.classify(e, c, NOW)["state"], "INDETERMINATE")
        for bad in (None, [], {}, "token=secret"):
            _, c = fixtures()
            value = triage.classify(bad, c, NOW)
            self.assertEqual(value["state"], "INDETERMINATE")
            self.check_safe_flags(value)

    def test_historical_host_report_remains_unproven(self):
        e, c = observed_worker_incident()
        value = triage.classify(e, c, "2026-10-26T11:25:00Z")
        self.assertEqual(value, legacy.classify(e, c, "2026-10-26T11:25:00Z"))
        self.assertEqual(value["reason"], "HOST_WRITE_REPORTED_RAW_PROVIDER_ERROR_UNAVAILABLE")
        self.check_safe_flags(value)

    def test_input_unchanged_deterministic_and_generic_repository(self):
        e, c = fixtures()  # example/second-game; not hard-coded to Toy Wars.
        saved = deepcopy((e, c))
        self.assertEqual(triage.classify(e, c, NOW), triage.classify(e, c, NOW))
        self.assertEqual((e, c), saved)

    def run_cli(self, e, c, extra=(), *, canonical=True, raw=None, stdin=False):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence, config = root / "e.json", root / "c.json"
            payload = json.dumps(e) if raw is None else raw
            evidence.write_text(payload)
            config.write_text(json.dumps(c))
            script = "repair_control.py" if canonical else "system_host_write_triage_v2.py"
            cmd = [sys.executable, str(ROOT / "tools" / script)]
            if canonical:
                cmd.append("triage")
            cmd += ["--evidence", "-" if stdin else str(evidence),
                    "--config", str(config), "--now", NOW, *extra]
            return subprocess.run(cmd, input=payload if stdin else None,
                                  capture_output=True, text=True)

    def test_canonical_control_cli_executes_v2_for_all_terminal_states(self):
        for state, expected, code in (
            ("completed", "SAFE_TO_NEXT_SCHEDULE", 0),
            ("failed", "INDETERMINATE", 2), ("no_update", "INDETERMINATE", 2),
        ):
            e, c = fixtures()
            e["service"]["data"]["last_run"]["recorded_status"] = state
            proc = self.run_cli(e, c)
            self.assertEqual(proc.returncode, code, proc.stderr)
            self.assertEqual(proc.stderr, "")
            value = json.loads(proc.stdout)
            self.assertEqual(value["state"], expected)
            self.assertEqual(value, triage.classify(e, c, NOW))
            self.check_safe_flags(value)

    def test_control_dispatch_calls_v2_with_exact_arguments_and_exit_code(self):
        with patch.object(triage, "main", return_value=2) as called:
            self.assertEqual(repair_control.main(["triage", "--evidence", "-"]), 2)
        called.assert_called_once_with(["--evidence", "-"])

    def test_v2_direct_cli_and_stdin_match_canonical_entry(self):
        e, c = fixtures()
        e["service"]["data"]["last_run"]["recorded_status"] = "failed"
        for canonical in (True, False):
            proc = self.run_cli(e, c, canonical=canonical, stdin=True)
            self.assertEqual(proc.returncode, 2)
            self.assertEqual(proc.stderr, "")
            self.assertEqual(json.loads(proc.stdout), triage.classify(e, c, NOW))

    def test_cli_rejects_duplicate_keys_nan_bad_config_and_secret_args(self):
        e, c = fixtures()
        for raw in ('{"schema":1,"schema":1,"token":"private-token"}',
                    '{"schema":NaN,"password":"private-token"}'):
            proc = self.run_cli(e, c, raw=raw)
            self.assertEqual(proc.returncode, 2)
            self.assertEqual(json.loads(proc.stdout)["state"], "INDETERMINATE")
            self.assertNotIn("private-token", proc.stdout + proc.stderr)
        for canonical in (True, False):
            for extra in (("--unexpected", "private-token"),
                          ("--config", "-"), ("--now", "private-token")):
                proc = self.run_cli(e, c, extra, canonical=canonical)
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(json.loads(proc.stdout)["state"], "INDETERMINATE")
                self.assertEqual(proc.stderr, "")
                self.assertNotIn("private-token", proc.stdout)

    def test_raw_error_and_input_secrets_are_never_emitted(self):
        e, c = fixtures()
        e["raw_error"] = "Authorization: Bearer private-token password=hidden"
        for canonical in (True, False):
            proc = self.run_cli(e, c, canonical=canonical)
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stderr, "")
            self.assertNotIn("private-token", proc.stdout)
            self.assertNotIn("hidden", proc.stdout)
            self.check_safe_flags(json.loads(proc.stdout))

    def test_old_control_plan_cli_contract_is_unchanged(self):
        state = repair_control.initial_state()
        state["authorized_tasks"]["META"] = "meta-task"
        data = dict(state=state, kind="META", owner_id=RUN,
                    now=NOW, work_branch="auto/twf-system-review-" + RUN,
                    actor_task_id="meta-task", base_main_sha=A)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plan.json"
            path.write_text(json.dumps(data))
            proc = subprocess.run([sys.executable, str(ROOT / "tools/repair_control.py"),
                                   "plan", "--input", str(path)],
                                  capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout), repair_control.acquire(**data))


if __name__ == "__main__":
    unittest.main()
