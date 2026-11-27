#!/usr/bin/env python3
"""Offline, exact-input current69 source/Native/Rojo packet verification.

Only fresh derived ON/OFF directories are written. Historical receipts are
validated as immutable delivery files, never copied into a new build as results.
Supplying a source head labels the caller's input; this tool does not authenticate
GitHub, grant ownership, observe hosted CI, or establish Studio/RC acceptance.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode = True
from apply_lifecycle import (AURA, BASE_HEAD, CONTROLLER, apply_root, check_identity,
                             identity, load_lock, relative_path, rooted)

MANIFEST_NAME = "UNION22_DELIVERY_MANIFEST.json"
PROFILE_NAME = "UNION22_PROFILE_LOCK.json"
MANIFEST_ID = {"bytes": 21272, "sha256": "a9ec16c632873234ff3d33007529697b692a445652e8dfb2bf4d2f959b4e4ba8"}
PROJECT_ID = {"bytes": 9564, "sha256": "90cf3f9fd181002b1b5521a30f17b15b5a14d73bd00f0755d77aaeb68f7885e7"}
PLACE_ID = {"bytes": 828658, "sha256": "9cc9068b85893605c5090964fdc27175d9c48372803d65fe52914591fa7e5899"}
ARCHIVE_ID = {"bytes": 5840240, "sha256": "1187e0f2ff176a286855e911495da84006d5c99841f68891aeca9630915f275d"}
RUNTIME_LABELS = {"ACTIVE_RUNTIME": "rich51", "PRIVATE_COMPANION": "REAL69_UNION22", "RUNTIME_UNIFIED": "NO"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def file_id(path: Path) -> dict:
    return {"path": str(path.resolve()), **identity(path.read_bytes())}


def write_json(path: Path, value: object) -> dict:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return file_id(path)


def inventory(root: Path) -> dict:
    result = {}
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), f"Symlink in exact input tree: {path}")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = identity(path.read_bytes())
    return result


def verify_delivery(base: Path, lock: dict) -> tuple[dict, dict, dict]:
    official = lock["official_input"]
    require(official["manifest"]["path"] == MANIFEST_NAME, "Unexpected delivery manifest path")
    manifest_bytes = rooted(base, MANIFEST_NAME).read_bytes()
    check_identity(manifest_bytes, official["manifest"], "locked delivery manifest")
    check_identity(manifest_bytes, MANIFEST_ID, "immutable H93 delivery manifest")
    manifest = json.loads(manifest_bytes)
    require(manifest.get("schema") == "UNION22_DELIVERY_FILES_V1", "Unexpected delivery manifest schema")
    require(manifest.get("manifest_self_excluded") is True, "Manifest self exclusion changed")
    files = manifest["files"]
    require(len(files) == 119, "Expected exactly 119 manifest entries")
    for name, descriptor in files.items():
        check_identity(rooted(base, name).read_bytes(), descriptor, "manifest entry " + name)
    actual = inventory(base)
    expected = {**files, MANIFEST_NAME: MANIFEST_ID}
    require(actual == expected, "Extracted artifact has missing, extra, or changed files")
    require(official["project"]["path"] == "EGGRUMBLE_REAL69.project.json", "Unexpected project name")
    require(official["place"]["path"] == "EGGRUMBLE_REAL69_PRIVATE.rbxlx", "Unexpected Place name")
    require(manifest["current_place"] == official["place"]["path"], "Manifest Place selection differs")
    for name, fixed in (("project", PROJECT_ID), ("place", PLACE_ID)):
        data = rooted(base, official[name]["path"]).read_bytes()
        check_identity(data, official[name], "locked " + name)
        check_identity(data, fixed, "immutable H93 " + name)
    require({key: official["archive"].get(key) for key in ARCHIVE_ID} == ARCHIVE_ID,
            "Official archive pin differs from H93")
    profile = json.loads(rooted(base, PROFILE_NAME).read_bytes())
    return actual, manifest, profile


def verify_archive(path: Path | None, expected_files: dict) -> dict:
    if path is None:
        return {"provided": False, "verified": False, "status": "NOT_SUPPLIED_MANIFEST_TREE_STILL_VERIFIED"}
    data = path.read_bytes()
    check_identity(data, ARCHIVE_ID, "official ZIP")
    members = {}
    with zipfile.ZipFile(path) as archive:
        for entry in archive.infolist():
            if entry.is_dir():
                continue
            relative_path(entry.filename)
            require(entry.filename not in members, "Duplicate ZIP member")
            members[entry.filename] = identity(archive.read(entry))
    require(members == expected_files, "ZIP contents differ from the verified extracted tree")
    return {"provided": True, "verified": True, **file_id(path), "verified_file_count": len(members)}


def source_contract(base: Path, lock: dict, manifest: dict, profile: dict) -> tuple[dict, dict]:
    require(profile.get("source_count") == lock["selected_sources"] == 69, "Profile source count differs")
    require(profile.get("instance_count") == lock["instance_count"] == 75, "Profile instance count differs")
    require(profile.get("class_counts") == lock["class_counts"], "Profile class counts differ")
    require(profile.get("runtime_labels") == lock["runtime_labels"] == RUNTIME_LABELS,
            "Runtime profile labels differ")
    require(profile.get("project") == PROJECT_ID and profile.get("final_place") == PLACE_ID,
            "Profile project/Place identity differs")
    chain = lock["toolchain"]
    require(profile["luau_source"] == {"commit": chain["luau_commit"], "tree": chain["luau_tree"]},
            "Requested Luau source commit/tree differs from profile")
    require(profile["rojo"]["version"] == chain["rojo_version"]
            and profile["rojo"]["sha256"] == chain["rojo_sha256"], "Requested Rojo differs from profile")
    project = json.loads(rooted(base, lock["official_input"]["project"]["path"]).read_bytes())
    selected, nodes = {}, {}

    def walk(node: dict, route: str) -> None:
        if route:
            require(route not in nodes, "Duplicate project instance path")
            nodes[route] = node.get("$className")
        if "$path" in node:
            name = node["$path"]
            relative_path(name)
            require(name.startswith("sources/") and name.endswith(".luau"), "Non-source project path")
            require(name not in selected, "A source is selected more than once")
            inferred = "LocalScript" if name.endswith(".client.luau") else "Script" if name.endswith(".server.luau") else "ModuleScript"
            selected[name] = {"route": route, "class": node.get("$className", inferred)}
        for key, child in node.items():
            if not key.startswith("$"):
                require(isinstance(child, dict), "Non-object project instance")
                walk(child, route + "/" + key if route else key)

    require(project["tree"].get("$className") == "DataModel", "Project root changed")
    walk(project["tree"], "")
    require(len(selected) == 69 and len(nodes) == 75, "Project source/instance inventory differs")
    actual_source_names = {name for name in manifest["files"] if name.startswith("sources/")}
    require(set(selected) == actual_source_names, "Project-selected sources differ from manifest sources")
    require(set(profile["sources"]) == {name.removeprefix("sources/") for name in selected},
            "Profile source paths differ from selected project paths")
    for name, record in selected.items():
        row = profile["sources"][name.removeprefix("sources/")]
        require(record == {"route": row["route"], "class": row["class"]}, "Source class/route mismatch: " + name)
        check_identity(rooted(base, name).read_bytes(), row["after"], "profile after source " + name)
        record.update(identity(rooted(base, name).read_bytes()))
    require(dict(Counter(row["class"] for row in selected.values())) == lock["class_counts"],
            "Computed selected source class counts differ")
    return selected, nodes


def xml_inventory(place: Path, sources_root: Path, selected: dict, project_nodes: dict) -> dict:
    document = ET.parse(place).getroot()
    require(document.tag == "roblox", "Unexpected Place XML root")
    instances, source_rows = {}, {}

    def walk(item: ET.Element, parent: str) -> None:
        props = item.find("Properties")
        require(props is not None, "XML Item has no Properties")
        names = [prop for prop in props if prop.attrib.get("name") == "Name"]
        require(len(names) == 1 and bool(names[0].text), "XML Item has no unique Name")
        route = parent + "/" + names[0].text if parent else names[0].text
        require(route not in instances, "Duplicate XML instance path")
        instances[route] = item.attrib.get("class")
        sources = [prop for prop in props if prop.attrib.get("name") == "Source"]
        require(len(sources) <= 1, "Duplicate XML Source property")
        if sources:
            data = (sources[0].text or "").encode("utf-8")
            source_rows[route] = {"class": item.attrib.get("class"), **identity(data)}
        for child in item.findall("Item"):
            walk(child, route)

    for child in document.findall("Item"):
        walk(child, "")
    require(len(instances) == 75 and len(source_rows) == 69, "XML actual source/instance count differs")
    require(set(instances) == set(project_nodes), "XML and project instance paths differ")
    for route, declared in project_nodes.items():
        if declared is not None:
            require(instances[route] == declared, "XML explicit instance class differs: " + route)
    expected_sources = {}
    for name, row in selected.items():
        expected_sources[row["route"]] = {"class": row["class"], **identity(rooted(sources_root, name).read_bytes())}
    require(source_rows == expected_sources, "XML source bodies/classes differ from the selected actual files")
    stripped = copy.deepcopy(document)
    for item in stripped.iter("Item"):
        properties = item.find("Properties")
        if properties is not None:
            for prop in properties:
                if prop.attrib.get("name") == "Source":
                    prop.text = None
    return {"place": file_id(place), "instance_count": len(instances), "source_count": len(source_rows),
            "instances": instances, "sources": source_rows,
            "source_class_counts": dict(Counter(row["class"] for row in source_rows.values())),
            "xml_with_only_source_text_removed": identity(ET.tostring(stripped, encoding="utf-8"))}


def execute(argv: list[str], cwd: Path, logs: Path, label: str, commands: list[dict], timeout: int = 120) -> dict:
    started = datetime.now(timezone.utc).isoformat()
    stdout_path, stderr_path = logs / (label + ".stdout.txt"), logs / (label + ".stderr.txt")
    result = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=timeout, check=False)
    stdout_path.write_bytes(result.stdout)
    stderr_path.write_bytes(result.stderr)
    receipt = {"command": argv, "cwd": str(cwd), "started_at_utc": started, "exit_code": result.returncode,
               "stdout": file_id(stdout_path), "stderr": file_id(stderr_path)}
    commands.append(receipt)
    require(result.returncode == 0, f"Command failed: {label}; inspect saved stderr")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--luau", type=Path, required=True)
    parser.add_argument("--luau-compile", type=Path, required=True)
    parser.add_argument("--rojo", type=Path, required=True)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--source-head")
    args = parser.parse_args()
    base, output, packet = args.base_artifact.resolve(), args.output.resolve(), Path(__file__).resolve().parent
    require(not output.exists(), "--output must be a new directory")
    require(not output.is_relative_to(base) and not base.is_relative_to(output), "Output must be disjoint from immutable input")
    require(not output.is_relative_to(packet) and not packet.is_relative_to(output), "Output must be outside the packet")
    if args.source_head:
        require(bool(re.fullmatch(r"[0-9a-f]{40}", args.source_head)), "source-head must be an actual 40-hex commit supplied by the caller")
        require(args.source_head != BASE_HEAD, "Baseline H93 cannot identify the changed unpublished Controller candidate")
    output.mkdir(parents=True)
    logs = output / "logs"; logs.mkdir()
    commands = []
    report = {"schema": "GQ824_AURA_LIFECYCLE_PACKET_REPORT_V1", "status": "RUNNING",
              "started_at_utc": datetime.now(timezone.utc).isoformat(), "source_head": args.source_head,
              "source_head_provenance": "CALLER_SUPPLIED_NOT_AUTHENTICATED_BY_OFFLINE_GATE" if args.source_head else "LOCAL_UNPUBLISHED_CANDIDATE",
              "base_rc_head": BASE_HEAD, "commands": commands,
              "hosted_ci_observed": False, "formal_rc_adopted": False,
              "studio": "NOT_TESTED", "two_client": "NOT_TESTED", "android": "NOT_TESTED", "art": "NOT_TESTED", "fun": "NOT_TESTED",
              "independent_approval": False, "owner_accepted": False}
    success = False
    try:
        lock_path = packet / "source_lock.json"
        lock = load_lock(lock_path)
        packet_paths = [lock_path, packet / "apply_lifecycle.py", packet / "verify_packet.py",
                        packet / "run_native.py", packet / "native_fixture.luau",
                        rooted(packet, lock["controller"]["candidate"]["file"])]
        packet_before = [file_id(path) for path in packet_paths]
        bins = {"luau": args.luau.resolve(), "luau_compile": args.luau_compile.resolve(), "rojo": args.rojo.resolve()}
        bins_before = {name: file_id(path) for name, path in bins.items()}
        require(bins_before["rojo"]["sha256"] == lock["toolchain"]["rojo_sha256"], "Supplied Rojo digest differs from pinned tool")
        report["toolchain"] = {"actual_binaries": bins_before, "declared_source_pins": lock["toolchain"],
                               "luau_binary_source_provenance": "NOT_INFERRED_FROM_BINARY_HASH_CALLER_BUILD_EVIDENCE_REQUIRED"}
        baseline_files, manifest, profile = verify_delivery(base, lock)
        archive_before = file_id(args.archive) if args.archive else None
        report["archive"] = verify_archive(args.archive, baseline_files)
        selected, nodes = source_contract(base, lock, manifest, profile)
        candidate = rooted(packet, lock["controller"]["candidate"]["file"]).read_bytes()
        check_identity(candidate, lock["controller"]["candidate"], "locked packet candidate")
        report["runtime_labels"] = lock["runtime_labels"]
        report["verified_manifest_entries"] = 119
        report["source_inventory"] = write_json(output / "BASE_SOURCE_CLASS_MAP.json", selected)
        report["input_manifest_verification"] = write_json(output / "BASE_DELIVERY_VERIFIED.json", baseline_files)
        baseline_xml = xml_inventory(rooted(base, lock["official_input"]["place"]["path"]), base, selected, nodes)
        on, off = output / "ON", output / "OFF"
        on.mkdir()
        project_name = lock["official_input"]["project"]["path"]
        for relative in [project_name, *sorted(selected)]:
            destination = rooted(on, relative); destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(rooted(base, relative), destination)
        copied = inventory(on)
        wanted = {name: baseline_files[name] for name in [project_name, *sorted(selected)]}
        require(copied == wanted, "ON input copy differs or includes stale receipts")
        forward_receipt = apply_root(on, base, packet, lock)
        on_files = inventory(on)
        require(set(on_files) == set(wanted), "ON file inventory changed")
        changed = sorted(name for name in wanted if on_files[name] != wanted[name])
        require(changed == [CONTROLLER], "ON must change exactly the selected Controller")
        shutil.copytree(on, off)
        inverse_receipt = apply_root(off, base, packet, lock, revert=True)
        require(inventory(off) == wanted, "Actual inverse did not restore exact project plus 69 sources")
        report["transform"] = {"forward": forward_receipt, "inverse": inverse_receipt,
                               "changed_sources": changed, "other_sources_unchanged": 68, "copied_old_receipts": 0}
        version_receipt = execute([str(bins["rojo"]), "--version"], output, logs, "rojo_version", commands)
        version_text = Path(version_receipt["stdout"]["path"]).read_text().strip()
        require(version_text == "Rojo " + lock["toolchain"]["rojo_version"], "Rojo version output differs")
        for index, name in enumerate(sorted(selected), 1):
            execute([str(bins["luau_compile"]), "--null", str(rooted(on, name))], output, logs,
                    f"compile_{index:02d}", commands, timeout=30)
        report["compile"] = {"selected_on_sources": 69, "successful_commands": 69, "mode": "--null bytecode compilation, not --only-parse"}
        native_dir = output / "native"
        execute([sys.executable, str(packet / "run_native.py"), "--aura-client", str(rooted(base, AURA)),
                 "--baseline-controller", str(rooted(base, CONTROLLER)), "--candidate-controller", str(rooted(on, CONTROLLER)),
                 "--candidate-sha256", lock["controller"]["candidate"]["sha256"], "--luau", str(bins["luau"]),
                 "--output", str(native_dir)], output, logs, "native_runner", commands)
        native = json.loads((native_dir / "receipt.json").read_text())
        require(native["run_mode"] == "BASELINE_AND_CANDIDATE" and native["native_starts"] == 2
                and native["baseline_expected_red_reproduced"] and native["candidate_all_expectations_passed"]
                and native["run_valid"] and native["inputs_unchanged"], "Native receipt is not exact baseline red/candidate green")
        require(len(native["runs"]) == 2 and all(len(run["expectations"]) == 13 for run in native["runs"]), "Native suite count changed")
        report["native"] = {"receipt": file_id(native_dir / "receipt.json"), "starts": 2,
                            "baseline_pass": native["runs"][0]["pass_count"], "baseline_fail": native["runs"][0]["fail_count"],
                            "candidate_pass": native["runs"][1]["pass_count"], "candidate_fail": native["runs"][1]["fail_count"],
                            "actual_native_commands": [run["command"] for run in native["runs"]]}
        place_name = lock["official_input"]["place"]["path"]
        for label, root in (("ON", on), ("OFF", off)):
            execute([str(bins["rojo"]), "build", str(rooted(root, project_name)), "-o", str(rooted(root, place_name))],
                    root, logs, "rojo_" + label.lower(), commands)
        on_xml = xml_inventory(rooted(on, place_name), on, selected, nodes)
        off_xml = xml_inventory(rooted(off, place_name), off, selected, nodes)
        require(on_xml["instances"] == off_xml["instances"] == baseline_xml["instances"], "Instance/class inventory changed")
        require(on_xml["xml_with_only_source_text_removed"] == off_xml["xml_with_only_source_text_removed"]
                == baseline_xml["xml_with_only_source_text_removed"], "Non-source XML properties changed")
        check_identity(rooted(off, place_name).read_bytes(), PLACE_ID, "actual OFF rebuilt Place")
        require(rooted(off, place_name).read_bytes() == rooted(base, place_name).read_bytes(), "OFF Place is not byte-exact")
        require({name: identity(rooted(on, name).read_bytes()) for name in wanted} == on_files,
                "ON project/source files drifted during commands")
        require({name: identity(rooted(off, name).read_bytes()) for name in wanted} == wanted,
                "OFF project/source files drifted during commands")
        report["xml"] = write_json(output / "XML_SOURCE_CLASS_INVENTORY.json", {"baseline": baseline_xml, "ON": on_xml, "OFF": off_xml})
        report["places"] = {"baseline": baseline_xml["place"], "candidate": on_xml["place"], "inverse": off_xml["place"],
                            "candidate_byte_delta": on_xml["place"]["bytes"] - PLACE_ID["bytes"],
                            "inverse_byte_equal": True, "instances": 75, "source_bodies": 69,
                            "non_source_properties_identical": True}
        selected_path = rooted(output / "selected_sources", CONTROLLER.removeprefix("sources/"))
        selected_path.parent.mkdir(parents=True, exist_ok=True)
        selected_path.write_bytes(rooted(on, CONTROLLER).read_bytes())
        report["selected_candidate_source"] = file_id(selected_path)
        require(inventory(base) == baseline_files, "Immutable delivery input drifted")
        require([file_id(path) for path in packet_paths] == packet_before, "Packet execution inputs drifted")
        require({name: file_id(path) for name, path in bins.items()} == bins_before, "Tool executable drifted")
        if args.archive:
            require(file_id(args.archive) == archive_before, "Immutable ZIP input drifted")
        report["read_only_inputs_unchanged"] = True
        report["packet_input_identities"] = packet_before
        report["status"] = "PASS_SOURCE_ONLY_NOT_STUDIO_NOT_FORMAL"
        success = True
    except Exception as error:
        report["status"] = "FAIL_CLOSED"
        report["error"] = {"type": type(error).__name__, "message": str(error)}
    report["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    write_json(output / "REPORT.json", report)
    if success:
        print("PASS source-only: 119 manifest entries; one changed Controller; 69 compiled; baseline 8P/5F; candidate 13P/0F; XML 69/75; OFF exact 828658 B")
    else:
        print("FAIL_CLOSED: " + report["error"]["message"], file=sys.stderr)
    print("REPORT=" + str(output / "REPORT.json"))
    return 0 if success else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"FAIL_CLOSED: {type(error).__name__}: {error}", file=sys.stderr)
        sys.exit(1)
