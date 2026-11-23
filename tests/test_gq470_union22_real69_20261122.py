#!/usr/bin/env python3
"""Focused fail-closed controls for the additional union boundary.

Repository discovery without UNION22_TEST_* runs artifact-free contracts.
Explicit core/final integration requires actual workflow outputs and runs the
complete fixed suite; missing context never becomes a skip or an empty PASS.
"""
from __future__ import annotations

import copy
from contextlib import redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
HERE = REPO / "quality_gameplay/gq470_union22_real69_20261122"
sys.path.insert(0, str(HERE))
import compose_union22 as compose
import verify_union22 as verify
spec = importlib.util.spec_from_file_location("union22_native_tests", HERE / "native/run_profile.py")
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


ARTIFACT_ENV = ("UNION22_TEST_PRIOR", "UNION22_TEST_REPORTS", "UNION22_TEST_ROOT",
                "UNION22_TEST_NATIVE", "UNION22_TEST_STAGE")
INTEGRATION_COUNTS = {"core": 42, "final": 9}


def artifact_environment(expected_stage=None):
    supplied = {key: value for key, value in os.environ.items() if key.startswith("UNION22_TEST_")}
    if set(supplied) - set(ARTIFACT_ENV):
        raise ValueError("RED_UNION22_UNKNOWN_TEST_ENVIRONMENT")
    stage = supplied.get("UNION22_TEST_STAGE", "core")
    if stage not in INTEGRATION_COUNTS or expected_stage is not None and stage != expected_stage:
        raise ValueError("RED_UNION22_UNKNOWN_OR_MISMATCHED_TEST_STAGE")
    required = ARTIFACT_ENV[:3] + (("UNION22_TEST_NATIVE",) if stage == "final" else ())
    missing = [key for key in required if not supplied.get(key, "").strip()]
    if missing:
        raise ValueError("RED_UNION22_MISSING_ARTIFACT_CONTEXT:" + ",".join(missing))
    paths = {key: Path(supplied[key]).resolve() for key in ARTIFACT_ENV[:4] if key in supplied}
    for key, path in paths.items():
        if not supplied[key].strip() or not path.is_dir():
            raise ValueError("RED_UNION22_ARTIFACT_DIRECTORY_MISSING:" + key)
    return stage, paths


def checked_suite(loader, case, expected_count):
    suite = loader.loadTestsFromTestCase(case)
    if suite.countTestCases() != expected_count:
        raise ValueError("RED_UNION22_INCOMPLETE_TEST_SELECTION")
    return suite


