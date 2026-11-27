#!/usr/bin/env python3
"""Admission negatives against the actual pinned REAL69 artifact and helpers.

These tests do not manufacture a gameplay PASS. They validate exact source,
route, output-path and native-result admission; run_current69.py executes the
full native behavior suites separately. All assertions remain active under -O.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import patch_current69 as patch

spec = importlib.util.spec_from_file_location("gq618_current69_test_runner", HERE / "native/run_current69.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--artifact-dir", type=Path, required=True)
parser.add_argument("--baseline-repo", type=Path, required=True)
inputs, remaining = parser.parse_known_args()
sys.argv = [sys.argv[0], *remaining]


class Current69AdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = inputs.artifact_dir.absolute()
        cls.repo = inputs.baseline_repo.absolute()
        cls.lock = gate.load_lock()
        cls.compose, cls.native, cls.native_lock = gate.load_helpers(cls.repo, cls.lock)
        cls.original, cls.project, cls.place, cls.properties = gate.validate_payload(
            cls.artifact, cls.lock, cls.compose)
        cls.combat = cls.original[patch.COMBAT_PATH]
        cls.on = patch.transform(cls.combat)

    @classmethod
    def tearDownClass(cls):
        # The real artifact and frozen helper checkout are read-only inputs.
        actual = gate.validate_payload(cls.artifact, cls.lock, cls.compose)
        unittest.TestCase().assertEqual(actual, (cls.original, cls.project, cls.place, cls.properties))
        gate.load_helpers(cls.repo, cls.lock)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="gq618_current69_admission_")
        self.addCleanup(temporary.cleanup)
        self.tmp = Path(temporary.name)

    def payload_copy(self, name="artifact"):
        folder = self.tmp / name
        folder.mkdir()
        for relative, raw in self.original.items():
            path = folder / "sources" / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        (folder / gate.PROJECT).write_bytes(self.project)
        (folder / gate.PLACE).write_bytes(self.place)
        return folder

    def cli(self, source, out, receipt, mode="on"):
        return subprocess.run(
            [sys.executable, "-B", "-O", str(HERE / "patch_current69.py"),
             "--combat", str(source), "--out", str(out), "--receipt", str(receipt), "--mode", mode],
            capture_output=True, timeout=30,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})

    def case_output(self, names=None, failures=None):
        names = self.lock["expected_cases"] if names is None else names
        failures = set() if failures is None else set(failures)
        return "".join("CASE\t" + name + "\t" + ("FAIL" if name in failures else "PASS")
                       + "\tparser fixture only\n" for name in names).encode()

    def test_actual_combat_exact_forward_and_inverse(self):
        self.assertEqual(patch.identity(self.combat), patch.BEFORE)
        self.assertEqual(patch.identity(self.on), patch.AFTER)
        self.assertEqual(patch.transform(self.on, "off"), self.combat)
        updated = {**self.original, patch.COMBAT_PATH: self.on}
        self.assertEqual([p for p in self.original if self.original[p] != updated[p]], [patch.COMBAT_PATH])
        self.assertEqual(len(updated), 69)

    def test_wrong_direction_prepatched_and_drift_are_rejected(self):
        unrelated = next(raw for name, raw in self.original.items() if name != patch.COMBAT_PATH)
        examples = [(self.on, "on"), (self.combat, "off"), (self.combat + b"\n", "on"),
                    (self.combat[:-1], "on"), (self.combat.replace(b"BEAST", b"BEASX", 1), "on"),
                    (unrelated, "on")]
        for raw, mode in examples:
            with self.subTest(mode=mode, identity=patch.identity(raw)):
                with self.assertRaisesRegex(ValueError, "COMBAT_PREIMAGE"):
                    patch.transform(raw, mode)
        for mode in ("ON", "unknown", "", None):
            with self.subTest(mode=mode):
                with self.assertRaisesRegex(ValueError, "UNKNOWN_MODE"):
                    patch.transform(self.combat, mode)

    def test_actual_69_sources_project_and_place_agree(self):
        self.assertEqual(len(self.original), 69)
        inventory = self.compose.project_inventory(self.project)
        embedded, properties = self.compose.place_inventory(self.place)
        self.assertEqual(inventory, {p: {"route": r["route"], "class": r["class"]}
                                     for p, r in self.lock["sources"].items()})
        self.assertEqual(embedded, {r["route"]: {"class": r["class"], "raw": self.original[p]}
                                    for p, r in self.lock["sources"].items()})
        self.assertEqual(properties, self.properties)

    def test_extra_missing_renamed_and_unrelated_source_drift_rejected(self):
        unrelated = next(p for p in self.original if p != patch.COMBAT_PATH)
        for mutation in ("extra", "missing", "renamed", "unrelated_drift"):
            with self.subTest(mutation=mutation):
                folder = self.payload_copy(mutation)
                target = folder / "sources" / unrelated
                if mutation == "extra":
                    (folder / "sources/UnselectedModule.luau").write_bytes(b"return {}\n")
                elif mutation == "missing":
                    target.unlink()
                elif mutation == "renamed":
                    target.rename(target.with_name("UnselectedRename.luau"))
                else:
                    target.write_bytes(target.read_bytes() + b"\n-- unrelated drift\n")
                with self.assertRaisesRegex(ValueError, "EXACT_69_SOURCE_PROFILE"):
                    gate.validate_payload(folder, self.lock, self.compose)

    def test_non_luau_extra_file_rejected(self):
        folder = self.payload_copy()
        (folder / "sources/unselected.txt").write_bytes(b"extra")
        with self.assertRaisesRegex(ValueError, "EXTRA_SOURCE_FILE"):
            gate.validate_payload(folder, self.lock, self.compose)

    def test_selected_source_symlink_rejected(self):
        folder = self.payload_copy()
        selected = folder / "sources" / patch.COMBAT_PATH
        selected.unlink()
        selected.symlink_to(self.artifact / "sources" / patch.COMBAT_PATH)
        with self.assertRaisesRegex(ValueError, "SOURCE_SYMLINK"):
            gate.validate_payload(folder, self.lock, self.compose)

    def test_project_or_place_byte_drift_rejected(self):
        for name in (gate.PROJECT, gate.PLACE):
            with self.subTest(file=name):
                folder = self.payload_copy(name)
                path = folder / name
                path.write_bytes(path.read_bytes() + b"\n")
                with self.assertRaisesRegex(ValueError, "BASE_PROJECT_OR_PLACE_IDENTITY"):
                    gate.validate_payload(folder, self.lock, self.compose)

    def test_duplicate_json_keys_rejected_without_last_key_wins(self):
        raw = self.project.replace(b'"name":', b'"name": "duplicate", "name":', 1)
        with self.assertRaisesRegex(ValueError, "DUPLICATE_JSON_KEY"):
            gate.strict_json(raw)
        with self.assertRaisesRegex(ValueError, "DUPLICATE_JSON_KEY"):
            self.compose.project_inventory(raw)

    def test_duplicate_project_runtime_route_rejected(self):
        key = b'"EGGRUMBLE_SevenRoleCombat":'
        duplicate = key + b' {"$path":"sources/' + patch.COMBAT_PATH.encode() + b'"}, ' + key
        raw = self.project.replace(key, duplicate, 1)
        self.assertNotEqual(raw, self.project)
        with self.assertRaisesRegex(ValueError, "DUPLICATE_JSON_KEY"):
            self.compose.project_inventory(raw)

    def test_one_source_at_two_project_routes_rejected(self):
        project = gate.strict_json(self.project)
        project["tree"]["ServerScriptService"]["DuplicateCombat"] = {
            "$path": "sources/" + patch.COMBAT_PATH}
        with self.assertRaisesRegex(ValueError, "DUPLICATE_PROJECT_SOURCE"):
            self.compose.project_inventory(json.dumps(project).encode())

    def test_duplicate_embedded_route_and_source_property_rejected(self):
        for mutation in ("route", "source_property"):
            with self.subTest(mutation=mutation):
                tree = ET.fromstring(self.place)
                for parent in tree.iter():
                    item = next((child for child in parent.findall("Item")
                                 if child.find("Properties/ProtectedString[@name='Source']") is not None
                                 or child.find("Properties/string[@name='Source']") is not None), None)
                    if item is not None:
                        break
                self.assertIsNotNone(item)
                if mutation == "route":
                    parent.append(copy.deepcopy(item))
                    reason = "DUPLICATE_INSTANCE_ROUTE"
                else:
                    properties = item.find("Properties")
                    node = next(child for child in properties if child.get("name") == "Source")
                    properties.append(copy.deepcopy(node))
                    reason = "DUPLICATE_SOURCE_PROPERTY"
                with self.assertRaisesRegex(ValueError, reason):
                    self.compose.place_inventory(ET.tostring(tree))

    def test_changed_frozen_helper_rejected_before_import(self):
        original = self.repo / gate.BASE / "compose_union22.py"
        changed = self.tmp / "changed_helper.py"
        changed.write_bytes(original.read_bytes() + b"\nraise RuntimeError('MUST_NOT_EXECUTE')\n")
        with self.assertRaisesRegex(ValueError, "PINNED_HELPER"):
            gate.import_pinned("changed_helper", changed, self.lock["helpers"]["compose"])

    def test_separate_new_output_directories_are_admitted(self):
        roots = [self.tmp / name for name in ("artifact", "luau", "build", "out")]
        roots[0].mkdir(); roots[1].mkdir()
        gate.validate_outputs(*roots)
        self.assertFalse(roots[2].exists())
        self.assertFalse(roots[3].exists())

    def test_output_overlap_rejected_for_every_pair(self):
        for left in range(4):
            for right in range(left + 1, 4):
                for nested in (False, True):
                    with self.subTest(left=left, right=right, nested=nested):
                        roots = [self.tmp / ("root" + str(i)) for i in range(4)]
                        roots[right] = roots[left] / "nested" if nested else roots[left]
                        with self.assertRaisesRegex(ValueError, "INPUT_OUTPUT_OVERLAP"):
                            gate.validate_outputs(*roots)

    def test_dotdot_output_alias_cannot_evade_input_overlap(self):
        artifact = self.tmp / "artifact"
        artifact.mkdir()
        alias = self.tmp / "alias"
        alias.mkdir()
        escaped_output = alias / ".." / "artifact" / "nested-output"
        with self.assertRaisesRegex(ValueError, "INPUT_OUTPUT_OVERLAP"):
            gate.validate_outputs(artifact, self.tmp / "luau", self.tmp / "build", escaped_output)
        self.assertFalse((artifact / "nested-output").exists())

    def test_output_root_or_parent_symlinks_rejected(self):
        target = self.tmp / "target"
        target.mkdir()
        alias = self.tmp / "alias"
        alias.symlink_to(target, target_is_directory=True)
        for index in range(4):
            for nested in (False, True):
                with self.subTest(index=index, nested=nested):
                    roots = [self.tmp / ("root" + str(i)) for i in range(4)]
                    roots[index] = alias / "child" if nested else alias
                    with self.assertRaisesRegex(ValueError, "DIRECTORY_SYMLINK"):
                        gate.validate_outputs(*roots)

    def test_preexisting_build_or_output_rejected(self):
        for index in (2, 3):
            with self.subTest(index=index):
                roots = [self.tmp / (str(index) + "-root" + str(i)) for i in range(4)]
                roots[index].mkdir()
                with self.assertRaisesRegex(ValueError, "BUILD_AND_OUTPUT_MUST_BE_NEW"):
                    gate.validate_outputs(*roots)

    def test_optimized_cli_round_trip_writes_exact_new_outputs(self):
        source, on, on_receipt, off, off_receipt = [self.tmp / name for name in
            ("input.luau", "on.luau", "on.json", "off.luau", "off.json")]
        source.write_bytes(self.combat)
        forward = self.cli(source, on, on_receipt)
        self.assertEqual(forward.returncode, 0, forward.stderr.decode())
        self.assertEqual(on.read_bytes(), self.on)
        inverse = self.cli(on, off, off_receipt, "off")
        self.assertEqual(inverse.returncode, 0, inverse.stderr.decode())
        self.assertEqual(off.read_bytes(), self.combat)
        self.assertEqual(source.read_bytes(), self.combat)
        for receipt in (on_receipt, off_receipt):
            record = gate.strict_json(receipt.read_bytes())
            self.assertIs(record["exact_inverse"], True)
            self.assertIs(record["official_rc_adopted"], False)
            self.assertIs(record["studio_tested"], False)

    def test_optimized_cli_refuses_overwriting_output_or_receipt(self):
        source = self.tmp / "input.luau"
        source.write_bytes(self.combat)
        for which in ("output", "receipt"):
            with self.subTest(which=which):
                out, receipt = self.tmp / (which + ".luau"), self.tmp / (which + ".json")
                occupied = out if which == "output" else receipt
                occupied.write_bytes(b"must survive")
                result = self.cli(source, out, receipt)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(b"OUTPUT_MUST_BE_NEW_REGULAR_PATH", result.stderr)
                self.assertEqual(occupied.read_bytes(), b"must survive")
                self.assertFalse((receipt if which == "output" else out).exists())
        self.assertEqual(source.read_bytes(), self.combat)

    def test_optimized_cli_refuses_input_and_output_aliases(self):
        source = self.tmp / "input.luau"
        source.write_bytes(self.combat)
        for out, receipt in ((source, self.tmp / "receipt.json"),
                             (self.tmp / "out.luau", source),
                             (self.tmp / "same", self.tmp / "same")):
            with self.subTest(out=out.name, receipt=receipt.name):
                result = self.cli(source, out, receipt)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(b"OUTPUT_ALIASES_INPUT", result.stderr)
        self.assertEqual(source.read_bytes(), self.combat)
        self.assertEqual(list(self.tmp.iterdir()), [source])

    def test_optimized_cli_refuses_symlink_source_and_output_parent(self):
        source = self.tmp / "input.luau"
        source.write_bytes(self.combat)
        alias = self.tmp / "source-link.luau"
        alias.symlink_to(source)
        out, receipt = self.tmp / "out.luau", self.tmp / "receipt.json"
        result = self.cli(alias, out, receipt)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"SYMLINK_PATH", result.stderr)
        self.assertFalse(out.exists()); self.assertFalse(receipt.exists())
        target = self.tmp / "target"
        target.mkdir()
        directory_alias = self.tmp / "directory-link"
        directory_alias.symlink_to(target, target_is_directory=True)
        result = self.cli(source, directory_alias / "out.luau", receipt)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"OUTPUT_MUST_BE_NEW_REGULAR_PATH", result.stderr)
        self.assertEqual(list(target.iterdir()), [])
        self.assertFalse(receipt.exists())

    def test_exact_native_case_vectors_admit_expected_baseline_and_candidate(self):
        names = self.lock["expected_cases"]
        for failures in (set(), set(self.lock["baseline_failures"])):
            with self.subTest(failures=sorted(failures)):
                rows = gate.exact_cases(self.case_output(failures=failures), names, failures)
                self.assertEqual([row[1] for row in rows], names)

    def test_extra_missing_duplicate_reordered_and_malformed_cases_rejected(self):
        names = self.lock["expected_cases"]
        duplicate = list(names); duplicate[-1] = duplicate[0]
        reordered = list(names); reordered[0], reordered[1] = reordered[1], reordered[0]
        malformed = self.case_output().replace(b"\tparser fixture only", b"", 1)
        variants = {
            "extra": self.case_output(names + ["UNAUTHORIZED_CASE"]),
            "missing": self.case_output(names[:-1]),
            "duplicate": self.case_output(duplicate),
            "reordered": self.case_output(reordered),
            "malformed": malformed,
        }
        for name, stdout in variants.items():
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, "EXACT_CASE_VECTOR"):
                    gate.exact_cases(stdout, names, set())

    def test_false_or_unknown_native_outcomes_rejected(self):
        names = self.lock["expected_cases"]
        baseline_failures = set(self.lock["baseline_failures"])
        variants = [
            (self.case_output(), baseline_failures),
            (self.case_output(failures={names[0]}), set()),
            (self.case_output().replace(b"\tPASS\t", b"\tSKIP\t", 1), set()),
            (self.case_output().replace(b"\tPASS\t", b"\tpass\t", 1), set()),
        ]
        for stdout, failures in variants:
            with self.subTest(failures=sorted(failures), first=stdout.splitlines()[0]):
                with self.assertRaisesRegex(ValueError, "CASE_OUTCOME_VECTOR"):
                    gate.exact_cases(stdout, names, failures)

    def test_actual_28_body_bindings_reject_post_build_source_or_program_mutation(self):
        suite = "combined_clear_los"
        program, _lines, ranges = self.native.assemble(
            self.artifact / "sources", self.native_lock, suite)
        self.assertEqual(len(ranges), 28)
        gate.verify_body_bindings(program, ranges, self.original)

        # The assembler faithfully reports the later file's bytes and hash.
        # Admission must still bind them to the earlier immutable source set.
        folder = self.payload_copy("assembled_after_build")
        path = folder / "sources" / patch.COMBAT_PATH
        path.write_bytes(self.combat + b"\n-- source changed after compilation\n")
        changed_program, _lines, changed_ranges = self.native.assemble(
            folder / "sources", self.native_lock, suite)
        self.assertNotEqual(changed_program, program)
        self.assertEqual(changed_ranges[patch.COMBAT_PATH]["sha256"],
                         patch.identity(path.read_bytes())["sha256"])
        with self.assertRaisesRegex(ValueError, "EXECUTED_BODY_DIFFERS_FROM_COMPILED_SOURCE"):
            gate.verify_body_bindings(changed_program, changed_ranges, self.original)

        # Keeping original metadata cannot conceal a changed program body.
        at = ranges[patch.COMBAT_PATH]["start"]
        mutated = program[:at] + bytes([program[at] ^ 1]) + program[at + 1:]
        with self.assertRaisesRegex(ValueError, "EXECUTED_BODY_DIFFERS_FROM_COMPILED_SOURCE"):
            gate.verify_body_bindings(mutated, ranges, self.original)

    def test_final_on_and_off_snapshots_reject_changed_source(self):
        # Both labels use actual baseline bytes as mutation-admission fixtures;
        # these copies do not claim a new ON/OFF compile or Rojo build.
        selected = {label: dict(self.original) for label in ("on", "off")}
        profiles = {label: {"place": patch.identity(self.place)} for label in selected}
        for label in selected:
            self.payload_copy(label)
        gate.verify_built_profiles(self.tmp, selected, self.project, profiles)
        for label in selected:
            with self.subTest(profile=label):
                path = self.tmp / label / "sources" / patch.COMBAT_PATH
                path.write_bytes(self.combat + b"\n-- source changed after native suites\n")
                try:
                    with self.assertRaisesRegex(ValueError, "FINAL_SOURCE_PROFILE_CHANGED:" + label):
                        gate.verify_built_profiles(self.tmp, selected, self.project, profiles)
                finally:
                    path.write_bytes(self.combat)
        gate.verify_built_profiles(self.tmp, selected, self.project, profiles)

    def test_final_on_and_off_snapshots_reject_changed_project_or_place(self):
        selected = {label: dict(self.original) for label in ("on", "off")}
        profiles = {label: {"place": patch.identity(self.place)} for label in selected}
        for label in selected:
            self.payload_copy(label)
        gate.verify_built_profiles(self.tmp, selected, self.project, profiles)
        for label in selected:
            for name, original, reason in (
                    (gate.PROJECT, self.project, "FINAL_PROJECT_CHANGED:"),
                    (gate.PLACE, self.place, "FINAL_PLACE_CHANGED:")):
                with self.subTest(profile=label, file=name):
                    path = self.tmp / label / name
                    path.write_bytes(original + b"\n")
                    try:
                        with self.assertRaisesRegex(ValueError, reason + label):
                            gate.verify_built_profiles(self.tmp, selected, self.project, profiles)
                    finally:
                        path.write_bytes(original)
        gate.verify_built_profiles(self.tmp, selected, self.project, profiles)


if __name__ == "__main__":
    unittest.main()
