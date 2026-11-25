#!/usr/bin/env python3
"""Rebind the registered #1010 cleanup to real, current Union22 A-only inputs."""
from __future__ import annotations

import argparse
from collections import Counter
from difflib import SequenceMatcher
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
from xml.etree import ElementTree as ET
import zipfile

OFFICIAL_HEAD = "273e763c42ee0f405ef854b75c3cf071b078e896"
OFFICIAL_BRANCH = "rc/p0d-s1-kids-rc01"
ARTIFACT = {"run_id": 45516606797, "artifact_id": 14977773039, "bytes": 13407250,
            "sha256": "f4e8cfb036cfb83e33d95c20e0d9cf9522e5737881e26e61f317fccb230567b0"}
AUTHOR_HEAD = "19fe14a7b5cc4f4f7cfb09943128d7a1ebf803d4"
AUTHOR_BLOB = "3723dee279d5ed441e52485533ef889cdf1004a0"
TARGET = "ServerScriptService/EGGRUMBLE_EncounterReadabilityArt"
TARGET_FILE = "sources/" + TARGET + ".server.luau"
SOURCE_BEFORE = {"bytes": 22046, "sha256": "40f4f741be4b71a37085240927dc61fa1a776acceff759f268d97c6d115ec05c"}
SOURCE_AFTER = {"bytes": 22284, "sha256": "293eed3bff121484d132ecf7759d189fc3dc6d951412fd60f92f9598341b7837"}
PROJECT = "EGGRUMBLE_REAL69.project.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
PROJECT_PIN = {"bytes": 9564, "sha256": "90cf3f9fd181002b1b5521a30f17b15b5a14d73bd00f0755d77aaeb68f7885e7"}
GUARDIAN_FILE = "sources/ServerScriptService/EGGRUMBLE_CastleGuardianRuntime.luau"
GUARDIAN_PIN = {"bytes": 14201, "sha256": "a6a4433966ba52212d42e12dc69e8bca7a63424fe31c25ade89724928d417ef2"}
OFF_PLACE = {"bytes": 829822, "sha256": "ab6c1242a4df6d905b8abaf6662f78b704a15f707e2c6f2a838357f1feb511e5"}
ON_PLACE = {"bytes": 830060, "sha256": "0080dddb38dd9e551007e0526d81ba686aff5ad5fea0627f39caa04cda275bf3"}
MANIFEST = "UNION22_DELIVERY_MANIFEST.json"
ADMISSION = "UNION22_FINAL_ADMISSION.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
A_RECEIPT = "GQ470_ITEM_CLEANUP_A_ONLY_EVIDENCE.json"
REGISTERED = Path(__file__).with_name("current69") / "EncounterReadabilityArt.cleanup.luau.txt"
CLASS_COUNTS = {"ModuleScript": 47, "Script": 12, "LocalScript": 10}
HUNKS = [("replace", 195, 196, 195, 197), ("replace", 247, 248, 248, 250),
         ("insert", 257, 257, 259, 262), ("insert", 338, 338, 343, 346)]


def require(condition, reason):
    if not condition:
        raise ValueError("RED_ITEM_CLEANUP_" + reason)


