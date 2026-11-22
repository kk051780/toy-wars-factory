#!/usr/bin/env python3
"""Prepare canonical #487's existing 711-byte repair on one fixed union69 input.

This stage verifies source identity and an actual inverse. It does not certify
provider execution or the final Score workflow. Union mode validates the actual
archived parent envelope; it does not execute parent Native or build a Place.
"""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import json
import io
import tarfile
import os
from pathlib import Path
import re
import stat
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
LOCK_PATH = ROOT / "source_lock.json"
TARGET = "ServerScriptService/EGGRUMBLE_ScoreBalance.luau"
TARGET_ROUTE = "ServerScriptService/EGGRUMBLE_ScoreBalance"
PROJECT = "EGGRUMBLE_REAL69.project.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
MANIFEST = "SCORE_RELAY_PREP_SOURCE_MANIFEST.json"
RECEIPT = "SCORE_RELAY_PREP_RECEIPT.json"
INVERSE_INPUT_MANIFEST = "SCORE_RELAY_INVERSE_INPUT_MANIFEST.json"
INVERSE_INPUT_RECEIPT = "SCORE_RELAY_INVERSE_INPUT_RECEIPT.json"
PARENT_MANIFEST = "SCORE_RELAY_PARENT_SOURCE_MANIFEST.json"
BASE_SHA = "ef0c1bf657ecf9fb8883036b114e0a19bb6def86b46dec1b6f8b11ccb94662a9"
AFTER_SHA = "67c76c12cc4d311847fb1cf794988b2f164053690660f6b55f4e590f93824136"
FRAGMENT_SHA = "acf5c2d1bea91b1387251fd0de3c4cdc132fa42a818e8df1c8b366789381a55b"
PARENT_MANIFEST_SHA = "13000a809f2cf0c091af94d8f1dadbdf0ed972f2303bb85e0d5be2db04078e28"
ANCHOR = b'  elseif kind=="EGG_DEPOSIT" then\n'
STATUS = "SOURCE_ONLY_PREP_FINAL_UNION_CONTRACT_NOT_BOUND"
PARENT_CONTRACT_SHA = 'fe49a2f97b4a3b6361d6d41248bb756e1e39c0aad720e0f774cc53b4c2bb2c27'


