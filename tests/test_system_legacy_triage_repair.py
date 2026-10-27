"""Issue72: execute the accepted legacy module/CLI; keep all existing tests."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import system_host_write_triage as legacy
import system_host_write_triage_v2 as versioned
from test_system_host_write_triage import fixtures, holder, operation, NOW, A


class LegacyCompletionRepairTests(unittest.TestCase):
    def check_unhealthy_terminal(self, status):
        evidence, config = fixtures()
        evidence["service"]["data"]["last_run"]["recorded_status"] = status
        value = legacy.classify(evidence, config, NOW)
        self.assertEqual(value["state"], "INDETERMINATE")
        self.assertEqual(value["reason"], "SERVICE_NOT_SUCCESSFULLY_COMPLETED")
        self.assertFalse(value["safe_to_next_schedule"])
        self.assertEqual(value, versioned.classify(evidence, config, NOW))
        for key in ("write_authorized", "start_now_allowed", "takeover_allowed"):
            self.assertIs(value[key], False)

    def test_failed_exact_head_green_qa_cannot_be_healthy(self):
        self.check_unhealthy_terminal("failed")

    def test_no_update_exact_head_green_qa_cannot_be_healthy(self):
        self.check_unhealthy_terminal("no_update")

    def test_completed_healthy_result_is_preserved_without_input_mutation(self):
        evidence, config = fixtures()  # Generic example/second-game.
        before = deepcopy((evidence, config))
        value = legacy.classify(evidence, config, NOW)
        self.assertEqual(value["state"], "SAFE_TO_NEXT_SCHEDULE")
        self.assertEqual(value["reason"], "TERMINAL_IDLE_EXACT_RUN_HEAD_QA_SUCCESS")
        self.assertTrue(value["safe_to_next_schedule"])
        self.assertEqual(value, versioned.classify(evidence, config, NOW))
        self.assertEqual((evidence, config), before)
        self.assertFalse(value["write_authorized"])

    def test_diagnostic_priority_and_binding_are_preserved(self):
        cases = []
        for status in ("completed", "failed", "no_update"):
            e, c = fixtures()
            holder(e)
            e["service"]["data"]["last_run"]["recorded_status"] = status
            cases.append(("active-" + status, e, c, "ACTIVE_LEASE", "JOIN_EXISTING_WRITER"))
        for status in ("failed", "no_update"):
            e, c = fixtures()
            holder(e, expired=True)
            e["service"]["data"]["last_run"]["recorded_status"] = status
            e["holder_service"] = deepcopy(e["service"])
            cases.append(("orphan-" + status, e, c, "WRITER_EXITED_WITHOUT_RELEASE",
                          "EXACT_OWNER_TERMINAL_EVIDENCE_RECOVERY_REVIEW_REQUIRED"))
        for layer, code, state, reason in (
            ("host", "HOST_WRITE_DENIED", "HOST_WRITE_DENIED", "PROVIDER_HOST_REJECTION_OBSERVED"),
            ("github", "EXPECTED_SHA_MISMATCH", "REF_RACE", "EXPECTED_REF_CHANGED_REREAD_REQUIRED"),
            ("host", "unrecognized", "INDETERMINATE", "UNRECOGNIZED_OPERATION_FAILURE"),
        ):
            e, c = fixtures()
            operation(e, outcome="failure", layer=layer, code=code)
            cases.append((code, e, c, state, reason))
        e, c = fixtures()
        e["ci"]["data"]["head"] = A
        for job in e["ci"]["data"]["jobs"]:
            job["head"] = A
        cases.append(("old-head", e, c, "INDETERMINATE", "RUN_OR_HEAD_OR_BASE_QA_BINDING_MISMATCH"))
        for status in ("completed", "failed", "no_update"):
            e, c = fixtures()
            e["service"]["data"]["last_run"]["recorded_status"] = status
            e["ci"]["data"].update(status="queued", conclusion=None, jobs=[])
            cases.append(("pending-" + status, e, c, "WAIT_CI", "EXACT_RUN_HEAD_QA_PENDING"))
        e, c = fixtures()
        e["ci"]["data"]["conclusion"] = "failure"
        cases.append(("failed-qa", e, c, "INDETERMINATE", "QA_FAILED_OR_INCOMPLETE"))
        e, c = fixtures()
        e["service"]["data"]["last_run"].update(recorded_status="in_progress", completed_at=None)
        cases.append(("running", e, c, "INDETERMINATE", "SERVICE_IN_PROGRESS_DO_NOT_START_DUPLICATE"))
        e, c = fixtures()
        holder(e, expired=True)
        e["holder_service"] = deepcopy(e["service"])
        e["holder_service"]["data"]["last_run"].update(recorded_status="in_progress", completed_at=None)
        cases.append(("expiry-only", e, c, "INDETERMINATE", "EXPIRY_IS_NOT_TAKEOVER_EVIDENCE"))
        e, c = fixtures()
        operation(e, stage="create_commit")
        cases.append(("commit-only", e, c, "INDETERMINATE", "COMMIT_OR_REF_RESPONSE_WITHOUT_CONFIRMED_CLAIM"))
        e, c = fixtures()
        e["lock"]["source"]["provider"] = "forged"
        cases.append(("fake-source", e, c, "INDETERMINATE", "INVALID_OR_MISSING_EVIDENCE"))
        self.assertEqual(len(cases), 17)
        for label, evidence, config, state, reason in cases:
            with self.subTest(case=label):
                before = deepcopy((evidence, config))
                value = legacy.classify(evidence, config, NOW)
                self.assertEqual((value["state"], value["reason"]), (state, reason))
                self.assertEqual(value, versioned.classify(evidence, config, NOW))
                self.assertFalse(value["safe_to_next_schedule"])
                for key in ("write_authorized", "start_now_allowed", "takeover_allowed"):
                    self.assertIs(value[key], False)
                self.assertEqual((evidence, config), before)

    def test_original_cli_and_both_versioned_entrypoints_agree(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence_path, config_path = Path(tmp) / "e.json", Path(tmp) / "c.json"
            for status, expected, code in (
                ("completed", "SAFE_TO_NEXT_SCHEDULE", 0),
                ("failed", "INDETERMINATE", 2),
                ("no_update", "INDETERMINATE", 2),
            ):
                evidence, config = fixtures()
                evidence["service"]["data"]["last_run"]["recorded_status"] = status
                evidence["raw_error"] = "Authorization: Bearer private-token password=hidden"
                evidence_path.write_text(json.dumps(evidence))
                config_path.write_text(json.dumps(config))
                expected_result = legacy.classify(evidence, config, NOW)
                for entry in (
                    ["system_host_write_triage.py"],
                    ["system_host_write_triage_v2.py"],
                    ["repair_control.py", "triage"],
                ):
                    with self.subTest(service=status, entry=entry):
                        cmd = [sys.executable, str(ROOT / "tools" / entry[0]), *entry[1:],
                               "--config", str(config_path), "--evidence", str(evidence_path), "--now", NOW]
                        proc = subprocess.run(cmd, capture_output=True, text=True)
                        self.assertEqual(proc.returncode, code)
                        self.assertEqual(proc.stderr, "")
                        result = json.loads(proc.stdout)
                        self.assertEqual(result["state"], expected)
                        self.assertEqual(result, expected_result)
                        self.assertEqual(result, versioned.classify(evidence, config, NOW))
                        self.assertNotIn("private-token", proc.stdout)
                        self.assertNotIn("hidden", proc.stdout)


if __name__ == "__main__":
    unittest.main()
