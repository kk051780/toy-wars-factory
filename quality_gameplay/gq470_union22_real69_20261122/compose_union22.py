#!/usr/bin/env python3
"""Strict existing-hunk union after the unchanged BR-only REAL69 boundary.

The CLI requires the real Actions event/live-RC provenance guard. The separately
named local_source_context is for explicit offline source QA through the Python
API; it never asserts canonical/formal execution. No delivery is admitted here.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tarfile
import tempfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LOCK_SHA256 = "826235327ba98bbde81242661d0929e81e8dda6d69550e1d040586414c7a0b60"
FORMAL = "rc/p0d-s1-kids-rc01"
REPOSITORY = "kk051780/toy-wars-factory"
PROJECT = "EGGRUMBLE_REAL69.project.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
OFF = "off69_union22_prior_br"
OFF_ARCHIVE = "OFF69_UNION22_PRIOR_BR_ROLLBACK.tar.gz"
SHA = re.compile(r"[0-9a-f]{40}\Z")
CLASSES = {"ModuleScript": 47, "Script": 12, "LocalScript": 10}


class GateError(ValueError):
    pass


def need(condition, reason):
    if not condition:
        raise GateError("RED_UNION22_" + reason)


def identity(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def read_file(path):
    path = Path(path)
    need(not path.is_symlink() and path.is_file(), "NOT_REGULAR_FILE:" + str(path))
    need(stat.S_ISREG(path.stat().st_mode), "NOT_REGULAR_FILE:" + str(path))
    need(not path.stat().st_mode & 0o7000, "SPECIAL_FILE_MODE:" + str(path))
    return path.read_bytes()


def strict_json(raw):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            need(key not in value, "DUPLICATE_JSON_KEY")
            value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=unique)


def safe(root, relative):
    need(isinstance(relative, str) and relative and "\\" not in relative,
         "INVALID_RELATIVE_PATH")
    rel = PurePosixPath(relative)
    need(not rel.is_absolute() and ".." not in rel.parts, "ESCAPED_PATH")
    path = Path(root) / relative
    need(path.resolve().is_relative_to(Path(root).resolve()), "ESCAPED_PATH")
    need(not any(p.is_symlink() for p in [path, *path.parents]
                 if p == Path(root) or p.is_relative_to(Path(root))), "SYMLINK_PATH")
    return path


def load_lock():
    raw = read_file(HERE / "profile_lock.json")
    need(identity(raw)["sha256"] == LOCK_SHA256, "PROFILE_LOCK_MISMATCH")
    lock = strict_json(raw)
    need(lock["schema"] == "GQ470_UNION22_PRODUCTION_PROFILE_V1"
         and len(lock["sources"]) == 69, "PROFILE_SCHEMA_OR_COUNT")
    return lock


def source_class(path):
    if path.endswith(".server.luau"):
        return "Script"
    if path.endswith(".client.luau"):
        return "LocalScript"
    need(path.endswith(".luau"), "SOURCE_EXTENSION")
    return "ModuleScript"


def project_inventory(raw):
    tree = strict_json(raw)["tree"]
    need(tree.get("$className") == "DataModel", "PROJECT_ROOT_CLASS")
    result = {}
    def walk(node, route):
        need(isinstance(node, dict), "PROJECT_NODE")
        if "$path" in node:
            name = node["$path"]
            need(isinstance(name, str) and name.startswith("sources/"), "PROJECT_PATH")
            relative = name.removeprefix("sources/")
            need(relative not in result and route, "DUPLICATE_PROJECT_SOURCE")
            result[relative] = {"route": route, "class": source_class(relative)}
        for name, child in node.items():
            if not name.startswith("$"):
                walk(child, route + "/" + name if route else name)
    walk(tree, "")
    need(len(result) == 69 and Counter(x["class"] for x in result.values()) == CLASSES,
         "PROJECT_INVENTORY")
    return result


def place_inventory(raw):
    tree = ET.fromstring(raw)
    sources, routes = {}, set()
    def walk(item, parent=""):
        props = item.find("Properties")
        need(props is not None, "PLACE_PROPERTIES")
        names = props.findall("string[@name='Name']")
        need(len(names) == 1 and names[0].text, "PLACE_NAME")
        route = parent + "/" + names[0].text if parent else names[0].text
        need(route not in routes, "DUPLICATE_INSTANCE_ROUTE")
        routes.add(route)
        nodes = [x for x in props if x.get("name") == "Source"]
        need(len(nodes) <= 1, "DUPLICATE_SOURCE_PROPERTY")
        if nodes:
            node = nodes[0]
            need(node.tag in ("string", "ProtectedString"), "SOURCE_ENCODING")
            sources[route] = {"class": item.get("class"),
                              "raw": (node.text or "").encode()}
            node.text = "__SOURCE_OMITTED_FOR_NON_SOURCE_COMPARISON__"
        for child in item.findall("Item"):
            walk(child, route)
    for item in tree.findall("Item"):
        walk(item)
    need(len(sources) == 69 and Counter(x["class"] for x in sources.values()) == CLASSES,
         "PLACE_SOURCE_INVENTORY")
    need(len(routes) == 75, "PLACE_INSTANCE_COUNT")
    return sources, ET.tostring(tree, encoding="utf-8")


def load_inputs(base, reports, lock=None):
    lock = lock or load_lock()
    for value in (base, reports):
        path = Path(value).absolute()
        need(not any(p.is_symlink() for p in [path, *path.parents]), "INPUT_ROOT_SYMLINK")
    base, reports = Path(base).resolve(), Path(reports).resolve()
    need(reports in (base, base / "delivery"), "PRIOR_REPORT_DIRECTORY")
    project = read_file(base / PROJECT)
    place = read_file(base / PLACE)
    need(identity(project) == lock["project"], "PRIOR_PROJECT_IDENTITY")
    need(identity(place) == lock["prior_place"], "PRIOR_PLACE_IDENTITY")
    inventory = project_inventory(project)
    need(inventory == {p: {"route": row["route"], "class": row["class"]}
                       for p, row in lock["sources"].items()}, "PRIOR_PROJECT_ROUTE_CLASS")
    source_root = safe(base, "sources")
    found = set()
    for path in source_root.rglob("*"):
        need(not path.is_symlink(), "SOURCE_SYMLINK")
        if path.is_file():
            found.add(path.relative_to(source_root).as_posix())
        else:
            need(path.is_dir(), "SOURCE_SPECIAL_FILE")
    need(found == set(lock["sources"]), "PRIOR_SOURCE_INVENTORY")
    sources = {}
    for name, row in lock["sources"].items():
        raw = read_file(safe(source_root, name))
        need(identity(raw) == row["before"], "PRIOR_SOURCE_IDENTITY:" + name)
        sources[name] = raw
    embedded, non_source = place_inventory(place)
    for name, row in lock["sources"].items():
        need(embedded[row["route"]] == {"class": row["class"], "raw": sources[name]},
             "PRIOR_EMBEDDED_SOURCE:" + name)
    receipt_raw = read_file(base / RECEIPT)
    receipt = strict_json(receipt_raw)
    need(receipt.get("official_branch") == FORMAL and receipt.get("source_profile") == "REAL69"
         and receipt.get("selected_source_count") == 69, "PRIOR_RECEIPT_PROFILE")
    need(receipt.get("source_hashes") == {r["route"]: r["before"]["sha256"] for r in lock["sources"].values()}
         and receipt.get("source_classes") == {r["route"]: r["class"] for r in lock["sources"].values()},
         "PRIOR_RECEIPT_SOURCE_IDENTITY")
    need(receipt.get("private_place_bytes") == len(place)
         and receipt.get("private_place_sha256") == identity(place)["sha256"],
         "PRIOR_RECEIPT_PLACE_IDENTITY")
    need(type(receipt.get("canonical_build")) is bool
         and isinstance(receipt.get("build_head"), str) and SHA.fullmatch(receipt["build_head"])
         and receipt.get("legacy_48_all_ported") is False, "PRIOR_RECEIPT_CONTEXT")
    evidence = {name: read_file(reports / name) for name in lock["prior_report_names"]}
    r17, r48, art = [strict_json(evidence[n]) for n in lock["prior_report_names"]]
    need(r17.get("build_head") == receipt["build_head"]
         and r17.get("source_family_marker_count") == 17
         and r17.get("selected_luau_sources") == 69
         and r17.get("source_route_class_hash_receipt") == "PASS_69_OF_69"
         and r17.get("private_place_sha256") == lock["prior_place"]["sha256"]
         and r17.get("private_place_bytes") == lock["prior_place"]["bytes"], "PRIOR_17_REPORT")
    need(r48.get("official_head") == receipt["build_head"] and r48.get("source_count") == 69
         and r48.get("original_legacy_flags") == 48 and len(r48.get("flags", [])) == 48
         and r48.get("all_48_semantic_parity") == "NOT_PROVEN"
         and r48.get("summary") == {"EVIDENCE_GAP": 4, "MARKER_SOURCE_PRESENT": 15,
                                   "NON_RUNTIME_LEGACY_FLAG": 2, "SOURCE_ANALOGUE_ONLY": 27},
         "PRIOR_48_REPORT")
    expected_kind = "OFFICIAL" if receipt["canonical_build"] else "PR_CANDIDATE"
    need(art.get("candidate_build_head") == receipt["build_head"]
         and art.get("receipt_provenance") == expected_kind
         and art.get("formal_rc_adoption_proven") is receipt["canonical_build"]
         and art.get("official_build_head") == (receipt["build_head"] if receipt["canonical_build"] else None)
         and art.get("private_place_sha256") == lock["prior_place"]["sha256"]
         and art.get("private_place_bytes") == lock["prior_place"]["bytes"]
         and art.get("source_gate", {}).get("status") == "PASS_SOURCE_ONLY"
         and art["source_gate"].get("actual_place_scripts") == 69
         and art["source_gate"].get("verified_visual_feature_sources") == 3
         and art.get("art_gate") == "ART_NO_GO" and art.get("product_gate") == "PRODUCT_NO_GO"
         and art.get("owner_accepted") is False, "PRIOR_ART_REPORT")
    archives = {p.name for p in reports.glob("OFF*.tar.gz")}
    need(archives == set(lock["prior_opaque_rollback_names"]), "PRIOR_ROLLBACK_INVENTORY")
    for name in sorted(archives):
        evidence["legacy_rollbacks/" + name] = read_file(reports / name)
    evidence[RECEIPT] = receipt_raw
    snapshot = {"sources/" + name: identity(raw) for name, raw in sources.items()}
    snapshot.update({PROJECT: identity(project), PLACE: identity(place), RECEIPT: identity(receipt_raw)})
    snapshot.update({"reports/" + name: identity(raw) for name, raw in evidence.items()})
    return {"base": base, "reports": reports, "project": project, "place": place,
            "sources": sources, "non_source": non_source, "receipt": receipt,
            "receipt_raw": receipt_raw, "evidence": evidence, "snapshot": snapshot}


def live_context(receipt, head):
    need(os.environ.get("GITHUB_ACTIONS") == "true"
         and os.environ.get("GITHUB_REPOSITORY") == REPOSITORY, "REAL_ACTIONS_CONTEXT_REQUIRED")
    need(head == os.environ.get("GITHUB_SHA") == receipt.get("build_head"), "BUILD_HEAD_MISMATCH")
    checkout = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                                       env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_REPLACE_OBJECTS": "1"},
                                       text=True, timeout=30).strip()
    need(checkout == head, "ACTUAL_CHECKOUT_HEAD_MISMATCH")
    need(all(os.environ.get(key, "").isdigit() and int(os.environ[key]) > 0
             for key in ("GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT")), "ACTUAL_RUN_ID_ATTEMPT_REQUIRED")
    sys.path.insert(0, str(REPO))
    from quality_gameplay.gq470_art_pr_provenance_20261121.guard import verify_receipt
    event = strict_json(read_file(Path(os.environ["GITHUB_EVENT_PATH"])))
    live = subprocess.check_output(
        ["gh", "api", f"repos/{REPOSITORY}/git/ref/heads/{FORMAL}", "--jq", ".object.sha"],
        text=True, timeout=30).strip()
    kind = verify_receipt(receipt, dict(os.environ), event, live)
    need(kind in ("OFFICIAL", "PR_CANDIDATE"), "UNSUPPORTED_PRODUCTION_CONTEXT")
    return {"kind": kind, "build_head": head, "canonical_build": kind == "OFFICIAL",
            "checkout_sha": checkout,
            "official_build_head": head if kind == "OFFICIAL" else None,
            "observed_live_rc": live, "event": os.environ["GITHUB_EVENT_NAME"],
            "run_id": os.environ.get("GITHUB_RUN_ID"), "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT")}


def local_source_context(receipt):
    """Explicit offline Python-API QA. CLI admission cannot select this mode."""
    checkout = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                                       env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_REPLACE_OBJECTS": "1"},
                                       text=True, timeout=30).strip()
    return {"kind": "LOCAL_SOURCE_REVIEW", "build_head": receipt["build_head"],
            "checkout_sha": checkout,
            "canonical_build": False, "official_build_head": None,
            "observed_live_rc": None, "event": None, "run_id": None, "run_attempt": None}


def validate_context(context, receipt):
    need(set(context) == {"kind", "build_head", "checkout_sha", "canonical_build", "official_build_head",
                          "observed_live_rc", "event", "run_id", "run_attempt"}, "CONTEXT_FIELD_SET")
    need(context.get("kind") in ("OFFICIAL", "PR_CANDIDATE", "LOCAL_SOURCE_REVIEW"),
         "CONTEXT_KIND")
    official = context["kind"] == "OFFICIAL"
    need(context.get("build_head") == receipt["build_head"]
         and context.get("canonical_build") is official
         and context.get("official_build_head") == (receipt["build_head"] if official else None),
         "CONTEXT_CLASSIFICATION")
    if context["kind"] != "LOCAL_SOURCE_REVIEW":
        need(receipt["canonical_build"] is official and context["checkout_sha"] == context["build_head"]
             and all(isinstance(context[k], str) and context[k].isdigit() and int(context[k]) > 0
                     for k in ("run_id", "run_attempt")), "PARENT_CONTEXT_CLASSIFICATION")
    else:
        need(isinstance(context["checkout_sha"], str) and SHA.fullmatch(context["checkout_sha"])
             and all(context[k] is None for k in ("observed_live_rc", "event", "run_id", "run_attempt")),
             "LOCAL_CONTEXT_CANNOT_CLAIM_CI")


def apply_hunks(raw, hunks):
    lines = raw.decode().splitlines(keepends=True)
    result, cursor, previous = [], 0, None
    need(hunks == sorted(hunks, key=lambda h: (h["start"], h["stop"])), "HUNK_ORDER")
    for hunk in hunks:
        start, stop = hunk["start"], hunk["stop"]
        need(type(start) is int and type(stop) is int and cursor <= start <= stop <= len(lines),
             "HUNK_RANGE_OR_OVERLAP")
        need(previous != (start, stop), "DUPLICATE_HUNK")
        need(identity(hunk["old"].encode()) == hunk["old_identity"]
             and identity(hunk["new"].encode()) == hunk["new_identity"], "HUNK_PAYLOAD_IDENTITY")
        need("".join(lines[start:stop]) == hunk["old"], "HUNK_REMOVED_TEXT")
        result.extend(lines[cursor:start])
        result.append(hunk["new"])
        cursor, previous = stop, (start, stop)
    result.extend(lines[cursor:])
    return "".join(result).encode()


def transform(inputs, lock):
    on, off = {}, {}
    for name, row in lock["sources"].items():
        on[name] = apply_hunks(inputs["sources"][name], row["forward"])
        need(identity(on[name]) == row["after"], "FINAL_SOURCE_IDENTITY:" + name)
        off[name] = apply_hunks(on[name], row["inverse"])
        need(off[name] == inputs["sources"][name] and identity(off[name]) == row["before"],
             "INVERSE_NOT_EXACT:" + name)
    need(sum(on[p] != inputs["sources"][p] for p in on) == 22, "CHANGED_SOURCE_COUNT")
    return on, off


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def run_checked(command, log, timeout=60, quiet_stdout=False):
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run([str(x) for x in command], stdout=subprocess.DEVNULL if quiet_stdout else subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=timeout)
    row = {"command": [str(x) for x in command], "started_at_utc": started,
           "exit": result.returncode, "stderr": result.stderr.decode(errors="replace"),
           "stdout": None if quiet_stdout else result.stdout.decode(errors="replace")}
    log.append(row)
    need(result.returncode == 0, "COMMAND_FAILED:" + str(command[0]))
    return row


def make_archive(root, destination):
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for file in sorted(p for p in root.rglob("*") if p.is_file()):
            relative = OFF + "/" + file.relative_to(root).as_posix()
            content = read_file(file)
            info = tarfile.TarInfo(relative)
            info.size, info.mode, info.mtime, info.uid, info.gid = len(content), 0o644, 0, 0, 0
            archive.addfile(info, io.BytesIO(content))
    with destination.open("wb") as output:
        with gzip.GzipFile(fileobj=output, filename="", mode="wb", mtime=0) as zipped:
            zipped.write(raw.getvalue())


def staged_payload(stage):
    need(not stage.stat().st_mode & 0o7000, "STAGED_DIRECTORY_SPECIAL_MODE")
    result = {}
    for path in sorted(stage.rglob("*")):
        need(not path.is_symlink(), "STAGED_OUTPUT_SYMLINK")
        if path.is_file():
            result[path.relative_to(stage).as_posix()] = identity(read_file(path))
        else:
            need(path.is_dir(), "STAGED_OUTPUT_SPECIAL_FILE")
            need(not path.stat().st_mode & 0o7000, "STAGED_DIRECTORY_SPECIAL_MODE")
    return result


def build_source_candidate(base, reports, output, compiler, rojo, context):
    """Build exact source identities; final verifier alone may create delivery."""
    lock = load_lock()
    producer_before = read_file(Path(__file__))
    profile_before = read_file(HERE / "profile_lock.json")
    output = Path(output).absolute()
    need(not output.exists() and not output.is_symlink(), "OUTPUT_ALREADY_EXISTS")
    inputs = load_inputs(base, reports, lock)
    base = inputs["base"]
    need(not output.resolve().is_relative_to(base) and not base.is_relative_to(output.resolve()),
         "OUTPUT_OVERLAPS_INPUT")
    validate_context(context, inputs["receipt"])
    on, off = transform(inputs, lock)
    compiler, rojo = Path(compiler).resolve(), Path(rojo).resolve()
    compiler_before, rojo_before = identity(read_file(compiler)), identity(read_file(rojo))
    need(os.access(compiler, os.X_OK) and os.access(rojo, os.X_OK), "TOOL_NOT_EXECUTABLE")
    need(rojo_before == {k: lock["rojo"][k] for k in ("bytes", "sha256")}, "ROJO_IDENTITY")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=output.name + ".building-", dir=output.parent))
    logs = []
    try:
        for folder, sources in ((stage, on), (stage / OFF, off)):
            folder.mkdir(exist_ok=True)
            (folder / PROJECT).write_bytes(inputs["project"])
            for name, raw in sources.items():
                path = folder / "sources" / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
                run_checked([compiler, "--text", path], logs, quiet_stdout=True)
            run_checked([rojo, "build", folder / PROJECT, "-o", folder / PLACE], logs)
            wanted = lock["final_place"] if folder == stage else lock["prior_place"]
            place = read_file(folder / PLACE)
            need(identity(place) == wanted, "BUILT_PLACE_IDENTITY")
            embedded, non_source = place_inventory(place)
            need(non_source == inputs["non_source"], "NON_SOURCE_PROPERTY_DRIFT")
            for name, row in lock["sources"].items():
                need(embedded[row["route"]] == {"class": row["class"], "raw": sources[name]},
                     "BUILT_EMBEDDED_SOURCE:" + name)
        (stage / OFF / RECEIPT).write_bytes(inputs["receipt_raw"])
        for name, raw in inputs["evidence"].items():
            path = stage / "prior_boundary" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            if name in lock["prior_report_names"]:
                (stage / OFF / name).write_bytes(raw)
        make_archive(stage / OFF, stage / OFF_ARCHIVE)
        archive_identity = identity(read_file(stage / OFF_ARCHIVE))
        expected_stage = {"sources/" + name: identity(raw) for name, raw in on.items()}
        expected_stage.update({OFF + "/sources/" + name: identity(raw) for name, raw in off.items()})
        expected_stage.update({PROJECT: lock["project"], PLACE: lock["final_place"],
                               OFF + "/" + PROJECT: lock["project"], OFF + "/" + PLACE: lock["prior_place"],
                               OFF + "/" + RECEIPT: identity(inputs["receipt_raw"]), OFF_ARCHIVE: archive_identity})
        expected_stage.update({"prior_boundary/" + name: identity(raw) for name, raw in inputs["evidence"].items()})
        expected_stage.update({OFF + "/" + name: identity(inputs["evidence"][name]) for name in lock["prior_report_names"]})
        final_receipt = {
            "schema": "GQ470_UNION22_CURRENT_SOURCE_RECEIPT_V1",
            "feature_id": lock["feature_id"], "source_profile": "REAL69",
            "private_companion_profile": "REAL69_UNION22", "official_branch": FORMAL,
            "build_head": context["build_head"], "canonical_build": context["canonical_build"],
            "execution_context": context,
            "receipt_provenance": context["kind"], "official_build_head": context["official_build_head"],
            "formal_rc_adoption_proven": context["kind"] == "OFFICIAL",
            "selected_source_count": 69, "changed_source_count": 22, "unchanged_source_count": 47,
            "source_hashes": {row["route"]: row["after"]["sha256"] for row in lock["sources"].values()},
            "source_classes": {row["route"]: row["class"] for row in lock["sources"].values()},
            "private_place_bytes": lock["final_place"]["bytes"],
            "private_place_sha256": lock["final_place"]["sha256"],
            "prior_place": lock["prior_place"], "prior_receipt": identity(inputs["receipt_raw"]),
            "profile_lock": identity(read_file(HERE / "profile_lock.json")),
            "prior_evidence": {name: identity(raw) for name, raw in inputs["evidence"].items()},
            "runtime_rollback_archive": archive_identity,
            "legacy_48_all_ported": False, "owner_accepted": False,
            "art_gate": "ART_NO_GO", "product_gate": "PRODUCT_NO_GO",
            "studio_solo": "NOT_TESTED", "studio_two_client": "NOT_TESTED",
            "android_15min": "NOT_TESTED", "fun": "NOT_TESTED",
            "roblox_publish": False, "paid_trade": False,
            "identity_receipt_is_not_final_delivery_admission": True,
            **lock["runtime_labels"],
        }
        core_report = {
            "schema": "GQ470_UNION22_CORE_BUILD_V1", "status": "PASS_SOURCE_BUILD_ONLY",
            "final_delivery_created": False, "context": context,
            "source_count": 69, "changed_sources": 22, "unchanged_sources": 47,
            "compile_count": 138, "rojo_build_count": 2, "instances": 75,
            "prior_snapshot": inputs["snapshot"], "final_place": lock["final_place"],
            "off_place": lock["prior_place"], "actual_inverse_source_and_place_exact": True,
            "non_source_property_identity": identity(inputs["non_source"]),
            "compiler": compiler_before, "rojo": rojo_before,
            "build_command_namespace": {"executed_stage": str(stage), "committed_root": str(output),
                                        "commands_are_actual_pre_rename_paths": True},
            "profile_lock": identity(read_file(HERE / "profile_lock.json")),
            "composer": identity(producer_before),
            "commands": logs, "original_receipt_preserved_byte_exact": True}
        need(load_inputs(base, reports, lock)["snapshot"] == inputs["snapshot"], "INPUT_CHANGED_DURING_BUILD")
        need(identity(read_file(compiler)) == compiler_before and identity(read_file(rojo)) == rojo_before,
             "TOOL_CHANGED_DURING_BUILD")
        need(read_file(Path(__file__)) == producer_before
             and read_file(HERE / "profile_lock.json") == profile_before, "PRODUCER_OR_PROFILE_CHANGED_DURING_BUILD")
        need(staged_payload(stage) == expected_stage, "STAGED_OUTPUT_CHANGED_AFTER_BUILD")
        core_report["staged_payload_verified_after_all_commands"] = True
        core_report["staged_payload"] = expected_stage
        need(not (stage / "delivery").exists(), "PREMATURE_DELIVERY")
        write_json(stage / RECEIPT, final_receipt)
        write_json(stage / "CORE_BUILD_REPORT.json", core_report)
        stage.rename(output)
        return output
    except Exception as error:
        # A failed private stage cannot retain an apparently successful report.
        for name in (RECEIPT, "CORE_BUILD_REPORT.json"):
            (stage / name).unlink(missing_ok=True)
        write_json(stage / "FAILED.json", {"status": "FAIL_NO_DELIVERY", "reason": str(error), "commands": logs})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--prior-reports", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--luau-compile", type=Path, required=True)
    parser.add_argument("--rojo", type=Path, required=True)
    args = parser.parse_args()
    inputs = load_inputs(args.base, args.prior_reports)
    context = live_context(inputs["receipt"], args.head)
    result = build_source_candidate(args.base, args.prior_reports, args.out,
                                    args.luau_compile, args.rojo, context)
    print("UNION22_EXACT_SOURCE_BUILD_ONLY_NO_DELIVERY", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