class ScoreRelayError(ValueError):
    """A bounded input, output or provenance check failed."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ScoreRelayError("RED_SCORE_RELAY_" + reason)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def info(raw: bytes) -> dict:
    return {"bytes": len(raw), "sha256": digest(raw)}


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "DUPLICATE_JSON_KEY_" + key)
        result[key] = value
    return result


def parse(raw: bytes) -> dict:
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique_pairs)


def regular_file(path: Path) -> bytes:
    require(path.is_file() and not path.is_symlink(), "REGULAR_FILE_REQUIRED_" + path.name)
    mode = path.stat().st_mode
    require(stat.S_ISREG(mode) and not mode & 0o7000, "UNSAFE_FILE_MODE_" + path.name)
    return path.read_bytes()


def load_lock() -> dict:
    raw = regular_file(LOCK_PATH)
    lock = parse(raw)
    require(lock.get("schema") == "SCORE_RELAY_FIXED_PARENT_PREP_V1", "LOCK_SCHEMA")
    require(lock.get("final_union_contract_bound") is False, "UNBOUND_PRODUCTION_CONTRACT_REQUIRED")
    require(lock["fixed_input"]["source_manifest_sha256"] == PARENT_MANIFEST_SHA, "PARENT_MANIFEST_PIN")
    baseline = lock["baseline_source_text"].encode("utf-8")
    fragment = lock["fragment_text"].encode("utf-8")
    require(info(baseline) == {"bytes": 8030, "sha256": BASE_SHA}, "BASELINE_SOURCE_PIN")
    require(info(fragment) == {"bytes": 711, "sha256": FRAGMENT_SHA}, "EXISTING_FRAGMENT_PIN")
    require(baseline.count(ANCHOR) == 1 and fragment not in baseline, "BASELINE_ANCHOR")
    require(info(baseline.replace(ANCHOR, fragment + ANCHOR, 1)) ==
            {"bytes": 8741, "sha256": AFTER_SHA}, "EXISTING_AFTER_PIN")
    rows = lock["input_sources"]
    require(len(rows) == 69 and TARGET in rows, "LOCK_SOURCE_COUNT")
    routes = set()
    for relative, row in rows.items():
        path = Path(relative)
        require(not path.is_absolute() and ".." not in path.parts and
                path.as_posix() == relative and relative.endswith(".luau"), "LOCK_RELATIVE_PATH")
        require(row["class"] in {"Script", "LocalScript", "ModuleScript"}, "LOCK_SOURCE_CLASS")
        require(row["route"] not in routes, "LOCK_DUPLICATE_ROUTE")
        routes.add(row["route"])
        require(type(row["bytes"]) is int and row["bytes"] > 0 and
                re.fullmatch(r"[a-f0-9]{64}", row["sha256"]) is not None, "LOCK_SOURCE_DIGEST")
    require(rows[TARGET] == {"bytes": 8030, "sha256": BASE_SHA,
                            "class": "ModuleScript", "route": TARGET_ROUTE}, "LOCK_SELECTED_SOURCE")
    require(lock["selected_source"] == {
        "path": TARGET, "route": TARGET_ROUTE, "class": "ModuleScript",
        "before": {"bytes": 8030, "sha256": BASE_SHA},
        "after": {"bytes": 8741, "sha256": AFTER_SHA},
        "fragment": {"bytes": 711, "sha256": FRAGMENT_SHA}}, "LOCK_SELECTED_METADATA")
    contract = lock.get("upstream_parent_contract")
    require(type(contract) is dict and canonical_digest(contract) == PARENT_CONTRACT_SHA, "UNION_PARENT_CONTRACT_PIN")
    require(contract["source_rows"] == rows, "UNION_PARENT_LOCK_ROWS")
    lock["_lock_sha256"] = digest(raw)
    return lock


PARENT_PACKET = "parent_union22"
PARENT_BINDING = "SCORE_RELAY_PARENT_BINDING.json"
PARENT_EXPECTATION = "SCORE_RELAY_EXTERNAL_PARENT_EXPECTATION.json"
UNION_MANIFEST = "UNION22_DELIVERY_MANIFEST.json"
UNION_RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
UNION_OFF = "off69_union22_prior_br"
UNION_ARCHIVE = "OFF69_UNION22_PRIOR_BR_ROLLBACK.tar.gz"
CONTEXT_FIELDS = {"kind", "build_head", "checkout_sha", "canonical_build", "official_build_head",
                  "observed_live_rc", "event", "run_id", "run_attempt"}
OWN_UNPROVEN = {"parent_origin_attestation_verified": False, "parent_native_reexecuted_by_score": False,
                "parent_retention_reexecuted_by_score": False, "final_score_workflow_bound": False,
                "score_same_head_ci_proven": False, "final_union_contract_bound": False,
                "canonical_build": False, "official_build_head": None}


def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def canonical_digest(value) -> str:
    return digest(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def typed_equal(actual, expected) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return set(actual) == set(expected) and all(typed_equal(actual[k], v) for k, v in expected.items())
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(typed_equal(a, b) for a, b in zip(actual, expected))
    return actual == expected


def validate_parent_context(value: dict) -> dict:
    require(type(value) is dict and set(value) == CONTEXT_FIELDS, "EXTERNAL_PARENT_CONTEXT_FIELDS")
    value = copy.deepcopy(value)
    require(value["kind"] in {"PR_CANDIDATE", "OFFICIAL"}, "EXTERNAL_PARENT_CONTEXT_KIND")
    for field in ("build_head", "checkout_sha", "observed_live_rc"):
        require(type(value[field]) is str and re.fullmatch(r"[0-9a-f]{40}", value[field]) is not None,
                "EXTERNAL_PARENT_CONTEXT_SHA_" + field)
    require(value["checkout_sha"] == value["build_head"], "EXTERNAL_PARENT_CONTEXT_CHECKOUT")
    for field in ("run_id", "run_attempt"):
        require(type(value[field]) is str and re.fullmatch(r"[0-9]+", value[field]) is not None
                and int(value[field]) > 0, "EXTERNAL_PARENT_CONTEXT_RUN_" + field)
    official = value["kind"] == "OFFICIAL"
    require(value["canonical_build"] is official and
            value["official_build_head"] == (value["build_head"] if official else None) and
            value["event"] == ("push" if official else "pull_request"), "EXTERNAL_PARENT_CONTEXT_CLASSIFICATION")
    if official:
        require(value["observed_live_rc"] == value["build_head"], "EXTERNAL_PARENT_CONTEXT_LIVE_RC")
    return value


def read_parent_expectation(path: Path) -> dict:
    data = parse(regular_file(Path(path)))
    if type(data) is dict and data.get("schema") == "SCORE_RELAY_EXTERNAL_PARENT_EXPECTATION_V1":
        require(set(data) <= {"schema", "expected_execution_context", "origin_observation"},
                "EXTERNAL_PARENT_EXPECTATION_WRAPPER_FIELDS")
        data = data.get("expected_execution_context")
    return validate_parent_context(data)


def parent_arguments(parent_kind: str, expected_parent_context: dict | None) -> dict | None:
    require(parent_kind in {"FROZEN_LOCAL", "UNION22_DELIVERY"}, "UNKNOWN_PARENT_KIND")
    if parent_kind == "FROZEN_LOCAL":
        require(expected_parent_context is None, "FROZEN_LOCAL_FORBIDS_PARENT_CONTEXT")
        return None
    require(expected_parent_context is not None, "UNION22_REQUIRES_EXTERNAL_PARENT_CONTEXT")
    return validate_parent_context(expected_parent_context)


def safe_relative(name: str) -> bool:
    return (type(name) is str and bool(name) and not name.startswith("/") and "\\" not in name
            and ".." not in Path(name).parts and Path(name).as_posix() == name)


def snapshot_union_delivery(root: Path) -> dict:
    """Read the exact packet before interpreting any of its claims."""
    root = Path(root).absolute()
    for ancestor in (root, *root.parents):
        require(not ancestor.is_symlink(), "UNION_PARENT_ANCESTOR_SYMLINK")
    require(root.is_dir(), "UNION_PARENT_ROOT")
    expected = set(load_lock()["upstream_parent_contract"]["inventory"]["delivery_members"])
    directories = {str(Path(name).parent) for name in expected}
    directories |= {str(p) for name in expected for p in Path(name).parents}
    raw, modes = {}, {}
    for directory, dirs, files in os.walk(root, followlinks=False):
        current = Path(directory)
        require(not current.is_symlink() and not current.stat().st_mode & 0o7000,
                "UNION_PARENT_UNSAFE_DIRECTORY")
        for name in dirs:
            child = current / name
            require(not child.is_symlink() and child.relative_to(root).as_posix() in directories,
                    "UNION_PARENT_UNEXPECTED_DIRECTORY")
        for name in files:
            path = current / name
            relative = path.relative_to(root).as_posix()
            require(safe_relative(relative) and relative in expected and relative not in raw,
                    "UNION_PARENT_MEMBER_SET")
            before = path.lstat()
            require(stat.S_ISREG(before.st_mode) and not before.st_mode & 0o7000
                    and 0 <= before.st_size <= 16 * 1024 * 1024, "UNION_PARENT_UNSAFE_FILE")
            value = regular_file(path)
            after = path.lstat()
            attributes = ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns")
            require(all(getattr(before, k) == getattr(after, k) for k in attributes), "UNION_PARENT_READ_DRIFT")
            raw[relative] = value
            modes[relative] = stat.S_IMODE(after.st_mode)
    require(set(raw) == expected and len(raw) == 110 and sum(map(len, raw.values())) <= 32 * 1024 * 1024,
            "UNION_PARENT_EXACT_110_FILES")
    return {"raw": raw, "modes": modes}


def union_payload_identity(packet: dict) -> dict:
    return {name: {**info(raw), "mode": packet["modes"][name]} for name, raw in sorted(packet["raw"].items())}


def verify_parent_xml(raw: bytes, source_bytes: dict, rows: dict, place_pin: dict, non_source_pin: dict) -> None:
    require(info(raw) == place_pin, "UNION_PARENT_PLACE_PIN")
    xml = ET.fromstring(raw)
    by_route = {row["route"]: (name, row) for name, row in rows.items()}
    observed, instances = {}, {}

    def visit(item, parent):
        props = item.find("Properties")
        require(props is not None, "UNION_PARENT_XML_PROPERTIES")
        names = [p for p in props if p.get("name") == "Name"]
        require(len(names) == 1 and names[0].text, "UNION_PARENT_XML_NAME")
        route = "/".join(filter(None, (parent, names[0].text)))
        require(route not in instances, "UNION_PARENT_XML_DUPLICATE_ROUTE")
        instances[route] = item.get("class")
        bodies = [p for p in props if p.get("name") == "Source"]
        if item.get("class") in {"Script", "LocalScript", "ModuleScript"}:
            require(len(bodies) == 1 and bodies[0].tag in {"string", "ProtectedString"}, "UNION_PARENT_XML_SOURCE")
        require(len(bodies) <= 1, "UNION_PARENT_XML_DUPLICATE_SOURCE")
        if bodies:
            require(route in by_route and route not in observed, "UNION_PARENT_XML_SOURCE_ROUTE")
            name, row = by_route[route]
            body = (bodies[0].text or "").encode("utf-8")
            require(item.get("class") == row["class"] and body == source_bytes[name], "UNION_PARENT_XML_BODY")
            observed[route] = True
            bodies[0].text = "__SOURCE_OMITTED_FOR_NON_SOURCE_COMPARISON__"
        for child in item.findall("Item"):
            visit(child, route)

    for item in xml.findall("Item"):
        visit(item, "")
    require(len(instances) == 75 and set(observed) == set(by_route), "UNION_PARENT_XML_75_69")
    require(info(ET.tostring(xml, encoding="utf-8")) == non_source_pin, "UNION_PARENT_XML_NON_SOURCE")


def verify_union_parent(packet: dict, expected_context: dict) -> dict:
    """Verify archived content and external context; never attest the upstream host."""
    context = validate_parent_context(expected_context)
    lock = load_lock()
    contract, raw = lock["upstream_parent_contract"], packet["raw"]
    code = contract["contract_code"]
    pin = lambda name: info(raw[name])
    read = lambda name: parse(raw[name])
    codepin = lambda name: {k: code[name][k] for k in ("bytes", "sha256")}
    require(set(raw) == set(contract["inventory"]["delivery_members"]), "UNION_PARENT_MEMBER_SET")
    manifest = read(UNION_MANIFEST)
    require(typed_equal(manifest, {"schema": "UNION22_DELIVERY_FILES_V1", "current_place": PLACE,
                        "manifest_self_excluded": True, "files": {n: pin(n) for n in sorted(raw) if n != UNION_MANIFEST}}),
            "UNION_PARENT_MANIFEST_GRAPH")
    require(pin("UNION22_PROFILE_LOCK.json") == codepin("profile"), "UNION_PARENT_PROFILE_PIN")
    profile = read("UNION22_PROFILE_LOCK.json")
    rows = {name: {**row["after"], "class": row["class"], "route": row["route"]}
            for name, row in profile["sources"].items()}
    require(profile.get("schema") == contract["profile_schema"] and rows == lock["input_sources"]
            and rows == contract["source_rows"], "UNION_PARENT_EXACT_SOURCE_PROFILE")
    sources = {name: raw["sources/" + name] for name in rows}
    require(all(info(sources[n]) == {k: row[k] for k in ("bytes", "sha256")} for n, row in rows.items()),
            "UNION_PARENT_SOURCE_PIN")
    require(pin(PROJECT) == contract["project"] and project_selection(raw[PROJECT]) ==
            {r["route"]: {"path": "sources/" + n, "class": r["class"]} for n, r in rows.items()},
            "UNION_PARENT_PROJECT_PIN")
    non_source = {k: contract["non_source_normalizations"]["union_parent"][k] for k in ("bytes", "sha256")}
    verify_parent_xml(raw[PLACE], sources, rows, contract["place"], non_source)
    # The rollback contains the actual prior 69 Sources and Place, not an inferred inverse.
    off = {}
    expected_off_names = {"sources/" + n for n in rows} | {PROJECT, PLACE, UNION_RECEIPT} | set(profile["prior_report_names"])
    with tarfile.open(fileobj=io.BytesIO(raw[UNION_ARCHIVE]), mode="r:gz") as archive:
        for member in archive:
            require(len(off) < 75, "UNION_PARENT_ROLLBACK_MEMBER_COUNT")
            require(member.isfile() and safe_relative(member.name) and member.name.startswith(UNION_OFF + "/")
                    and not member.mode & 0o7000, "UNION_PARENT_UNSAFE_ROLLBACK")
            name = member.name[len(UNION_OFF) + 1:]
            require(name in expected_off_names and name not in off and 0 <= member.size <= 2 * 1024 * 1024,
                    "UNION_PARENT_ROLLBACK_MEMBER_SET")
            stream = archive.extractfile(member)
            require(stream is not None, "UNION_PARENT_ROLLBACK_READ")
            off[name] = stream.read(member.size + 1)
            require(len(off[name]) == member.size, "UNION_PARENT_ROLLBACK_SIZE")
    require(set(off) == expected_off_names and len(off) == 75, "UNION_PARENT_ROLLBACK_EXACT_SET")
    before_rows = {n: {**r["before"], "class": r["class"], "route": r["route"]} for n, r in profile["sources"].items()}
    before_sources = {n: off["sources/" + n] for n in rows}
    require(all(info(before_sources[n]) == profile["sources"][n]["before"] for n in rows)
            and off[PROJECT] == raw[PROJECT], "UNION_PARENT_ROLLBACK_SOURCE_PROJECT")
    verify_parent_xml(off[PLACE], before_sources, before_rows, profile["prior_place"], non_source)
    prior = {n[len("prior_boundary/"):]: pin(n) for n in raw if n.startswith("prior_boundary/")}
    require(len(prior) == 12 and sum(n.startswith("legacy_rollbacks/") for n in prior) == 8,
            "UNION_PARENT_PRIOR_INVENTORY")
    for name in {UNION_RECEIPT, *profile["prior_report_names"]}:
        require(off[name] == raw["prior_boundary/" + name], "UNION_PARENT_ROLLBACK_PRIOR_LINK")
    receipt = read(UNION_RECEIPT)
    untested = {"legacy_48_all_ported": False, "owner_accepted": False, "art_gate": "ART_NO_GO",
                "product_gate": "PRODUCT_NO_GO", "studio_solo": "NOT_TESTED", "studio_two_client": "NOT_TESTED",
                "android_15min": "NOT_TESTED", "fun": "NOT_TESTED"}
    expected_receipt = {"schema": contract["receipt_schema"], "feature_id": profile["feature_id"],
        "source_profile": "REAL69", "private_companion_profile": "REAL69_UNION22",
        "official_branch": "rc/p0d-s1-kids-rc01", "build_head": context["build_head"], "execution_context": context,
        "canonical_build": context["canonical_build"], "receipt_provenance": context["kind"],
        "official_build_head": context["official_build_head"], "formal_rc_adoption_proven": context["kind"] == "OFFICIAL",
        "selected_source_count": 69, "changed_source_count": 22, "unchanged_source_count": 47,
        "source_hashes": {r["route"]: r["sha256"] for r in rows.values()},
        "source_classes": {r["route"]: r["class"] for r in rows.values()},
        "private_place_bytes": contract["place"]["bytes"], "private_place_sha256": contract["place"]["sha256"],
        "prior_place": profile["prior_place"], "prior_receipt": info(off[UNION_RECEIPT]),
        "profile_lock": codepin("profile"), "prior_evidence": prior, "runtime_rollback_archive": pin(UNION_ARCHIVE),
        "identity_receipt_is_not_final_delivery_admission": True, "roblox_publish": False, "paid_trade": False,
        **untested, **profile["runtime_labels"]}
    require(typed_equal(receipt, expected_receipt), "UNION_PARENT_SOURCE_RECEIPT_FACTS")
    core = read("CORE_BUILD_REPORT.json")
    prior_snapshot = {"sources/" + n: info(v) for n, v in before_sources.items()}
    prior_snapshot.update({PROJECT: pin(PROJECT), PLACE: profile["prior_place"], UNION_RECEIPT: info(off[UNION_RECEIPT])})
    prior_snapshot.update({"reports/" + n: p for n, p in prior.items()})
    staged = {"sources/" + n: info(v) for n, v in sources.items()}
    staged.update({UNION_OFF + "/" + n: info(v) for n, v in off.items()})
    staged.update({"prior_boundary/" + n: p for n, p in prior.items()})
    staged.update({PROJECT: pin(PROJECT), PLACE: pin(PLACE), UNION_ARCHIVE: pin(UNION_ARCHIVE)})
    core_facts = {"schema": "GQ470_UNION22_CORE_BUILD_V1", "status": "PASS_SOURCE_BUILD_ONLY", "context": context,
        "source_count": 69, "changed_sources": 22, "unchanged_sources": 47, "instances": 75,
        "compile_count": 138, "rojo_build_count": 2, "final_delivery_created": False,
        "actual_inverse_source_and_place_exact": True, "original_receipt_preserved_byte_exact": True,
        "staged_payload_verified_after_all_commands": True, "staged_payload": staged, "prior_snapshot": prior_snapshot,
        "final_place": pin(PLACE), "off_place": profile["prior_place"], "profile_lock": codepin("profile"),
        "composer": codepin("composer"), "non_source_property_identity": non_source,
        "rojo": {k: profile["rojo"][k] for k in ("bytes", "sha256")}}
    require(all(typed_equal(core.get(k), v) for k, v in core_facts.items()), "UNION_PARENT_CORE_FACTS")
    commands, namespace = core.get("commands", []), core.get("build_command_namespace", {})
    stage = namespace.get("executed_stage")
    require(type(stage) is str and Path(stage).is_absolute() and namespace.get("commands_are_actual_pre_rename_paths") is True
            and type(namespace.get("committed_root")) is str and Path(namespace["committed_root"]).is_absolute(),
            "UNION_PARENT_CORE_NAMESPACE")
    require(len(commands) == 140 and all(type(c.get("exit")) is int and c["exit"] == 0 for c in commands),
            "UNION_PARENT_CORE_COMMANDS")
    compiles = [c["command"] for c in commands if len(c.get("command", [])) == 3 and c["command"][1] == "--text"]
    builds = [c["command"] for c in commands if len(c.get("command", [])) == 5 and c["command"][1] == "build" and c["command"][3] == "-o"]
    require(len(compiles) == 138 and {c[2] for c in compiles} ==
            {str(Path(stage) / prefix / "sources" / n) for prefix in ("", UNION_OFF) for n in rows}
            and len(builds) == 2 and {(c[2], c[4]) for c in builds} ==
            {(str(Path(stage) / prefix / PROJECT), str(Path(stage) / prefix / PLACE)) for prefix in ("", UNION_OFF)},
            "UNION_PARENT_CORE_COMMAND_TARGETS")
    native = contract["native"]
    source_profile = {n: info(v) for n, v in sources.items()}
    native_common = {"execution_context": context, "input_lock": codepin("native_lock"),
                     "runner": codepin("native_runner"), "source_receipt": pin(UNION_RECEIPT)}
    aggregate = read("native_evidence/receipt.json")
    build = read("native_evidence/build_receipt.json")
    build_facts = {"schema": "UNION22_F46_REPL_BUILD_V1", "status": "PASS_NEW_BUILD", **native_common,
                  **native["toolchain"], "build_exit": 0, "configure_exit": 0,
                  "source_tree_clean_before_after": True, "binary_absent_before_build": True,
                  "build_directory_absent_initially": True}
    require(all(typed_equal(build.get(k), v) for k, v in build_facts.items()), "UNION_PARENT_NATIVE_BUILD_FACTS")
    binary = build.get("binary_before_suites")
    require(type(binary) is dict and set(binary) == {"bytes", "sha256"} and type(binary["bytes"]) is int
            and binary["bytes"] > 0 and re.fullmatch(r"[0-9a-f]{64}", binary["sha256"]) is not None
            and build.get("binary_after_suites") == binary, "UNION_PARENT_NATIVE_BINARY_LINK")
    expected_build_files = {n[len("native_evidence/"):]: pin(n) for n in raw
                            if n.startswith("native_evidence/") and "/" not in n[len("native_evidence/"):]
                            and n not in {"native_evidence/receipt.json", "native_evidence/build_receipt.json"}}
    require(len(expected_build_files) == 7 and build.get("evidence_files") == expected_build_files,
            "UNION_PARENT_NATIVE_BUILD_FILE_LINKS")
    for command in ("configure", "build"):
        record = build.get("commands", {}).get(command, {})
        require(record.get("exit_code") == 0 and all(record.get(stream) == pin("native_evidence/" + command + "." + stream + ".log")
                for stream in ("stdout", "stderr")), "UNION_PARENT_NATIVE_COMMAND_LOG_LINKS")
    source_tree = read("native_evidence/source_tree_manifest.json")
    require(source_tree.get("source_commit") == native["toolchain"]["source_commit"] and
            source_tree.get("source_tree") == native["toolchain"]["source_tree"] and
            len(source_tree.get("files", {})) == 2336 and pin("native_evidence/source_tree_manifest.json") == native["source_tree_manifest"],
            "UNION_PARENT_NATIVE_SOURCE_TREE_MANIFEST")
    suite_links, suite_admission, variants = {}, {}, {}
    for suite_name, suite_contract in native["suites"].items():
        prefix = "native_evidence/" + suite_name + "/"
        suite = read(prefix + "receipt.json")
        program = raw[prefix + "generated.luau"]
        stdout = raw[prefix + "stdout.log"].decode("utf-8")
        cases = [line for line in stdout.splitlines() if line.startswith("CASE\t")]
        traces = [line for line in stdout.splitlines() if line.startswith(("TRACE\t", "METRIC\t"))]
        expected_cases = suite_contract["observed_case_lines_same_in_both_artifacts"]
        suite_facts = {"schema": "UNION22_FULL_RUNTIME_SUITE_V2", "status": "PASS", "suite": suite_name,
            "profile": "union22", **native_common, "source_count_executed_full_body": 28,
            "source_count_pinned": 69, "source_inputs_unchanged": True, "source_profile": source_profile,
            "input_variant": suite_contract["input_variant"], "case_file": suite_contract["case"],
            "case_path": suite_contract["case_path"], "fixture_pins": native["fixture_pins"],
            "exact_complete_pass_vector": True, "expected_case_names": suite_contract["expected_case_names"],
            "cases": cases, "traces": traces, "exit_code": 0, "generated": info(program), "native": binary,
            "stdout": pin(prefix + "stdout.log"), "stderr": pin(prefix + "stderr.log")}
        require(all(typed_equal(suite.get(k), v) for k, v in suite_facts.items()) and cases == expected_cases
                and raw[prefix + "stderr.log"] == b"" and info(program) == native["programs"][suite_name],
                "UNION_PARENT_NATIVE_SUITE_GRAPH_" + suite_name)
        modules = native["modules_in_load_order"]
        names = {"ServerScriptService/EGGRUMBLE_" + n + ".luau" for n in modules}
        ranges = suite.get("full_body_byte_ranges", {})
        require(set(ranges) == names and len(names) == 28, "UNION_PARENT_NATIVE_FULL_BODY_SET")
        spans = []
        for name, span in ranges.items():
            start, end = span.get("start"), span.get("end")
            require(type(start) is int and type(end) is int and 0 <= start < end <= len(program)
                    and span == {**info(sources[name]), "start": start, "end": end}
                    and program[start:end] == sources[name], "UNION_PARENT_NATIVE_FULL_BODY_BYTES")
            spans.append((start, end))
        spans.sort()
        require(all(a[1] <= b[0] for a, b in zip(spans, spans[1:])), "UNION_PARENT_NATIVE_BODY_OVERLAP")
        expected_lines = {}
        for name in modules:
            relative = "ServerScriptService/EGGRUMBLE_" + name + ".luau"
            span = ranges[relative]
            first = program[:span["start"]].count(b"\n") + 1
            label = "Host" if name == "LobbyCastleModesPreview.server" else name
            expected_lines[label] = {"first": first, "last": first + sources[relative].count(b"\n")}
        require(suite.get("source_line_ranges") == expected_lines, "UNION_PARENT_NATIVE_SOURCE_LINES")
        suite_links[suite_name] = pin(prefix + "receipt.json")
        suite_admission[suite_name] = {"case_count": len(expected_cases), "receipt": suite_links[suite_name]}
        variants[suite_name] = suite_contract["input_variant"]
    aggregate_facts = {"schema": "UNION22_NATIVE_BOTH_SUITES_V2", "profile": "union22", "status": "PASS",
        **native_common, "source_count_executed_full_body": 28, "source_count_pinned": 69,
        "source_inputs_unchanged": True, "source_only": True, "formal_rc_adoption_proven": False,
        "source_profile": source_profile, "build_receipt": pin("native_evidence/build_receipt.json"),
        "suites": suite_links, "suite_input_variants": variants,
        "original_combined_case_preserved_not_claimed_as_unchanged_pass": True}
    require(all(typed_equal(aggregate.get(k), v) for k, v in aggregate_facts.items()), "UNION_PARENT_NATIVE_AGGREGATE_GRAPH")
    admission = read("UNION22_FINAL_ADMISSION.json")
    provenance = {"candidate_build_head": context["build_head"], "receipt_provenance": context["kind"],
                  "official_build_head": context["official_build_head"],
                  "formal_rc_adoption_proven": context["kind"] == "OFFICIAL", **profile["runtime_labels"]}
    admission_expected = {"schema": contract["admission_schema"], "status": contract["admission_status"],
        **provenance, **untested, "source_count": 69, "changed_sources": 22, "unchanged_sources": 47,
        "instances": 75, "current_place": pin(PLACE), "inverse_place": profile["prior_place"],
        "inverse_archive_extracted_members": 75, "prior_opaque_rollback_archives_preserved": 8,
        "prior_reports_are_prior_boundary_only": True, "fresh_final_marker_retention": 17,
        "unchanged_all48_auditor_executed_on_final": 48, "visual_source_retention": 3,
        "native_suites": suite_admission, "native_suite_input_variants": variants,
        "original_combined_case_preserved_not_claimed_as_unchanged_pass": True,
        "native_build_receipt": pin("native_evidence/build_receipt.json"), "profile_lock": codepin("profile"),
        "verifier": codepin("verifier")}
    require(typed_equal(admission, admission_expected), "UNION_PARENT_FINAL_ADMISSION_GRAPH")
    # These are archived auditor outputs, not a rerun or evidence about Score8741.
    for name, retained in contract["retention_records"].items():
        data = read(name)
        if name == "UNION22_FINAL_ALL48_RAW.json":
            require(data.get("official_head") == context["build_head"], "UNION_PARENT_ALL48_BUILD_HEAD")
        else:
            require(all(typed_equal(data.get(k), v) for k, v in provenance.items()) and data.get("private_place") == pin(PLACE),
                    "UNION_PARENT_RETENTION_PROVENANCE")
        body = {k: v for k, v in data.items() if k not in retained["context_fields"]}
        require(canonical_digest(body) == retained["body_sha256"], "UNION_PARENT_RETENTION_CONTENT_" + name)
    return {"schema": "SCORE_RELAY_UNION22_PARENT_BINDING_V1", "parent_kind": "UNION22_DELIVERY",
            "expected_execution_context": context, "parent_contract_verified": True,
            "contract_sha256": canonical_digest(contract), "payload": union_payload_identity(packet),
            "source_count": 69, "instance_count": 75, "parent_score": {"bytes": 8030, "sha256": BASE_SHA},
            "native_evidence_scope": "ARCHIVED_PARENT8030_PROGRAM_AND_LOG_GRAPH_ONLY",
            "rollback_files_verified": 75, "opaque_older_archives_preserved": 8, **OWN_UNPROVEN}


def copy_union_packet(packet: dict, output: Path) -> None:
    output.mkdir()
    for relative, raw in packet["raw"].items():
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        target.chmod(packet["modes"][relative])


def verify_stage_parent(root: Path, parent_kind: str, context: dict | None) -> tuple[bytes | None, dict | None]:
    if parent_kind == "FROZEN_LOCAL":
        require(not any((root / n).exists() or (root / n).is_symlink() for n in
                        (PARENT_PACKET, PARENT_BINDING, PARENT_EXPECTATION)), "MIXED_PARENT_MODES")
        return parent_manifest_bytes(root), None
    require(not any((root / n).exists() or (root / n).is_symlink() for n in
                    (PARENT_MANIFEST, "frozen_union22_source_manifest.json", "source_manifest.json")), "MIXED_PARENT_MODES")
    packet = snapshot_union_delivery(root / PARENT_PACKET)
    binding = verify_union_parent(packet, context)
    require(typed_equal(parse(regular_file(root / PARENT_BINDING)), binding), "PARENT_BINDING_SIDECAR")
    require(read_parent_expectation(root / PARENT_EXPECTATION) == context, "PARENT_EXPECTATION_SIDECAR")
    require(snapshot_union_delivery(root / PARENT_PACKET) == packet, "PARENT_COPY_DRIFT")
    return None, binding


def transform_score(raw: bytes, direction: str) -> bytes:
    lock = load_lock()
    fragment = lock["fragment_text"].encode("utf-8")
    require(direction in {"on", "off"}, "DIRECTION")
    if direction == "on":
        require(info(raw) == {"bytes": 8030, "sha256": BASE_SHA}, "ON_INPUT_SOURCE_PIN")
        require(raw.count(ANCHOR) == 1 and fragment not in raw, "ON_UNIQUE_ANCHOR")
        result = raw.replace(ANCHOR, fragment + ANCHOR, 1)
        require(info(result) == {"bytes": 8741, "sha256": AFTER_SHA}, "ON_OUTPUT_SOURCE_PIN")
    else:
        require(info(raw) == {"bytes": 8741, "sha256": AFTER_SHA}, "OFF_INPUT_SOURCE_PIN")
        require(raw.count(fragment + ANCHOR) == 1 and raw.count(fragment) == 1, "OFF_UNIQUE_FRAGMENT")
        result = raw.replace(fragment + ANCHOR, ANCHOR, 1)
        require(info(result) == {"bytes": 8030, "sha256": BASE_SHA}, "OFF_OUTPUT_SOURCE_PIN")
    return result


def expected_sources(lock: dict, profile: str) -> dict:
    require(profile in {"before", "after"}, "PROFILE")
    rows = copy.deepcopy(lock["input_sources"])
    if profile == "after":
        rows[TARGET].update(bytes=8741, sha256=AFTER_SHA)
    return rows


def project_selection(raw: bytes) -> dict:
    data = parse(raw)
    result = {}

    def walk(node, route):
        require(isinstance(node, dict), "PROJECT_NODE")
        if "$path" in node:
            require(route not in result and isinstance(node["$path"], str), "PROJECT_ROUTE")
            selected_path = node["$path"]
            # The pinned Rojo project uses file-based inference. Explicit
            # classes still have to match, and built XML is checked separately.
            inferred = ("Script" if selected_path.endswith(".server.luau") else
                        "LocalScript" if selected_path.endswith(".client.luau") else
                        "ModuleScript" if selected_path.endswith(".luau") else None)
            result[route] = {"path": selected_path, "class": node.get("$className", inferred)}
        for name, child in node.items():
            if not name.startswith("$"):
                walk(child, route + "/" + name if route else name)

    walk(data["tree"], "")
    return result


def capture_sources(root: Path, profile: str) -> tuple[dict, dict, bytes]:
    lock = load_lock()
    root = Path(root)
    require(root.is_dir() and not root.is_symlink() and not root.stat().st_mode & 0o7000, "INPUT_ROOT")
    source_root = root / "sources"
    require(source_root.is_dir() and not source_root.is_symlink(), "SOURCE_ROOT")
    expected = expected_sources(lock, profile)
    found = set()
    for directory, dirs, files in os.walk(source_root, followlinks=False):
        d = Path(directory)
        require(not d.is_symlink() and not d.stat().st_mode & 0o7000, "UNSAFE_SOURCE_DIRECTORY")
        for name in dirs:
            require(not (d / name).is_symlink(), "SOURCE_DIRECTORY_SYMLINK")
        for name in files:
            relative = (d / name).relative_to(source_root).as_posix()
            require(relative in expected, "UNEXPECTED_SOURCE_FILE_" + relative)
            found.add(relative)
    require(found == set(expected), "EXACT_69_SOURCE_FILES")
    contents, rows = {}, {}
    for relative, pin in expected.items():
        path = source_root / relative
        raw = regular_file(path)
        require(info(raw) == {"bytes": pin["bytes"], "sha256": pin["sha256"]}, "SOURCE_PIN_" + relative)
        contents[relative] = raw
        rows[relative] = {**pin, "mode": stat.S_IMODE(path.stat().st_mode)}
    project = regular_file(root / PROJECT)
    require(info(project) == lock["fixed_input"]["project"], "PROJECT_PIN")
    selected = project_selection(project)
    require(len(selected) == 69 and set(selected) == {r["route"] for r in expected.values()}, "PROJECT_69_ROUTES")
    for relative, pin in expected.items():
        require(selected[pin["route"]] == {"path": "sources/" + relative, "class": pin["class"]},
                "PROJECT_PATH_CLASS_" + relative)
    snapshot = {"profile": profile, "source_count": 69, "sources": rows,
                "project": info(project), "project_mode": stat.S_IMODE((root / PROJECT).stat().st_mode),
                "source_lock_sha256": lock["_lock_sha256"]}
    return snapshot, contents, project


def validate_sources(root: Path, profile: str) -> dict:
    return capture_sources(root, profile)[0]


def parent_manifest_bytes(root: Path) -> bytes:
    candidates = [root / name for name in (PARENT_MANIFEST, "frozen_union22_source_manifest.json", "source_manifest.json")
                  if (root / name).exists() or (root / name).is_symlink()]
    require(len(candidates) == 1, "ONE_RAW_PARENT_MANIFEST_REQUIRED")
    raw = regular_file(candidates[0])
    require(digest(raw) == PARENT_MANIFEST_SHA, "RAW_PARENT_MANIFEST_PIN")
    parent, lock = parse(raw), load_lock()
    rows = {path: {key: row[key] for key in ("bytes", "sha256", "class", "route")}
            for path, row in parent["sources"].items()}
    require(parent["source_count"] == 69 and rows == lock["input_sources"], "LOCK_PARENT_ROWS")
    require(parent["project"] == lock["fixed_input"]["project"] and
            parent["place"] == lock["fixed_input"]["place"], "LOCK_PARENT_BUILD_PINS")
    return raw


def verify_place(root: Path, place_path: Path, profile: str) -> dict:
    lock = load_lock()
    snapshot, contents, _ = capture_sources(Path(root), profile)
    raw = regular_file(Path(place_path))
    xml = ET.fromstring(raw)
    expected = {row["route"]: (relative, row) for relative, row in expected_sources(lock, profile).items()}
    sources, items = {}, []

    def visit(item, parent):
        props = item.find("Properties")
        require(props is not None, "XML_PROPERTIES")
        names = [x for x in props if x.attrib.get("name") == "Name"]
        require(len(names) == 1, "XML_UNIQUE_NAME")
        route = "/".join(x for x in (parent, names[0].text or "") if x)
        klass = item.attrib.get("class")
        items.append((route, klass))
        body = [x for x in props if x.attrib.get("name") == "Source"]
        if body:
            require(len(body) == 1 and route in expected and route not in sources, "XML_SOURCE_ROUTE")
            relative, row = expected[route]
            value = (body[0].text or "").encode("utf-8")
            require(klass == row["class"] and value == contents[relative], "XML_SOURCE_BODY_CLASS_" + route)
            sources[route] = info(value)
        for child in item.findall("Item"):
            visit(child, route)

    for item in xml.findall("Item"):
        visit(item, "")
    require(len(items) == 75 and set(sources) == set(expected), "XML_75_ITEMS_69_SOURCES")
    for props in xml.iter("Properties"):
        for prop in props:
            if prop.attrib.get("name") == "Source":
                prop.text = "SOURCE_BODY_OMITTED"
    non_source = digest(ET.tostring(xml, encoding="utf-8"))
    require(non_source == lock["fixed_input"]["non_source_xml_sha256"], "XML_NON_SOURCE_PRESERVATION")
    if profile == "before":
        require(info(raw) == lock["fixed_input"]["place"], "ACTUAL_INVERSE_PLACE_BYTE_EXACT")
    require(validate_sources(Path(root), profile) == snapshot, "SOURCE_DRIFT_DURING_PLACE_CHECK")
    return {**info(raw), "source_count": 69, "item_count": 75, "non_source_xml_sha256": non_source,
            "profile": profile, "place_built_by_this_verifier": False}


def verify_receipt_metadata(receipt: dict, snapshot: dict, manifest_raw: bytes, parent: bytes | None,
                            parent_kind: str, context: dict | None, binding_pin: dict | None,
                            expectation_pin: dict | None) -> dict:
    """Bind a receipt to actual bytes and both exact source profiles.

    The inverse uses this same check for the preserved raw ON receipt. This is
    local execution evidence; it does not establish provider attestation.
    """
    profile = snapshot["profile"]
    manifest = parse(manifest_raw)
    require(manifest == {"schema": "SCORE_RELAY_PREP_SOURCE_MANIFEST_V1", "status": STATUS, **snapshot},
            "STAGE_MANIFEST_BINDING")
    require(receipt.get("schema") == "SCORE_RELAY_PREP_RECEIPT_V3" and receipt.get("status") == STATUS,
            "STAGE_RECEIPT_SCHEMA_STATUS")
    require(receipt.get("output_profile") == profile and receipt.get("output_snapshot") == snapshot,
            "STAGE_RECEIPT_OUTPUT")
    direction = "on" if profile == "after" else "off"
    expected_input = copy.deepcopy(snapshot)
    expected_input["profile"] = "before" if profile == "after" else "after"
    expected_input["sources"][TARGET].update(
        bytes=8030 if profile == "after" else 8741,
        sha256=BASE_SHA if profile == "after" else AFTER_SHA)
    require(receipt.get("direction") == direction and
            receipt.get("input_profile") == expected_input["profile"] and
            receipt.get("input_snapshot") == expected_input, "STAGE_RECEIPT_INPUT")
    require(receipt.get("only_changed_source") == TARGET and receipt.get("source_count") == 69
            and receipt.get("other_sources_preserved") == 68, "STAGE_RECEIPT_SCOPE")
    require(receipt.get("inverse_reads_actual_on_source") is (direction == "off"), "STAGE_RECEIPT_INVERSE")
    require(receipt.get("Native_executed_by_composer") is False and receipt.get("Place_built_by_composer") is False
            and receipt.get("RC_adopted_by_composer") is False
            and receipt.get("Studio_Android_ART_FUN") == "NOT_VERIFIED", "STAGE_RECEIPT_UNEARNED_EVIDENCE")
    if direction == "on":
        require(receipt.get("parent_stage_receipt") is None and
                receipt.get("parent_stage_manifest") is None, "STAGE_RECEIPT_PARENT")
    require(receipt.get("source_lock_sha256") == load_lock()["_lock_sha256"] and
            receipt.get("manifest") == info(manifest_raw) and receipt.get("parent_manifest") == (info(parent) if parent is not None else None),
            "STAGE_RECEIPT_PIN")
    require(receipt.get("final_union_contract_bound") is False and receipt.get("canonical_build") is False
            and receipt.get("official_build_head") is None, "STAGE_UNEARNED_PROVENANCE")
    require(receipt.get("parent_kind") == parent_kind and typed_equal(receipt.get("expected_parent_context"), context)
            and receipt.get("parent_binding") == binding_pin and receipt.get("parent_expectation") == expectation_pin
            and receipt.get("parent_contract_verified") is (parent_kind == "UNION22_DELIVERY")
            and all(receipt.get(k) is v for k, v in OWN_UNPROVEN.items()), "STAGE_PARENT_BINDING_OR_UNEARNED_CLAIM")
    return expected_input


def verify_stage(root: Path, profile: str = "after", *, parent_kind: str = "FROZEN_LOCAL",
                 expected_parent_context: dict | None = None) -> dict:
    context = parent_arguments(parent_kind, expected_parent_context)
    root = Path(root)
    snapshot = validate_sources(root, profile)
    parent, binding = verify_stage_parent(root, parent_kind, context)
    binding_raw = regular_file(root / PARENT_BINDING) if binding is not None else None
    expectation_raw = regular_file(root / PARENT_EXPECTATION) if binding is not None else None
    binding_pin = info(binding_raw) if binding_raw is not None else None
    expectation_pin = info(expectation_raw) if expectation_raw is not None else None
    manifest_raw, receipt_raw = regular_file(root / MANIFEST), regular_file(root / RECEIPT)
    receipt = parse(receipt_raw)
    expected_input = verify_receipt_metadata(receipt, snapshot, manifest_raw, parent,
                                            parent_kind, context, binding_pin, expectation_pin)
    inverse_raw = {}
    if profile == "before":
        on_receipt_raw = regular_file(root / INVERSE_INPUT_RECEIPT)
        on_manifest_raw = regular_file(root / INVERSE_INPUT_MANIFEST)
        inverse_raw = {INVERSE_INPUT_RECEIPT: on_receipt_raw, INVERSE_INPUT_MANIFEST: on_manifest_raw}
        require(receipt.get("parent_stage_receipt") == info(on_receipt_raw) and
                receipt.get("parent_stage_manifest") == info(on_manifest_raw), "INVERSE_INPUT_EVIDENCE_PIN")
        verify_receipt_metadata(parse(on_receipt_raw), expected_input, on_manifest_raw, parent,
                                parent_kind, context, binding_pin, expectation_pin)
    else:
        require(not any((root / name).exists() or (root / name).is_symlink()
                        for name in (INVERSE_INPUT_RECEIPT, INVERSE_INPUT_MANIFEST)),
                "ON_STAGE_HAS_INVERSE_EVIDENCE")
    result = {"status": STATUS, "profile": profile, "snapshot": snapshot,
              "manifest": info(manifest_raw), "receipt": info(receipt_raw),
              "parent_manifest": info(parent) if parent is not None else None,
              "parent_kind": parent_kind, "expected_parent_context": context,
              "parent_binding": binding_pin, "parent_expectation": expectation_pin,
              "parent_contract_verified": binding is not None, **OWN_UNPROVEN}
    if (root / PLACE).exists() or (root / PLACE).is_symlink():
        result["place"] = verify_place(root, root / PLACE, profile)
    require(validate_sources(root, profile) == snapshot and regular_file(root / RECEIPT) == receipt_raw
            and regular_file(root / MANIFEST) == manifest_raw
            and all(regular_file(root / n) == value for n, value in inverse_raw.items()), "STAGE_VERIFICATION_DRIFT")
    if binding is not None:
        require(union_payload_identity(snapshot_union_delivery(root / PARENT_PACKET)) == binding["payload"]
                and regular_file(root / PARENT_BINDING) == binding_raw
                and regular_file(root / PARENT_EXPECTATION) == expectation_raw, "STAGE_PARENT_VERIFICATION_DRIFT")
    else:
        require(parent_manifest_bytes(root) == parent, "STAGE_PARENT_VERIFICATION_DRIFT")
    return result


def compose(input_root: Path, output_root: Path, direction: str = "on", *,
            parent_kind: str = "FROZEN_LOCAL", expected_parent_context: dict | None = None) -> dict:
    context = parent_arguments(parent_kind, expected_parent_context)
    require(direction in {"on", "off"}, "DIRECTION")
    input_root, output_root = Path(input_root), Path(output_root)
    require(not output_root.exists() and not output_root.is_symlink(), "OUTPUT_EXISTS")
    source_abs, out_abs = input_root.resolve(), output_root.resolve()
    require(source_abs != out_abs and source_abs not in out_abs.parents and out_abs not in source_abs.parents,
            "INPUT_OUTPUT_OVERLAP")
    for path in (output_root.parent, *output_root.parent.parents):
        require(not path.is_symlink(), "OUTPUT_ANCESTOR_SYMLINK")
    before_profile, after_profile = ("before", "after") if direction == "on" else ("after", "before")
    packet, binding, parent = None, None, None
    packet_root = input_root if direction == "on" else input_root / PARENT_PACKET
    if parent_kind == "UNION22_DELIVERY":
        packet = snapshot_union_delivery(packet_root)
        binding = verify_union_parent(packet, context)
    original, contents, project = capture_sources(input_root, before_profile)
    if parent_kind == "FROZEN_LOCAL":
        parent, _ = verify_stage_parent(input_root, parent_kind, context)
    elif direction == "on":
        require(project == packet["raw"][PROJECT] and
                all(value == packet["raw"]["sources/" + n] for n, value in contents.items()),
                "UNION_PARENT_SOURCE_SNAPSHOT_DRIFT")
    input_stage = verify_stage(input_root, "after", parent_kind=parent_kind,
                               expected_parent_context=context) if direction == "off" else None
    on_evidence = {}
    if input_stage is not None:
        for original_name, copy_name, pin_name in (
                (RECEIPT, INVERSE_INPUT_RECEIPT, "receipt"),
                (MANIFEST, INVERSE_INPUT_MANIFEST, "manifest")):
            value = regular_file(input_root / original_name)
            require(info(value) == input_stage[pin_name], "ON_EVIDENCE_DRIFT_BEFORE_COPY")
            on_evidence[copy_name] = value
    transformed = dict(contents)
    transformed[TARGET] = transform_score(contents[TARGET], direction)
    require([k for k in contents if contents[k] != transformed[k]] == [TARGET], "ONE_SELECTED_SOURCE_CHANGE")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    output_root.mkdir()
    try:
        for relative, value in transformed.items():
            target = output_root / "sources" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(value)
            target.chmod(original["sources"][relative]["mode"])
        (output_root / PROJECT).write_bytes(project)
        (output_root / PROJECT).chmod(original["project_mode"])
        binding_pin, expectation_pin = None, None
        if packet is not None:
            copy_union_packet(packet, output_root / PARENT_PACKET)
            binding_raw = json_bytes(binding)
            expectation_raw = json_bytes({"schema": "SCORE_RELAY_EXTERNAL_PARENT_EXPECTATION_V1",
                                          "expected_execution_context": context})
            (output_root / PARENT_BINDING).write_bytes(binding_raw)
            (output_root / PARENT_EXPECTATION).write_bytes(expectation_raw)
            binding_pin, expectation_pin = info(binding_raw), info(expectation_raw)
            require(snapshot_union_delivery(output_root / PARENT_PACKET) == packet, "UNION_PARENT_COPY_NOT_EXACT")
        else:
            (output_root / PARENT_MANIFEST).write_bytes(parent)
        for name, value in on_evidence.items():
            (output_root / name).write_bytes(value)
        final = validate_sources(output_root, after_profile)
        require(validate_sources(input_root, before_profile) == original, "INPUT_DRIFT_DURING_COMPOSITION")
        if packet is not None:
            require(snapshot_union_delivery(packet_root) == packet, "UNION_PARENT_INPUT_DRIFT_DURING_COMPOSITION")
        else:
            require(parent_manifest_bytes(input_root) == parent, "INPUT_DRIFT_DURING_COMPOSITION")
        if input_stage is not None:
            require(verify_stage(input_root, "after", parent_kind=parent_kind, expected_parent_context=context)
                    == input_stage, "ON_STAGE_DRIFT_DURING_INVERSE")
        require(final["source_lock_sha256"] == original["source_lock_sha256"], "LOCK_DRIFT_DURING_COMPOSITION")
        manifest = {"schema": "SCORE_RELAY_PREP_SOURCE_MANIFEST_V1", "status": STATUS, **final}
        manifest_raw = json_bytes(manifest)
        (output_root / MANIFEST).write_bytes(manifest_raw)
        receipt = {"schema": "SCORE_RELAY_PREP_RECEIPT_V3", "status": STATUS,
                   "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   "direction": direction, "input_profile": before_profile, "output_profile": after_profile,
                   "input_snapshot": original, "output_snapshot": final,
                   "only_changed_source": TARGET, "source_count": 69, "other_sources_preserved": 68,
                   "source_lock_sha256": final["source_lock_sha256"],
                   "parent_manifest": info(parent) if parent is not None else None,
                   "parent_kind": parent_kind, "expected_parent_context": context,
                   "parent_binding": binding_pin, "parent_expectation": expectation_pin,
                   "parent_contract_verified": packet is not None,
                   "manifest": info(manifest_raw), "inverse_reads_actual_on_source": direction == "off",
                   "parent_stage_receipt": input_stage["receipt"] if input_stage else None,
                   "parent_stage_manifest": input_stage["manifest"] if input_stage else None,
                   "Native_executed_by_composer": False, "Place_built_by_composer": False,
                   "Studio_Android_ART_FUN": "NOT_VERIFIED", "RC_adopted_by_composer": False, **OWN_UNPROVEN}
        (output_root / RECEIPT).write_bytes(json_bytes(receipt))
        result = verify_stage(output_root, after_profile, parent_kind=parent_kind, expected_parent_context=context)
        # Do not publish a success marker if the input changed during final verification.
        require(validate_sources(input_root, before_profile) == original, "INPUT_DRIFT_AFTER_FINAL_VERIFICATION")
        if packet is not None:
            require(snapshot_union_delivery(packet_root) == packet, "UNION_PARENT_INPUT_DRIFT_AFTER_FINAL_VERIFICATION")
        else:
            require(parent_manifest_bytes(input_root) == parent, "INPUT_DRIFT_AFTER_FINAL_VERIFICATION")
        if input_stage is not None:
            require(verify_stage(input_root, "after", parent_kind=parent_kind, expected_parent_context=context)
                    == input_stage, "ON_STAGE_DRIFT_AFTER_FINAL_VERIFICATION")
        return result
    except BaseException:
        # Only our new output is touched; partial evidence remains for diagnosis.
        (output_root / RECEIPT).unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    actions = []
    for action in ("compose", "inverse"):
        command = sub.add_parser(action)
        command.add_argument("--input", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
        actions.append(command)
    command = sub.add_parser("verify")
    command.add_argument("--root", type=Path, required=True)
    command.add_argument("--profile", choices=("before", "after"), default="after")
    actions.append(command)
    for command in actions:
        command.add_argument("--parent-kind", choices=("frozen-local", "union22-delivery"), default="frozen-local")
        command.add_argument("--expected-parent-context", type=Path)
    sub.add_parser("verify-final", help="Blocked until the final Score workflow and union contract are bound")
    args = parser.parse_args()
    if args.command == "verify-final":
        raise ScoreRelayError("FINAL_UNION_CONTRACT_NOT_BOUND")
    context_raw = regular_file(args.expected_parent_context) if args.expected_parent_context is not None else None
    context = read_parent_expectation(args.expected_parent_context) if context_raw is not None else None
    if context_raw is not None:
        require(regular_file(args.expected_parent_context) == context_raw, "EXTERNAL_PARENT_EXPECTATION_READ_DRIFT")
    kwargs = {"parent_kind": args.parent_kind.replace("-", "_").upper(), "expected_parent_context": context}
    if args.command == "verify":
        result = verify_stage(args.root, args.profile, **kwargs)
    else:
        result = compose(args.input, args.output, "on" if args.command == "compose" else "off", **kwargs)
    if context_raw is not None:
        try:
            require(regular_file(args.expected_parent_context) == context_raw, "EXTERNAL_PARENT_EXPECTATION_FINAL_DRIFT")
        except BaseException:
            if args.command in {"compose", "inverse"}:
                (args.output / RECEIPT).unlink(missing_ok=True)
            raise
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
