"""Bootstrap regression checks: no downloaded artifact, Luau, or network needed."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
PACKAGE = REPO / "quality_gameplay/gq487_relay_score_real69_20261122"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load granted regression dependency: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def synthetic_parent_context():
    """Typed caller input, not an observed GitHub run or artifact dependency."""
    return {
        "kind": "PR_CANDIDATE", "build_head": "a" * 40, "checkout_sha": "a" * 40,
        "canonical_build": False, "official_build_head": None,
        "observed_live_rc": "b" * 40, "event": "pull_request",
        "run_id": "12345", "run_attempt": "1",
    }


class ScoreRelayBootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.producer = load_module("gq487_producer_bootstrap_tests", PACKAGE / "compose_score_relay.py")
        cls.native = load_module("gq487_native_bootstrap_tests", PACKAGE / "native/run_regressions.py")
        cls.lock = cls.producer.load_lock()
        cls.baseline = cls.lock["baseline_source_text"].encode("utf-8")

    def test_exact_existing_repair_and_actual_inverse_preserve_current_rare_source(self):
        self.assertEqual(len(self.baseline), 8030)
        self.assertEqual(hashlib.sha256(self.baseline).hexdigest(), "ef0c1bf657ecf9fb8883036b114e0a19bb6def86b46dec1b6f8b11ccb94662a9")
        after = self.producer.transform_score(self.baseline, "on")
        self.assertEqual(len(after), 8741)
        self.assertEqual(hashlib.sha256(after).hexdigest(), "67c76c12cc4d311847fb1cf794988b2f164053690660f6b55f4e590f93824136")
        self.assertEqual(self.producer.transform_score(after, "off"), self.baseline)

    def test_changed_rare_rate_is_rejected_before_insertion(self):
        changed = self.baseline.replace(b"RARE_FIELD_EGG_RATE=60", b"RARE_FIELD_EGG_RATE=61", 1)
        self.assertNotEqual(changed, self.baseline)
        with self.assertRaisesRegex(self.producer.ScoreRelayError, "ON_INPUT_SOURCE_PIN"):
            self.producer.transform_score(changed, "on")

    def test_existing_repair_cannot_be_applied_twice(self):
        after = self.producer.transform_score(self.baseline, "on")
        with self.assertRaisesRegex(self.producer.ScoreRelayError, "ON_INPUT_SOURCE_PIN"):
            self.producer.transform_score(after, "on")

    def test_inverse_rejects_changed_after_source(self):
        after = self.producer.transform_score(self.baseline, "on")
        with self.assertRaisesRegex(self.producer.ScoreRelayError, "OFF_INPUT_SOURCE_PIN"):
            self.producer.transform_score(after + b"\n", "off")

    def test_unknown_transform_direction_fails_closed(self):
        with self.assertRaisesRegex(self.producer.ScoreRelayError, "DIRECTION"):
            self.producer.transform_score(self.baseline, "unknown")

    def test_missing_generated_input_leaves_no_produced_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "not-produced"
            with self.assertRaisesRegex(self.producer.ScoreRelayError, "INPUT_ROOT"):
                self.producer.compose(root / "missing-input", output, "on")
            self.assertFalse(output.exists())

    def test_native_refuses_unproduced_input_before_any_process(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with mock.patch.object(self.native.subprocess, "run", side_effect=AssertionError("Native subprocess forbidden in bootstrap tests")) as process:
                receipt = self.native.run_regressions(
                    root / "missing-stage", root / "missing-luau", root / "missing-compiler", root / "native-output"
                )
            self.assertEqual(receipt["status"], "SOURCE_ONLY_NATIVE_FAIL")
            self.assertEqual(receipt["native_invocations"], 0)
            self.assertFalse(receipt["native_pass"])
            self.assertIn("INPUT_ROOT", receipt["error"]["message"])
            process.assert_not_called()
            self.assertTrue((root / "native-output/native_receipt.json").is_file())

    def test_native_never_overwrites_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "existing-output"
            output.mkdir()
            sentinel = output / "retained.txt"
            sentinel.write_bytes(b"keep prior evidence\n")
            with mock.patch.object(self.native.subprocess, "run", side_effect=AssertionError("Native subprocess forbidden in bootstrap tests")) as process:
                with self.assertRaisesRegex(ValueError, "fresh directory"):
                    self.native.run_regressions(root / "stage", root / "luau", root / "compiler", output)
            self.assertEqual(sentinel.read_bytes(), b"keep prior evidence\n")
            self.assertEqual(sorted(p.name for p in output.iterdir()), ["retained.txt"])
            process.assert_not_called()

    def test_frozen_spec_hash_mismatch_is_rejected(self):
        lock = copy.deepcopy(self.lock)
        lock["native"]["specs"]["score_v2"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Pinned Native spec bytes drift"):
            self.native.native_inputs(lock)

    def test_toolchain_receipt_with_wrong_binary_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            luau, compiler = root / "tool-fixture-a", root / "tool-fixture-b"
            luau.write_bytes(b"non-executable bootstrap fixture A")
            compiler.write_bytes(b"non-executable bootstrap fixture B")
            receipt = root / "receipt.json"
            receipt.write_text(json.dumps({
                "luau_source_commit": self.native.PINNED_LUAU_COMMIT,
                "tool_sha256": {"luau": "0" * 64, "luau-compile": self.native.file_info(compiler)["sha256"]},
            }))
            with self.assertRaisesRegex(ValueError, "binary hash mismatch: luau"):
                self.native.toolchain_record(luau, compiler, receipt)

    def test_missing_toolchain_receipt_never_claims_source_commit_or_gate_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            luau, compiler = root / "tool-fixture-a", root / "tool-fixture-b"
            luau.write_bytes(b"non-executable bootstrap fixture A")
            compiler.write_bytes(b"non-executable bootstrap fixture B")
            record = self.native.toolchain_record(luau, compiler, None)
            self.assertEqual(record["source_commit"], "UNKNOWN")
            self.assertFalse(record["local_toolchain_gate_ready"])
            self.assertFalse(record["provider_attestation_verified"])
            self.assertEqual(record["binaries"]["luau"], self.native.file_info(luau))


    def test_native_parent_mode_errors_do_not_start_artifact_or_process_work(self):
        for kind, context, message in (
            ("UNION22_DELIVERY", None, "requires external expected_parent_context"),
            ("FROZEN_LOCAL", synthetic_parent_context(), "forbids expected_parent_context"),
            ("UNKNOWN", None, "Unknown parent_kind"),
        ):
            with self.subTest(parent_kind=kind), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with mock.patch.object(self.native, "load_producer", side_effect=AssertionError("mode error must precede artifact work")) as loader:
                    with mock.patch.object(self.native.subprocess, "run", side_effect=AssertionError("bootstrap subprocess forbidden")) as process:
                        receipt = self.native.run_regressions(
                            root / "absent-stage", root / "absent-vm", root / "absent-compiler", root / "output",
                            parent_kind=kind, expected_parent_context=context,
                        )
                self.assertEqual(receipt["status"], "SOURCE_ONLY_NATIVE_FAIL")
                self.assertEqual(receipt["native_invocations"], 0)
                self.assertIn(message, receipt["error"]["message"])
                loader.assert_not_called()
                process.assert_not_called()

    def test_union_stage_rejection_never_retries_as_frozen(self):
        context = synthetic_parent_context()
        rejected = mock.Mock(side_effect=ValueError("UNION_ADMISSION_REJECTED_BY_TEST_BOUNDARY"))
        boundary = SimpleNamespace(load_lock=lambda: self.lock, verify_stage=rejected)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with mock.patch.object(self.native, "load_producer", return_value=boundary):
                with mock.patch.object(self.native.subprocess, "run", side_effect=AssertionError("bootstrap subprocess forbidden")) as process:
                    receipt = self.native.run_regressions(
                        root / "absent-stage", root / "absent-vm", root / "absent-compiler", root / "output",
                        parent_kind="UNION22_DELIVERY", expected_parent_context=context,
                    )
            self.assertEqual(receipt["status"], "SOURCE_ONLY_NATIVE_FAIL")
            self.assertEqual(receipt["native_invocations"], 0)
            self.assertIn("UNION_ADMISSION_REJECTED_BY_TEST_BOUNDARY", receipt["error"]["message"])
            rejected.assert_called_once_with(
                (root / "absent-stage").resolve(), "after", parent_kind="UNION22_DELIVERY",
                expected_parent_context=context,
            )
            process.assert_not_called()

    def test_stage_sidecar_drift_after_semantic_validation_cannot_set_a_new_pin(self):
        """Real sidecar files/JSON/receipt checks; payload and parent proof mocked.

        This is the independent timing-specific counterexample: change a checked
        sidecar and its receipt link immediately after semantic validation. The
        original validated raw bytes must remain the receipt's expected pins.
        No real69/110 artifact, native runtime, or production source is needed.
        """
        p = self.producer
        context = synthetic_parent_context()
        snapshot = {
            "profile": "after", "source_count": 69,
            "sources": {name: {**row, "mode": 0o644}
                        for name, row in p.expected_sources(self.lock, "after").items()},
            "project": copy.deepcopy(self.lock["fixed_input"]["project"]),
            "project_mode": 0o644, "source_lock_sha256": self.lock["_lock_sha256"],
        }
        before_snapshot = copy.deepcopy(snapshot)
        before_snapshot["profile"] = "before"
        before_snapshot["sources"][p.TARGET].update(bytes=8030, sha256=p.BASE_SHA)
        packet = {"raw": {"bootstrap-only.txt": b"MOCKED_PARENT_PAYLOAD"},
                  "modes": {"bootstrap-only.txt": 0o644}}
        binding = {"payload": p.union_payload_identity(packet),
                   "expected_execution_context": copy.deepcopy(context),
                   "boundary": "MOCKED_PARENT_CONTENT_PROOF_NOT_REAL_DELIVERY"}
        real_parent_check = p.verify_stage_parent
        real_receipt_check = p.verify_receipt_metadata
        for fault in (None, "expectation", "binding"):
            with self.subTest(sidecar=fault or "unchanged_control"), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                binding_raw = p.json_bytes(binding)
                expectation_raw = p.json_bytes({
                    "schema": "SCORE_RELAY_EXTERNAL_PARENT_EXPECTATION_V1",
                    "expected_execution_context": context,
                })
                manifest_raw = p.json_bytes({"schema": "SCORE_RELAY_PREP_SOURCE_MANIFEST_V1",
                                             "status": p.STATUS, **snapshot})
                (root / p.PARENT_BINDING).write_bytes(binding_raw)
                (root / p.PARENT_EXPECTATION).write_bytes(expectation_raw)
                (root / p.MANIFEST).write_bytes(manifest_raw)
                receipt = {
                    "schema": "SCORE_RELAY_PREP_RECEIPT_V3", "status": p.STATUS,
                    "created_at_utc": "2026-11-22T00:00:00+00:00", "direction": "on",
                    "input_profile": "before", "output_profile": "after",
                    "input_snapshot": before_snapshot, "output_snapshot": snapshot,
                    "only_changed_source": p.TARGET, "source_count": 69, "other_sources_preserved": 68,
                    "source_lock_sha256": self.lock["_lock_sha256"], "parent_manifest": None,
                    "parent_kind": "UNION22_DELIVERY", "expected_parent_context": context,
                    "parent_binding": p.info(binding_raw), "parent_expectation": p.info(expectation_raw),
                    "parent_contract_verified": True, "manifest": p.info(manifest_raw),
                    "inverse_reads_actual_on_source": False,
                    "parent_stage_receipt": None, "parent_stage_manifest": None,
                    "Native_executed_by_composer": False, "Place_built_by_composer": False,
                    "RC_adopted_by_composer": False, "Studio_Android_ART_FUN": "NOT_VERIFIED",
                    **p.OWN_UNPROVEN,
                }
                (root / p.RECEIPT).write_bytes(p.json_bytes(receipt))
                crossed_semantic_boundary = []

                def after_semantic_check(actual_root, parent_kind, expected_context):
                    # Run actual JSON parsing, strict context equality and raw
                    # sidecar binding checks before injecting the filesystem drift.
                    validated = real_parent_check(actual_root, parent_kind, expected_context)
                    crossed_semantic_boundary.append(True)
                    if fault is not None:
                        name = p.PARENT_EXPECTATION if fault == "expectation" else p.PARENT_BINDING
                        sidecar = actual_root / name
                        changed = json.loads(sidecar.read_bytes())
                        changed["expected_execution_context"]["run_id"] = "1"
                        sidecar.write_bytes(p.json_bytes(changed))
                        own_receipt = json.loads((actual_root / p.RECEIPT).read_bytes())
                        own_receipt["parent_" + fault] = p.info(sidecar.read_bytes())
                        (actual_root / p.RECEIPT).write_bytes(p.json_bytes(own_receipt))
                    return validated

                with mock.patch.object(p, "validate_sources", return_value=snapshot), \
                     mock.patch.object(p, "snapshot_union_delivery", return_value=packet), \
                     mock.patch.object(p, "verify_union_parent", return_value=binding), \
                     mock.patch.object(p, "verify_stage_parent", side_effect=after_semantic_check) as boundary, \
                     mock.patch.object(p, "verify_receipt_metadata", wraps=real_receipt_check) as receipt_check:
                    if fault is None:
                        result = p.verify_stage(root, "after", parent_kind="UNION22_DELIVERY",
                                                expected_parent_context=context)
                        self.assertTrue(result["parent_contract_verified"])
                        self.assertEqual(result["parent_binding"], p.info(binding_raw))
                        self.assertEqual(result["parent_expectation"], p.info(expectation_raw))
                    else:
                        with self.assertRaisesRegex(p.ScoreRelayError, "STAGE_PARENT_BINDING_OR_UNEARNED_CLAIM"):
                            p.verify_stage(root, "after", parent_kind="UNION22_DELIVERY",
                                           expected_parent_context=context)
                    boundary.assert_called_once()
                    receipt_check.assert_called_once()
                self.assertEqual(crossed_semantic_boundary, [True])

    def test_orchestration_rejects_drift_in_executed_and_archived_copies(self):
        """Actual runner and file I/O, mocked stage gate/processes; zero artifact/VM.

        Controls prove fake successful process returns can reach PASS. Drift
        cases exercise actual copy checks. Union cases also verify both explicit
        parent-context handoffs; these are not Native/gameplay execution counts.
        """
        after = self.producer.transform_score(self.baseline, "on")
        scenarios = (
            ("unchanged_control", None, 8, 2),
            ("results_during_compile", "after compile score_v2/Results.luau", 1, 0),
            ("cases_during_compile", "after compile score_v2/Results.luau", 1, 0),
            ("runner_during_native", "after Native score_v2", 4, 1),
            ("archive_after_last_native", "final execution_inputs archive", 8, 2),
            ("receipt_after_last_native", "final provided_toolchain_receipt copy", 8, 2),
            ("union_dict_control", None, 8, 2),
            ("union_wrapper_file_control", None, 8, 2),
            ("union_context_input_drift", "final external parent expectation input", 8, 2),
            ("union_context_copy_drift", "final execution_inputs archive", 8, 2),
        )
        for scenario, failure_boundary, expected_calls, expected_native_calls in scenarios:
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                stage, output = root / "mocked-stage", root / "mocked-output"
                score_path = stage / "sources" / self.native.SCORE_PATH
                score_path.parent.mkdir(parents=True)
                score_path.write_bytes(after)
                luau, compiler = root / "mock-luau", root / "mock-compiler"
                luau.write_bytes(b"Non-executable fixture; mocked subprocess only")
                compiler.write_bytes(b"Non-executable compiler fixture; mocked subprocess only")
                provided = root / "mock-build-receipt.json"
                provided.write_text(json.dumps({
                    "luau_source_commit": self.native.PINNED_LUAU_COMMIT,
                    "tool_sha256": {
                        "luau": self.native.file_info(luau)["sha256"],
                        "luau-compile": self.native.file_info(compiler)["sha256"],
                    },
                    "boundary": "MOCKED_BOOTSTRAP_NOT_A_BUILD_RECEIPT",
                }))
                identity = {"source_count": 69, "sources": copy.deepcopy(self.lock["input_sources"])}
                identity["sources"][self.native.SCORE_PATH].update(self.native.SCORE_AFTER)
                is_union = scenario.startswith("union_")
                kind = "UNION22_DELIVERY" if is_union else "FROZEN_LOCAL"
                expected_context = synthetic_parent_context() if is_union else None
                caller_context = copy.deepcopy(expected_context)
                context_path = root / "external-parent-context.json"
                context_raw = None
                if is_union and scenario != "union_dict_control":
                    payload = expected_context
                    if scenario == "union_wrapper_file_control":
                        payload = {
                            "schema": "SCORE_RELAY_EXTERNAL_PARENT_EXPECTATION_V1",
                            "expected_execution_context": expected_context,
                            "origin_observation": {"note": "SYNTHETIC_DIAGNOSTIC_ONLY"},
                        }
                    context_raw = (json.dumps(payload, indent=2) + "\n").encode()
                    context_path.write_bytes(context_raw)
                    caller_context = context_path
                verify_calls = []

                def verify_boundary(actual_root, profile, *, parent_kind, expected_parent_context):
                    verify_calls.append((actual_root, profile, parent_kind, copy.deepcopy(expected_parent_context)))
                    if scenario == "union_dict_control":
                        # A callee cannot mutate the runner's saved expectation.
                        expected_parent_context["run_id"] = "99999"
                    return {"boundary": "MOCKED_GATE_NO_GENERATED_ARTIFACT"}

                mocked_producer = SimpleNamespace(
                    load_lock=lambda: self.lock,
                    verify_stage=verify_boundary,
                    validate_sources=lambda *_: identity,
                    read_parent_expectation=lambda path: self.producer.read_parent_expectation(path),
                )

                def fake_process(argv, *, cwd, capture_output, timeout, check):
                    self.assertTrue(capture_output)
                    self.assertEqual(timeout, 30)
                    self.assertFalse(check)
                    is_native = "--null" not in argv
                    variant = Path(cwd).name
                    target = None
                    if variant == "score_v2" and not is_native and argv[-1] == "Results.luau":
                        if scenario == "results_during_compile":
                            target = Path(cwd) / "Results.luau"
                        elif scenario == "cases_during_compile":
                            target = Path(cwd) / "Cases.luau"
                        elif scenario == "union_dict_control":
                            # Caller mutation after admission must not replace
                            # the expectation used by the final stage verifier.
                            caller_context["run_id"] = "77777"
                    if variant == "score_v2" and is_native and scenario == "runner_during_native":
                        target = Path(cwd) / "Runner.luau"
                    if variant == "relay_original" and is_native:
                        if scenario == "archive_after_last_native":
                            target = output / "execution_inputs/native/run_regressions.py"
                        elif scenario == "receipt_after_last_native":
                            target = output / "provided_toolchain_receipt.json"
                        elif scenario == "union_context_input_drift":
                            target = context_path
                        elif scenario == "union_context_copy_drift":
                            target = output / "execution_inputs/external_parent_context.json"
                    if target is not None:
                        # Whitespace leaves Lua/Python/JSON meaning intact but
                        # invalidates the exact bytes claimed by the receipt.
                        target.write_bytes(target.read_bytes() + b"\n ")
                    stdout = b""
                    if is_native:
                        stdout = ("MOCKED PROCESS; NO NATIVE EXECUTION\n" +
                                  self.native.SPEC_CONTRACTS[variant]["marker"] + "\n" +
                                  self.native.ENTRY_MARKER + "\n").encode()
                    return self.native.subprocess.CompletedProcess(argv, 0, stdout, b"")

                with mock.patch.object(self.native, "load_producer", return_value=mocked_producer):
                    with mock.patch.object(self.native.subprocess, "run", side_effect=fake_process) as process:
                        receipt = self.native.run_regressions(
                            stage, luau, compiler, output, provided,
                            parent_kind=kind, expected_parent_context=caller_context,
                        )
                self.assertEqual(process.call_count, expected_calls)
                self.assertEqual(receipt["native_invocations"], expected_native_calls)
                self.assertTrue(receipt["stage_files_unchanged"])
                self.assertTrue(receipt["code_and_lock_unchanged"])
                self.assertTrue(receipt["tool_binaries_unchanged"])
                self.assertEqual(verify_calls, [(stage.resolve(), "after", kind, expected_context)] * 2)
                self.assertEqual(receipt["parent_kind"], kind)
                self.assertEqual(receipt["expected_parent_context"], expected_context)
                self.assertFalse(receipt["parent_origin_attestation_verified"])
                if context_raw is not None:
                    self.assertEqual(
                        {key: receipt["external_parent_context_input"][key] for key in ("bytes", "sha256")},
                        self.native.byte_info(context_raw),
                    )
                    if scenario != "union_context_copy_drift":
                        self.assertEqual((output / "execution_inputs/external_parent_context.json").read_bytes(), context_raw)
                if scenario == "union_dict_control":
                    self.assertEqual(caller_context["run_id"], "77777")
                if failure_boundary is None:
                    self.assertEqual(receipt["status"], "SOURCE_ONLY_NATIVE_PASS")
                    self.assertTrue(receipt["native_pass"])
                    self.assertTrue(receipt["local_native_gate_ready"])
                else:
                    self.assertEqual(receipt["status"], "SOURCE_ONLY_NATIVE_FAIL")
                    self.assertFalse(receipt["native_pass"])
                    self.assertFalse(receipt["local_native_gate_ready"])
                    error = receipt.get("error", receipt.get("postflight_error", receipt.get("copy_postflight_error", {})))
                    self.assertIn("Copy integrity failure", error.get("message", ""))
                    self.assertIn(failure_boundary, error["message"])


if __name__ == "__main__":
    unittest.main()