def identity(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


def safe_path(path):
    parts = PurePosixPath(path).parts
    return bool(parts and not PurePosixPath(path).is_absolute() and ".." not in parts and "\\" not in path
                and str(PurePosixPath(path)) == path)


def read_zip(raw):
    contents = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for entry in archive.infolist():
            path = entry.filename.rstrip("/") if entry.is_dir() else entry.filename
            mode = (entry.external_attr >> 16) & 0xffff
            require(safe_path(path) and not mode & 0o7000,
                    "UNSAFE_ZIP_MEMBER")
            if entry.is_dir():
                require(stat.S_IFMT(mode) in (0, stat.S_IFDIR), "UNSAFE_ZIP_DIRECTORY")
                continue
            require(path not in contents and stat.S_IFMT(mode) in (0, stat.S_IFREG), "UNSAFE_ZIP_FILE")
            contents[path] = archive.read(entry)
    return contents


def project_routes(project):
    root = strict_json(project)["tree"]
    require(root.get("$className") == "DataModel", "PROJECT_ROOT")
    routes = {}

    def visit(node, parts):
        require(isinstance(node, dict), "PROJECT_NODE")
        if "$path" in node:
            path = node["$path"]
            route = "/".join(parts)
            require(isinstance(path, str) and safe_path(path) and path.startswith("sources/")
                    and path.endswith(".luau") and route not in routes, "PROJECT_ROUTE")
            routes[route] = path
        for name, value in node.items():
            if not name.startswith("$"):
                visit(value, parts + [name])
    visit(root, [])
    require(len(routes) == len(set(routes.values())) == 69 and routes.get(TARGET) == TARGET_FILE, "PROJECT_69")
    return routes


def scan_place(place, routes, classes, source):
    root = ET.fromstring(place)
    instances, observed = set(), set()

    def visit(node, parent):
        props = node.find("Properties")
        require(props is not None, "PLACE_PROPERTIES")
        names = [p.text for p in props if p.tag == "string" and p.get("name") == "Name"]
        require(len(names) == 1 and names[0], "INSTANCE_NAME")
        route = "/".join(parent + [names[0]])
        require(route not in instances, "DUPLICATE_INSTANCE")
        instances.add(route)
        cells = [p for p in props if p.get("name") == "Source"]
        actual = node.get("class")
        if cells or actual in CLASS_COUNTS:
            require(len(cells) == 1 and route in routes and actual == classes[route]
                    and cells[0].tag in ("string", "ProtectedString"), "PLACE_SOURCE_ROUTE_OR_CLASS")
            require((cells[0].text or "").encode() == source[routes[route]], "PLACE_EMBEDDED_SOURCE")
            cells[0].text = "__SOURCE__"
            observed.add(route)
        for child in node.findall("Item"):
            visit(child, parent + [names[0]])
    for node in root.findall("Item"):
        visit(node, [])
    require(len(instances) == 75 and observed == set(routes), "PLACE_69_SOURCES_75_INSTANCES")
    return ET.tostring(root, encoding="utf-8")


def verify_parent(contents):
    manifest = strict_json(contents[MANIFEST])
    recorded = manifest["files"]
    actual = {path: identity(body) for path, body in contents.items() if path != MANIFEST}
    require(len(contents) == 326 and len(recorded) == 325
            and manifest["schema"] == "UNION22_DELIVERY_FILES_V1"
            and manifest["manifest_self_excluded"] is True and manifest["current_place"] == PLACE
            and actual == recorded, "PARENT_MANIFEST_325")
    receipt = strict_json(contents[RECEIPT])
    admission = strict_json(contents[ADMISSION])
    require(admission["schema"] == "UNION22_FINAL_DELIVERY_ADMISSION_V1"
            and admission["status"] == "PASS_SOURCE_AND_NATIVE_ONLY"
            and admission["candidate_build_head"] == admission["official_build_head"] == OFFICIAL_HEAD
            and admission["receipt_provenance"] == "OFFICIAL" and admission["formal_rc_adoption_proven"] is True
            and admission["source_count"] == 69 and admission["instances"] == 75, "OFFICIAL_ADMISSION")
    require(receipt["build_head"] == receipt["official_build_head"] == OFFICIAL_HEAD
            and receipt["official_branch"] == OFFICIAL_BRANCH and receipt["receipt_provenance"] == "OFFICIAL"
            and receipt["canonical_build"] is True and receipt["formal_rc_adoption_proven"] is True
            and receipt["selected_source_count"] == 69, "OFFICIAL_RECEIPT")
    require(admission["current_place"] == identity(contents[PLACE]) == OFF_PLACE
            and receipt["private_place_bytes"] == OFF_PLACE["bytes"]
            and receipt["private_place_sha256"] == OFF_PLACE["sha256"], "PARENT_PLACE")
    require(identity(contents[PROJECT]) == PROJECT_PIN and identity(contents[GUARDIAN_FILE]) == GUARDIAN_PIN,
            "PROJECT_AND_GUARDIAN_PARENT_PINS")
    routes = project_routes(contents[PROJECT])
    hashes, classes = receipt["source_hashes"], receipt["source_classes"]
    require(set(hashes) == set(classes) == set(routes) and Counter(classes.values()) == CLASS_COUNTS
            and classes[TARGET] == "Script", "RECEIPT_ROUTE_CLASSES")
    require({p for p in contents if p.startswith("sources/")} == set(routes.values()), "ONLY_69_SOURCE_MEMBERS")
    source = {path: contents[path] for path in routes.values()}
    require(all(identity(source[path])["sha256"] == hashes[route] for route, path in routes.items()), "SOURCE_HASHES")
    require(identity(source[TARGET_FILE]) == SOURCE_BEFORE, "EXACT_IMMEDIATE_PREIMAGE")
    shape = scan_place(contents[PLACE], routes, classes, source)
    return routes, classes, source, shape


def registered_cleanup(original, candidate):
    require(identity(original) == SOURCE_BEFORE and identity(candidate) == SOURCE_AFTER,
            "REGISTERED_SOURCE_PAIR")
    git_object = b"blob " + str(len(candidate)).encode() + b"\0" + candidate
    require(hashlib.sha1(git_object).hexdigest() == AUTHOR_BLOB, "REGISTERED_GIT_BLOB")
    opcodes = SequenceMatcher(None, original.splitlines(keepends=True),
                              candidate.splitlines(keepends=True), autojunk=False).get_opcodes()
    require([row for row in opcodes if row[0] != "equal"] == HUNKS, "EXACT_FOUR_HUNKS")
    return candidate


def patch_artifact(artifact, out):
    raw = artifact.read_bytes()
    require(identity(raw) == {key: ARTIFACT[key] for key in ("bytes", "sha256")}, "OFFICIAL_ZIP_PIN")
    contents = read_zip(raw)
    _, _, original, _ = verify_parent(contents)
    candidate = original | {TARGET_FILE: registered_cleanup(original[TARGET_FILE], REGISTERED.read_bytes())}
    require(out.is_dir() and not (out / "ON69").exists() and not (out / "OFF69").exists(), "NEW_OUTPUT_PAIR")
    for name, sources in (("ON69", candidate), ("OFF69", original)):
        root = out / name
        root.mkdir()
        (root / PROJECT).write_bytes(contents[PROJECT])
        for path, body in sources.items():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)
    return {"scope": "A_ONLY_NOT_FORMAL", "official_parent_head": OFFICIAL_HEAD, "artifact": ARTIFACT,
            "author_original_head": AUTHOR_HEAD, "author_blob": AUTHOR_BLOB, "changed_source": TARGET,
            "before": SOURCE_BEFORE, "after": SOURCE_AFTER, "new_bytes": 238,
            "changed_sources": 1, "unchanged_sources": 68, "formal_rc_adoption": False,
            "studio": "NOT_TESTED", "android": "NOT_TESTED", "human_art": "NOT_TESTED",
            "art_gate": "ART_NO_GO", "product_gate": "PRODUCT_NO_GO"}


