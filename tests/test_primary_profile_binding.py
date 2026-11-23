#!/usr/bin/env python3
"""Independent, offline controls for the public primary-binding validator.

Ordinary discovery runs rejection-only contracts without an external artifact.
Set PRIMARY_BINDING_TEST_DELIVERY to the explicit, authentic dcb delivery to
run archive/synthetic integration controls. No fixture is auto-discovered. Set
PRIMARY_BINDING_TEST_REQUIRE_INTEGRATION=1 to make absent input an error rather
than the explicit NOT_RUN skip. Synthetic copies are test data, not new CI,
Native, Studio, adoption, or Publish evidence. No producer helper is an oracle.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET


REPO = Path(__file__).resolve().parents[1]
IMPLEMENTATION = REPO / "rc_fastlane/bind_primary_profile.py"
ACTIVE = REPO / "rc_fastlane/ACTIVE.json"
PROFILE = REPO / "quality_gameplay/gq470_union22_real69_20261122/profile_lock.json"
SPEC = importlib.util.spec_from_file_location("primary_binding_under_test", IMPLEMENTATION)
binding = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = binding
SPEC.loader.exec_module(binding)

HEAD = "dcb501673d7959e4904cf360ef0119917e6aa2e0"
CONTEXT = {
    "kind": "OFFICIAL", "build_head": HEAD, "checkout_sha": HEAD,
    "canonical_build": True, "official_build_head": HEAD,
    "observed_live_rc": HEAD, "event": "push", "run_id": "45083333379",
    "run_attempt": "1",
}
LOCAL_CONTEXT = {
    "kind": "LOCAL_SOURCE_REVIEW", "build_head": HEAD, "checkout_sha": HEAD,
    "canonical_build": False, "official_build_head": None,
    "observed_live_rc": None, "event": None, "run_id": None, "run_attempt": None,
}
TARGET = "eggrumble_v3_real69_union22_private_studio"
MANIFEST = "UNION22_DELIVERY_MANIFEST.json"
PACKAGED_PROFILE = "UNION22_PROFILE_LOCK.json"
SOURCE_RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
ADMISSION = "UNION22_FINAL_ADMISSION.json"
CORE = "CORE_BUILD_REPORT.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
PROJECT = "EGGRUMBLE_REAL69.project.json"
HOST_REL = "ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview.server.luau"
HOST_ROUTE = "ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview"
ENVELOPES = (
    "UNION22_FINAL_ALL48_ENVELOPE.json", "UNION22_FINAL_17_MARKER_RETENTION.json",
    "UNION22_FINAL_ART_SOURCE_RETENTION.json",
)
FIXTURE_PINS = {
    MANIFEST: (19495, "f9efc17709bdbd1ae77037ea7e44b81fee4c1e8b39fb69c813bdacd398121782"),
    PACKAGED_PROFILE: (289381, "826235327ba98bbde81242661d0929e81e8dda6d69550e1d040586414c7a0b60"),
    SOURCE_RECEIPT: (17623, "749a80be9cb050cead632a8ddf0cdd66fa2506adf01ef09c6726eb716c69de2f"),
    ADMISSION: (2390, "fb5f348e8e913a12613b453c4ad91a3ecf264ea6572c85d3d3e3c302036db38e"),
    PROJECT: (9564, "90cf3f9fd181002b1b5521a30f17b15b5a14d73bd00f0755d77aaeb68f7885e7"),
    PLACE: (828114, "356bcfc9b5602b03a04f77f9638e15175be2deec084ef2a9d95963cadf7586f6"),
}
FALSE_CLAIMS = (
    "legacy_48_all_ported", "default_selection_changed", "fresh_ci_executed",
    "native_executed", "formal_rc_adoption_performed", "studio_executed",
    "roblox_publish", "current_native_admission_proven", "upstream_authentication_performed",
)


def data(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def put(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                          encoding="utf-8")


def pin(path):
    raw = Path(path).read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def inventory(root):
    return {p.relative_to(root).as_posix(): pin(p)
            for p in sorted(Path(root).rglob("*")) if p.is_file()}


def reseal_manifest(root):
    """Test-only outer byte pins; never a production assembly/validation call."""
    manifest = data(root / MANIFEST)
    manifest["files"] = {k: v for k, v in inventory(root).items() if k != MANIFEST}
    put(root / MANIFEST, manifest)


class TemporaryInputs(unittest.TestCase):
    def temp(self):
        ctx = tempfile.TemporaryDirectory(prefix="primary-binding-test-")
        self.addCleanup(ctx.cleanup)
        return Path(ctx.name)

    def incomplete(self):
        root = self.temp()
        active, profile, delivery = root / "ACTIVE.json", root / "profile.json", root / "delivery"
        shutil.copyfile(ACTIVE, active)
        shutil.copyfile(PROFILE, profile)
        delivery.mkdir()
        return dict(active=active, profile=profile, delivery=delivery,
                    expected_context=copy.deepcopy(CONTEXT))

    def rejects(self, code, **kwargs):
        with self.assertRaises(binding.BindingError) as caught:
            binding.validate_binding(**kwargs)
        self.assertEqual(caught.exception.code, code)

    def cli(self, inputs, out, *, extra=(), env=None, context_raw=None):
        context = out.parent / "expected_context.json"
        if context_raw is None:
            put(context, inputs["expected_context"])
        else:
            context.write_text(context_raw, encoding="utf-8")
        cmd = [sys.executable, "-B"] + ([] if __debug__ else ["-O"])
        cmd += [str(IMPLEMENTATION), "--active", str(inputs["active"]),
                "--profile", str(inputs["profile"]), "--delivery", str(inputs["delivery"]),
                "--expected-context", str(context), "--input-kind",
                inputs.get("input_kind", "ARCHIVED_ARTIFACT"), "--out", str(out)]
        if inputs.get("historical_delivery") is not None:
            cmd += ["--historical-delivery", str(inputs["historical_delivery"])]
        return subprocess.run(cmd + list(extra), capture_output=True, text=True,
                              timeout=30, env=env)


class StrictInputContracts(TemporaryInputs):
    """Substantive rejection controls always run, even without external history."""

    def test_unsupported_input_kinds_fail_before_artifact_lookup(self):
        for value in (None, "", "OFFICIAL", "local_synthetic", 1):
            with self.subTest(value=value):
                self.rejects("BIND_INPUT_KIND", **self.incomplete(), input_kind=value)

    def test_expected_context_requires_exact_fields(self):
        for operation in ("missing", "extra"):
            with self.subTest(operation=operation):
                args = self.incomplete()
                if operation == "missing":
                    del args["expected_context"]["run_attempt"]
                else:
                    args["expected_context"]["claimed_ci"] = True
                self.rejects("BIND_CONTEXT", **args)

    def test_expected_context_rejects_coercion_and_invalid_provenance(self):
        for key, value in (("canonical_build", 1), ("canonical_build", "true"),
                           ("run_id", 45083333379), ("run_attempt", 1),
                           ("run_id", "²"), ("run_id", "１２"), ("run_id", "0"),
                           ("run_attempt", "+1"), ("run_attempt", "-1"),
                           ("build_head", "abc"), ("kind", "CLAIMED_OFFICIAL"),
                           ("official_build_head", None), ("event", None)):
            with self.subTest(key=key, value=value):
                args = self.incomplete()
                args["expected_context"][key] = value
                self.rejects("BIND_CONTEXT", **args)

    def test_context_is_a_mapping_and_local_has_no_official_run(self):
        for value in (None, [], "OFFICIAL", {**LOCAL_CONTEXT, "run_id": "123"}):
            with self.subTest(value=value):
                args = self.incomplete()
                args["expected_context"] = value
                self.rejects("BIND_CONTEXT", **args)

    def test_active_and_profile_strict_json(self):
        for field in ("active", "profile"):
            for raw in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}',
                        '[]', 'null', 'true', '"text"', '{broken'):
                with self.subTest(field=field, raw=raw):
                    args = self.incomplete()
                    args[field].write_text(raw, encoding="utf-8")
                    self.rejects("BIND_JSON", **args)

    def test_manifest_strict_json_without_canonical_fixture(self):
        for raw in ('{"files":{},"files":{}}', '{"files":NaN}', '[]'):
            with self.subTest(raw=raw):
                args = self.incomplete()
                (args["delivery"] / MANIFEST).write_text(raw, encoding="utf-8")
                self.rejects("BIND_JSON", **args)

    def test_symlink_primary_inputs_rejected(self):
        for field in ("active", "profile", "delivery"):
            with self.subTest(field=field):
                args = self.incomplete()
                alias = args[field].parent / (field + "_alias")
                alias.symlink_to(args[field], target_is_directory=field == "delivery")
                args[field] = alias
                self.rejects("BIND_PATH", **args)

    def test_symlink_ancestor_rejected(self):
        args = self.incomplete()
        alias = self.temp() / "alias"
        alias.symlink_to(args["active"].parent, target_is_directory=True)
        args["active"] = alias / args["active"].name
        self.rejects("BIND_PATH", **args)

    def test_nonregular_and_missing_input_rejected(self):
        for field in ("active", "profile"):
            with self.subTest(field=field):
                args = self.incomplete()
                args[field].unlink()
                args[field].mkdir()
                self.rejects("BIND_PATH", **args)
        args = self.incomplete()
        args["active"].unlink()
        self.rejects("BIND_IO", **args)

    def test_cli_invalid_arguments_no_report(self):
        root = self.temp()
        result = subprocess.run([sys.executable, "-B", str(IMPLEMENTATION), "--unknown"],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(list(root.iterdir()), [])

    def test_cli_incomplete_delivery_is_rejection_not_success(self):
        args = self.incomplete()
        out = self.temp() / "report.json"
        result = self.cli(args, out)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("BIND_", result.stdout + result.stderr)
        self.assertFalse(out.exists())

    def test_cli_context_json_rejects_duplicate_keys_and_nonfinite_values(self):
        raw_cases = ('{"kind":"OFFICIAL","kind":"OFFICIAL"}', '{"run_id":NaN}', '[]')
        # Python's JSON integer conversion limit is a parser rejection, not
        # permission to leak an unstructured ValueError through the public CLI.
        integer_limit = getattr(sys, "get_int_max_str_digits", lambda: 0)()
        if integer_limit:
            raw_cases += ('{"run_id":' + "9" * (integer_limit + 1) + '}',)
        for raw in raw_cases:
            with self.subTest(raw_prefix=raw[:80], bytes=len(raw)):
                out = self.temp() / "report.json"
                result = self.cli(self.incomplete(), out, context_raw=raw)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("BIND_JSON", result.stdout + result.stderr)
                self.assertFalse(out.exists())


class ArchivedBindingContracts(TemporaryInputs):
    """Integration requires the explicit authentic external archive; never fabricated."""

    @classmethod
    def setUpClass(cls):
        supplied = os.environ.get("PRIMARY_BINDING_TEST_DELIVERY", "")
        if not supplied.strip():
            reason = "NOT_RUN: explicit PRIMARY_BINDING_TEST_DELIVERY authentic archive unavailable"
            if os.environ.get("PRIMARY_BINDING_TEST_REQUIRE_INTEGRATION") == "1":
                raise RuntimeError(reason)
            raise unittest.SkipTest(reason)
        cls.archive = Path(supplied).absolute()
        if not cls.archive.is_dir() or cls.archive.is_symlink():
            raise RuntimeError("Explicit archive must be a real directory")
        for name, (size, digest) in FIXTURE_PINS.items():
            if pin(cls.archive / name) != {"bytes": size, "sha256": digest}:
                raise RuntimeError("Authentic dcb fixture pin mismatch: " + name)
        observed = inventory(cls.archive)
        manifest = data(cls.archive / MANIFEST)
        if len(observed) != 110 or len(manifest["files"]) != 109:
            raise RuntimeError("Authentic dcb closure must be 110/109")
        if {k: v for k, v in observed.items() if k != MANIFEST} != manifest["files"]:
            raise RuntimeError("Authentic dcb manifest closure mismatch")
        if data(cls.archive / SOURCE_RECEIPT)["execution_context"] != CONTEXT:
            raise RuntimeError("Authentic dcb context mismatch")
        cls.original_inventory = observed

    @classmethod
    def tearDownClass(cls):
        if inventory(cls.archive) != cls.original_inventory:
            raise AssertionError("Tests changed the authentic archive")

    def inputs(self):
        root = self.temp()
        delivery = root / "delivery"
        shutil.copytree(self.archive, delivery)
        active, profile = root / "ACTIVE.json", root / "profile.json"
        shutil.copyfile(ACTIVE, active)
        # Historical controls bind their explicitly supplied, independently
        # pinned profile. A later legitimate repo HUD/profile update is not
        # evidence that this immutable historical archive became invalid.
        shutil.copyfile(self.archive / PACKAGED_PROFILE, profile)
        return dict(active=active, profile=profile, delivery=delivery,
                    expected_context=copy.deepcopy(CONTEXT))

    def edit(self, args, name, mutate, *, reseal=True):
        path = args["delivery"] / name
        obj = data(path)
        mutate(obj)
        put(path, obj)
        if reseal:
            reseal_manifest(args["delivery"])

    def profile_edit(self, args, mutate):
        obj = data(args["profile"])
        mutate(obj)
        put(args["profile"], obj)
        put(args["delivery"] / PACKAGED_PROFILE, obj)
        profile_pin = pin(args["profile"])
        for name in (SOURCE_RECEIPT, CORE, ADMISSION):
            self.edit(args, name, lambda value: value.update(profile_lock=profile_pin), reseal=False)
        reseal_manifest(args["delivery"])

    def rebind_place(self, args, tree, *, changed_host=None):
        """Re-pin a deliberately invalid XML fixture without the producer's code."""
        path = args["delivery"] / PLACE
        tree.write(path, encoding="utf-8", xml_declaration=True)
        place_pin = pin(path)

        def profile_change(obj):
            obj["final_place"] = place_pin
            if changed_host is not None:
                obj["sources"][HOST_REL]["after"] = pin(changed_host)
        self.profile_edit(args, profile_change)
        receipt = data(args["delivery"] / SOURCE_RECEIPT)
        receipt["private_place_bytes"] = place_pin["bytes"]
        receipt["private_place_sha256"] = place_pin["sha256"]
        if changed_host is not None:
            receipt["source_hashes"][HOST_ROUTE] = pin(changed_host)["sha256"]
        put(args["delivery"] / SOURCE_RECEIPT, receipt)
        def core_change(obj):
            obj["final_place"] = place_pin
            obj["staged_payload"][PLACE] = place_pin
            if changed_host is not None:
                obj["staged_payload"]["sources/" + HOST_REL] = pin(changed_host)
        self.edit(args, CORE, core_change, reseal=False)
        self.edit(args, ADMISSION, lambda obj: obj.update(current_place=place_pin), reseal=False)
        for name in ENVELOPES:
            self.edit(args, name, lambda obj: obj.update(private_place=place_pin), reseal=False)
        reseal_manifest(args["delivery"])

    @staticmethod
    def host_item(tree):
        matches = [item for item in tree.iter("Item")
                   if item.findtext("Properties/string[@name='Name']") == HOST_ROUTE.rsplit("/", 1)[1]]
        if len(matches) != 1:
            raise AssertionError("Independent authentic XML Host locator is not unique")
        return matches[0]

    def synthetic(self):
        args = self.inputs()
        active = data(args["active"])
        active["active_profile"] = TARGET
        active["active_source_commit"] = HEAD
        active["source_profiles"][TARGET] = {
            "source_profile": "REAL69_UNION22",
            "source_manifest": "quality_gameplay/gq470_union22_real69_20261122/profile_lock.json",
            "build_workflow": ".github/workflows/gq8-real63-source-composite.yml",
            "source_count": 69, "expected_script_count": 69,
            "release_place": PLACE, "selected_for_roblox_publish": False, "source_commit": HEAD,
        }
        put(args["active"], active)
        self.profile_edit(args, lambda obj: obj["runtime_labels"].update(ACTIVE_RUNTIME=TARGET))
        for name in (SOURCE_RECEIPT, CORE, ADMISSION) + ENVELOPES:
            obj = data(args["delivery"] / name)
            if "ACTIVE_RUNTIME" in obj:
                obj["ACTIVE_RUNTIME"] = TARGET
            if "execution_context" in obj:
                obj["execution_context"] = copy.deepcopy(LOCAL_CONTEXT)
            if "context" in obj:
                obj["context"] = copy.deepcopy(LOCAL_CONTEXT)
            if "canonical_build" in obj:
                obj["canonical_build"] = False
            if "receipt_provenance" in obj:
                obj["receipt_provenance"] = "LOCAL_SOURCE_REVIEW"
            if "official_build_head" in obj:
                obj["official_build_head"] = None
            if "formal_rc_adoption_proven" in obj:
                obj["formal_rc_adoption_proven"] = False
            if name == ADMISSION:
                obj["status"] = "LOCAL_SYNTHETIC_SOURCE_SELECTION_ONLY"
            put(args["delivery"] / name, obj)
        reseal_manifest(args["delivery"])
        args.update(expected_context=copy.deepcopy(LOCAL_CONTEXT),
                    input_kind="LOCAL_SYNTHETIC", historical_delivery=self.archive)
        # This independent fixture assertion prevents accidentally laundering
        # old Native receipts into a new invocation in the fixture itself.
        self.assertEqual(inventory(args["delivery"] / "native_evidence"),
                         inventory(self.archive / "native_evidence"))
        return args

    def report_contract(self, report, *, synthetic=False):
        self.assertEqual(report["schema"], "GQ866_PRIMARY_BINDING_VALIDATION_V1")
        self.assertEqual(report["status"], "PASS_READ_ONLY_BINDING")
        self.assertEqual(report["validator_execution"], "LOCAL_READ_ONLY")
        self.assertEqual(report["target_profile"], "REAL69_UNION22")
        self.assertEqual(report["source_count"], 69)
        self.assertEqual(report["instances"], 75)
        self.assertEqual(report["class_counts"], {"Script": 12, "ModuleScript": 47, "LocalScript": 10})
        self.assertEqual(report["delivery_file_count"], 110)
        self.assertEqual(report["all_48_semantic_parity"], "NOT_PROVEN")
        self.assertEqual(report["host"]["route"], HOST_ROUTE)
        self.assertEqual(report["host"]["class"], "Script")
        self.assertIs(report["host"]["studio_guard_preserved"], True)
        self.assertEqual(report["host"]["bytes"], 94590)
        self.assertEqual(report["host"]["sha256"],
                         "12e74acc12b991e1287f158fbc9bb0b52329b3bdb8cf33d2a24c2378da39fe00")
        for key in FALSE_CLAIMS:
            self.assertIs(report[key], False, key)
        self.assertEqual(report["input_evidence_context"], LOCAL_CONTEXT if synthetic else CONTEXT)
        self.assertEqual(report["observed_primary_profile"], TARGET if synthetic else "rich51")
        self.assertIs(report["target_registered"], synthetic)
        self.assertIs(report["configuration_selects_target"], synthetic)
        self.assertEqual(report["selection_status"],
                         "LOCAL_SYNTHETIC_SELECTION_ONLY" if synthetic else "COMPANION_NOT_SELECTED")
        self.assertEqual(report["input_kind"], "LOCAL_SYNTHETIC" if synthetic else "ARCHIVED_ARTIFACT")
        self.assertEqual(report["native_evidence_scope"],
                         "HISTORICAL_ONLY" if synthetic else "ARCHIVED_ADMISSION_BINDING")
        self.assertIs(report["archived_native_admission_bound"], not synthetic)
        self.assertIs(report["historical_native_bytes_preserved"], True if synthetic else None)
        self.assertEqual(report["historical_input_evidence_context"], CONTEXT if synthetic else None)
        expected_keys = {"active", "profile", "packaged_profile", "manifest", "source_receipt",
                         "core", "admission", "project", "place"}
        if synthetic:
            expected_keys |= {"historical_manifest", "historical_source_receipt"}
        self.assertEqual(set(report["inputs"]), expected_keys)
        for value in report["inputs"].values():
            self.assertEqual(set(value), {"bytes", "sha256"})
            self.assertIs(type(value["bytes"]), int)
            self.assertGreater(value["bytes"], 0)
            self.assertRegex(value["sha256"], r"^[0-9a-f]{64}$")
        for key, name in (("project", PROJECT), ("place", PLACE)):
            self.assertEqual(report["inputs"][key], pin(self.archive / name))
        if not synthetic:
            for key, path in (("active", ACTIVE), ("profile", self.archive / PACKAGED_PROFILE),
                              ("packaged_profile", self.archive / PACKAGED_PROFILE),
                              ("manifest", self.archive / MANIFEST),
                              ("source_receipt", self.archive / SOURCE_RECEIPT),
                              ("core", self.archive / CORE), ("admission", self.archive / ADMISSION)):
                self.assertEqual(report["inputs"][key], pin(path))

    def test_authentic_companion_archive_control(self):
        args = self.inputs()
        before = inventory(args["delivery"])
        self.report_contract(binding.validate_binding(**args).as_dict())
        self.assertEqual(inventory(args["delivery"]), before)

    def test_detached_report_and_atomic_new_output(self):
        args = self.inputs()
        before = inventory(args["delivery"])
        validated = binding.validate_binding(**args)
        changed = validated.as_dict()
        changed["status"] = "FAKE"
        changed["native_executed"] = True
        changed["input_evidence_context"]["kind"] = "FAKE"
        self.report_contract(validated.as_dict())
        outdir = self.temp()
        out = outdir / "report.json"
        self.assertEqual(binding.write_report(validated, out), out)
        self.report_contract(data(out))
        self.assertEqual(list(outdir.iterdir()), [out])
        self.assertEqual(inventory(args["delivery"]), before)

    def test_explicit_synthetic_selection_preserves_historical_native(self):
        args = self.synthetic()
        self.report_contract(binding.validate_binding(**args).as_dict(), synthetic=True)
        self.assertEqual(inventory(args["delivery"] / "native_evidence"),
                         inventory(self.archive / "native_evidence"))

    def test_stale_expected_context_each_identity_field(self):
        for field, value in (("build_head", "a" * 40), ("checkout_sha", "b" * 40),
                             ("run_id", "45083333378"), ("run_attempt", "2")):
            with self.subTest(field=field):
                args = self.inputs()
                args["expected_context"][field] = value
                self.rejects("BIND_CONTEXT", **args)

    def test_cross_report_context_mixture(self):
        for name, field in ((SOURCE_RECEIPT, "execution_context"), (CORE, "context"),
                            ("native_evidence/receipt.json", "execution_context")):
            with self.subTest(name=name):
                args = self.inputs()
                self.edit(args, name, lambda obj: obj[field].update(run_id="1"))
                self.rejects("BIND_CONTEXT", **args)
        args = self.inputs()
        self.edit(args, "UNION22_FINAL_ALL48_RAW.json", lambda obj: obj.update(official_head="a" * 40))
        self.rejects("BIND_CONTEXT", **args)

    def test_selector_unknown_missing_and_stale_commit(self):
        for mutation in ("unknown", "missing", "stale"):
            with self.subTest(mutation=mutation):
                args = self.inputs()
                active = data(args["active"])
                if mutation == "unknown":
                    active["active_profile"] = "NOT_REGISTERED"
                elif mutation == "missing":
                    del active["source_profiles"]["rich51"]
                else:
                    active["active_source_commit"] = "a" * 40
                put(args["active"], active)
                self.rejects("BIND_SELECTION", **args)

    def test_synthetic_mapping_requires_every_exact_field(self):
        variants = (("source_profile", "REAL68"), ("source_manifest", "other.json"),
                    ("build_workflow", ".github/workflows/other.yml"),
                    ("source_count", 68), ("expected_script_count", True),
                    ("release_place", "other.rbxlx"), ("source_commit", "a" * 40))
        for field, value in variants:
            with self.subTest(field=field):
                args = self.synthetic()
                active = data(args["active"])
                active["source_profiles"][TARGET][field] = value
                put(args["active"], active)
                self.rejects("BIND_SELECTION", **args)

    def test_synthetic_active_source_commit_must_match_selected_row(self):
        args = self.synthetic()
        active = data(args["active"])
        active["active_source_commit"] = "f" * 40
        put(args["active"], active)
        self.rejects("BIND_SELECTION", **args)

    def test_archive_cannot_claim_unreviewed_cutover(self):
        args = self.inputs()
        active = data(args["active"])
        active["active_profile"] = TARGET
        active["active_source_commit"] = HEAD
        active["source_profiles"][TARGET] = {"source_profile": "REAL69_UNION22", "source_commit": HEAD}
        put(args["active"], active)
        self.rejects("BIND_SELECTION", **args)

    def test_delivery_inventory_added_removed_and_renamed(self):
        for change in ("add", "remove", "rename"):
            with self.subTest(change=change):
                args = self.inputs()
                root = args["delivery"]
                if change == "add":
                    (root / "extra.txt").write_text("extra")
                elif change == "remove":
                    (root / PROJECT).unlink()
                else:
                    (root / PROJECT).rename(root / "renamed.json")
                self.rejects("BIND_MANIFEST_FILES", **args)

    def test_resealed_unexpected_member_and_second_place_rejected(self):
        for name in ("extra.txt", "SECOND_GAME.rbxlx"):
            with self.subTest(name=name):
                args = self.inputs()
                (args["delivery"] / name).write_bytes(b"deliberately invalid extra input")
                reseal_manifest(args["delivery"])
                self.rejects("BIND_MANIFEST_FILES", **args)

    def test_manifest_members_self_exclusion_and_unsafe_paths(self):
        for member in (MANIFEST, "../outside", "/absolute", "sources/../alias", "./alias", "a\\b"):
            with self.subTest(member=member):
                args = self.inputs()
                self.edit(args, MANIFEST, lambda obj: obj["files"].update({member: {"bytes": 0, "sha256": "0" * 64}}), reseal=False)
                self.rejects("BIND_MANIFEST_FILES", **args)

    def test_unsealed_byte_drift_in_every_evidence_kind(self):
        for name in (PROJECT, SOURCE_RECEIPT, "native_evidence/combined_clear_los/stdout.log",
                     "sources/ServerScriptService/EGGRUMBLE_RoundReplay.luau",
                     "prior_boundary/legacy_rollbacks/OFF69_BOT_ART_ROLLBACK.tar.gz"):
            with self.subTest(name=name):
                args = self.inputs()
                path = args["delivery"] / name
                path.write_bytes(path.read_bytes() + b"\n")
                self.rejects("BIND_MANIFEST_PIN", **args)

    def test_packaged_profile_and_external_profile_must_match(self):
        args = self.inputs()
        profile = data(args["profile"])
        profile["source_count"] = 68
        put(args["profile"], profile)
        self.rejects("BIND_PROFILE", **args)

    def test_profile_contract_wrong_count_or_class_inventory(self):
        for field, value in (("source_count", 68), ("instance_count", 74),
                             ("class_counts", {"Script": 13, "ModuleScript": 46, "LocalScript": 10})):
            with self.subTest(field=field):
                args = self.inputs()
                self.profile_edit(args, lambda obj: obj.update({field: value}))
                self.rejects("BIND_PROFILE", **args)

    def test_source_body_drift_after_manifest_reseal(self):
        args = self.inputs()
        source = args["delivery"] / "sources/ServerScriptService/EGGRUMBLE_RoundReplay.luau"
        source.write_bytes(source.read_bytes() + b"\n-- deliberately invalid negative fixture\n")
        reseal_manifest(args["delivery"])
        self.rejects("BIND_SOURCE", **args)

    def test_source_route_rename_after_manifest_reseal(self):
        args = self.inputs()
        source = args["delivery"] / "sources/ServerScriptService/EGGRUMBLE_RoundReplay.luau"
        source.rename(source.with_name("WrongRoute.luau"))
        reseal_manifest(args["delivery"])
        self.rejects("BIND_SOURCE", **args)

    def test_project_redirect_duplicate_and_mixed_game_rejected(self):
        for mutation in ("redirect", "duplicate", "mixed_game"):
            with self.subTest(mutation=mutation):
                args = self.inputs()
                project = data(args["delivery"] / PROJECT)
                server = project["tree"]["ServerScriptService"]
                if mutation == "redirect":
                    server["EGGRUMBLE_RoundReplay"]["$path"] = "../outside.luau"
                elif mutation == "duplicate":
                    server["DuplicateReplay"] = copy.deepcopy(server["EGGRUMBLE_RoundReplay"])
                else:
                    server["Game"] = {"$className": "Script", "$path": "sources/ServerScriptService/EGGRUMBLE_RoundReplay.luau"}
                put(args["delivery"] / PROJECT, project)
                self.profile_edit(args, lambda obj: obj.update(project=pin(args["delivery"] / PROJECT)))
                self.edit(args, CORE, lambda obj: obj["staged_payload"].update({PROJECT: pin(args["delivery"] / PROJECT)}))
                self.rejects("BIND_PROJECT", **args)

    def test_place_byte_pin_and_xml_source_mismatch(self):
        args = self.inputs()
        path = args["delivery"] / PLACE
        path.write_bytes(path.read_bytes() + b"\n")
        reseal_manifest(args["delivery"])
        self.rejects("BIND_PLACE", **args)

    def test_place_xml_duplicate_source_class_and_route_rejected(self):
        for mutation in ("source", "duplicate_source", "class", "duplicate_route"):
            with self.subTest(mutation=mutation):
                args = self.inputs()
                tree = ET.parse(args["delivery"] / PLACE)
                host = self.host_item(tree)
                properties = host.find("Properties")
                source = properties.find("*[@name='Source']")
                self.assertIsNotNone(source)
                if mutation == "source":
                    source.text += "\n-- XML body must agree with the actual source file\n"
                elif mutation == "duplicate_source":
                    properties.append(copy.deepcopy(source))
                elif mutation == "class":
                    host.set("class", "ModuleScript")
                else:
                    parent = next(item for item in tree.iter("Item") if host in list(item))
                    parent.append(copy.deepcopy(host))
                self.rebind_place(args, tree)
                # A second Host is rejected at the authority inventory; the
                # remaining mutations violate the selected Place inventory.
                self.rejects("BIND_AUTHORITY" if mutation == "duplicate_route" else "BIND_PLACE", **args)

    def test_host_executable_studio_guard_not_just_text_presence(self):
        for replacement in ("-- if not RunService:IsStudio() then return end", "-- guard deliberately removed"):
            with self.subTest(replacement=replacement):
                args = self.inputs()
                path = args["delivery"] / "sources" / HOST_REL
                text = path.read_text(encoding="utf-8")
                guard = "if not RunService:IsStudio() then return end"
                # The genuine dcb Host has an early guard and a retained
                # historical guard at line1866. Remove/comment both so this
                # negative cannot still be satisfied by the second guard.
                self.assertEqual(text.splitlines().count(guard), 2)
                text = text.replace(guard, replacement)
                path.write_text(text, encoding="utf-8")
                tree = ET.parse(args["delivery"] / PLACE)
                self.host_item(tree).find("Properties/*[@name='Source']").text = text
                self.rebind_place(args, tree, changed_host=path)
                self.rejects("BIND_AUTHORITY", **args)

    def test_runtime_unification_and_parity_claims_rejected(self):
        cases = ((SOURCE_RECEIPT, "RUNTIME_UNIFIED", "YES"),
                 (ADMISSION, "legacy_48_all_ported", True),
                 (ENVELOPES[0], "all_48_semantic_parity", "PASS"),
                 ("UNION22_FINAL_ALL48_RAW.json", "all_48_semantic_parity", "PASS"))
        for name, key, value in cases:
            with self.subTest(name=name, key=key):
                args = self.inputs()
                self.edit(args, name, lambda obj: obj.update({key: value}))
                self.rejects("BIND_RUNTIME_CLAIM", **args)

    def test_evidence_gap_cannot_be_reclassified(self):
        args = self.inputs()
        def mutate(obj):
            row = next(row for row in obj["flags"] if row["feature_id"] == "SAVED_BEAST_EVOLUTION")
            row["current_evidence"] = "SOURCE_ANALOGUE_ONLY"
        self.edit(args, "UNION22_FINAL_ALL48_RAW.json", mutate)
        self.rejects("BIND_RUNTIME_CLAIM", **args)

    def test_engine_product_owner_and_publish_claims_rejected(self):
        cases = ((SOURCE_RECEIPT, "studio_solo", "PASS"),
                 (ADMISSION, "studio_two_client", "PASS"),
                 (ADMISSION, "android_15min", "PASS"),
                 (ADMISSION, "fun", "PASS"), (ADMISSION, "owner_accepted", True),
                 (ADMISSION, "art_gate", "PASS"), (ADMISSION, "product_gate", "PASS"),
                 (SOURCE_RECEIPT, "roblox_publish", True))
        for name, key, value in cases:
            with self.subTest(key=key):
                args = self.inputs()
                self.edit(args, name, lambda obj: obj.update({key: value}))
                self.rejects("BIND_ENGINE_CLAIM", **args)
        for mutation in ("GO", "missing"):
            with self.subTest(raw_product_quality=mutation):
                args = self.inputs()
                def raw_product(obj):
                    if mutation == "missing":
                        del obj["product_quality"]
                    else:
                        obj["product_quality"] = mutation
                self.edit(args, "UNION22_FINAL_ALL48_RAW.json", raw_product)
                self.rejects("BIND_ENGINE_CLAIM", **args)
        args = self.inputs()
        active = data(args["active"])
        active["production_publish_authorized"] = True
        put(args["active"], active)
        self.rejects("BIND_ENGINE_CLAIM", **args)

    def test_missing_or_local_history_rejected(self):
        args = self.synthetic()
        del args["historical_delivery"]
        self.rejects("BIND_HISTORY", **args)
        args = self.synthetic()
        args["historical_delivery"] = args["delivery"]
        self.rejects("BIND_HISTORY", **args)

    def test_history_context_and_manifest_must_be_valid(self):
        for mutation in ("context", "body"):
            with self.subTest(mutation=mutation):
                args = self.synthetic()
                history = self.temp() / "history"
                shutil.copytree(self.archive, history)
                args["historical_delivery"] = history
                if mutation == "context":
                    obj = data(history / SOURCE_RECEIPT)
                    obj["execution_context"]["run_id"] = "0"
                    put(history / SOURCE_RECEIPT, obj)
                    reseal_manifest(history)
                else:
                    (history / PLACE).write_bytes(b"not a place")
                self.rejects("BIND_HISTORY", **args)

    def test_synthetic_native_member_set_and_bytes_remain_historical(self):
        for mutation in ("change", "remove", "add"):
            with self.subTest(mutation=mutation):
                args = self.synthetic()
                native = args["delivery"] / "native_evidence"
                target = native / "combined_clear_los/stdout.log"
                if mutation == "change":
                    target.write_bytes(target.read_bytes() + b"FAKE\n")
                elif mutation == "remove":
                    target.unlink()
                else:
                    (native / "extra.log").write_text("not historical")
                reseal_manifest(args["delivery"])
                self.rejects("BIND_HISTORY", **args)

    def test_synthetic_native_context_cannot_be_relabelled_local(self):
        args = self.synthetic()
        self.edit(args, "native_evidence/receipt.json",
                  lambda obj: obj.update(execution_context=copy.deepcopy(LOCAL_CONTEXT)))
        self.rejects("BIND_HISTORY", **args)

    def test_synthetic_cannot_claim_fresh_native_admission(self):
        args = self.synthetic()
        self.edit(args, ADMISSION, lambda obj: obj.update(status="PASS_SOURCE_AND_NATIVE_ONLY"))
        self.rejects("BIND_ADMISSION", **args)

    def test_postvalidation_input_bytes_fail_emission(self):
        for field, name in (("active", None), ("profile", None), ("delivery", PACKAGED_PROFILE),
                            ("delivery", SOURCE_RECEIPT), ("delivery", PLACE),
                            ("delivery", "sources/ServerScriptService/EGGRUMBLE_RoundReplay.luau")):
            with self.subTest(field=field, name=name):
                args = self.inputs()
                validated = binding.validate_binding(**args)
                path = args[field] / name if name else args[field]
                path.write_bytes(path.read_bytes() + b"\n")
                out = self.temp() / "report.json"
                with self.assertRaises(binding.BindingError) as caught:
                    binding.write_report(validated, out)
                self.assertEqual(caught.exception.code, "BIND_INPUT_CHANGED")
                self.assertFalse(out.exists())

    def test_postvalidation_file_set_and_symlink_changes_fail_emission(self):
        for mutation in ("add", "remove", "rename", "symlink"):
            with self.subTest(mutation=mutation):
                args = self.inputs()
                validated = binding.validate_binding(**args)
                root = args["delivery"]
                if mutation == "add":
                    (root / "new.log").write_text("new")
                elif mutation == "remove":
                    (root / PROJECT).unlink()
                elif mutation == "rename":
                    (root / PROJECT).rename(root / "renamed.json")
                else:
                    original = self.temp() / "project.json"
                    shutil.copyfile(root / PROJECT, original)
                    (root / PROJECT).unlink()
                    (root / PROJECT).symlink_to(original)
                out = self.temp() / "report.json"
                with self.assertRaises(binding.BindingError) as caught:
                    binding.write_report(validated, out)
                self.assertEqual(caught.exception.code, "BIND_INPUT_CHANGED")
                self.assertFalse(out.exists())

    def test_postvalidation_historical_reference_change_fails_emission(self):
        for mutation in ("bytes", "added_file", "symlink"):
            with self.subTest(mutation=mutation):
                args = self.synthetic()
                history = self.temp() / "history"
                shutil.copytree(self.archive, history)
                args["historical_delivery"] = history
                validated = binding.validate_binding(**args)
                path = history / "native_evidence/configure.stderr.log"
                if mutation == "bytes":
                    path.write_text("changed")
                elif mutation == "added_file":
                    (history / "added.log").write_text("added")
                else:
                    target = self.temp() / "log"
                    shutil.copyfile(path, target)
                    path.unlink()
                    path.symlink_to(target)
                out = self.temp() / "report.json"
                with self.assertRaises(binding.BindingError) as caught:
                    binding.write_report(validated, out)
                self.assertEqual(caught.exception.code, "BIND_INPUT_CHANGED")
                self.assertFalse(out.exists())

    def test_existing_output_sentinels_are_never_overwritten(self):
        for kind in ("file", "directory", "symlink"):
            with self.subTest(kind=kind):
                args = self.inputs()
                validated = binding.validate_binding(**args)
                root = self.temp()
                sentinel = root / "sentinel"
                sentinel.write_text("KEEP")
                out = root / "report.json"
                if kind == "file":
                    out.write_text("KEEP")
                elif kind == "directory":
                    out.mkdir()
                else:
                    out.symlink_to(sentinel)
                with self.assertRaises(binding.BindingError) as caught:
                    binding.write_report(validated, out)
                self.assertEqual(caught.exception.code, "BIND_OUTPUT_EXISTS")
                self.assertEqual(sentinel.read_text(), "KEEP")
                if kind == "file":
                    self.assertEqual(out.read_text(), "KEEP")

    def test_output_cannot_intersect_any_input_namespace(self):
        args = self.synthetic()
        history = self.temp() / "history"
        shutil.copytree(self.archive, history)
        args["historical_delivery"] = history
        validated = binding.validate_binding(**args)
        for out in (args["delivery"] / "new.json", history / "new.json", args["active"], args["profile"]):
            with self.subTest(out=out):
                before = pin(out) if out.is_file() else None
                with self.assertRaises(binding.BindingError) as caught:
                    binding.write_report(validated, out)
                self.assertEqual(caught.exception.code, "BIND_OUTPUT_PATH")
                self.assertEqual(pin(out) if out.is_file() else None, before)

    def test_link_destination_replacement_is_never_deleted_as_owned(self):
        args = self.inputs()
        validated = binding.validate_binding(**args)
        out = self.temp() / "report.json"
        original_link = os.link
        sentinel = b"FOREIGN_DESTINATION_MUST_SURVIVE"

        def replace_after_link(src, dst, *positional, **kwargs):
            original_link(src, dst, *positional, **kwargs)
            Path(dst).unlink()
            Path(dst).write_bytes(sentinel)
            args["active"].write_bytes(args["active"].read_bytes() + b"\n")

        with patch("os.link", side_effect=replace_after_link):
            with self.assertRaises(binding.BindingError) as caught:
                binding.write_report(validated, out)
        # Destination ownership is checked immediately after link, before the
        # deliberately changed ACTIVE can reach the subsequent snapshot guard.
        self.assertEqual(caught.exception.code, "BIND_OUTPUT_PATH")
        self.assertEqual(out.read_bytes(), sentinel)
        self.assertNotIn(b"PASS_READ_ONLY_BINDING", out.read_bytes())

    def test_temporary_name_replacement_is_never_deleted_as_owned(self):
        args = self.inputs()
        validated = binding.validate_binding(**args)
        out = self.temp() / "report.json"
        original_link = os.link
        sentinel = b"FOREIGN_TEMPORARY_NAME_MUST_SURVIVE"
        replaced = []

        def replace_after_link(src, dst, *positional, **kwargs):
            original_link(src, dst, *positional, **kwargs)
            path = Path(src)
            path.unlink()
            path.write_bytes(sentinel)
            replaced.append(path)
            args["active"].write_bytes(args["active"].read_bytes() + b"\n")

        with patch("os.link", side_effect=replace_after_link):
            with self.assertRaises(binding.BindingError) as caught:
                binding.write_report(validated, out)
        self.assertEqual(caught.exception.code, "BIND_INPUT_CHANGED")
        self.assertEqual(len(replaced), 1)
        self.assertEqual(replaced[0].read_bytes(), sentinel)
        self.assertFalse(out.exists())

    def test_cli_archived_success_remains_local_read_only(self):
        args = self.inputs()
        out = self.temp() / "report.json"
        result = self.cli(args, out)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.report_contract(data(out))

    def test_adversarial_github_environment_cannot_promote_synthetic_result(self):
        """Deliberately forged environment is negative test data, never CI evidence."""
        args = self.synthetic()
        out = self.temp() / "report.json"
        env = dict(os.environ)
        env.update(GITHUB_ACTIONS="true", GITHUB_EVENT_NAME="push",
                   GITHUB_REF="refs/heads/rc/p0d-s1-kids-rc01", GITHUB_SHA=HEAD,
                   GITHUB_RUN_ID="99999999999", GITHUB_RUN_ATTEMPT="99",
                   GITHUB_REPOSITORY="kk051780/toy-wars-factory")
        result = self.cli(args, out, env=env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.report_contract(data(out), synthetic=True)
        self.assertEqual(data(out)["input_evidence_context"], LOCAL_CONTEXT)


if __name__ == "__main__":
    unittest.main(verbosity=2)
