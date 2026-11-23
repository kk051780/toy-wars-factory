#!/usr/bin/env python3
"""Validate two exact published ZIP inputs; emit seven unattached ModuleScripts.

No extraction into either input, project rewrite, Place creation, Store edit or
runtime installation. Every input/path check precedes output creation.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode = True
HERE = Path(__file__).absolute().parent
NAMESPACE = "EGGRUMBLE_PersistentBaseSupport"
MODULE = "EGGRUMBLE_PersistentBaseAdmission"


def require(value, reason):
    if not value:
        raise ValueError("PERSISTENT_BASE_PREP_" + reason)


def identity(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result
    def nonfinite(_):
        raise ValueError("PERSISTENT_BASE_PREP_NONFINITE_JSON")
    return json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)


def safe_path(value):
    require(isinstance(value, (str, Path)) and str(value).strip() != "", "EMPTY_PATH")
    path = Path(value).absolute()
    require(".." not in path.parts and not any(p.is_symlink() for p in (path, *path.parents)),
            "SYMLINK_OR_PARENT_TRAVERSAL")
    return path


def read_file(value):
    path = safe_path(value)
    require(path.is_file() and stat.S_ISREG(path.stat().st_mode), "REGULAR_FILE_REQUIRED")
    return path.read_bytes()


def member_name(value):
    require(isinstance(value, str) and value and "\\" not in value and "\x00" not in value,
            "BAD_MEMBER_NAME")
    path = PurePosixPath(value)
    require(not path.is_absolute() and all(x not in ("", ".", "..") for x in value.rstrip("/").split("/"))
            and ":" not in path.parts[0], "MEMBER_PATH_ESCAPE")
    return value


def zip_members(raw):
    result, folded, total = {}, set(), 0
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        require(len(archive.infolist()) <= 1000, "ZIP_ENTRY_LIMIT")
        for info in archive.infolist():
            name = member_name(info.filename)
            key = name.rstrip("/").casefold()
            require(key not in folded, "DUPLICATE_ZIP_MEMBER")
            folded.add(key)
            mode = info.external_attr >> 16
            require(not info.flag_bits & 1 and not stat.S_ISLNK(mode), "ENCRYPTED_OR_SYMLINK_MEMBER")
            kind = stat.S_IFMT(mode)
            require(kind in (0, stat.S_IFREG, stat.S_IFDIR), "SPECIAL_ZIP_MEMBER")
            total += info.file_size
            require(info.file_size <= 32 * 1024 * 1024 and total <= 256 * 1024 * 1024,
                    "ZIP_SIZE_LIMIT")
            if not info.is_dir():
                result[name] = archive.read(info)
    return result


def place_sources(raw):
    require(b"<!DOCTYPE" not in raw.upper() and b"<!ENTITY" not in raw.upper(), "XML_DECLARATION")
    root = ET.fromstring(raw)
    require(root.tag == "roblox" and root.get("version") == "4", "PLACE_SCHEMA")
    rows, routes, count = {}, set(), 0
    def visit(item, parent):
        nonlocal count
        count += 1
        props = item.find("Properties")
        require(props is not None, "ITEM_PROPERTIES")
        names = [p for p in props if p.get("name") == "Name"]
        require(len(names) == 1 and names[0].text and "/" not in names[0].text, "ITEM_NAME")
        route = "/".join((*parent, names[0].text))
        require(route not in routes, "DUPLICATE_INSTANCE_ROUTE")
        routes.add(route)
        values = [p for p in props if p.get("name") == "Source"]
        require(len(values) <= 1, "DUPLICATE_SOURCE_PROPERTY")
        if values:
            require(item.get("class") in ("ModuleScript", "Script", "LocalScript"), "SOURCE_CLASS")
            rows[route] = {"class": item.get("class"), "raw": (values[0].text or "").encode("utf-8")}
        for child in item.findall("Item"):
            visit(child, (*parent, names[0].text))
    for item in root.findall("Item"):
        visit(item, ())
    return rows, count


def load_lock():
    read_file(__file__)  # Reject a symlinked script as well as symlinked ancestors.
    lock = strict_json(read_file(HERE / "source_lock.json"))
    require(lock.get("schema") == "P0D033_PERSISTENT_BASE_SOURCE_INPUTS_V1", "LOCK_SCHEMA")
    require(len(lock["donors"]) == 6 and len(lock["selected69"]) == 69, "LOCK_COUNTS")
    require(lock["adapter"]["file"] == MODULE + ".luau", "ADAPTER_FILENAME")
    return lock


def verify_inputs(official_zip, donor_zip):
    lock = load_lock()
    paths = [safe_path(official_zip), safe_path(donor_zip)]
    require(paths[0] != paths[1], "SAME_INPUT_FILE")
    originals = [read_file(path) for path in paths]
    for raw, label in zip(originals, ("official", "donor")):
        require(identity(raw) == lock[label]["zip"], "EXACT_" + label.upper() + "_ZIP")
    official, donor = [zip_members(raw) for raw in originals]
    for members, label in ((official, "official"), (donor, "donor")):
        for name, pin in lock[label]["members"].items():
            require(name in members and identity(members[name]) == pin, "PINNED_MEMBER:" + name)
    current, current_count = place_sources(official[lock["official"]["place_member"]])
    prior, prior_count = place_sources(donor[lock["donor"]["place_member"]])
    require(current_count == 75 and len(current) == 69 and prior_count == 77 and len(prior) == 66,
            "PLACE_INSTANCE_COUNTS")
    require(dict(Counter(x["class"] for x in current.values())) ==
            {"ModuleScript": 47, "Script": 12, "LocalScript": 10}, "SELECTED_CLASSES")
    project = strict_json(official["EGGRUMBLE_REAL69.project.json"])
    profile = strict_json(official["UNION22_PROFILE_LOCK.json"])
    delivery = strict_json(official["UNION22_DELIVERY_MANIFEST.json"])
    intake = strict_json(official["REAL69_LEGACY_INTAKE_RECEIPT.json"])
    require(profile["schema"] == "GQ470_UNION22_PRODUCTION_PROFILE_V1"
            and delivery["schema"] == "UNION22_DELIVERY_FILES_V1"
            and intake["schema"] == "GQ470_UNION22_CURRENT_SOURCE_RECEIPT_V1", "CURRENT_SCHEMAS")
    context = intake["execution_context"]
    require(context["checkout_sha"] == lock["official"]["head"]
            and context["official_build_head"] == lock["official"]["head"]
            and context["run_id"] == str(lock["official"]["run_id"])
            and context["event"] == "push" and context["canonical_build"] is True,
            "OFFICIAL_EXECUTION_BINDING")
    selected = {}
    def walk(node, route):
        require(isinstance(node, dict), "PROJECT_NODE")
        if "$path" in node:
            name = member_name(node["$path"])
            require(name.startswith("sources/") and name.endswith(".luau"), "PROJECT_SOURCE_PATH")
            relative = name[len("sources/"):]
            require(relative not in selected, "PROJECT_DUPLICATE_PATH")
            selected[relative] = {"member": name, "route": "/".join(route)}
        for key, child in node.items():
            if not key.startswith("$"):
                walk(child, (*route, key))
    require(project["tree"]["$className"] == "DataModel", "PROJECT_ROOT")
    walk(project["tree"], ())
    require(set(selected) == set(profile["sources"]) == set(lock["selected69"]), "SELECTED_SET")
    require({x["route"] for x in selected.values()} == set(current), "SOURCE_ROUTE_SET")
    require({x["member"] for x in selected.values()} ==
            {n for n in official if n.startswith("sources/") and n.endswith(".luau")}, "SOURCE_MEMBER_SET")
    for relative, row in selected.items():
        expected = lock["selected69"][relative]
        actual = profile["sources"][relative]
        body = official[row["member"]]
        placed = current[row["route"]]
        require(row["route"] == actual["route"] == expected["route"]
                and actual["class"] == placed["class"] == expected["class"]
                and identity(body) == actual["after"] == expected["identity"]
                and placed["raw"] == body
                and delivery["files"][row["member"]] == identity(body)
                and intake["source_hashes"][row["route"]] == identity(body)["sha256"]
                and intake["source_classes"][row["route"]] == placed["class"],
                "SELECTED_BODY_ROUTE_BINDING:" + relative)
    manifest = strict_json(donor["ACTIVE_RUNTIME_SOURCE_MANIFEST.json"])
    require(manifest["schema"] == "ACTIVE_RUNTIME_SELECTED_SOURCES_V1"
            and manifest["profile"] == "rich51" and manifest["source_count"] == 66, "DONOR_MANIFEST")
    bodies = {}
    for name, row in lock["donors"].items():
        actual = prior[row["route"]]
        declared = manifest["sources"][row["manifest_key"]]
        require(actual["class"] == declared["class"] == "ModuleScript"
                and declared["instance_path"] == row["route"]
                and identity(actual["raw"]) == row["identity"]
                and {k: declared[k] for k in ("bytes", "sha256")} == row["identity"],
                "DONOR_FULL_BODY:" + name)
        bodies[name] = actual["raw"]
    adapter = read_file(HERE / lock["adapter"]["file"])
    require(identity(adapter) == lock["adapter"]["identity"], "ADAPTER_CHANGED")
    bodies[MODULE] = adapter
    require(all(read_file(path) == raw for path, raw in zip(paths, originals)), "INPUT_CHANGED_DURING_READ")
    return lock, paths, originals, bodies


def prepare(official_zip, donor_zip, output):
    out = safe_path(output)
    require(not out.exists() and out.parent.is_dir(), "OUTPUT_MUST_BE_NEW_WITH_EXISTING_PARENT")
    inputs = [safe_path(official_zip), safe_path(donor_zip)]
    require(out not in inputs and all(not path.is_relative_to(out) for path in inputs), "OUTPUT_OVERLAPS_INPUT")
    lock, paths, originals, bodies = verify_inputs(official_zip, donor_zip)
    # All immutable-input and path checks have passed before the first write.
    out.mkdir()
    modules = out / NAMESPACE
    modules.mkdir()
    for name, body in sorted(bodies.items()):
        with (modules / (name + ".luau")).open("xb") as stream:
            stream.write(body)
    require(all(read_file(path) == raw for path, raw in zip(paths, originals)), "INPUT_CHANGED_DURING_OUTPUT")
    receipt = {"schema": "P0D033_UNATTACHED_PREPARATION_RECEIPT_V1", "status": "INPUTS_VERIFIED_OUTPUT_PREPARED",
               "official_head": lock["official"]["head"], "donor_head": lock["donor"]["head"],
               "input_zips_unchanged": True, "inputs": {label: identity(raw) for label, raw in zip(("official", "donor"), originals)},
               "selected_sources_preserved": 69, "original_project_and_place_unchanged": True,
               "output_namespace": NAMESPACE, "modules": {name: identity(raw) for name, raw in sorted(bodies.items())},
               "unchanged_donors": 6, "new_unattached_module": 1, "created_place": False,
               "installed_in_runtime": False, "source_accepted": False, "PREP_READY": False,
               "RC_adopted": False, "studio_or_actual_datastore_verified": False}
    with (out / "PREPARE_RECEIPT.json").open("x") as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official-zip", required=True)
    parser.add_argument("--donor-zip", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        receipt = prepare(args.official_zip, args.donor_zip, args.output)
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}))
        return 2
    print(json.dumps(receipt, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
