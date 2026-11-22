"""Bootstrap regression checks: no downloaded artifact, Luau, or network needed."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
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


if __name__ == "__main__":
    unittest.main()