class UnionBoundary(unittest.TestCase):
    ARTIFACT_STAGE = "core"

    @classmethod
    def setUpClass(cls):
        _, paths = artifact_environment(cls.ARTIFACT_STAGE)
        cls.prior = paths["UNION22_TEST_PRIOR"]
        cls.reports = paths["UNION22_TEST_REPORTS"]
        cls.current = paths["UNION22_TEST_ROOT"]
        cls.lock = compose.load_lock()
        cls.native_lock = native.load_lock()
        cls.context = verify.data(cls.current / "CORE_BUILD_REPORT.json")["context"]
        cls.first = next(iter(cls.lock["sources"]))
        # Missing or invalid artifacts must fail before a negative test can
        # mistake that setup failure for the particular rejection it exercises.
        verify.verify_core(cls.current, cls.prior, cls.reports, cls.context)

    def temporary(self):
        context = tempfile.TemporaryDirectory(prefix="union22-negative-")
        self.addCleanup(context.cleanup)
        return Path(context.name)

    def prior_copy(self):
        dest = self.temporary() / "prior"
        dest.mkdir()
        for name in (compose.PROJECT, compose.PLACE, compose.RECEIPT):
            shutil.copyfile(self.prior / name, dest / name)
        shutil.copytree(self.prior / "sources", dest / "sources")
        for name in self.lock["prior_report_names"] + self.lock["prior_opaque_rollback_names"]:
            shutil.copyfile(self.reports / name, dest / name)
        return dest

    def current_copy(self):
        dest = self.temporary() / "current"
        shutil.copytree(self.current, dest)
        return dest

    def reject_core(self, root):
        with self.assertRaises(ValueError):
            verify.verify_core(root, self.prior, self.reports, self.context)
        self.assertFalse((root / "delivery").exists())

    def test_actual_parent_and_core(self):
        result = verify.verify_core(self.current, self.prior, self.reports, self.context)
        self.assertEqual(len(result["current"]["sources"]), 69)
        self.assertEqual(len(result["archive_members"]), 75)

    def test_original_39_workflow_step_payloads_byte_exact(self):
        workflow = (REPO / ".github/workflows/gq8-real63-source-composite.yml").read_bytes().decode("utf-8")
        # Only the reviewed original-input transport changes; invert it before
        # checking the unchanged historical 39-step contract.
        old_transport = (
            '          mkdir -p /tmp/gq863/{base55,hud59,trade62,formal62,formal63,viral56,counter56}\n'
            '          gh run download 44393525211 --repo "$GITHUB_REPOSITORY" --name P0D-EGGRUMBLE-V3-REAL55-CANONICAL-PRIVATE-STUDIO --dir /tmp/gq863/base55\n'
            '          gh run download 44401178585 --repo "$GITHUB_REPOSITORY" --name P0D-EGGRUMBLE-V3-REAL59-HUD-MAP-CANONICAL-PRIVATE-STUDIO --dir /tmp/gq863/hud59\n'
            '          gh run download 44402402944 --repo "$GITHUB_REPOSITORY" --name GQ8-REAL62-HUD59-TRADE3-PRIVATE-NOT-OFFICIAL --dir /tmp/gq863/trade62\n'
            '          gh run download 44404334603 --repo "$GITHUB_REPOSITORY" --name P0D-EGGRUMBLE-V3-REAL62-HUD-TRADE-PRIVATE-STUDIO --dir /tmp/gq863/formal62\n'
            '          gh run download 44413796990 --repo "$GITHUB_REPOSITORY" --name P0D-EGGRUMBLE-V3-REAL63-BASIC-DODGE-CANONICAL-PRIVATE-STUDIO --dir /tmp/gq863/formal63\n'
            '          gh run download 44398710101 --repo "$GITHUB_REPOSITORY" --name GQ8-REAL56-VIRAL-CAPTURE-PRIVATE-NOT-OFFICIAL --dir /tmp/gq863/viral56\n'
            '          gh run download 44397387116 --repo "$GITHUB_REPOSITORY" --name GQ822-REAL56-CURRENT-FORMAL55-COUNTER-PRIVATE-NOT-OFFICIAL --dir /tmp/gq863/counter56\n'
        )
        new_transport = '          python3 -B quality_gameplay/gq8_real63_intake_20261119/restore_original_inputs.py --out /tmp/gq863\n'
        original = {"bytes": 106837,
                    "sha256": "0ab1ece54d56747dd655146ef3f4425ab2ad0346bd9843956a9d6dcd532cd039"}

        def check_original_prefix(candidate):
            self.assertEqual(candidate.count(new_transport), 1)
            self.assertNotIn(old_transport, candidate)
            prefix = candidate.split("    steps:\n", 1)[1].split(
                '      - name: "Union22: exact existing hunks after the unchanged BR-only prior boundary"\n', 1)[0]
            self.assertEqual(prefix.count(new_transport), 1)
            restored = prefix.replace(new_transport, old_transport, 1)
            self.assertEqual(compose.identity(restored.encode()), original)

        check_original_prefix(workflow)
        self.assertEqual(workflow.count("path: artifacts/real69_union22/delivery/"), 1)
        # Historical bytes, loader commands and multiplicity are exact; even a
        # physical LF-to-CRLF change must fail the inverse contract.
        mutations = {
            "historical_head": workflow.replace(
                "44393525211:a6020867fac80fa3b2ca47478625873fc6f3678e",
                "44393525211:b6020867fac80fa3b2ca47478625873fc6f3678e", 1),
            "loader_output": workflow.replace("--out /tmp/gq863\n", "--out /tmp/gq863x\n", 1),
            "duplicate_loader": workflow.replace(new_transport, new_transport * 2, 1),
            "prefix_crlf": workflow.replace("          set -euo pipefail\n", "          set -euo pipefail\r\n", 1),
        }
        for label, mutated in mutations.items():
            with self.subTest(mutation=label):
                self.assertNotEqual(mutated, workflow)
                with self.assertRaises(AssertionError):
                    check_original_prefix(mutated)

    def test_actual_final_retention(self):
        result = verify.verify_core(self.current, self.prior, self.reports, self.context)
        reports = verify.retention_reports(self.current, result, self.context)
        self.assertEqual(reports["UNION22_FINAL_17_MARKER_RETENTION.json"]["source_family_marker_count"], 17)
        self.assertEqual(reports["UNION22_FINAL_ALL48_RAW.json"]["original_legacy_flags"], 48)

    def test_dynamic_actual_receipt_not_whole_hash_pinned(self):
        root = self.prior_copy()
        receipt = verify.data(root / compose.RECEIPT)
        receipt["test_only_distinct_receipt_metadata"] = "same exact prior profile"
        compose.write_json(root / compose.RECEIPT, receipt)
        result = compose.load_inputs(root, root)
        self.assertNotEqual(result["receipt_raw"], (self.prior / compose.RECEIPT).read_bytes())
        self.assertEqual(len(result["sources"]), 69)

    def test_unknown_prior_source_rejected(self):
        root = self.prior_copy()
        path = root / "sources" / self.first
        path.write_bytes(path.read_bytes() + b"\n-- unknown change\n")
        with self.assertRaises(ValueError):
            compose.load_inputs(root, root)

    def test_extra_prior_source_rejected(self):
        root = self.prior_copy()
        (root / "sources/extra.luau").write_text("return {}\n")
        with self.assertRaises(ValueError):
            compose.load_inputs(root, root)

    def test_unknown_prior_place_rejected(self):
        root = self.prior_copy()
        path = root / compose.PLACE
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaises(ValueError):
            compose.load_inputs(root, root)

    def test_prior_root_symlink_rejected(self):
        link = self.temporary() / "link"
        link.symlink_to(self.prior, target_is_directory=True)
        with self.assertRaises(ValueError):
            compose.load_inputs(link, link)

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(ValueError):
            compose.strict_json(b'{"canonical_build":false,"canonical_build":true}')

    def test_receipt_source_lie_rejected(self):
        root = self.prior_copy()
        receipt = verify.data(root / compose.RECEIPT)
        receipt["source_hashes"][next(iter(receipt["source_hashes"]))] = "0" * 64
        compose.write_json(root / compose.RECEIPT, receipt)
        with self.assertRaises(ValueError):
            compose.load_inputs(root, root)

    def test_canonical_string_rejected(self):
        root = self.prior_copy()
        receipt = verify.data(root / compose.RECEIPT)
        receipt["canonical_build"] = "true"
        compose.write_json(root / compose.RECEIPT, receipt)
        with self.assertRaises(ValueError):
            compose.load_inputs(root, root)

    def test_context_false_formal_rejected(self):
        context = copy.deepcopy(self.context)
        context.update(kind="PR_CANDIDATE", canonical_build=True, official_build_head=context["build_head"])
        receipt = verify.data(self.prior / compose.RECEIPT)
        with self.assertRaises(ValueError):
            compose.validate_context(context, receipt)

    def test_cli_provenance_has_no_offline_fallback(self):
        receipt = verify.data(self.prior / compose.RECEIPT)
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
            compose.live_context(receipt, receipt["build_head"])

    def test_hunk_removed_bytes_rejected(self):
        hunk = {"start": 0, "stop": 1, "old": "wrong\n", "new": "new\n",
                "old_identity": compose.identity(b"wrong\n"), "new_identity": compose.identity(b"new\n")}
        with self.assertRaises(ValueError):
            compose.apply_hunks(b"actual\n", [hunk])

    def test_hunk_overlap_rejected(self):
        hunk = {"start": 0, "stop": 1, "old": "old\n", "new": "new\n",
                "old_identity": compose.identity(b"old\n"), "new_identity": compose.identity(b"new\n")}
        with self.assertRaises(ValueError):
            compose.apply_hunks(b"old\n", [hunk, hunk])

    def test_double_application_rejected(self):
        root = self.current
        with self.assertRaises(ValueError):
            compose.load_inputs(root, root)

    def late_mutation_control(self, target):
        prior = self.prior_copy()
        output = self.temporary() / "candidate"
        commands = verify.data(self.current / "CORE_BUILD_REPORT.json")["commands"]
        compiler = Path(next(c["command"][0] for c in commands if c["command"][1] == "--text"))
        rojo = Path(next(c["command"][0] for c in commands if c["command"][1] == "build"))
        real_run = compose.run_checked
        calls = 0
        def mutate_after_last_real_build(command, logs, *args, **kwargs):
            nonlocal calls
            result = real_run(command, logs, *args, **kwargs)
            calls += 1
            if calls == 140:
                stage = Path(command[-1]).parent.parent
                path = (prior if target == "input" else stage) / "sources" / self.first
                path.write_bytes(path.read_bytes() + b"\n-- reviewer late mutation control\n")
            return result
        expected = "PRIOR_SOURCE_IDENTITY" if target == "input" else "STAGED_OUTPUT_CHANGED_AFTER_BUILD"
        with patch.object(compose, "run_checked", mutate_after_last_real_build), self.assertRaisesRegex(ValueError, expected):
            compose.build_source_candidate(prior, prior, output, compiler, rojo, self.context)
        self.assertEqual(calls, 140)
        self.assertFalse(output.exists())
        stages = list(output.parent.glob(output.name + ".building-*"))
        self.assertEqual(len(stages), 1)
        self.assertTrue((stages[0] / "FAILED.json").is_file())
        self.assertFalse((stages[0] / "CORE_BUILD_REPORT.json").exists())
        self.assertFalse((stages[0] / compose.RECEIPT).exists())
        self.assertFalse((stages[0] / "delivery").exists())

    def test_late_input_mutation_cannot_leave_success_report(self):
        self.late_mutation_control("input")

    def test_late_staged_source_mutation_cannot_commit(self):
        self.late_mutation_control("stage")

    def test_final_source_mutation_rejected(self):
        root = self.current_copy()
        p = root / "sources" / self.first
        p.write_bytes(p.read_bytes() + b"\n-- unknown final\n")
        self.reject_core(root)

    def test_final_non_source_property_mutation_rejected(self):
        root = self.current_copy()
        p = root / compose.PLACE
        p.write_bytes(p.read_bytes().replace(b'<roblox ', b'<roblox changed="1" ', 1))
        self.reject_core(root)

    def test_final_receipt_formal_lie_rejected(self):
        root = self.current_copy()
        receipt = verify.data(root / compose.RECEIPT)
        receipt["formal_rc_adoption_proven"] = not receipt["formal_rc_adoption_proven"]
        compose.write_json(root / compose.RECEIPT, receipt)
        self.reject_core(root)

    def test_immediate_prior_inverse_drift_rejected(self):
        root = self.current_copy()
        p = root / compose.OFF / "sources" / self.first
        p.write_bytes(p.read_bytes() + b"\n")
        self.reject_core(root)

    def test_opaque_prior_archive_drift_rejected(self):
        root = self.current_copy()
        p = root / "prior_boundary/legacy_rollbacks" / self.lock["prior_opaque_rollback_names"][0]
        p.write_bytes(p.read_bytes() + b"changed")
        self.reject_core(root)

    def test_archive_traversal_rejected(self):
        target = self.temporary() / "escape.tar.gz"
        with tarfile.open(target, "w:gz") as archive:
            info = tarfile.TarInfo(compose.OFF + "/../escape")
            info.size = 1
            archive.addfile(info, io.BytesIO(b"x"))
        with self.assertRaises(ValueError):
            verify.verify_archive(target, {"escape": compose.identity(b"x")})

    def test_archive_duplicate_rejected(self):
        target = self.temporary() / "duplicate.tar.gz"
        with tarfile.open(target, "w:gz") as archive:
            for _ in range(2):
                info = tarfile.TarInfo(compose.OFF + "/one")
                info.size = 1
                archive.addfile(info, io.BytesIO(b"x"))
        with self.assertRaises(ValueError):
            verify.verify_archive(target, {"one": compose.identity(b"x"), "two": compose.identity(b"x")})

    def test_ordinary_readonly_payload_mode_accepted(self):
        root = self.temporary()
        path = root / "regular"
        path.write_bytes(b"x")
        path.chmod(0o444)
        self.assertEqual(compose.read_file(path), b"x")
        self.assertEqual(verify.files(root), {"regular": compose.identity(b"x")})

    def test_special_file_and_payload_directory_modes_rejected(self):
        root = self.temporary()
        path = root / "regular"
        path.write_bytes(b"x")
        path.chmod(0o4644)
        with self.assertRaises(ValueError):
            compose.read_file(path)
        with self.assertRaises(ValueError):
            verify.files(root)
        path.chmod(0o644)
        root.chmod(0o2755)
        with self.assertRaises(ValueError):
            verify.files(root)
        root.chmod(0o755)

    def test_archive_special_permission_bits_rejected(self):
        target = self.temporary() / "special-mode.tar.gz"
        with tarfile.open(target, "w:gz") as archive:
            info = tarfile.TarInfo(compose.OFF + "/one")
            info.size, info.mode = 1, 0o4644
            archive.addfile(info, io.BytesIO(b"x"))
        with self.assertRaises(ValueError):
            verify.verify_archive(target, {"one": compose.identity(b"x")})

    def test_missing_native_cannot_leave_delivery(self):
        with self.assertRaises((ValueError, FileNotFoundError)):
            verify.admit_delivery(self.current, self.prior, self.reports, self.temporary() / "missing", self.context)
        self.assertFalse((self.current / "delivery").exists())

    def test_original_vectors_exact_positive(self):
        for suite in self.native_lock["suites"].values():
            names = suite["expected_case_names"]
            stdout = "\n".join("CASE\t" + name + "\tPASS\tdetail" for name in names)
            self.assertTrue(native.exact_vector(stdout, names)[0])

    def test_revised_suite_is_separate_from_original_combined(self):
        self.assertEqual(set(self.native_lock["suites"]), {"combined_clear_los", "objective_full_clear_los"})
        self.assertEqual(self.native_lock["suites"]["combined_clear_los"]["input_variant"],
                         "BOUNDED_CLEAR_LOS_APPROACH_INPUT")
        self.assertEqual(self.native_lock["suites"]["objective_full_clear_los"]["input_variant"], "BOUNDED_CLEAR_LOS_MELEE_APPROACH_INPUT")
        with self.assertRaisesRegex(ValueError, "UNKNOWN_CASE_VARIANT"):
            native.assemble(self.current / "sources", self.native_lock, "original_combined")

    def test_clear_los_case_exact_inverse_preserves_original_assertions(self):
        original = (HERE / "native/fixtures/combined_cases.luau").read_bytes()
        revised = (HERE / "native/combined_cases_clear_los.luau").read_bytes()
        start = revised.index(b"local function clearNeutralApproach(neutral,target)\n")
        end = revised.index(b"local function neutralKO(session,label)\n", start)
        restored = revised[:start] + revised[end:]
        changed = b" rootPart.CFrame=clearNeutralApproach(neutral,target)\n"
        self.assertEqual(restored.count(changed), 1)
        restored = restored.replace(changed, b" rootPart.CFrame=CFrame.new(target-Vector3.new(0,-1,21),target)\n", 1)
        self.assertEqual(restored, original)

    def test_corrupt_new_case_rejected_before_execution(self):
        copied = self.temporary() / "native"
        shutil.copytree(HERE / "native", copied)
        p = copied / "combined_cases_clear_los.luau"
        p.write_bytes(p.read_bytes() + b"\n-- unknown case change\n")
        with patch.object(native, "HERE", copied), self.assertRaisesRegex(ValueError, "CASE_MISMATCH"):
            native.fixture_snapshot(self.native_lock)

    def test_old_case_pin_cannot_substitute_clear_los_case(self):
        altered = copy.deepcopy(self.native_lock)
        altered["suites"]["combined_clear_los"]["case"] = altered["fixtures"]["combined_cases.luau"]
        with self.assertRaisesRegex(ValueError, "CASE_MISMATCH"):
            native.fixture_snapshot(altered)

    def test_empty_missing_duplicate_extra_failed_case_rejected(self):
        names = self.native_lock["suites"]["objective_full_clear_los"]["expected_case_names"]
        lines = ["CASE\t" + name + "\tPASS\tdetail" for name in names]
        bad = [[], lines[:-1], lines + [lines[0]], lines + ["CASE\tEXTRA\tPASS\tdetail"],
               [lines[0].replace("\tPASS\t", "\tFAIL\t")] + lines[1:], list(reversed(lines))]
        for case in bad:
            self.assertFalse(native.exact_vector("\n".join(case), names)[0])

    def test_new_build_directory_preexisting_rejected(self):
        base = self.temporary()
        build = base / "existing-build"
        build.mkdir()
        with self.assertRaises(ValueError):
            native.run_profile(self.current / "sources", base / "source", build, base / "out",
                               Path("/missing-cmake"), Path("/missing-ninja"), Path("/missing-git"),
                               Path("/missing-cc"), Path("/missing-cxx"), self.context)
        self.assertFalse((base / "out").exists())

    def test_new_native_lock_cannot_accept_modified_fixture(self):
        altered = copy.deepcopy(self.native_lock)
        altered["fixtures"]["native_prefix.luau"]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            native.fixture_snapshot(altered)

    def test_both_suites_assembly_full_body_exact(self):
        for suite in self.native_lock["suites"]:
            generated, _, ranges = native.assemble(self.current / "sources", self.native_lock, suite)
            self.assertEqual(len(ranges), 28)
            for rel, row in ranges.items():
                self.assertEqual(generated[row["start"]:row["end"]], (self.current / "sources" / rel).read_bytes())

    def test_objective_clear_los_case_inverse_preserves_original_assertions(self):
        original = (HERE / "native/objective_full_cases.luau").read_bytes()
        revised = (HERE / "native/objective_full_cases_clear_los.luau").read_bytes()
        first = b"-- OBJECTIVE_FULL_CLEAR_LOS_INPUT_BEGIN\n"
        last = b"-- OBJECTIVE_FULL_CLEAR_LOS_INPUT_END\n\n"
        self.assertEqual(revised.count(first), 1)
        self.assertEqual(revised.count(last), 1)
        start = revised.index(first)
        end = revised.index(last, start) + len(last)
        self.assertEqual(compose.identity(revised[start:end]), {"bytes": 768,
                         "sha256": "924c41396b10c0b31645f6edeefc456531671e5383e60510896091ae421daf30"})
        restored = revised[:start] + revised[end:]
        changed = (b" local beforeHealth=humanoid.Health\n local beforeWrites=#healthWrites\n"
                   b" local target=neutral.PrimaryPart.Position\n"
                   b" rootPart.CFrame=CFrame.new(clearMeleeApproach(neutral,character),target)\n"
                   b" local beforeRays=rayQueries\n")
        previous = (b" local beforeHealth=humanoid.Health\n local beforeWrites=#healthWrites\n"
                    b" local beforeRays=rayQueries\n local target=neutral.PrimaryPart.Position\n"
                    b" rootPart.CFrame=CFrame.new(target+Vector3.new(2,0,0),target)\n")
        self.assertEqual(restored.count(changed), 1)
        self.assertEqual(restored.replace(changed, previous, 1), original)

    def test_corrupt_objective_clear_los_case_rejected_before_execution(self):
        copied = self.temporary() / "native"
        shutil.copytree(HERE / "native", copied)
        p = copied / "objective_full_cases_clear_los.luau"
        p.write_bytes(p.read_bytes() + b"\n-- unknown objective case change\n")
        with patch.object(native, "HERE", copied), self.assertRaisesRegex(ValueError, "CASE_MISMATCH"):
            native.fixture_snapshot(self.native_lock)

    def test_original_objective_pin_cannot_substitute_clear_los_case(self):
        altered = copy.deepcopy(self.native_lock)
        original = altered["objective_case_amendment"]["original_case"]
        altered["suites"]["objective_full_clear_los"]["case"] = {k: original[k] for k in ("bytes", "sha256")}
        with self.assertRaisesRegex(ValueError, "CASE_MISMATCH"):
            native.fixture_snapshot(altered)

    def test_preserved_original_objective_drift_rejected_by_both_checks(self):
        copied = self.temporary() / "contract"
        shutil.copytree(HERE, copied)
        p = copied / "native/objective_full_cases.luau"
        p.write_bytes(p.read_bytes() + b"\n-- changed retained original\n")
        with patch.object(native, "HERE", copied / "native"), self.assertRaisesRegex(
                ValueError, "ORIGINAL_OBJECTIVE_CASE_NOT_PRESERVED"):
            native.fixture_snapshot(self.native_lock)
        with patch.object(verify, "HERE", copied), self.assertRaisesRegex(
                ValueError, "NATIVE_ORIGINAL_OBJECTIVE_NOT_PRESERVED"):
            verify.verify_native(copied / "missing-native-results", self.current, self.lock, self.context)


