#!/usr/bin/env python3
"""Admit the final union only after independent exact-source and Native checks.

The original whole nonloss/ART gates stay at their original BR-only boundary.
Here their unchanged marker and all48 functions inspect the actual final source.
Their prior reports remain explicitly prior evidence, not final execution proof.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
import compose_union22 as compose

HELPERS = {
    "quality_gameplay/gq8_rc85_rc86_real69_nonloss_20261120/verify_real69.py": "afcc6aa9215775f0495fed7fe2a1e6bb488072faebb7ec7943840cc3be53cba3",
    "quality_gameplay/gq8_rc85_rc86_real69_feature_truth_20261120/audit_legacy48.py": "fdbb8d7ef2978567364e4ad5b585cd90a946fa5ff38e008f5c2120ef9077a7dc",
    "quality_gameplay/gq8_rc85_rc86_real69_feature_truth_20261120/legacy48.json": "15893c3cf7af42dc03b38eaa72c3402f77781876a2714a82483f3e5f2f5d448a",
    "quality_gameplay/gq8_rc85_rc86_real68_nonloss_20261120/verify_nonloss.py": "c476de3d990febcdff6ef6cd971af31389b30ed0f23622263ab461ac86d1c50b",
    "art_quality/gq470_real69_source_gate.py": "5dd5c121cf59e7ec90d02790f1e53150a0074d7b9544ffbca065ddd10d26c578",
    "quality_gameplay/gq470_art_pr_provenance_20261121/guard.py": "5776cee1145742e2e5b1e830fb08243143b1bdb3b8cdfc7a0e2a27ec8df30a0f",
}


def require(value, reason):
    if not value:
        raise ValueError("RED_UNION22_FINAL_" + reason)


def digest(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def read(path):
    path = Path(path)
    require(not path.is_symlink() and path.is_file(), "REGULAR_FILE_REQUIRED:" + str(path))
    require(stat.S_ISREG(path.stat().st_mode) and not path.stat().st_mode & 0o7000,
            "REGULAR_FILE_SPECIAL_MODE:" + str(path))
    return path.read_bytes()


def data(path):
    return compose.strict_json(read(path))


def files(root):
    root = Path(root)
    require(root.is_dir() and not root.is_symlink(), "DIRECTORY_REQUIRED")
    require(not root.stat().st_mode & 0o7000, "PAYLOAD_DIRECTORY_SPECIAL_MODE")
    result = {}
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), "SYMLINK_IN_PAYLOAD")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = digest(read(path))
        else:
            require(path.is_dir(), "SPECIAL_FILE_IN_PAYLOAD")
            require(not path.stat().st_mode & 0o7000, "PAYLOAD_DIRECTORY_SPECIAL_MODE")
    return result


def independent_scan(root, lock, boundary):
    """A separate XML/project/69-file interpretation, not producer booleans."""
    project_raw = read(root / compose.PROJECT)
    require(digest(project_raw) == lock["project"], "PROJECT_IDENTITY")
    project = compose.strict_json(project_raw)
    paths = {}
    def selected(node, parts):
        require(isinstance(node, dict), "PROJECT_NODE")
        if "$path" in node:
            route = "/".join(parts)
            rel = node["$path"]
            require(isinstance(rel, str) and rel.startswith("sources/") and route not in paths,
                    "PROJECT_PATH")
            pure = PurePosixPath(rel)
            require(not pure.is_absolute() and ".." not in pure.parts and "\\" not in rel,
                    "PROJECT_PATH_ESCAPE")
            paths[route] = rel.removeprefix("sources/")
        for name, value in node.items():
            if not name.startswith("$"):
                selected(value, parts + [name])
    require(project["tree"].get("$className") == "DataModel", "PROJECT_ROOT")
    selected(project["tree"], [])
    require(paths == {row["route"]: p for p, row in lock["sources"].items()}, "PROJECT_ROUTE_SET")
    source_files = files(root / "sources")
    require(source_files == {p: row[boundary] for p, row in lock["sources"].items()}, "SOURCE_69_IDENTITY")
    place_raw = read(root / compose.PLACE)
    require(digest(place_raw) == lock["prior_place" if boundary == "before" else "final_place"],
            "PLACE_IDENTITY")
    tree = ET.fromstring(place_raw)
    observed, instances = {}, {}
    def inspect(item, parent):
        props = item.find("Properties")
        require(props is not None, "INSTANCE_PROPERTIES")
        names = [p for p in props if p.tag == "string" and p.get("name") == "Name"]
        require(len(names) == 1 and names[0].text, "INSTANCE_NAME")
        route = "/".join(parent + [names[0].text])
        require(route not in instances, "INSTANCE_ROUTE_DUPLICATE")
        instances[route] = item.get("class")
        src = [p for p in props if p.get("name") == "Source"]
        require(len(src) <= 1, "SOURCE_PROPERTY_DUPLICATE")
        if item.get("class") in ("Script", "ModuleScript", "LocalScript"):
            require(len(src) == 1 and src[0].tag in ("string", "ProtectedString"), "SOURCE_PROPERTY_MISSING")
        if src:
            require(route in paths and route not in observed, "UNSELECTED_EMBEDDED_SOURCE")
            raw = (src[0].text or "").encode("utf-8")
            row = lock["sources"][paths[route]]
            require(item.get("class") == row["class"] and digest(raw) == row[boundary]
                    and raw == read(root / "sources" / paths[route]), "EMBEDDED_SOURCE_MISMATCH")
            observed[route] = {"class": row["class"], "path": paths[route], "source": raw,
                               "sha256": row[boundary]["sha256"]}
            src[0].text = "__SOURCE_OMITTED_FOR_NON_SOURCE_COMPARISON__"
        for child in item.findall("Item"):
            inspect(child, parent + [names[0].text])
    for item in tree.findall("Item"):
        inspect(item, [])
    require(len(instances) == 75 and len(observed) == 69
            and Counter(x["class"] for x in observed.values()) == compose.CLASSES, "INSTANCE_SOURCE_COUNTS")
    return {"sources": observed, "non_source": ET.tostring(tree, encoding="utf-8"),
            "source_files": source_files, "instances": instances, "place": digest(place_raw)}


def independent_inverse(raw, hunks):
    lines, rebuilt, cursor = raw.decode("utf-8").splitlines(keepends=True), [], 0
    prior_pair = None
    for h in hunks:
        pair = (h["start"], h["stop"])
        require(type(pair[0]) is int and type(pair[1]) is int
                and cursor <= pair[0] <= pair[1] <= len(lines) and pair != prior_pair, "INVERSE_RANGE")
        require("".join(lines[pair[0]:pair[1]]) == h["old"]
                and digest(h["old"].encode()) == h["old_identity"]
                and digest(h["new"].encode()) == h["new_identity"], "INVERSE_REMOVED_BYTES")
        rebuilt.extend(lines[cursor:pair[0]])
        rebuilt.append(h["new"])
        cursor, prior_pair = pair[1], pair
    rebuilt.extend(lines[cursor:])
    return "".join(rebuilt).encode("utf-8")


def verify_archive(path, expected, prefix=compose.OFF):
    # Manual regular-file extraction: no tar extraction APIs, links or traversal.
    observed = {}
    with tempfile.TemporaryDirectory(prefix="union22-inverse-verify-") as tmp:
        with tarfile.open(path, "r:gz") as archive:
            members = archive.getmembers()
            require(len(members) == len(expected), "ARCHIVE_MEMBER_COUNT")
            for member in members:
                pure = PurePosixPath(member.name)
                require(member.isfile() and not pure.is_absolute() and ".." not in pure.parts
                        and "\\" not in member.name and pure.parts[0] == prefix,
                        "UNSAFE_ARCHIVE_MEMBER")
                require(not member.mode & 0o7000, "ARCHIVE_SPECIAL_MODE")
                relative = PurePosixPath(*pure.parts[1:]).as_posix()
                require(relative in expected and relative not in observed, "ARCHIVE_MEMBER_SET")
                require(member.size == expected[relative]["bytes"], "ARCHIVE_MEMBER_SIZE")
                stream = archive.extractfile(member)
                require(stream is not None, "ARCHIVE_STREAM")
                raw = stream.read(member.size + 1)
                require(digest(raw) == expected[relative], "ARCHIVE_MEMBER_IDENTITY")
                destination = Path(tmp) / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(raw)
                observed[relative] = digest(read(destination))
        require(observed == expected and files(Path(tmp)) == expected, "ARCHIVE_EXTRACTED_IDENTITY")
    return observed


def verify_hud_current_rollback(root, lock, current):
    """Independently verify the one-source inverse against the frozen current RC."""
    repair = lock["followup_repair"]
    require(repair["source_path"] == compose.HUD_SOURCE
            and repair["changed_sources_from_current_rc"] == 1
            and repair["unchanged_sources_from_current_rc"] == 68,
            "HUD_ROLLBACK_SCOPE")
    rollback_lock = dict(lock)
    rollback_lock["sources"] = {p: dict(row) for p, row in lock["sources"].items()}
    rollback_lock["sources"][compose.HUD_SOURCE]["after"] = repair["current_hud"]
    rollback_lock["final_place"] = repair["current_place"]
    restored = independent_scan(root / compose.HUD_OFF, rollback_lock, "after")
    require(restored["non_source"] == current["non_source"]
            and restored["instances"] == current["instances"], "HUD_ROLLBACK_NON_SOURCE_DRIFT")
    changes = []
    for name, row in lock["sources"].items():
        repaired = read(root / "sources" / name)
        off = read(root / compose.HUD_OFF / "sources" / name)
        expected = independent_inverse(repaired, repair["inverse"]) if name == compose.HUD_SOURCE else repaired
        require(off == expected, "HUD_ROLLBACK_INVERSE_NOT_CURRENT")
        if repaired != off:
            changes.append(name)
    require(changes == [compose.HUD_SOURCE], "HUD_ROLLBACK_CHANGE_SET")
    expected = {"sources/" + p: row["after"] for p, row in rollback_lock["sources"].items()}
    expected.update({compose.PROJECT: lock["project"], compose.PLACE: repair["current_place"]})
    require(len(expected) == 71 and files(root / compose.HUD_OFF) == expected, "HUD_ROLLBACK_MEMBER_SET")
    verify_archive(root / compose.HUD_OFF_ARCHIVE, expected, compose.HUD_OFF)
    return expected


def verify_core(root, base, reports, context):
    lock = compose.load_lock()
    root = Path(root).resolve()
    require(not (root / "delivery").exists(), "DELIVERY_MUST_NOT_EXIST_BEFORE_ADMISSION")
    inputs = compose.load_inputs(base, reports, lock)
    compose.validate_context(context, inputs["receipt"])
    prior = independent_scan(inputs["base"], lock, "before")
    current = independent_scan(root, lock, "after")
    off = independent_scan(root / compose.OFF, lock, "before")
    require(current["non_source"] == prior["non_source"] == off["non_source"]
            and current["instances"] == prior["instances"] == off["instances"], "NON_SOURCE_DRIFT")
    changed = [p for p, row in lock["sources"].items() if row["before"] != row["after"]]
    require(len(changed) == 22 and len(lock["sources"]) - len(changed) == 47, "CHANGE_COUNT")
    for name, row in lock["sources"].items():
        require(independent_inverse(read(root / "sources" / name), row["inverse"])
                == read(root / compose.OFF / "sources" / name) == inputs["sources"][name], "INVERSE_NOT_PRIOR_BR")
    expected_off = {"sources/" + p: row["before"] for p, row in lock["sources"].items()}
    expected_off.update({compose.PROJECT: lock["project"], compose.PLACE: lock["prior_place"],
                         compose.RECEIPT: digest(inputs["receipt_raw"])})
    expected_off.update({p: digest(inputs["evidence"][p]) for p in lock["prior_report_names"]})
    require(len(expected_off) == 75 and files(root / compose.OFF) == expected_off, "OFF_RUNTIME_MEMBER_SET")
    archive = verify_archive(root / compose.OFF_ARCHIVE, expected_off)
    expected_hud_off = verify_hud_current_rollback(root, lock, current)
    expected_prior = {p: digest(raw) for p, raw in inputs["evidence"].items()}
    require(files(root / "prior_boundary") == expected_prior, "PRIOR_EVIDENCE_NOT_BYTE_EXACT")
    require(len([p for p in expected_prior if p.startswith("legacy_rollbacks/")]) == 8, "OPAQUE_ROLLBACK_COUNT")
    receipt = data(root / compose.RECEIPT)
    expected = {
        "schema": "GQ470_UNION22_CURRENT_SOURCE_RECEIPT_V1", "feature_id": lock["feature_id"],
        "source_profile": "REAL69", "private_companion_profile": "REAL69_UNION22",
        "official_branch": compose.FORMAL, "build_head": context["build_head"],
        "execution_context": context,
        "canonical_build": context["canonical_build"], "receipt_provenance": context["kind"],
        "official_build_head": context["official_build_head"],
        "formal_rc_adoption_proven": context["kind"] == "OFFICIAL",
        "selected_source_count": 69, "changed_source_count": 22, "unchanged_source_count": 47,
        "source_hashes": {r: v["sha256"] for r, v in current["sources"].items()},
        "source_classes": {r: v["class"] for r, v in current["sources"].items()},
        "private_place_bytes": lock["final_place"]["bytes"], "private_place_sha256": lock["final_place"]["sha256"],
        "prior_place": lock["prior_place"], "prior_receipt": digest(inputs["receipt_raw"]),
        "profile_lock": digest(read(HERE / "profile_lock.json")), "prior_evidence": expected_prior,
        "runtime_rollback_archive": digest(read(root / compose.OFF_ARCHIVE)),
        "followup_repair": lock["followup_repair"],
        "hud_only_current_rc_rollback_archive": digest(read(root / compose.HUD_OFF_ARCHIVE)),
        "legacy_48_all_ported": False, "owner_accepted": False, "art_gate": "ART_NO_GO",
        "product_gate": "PRODUCT_NO_GO", "studio_solo": "NOT_TESTED", "studio_two_client": "NOT_TESTED",
        "android_15min": "NOT_TESTED", "fun": "NOT_TESTED", "roblox_publish": False, "paid_trade": False,
        "identity_receipt_is_not_final_delivery_admission": True, **lock["runtime_labels"],
    }
    require(receipt == expected, "FINAL_RECEIPT_FIELD_SET_OR_FACTS")
    core = data(root / "CORE_BUILD_REPORT.json")
    require(core.get("status") == "PASS_SOURCE_BUILD_ONLY" and core.get("final_delivery_created") is False
            and core.get("context") == context and core.get("source_count") == 69
            and core.get("changed_sources") == 22 and core.get("unchanged_sources") == 47
            and core.get("compile_count") == 139 and core.get("rojo_build_count") == 3
            and core.get("historical_on_br_compile_count") == 138 and core.get("historical_on_br_rojo_build_count") == 2
            and core.get("hud_only_compile_count") == 1 and core.get("hud_only_rojo_build_count") == 1
            and core.get("hud_only_off_place") == lock["followup_repair"]["current_place"]
            and core.get("changed_sources_from_current_rc") == 1 and core.get("unchanged_sources_from_current_rc") == 68
            and core.get("instances") == 75 and core.get("prior_snapshot") == inputs["snapshot"]
            and core.get("final_place") == lock["final_place"] and core.get("off_place") == lock["prior_place"]
            and core.get("non_source_property_identity") == digest(current["non_source"])
            and core.get("profile_lock") == digest(read(HERE / "profile_lock.json"))
            and core.get("composer") == digest(read(HERE / "compose_union22.py")), "CORE_REPORT_FACTS")
    expected_stage = {"sources/" + name: row["after"] for name, row in lock["sources"].items()}
    expected_stage.update({compose.OFF + "/" + name: pin for name, pin in expected_off.items()})
    expected_stage.update({"prior_boundary/" + name: pin for name, pin in expected_prior.items()})
    expected_stage.update({compose.HUD_OFF + "/" + name: pin for name, pin in expected_hud_off.items()})
    expected_stage[compose.HUD_OFF_ARCHIVE] = digest(read(root / compose.HUD_OFF_ARCHIVE))
    expected_stage.update({compose.PROJECT: lock["project"], compose.PLACE: lock["final_place"],
                           compose.OFF_ARCHIVE: digest(read(root / compose.OFF_ARCHIVE))})
    require(core.get("staged_payload_verified_after_all_commands") is True
            and core.get("staged_payload") == expected_stage, "CORE_FINAL_STAGED_PAYLOAD")
    expected_root = {**expected_stage, compose.RECEIPT: digest(read(root / compose.RECEIPT)),
                     "CORE_BUILD_REPORT.json": digest(read(root / "CORE_BUILD_REPORT.json"))}
    require(files(root) == expected_root, "CURRENT_ROOT_PAYLOAD_SET_OR_IDENTITY")
    commands = core.get("commands", [])
    require(len(commands) == 142 and all(c.get("exit") == 0 for c in commands), "CORE_COMMAND_COMPLETION")
    compile_commands = [c for c in commands if len(c.get("command", [])) == 3 and c["command"][1] == "--text"]
    rojo_commands = [c for c in commands if len(c.get("command", [])) == 5 and c["command"][1] == "build"
                     and c["command"][3] == "-o"]
    require(len(compile_commands) == 139 and len(rojo_commands) == 3, "CORE_COMMAND_TYPES")
    stage = core.get("build_command_namespace", {}).get("executed_stage")
    require(isinstance(stage, str) and Path(stage).is_absolute()
            and core["build_command_namespace"].get("committed_root") == str(root)
            and core["build_command_namespace"].get("commands_are_actual_pre_rename_paths") is True,
            "CORE_COMMAND_NAMESPACE")
    expected_compile = {str(Path(stage) / prefix / "sources" / p)
                        for prefix in ("", compose.OFF) for p in lock["sources"]}
    expected_compile.add(str(Path(stage) / compose.HUD_OFF / "sources" / compose.HUD_SOURCE))
    require({c["command"][2] for c in compile_commands} == expected_compile, "CORE_COMPILED_SOURCE_SET")
    require({(c["command"][2], c["command"][4]) for c in rojo_commands}
            == {(str(Path(stage) / prefix / compose.PROJECT), str(Path(stage) / prefix / compose.PLACE))
                for prefix in ("", compose.OFF, compose.HUD_OFF)}, "CORE_ROJO_PROJECT_SET")
    require(core["rojo"] == {k: lock["rojo"][k] for k in ("bytes", "sha256")}, "CORE_ROJO_IDENTITY")
    return {"lock": lock, "inputs": inputs, "current": current, "receipt": receipt, "core": core,
            "archive_members": archive, "prior_evidence": expected_prior}


def module(relative, name):
    require(digest(read(REPO / relative))["sha256"] == HELPERS[relative], "HISTORICAL_HELPER_CHANGED")
    spec = importlib.util.spec_from_file_location(name, REPO / relative)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def retention_reports(root, verified, context):
    for name, sha in HELPERS.items():
        require(digest(read(REPO / name))["sha256"] == sha, "HISTORICAL_GATE_OR_MANIFEST_CHANGED")
    gate17 = module("quality_gameplay/gq8_rc85_rc86_real69_nonloss_20261120/verify_real69.py", "union22_old17")
    family = gate17.marker_check(verified["current"]["sources"])
    require(len(family) == 17, "FINAL_MARKER_COUNT")
    gate48 = module("quality_gameplay/gq8_rc85_rc86_real69_feature_truth_20261120/audit_legacy48.py", "union22_old48")
    manifest48 = gate48.load_manifest(REPO / "quality_gameplay/gq8_rc85_rc86_real69_feature_truth_20261120/legacy48.json")
    truth = gate48.inspect(root, manifest48)
    require(truth.get("summary") == {"MARKER_SOURCE_PRESENT": 15, "SOURCE_ANALOGUE_ONLY": 27,
                                    "EVIDENCE_GAP": 4, "NON_RUNTIME_LEGACY_FLAG": 2}
            and truth.get("source_count") == 69 and len(truth.get("flags", [])) == 48
            and truth.get("official_head") == context["build_head"]
            and truth.get("all_48_semantic_parity") == "NOT_PROVEN", "FINAL_ALL48_RETENTION")
    art = module("art_quality/gq470_real69_source_gate.py", "union22_old_art")
    visual = {}
    for name, (_, route, _, marker, historical_sha, guards) in art.FEATURES.items():
        row = verified["current"]["sources"][route]
        text = row["source"].decode("utf-8")
        require(row["class"] == "Script" and marker in text and all(g in text for g in guards),
                "VISUAL_SOURCE_RETENTION:" + name)
        visual[name] = {"route": route, "current_source_sha256": row["sha256"],
                        "prior_boundary_source_sha256": historical_sha,
                        "marker_and_scope_guards_retained": True, "studio_render": "NOT_TESTED"}
    require(len(visual) == 3, "VISUAL_FEATURE_COUNT")
    common = {"candidate_build_head": context["build_head"], "official_build_head": context["official_build_head"],
              "receipt_provenance": context["kind"], "formal_rc_adoption_proven": context["kind"] == "OFFICIAL",
              "private_place": verified["lock"]["final_place"], **verified["lock"]["runtime_labels"]}
    return {
        "UNION22_FINAL_17_MARKER_RETENTION.json": {
            "schema": "UNION22_FINAL_17_MARKER_RETENTION_V1", **common, "source_family_marker_count": 17,
            "historic_source_family_evidence": family,
            "method": "Unchanged marker_check on actual final 69 sources; original full nonloss remains prior-boundary evidence",
            "full_original_nonloss_gate_executed_on_union22": False},
        "UNION22_FINAL_ALL48_RAW.json": truth,
        "UNION22_FINAL_ALL48_ENVELOPE.json": {
            "schema": "UNION22_FINAL_ALL48_PROVENANCE_V1", **common,
            "raw_report_name": "UNION22_FINAL_ALL48_RAW.json", "raw_official_head_field_is_build_head_only": True,
            "unchanged_all48_auditor_executed_on_actual_final_sources": True,
            "summary": truth["summary"], "all_48_semantic_parity": "NOT_PROVEN"},
        "UNION22_FINAL_ART_SOURCE_RETENTION.json": {
            "schema": "UNION22_FINAL_ART_SOURCE_RETENTION_V1", **common, "source_count": 69,
            "exact_locked_source_class_route_place": True, "visual_features": visual,
            "prior_fixed_sha_art_gate_reused_as_final_pass": False,
            "screenshots_required": 32, "screenshots_received": 0,
            "studio_solo": "NOT_TESTED", "studio_two_client": "NOT_TESTED", "android_15min": "NOT_TESTED",
            "fun": "NOT_TESTED", "owner_accepted": False, "art_gate": "ART_NO_GO", "product_gate": "PRODUCT_NO_GO"},
    }


def git_tree_from_manifest(manifest):
    tree = {}
    for path, row in manifest.items():
        parts = PurePosixPath(path).parts
        require(parts and not PurePosixPath(path).is_absolute() and ".." not in parts and "\\" not in path,
                "NATIVE_TOOLCHAIN_MANIFEST_PATH")
        node = tree
        for part in parts[:-1]:
            require(not isinstance(node.get(part), tuple), "NATIVE_TOOLCHAIN_TREE_COLLISION")
            node = node.setdefault(part, {})
        require(parts[-1] not in node and row["mode"] in ("100644", "100755"), "NATIVE_TOOLCHAIN_TREE_DUPLICATE")
        node[parts[-1]] = (row["mode"], row["git_blob"])
    def hash_tree(node):
        chunks = []
        for name in sorted(node, key=lambda key: (key + ("/" if isinstance(node[key], dict) else "")).encode()):
            item = node[name]
            mode, oid = ("40000", hash_tree(item)) if isinstance(item, dict) else item
            chunks.append(mode.encode() + b" " + name.encode() + b"\0" + bytes.fromhex(oid))
        raw = b"".join(chunks)
        return hashlib.sha1(b"tree " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    return hash_tree(tree)


def independent_generated(root, pins, suite_name):
    """Rebuild every fixture, wrapper, body and case byte without adapter calls."""
    program = bytearray()
    for name in pins["fixture_order"]:
        raw = read(HERE / "native/fixtures" / name)
        require(digest(raw) == pins["fixtures"][name], "NATIVE_EXECUTED_FIXTURE_IDENTITY")
        program.extend(raw + b"\n")
    byte_ranges, line_ranges = {}, {}
    for name in pins["modules_in_load_order"] + ["LobbyCastleModesPreview.server"]:
        relative = "ServerScriptService/EGGRUMBLE_" + name + ".luau"
        body = read(root / "sources" / relative)
        if name == "LobbyCastleModesPreview.server":
            program.extend(b"\ninstallApiObservers()\nloadingModule='Host'\ndo local _=(function()\n")
            label, first_line = "Host", program.count(b"\n") + 1
            closing = b"\nend)()end\n"
        else:
            program.extend(("\nloadingModule='" + name + "'\n").encode())
            label, first_line = name, program.count(b"\n") + 3
            program.extend((f"fullSourceRanges.{name}={{first={first_line},last={first_line + body.count(bytes([10]))}}}\n"
                            + "dependencies.EGGRUMBLE_" + name + "=(function()\n").encode())
            closing = b"\nend)()\n"
        start = len(program)
        program.extend(body)
        byte_ranges[relative] = {"start": start, "end": len(program), **digest(body)}
        line_ranges[label] = {"first": first_line, "last": first_line + body.count(b"\n")}
        program.extend(closing)
    case_files = {"combined_clear_los": "combined_cases_clear_los.luau",
                  "objective_full_clear_los": "objective_full_cases_clear_los.luau"}
    require(pins["case_files"] == case_files and suite_name in case_files, "NATIVE_CASE_VARIANT")
    case_path = HERE / "native" / case_files[suite_name]
    case = read(case_path)
    require(digest(case) == pins["suites"][suite_name]["case"], "NATIVE_EXECUTED_CASE_IDENTITY")
    program.extend(b"\n" + case)
    return bytes(program), byte_ranges, line_ranges


def independent_build_evidence(native, build, pins, context, root):
    require(build.get("execution_context") == context
            and build.get("source_receipt") == digest(read(root / compose.RECEIPT))
            and build.get("input_lock") == digest(read(HERE / "native/INPUT_LOCK.json"))
            and build.get("runner") == digest(read(HERE / "native/run_profile.py")), "NATIVE_BUILD_CONTEXT")
    recipe = pins["toolchain"]["recipe"]
    source = Path(build["source_path"])
    directory = Path(build["build_directory"])
    binary = Path(build["binary_path"])
    require(source.is_absolute() and directory.is_absolute() and source.is_dir() and directory.is_dir()
            and not source.is_symlink() and not directory.is_symlink()
            and not directory.is_relative_to(source) and not source.is_relative_to(directory)
            and binary == directory / "luau", "NATIVE_BUILD_PATHS")
    binary_raw = read(binary)
    require(os.access(binary, os.X_OK) and digest(binary_raw) == build["binary_before_suites"]
            and binary.stat().st_mtime_ns == build["binary_mtime_ns"] >= build["target_build_started_ns"],
            "NATIVE_ACTUAL_BINARY_AFTER_EXECUTION")
    tools = build["tools"]
    require(set(tools) == {"cmake", "ninja", "git", "cc", "cxx"}, "NATIVE_BUILD_TOOL_SET")
    for row in tools.values():
        require(Path(row["path"]).is_absolute() and os.access(row["path"], os.X_OK)
                and digest(read(row["path"])) == {k: row[k] for k in ("bytes", "sha256")}, "NATIVE_ACTUAL_BUILD_TOOL")
    paths = {key: row["path"] for key, row in tools.items()}
    raw_cache = read(native / "CMakeCache.txt")
    require(raw_cache == read(directory / "CMakeCache.txt")
            and read(native / "build.ninja") == read(directory / "build.ninja"), "NATIVE_ACTUAL_CACHE_RECIPE")
    cache = {}
    for line in raw_cache.decode().splitlines():
        if line and not line.startswith(("#", "//")):
            key_type, value = line.split("=", 1)
            key = key_type.rsplit(":", 1)[0]
            require(key not in cache, "NATIVE_CACHE_DUPLICATE")
            cache[key] = value
    expected_cache = {"CMAKE_HOME_DIRECTORY": str(source), "CMAKE_CACHEFILE_DIR": str(directory),
                      "CMAKE_GENERATOR": "Ninja", "CMAKE_BUILD_TYPE": "Release",
                      "LUAU_BUILD_TESTS": "OFF", "LUAU_BUILD_CLI": "ON", "CMAKE_PROJECT_NAME": "Luau",
                      "CMAKE_MAKE_PROGRAM": paths["ninja"], "CMAKE_C_COMPILER": paths["cc"],
                      "CMAKE_CXX_COMPILER": paths["cxx"], "CMAKE_COMMAND": paths["cmake"]}
    require(all(cache.get(k) == value for k, value in expected_cache.items())
            and build["cache_contract"] == expected_cache, "NATIVE_CACHE_SOURCE_COMMIT_RECIPE")
    for name in ("CMAKE_TOOLCHAIN_FILE", "CMAKE_C_COMPILER_LAUNCHER", "CMAKE_CXX_COMPILER_LAUNCHER",
                 "CMAKE_PROJECT_INCLUDE", "CMAKE_PROJECT_INCLUDE_BEFORE", "CMAKE_PROJECT_TOP_LEVEL_INCLUDES"):
        require(not cache.get(name), "NATIVE_EXTERNAL_BUILD_RECIPE")
    require(cache.get("LUAU_BUILD_SHARED") == cache.get("LUAU_BUILD_WEB") == "OFF"
            and cache.get("CMAKE_C_FLAGS") == cache.get("CMAKE_CXX_FLAGS") == "", "NATIVE_CACHE_OPTIONS")
    commands = build["commands"]
    expected_configure = [paths["cmake"], "-S", str(source), "-B", str(directory), "-G", "Ninja",
        "-DCMAKE_BUILD_TYPE=Release", "-DLUAU_BUILD_TESTS=OFF", "-DLUAU_BUILD_CLI=ON",
        "-DCMAKE_MAKE_PROGRAM=" + paths["ninja"], "-DCMAKE_C_COMPILER=" + paths["cc"],
        "-DCMAKE_CXX_COMPILER=" + paths["cxx"]]
    expected_build = [paths["cmake"], "--build", str(directory), "--target", "Luau.Repl.CLI", "--parallel", "2"]
    require(set(commands) == {"configure", "build"} and commands["configure"]["argv"] == expected_configure
            and commands["build"]["argv"] == expected_build, "NATIVE_ACTUAL_BUILD_ARGUMENTS")
    for name in commands:
        require(commands[name]["exit_code"] == 0
                and commands[name]["stdout"] == digest(read(native / (name + ".stdout.log")))
                and commands[name]["stderr"] == digest(read(native / (name + ".stderr.log"))), "NATIVE_COMMAND_LOG_BINDING")
    require(b"Linking CXX executable luau" in read(native / "build.stdout.log")
            and b"Luau.Repl.CLI" in read(native / "build.ninja"), "NATIVE_REPL_TARGET_NOT_LINKED")
    manifest = data(native / "source_tree_manifest.json")
    require(manifest.get("source_commit") == pins["toolchain"]["source_commit"]
            and manifest.get("source_tree") == pins["toolchain"]["source_tree"]
            and len(manifest.get("files", {})) == 2336
            and git_tree_from_manifest(manifest["files"]) == pins["toolchain"]["source_tree"], "NATIVE_SOURCE_TREE_MERKLE")
    for name, row in manifest["files"].items():
        raw = read(source / name)
        git_blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        mode = "100755" if (source / name).stat().st_mode & 0o111 else "100644"
        require(git_blob == row["git_blob"] and mode == row["mode"]
                and digest(raw) == {k: row[k] for k in ("bytes", "sha256")}, "NATIVE_PHYSICAL_SOURCE_TREE")
    git_env = {"PATH": os.environ.get("PATH", ""), "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_REPLACE_OBJECTS": "1"}
    def git(*args):
        result = subprocess.run([paths["git"], "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null",
                                 "-C", str(source), *args], env=git_env, capture_output=True, timeout=30)
        require(result.returncode == 0, "NATIVE_SOURCE_GIT_CHECK")
        return result.stdout.decode().strip()
    require(git("rev-parse", "HEAD") == pins["toolchain"]["source_commit"]
            and git("rev-parse", "HEAD^{tree}") == pins["toolchain"]["source_tree"]
            and not git("status", "--porcelain=v1", "--untracked-files=all", "--ignored"), "NATIVE_ACTUAL_CLEAN_SOURCE")


def verify_selected_hud_layout(native, root, pins, build, aggregate, context):
    """Independently bind original main, selected final bodies, generated code and execution."""
    folder = native / "selected_hud_layout"
    result = data(folder / "receipt.json")
    contract = pins["selected_hud_layout"]
    relative = "quality_gameplay/gq8_real63_ui_occlusion_20261119/native_layout.py"
    expected_generator = {"bytes": 3097, "sha256": "1323e10a2d66ca5c986f9a75049df5b4e7fbd016c22583f9d9790d7d1d3e164d"}
    flat = {
        "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_HudIntelRuntime.client.luau":
            "EGGRUMBLE_HudIntelRuntime.client.luau",
        "ReplicatedStorage/EGGRUMBLE_HudPresentationPolicy.luau":
            "EGGRUMBLE_HudPresentationPolicy.luau",
    }
    require(contract["schema"] == "GQ828_SELECTED_HUD_LAYOUT_GATE_V1"
            and contract["generator"] == {"path": relative, **expected_generator}
            and contract["flat_sources"] == flat and contract["condition_count"] == 14
            and contract["viewport_shapes"] == [[320, 260], [393, 851], [375, 667],
                                               [600, 300], [851, 393], [1280, 720], [1024, 768]]
            and contract["hands"] == ["RIGHT", "LEFT"]
            and contract["generator_python_optimization"] == 0
            and contract["hud_runtime_executed"] is False
            and contract["policy_full_body_executed"] is True, "NATIVE_SELECTED_LAYOUT_CONTRACT")
    generator = read(folder / "native_layout.py")
    require(digest(generator) == expected_generator and generator == read(REPO / relative),
            "NATIVE_SELECTED_LAYOUT_GENERATOR_IDENTITY")
    selected = {}
    for path, name in flat.items():
        raw = read(root / "sources" / path)
        require(raw == read(folder / "sources" / name) and digest(raw) == pins["sources"][path],
                "NATIVE_SELECTED_LAYOUT_FINAL_SOURCE")
        selected[path] = digest(raw)
    tree = ast.parse(generator.decode("utf-8"))
    values = [ast.literal_eval(node.value) for node in tree.body
              if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "TEST"
                                                     for t in node.targets)]
    require(len(values) == 1 and isinstance(values[0], str) and values[0].count("__SOURCE__") == 1,
            "NATIVE_SELECTED_LAYOUT_TEST_TEMPLATE")
    policy = read(root / "sources/ReplicatedStorage/EGGRUMBLE_HudPresentationPolicy.luau")
    expected_program = values[0].replace("__SOURCE__", policy.decode("utf-8")).encode("utf-8")
    generated = read(folder / "generated.luau")
    require(generated == expected_program and generated.count(policy) == 1,
            "NATIVE_SELECTED_LAYOUT_GENERATED_PROGRAM")
    execution = Path(result["execution_directory"])
    require(execution.is_absolute() and execution.name == "selected_hud_layout"
            and ".." not in execution.parts, "NATIVE_SELECTED_LAYOUT_EXECUTION_PATH")
    python = result["python"]
    require(Path(python["path"]).is_absolute()
            and digest(read(python["path"])) == {k: python[k] for k in ("bytes", "sha256")},
            "NATIVE_SELECTED_LAYOUT_PYTHON_IDENTITY")
    expected_argv = {
        "generator": [python["path"], "-B", str(execution / "native_layout.py"), "--sources",
                      str(execution / "sources"), "--out", str(execution / "generated.luau")],
        "native": [build["binary_path"], str(execution / "generated.luau")],
    }
    require(set(result.get("commands", {})) == set(expected_argv), "NATIVE_SELECTED_LAYOUT_COMMAND_SET")
    expected_stdout = {
        "generator": b"GQ8_REAL63_SELECTED_SOURCE_MODAL_LAYOUT_PROOFS_PASS\n",
        "native": b"GQ8_REAL63_UI_SQUARE_COLLISIONS_14_CASES_PASS\n",
    }
    for name, argv in expected_argv.items():
        command = result["commands"][name]
        stdout, stderr = read(folder / (name + ".stdout.log")), read(folder / (name + ".stderr.log"))
        require(command["argv"] == argv and command["exit_code"] == 0
                and command["stdout"] == digest(stdout) and command["stderr"] == digest(stderr)
                and stdout == expected_stdout[name] and stderr == b"",
                "NATIVE_SELECTED_LAYOUT_EXECUTED_COMMAND:" + name)
    require(contract["expected_generator_stdout"].encode() == expected_stdout["generator"]
            and contract["expected_native_stdout"].encode() == expected_stdout["native"],
            "NATIVE_SELECTED_LAYOUT_LOCK_MARKERS")
    require(result.get("schema") == "UNION22_SELECTED_HUD_LAYOUT_EXECUTION_V1"
            and result.get("status") == "PASS_SOURCE_LAYOUT_ONLY"
            and result.get("execution_context") == context
            and result.get("source_receipt") == digest(read(root / compose.RECEIPT))
            and result.get("input_lock") == digest(read(HERE / "native/INPUT_LOCK.json"))
            and result.get("runner") == digest(read(HERE / "native/run_profile.py"))
            and result.get("contract") == contract and result.get("selected_sources") == selected
            and result.get("generator") == expected_generator and result.get("generated") == digest(generated)
            and result.get("native") == build["binary_before_suites"]
            and result.get("condition_count") == 14 and result.get("completion_marker_count") == 1
            and result.get("hud_runtime_executed") is False and result.get("policy_full_body_executed") is True
            and result.get("separate_from_server28_suites") is True
            and result.get("source_inputs_unchanged") is True, "NATIVE_SELECTED_LAYOUT_RECEIPT_FACTS")
    require(aggregate.get("selected_hud_layout") == digest(read(folder / "receipt.json")),
            "NATIVE_SELECTED_LAYOUT_AGGREGATE_BINDING")
    expected_files = {"native_layout.py", "generated.luau", "receipt.json",
                      "generator.stdout.log", "generator.stderr.log", "native.stdout.log", "native.stderr.log"}
    expected_files |= {"sources/" + name for name in flat.values()}
    require(set(files(folder)) == expected_files, "NATIVE_SELECTED_LAYOUT_FILE_SET")
    return {"condition_count": 14, "completion_marker_count": 1,
            "receipt": digest(read(folder / "receipt.json")), "selected_sources": selected,
            "hud_runtime_executed": False, "policy_full_body_executed": True,
            "files": expected_files}


def verify_native(native, root, lock, context):
    """Verify concrete body ranges, case logs and new-build receipt, not PASS alone."""
    native = Path(native).resolve()
    input_lock_path = HERE / "native/INPUT_LOCK.json"
    # The adapter exposes its literal lock digest; source bytes are part of this candidate.
    spec = importlib.util.spec_from_file_location("union22_native_contract", HERE / "native/run_profile.py")
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    require(digest(read(input_lock_path))["sha256"] == adapter.INPUT_LOCK_SHA256, "NATIVE_LOCK_IDENTITY")
    pins = data(input_lock_path)
    require(pins.get("schema") == "UNION22_NATIVE_DUAL_CLEAR_LOS_SOURCE_BUILD_INPUTS_V3"
            and pins.get("sources") == {p: row["after"] for p, row in lock["sources"].items()}, "NATIVE_SOURCE_LOCK")
    variants = {"combined_clear_los": "BOUNDED_CLEAR_LOS_APPROACH_INPUT",
                "objective_full_clear_los": "BOUNDED_CLEAR_LOS_MELEE_APPROACH_INPUT"}
    require(set(pins["suites"]) == set(variants)
            and {name: row["input_variant"] for name, row in pins["suites"].items()} == variants,
            "NATIVE_SUITE_VARIANT_CLASSIFICATION")
    original_objective = pins["objective_case_amendment"]["original_case"]
    require(original_objective == {"path": "objective_full_cases.luau", "bytes": 7882,
                                  "sha256": "27d69b1cdf78c0936ab821d2ed0b945364839e62470a19d16fa6be084f8f9b1a"}
            and digest(read(HERE / "native/objective_full_cases.luau"))
            == {k: original_objective[k] for k in ("bytes", "sha256")},
            "NATIVE_ORIGINAL_OBJECTIVE_NOT_PRESERVED")
    build = data(native / "build_receipt.json")
    require(build.get("schema") == "UNION22_F46_REPL_BUILD_V1" and build.get("status") == "PASS_NEW_BUILD"
            and build.get("execution_context") == context
            and build.get("source_commit") == pins["toolchain"]["source_commit"]
            and build.get("source_tree") == pins["toolchain"]["source_tree"]
            and build.get("tracked_file_count") == 2336 and build.get("source_tree_clean_before_after") is True
            and build.get("build_directory_absent_initially") is True and build.get("binary_absent_before_build") is True
            and build.get("recipe") == pins["toolchain"]["recipe"]
            and build.get("binary_before_suites") == build.get("binary_after_suites")
            and build.get("configure_exit") == 0 and build.get("build_exit") == 0,
            "NATIVE_FRESH_BUILD_CONTRACT")
    for name, pin in build.get("evidence_files", {}).items():
        require(digest(read(native / name)) == pin, "NATIVE_BUILD_EVIDENCE_DRIFT")
    require(set(build.get("evidence_files", {})) == {"configure.stdout.log", "configure.stderr.log", "build.stdout.log",
            "build.stderr.log", "CMakeCache.txt", "build.ninja", "source_tree_manifest.json"}, "NATIVE_BUILD_EVIDENCE_SET")
    independent_build_evidence(native, build, pins, context, root)
    aggregate = data(native / "receipt.json")
    require(type(aggregate.get("suites")) is dict and set(aggregate["suites"]) == set(variants),
            "NATIVE_AGGREGATE_SUITE_SET")
    require(aggregate.get("schema") == "UNION22_NATIVE_BOTH_SUITES_V3" and aggregate.get("status") == "PASS"
            and aggregate.get("suite_input_variants") == variants
            and aggregate.get("original_combined_case_preserved_not_claimed_as_unchanged_pass") is True
             and aggregate.get("original_objective_case_preserved_not_claimed_as_unchanged_pass") is True
            and aggregate.get("execution_context") == context
            and aggregate.get("source_receipt") == digest(read(root / compose.RECEIPT))
            and aggregate.get("build_receipt") == digest(read(native / "build_receipt.json"))
            and aggregate.get("input_lock") == digest(read(input_lock_path))
            and aggregate.get("runner") == digest(read(HERE / "native/run_profile.py"))
            and aggregate.get("source_profile") == pins["sources"]
            and aggregate.get("source_count_pinned") == 69 and aggregate.get("source_count_executed_full_body") == 28
            and aggregate.get("source_only") is True and aggregate.get("formal_rc_adoption_proven") is False
            and aggregate.get("source_inputs_unchanged") is True, "NATIVE_AGGREGATE_FACTS")
    for name, pin in pins["fixtures"].items():
        require(digest(read(HERE / "native/fixtures" / name)) == pin, "NATIVE_FIXED_FIXTURE_DRIFT")
    results = {}
    for suite_name, suite in pins["suites"].items():
        folder = native / suite_name
        result = data(folder / "receipt.json")
        generated = read(folder / "generated.luau")
        stdout = read(folder / "stdout.log").decode("utf-8")
        stderr = read(folder / "stderr.log")
        require(stderr == b"", "NATIVE_RUNTIME_STDERR_NOT_EMPTY")
        expected_program, expected_ranges, expected_lines = independent_generated(root, pins, suite_name)
        require(generated == expected_program and result.get("full_body_byte_ranges") == expected_ranges
                and result.get("source_line_ranges") == expected_lines, "NATIVE_EXECUTED_PROGRAM_NOT_EXACT")
        case_lines = [line for line in stdout.splitlines() if line.startswith("CASE\t")]
        parts = [line.split("\t", 3) for line in case_lines]
        require([p[1] for p in parts if len(p) == 4] == suite["expected_case_names"]
                and len(parts) == len(suite["expected_case_names"])
                and all(len(p) == 4 and p[2] == "PASS" for p in parts), "NATIVE_EXACT_CASE_VECTOR:" + suite_name)
        expected_bodies = {"ServerScriptService/EGGRUMBLE_" + p + ".luau"
                           for p in pins["modules_in_load_order"] + ["LobbyCastleModesPreview.server"]}
        ranges = result.get("full_body_byte_ranges", {})
        require(set(ranges) == expected_bodies and len(ranges) == 28, "NATIVE_FULL_BODY_SET")
        previous = -1
        for name in pins["modules_in_load_order"] + ["LobbyCastleModesPreview.server"]:
            rel = "ServerScriptService/EGGRUMBLE_" + name + ".luau"
            row = ranges[rel]
            require(type(row["start"]) is int and type(row["end"]) is int
                    and previous < row["start"] < row["end"] <= len(generated), "NATIVE_BODY_RANGE")
            body = generated[row["start"]:row["end"]]
            require(body == read(root / "sources" / rel) and digest(body) == pins["sources"][rel]
                    and {k: row[k] for k in ("bytes", "sha256")} == pins["sources"][rel], "NATIVE_BODY_CHANGED")
            previous = row["end"]
        require(result.get("schema") == "UNION22_FULL_RUNTIME_SUITE_V2"
                and result.get("status") == "PASS" and result.get("suite") == suite_name
                and result.get("input_variant") == variants[suite_name]
                and result.get("case_path") == pins["case_files"][suite_name]
                and result.get("execution_context") == context
                and result.get("source_receipt") == digest(read(root / compose.RECEIPT))
                and result.get("profile") == "union22" and result.get("source_count_pinned") == 69
                and result.get("source_count_executed_full_body") == 28 and result.get("exit_code") == 0
                and result.get("generated") == digest(generated) and result.get("stdout") == digest(stdout.encode())
                and result.get("stderr") == digest(stderr) and result.get("cases") == case_lines
                and result.get("expected_case_names") == suite["expected_case_names"]
                and result.get("exact_complete_pass_vector") is True
                and result.get("source_inputs_unchanged") is True
                and result.get("native") == build["binary_before_suites"]
                and result.get("input_lock") == digest(read(input_lock_path))
                and result.get("case_file") == suite["case"]
                and result.get("fixture_pins") == pins["fixtures"], "NATIVE_SUITE_RECEIPT_FACTS")
        require(result.get("source_profile") == pins["sources"]
                and result.get("runner") == digest(read(HERE / "native/run_profile.py")), "NATIVE_SUITE_SOURCE_RUNNER_BINDING")
        require(aggregate.get("suites", {}).get(suite_name) == digest(read(folder / "receipt.json")), "NATIVE_SUITE_BINDING")
        results[suite_name] = {"case_count": len(parts), "receipt": digest(read(folder / "receipt.json"))}
    require(set(results) == {"combined_clear_los", "objective_full_clear_los"} and len(results) == 2,
            "NATIVE_BOTH_SUITES")
    layout = verify_selected_hud_layout(native, root, pins, build, aggregate, context)
    expected_files = set(build["evidence_files"]) | {"build_receipt.json", "receipt.json"}
    expected_files |= {suite + "/" + name for suite in pins["suites"]
                       for name in ("generated.luau", "stdout.log", "stderr.log", "receipt.json")}
    expected_files |= {"selected_hud_layout/" + name for name in layout["files"]}
    require(set(files(native)) == expected_files, "NATIVE_RESULT_FILE_SET")
    return {"results": results, "build": build, "payload": files(native), "aggregate": aggregate,
            "selected_hud_layout": {key: value for key, value in layout.items() if key != "files"}}


def admit_delivery(root, base, reports, native, context):
    root = Path(root).resolve()
    native = Path(native).resolve()
    require(not (root / "delivery").exists(), "DELIVERY_ALREADY_EXISTS")
    # The admission boundary starts before the first validation, so a mutation
    # after a checker returns can never become the accepted copy baseline.
    before = files(root)
    native_before = files(native)
    verifier_before = read(Path(__file__))
    profile_before = read(HERE / "profile_lock.json")
    contract_before = files(HERE)
    prior_before = compose.load_inputs(base, reports)["snapshot"]
    def unchanged(phase):
        require(files(root) == before and files(native) == native_before
                and files(HERE) == contract_before
                and compose.load_inputs(base, reports)["snapshot"] == prior_before,
                "PAYLOAD_CHANGED_AFTER_" + phase)
    verified = verify_core(root, base, reports, context)
    unchanged("CORE")
    require(verified["inputs"]["snapshot"] == prior_before, "CORE_PRIOR_SNAPSHOT_CHANGED")
    retained = retention_reports(root, verified, context)
    unchanged("RETENTION")
    runtime = verify_native(native, root, verified["lock"], context)
    unchanged("NATIVE")
    require(runtime["payload"] == native_before, "NATIVE_VALIDATION_SNAPSHOT_CHANGED")
    expected_stage = {name: pin for name, pin in before.items()
                      if name.startswith(("sources/", "prior_boundary/"))
                      or name in (compose.PROJECT, compose.PLACE, compose.RECEIPT, compose.OFF_ARCHIVE, compose.HUD_OFF_ARCHIVE, "CORE_BUILD_REPORT.json")}
    expected_stage.update({"native_evidence/" + name: pin for name, pin in native_before.items()})
    expected_stage["UNION22_PROFILE_LOCK.json"] = digest(profile_before)
    stage = Path(tempfile.mkdtemp(prefix=".union22-delivery-", dir=root.parent))
    try:
        for relative in ("sources", "prior_boundary"):
            shutil.copytree(root / relative, stage / relative)
        for name in (compose.PROJECT, compose.PLACE, compose.RECEIPT, compose.OFF_ARCHIVE, compose.HUD_OFF_ARCHIVE, "CORE_BUILD_REPORT.json"):
            (stage / name).write_bytes(read(root / name))
        shutil.copytree(native, stage / "native_evidence")
        (stage / "UNION22_PROFILE_LOCK.json").write_bytes(read(HERE / "profile_lock.json"))
        for name, report in retained.items():
            compose.write_json(stage / name, report)
            expected_stage[name] = digest((json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode())
        admission = {
            "schema": "UNION22_FINAL_DELIVERY_ADMISSION_V1", "status": "PASS_SOURCE_AND_NATIVE_ONLY",
            "candidate_build_head": context["build_head"], "official_build_head": context["official_build_head"],
            "receipt_provenance": context["kind"], "formal_rc_adoption_proven": context["kind"] == "OFFICIAL",
            "profile_lock": digest(profile_before), "verifier": digest(verifier_before),
            "source_count": 69, "changed_sources": 22, "unchanged_sources": 47, "instances": 75,
            "current_place": verified["lock"]["final_place"], "inverse_place": verified["lock"]["prior_place"],
            "inverse_archive_extracted_members": len(verified["archive_members"]),
            "followup_repair": verified["lock"]["followup_repair"],
            "hud_only_current_rc_inverse_place": verified["lock"]["followup_repair"]["current_place"],
            "hud_only_current_rc_inverse_archive": digest(read(root / compose.HUD_OFF_ARCHIVE)),
            "hud_only_current_rc_inverse_archive_members": 71,
            "changed_sources_from_current_rc": 1, "unchanged_sources_from_current_rc": 68,
            "server_native_suites_are_not_hud_behavior_verification": True,
            "prior_reports_are_prior_boundary_only": True, "prior_opaque_rollback_archives_preserved": 8,
            "fresh_final_marker_retention": 17, "unchanged_all48_auditor_executed_on_final": 48,
            "visual_source_retention": 3, "native_suites": runtime["results"],
            "selected_hud_layout": runtime["selected_hud_layout"],
            "native_suite_input_variants": runtime["aggregate"]["suite_input_variants"],
            "original_combined_case_preserved_not_claimed_as_unchanged_pass": True,
            "original_objective_case_preserved_not_claimed_as_unchanged_pass": True,
            "native_build_receipt": digest(read(Path(native) / "build_receipt.json")),
            "legacy_48_all_ported": False, "owner_accepted": False, "art_gate": "ART_NO_GO",
            "product_gate": "PRODUCT_NO_GO", "studio_solo": "NOT_TESTED", "studio_two_client": "NOT_TESTED",
            "android_15min": "NOT_TESTED", "fun": "NOT_TESTED", **verified["lock"]["runtime_labels"],
        }
        compose.write_json(stage / "UNION22_FINAL_ADMISSION.json", admission)
        expected_stage["UNION22_FINAL_ADMISSION.json"] = digest(
            (json.dumps(admission, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode())
        unchanged("DELIVERY_COPY")
        require(files(stage) == expected_stage, "DELIVERY_COPY_NOT_VALIDATED_STARTING_PAYLOAD")
        require(len(list(stage.glob("*.rbxlx"))) == 1, "DELIVERY_ONE_CURRENT_PLACE")
        manifest = {"schema": "UNION22_DELIVERY_FILES_V1", "files": dict(expected_stage),
                    "manifest_self_excluded": True, "current_place": compose.PLACE}
        compose.write_json(stage / "UNION22_DELIVERY_MANIFEST.json", manifest)
        expected_stage["UNION22_DELIVERY_MANIFEST.json"] = digest(
            (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode())
        require(read(Path(__file__)) == verifier_before and read(HERE / "profile_lock.json") == profile_before,
                "VERIFIER_OR_PROFILE_CHANGED_DURING_ADMISSION")
        unchanged("FINAL_PAYLOAD")
        if context["kind"] != "LOCAL_SOURCE_REVIEW":
            require(compose.live_context(verified["inputs"]["receipt"], context["build_head"]) == context,
                    "LIVE_PROVENANCE_CHANGED_BEFORE_DELIVERY")
        unchanged("FINAL_LIVE_CONTEXT")
        require(files(stage) == expected_stage, "DELIVERY_FINAL_EXPECTED_PAYLOAD_MISMATCH")
        stage.rename(root / "delivery")
        return admission
    except Exception as error:
        # The failed staging directory is outside root and cannot be uploaded by
        # the delivery-only workflow. Preserve it for failure investigation.
        for name in ("UNION22_FINAL_ADMISSION.json", "UNION22_DELIVERY_MANIFEST.json"):
            (stage / name).unlink(missing_ok=True)
        compose.write_json(stage / "FAILED.json", {"status": "FAIL_NO_DELIVERY", "reason": str(error)})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--prior-reports", type=Path, required=True)
    parser.add_argument("--native-results", type=Path, required=True)
    parser.add_argument("--head", required=True)
    args = parser.parse_args()
    inputs = compose.load_inputs(args.base, args.prior_reports)
    context = compose.live_context(inputs["receipt"], args.head)
    admit_delivery(args.root, args.base, args.prior_reports, args.native_results, context)
    print("UNION22_FINAL_SOURCE_NATIVE_DELIVERY_ADMITTED_ART_PRODUCT_NO_GO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
