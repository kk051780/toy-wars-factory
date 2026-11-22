#!/usr/bin/env python3
"""Prepare canonical #487's existing 711-byte repair on one fixed union69 input.

This stage verifies source identity and an actual inverse. It does not certify
the unpublished upstream production envelope, execute Native, or build a Place.
"""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import json
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
PARENT_MANIFEST = "SCORE_RELAY_PARENT_SOURCE_MANIFEST.json"
BASE_SHA = "ef0c1bf657ecf9fb8883036b114e0a19bb6def86b46dec1b6f8b11ccb94662a9"
AFTER_SHA = "67c76c12cc4d311847fb1cf794988b2f164053690660f6b55f4e590f93824136"
FRAGMENT_SHA = "acf5c2d1bea91b1387251fd0de3c4cdc132fa42a818e8df1c8b366789381a55b"
PARENT_MANIFEST_SHA = "13000a809f2cf0c091af94d8f1dadbdf0ed972f2303bb85e0d5be2db04078e28"
ANCHOR = b'  elseif kind=="EGG_DEPOSIT" then\n'
STATUS = "SOURCE_ONLY_PREP_FINAL_UNION_CONTRACT_NOT_BOUND"


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
    lock["_lock_sha256"] = digest(raw)
    return lock


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


def verify_stage(root: Path, profile: str = "after") -> dict:
    root = Path(root)
    snapshot = validate_sources(root, profile)
    parent = parent_manifest_bytes(root)
    manifest_raw, receipt_raw = regular_file(root / MANIFEST), regular_file(root / RECEIPT)
    manifest, receipt = parse(manifest_raw), parse(receipt_raw)
    require(manifest == {"schema": "SCORE_RELAY_PREP_SOURCE_MANIFEST_V1", "status": STATUS, **snapshot},
            "STAGE_MANIFEST_BINDING")
    require(receipt.get("schema") == "SCORE_RELAY_PREP_RECEIPT_V1" and receipt.get("status") == STATUS,
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
        require(receipt.get("parent_stage_receipt") is None, "STAGE_RECEIPT_PARENT")
    else:
        predecessor = receipt.get("parent_stage_receipt")
        require(isinstance(predecessor, dict) and set(predecessor) == {"bytes", "sha256"}
                and type(predecessor["bytes"]) is int and predecessor["bytes"] > 0
                and re.fullmatch(r"[a-f0-9]{64}", predecessor["sha256"]) is not None, "STAGE_RECEIPT_PARENT")
    require(receipt.get("source_lock_sha256") == load_lock()["_lock_sha256"] and
            receipt.get("manifest") == info(manifest_raw) and receipt.get("parent_manifest") == info(parent),
            "STAGE_RECEIPT_PIN")
    require(receipt.get("final_union_contract_bound") is False and receipt.get("canonical_build") is False
            and receipt.get("official_build_head") is None, "STAGE_UNEARNED_PROVENANCE")
    result = {"status": STATUS, "profile": profile, "snapshot": snapshot,
              "manifest": info(manifest_raw), "receipt": info(receipt_raw), "parent_manifest": info(parent),
              "final_union_contract_bound": False, "canonical_build": False, "official_build_head": None}
    if (root / PLACE).exists() or (root / PLACE).is_symlink():
        result["place"] = verify_place(root, root / PLACE, profile)
    return result


def compose(input_root: Path, output_root: Path, direction: str = "on") -> dict:
    require(direction in {"on", "off"}, "DIRECTION")
    input_root, output_root = Path(input_root), Path(output_root)
    require(not output_root.exists() and not output_root.is_symlink(), "OUTPUT_EXISTS")
    source_abs, out_abs = input_root.resolve(), output_root.resolve()
    require(source_abs != out_abs and source_abs not in out_abs.parents and out_abs not in source_abs.parents,
            "INPUT_OUTPUT_OVERLAP")
    for path in (output_root.parent, *output_root.parent.parents):
        require(not path.is_symlink(), "OUTPUT_ANCESTOR_SYMLINK")
    before_profile, after_profile = ("before", "after") if direction == "on" else ("after", "before")
    original, contents, project = capture_sources(input_root, before_profile)
    parent = parent_manifest_bytes(input_root)
    input_stage = verify_stage(input_root, "after") if direction == "off" else None
    transformed = dict(contents)
    transformed[TARGET] = transform_score(contents[TARGET], direction)
    require([k for k in contents if contents[k] != transformed[k]] == [TARGET], "ONE_SELECTED_SOURCE_CHANGE")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    # Atomic exclusive reservation: no existing directory, even an empty one,
    # is replaced. A failure leaves its new incomplete directory for diagnosis.
    output_root.mkdir()
    for relative, raw in transformed.items():
        target = output_root / "sources" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        target.chmod(original["sources"][relative]["mode"])
    (output_root / PROJECT).write_bytes(project)
    (output_root / PROJECT).chmod(original["project_mode"])
    (output_root / PARENT_MANIFEST).write_bytes(parent)
    final = validate_sources(output_root, after_profile)
    require(validate_sources(input_root, before_profile) == original and
            parent_manifest_bytes(input_root) == parent, "INPUT_DRIFT_DURING_COMPOSITION")
    if input_stage is not None:
        require(verify_stage(input_root, "after") == input_stage, "ON_STAGE_DRIFT_DURING_INVERSE")
    require(final["source_lock_sha256"] == original["source_lock_sha256"], "LOCK_DRIFT_DURING_COMPOSITION")
    manifest = {"schema": "SCORE_RELAY_PREP_SOURCE_MANIFEST_V1", "status": STATUS, **final}
    manifest_raw = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    (output_root / MANIFEST).write_bytes(manifest_raw)
    receipt = {"schema": "SCORE_RELAY_PREP_RECEIPT_V1", "status": STATUS,
               "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "direction": direction, "input_profile": before_profile, "output_profile": after_profile,
               "input_snapshot": original, "output_snapshot": final,
               "only_changed_source": TARGET, "source_count": 69, "other_sources_preserved": 68,
               "source_lock_sha256": final["source_lock_sha256"], "parent_manifest": info(parent),
               "manifest": info(manifest_raw), "inverse_reads_actual_on_source": direction == "off",
               "parent_stage_receipt": input_stage["receipt"] if input_stage else None,
               "canonical_build": False, "official_build_head": None, "final_union_contract_bound": False,
               "Native_executed_by_composer": False, "Place_built_by_composer": False,
               "Studio_Android_ART_FUN": "NOT_VERIFIED", "RC_adopted_by_composer": False}
    # The receipt is written last. Consumers also re-read every actual source.
    (output_root / RECEIPT).write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return verify_stage(output_root, after_profile)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for action in ("compose", "inverse"):
        command = sub.add_parser(action)
        command.add_argument("--input", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
    command = sub.add_parser("verify")
    command.add_argument("--root", type=Path, required=True)
    command.add_argument("--profile", choices=("before", "after"), default="after")
    sub.add_parser("verify-final", help="Blocked until the actual union production contract is bound")
    args = parser.parse_args()
    if args.command == "verify-final":
        raise ScoreRelayError("FINAL_UNION_CONTRACT_NOT_BOUND")
    if args.command == "verify":
        result = verify_stage(args.root, args.profile)
    else:
        result = compose(args.input, args.output, "on" if args.command == "compose" else "off")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