class FinalAdmissionBoundary(unittest.TestCase):
    """Run explicitly after actual Native completion; no fixture or gate stubs."""
    ARTIFACT_STAGE = "final"

    @classmethod
    def setUpClass(cls):
        UnionBoundary.setUpClass.__func__(cls)
        _, paths = artifact_environment(cls.ARTIFACT_STAGE)
        cls.native = paths["UNION22_TEST_NATIVE"]
        verify.verify_native(cls.native, cls.current, cls.lock, cls.context)

    def temporary(self):
        context = tempfile.TemporaryDirectory(prefix="union22-final-negative-")
        self.addCleanup(context.cleanup)
        return Path(context.name)

    def fresh_core(self):
        output = self.temporary() / "candidate"
        commands = verify.data(self.current / "CORE_BUILD_REPORT.json")["commands"]
        compiler = Path(next(c["command"][0] for c in commands if c["command"][1] == "--text"))
        rojo = Path(next(c["command"][0] for c in commands if c["command"][1] == "build"))
        compose.build_source_candidate(self.prior, self.reports, output, compiler, rojo, self.context)
        return output

    def check_failure(self, output, callback, native, reason):
        with callback, self.assertRaisesRegex(ValueError, reason):
            verify.admit_delivery(output, self.prior, self.reports, native, self.context)
        self.assertFalse((output / "delivery").exists())
        for stage in output.parent.glob(".union22-delivery-*"):
            self.assertTrue((stage / "FAILED.json").is_file())
            self.assertFalse((stage / "UNION22_FINAL_ADMISSION.json").exists())
            self.assertFalse((stage / "UNION22_DELIVERY_MANIFEST.json").exists())

    def phase_mutation(self, function_name, phase, mutation, copy_native=False):
        output = self.fresh_core()
        native = self.native
        if copy_native:
            native = self.temporary() / "native"
            shutil.copytree(self.native, native)
        original = getattr(verify, function_name)
        def after_real_check(*args, **kwargs):
            result = original(*args, **kwargs)
            mutation(output, native)
            return result
        self.check_failure(output, patch.object(verify, function_name, after_real_check), native,
                           "PAYLOAD_CHANGED_AFTER_" + phase)

    def test_place_changed_after_real_core_rejected(self):
        def mutate(root, _):
            p = root / compose.PLACE
            p.write_bytes(p.read_bytes() + b"\n<!-- after real core -->\n")
        self.phase_mutation("verify_core", "CORE", mutate)

    def test_project_changed_after_real_retention_rejected(self):
        def mutate(root, _):
            p = root / compose.PROJECT
            p.write_bytes(p.read_bytes() + b"\n")
        self.phase_mutation("retention_reports", "RETENTION", mutate)

    def test_place_changed_after_real_native_rejected(self):
        def mutate(root, _):
            p = root / compose.PLACE
            p.write_bytes(p.read_bytes() + b"\n<!-- after actual strong Native check -->\n")
        self.phase_mutation("verify_native", "NATIVE", mutate)

    def test_native_evidence_changed_after_real_native_rejected(self):
        def mutate(_, root):
            p = root / "objective_full_clear_los/stdout.log"
            p.write_bytes(p.read_bytes() + b"TRACE\tlate evidence drift\n")
        self.phase_mutation("verify_native", "NATIVE", mutate, copy_native=True)

    def test_unknown_file_in_delivery_stage_rejected(self):
        output = self.fresh_core()
        original = verify.shutil.copytree
        def mutate_stage_after_copy(src, dst, *args, **kwargs):
            result = original(src, dst, *args, **kwargs)
            if Path(dst).name == "native_evidence":
                (Path(dst).parent / "unexpected.txt").write_text("not part of the validated input or reports\n")
            return result
        self.check_failure(output, patch.object(verify.shutil, "copytree", mutate_stage_after_copy),
                           self.native, "DELIVERY_COPY_NOT_VALIDATED_STARTING_PAYLOAD")

    def test_original_case_tail_cannot_be_relabelled_as_clear_los(self):
        copied = self.temporary() / "native"
        shutil.copytree(self.native, copied)
        suite = copied / "combined_clear_los"
        program = (suite / "generated.luau").read_bytes()
        revised = (HERE / "native/combined_cases_clear_los.luau").read_bytes()
        original = (HERE / "native/fixtures/combined_cases.luau").read_bytes()
        self.assertTrue(program.endswith(revised))
        altered = program[:-len(revised)] + original
        (suite / "generated.luau").write_bytes(altered)
        receipt = verify.data(suite / "receipt.json")
        receipt["generated"] = compose.identity(altered)
        compose.write_json(suite / "receipt.json", receipt)
        aggregate = verify.data(copied / "receipt.json")
        aggregate["suites"]["combined_clear_los"] = compose.identity((suite / "receipt.json").read_bytes())
        compose.write_json(copied / "receipt.json", aggregate)
        with self.assertRaisesRegex(ValueError, "NATIVE_EXECUTED_PROGRAM_NOT_EXACT"):
            verify.verify_native(copied, self.current, self.lock, self.context)

    def test_unexecuted_original_combined_cannot_enter_aggregate(self):
        copied = self.temporary() / "native"
        shutil.copytree(self.native, copied)
        aggregate = verify.data(copied / "receipt.json")
        aggregate["suites"]["original_combined"] = dict(aggregate["suites"]["combined_clear_los"])
        compose.write_json(copied / "receipt.json", aggregate)
        with self.assertRaisesRegex(ValueError, "NATIVE_AGGREGATE_SUITE_SET"):
            verify.verify_native(copied, self.current, self.lock, self.context)

    def test_original_objective_tail_cannot_be_relabelled_as_clear_los(self):
        copied = self.temporary() / "native"
        shutil.copytree(self.native, copied)
        suite = copied / "objective_full_clear_los"
        program = (suite / "generated.luau").read_bytes()
        revised = (HERE / "native/objective_full_cases_clear_los.luau").read_bytes()
        original = (HERE / "native/objective_full_cases.luau").read_bytes()
        self.assertTrue(program.endswith(revised))
        altered = program[:-len(revised)] + original
        (suite / "generated.luau").write_bytes(altered)
        receipt = verify.data(suite / "receipt.json")
        receipt["generated"] = compose.identity(altered)
        compose.write_json(suite / "receipt.json", receipt)
        aggregate = verify.data(copied / "receipt.json")
        aggregate["suites"]["objective_full_clear_los"] = compose.identity((suite / "receipt.json").read_bytes())
        compose.write_json(copied / "receipt.json", aggregate)
        with self.assertRaisesRegex(ValueError, "NATIVE_EXECUTED_PROGRAM_NOT_EXACT"):
            verify.verify_native(copied, self.current, self.lock, self.context)

    def test_unexecuted_original_objective_cannot_enter_aggregate(self):
        copied = self.temporary() / "native"
        shutil.copytree(self.native, copied)
        aggregate = verify.data(copied / "receipt.json")
        aggregate["suites"]["objective_full"] = dict(aggregate["suites"]["objective_full_clear_los"])
        compose.write_json(copied / "receipt.json", aggregate)
        with self.assertRaisesRegex(ValueError, "NATIVE_AGGREGATE_SUITE_SET"):
            verify.verify_native(copied, self.current, self.lock, self.context)