def verify_places(artifact, out, evidence):
    raw = artifact.read_bytes()
    require(identity(raw) == {key: ARTIFACT[key] for key in ("bytes", "sha256")}, "OFFICIAL_ZIP_CHANGED")
    contents = read_zip(raw)
    routes, classes, original, shape = verify_parent(contents)
    patched = original | {TARGET_FILE: registered_cleanup(original[TARGET_FILE], REGISTERED.read_bytes())}
    for name, wanted, sources in (("ON69", ON_PLACE, patched), ("OFF69", OFF_PLACE, original)):
        root = out / name
        place = (root / PLACE).read_bytes()
        require((root / PROJECT).read_bytes() == contents[PROJECT], "PROJECT_OUTPUT_DRIFT")
        require({p.relative_to(root).as_posix() for p in (root / "sources").rglob("*") if p.is_file()}
                == set(sources), "OUTPUT_SOURCE_MEMBERS")
        require(all((root / path).read_bytes() == body for path, body in sources.items()), "OUTPUT_SOURCE_DRIFT")
        require(identity(place) == wanted and scan_place(place, routes, classes, sources) == shape,
                "ROJO_EXACT_PLACE_OR_STRUCTURE")
        if name == "OFF69":
            require(place == contents[PLACE], "BYTE_EXACT_OFF_PLACE")
    native = out / "native"
    receipt_bytes = (native / "receipt.json").read_bytes()
    receipt = strict_json(receipt_bytes)
    require(receipt["scope"] == "A_ONLY_API_DOUBLE" and receipt["compile_count"] == 138
            and receipt["actual_luau_executions"] == 2 and receipt["candidate_pass"] == 5
            and receipt["baseline_control_pass"] == 1 and receipt["expected_baseline_remainders"] == 4
            and set(receipt["runs"]) == {"off", "on"}, "NATIVE_RECEIPT_COUNTS")
    for mode, wanted in (("off", SOURCE_BEFORE), ("on", SOURCE_AFTER)):
        files = native / mode
        row = receipt["runs"][mode]
        generated = (files / "generated.luau").read_bytes()
        first, last = row["source_range"]
        require(row["selected_source"] == identity(generated[first:last]) == wanted
                and identity(generated) == row["program"] and row["exit"] == 0
                and identity((files / "stdout.log").read_bytes()) == row["stdout"]
                and identity((files / "stderr.log").read_bytes()) == row["stderr"] == identity(b""),
                "NATIVE_RECEIPT_FILE_PIN")
    evidence.update({"on_place": ON_PLACE, "off_place": OFF_PLACE, "instances": 75,
                     "native_receipt": identity(receipt_bytes),
                     "source_inventory": 69, "rojo_round_trip": "PASS_BOTH_69", "byte_exact_off": True})
    (out / A_RECEIPT).write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-places", action="store_true")
    args = parser.parse_args()
    preliminary = args.output / "A_SOURCE_PREP.json"
    if args.verify_places:
        verify_places(args.artifact, args.output, strict_json(preliminary.read_bytes()))
    else:
        report = patch_artifact(args.artifact, args.output)
        preliminary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