class UnionOfflineContract(unittest.TestCase):
    """Repository-only checks; no artifact or runtime acceptance is claimed."""
    @classmethod
    def setUpClass(cls):
        cls.lock = compose.load_lock()
        cls.native_lock = native.load_lock()

    def test_profile_and_native_lock_share_exact69(self):
        self.assertEqual(len(self.lock["sources"]), 69)
        self.assertEqual(self.native_lock["sources"],
                         {name: row["after"] for name, row in self.lock["sources"].items()})
        self.assertEqual(set(self.native_lock["suites"]), {"combined_clear_los", "objective_full_clear_los"})

    def test_original_fixture_and_case_bytes_remain_pinned(self):
        self.assertEqual(native.fixture_snapshot(self.native_lock), self.native_lock["fixtures"])

    def test_absent_partial_and_unknown_artifact_context_rejected(self):
        for environment in ({}, {"UNION22_TEST_PRIOR": "/missing"},
                            {"UNION22_TEST_STAGE": "final"}, {"UNION22_TEST_STAGE": "other"},
                            {"UNION22_TEST_UNKNOWN": "unexpected"}):
            with patch.dict(os.environ, environment, clear=True), self.assertRaises(ValueError):
                artifact_environment()

    def test_native_failure_observation_preserves_fail_and_success_contracts(self):
        # Python protocol controls only: subprocess, assembly and source reads
        # are mocked. No game, source-build, Native or CI acceptance is claimed.
        with tempfile.TemporaryDirectory(prefix="union22-diagnostic-protocol-") as directory:
            parent = Path(directory)
            binary = parent / "protocol-binary"
            binary.write_bytes(b"protocol-only; never executed")
            binary_pin = native.identity(binary.read_bytes())
            before = copy.deepcopy(self.native_lock["sources"])
            changed = copy.deepcopy(before)
            changed[next(iter(changed))]["sha256"] = "0" * 64
            expected = self.native_lock["suites"]["objective_full_clear_los"]["expected_case_names"]
            passed = ("\n".join("CASE\t" + name + "\tPASS\tprotocol-only" for name in expected) + "\n").encode()
            failed = passed.replace(b"\tPASS\t", b"\tFAIL\t", 1)
            controls = [
                ("process", subprocess.CompletedProcess([], 1, failed, b"original failure\n"), before, ValueError),
                ("vector", subprocess.CompletedProcess([], 0, failed, b""), before, ValueError),
                ("source", subprocess.CompletedProcess([], 0, passed, b""), changed, ValueError),
                ("timeout", subprocess.TimeoutExpired([], 60, output=b"partial output\n", stderr=b"partial error\n"), before, subprocess.TimeoutExpired),
                ("utf8", subprocess.CompletedProcess([], 0, b"\xff", b""), before, UnicodeDecodeError),
                ("success", subprocess.CompletedProcess([], 0, passed, b""), before, None),
            ]
            for name, response, snapshot, error_type in controls:
                with self.subTest(name=name):
                    output = parent / name
                    console = io.StringIO()
                    effect = {"side_effect": response} if isinstance(response, Exception) else {"return_value": response}
                    with patch.object(native, "assemble", return_value=(b"-- protocol only\n", {}, {})), \
                         patch.object(native.subprocess, "run", **effect), \
                         patch.object(native, "source_snapshot", return_value=snapshot), \
                         patch.object(native, "fixture_snapshot"), redirect_stdout(console):
                        arguments = (parent / "unused-source", output, binary, self.native_lock, "objective_full_clear_los", before,
                                     binary_pin, {"kind": "PROTOCOL_ONLY"}, native.identity(b"protocol-receipt"),
                                     native.identity(b"protocol-runner"))
                        if error_type is None:
                            result = native.run_suite(*arguments)
                        else:
                            with self.assertRaises(error_type) as caught:
                                native.run_suite(*arguments)
                    if error_type is None:
                        self.assertEqual(console.getvalue(), "objective_full_clear_los: 7/7 exact PASS cases\n")
                        self.assertEqual(result["schema"], "UNION22_FULL_RUNTIME_SUITE_V2")
                        self.assertEqual(result["status"], "PASS")
                        self.assertEqual({p.name for p in output.iterdir()},
                                         {"generated.luau", "stdout.log", "stderr.log", "receipt.json"})
                        self.assertEqual((output / "stdout.log").read_bytes(), passed)
                        continue
                    self.assertFalse((output / "receipt.json").exists())
                    diagnostic = verify.data(output / "FAILED.json")
                    stdout = response.stdout or b""
                    stderr = response.stderr or b""
                    self.assertEqual((output / "stdout.log").read_bytes(), stdout)
                    self.assertEqual((output / "stderr.log").read_bytes(), stderr)
                    self.assertEqual(diagnostic["stdout"], native.identity(stdout))
                    self.assertEqual(diagnostic["stderr"], native.identity(stderr))
                    self.assertEqual(diagnostic["native"], binary_pin)
                    self.assertEqual(diagnostic["generated"], native.identity(b"-- protocol only\n"))
                    self.assertEqual(diagnostic["status"], "FAIL_DIAGNOSTIC_ONLY")
                    self.assertFalse(diagnostic["native_admission"])
                    displayed = console.getvalue().splitlines()
                    self.assertEqual(len(displayed), 3)
                    self.assertEqual(json.loads(displayed[0].removeprefix("UNION22_NATIVE_FAILURE ")), diagnostic)
                    self.assertEqual(json.loads(displayed[1].removeprefix("UNION22_NATIVE_FAILURE_STDOUT ")),
                                     stdout.decode("utf-8", errors="backslashreplace"))
                    self.assertEqual(json.loads(displayed[2].removeprefix("UNION22_NATIVE_FAILURE_STDERR ")),
                                     stderr.decode("utf-8", errors="backslashreplace"))
                    if name in ("process", "vector", "source"):
                        self.assertIn("SUITE_FAILED_OR_SOURCE_MUTATED:objective_full_clear_los", str(caught.exception))
                        self.assertEqual(diagnostic["native_exit"], response.returncode)
                        self.assertEqual(diagnostic["source_inputs_unchanged"], name != "source")
                        self.assertEqual(diagnostic["exact_complete_pass_vector"], name == "source")
                        self.assertEqual(diagnostic["parse_reason"], "EXACT_PASS_VECTOR" if name == "source" else "NON_PASS_CASE")
                    elif name == "timeout":
                        self.assertIs(caught.exception, response)
                        self.assertTrue(diagnostic["timed_out"])
                        self.assertEqual(diagnostic["parse_reason"], "NOT_PARSED_TIMEOUT")
                    else:
                        self.assertEqual(diagnostic["parse_reason"], "INVALID_UTF8")

    test_original_39_workflow_step_payloads_byte_exact = UnionBoundary.test_original_39_workflow_step_payloads_byte_exact
    test_clear_los_case_exact_inverse_preserves_original_assertions = UnionBoundary.test_clear_los_case_exact_inverse_preserves_original_assertions
    test_objective_clear_los_case_inverse_preserves_original_assertions = UnionBoundary.test_objective_clear_los_case_inverse_preserves_original_assertions
    test_original_vectors_exact_positive = UnionBoundary.test_original_vectors_exact_positive
    test_empty_missing_duplicate_extra_failed_case_rejected = UnionBoundary.test_empty_missing_duplicate_extra_failed_case_rejected
    test_duplicate_json_keys_rejected = UnionBoundary.test_duplicate_json_keys_rejected
    test_hunk_removed_bytes_rejected = UnionBoundary.test_hunk_removed_bytes_rejected
    test_hunk_overlap_rejected = UnionBoundary.test_hunk_overlap_rejected


def integration_suite(loader):
    stage, _ = artifact_environment()
    case = FinalAdmissionBoundary if stage == "final" else UnionBoundary
    return checked_suite(loader, case, INTEGRATION_COUNTS[stage])


def load_tests(loader, standard_tests, pattern):
    # Only ordinary discovery with no union-specific context selects contracts.
    # A module/script entry or even a partial context must request real artifacts.
    has_context = any(key.startswith("UNION22_TEST_") for key in os.environ)
    if pattern is not None and not has_context:
        return checked_suite(loader, UnionOfflineContract, 12)
    return integration_suite(loader)


def main():
    if len(sys.argv) != 1:
        raise ValueError("RED_UNION22_COMPLETE_INTEGRATION_ENTRY_ONLY")
    stage, _ = artifact_environment()
    suite = integration_suite(unittest.defaultTestLoader)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun != INTEGRATION_COUNTS[stage] or result.skipped:
        raise ValueError("RED_UNION22_INCOMPLETE_INTEGRATION_EXECUTION")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
