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
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
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

BOT_INPUTS = {
    "bot_vault_base.template.luau": {"bytes": 39006, "sha256": "ba71e926da72b3c60118751d4c89ba4086dfec24a9d67b0d2ee9a04877f81ad7"},
    "bot_vault_cases.json": {"bytes": 71446, "sha256": "dc1434c328ab30853a75993d2f6042b01e1d0bdc8733c528d4a9b39b7557289c"},
    "bot_vault_suite.py": {"bytes": 20273, "sha256": "e0f72127a01f9a6af8422a5d35d6f515f9a3f00eb75f43a2ef8624df1fb46c09"},
}
BOT_SCENARIOS = (
    "candidate_route62_TEAM_normal", "candidate_route62_TEAM_slow",
    "candidate_route62_BATTLE_ROYALE_normal", "candidate_route62_BATTLE_ROYALE_slow",
    "candidate_route58_TEAM_normal", "candidate_contracts_TEAM_normal",
    "candidate_actors_TEAM_normal", "candidate_eggs_TEAM_normal", "candidate_parallel_TEAM_normal",
)


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


# Positive-only exact-byte cache, bounded to one verifier process.
_archive_verified = set()


def verify_archive(path, expected, prefix=compose.OFF):
    archive_raw = read(path)
    pin = digest(archive_raw)
    key = (pin['bytes'], pin['sha256'], prefix,
           json.dumps(expected, sort_keys=True, separators=(',', ':'), ensure_ascii=True))
    if key in _archive_verified:
        return {name: dict(pin) for name, pin in expected.items()}
    observed = {}
    with tempfile.TemporaryDirectory(prefix="union22-inverse-verify-") as tmp:
        with tarfile.open(fileobj=io.BytesIO(archive_raw), mode="r:gz") as archive:
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
    if len(_archive_verified) >= 64:
        _archive_verified.clear()
    _archive_verified.add(key)
    return observed


def verify_single_source_rollback(root, input_folder, lock, current, name, repair, previous,
                                  expected_place, rollback_dir, archive, reason):
    require(repair["source_path"] == name, reason + "_ROLLBACK_CONTRACT")
    rows = {name: {"parent": previous, "inverse": repair["inverse"], "forward": repair["forward"]}}
    return verify_source_rollback(root, input_folder, lock, current, repair, rows, expected_place,
                                  rollback_dir, archive, reason)


def verify_source_rollback(root, input_folder, lock, current, repair, rows, expected_place,
                           rollback_dir, archive, reason):
    require(repair["repaired_place"] == lock["final_place"] and repair["parent_place"] == expected_place
            and all(row["parent"]["before"] == lock["sources"][name]["before"] for name,row in rows.items()),
            reason + "_ROLLBACK_CONTRACT")
    parent_lock = lock | {"sources": lock["sources"] | {name: row["parent"] for name,row in rows.items()},
                          "final_place": repair["parent_place"]}
    folder = root / rollback_dir
    parent = independent_scan(folder, parent_lock, "after")
    require(parent["non_source"] == current["non_source"] and parent["instances"] == current["instances"],
            reason + "_ROLLBACK_NON_SOURCE_DRIFT")
    for path in parent_lock["sources"]:
        on, off = (read(location / "sources" / path) for location in (input_folder, folder))
        if path in rows:
            row = rows[path]
            require(on != off and independent_inverse(on, row["inverse"]) == off
                    and independent_inverse(off, row["forward"]) == on, reason + "_EXACT_TWO_WAY")
        else:
            require(on == off, reason + "_ROLLBACK_ADDITIONAL_SOURCE_CHANGE")
    expected = {"sources/" + source: item["after"] for source, item in parent_lock["sources"].items()}
    expected.update({compose.PROJECT: parent_lock["project"], compose.PLACE: parent_lock["final_place"]})
    require(len(expected) == 71 and files(folder) == expected, reason + "_ROLLBACK_MEMBER_SET")
    verify_archive(root / archive, expected, rollback_dir)
    return expected, parent_lock, parent


def verify_guardian_parent_rollback(root, lock, current, input_folder=None):
    repair = lock["guardian_followup_repair"]
    name = compose.GUARDIAN_SOURCE
    row = lock["sources"][name]
    require(repair["source_path"] == name and repair["repaired_place"] == lock["final_place"]
            and repair["parent_place"] == lock["beast_followup_repair"]["repaired_place"]
            and repair["repaired_guardian"] == row["after"]
            and repair["parent_guardian_row"]["after"] == repair["parent_guardian"]
            and repair["parent_guardian_row"]["before"] == row["before"]
            and repair["changed_sources_from_beast_parent"] == 1
            and repair["unchanged_sources_from_beast_parent"] == 68, "GUARDIAN_ROLLBACK_CONTRACT")
    parent_lock = lock | {
        "sources": lock["sources"] | {name: repair["parent_guardian_row"]},
        "final_place": repair["parent_place"],
    }
    folder = root / compose.GUARDIAN_OFF
    parent = independent_scan(folder, parent_lock, "after")
    require(parent["non_source"] == current["non_source"]
            and parent["instances"] == current["instances"], "GUARDIAN_ROLLBACK_NON_SOURCE_DRIFT")
    changed = []
    for candidate in parent_lock["sources"]:
        raw = read((input_folder or root) / "sources" / candidate)
        off = read(folder / "sources" / candidate)
        if candidate == name:
            require(independent_inverse(raw, repair["inverse"]) == off
                    and independent_inverse(off, repair["forward"]) == raw, "GUARDIAN_EXACT_TWO_WAY")
        else:
            require(raw == off, "GUARDIAN_ROLLBACK_ADDITIONAL_SOURCE_CHANGE")
        if raw != off:
            changed.append(candidate)
    require(changed == [name], "GUARDIAN_ROLLBACK_SCOPE")
    expected = {"sources/" + source: item["after"] for source, item in parent_lock["sources"].items()}
    expected.update({compose.PROJECT: parent_lock["project"], compose.PLACE: parent_lock["final_place"]})
    require(len(expected) == 71 and files(folder) == expected, "GUARDIAN_ROLLBACK_MEMBER_SET")
    verify_archive(root / compose.GUARDIAN_OFF_ARCHIVE, expected, compose.GUARDIAN_OFF)
    return expected, parent_lock, parent


def verify_beast_parent_rollback(root, lock, current, input_folder=None):
    repair = lock["beast_followup_repair"]
    row = repair["parent_combat_row"]
    require(repair["source_path"] == compose.BEAST_SOURCE
            and repair["parent_combat"] == row["after"]
            and repair["repaired_combat"] == lock["sources"][compose.BEAST_SOURCE]["after"]
            and repair["parent_place"] == lock["bot_followup_repair"]["repaired_place"]
            and repair["repaired_place"] == lock["final_place"]
            and repair["changed_sources_from_h72_parent"] == 1
            and repair["unchanged_sources_from_h72_parent"] == 68, "BEAST_ROLLBACK_IDENTITY")
    parent_lock = lock | {
        "sources": lock["sources"] | {compose.BEAST_SOURCE: row},
        "final_place": repair["parent_place"],
    }
    off = root / compose.BEAST_OFF
    parent = independent_scan(off, parent_lock, "after")
    require(parent["non_source"] == current["non_source"]
            and parent["instances"] == current["instances"], "BEAST_ROLLBACK_NON_SOURCE_DRIFT")
    changed = []
    for name in parent_lock["sources"]:
        raw = read((input_folder or root) / "sources" / name)
        restored = read(off / "sources" / name)
        if name == compose.BEAST_SOURCE:
            require(independent_inverse(raw, repair["inverse"]) == restored
                    and independent_inverse(restored, repair["forward"]) == raw, "BEAST_EXACT_TWO_WAY")
        else:
            require(raw == restored, "BEAST_ADDITIONAL_SOURCE_CHANGE")
        if raw != restored:
            changed.append(name)
    require(changed == [compose.BEAST_SOURCE], "BEAST_ROLLBACK_SCOPE")
    expected = {"sources/" + p: v["after"] for p, v in parent_lock["sources"].items()}
    expected.update({compose.PROJECT: parent_lock["project"], compose.PLACE: repair["parent_place"]})
    require(len(expected) == 71 and files(off) == expected, "BEAST_ROLLBACK_MEMBER_SET")
    verify_archive(root / compose.BEAST_OFF_ARCHIVE, expected, compose.BEAST_OFF)
    return expected, parent_lock, parent


def verify_bot_parent_rollback(root, lock, current):
    """Independently check final -> Bot-only OFF -> frozen HUD preview parent."""
    repair = lock["bot_followup_repair"]
    row = lock["sources"][compose.BOT_SOURCE]
    require(repair["source_path"] == compose.BOT_SOURCE
            and repair["changed_sources_from_hud_parent"] == 1
            and repair["unchanged_sources_from_hud_parent"] == 68, "BOT_ROLLBACK_SCOPE")
    require(repair["parent_bot"] == row["before"] and repair["repaired_bot"] == row["after"]
            and repair["forward"] == row["forward"] and repair["inverse"] == row["inverse"]
            and repair["parent_place"] == lock["followup_repair"]["repaired_place"]
            and repair["repaired_place"] == lock["final_place"], "BOT_ROLLBACK_CONTRACT")
    parent_lock = dict(lock)
    parent_lock["sources"] = {p: dict(r) for p, r in lock["sources"].items()}
    parent_lock["sources"][compose.BOT_SOURCE]["after"] = repair["parent_bot"]
    parent_lock["final_place"] = repair["parent_place"]
    parent = independent_scan(root / compose.BOT_OFF, parent_lock, "after")
    require(parent["non_source"] == current["non_source"]
            and parent["instances"] == current["instances"], "BOT_ROLLBACK_NON_SOURCE_DRIFT")
    changes = []
    for name in lock["sources"]:
        final = read(root / compose.BEAST_OFF / "sources" / name)
        restored = read(root / compose.BOT_OFF / "sources" / name)
        expected = independent_inverse(final, repair["inverse"]) if name == compose.BOT_SOURCE else final
        require(restored == expected, "BOT_ROLLBACK_INVERSE_NOT_PARENT")
        if final != restored:
            changes.append(name)
    require(changes == [compose.BOT_SOURCE], "BOT_ROLLBACK_CHANGE_SET")
    expected = {"sources/" + p: r["after"] for p, r in parent_lock["sources"].items()}
    expected.update({compose.PROJECT: lock["project"], compose.PLACE: repair["parent_place"]})
    require(len(expected) == 71 and files(root / compose.BOT_OFF) == expected, "BOT_ROLLBACK_MEMBER_SET")
    verify_archive(root / compose.BOT_OFF_ARCHIVE, expected, compose.BOT_OFF)
    return expected


def verify_hud_current_rollback(root, lock, current):
    """Independently check HUD-parent -> HUD-only OFF -> historical fb5."""
    repair = lock["followup_repair"]
    require(repair["source_path"] == compose.HUD_SOURCE
            and repair["changed_sources_from_current_rc"] == 1
            and repair["unchanged_sources_from_current_rc"] == 68,
            "HUD_ROLLBACK_SCOPE")
    rollback_lock = dict(lock)
    rollback_lock["sources"] = {p: dict(row) for p, row in lock["sources"].items()}
    rollback_lock["sources"][compose.BOT_SOURCE]["after"] = lock["bot_followup_repair"]["parent_bot"]
    rollback_lock["final_place"] = lock["bot_followup_repair"]["parent_place"]
    parent = independent_scan(root / compose.BOT_OFF, rollback_lock, "after")
    require(parent["non_source"] == current["non_source"]
            and parent["instances"] == current["instances"], "HUD_PARENT_NON_SOURCE_DRIFT")
    rollback_lock["sources"][compose.HUD_SOURCE]["after"] = repair["current_hud"]
    rollback_lock["final_place"] = repair["current_place"]
    restored = independent_scan(root / compose.HUD_OFF, rollback_lock, "after")
    require(restored["non_source"] == current["non_source"]
            and restored["instances"] == current["instances"], "HUD_ROLLBACK_NON_SOURCE_DRIFT")
    changes = []
    for name, row in lock["sources"].items():
        repaired = read(root / compose.BOT_OFF / "sources" / name)
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


def neutral_names_author(lock):
    record = lock["neutral_names_followup"]
    return visual_author("quality_gameplay/gq470_art16_p0_lobby_composite_20261121/neutral_name_visibility_fix.py",
                         record["author_transform"], "NEUTRAL_NAMES_AUTHOR")


def visual_author(relative, pin, label):
    path = REPO / relative
    require(digest(read(path)) == pin, label + "_IDENTITY")
    spec = importlib.util.spec_from_file_location("union22_" + label.lower(), path)
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    return original


def verify_growth_donor_sources(root, repair):
    donor_files = repair["donor_files"]
    require(len(donor_files) == 11 and all(digest(read(REPO / name)) == pin
                                          for name, pin in donor_files.items()), "GROWTH_MUSOU_DONOR_PINS")
    parent = root / compose.GROWTH_MUSOU_OFF / "sources"
    current = root / compose.ART_POLISH_OFF / "sources"
    growth_path = repair["origins"]["growth"]["package"] + "/apply_growth.py"
    source = visual_author(growth_path, donor_files[growth_path], "GROWTH_ORIGINAL")
    _, patch = source.load_contract()
    for entry in patch["files"]:
        relative = entry["path"]
        result = read(parent / relative)
        for row in entry["hunks"]:
            before, after = (row[p].encode("utf-8") for p in ("old", "new"))
            require(result.count(before) == 1, "GROWTH_ORIGINAL_HUNK:" + row["name"])
            result = result.replace(before, after, 1)
        require(result == read(current / relative), "GROWTH_EXACT_REUSE:" + relative)
    aura_dir = repair["origins"]["aura"]["package"]
    aura_path = aura_dir + "/apply_lifecycle.py"
    aura = visual_author(aura_path, donor_files[aura_path], "MUSOU_AURA_ORIGINAL")
    aura_lock = aura.load_lock(REPO / aura_dir / "source_lock.json")
    original = read(parent / aura.CONTROLLER.removeprefix("sources/"))
    selected = read(current / aura.CONTROLLER.removeprefix("sources/"))
    candidate = read(REPO / aura_dir / "MusouAuraController.client.luau")
    client = aura.AURA.removeprefix("sources/")
    require(aura.forward(original, candidate, aura_lock) == selected
            and aura.inverse(selected, original, aura_lock) == original
            and read(parent / client) == read(current / client)
            and digest(read(current / client)) == aura.AURA_ID, "MUSOU_AURA_EXACT_REUSE")


def verify_art_polish_donors(root, art):
    inputs = art["donors"]
    require(set(inputs) == {"skill", "twin", "field", "castle", "ridge", "guardian", "guardian_gate",
                            "result_gate", "result_patch"}, "ART_POLISH_DONOR_SET")
    for row in inputs.values():
        require(digest(read(REPO / row["path"])) == row["identity"], "ART_POLISH_AUTHOR_BYTES")

    def author(name):
        row = inputs[name]
        return visual_author(row["path"], row["identity"], "ART_POLISH_AUTHOR_" + name)

    current = root / compose.MAGE_CONTACT_OFF / "sources"
    prior = root / compose.ART_POLISH_OFF / "sources"
    routes = sorted(art["rows"])
    guard, field, twin, result, skill = routes
    before = {route: read(prior / route) for route in routes}
    actual = {route: read(current / route) for route in routes}
    require(routes == list(compose.ART_POLISH_SOURCES), "ART_POLISH_EXACT_ROUTES")
    guard_author = author("guardian")
    guard_author.SOURCE_SHA = art["rows"][guard]["parent"]["after"]["sha256"]
    guard_gate = author("guardian_gate")
    guard_gate.inspect(before[guard], actual[guard], lock=False)
    require(guard_author.patch(before[guard]) == actual[guard], "ART_POLISH_GUARDIAN_EXACT")
    sys.path.insert(0, str(REPO / "quality_gameplay/gq8_rc85_rc86_real68_nonloss_20261120"))
    try:
        field_author, castle, ridge = author("field"), author("castle"), author("ridge")
        require(field_author.artist_composite(before[field].decode(), castle, ridge).encode() == actual[field],
                "ART_POLISH_FIELD_EXACT")
    finally:
        sys.path.pop(0)
    require(author("twin").patch(before[twin].decode()).encode() == actual[twin], "ART_POLISH_TWIN_EXACT")
    require(author("skill").transform(before[skill].decode()).encode() == actual[skill], "ART_POLISH_SKILLFX_EXACT")
    author("result_gate").validate_patch(before[result].decode(), actual[result].decode())
    patch_lines = read(REPO / inputs["result_patch"]["path"]).splitlines(keepends=True)[2:]
    background, additions = [
        [line for line in section.splitlines(keepends=True) if line.startswith((b"+", b"-"))]
        for section in b"".join(patch_lines).split(b"@@")[2::2]
    ]
    removed, added = background
    anchor = b" corner.Parent=frame\n"
    require(removed.startswith(b"-") and added.startswith(b"+")
            and all(line.startswith(b"+") for line in additions)
            and before[result].count(removed[1:]) == 1 and before[result].count(anchor) == 1,
            "ART_POLISH_RESULT_AUTHOR_HUNKS")
    expected = before[result].replace(removed[1:], added[1:], 1)
    expected = expected.replace(anchor, anchor + b"".join(line[1:] for line in additions), 1)
    require(expected == actual[result], "ART_POLISH_RESULT_EXACT")


def verify_exact_author_patch(root, rollback, routes, author, label, flags=(), *, result_stage=""):
    patch = REPO / author["path"]
    require(digest(read(patch)) == author["identity"], label + "_AUTHOR_PATCH")
    prior = root / rollback / "sources"
    with tempfile.TemporaryDirectory(prefix="union22-author-patch-") as directory:
        base = Path(directory) / "patch"
        for relative in routes:
            target = base / "sources" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(read(prior / relative))
        operation = ["git", "-c", "core.autocrlf=false", "apply", "--no-index", *flags, str(patch)]
        result = subprocess.run(operation, cwd=base, env={**os.environ, "GIT_CEILING_DIRECTORIES": directory},
                                capture_output=True, timeout=20)
        require(result.returncode == 0, label + "_AUTHOR_PATCH_FAILED:" + result.stderr.decode(errors="replace"))
        require(all(read(base / "sources" / relative) == read(root / result_stage / "sources" / relative)
                    for relative in routes), label + "_AUTHOR_PATCH_DRIFT")


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
    require(len(changed) == 37 and len(lock["sources"]) - len(changed) == 32, "CHANGE_COUNT")
    for name, row in lock["sources"].items():
        require(independent_inverse(read(root / "sources" / name), row["inverse"])
                == read(root / compose.OFF / "sources" / name) == inputs["sources"][name], "INVERSE_NOT_PRIOR_BR")
    expected_off = {"sources/" + p: row["before"] for p, row in lock["sources"].items()}
    expected_off.update({compose.PROJECT: lock["project"], compose.PLACE: lock["prior_place"],
                         compose.RECEIPT: digest(inputs["receipt_raw"])})
    expected_off.update({p: digest(inputs["evidence"][p]) for p in lock["prior_report_names"]})
    require(len(expected_off) == 75 and files(root / compose.OFF) == expected_off, "OFF_RUNTIME_MEMBER_SET")
    archive = verify_archive(root / compose.OFF_ARCHIVE, expected_off)
    vault = lock["empty_vault_followup"]
    item = lock["item_cleanup_followup"]
    castle = lock["castle_release_stock_followup"]
    score = lock["score_relay_followup"]
    relay = lock["relay_presentation_followup"]
    canyon = lock["br_canyon_followup"]
    role = lock["role_readability_followup"]
    field_prompt = lock["field_prompt_followup"]
    neutral_names = lock["neutral_names_followup"]
    wall = lock["guardian_wall_followup"]
    combat = lock["combat_visual_followup"]
    growth = lock["growth_musou_followup"]
    art_polish = lock["art_polish_followup"]
    mage = lock["mage_contact_followup"]
    eligibility = lock["relay_eligibility_followup"]
    moguron = lock["moguron_followup"]
    private_touch = lock["private_touch_followup"]
    portrait = lock["portrait_followup"]
    shorefoam = lock["shorefoam_followup"]
    hp = lock["fractional_hp_followup"]
    require(set(hp["rows"]) == {compose.HUD_SOURCE}
            and hp["feedback"] == {"id": "FB-002", "issue": 364}, "FRACTIONAL_HP_SCOPE")
    hp_row = hp["rows"][compose.HUD_SOURCE]
    require(len(hp_row["forward"]) == len(hp_row["inverse"]) == 1, "FRACTIONAL_HP_SINGLE_HUNK")
    projectiles = lock["mage_projectile_followup"]
    require(set(projectiles["rows"]) == set(compose.MAGE_PROJECTILES_SOURCES)
            and projectiles["ids"] == ["MAGE-033", "MAGE-051", "MAGE-071"]
            and projectiles["catalog_commit"] == "6810cefc345066ad465b981aabca045499add6d5",
            "MAGE_PROJECTILES_SCOPE")
    water_chain = lock["mage_water_chain_followup"]
    require(set(water_chain["rows"]) == set(compose.MAGE_WATER_CHAIN_SOURCES)
            and water_chain["ability_ids"] == ["MAGE-041", "MAGE-025"]
            and water_chain["combo_ids"] == ["COMBO-004"]
            and water_chain["original_combo_sha"] == "3b96ac3bc4284afa5d3907733f0d64b4c5470685",
            "MAGE_WATER_CHAIN_SCOPE")
    ninja_s4 = lock["ninja_s4_followup"]
    require(set(ninja_s4["rows"]) == set(compose.NINJA_S4_SOURCES)
            and ninja_s4["ability_ids"] == ["NINJA-031", "NINJA-061"]
            and ninja_s4["combo_ids"] == ["COMBO-008"]
            and ninja_s4["s4_hero_roles"] == ["BEAST", "BUILDER", "MAGE", "NINJA",
                                              "TRAPPER", "WARRIOR", "ZOMBIE"], "NINJA_S4_SCOPE")
    wing_warrior = lock["wing_warrior_followup"]
    require(set(wing_warrior["rows"]) == set(compose.WING_WARRIOR_SOURCES)
            and wing_warrior["ability_ids"] == ["MAGE-001", "MAGE-011", "MAGE-012", "MAGE-026",
                                              "MAGE-040", "WARRIOR-016", "WARRIOR-071"]
            and wing_warrior["combo_ids"] == ["COMBO-005", "COMBO-002"], "WING_WARRIOR_SCOPE")
    field_loadouts = lock["field_loadouts_followup"]
    require(set(field_loadouts["rows"]) == set(compose.FIELD_LOADOUTS_SOURCES)
            and field_loadouts["ability_ids"] == ["BUILDER-018", "BUILDER-040", "BEAST-005", "TRAPPER-015",
                                                 "WARRIOR-020", "WARRIOR-060"]
            and field_loadouts["combo_ids"] == ["COMBO-013", "COMBO-001"]
            and field_loadouts["feedback_id"] == "FB-004", "FIELD_LOADOUTS_SCOPE")
    return_convert = lock["return_convert_followup"]
    require(set(return_convert["rows"]) == set(compose.RETURN_CONVERT_SOURCES)
            and return_convert["ability_ids"] == ["TRAPPER-036", "ZOMBIE-035", "ZOMBIE-040"]
            and return_convert["combo_ids"] == ["COMBO-010", "COMBO-019"]
            and return_convert["tooltip_feedback"] == "FB-004", "RETURN_CONVERT_SCOPE")
    ground_night = lock["ground_night_followup"]
    require(set(ground_night["rows"]) == set(compose.GROUND_NIGHT_SOURCES)
            and ground_night["ability_ids"] == ["MAGE-006", "MAGE-022", "MAGE-058", "MAGE-069", "NINJA-025", "NINJA-060"]
            and ground_night["combo_ids"] == ["COMBO-009"]
            and ground_night["additional_cast_cues"] == 20, "GROUND_NIGHT_SCOPE")
    cover_orders = lock["cover_orders_followup"]
    require(set(cover_orders["rows"]) == set(compose.COVER_ORDERS_SOURCES)
            and cover_orders["ability_ids"] == ["BUILDER-026", "BUILDER-048", "BUILDER-066", "BUILDER-072",
                                               "BEAST-091", "BEAST-092", "BEAST-093"]
            and cover_orders["result_feedback"] == "FB-003", "COVER_ORDERS_SCOPE")
    mage_field_arcs = lock["mage_field_arcs_followup"]
    require(set(mage_field_arcs["rows"]) == set(compose.MAGE_FIELD_ARCS_SOURCES)
            and mage_field_arcs["ability_ids"] == [
                "MAGE-005", "MAGE-009", "MAGE-015", "MAGE-047", "MAGE-073", "MAGE-078",
                "MAGE-079", "MAGE-083", "BEAST-020", "BEAST-095"]
            and mage_field_arcs["combo_ids"] == ["COMBO-017"], "MAGE_FIELD_ARCS_SCOPE")
    eclipse_sweep = lock["eclipse_sweep_followup"]
    require(set(eclipse_sweep["rows"]) == set(compose.ECLIPSE_SWEEP_SOURCES)
            and eclipse_sweep["ability_ids"] == [
                "NINJA-020", "NINJA-028", "TRAPPER-025", "TRAPPER-054", "WARRIOR-001", "WARRIOR-003",
                "WARRIOR-005", "WARRIOR-008", "WARRIOR-015", "WARRIOR-018", "WARRIOR-021", "WARRIOR-027",
                "WARRIOR-091"] and eclipse_sweep["combo_ids"] == ["COMBO-007", "COMBO-011"], "ECLIPSE_SWEEP_SCOPE")
    builder_forms = lock["builder_forms_followup"]
    require(set(builder_forms["rows"]) == set(compose.BUILDER_FORMS_SOURCES)
            and builder_forms["ability_ids"] == [
                "BUILDER-060", "ZOMBIE-001", "ZOMBIE-008", "ZOMBIE-009", "ZOMBIE-072", "ZOMBIE-073", "ZOMBIE-097"]
            and builder_forms["combo_ids"] == ["COMBO-014"]
            and builder_forms["loadout_feedback"] == "FB-004", "BUILDER_FORMS_SCOPE")
    footing_wards = lock["footing_wards_followup"]
    require(set(footing_wards["rows"]) == set(compose.FOOTING_WARDS_SOURCES)
            and footing_wards["ability_ids"] == [
                "COMMON-025", "MAGE-035", "MAGE-042", "MAGE-065", "TRAPPER-040", "TRAPPER-060",
                "ZOMBIE-093", "ZOMBIE-098"]
            and footing_wards["combo_ids"] == ["COMBO-003", "COMBO-006", "COMBO-012"],
            "FOOTING_WARDS_SCOPE")
    ninja_beast_castle = lock["ninja_beast_castle_followup"]
    require(set(ninja_beast_castle["rows"]) == set(compose.NINJA_BEAST_CASTLE_SOURCES)
            and ninja_beast_castle["ability_ids"] == [
                "BEAST-001", "BEAST-007", "BEAST-028", "NINJA-001", "NINJA-002", "NINJA-004",
                "NINJA-005", "NINJA-006", "NINJA-008"]
            and ninja_beast_castle["castle_approach_source"] == "PR-1009",
            "NINJA_BEAST_CASTLE_SCOPE")
    spring_mist_forest = lock["spring_mist_forest_followup"]
    require(set(spring_mist_forest["rows"]) == set(compose.SPRING_MIST_FOREST_SOURCES)
            and spring_mist_forest["ability_ids"] == [
                "BEAST-061", "BEAST-062", "BEAST-067", "BUILDER-025", "BUILDER-075",
                "ZOMBIE-041", "ZOMBIE-044", "ZOMBIE-087"]
            and spring_mist_forest["combo_ids"] == ["COMBO-015"]
            and spring_mist_forest["forest_source"] == "PR-421", "SPRING_MIST_FOREST_SCOPE")
    ninja_steps_objectives = lock["ninja_steps_objectives_followup"]
    require(set(ninja_steps_objectives["rows"]) == set(compose.NINJA_STEPS_OBJECTIVES_SOURCES)
            and ninja_steps_objectives["ability_ids"] == ["NINJA-032", "NINJA-033", "NINJA-034", "NINJA-036"]
            and ninja_steps_objectives["minimap_source"] == "PR-960", "NINJA_STEPS_OBJECTIVES_SCOPE")
    warrior_field_horde = lock["warrior_field_horde_followup"]
    require(set(warrior_field_horde["rows"]) == set(compose.WARRIOR_FIELD_HORDE_SOURCES)
            and warrior_field_horde["ability_ids"] == ['WARRIOR-004', 'WARRIOR-006', 'WARRIOR-009', 'WARRIOR-013', 'WARRIOR-014', 'WARRIOR-017']
            and warrior_field_horde["horde_source"] == "PR-951" and warrior_field_horde["horde_species"] == 8, "WARRIOR_FIELD_HORDE_SCOPE")
    trapper_cast_audio = lock["trapper_cast_audio_followup"]
    require(set(trapper_cast_audio["rows"]) == set(compose.TRAPPER_CAST_AUDIO_SOURCES)
            and trapper_cast_audio["ability_ids"] == ['TRAPPER-001', 'TRAPPER-003', 'TRAPPER-004', 'TRAPPER-007', 'TRAPPER-008', 'TRAPPER-009']
            and trapper_cast_audio["additional_cast_cues"] == 18, "TRAPPER_CAST_AUDIO_SCOPE")
    zombie_formation_camera = lock["zombie_formation_camera_followup"]
    require(set(zombie_formation_camera["rows"]) == set(compose.ZOMBIE_FORMATION_CAMERA_SOURCES)
            and zombie_formation_camera["ability_ids"] == ['ZOMBIE-020']
            and zombie_formation_camera["combo_ids"] == ["COMBO-020"] and zombie_formation_camera["camera_source"] == "PR-981", "ZOMBIE_FORMATION_CAMERA_SCOPE")
    expected_zombie_formation_camera_off, zombie_formation_camera_off_lock, zombie_formation_camera_off = verify_source_rollback(
        root, root, lock, current, zombie_formation_camera, zombie_formation_camera["rows"], trapper_cast_audio["repaired_place"],
        compose.ZOMBIE_FORMATION_CAMERA_OFF, compose.ZOMBIE_FORMATION_CAMERA_OFF_ARCHIVE, "ZOMBIE_FORMATION_CAMERA")
    expected_trapper_cast_audio_off, trapper_cast_audio_off_lock, trapper_cast_audio_off = verify_source_rollback(
        root, root / compose.ZOMBIE_FORMATION_CAMERA_OFF, zombie_formation_camera_off_lock, zombie_formation_camera_off,
        trapper_cast_audio, trapper_cast_audio["rows"], warrior_field_horde["repaired_place"],
        compose.TRAPPER_CAST_AUDIO_OFF, compose.TRAPPER_CAST_AUDIO_OFF_ARCHIVE, "TRAPPER_CAST_AUDIO")
    expected_warrior_field_horde_off, warrior_field_horde_off_lock, warrior_field_horde_off = verify_source_rollback(
        root, root / compose.TRAPPER_CAST_AUDIO_OFF, trapper_cast_audio_off_lock, trapper_cast_audio_off,
        warrior_field_horde, warrior_field_horde["rows"], ninja_steps_objectives["repaired_place"],
        compose.WARRIOR_FIELD_HORDE_OFF, compose.WARRIOR_FIELD_HORDE_OFF_ARCHIVE, "WARRIOR_FIELD_HORDE")
    expected_ninja_steps_objectives_off, ninja_steps_objectives_off_lock, ninja_steps_objectives_off = verify_source_rollback(
        root, root / compose.WARRIOR_FIELD_HORDE_OFF, warrior_field_horde_off_lock, warrior_field_horde_off,
        ninja_steps_objectives, ninja_steps_objectives["rows"], spring_mist_forest["repaired_place"],
        compose.NINJA_STEPS_OBJECTIVES_OFF, compose.NINJA_STEPS_OBJECTIVES_OFF_ARCHIVE, "NINJA_STEPS_OBJECTIVES")
    expected_spring_mist_forest_off, spring_mist_forest_off_lock, spring_mist_forest_off = verify_source_rollback(
        root, root / compose.NINJA_STEPS_OBJECTIVES_OFF, ninja_steps_objectives_off_lock, ninja_steps_objectives_off,
        spring_mist_forest, spring_mist_forest["rows"],
        ninja_beast_castle["repaired_place"], compose.SPRING_MIST_FOREST_OFF,
        compose.SPRING_MIST_FOREST_OFF_ARCHIVE, "SPRING_MIST_FOREST")
    expected_ninja_beast_castle_off, ninja_beast_castle_off_lock, ninja_beast_castle_off = verify_source_rollback(
        root, root / compose.SPRING_MIST_FOREST_OFF, spring_mist_forest_off_lock, spring_mist_forest_off,
        ninja_beast_castle, ninja_beast_castle["rows"],
        footing_wards["repaired_place"], compose.NINJA_BEAST_CASTLE_OFF,
        compose.NINJA_BEAST_CASTLE_OFF_ARCHIVE, "NINJA_BEAST_CASTLE")
    expected_footing_wards_off, footing_wards_off_lock, footing_wards_off = verify_source_rollback(
        root, root / compose.NINJA_BEAST_CASTLE_OFF, ninja_beast_castle_off_lock, ninja_beast_castle_off,
        footing_wards, footing_wards["rows"], builder_forms["repaired_place"],
        compose.FOOTING_WARDS_OFF, compose.FOOTING_WARDS_OFF_ARCHIVE, "FOOTING_WARDS")
    expected_builder_forms_off, builder_forms_off_lock, builder_forms_off = verify_source_rollback(
        root, root / compose.FOOTING_WARDS_OFF, footing_wards_off_lock, footing_wards_off,
        builder_forms, builder_forms["rows"], eclipse_sweep["repaired_place"],
        compose.BUILDER_FORMS_OFF, compose.BUILDER_FORMS_OFF_ARCHIVE, "BUILDER_FORMS")
    expected_eclipse_sweep_off, eclipse_sweep_off_lock, eclipse_sweep_off = verify_source_rollback(
        root, root / compose.BUILDER_FORMS_OFF, builder_forms_off_lock, builder_forms_off,
        eclipse_sweep, eclipse_sweep["rows"], mage_field_arcs["repaired_place"],
        compose.ECLIPSE_SWEEP_OFF, compose.ECLIPSE_SWEEP_OFF_ARCHIVE, "ECLIPSE_SWEEP")
    expected_mage_field_arcs_off, mage_field_arcs_off_lock, mage_field_arcs_off = verify_source_rollback(
        root, root / compose.ECLIPSE_SWEEP_OFF, eclipse_sweep_off_lock, eclipse_sweep_off,
        mage_field_arcs, mage_field_arcs["rows"], cover_orders["repaired_place"],
        compose.MAGE_FIELD_ARCS_OFF, compose.MAGE_FIELD_ARCS_OFF_ARCHIVE, "MAGE_FIELD_ARCS")
    expected_cover_orders_off, cover_orders_off_lock, cover_orders_off = verify_source_rollback(
        root, root / compose.MAGE_FIELD_ARCS_OFF, mage_field_arcs_off_lock, mage_field_arcs_off,
        cover_orders, cover_orders["rows"], ground_night["repaired_place"],
        compose.COVER_ORDERS_OFF, compose.COVER_ORDERS_OFF_ARCHIVE, "COVER_ORDERS")
    expected_ground_night_off, ground_night_off_lock, ground_night_off = verify_source_rollback(
        root, root / compose.COVER_ORDERS_OFF, cover_orders_off_lock, cover_orders_off,
        ground_night, ground_night["rows"], return_convert["repaired_place"],
        compose.GROUND_NIGHT_OFF, compose.GROUND_NIGHT_OFF_ARCHIVE, "GROUND_NIGHT")
    expected_return_convert_off, return_convert_off_lock, return_convert_off = verify_source_rollback(
        root, root / compose.GROUND_NIGHT_OFF, ground_night_off_lock, ground_night_off,
        return_convert, return_convert["rows"], field_loadouts["repaired_place"],
        compose.RETURN_CONVERT_OFF, compose.RETURN_CONVERT_OFF_ARCHIVE, "RETURN_CONVERT")
    expected_field_loadouts_off, field_loadouts_off_lock, field_loadouts_off = verify_source_rollback(
        root, root / compose.RETURN_CONVERT_OFF, return_convert_off_lock, return_convert_off,
        field_loadouts, field_loadouts["rows"], wing_warrior["repaired_place"],
        compose.FIELD_LOADOUTS_OFF, compose.FIELD_LOADOUTS_OFF_ARCHIVE, "FIELD_LOADOUTS")
    expected_wing_warrior_off, wing_warrior_off_lock, wing_warrior_off = verify_source_rollback(
        root, root / compose.FIELD_LOADOUTS_OFF, field_loadouts_off_lock, field_loadouts_off,
        wing_warrior, wing_warrior["rows"], ninja_s4["repaired_place"],
        compose.WING_WARRIOR_OFF, compose.WING_WARRIOR_OFF_ARCHIVE, "WING_WARRIOR")
    expected_ninja_s4_off, ninja_s4_off_lock, ninja_s4_off = verify_source_rollback(
        root, root / compose.WING_WARRIOR_OFF, wing_warrior_off_lock, wing_warrior_off,
        ninja_s4, ninja_s4["rows"], water_chain["repaired_place"],
        compose.NINJA_S4_OFF, compose.NINJA_S4_OFF_ARCHIVE, "NINJA_S4")
    expected_water_chain_off, water_chain_off_lock, water_chain_off = verify_source_rollback(
        root, root / compose.NINJA_S4_OFF, ninja_s4_off_lock, ninja_s4_off,
        water_chain, water_chain["rows"], projectiles["repaired_place"],
        compose.MAGE_WATER_CHAIN_OFF, compose.MAGE_WATER_CHAIN_OFF_ARCHIVE, "MAGE_WATER_CHAIN")
    expected_projectile_off, projectile_off_lock, projectile_off = verify_source_rollback(
        root, root / compose.MAGE_WATER_CHAIN_OFF, water_chain_off_lock, water_chain_off,
        projectiles, projectiles["rows"], hp["repaired_place"],
        compose.MAGE_PROJECTILES_OFF, compose.MAGE_PROJECTILES_OFF_ARCHIVE, "MAGE_PROJECTILES")
    team_win = lock["team_win_rule_followup"]
    expected_hp_off, hp_off_lock, hp_off = verify_source_rollback(
        root, root / compose.MAGE_PROJECTILES_OFF, projectile_off_lock, projectile_off,
        hp, hp["rows"], team_win["repaired_place"],
        compose.FRACTIONAL_HP_OFF, compose.FRACTIONAL_HP_OFF_ARCHIVE, "FRACTIONAL_HP")
    require(set(team_win["rows"]) == {compose.VAULT_SOURCE}
            and team_win["feedback"] == {"id": "FB-003", "issue": 364, "queue": "TEAM"}, "TEAM_WIN_RULE_SCOPE")
    team_row = team_win["rows"][compose.VAULT_SOURCE]
    require(len(team_row["forward"]) == len(team_row["inverse"]) == 1, "TEAM_WIN_RULE_SINGLE_HUNK")
    expected_team_win_off, team_win_off_lock, team_win_off = verify_source_rollback(
        root, root / compose.FRACTIONAL_HP_OFF, hp_off_lock, hp_off,
        team_win, team_win["rows"], shorefoam["repaired_place"],
        compose.TEAM_WIN_RULE_OFF, compose.TEAM_WIN_RULE_OFF_ARCHIVE, "TEAM_WIN_RULE")
    require(set(shorefoam["rows"]) == {compose.SHOREFOAM_SOURCE}, "SHOREFOAM_SOURCE_SET")
    expected_shorefoam_off, shorefoam_off_lock, shorefoam_off = verify_source_rollback(
        root, root / compose.TEAM_WIN_RULE_OFF, team_win_off_lock, team_win_off,
        shorefoam, shorefoam["rows"], portrait["repaired_place"],
        compose.SHOREFOAM_OFF, compose.SHOREFOAM_OFF_ARCHIVE, "SHOREFOAM")
    author = shorefoam["author"]
    transform = visual_author(author["path"], author["identity"], "SHOREFOAM_EXACT_AUTHOR")
    old_traversal = read(root / compose.SHOREFOAM_OFF / "sources" / compose.SHOREFOAM_SOURCE)
    require(transform.patch(old_traversal.decode("utf-8")).encode("utf-8")
            == read(root / "sources" / compose.SHOREFOAM_SOURCE), "SHOREFOAM_AUTHOR_TRANSFORM_DRIFT")
    require(set(portrait["rows"]) == {compose.PORTRAIT_SOURCE}, "PORTRAIT_SOURCE_SET")
    expected_portrait_off, portrait_off_lock, portrait_off = verify_source_rollback(
        root, root / compose.SHOREFOAM_OFF, shorefoam_off_lock, shorefoam_off,
        portrait, portrait["rows"], private_touch["repaired_place"],
        compose.PORTRAIT_OFF, compose.PORTRAIT_OFF_ARCHIVE, "PORTRAIT")
    author = portrait["author"]
    transform = visual_author(author["path"], author["identity"], "PORTRAIT_EXACT_AUTHOR")
    old_policy = read(root / compose.PORTRAIT_OFF / "sources" / compose.PORTRAIT_SOURCE)
    require(transform.patch_module(old_policy.decode("utf-8")).encode("utf-8")
            == read(root / "sources" / compose.PORTRAIT_SOURCE), "PORTRAIT_AUTHOR_TRANSFORM_DRIFT")
    require(set(private_touch["rows"]) == {compose.PRIVATE_TOUCH_SOURCE}, "PRIVATE_TOUCH_SOURCE_SET")
    expected_touch_off, touch_off_lock, touch_off = verify_source_rollback(
        root, root / compose.PORTRAIT_OFF, portrait_off_lock, portrait_off,
        private_touch, private_touch["rows"], moguron["repaired_place"],
        compose.PRIVATE_TOUCH_OFF, compose.PRIVATE_TOUCH_OFF_ARCHIVE, "PRIVATE_TOUCH")
    verify_exact_author_patch(root, compose.PRIVATE_TOUCH_OFF, (compose.PRIVATE_TOUCH_SOURCE,),
                              private_touch["author_patch"], "PRIVATE_TOUCH", ("--directory=sources",),
                              result_stage=compose.PORTRAIT_OFF)
    require(set(moguron["rows"]) == {compose.MOGURON_SOURCE}, "MOGURON_SOURCE_SET")
    expected_moguron_off, moguron_off_lock, moguron_off = verify_source_rollback(
        root, root / compose.PRIVATE_TOUCH_OFF, touch_off_lock, touch_off, moguron, moguron["rows"],
        eligibility["repaired_place"],
        compose.MOGURON_OFF, compose.MOGURON_OFF_ARCHIVE, "MOGURON")
    verify_exact_author_patch(root, compose.MOGURON_OFF, (compose.MOGURON_SOURCE,),
                              moguron["author_patch"], "MOGURON", ("--directory=sources",),
                              result_stage=compose.PRIVATE_TOUCH_OFF)
    require(set(eligibility["rows"]) == set(compose.RELAY_ELIGIBILITY_SOURCES), "RELAY_ELIGIBILITY_SOURCE_SET")
    expected_eligibility_off, eligibility_off_lock, eligibility_off = verify_source_rollback(
        root, root / compose.MOGURON_OFF, moguron_off_lock, moguron_off, eligibility, eligibility["rows"],
        mage["repaired_place"],
        compose.RELAY_ELIGIBILITY_OFF, compose.RELAY_ELIGIBILITY_OFF_ARCHIVE, "RELAY_ELIGIBILITY")
    verify_exact_author_patch(root, compose.RELAY_ELIGIBILITY_OFF, compose.RELAY_ELIGIBILITY_SOURCES,
                              eligibility["author_patch"], "RELAY_ELIGIBILITY",
                              result_stage=compose.MOGURON_OFF)
    require(set(mage["rows"]) == set(compose.MAGE_CONTACT_SOURCES), "MAGE_CONTACT_SOURCE_SET")
    expected_mage_off, mage_off_lock, mage_off = verify_source_rollback(
        root, root / compose.RELAY_ELIGIBILITY_OFF, eligibility_off_lock, eligibility_off,
        mage, mage["rows"], art_polish["repaired_place"],
        compose.MAGE_CONTACT_OFF, compose.MAGE_CONTACT_OFF_ARCHIVE, "MAGE_CONTACT")
    verify_exact_author_patch(root, compose.MAGE_CONTACT_OFF, compose.MAGE_CONTACT_SOURCES,
                              mage["author_patch"], "MAGE_CONTACT", ("--directory=sources",),
                              result_stage=compose.RELAY_ELIGIBILITY_OFF)
    require(set(art_polish["rows"]) == set(compose.ART_POLISH_SOURCES), "ART_POLISH_SOURCE_SET")
    expected_art_off, art_off_lock, art_off = verify_source_rollback(
        root, root / compose.MAGE_CONTACT_OFF, mage_off_lock, mage_off, art_polish, art_polish["rows"], growth["repaired_place"],
        compose.ART_POLISH_OFF, compose.ART_POLISH_OFF_ARCHIVE, "ART_POLISH")
    verify_art_polish_donors(root, art_polish)
    require(set(growth["rows"]) == set(compose.GROWTH_MUSOU_SOURCES), "GROWTH_MUSOU_SOURCE_SET")
    expected_growth_off, growth_off_lock, growth_off = verify_source_rollback(
        root, root / compose.ART_POLISH_OFF, art_off_lock, art_off,
        growth, growth["rows"], combat["repaired_place"],
        compose.GROWTH_MUSOU_OFF, compose.GROWTH_MUSOU_OFF_ARCHIVE, "GROWTH_MUSOU")
    verify_growth_donor_sources(root, growth)
    require(set(combat["rows"]) == set(compose.COMBAT_VISUAL_SOURCES)
            and set(combat["origins"]) == set(combat["rows"]), "COMBAT_VISUAL_SOURCE_SET")
    expected_combat_off, combat_off_lock, combat_off = verify_source_rollback(
        root, root / compose.GROWTH_MUSOU_OFF, growth_off_lock, growth_off,
        combat, combat["rows"], wall["repaired_place"],
        compose.COMBAT_VISUAL_OFF, compose.COMBAT_VISUAL_OFF_ARCHIVE, "COMBAT_VISUAL")
    for source, origin in combat["origins"].items():
        author = visual_author(origin["path"], origin["python_bytes"], "COMBAT_VISUAL_ORIGINAL")
        old = read(root / compose.COMBAT_VISUAL_OFF / "sources" / source)
        selected = getattr(author, origin["apply"])(old.decode()).encode()
        if origin["pr"] == 928:
            fade = combat["ko_fade"]
            transform = visual_author(fade["path"], fade["identity"], "COMBAT_VISUAL_KO_FADE")
            capped = author.apply_owner_live_cap(selected)
            selected = transform.transform(capped)
            require(transform.inverse(selected) == capped, "COMBAT_VISUAL_KO_FADE_INVERSE")
        require(selected == read(root / "sources" / source), "COMBAT_VISUAL_EXACT_AUTHOR_TRANSFORM:" + source)
    require(set(wall["rows"]) == {compose.GUARDIAN_SOURCE}, "GUARDIAN_WALL_SOURCE_SET")
    expected_wall_off, wall_off_lock, wall_off = verify_source_rollback(
        root, root / compose.COMBAT_VISUAL_OFF, combat_off_lock, combat_off,
        wall, wall["rows"], neutral_names["repaired_place"],
        compose.GUARDIAN_WALL_OFF, compose.GUARDIAN_WALL_OFF_ARCHIVE, "GUARDIAN_WALL")
    require(set(neutral_names["rows"]) == set(compose.VISUAL_READABILITY_SOURCES), "VISUAL_READABILITY_SOURCE_SET")
    expected_neutral_off, neutral_off_lock, neutral_off = verify_source_rollback(
        root, root / compose.GUARDIAN_WALL_OFF, wall_off_lock, wall_off,
        neutral_names, neutral_names["rows"], field_prompt["repaired_place"],
        compose.NEUTRAL_NAMES_OFF, compose.NEUTRAL_NAMES_OFF_ARCHIVE, "NEUTRAL_NAMES")
    selected = compose.SWARM_SOURCE
    expected_swarm = neutral_names_author(lock).patch(read(root / compose.NEUTRAL_NAMES_OFF / "sources" / selected))
    require(expected_swarm == read(root / compose.GUARDIAN_WALL_OFF / "sources" / selected),
            "NEUTRAL_NAMES_EXACT_AUTHOR_TRANSFORM")
    plaza = neutral_names["plaza"]
    plaza_author = visual_author(plaza["author_file"], plaza["author_transform"], "LOBBY_PLAZA_AUTHOR")
    selected = compose.LOBBY_SOCIAL_SOURCE
    expected_plaza = plaza_author.transform(read(root / compose.NEUTRAL_NAMES_OFF / "sources" / selected).decode())
    require(expected_plaza.encode() == read(root / "sources" / selected), "LOBBY_PLAZA_EXACT_AUTHOR_TRANSFORM")
    require(set(field_prompt["rows"]) == {compose.VAULT_SOURCE}, "FIELD_PROMPT_SOURCE_SET")
    expected_field_off, field_off_lock, field_off = verify_source_rollback(
        root, root / compose.NEUTRAL_NAMES_OFF, neutral_off_lock, neutral_off,
        field_prompt, field_prompt["rows"], role["repaired_place"],
        compose.FIELD_PROMPT_OFF, compose.FIELD_PROMPT_OFF_ARCHIVE, "FIELD_PROMPT")
    require(set(role["rows"]) == set(compose.ROLE_READABILITY_SOURCES), "ROLE_READABILITY_SOURCE_SET")
    expected_role_off, role_off_lock, role_off = verify_source_rollback(
        root, root / compose.FIELD_PROMPT_OFF, field_off_lock, field_off, role, role["rows"], canyon["repaired_place"],
        compose.ROLE_READABILITY_OFF, compose.ROLE_READABILITY_OFF_ARCHIVE, "ROLE_READABILITY")
    require(set(canyon["rows"]) == set(compose.BR_CANYON_SOURCES), "BR_CANYON_SOURCE_SET")
    expected_canyon_off, canyon_off_lock, canyon_off = verify_source_rollback(
        root, root / compose.ROLE_READABILITY_OFF, role_off_lock, role_off, canyon, canyon["rows"], relay["repaired_place"],
        compose.BR_CANYON_OFF, compose.BR_CANYON_OFF_ARCHIVE, "BR_CANYON")
    require(set(relay["rows"]) == set(compose.RELAY_PRESENTATION_SOURCES), "RELAY_PRESENTATION_SOURCE_SET")
    expected_relay_off, relay_off_lock, relay_off = verify_source_rollback(
        root, root / compose.BR_CANYON_OFF, canyon_off_lock, canyon_off, relay, relay["rows"], score["repaired_place"],
        compose.RELAY_PRESENTATION_OFF, compose.RELAY_PRESENTATION_OFF_ARCHIVE, "RELAY_PRESENTATION")
    expected_score_off, score_off_lock, score_off = verify_single_source_rollback(
        root, root / compose.RELAY_PRESENTATION_OFF, relay_off_lock, relay_off, compose.SCORE_SOURCE, score,
        score["parent_score_row"], castle["repaired_place"],
        compose.SCORE_OFF, compose.SCORE_OFF_ARCHIVE, "SCORE_RELAY")
    expected_castle_off, castle_off_lock, castle_off = verify_single_source_rollback(
        root, root / compose.SCORE_OFF, score_off_lock, score_off, compose.VAULT_SOURCE, castle,
        castle["parent_host_row"], vault["repaired_place"],
        compose.CASTLE_OFF, compose.CASTLE_OFF_ARCHIVE, "CASTLE_RELEASE_STOCK")
    expected_vault_off, vault_off_lock, vault_off = verify_single_source_rollback(
        root, root / compose.CASTLE_OFF, castle_off_lock, castle_off, compose.VAULT_SOURCE, vault,
        vault["parent_host_row"], item["repaired_place"],
        compose.VAULT_OFF, compose.VAULT_OFF_ARCHIVE, "EMPTY_VAULT")
    expected_item_off, item_off_lock, item_off = verify_single_source_rollback(
        root, root / compose.VAULT_OFF, vault_off_lock, vault_off, compose.ITEM_SOURCE, item, item["parent_item_row"],
        lock["guardian_followup_repair"]["repaired_place"], compose.ITEM_OFF, compose.ITEM_OFF_ARCHIVE, "ITEM_CLEANUP")
    expected_guardian_off, guardian_off_lock, guardian_off = verify_guardian_parent_rollback(
        root, item_off_lock, item_off, root / compose.ITEM_OFF)
    expected_beast_off, h72_lock, h72 = verify_beast_parent_rollback(
        root, guardian_off_lock, guardian_off, root / compose.GUARDIAN_OFF)
    expected_bot_off = verify_bot_parent_rollback(root, h72_lock, h72)
    expected_hud_off = verify_hud_current_rollback(root, h72_lock, h72)
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
        "selected_source_count": 69, "changed_source_count": 37, "unchanged_source_count": 32,
        "source_hashes": {r: v["sha256"] for r, v in current["sources"].items()},
        "source_classes": {r: v["class"] for r, v in current["sources"].items()},
        "private_place_bytes": lock["final_place"]["bytes"], "private_place_sha256": lock["final_place"]["sha256"],
        "prior_place": lock["prior_place"], "prior_receipt": digest(inputs["receipt_raw"]),
        "profile_lock": digest(read(HERE / "profile_lock.json")), "prior_evidence": expected_prior,
        "runtime_rollback_archive": digest(read(root / compose.OFF_ARCHIVE)),
        "followup_repair": lock["followup_repair"],
        "hud_only_current_rc_rollback_archive": digest(read(root / compose.HUD_OFF_ARCHIVE)),
        "bot_followup_repair": lock["bot_followup_repair"],
        "bot_only_hud_parent_rollback_archive": digest(read(root / compose.BOT_OFF_ARCHIVE)),
        "beast_followup_repair": lock["beast_followup_repair"],
        "beast_only_h72_parent_rollback_archive": digest(read(root / compose.BEAST_OFF_ARCHIVE)),
        "guardian_followup_repair": lock["guardian_followup_repair"],
        "guardian_only_beast_parent_rollback_archive": digest(read(root / compose.GUARDIAN_OFF_ARCHIVE)),
        "item_cleanup_followup": lock["item_cleanup_followup"],
        "item_cleanup_only_rollback_archive": digest(read(root / compose.ITEM_OFF_ARCHIVE)),
        "empty_vault_followup": vault,
        "empty_vault_only_rollback_archive": digest(read(root / compose.VAULT_OFF_ARCHIVE)),
        "castle_release_stock_followup": castle,
        "castle_release_stock_rollback_archive": digest(read(root / compose.CASTLE_OFF_ARCHIVE)),
        "score_relay_followup": score,
        "score_relay_rollback_archive": digest(read(root / compose.SCORE_OFF_ARCHIVE)),
        "relay_presentation_followup": relay,
        "relay_presentation_rollback_archive": digest(read(root / compose.RELAY_PRESENTATION_OFF_ARCHIVE)),
        "br_canyon_followup": canyon,
        "br_canyon_rollback_archive": digest(read(root / compose.BR_CANYON_OFF_ARCHIVE)),
        "role_readability_followup": role,
        "role_readability_rollback_archive": digest(read(root / compose.ROLE_READABILITY_OFF_ARCHIVE)),
        "field_prompt_followup": field_prompt,
        "field_prompt_rollback_archive": digest(read(root / compose.FIELD_PROMPT_OFF_ARCHIVE)),
        "neutral_names_followup": neutral_names,
        "neutral_names_rollback_archive": digest(read(root / compose.NEUTRAL_NAMES_OFF_ARCHIVE)),
        "guardian_wall_followup": wall,
        "guardian_wall_rollback_archive": digest(read(root / compose.GUARDIAN_WALL_OFF_ARCHIVE)),
        "combat_visual_followup": combat,
        "combat_visual_rollback_archive": digest(read(root / compose.COMBAT_VISUAL_OFF_ARCHIVE)),
        "growth_musou_followup": growth,
        "growth_musou_rollback_archive": digest(read(root / compose.GROWTH_MUSOU_OFF_ARCHIVE)),
        "art_polish_followup": art_polish,
        "art_polish_rollback_archive": digest(read(root / compose.ART_POLISH_OFF_ARCHIVE)),
        "mage_contact_followup": mage,
        "mage_contact_rollback_archive": digest(read(root / compose.MAGE_CONTACT_OFF_ARCHIVE)),
        "relay_eligibility_followup": eligibility,
        "relay_eligibility_rollback_archive": digest(read(root / compose.RELAY_ELIGIBILITY_OFF_ARCHIVE)),
        "moguron_followup": moguron,
        "moguron_rollback_archive": digest(read(root / compose.MOGURON_OFF_ARCHIVE)),
        "private_touch_followup": private_touch,
        "private_touch_rollback_archive": digest(read(root / compose.PRIVATE_TOUCH_OFF_ARCHIVE)),
        "portrait_followup": portrait,
        "portrait_rollback_archive": digest(read(root / compose.PORTRAIT_OFF_ARCHIVE)),
        "shorefoam_followup": shorefoam,
        "shorefoam_rollback_archive": digest(read(root / compose.SHOREFOAM_OFF_ARCHIVE)),
        "team_win_rule_followup": team_win,
        "team_win_rule_rollback_archive": digest(read(root / compose.TEAM_WIN_RULE_OFF_ARCHIVE)),
        "fractional_hp_followup": hp,
        "fractional_hp_rollback_archive": digest(read(root / compose.FRACTIONAL_HP_OFF_ARCHIVE)),
        "mage_projectile_followup": projectiles,
        "mage_projectile_rollback_archive": digest(read(root / compose.MAGE_PROJECTILES_OFF_ARCHIVE)),
        "mage_water_chain_followup": water_chain,
        "mage_water_chain_rollback_archive": digest(read(root / compose.MAGE_WATER_CHAIN_OFF_ARCHIVE)),
        "ninja_s4_followup": ninja_s4,
        "ninja_s4_rollback_archive": digest(read(root / compose.NINJA_S4_OFF_ARCHIVE)),
        "wing_warrior_followup": wing_warrior,
        "wing_warrior_rollback_archive": digest(read(root / compose.WING_WARRIOR_OFF_ARCHIVE)),
        "field_loadouts_followup": field_loadouts,
        "field_loadouts_rollback_archive": digest(read(root / compose.FIELD_LOADOUTS_OFF_ARCHIVE)),
        "return_convert_followup": return_convert,
        "return_convert_rollback_archive": digest(read(root / compose.RETURN_CONVERT_OFF_ARCHIVE)),
        "ground_night_followup": ground_night,
        "ground_night_rollback_archive": digest(read(root / compose.GROUND_NIGHT_OFF_ARCHIVE)),
        "cover_orders_followup": cover_orders,
        "cover_orders_rollback_archive": digest(read(root / compose.COVER_ORDERS_OFF_ARCHIVE)),
        "mage_field_arcs_followup": mage_field_arcs,
        "mage_field_arcs_rollback_archive": digest(read(root / compose.MAGE_FIELD_ARCS_OFF_ARCHIVE)),
        "eclipse_sweep_followup": eclipse_sweep,
        "eclipse_sweep_rollback_archive": digest(read(root / compose.ECLIPSE_SWEEP_OFF_ARCHIVE)),
        "builder_forms_followup": builder_forms,
        "builder_forms_rollback_archive": digest(read(root / compose.BUILDER_FORMS_OFF_ARCHIVE)),
        "footing_wards_followup": footing_wards,
        "footing_wards_rollback_archive": digest(read(root / compose.FOOTING_WARDS_OFF_ARCHIVE)),
        "ninja_beast_castle_followup": ninja_beast_castle,
        "ninja_beast_castle_rollback_archive": digest(read(root / compose.NINJA_BEAST_CASTLE_OFF_ARCHIVE)),
        "spring_mist_forest_followup": spring_mist_forest,
        "spring_mist_forest_rollback_archive": digest(read(root / compose.SPRING_MIST_FOREST_OFF_ARCHIVE)),
        "ninja_steps_objectives_followup": ninja_steps_objectives,
        "ninja_steps_objectives_rollback_archive": digest(read(root / compose.NINJA_STEPS_OBJECTIVES_OFF_ARCHIVE)),
        "warrior_field_horde_followup": warrior_field_horde,
        "warrior_field_horde_rollback_archive": digest(read(root / compose.WARRIOR_FIELD_HORDE_OFF_ARCHIVE)),
        "trapper_cast_audio_followup": trapper_cast_audio,
        "trapper_cast_audio_rollback_archive": digest(read(root / compose.TRAPPER_CAST_AUDIO_OFF_ARCHIVE)),
        "zombie_formation_camera_followup": zombie_formation_camera,
        "zombie_formation_camera_rollback_archive": digest(read(root / compose.ZOMBIE_FORMATION_CAMERA_OFF_ARCHIVE)),
        "legacy_48_all_ported": False, "owner_accepted": False, "art_gate": "ART_NO_GO",
        "product_gate": "PRODUCT_NO_GO", "studio_solo": "NOT_TESTED", "studio_two_client": "NOT_TESTED",
        "android_15min": "NOT_TESTED", "fun": "NOT_TESTED", "roblox_publish": False, "paid_trade": False,
        "identity_receipt_is_not_final_delivery_admission": True, **lock["runtime_labels"],
    }
    require(receipt == expected, "FINAL_RECEIPT_FIELD_SET_OR_FACTS")
    core = data(root / "CORE_BUILD_REPORT.json")
    expected_reuse = {name: row["before"] for name, row in lock["sources"].items()
                      if row["before"] == row["after"]}
    require(core.get("compile_reuse_prior_br") == expected_reuse,
            "CORE_COMPILE_REUSE_PRIOR_BR_SET")
    require(all(read(root / "sources" / name) == read(root / compose.OFF / "sources" / name)
                for name in expected_reuse), "CORE_COMPILE_REUSE_PRIOR_BR_BYTES")
    require(core.get("status") == "PASS_SOURCE_BUILD_ONLY" and core.get("final_delivery_created") is False
            and core.get("context") == context and core.get("source_count") == 69
            and core.get("changed_sources") == 37 and core.get("unchanged_sources") == 32
            and type(core.get("compile_count")) is int and type(core.get("rojo_build_count")) is int
            and core.get("item_cleanup_only_parent_place") == item_off_lock["final_place"]
            and core.get("empty_vault_only_parent_place") == vault_off_lock["final_place"]
            and core.get("castle_release_stock_parent_place") == castle_off_lock["final_place"]
            and core.get("score_relay_parent_place") == score_off_lock["final_place"]
            and core.get("relay_presentation_parent_place") == relay_off_lock["final_place"]
            and core.get("br_canyon_parent_place") == canyon_off_lock["final_place"]
            and core.get("role_readability_parent_place") == role_off_lock["final_place"]
            and core.get("field_prompt_parent_place") == field_off_lock["final_place"]
            and core.get("neutral_names_parent_place") == neutral_off_lock["final_place"]
            and core.get("guardian_wall_parent_place") == wall_off_lock["final_place"]
            and core.get("combat_visual_parent_place") == combat_off_lock["final_place"]
            and core.get("growth_musou_parent_place") == growth_off_lock["final_place"]
            and core.get("art_polish_parent_place") == art_off_lock["final_place"]
            and core.get("mage_contact_parent_place") == mage_off_lock["final_place"]
            and core.get("relay_eligibility_parent_place") == eligibility_off_lock["final_place"]
            and core.get("private_touch_parent_place") == touch_off_lock["final_place"]
            and core.get("portrait_parent_place") == portrait_off_lock["final_place"]
            and core.get("shorefoam_parent_place") == shorefoam_off_lock["final_place"]
            and core.get("team_win_rule_parent_place") == team_win_off_lock["final_place"]
            and core.get("fractional_hp_parent_place") == hp_off_lock["final_place"]
            and core.get("mage_projectile_parent_place") == projectile_off_lock["final_place"]
            and core.get("mage_water_chain_parent_place") == water_chain_off_lock["final_place"]
            and core.get("ninja_s4_parent_place") == ninja_s4_off_lock["final_place"]
            and core.get("wing_warrior_parent_place") == wing_warrior_off_lock["final_place"]
            and core.get("field_loadouts_parent_place") == field_loadouts_off_lock["final_place"]
            and core.get("return_convert_parent_place") == return_convert_off_lock["final_place"]
            and core.get("ground_night_parent_place") == ground_night_off_lock["final_place"]
            and core.get("cover_orders_parent_place") == cover_orders_off_lock["final_place"]
            and core.get("mage_field_arcs_parent_place") == mage_field_arcs_off_lock["final_place"]
            and core.get("eclipse_sweep_parent_place") == eclipse_sweep_off_lock["final_place"]
            and core.get("builder_forms_parent_place") == builder_forms_off_lock["final_place"]
            and core.get("footing_wards_parent_place") == footing_wards_off_lock["final_place"]
            and core.get("ninja_beast_castle_parent_place") == ninja_beast_castle_off_lock["final_place"]
            and core.get("spring_mist_forest_parent_place") == spring_mist_forest_off_lock["final_place"]
            and core.get("ninja_steps_objectives_parent_place") == ninja_steps_objectives_off_lock["final_place"]
            and core.get("warrior_field_horde_parent_place") == warrior_field_horde_off_lock["final_place"]
            and core.get("trapper_cast_audio_parent_place") == trapper_cast_audio_off_lock["final_place"]
            and core.get("zombie_formation_camera_parent_place") == zombie_formation_camera_off_lock["final_place"]
            and core.get("guardian_only_compile_count") == 1 and core.get("guardian_only_rojo_build_count") == 1
            and core.get("guardian_only_beast_parent_place") == guardian_off_lock["final_place"]
            and core.get("changed_sources_from_beast_parent") == 1
            and core.get("unchanged_sources_from_beast_parent") == 68
            and core.get("beast_only_compile_count") == 1 and core.get("beast_only_rojo_build_count") == 1
            and core.get("beast_only_h72_parent_place") == h72_lock["final_place"]
            and core.get("changed_sources_from_h72_parent") == 1 and core.get("unchanged_sources_from_h72_parent") == 68
            and core.get("historical_on_br_compile_count") == 2 * len(lock["sources"]) - len(expected_reuse)
            and core.get("historical_on_br_rojo_build_count") == 2
            and core.get("hud_only_compile_count") == 1 and core.get("hud_only_rojo_build_count") == 1
            and core.get("hud_only_off_place") == lock["followup_repair"]["current_place"]
            and core.get("hud_stage_changed_sources_from_current_rc") == 1
            and core.get("hud_stage_unchanged_sources_from_current_rc") == 68
            and core.get("bot_only_compile_count") == 1 and core.get("bot_only_rojo_build_count") == 1
            and core.get("bot_only_parent_place") == lock["bot_followup_repair"]["parent_place"]
            and core.get("changed_sources_from_hud_parent") == 1 and core.get("unchanged_sources_from_hud_parent") == 68
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
    expected_stage.update({compose.BOT_OFF + "/" + name: pin for name, pin in expected_bot_off.items()})
    expected_stage[compose.BOT_OFF_ARCHIVE] = digest(read(root / compose.BOT_OFF_ARCHIVE))
    expected_stage.update({compose.BEAST_OFF + "/" + name: pin for name, pin in expected_beast_off.items()})
    expected_stage[compose.BEAST_OFF_ARCHIVE] = digest(read(root / compose.BEAST_OFF_ARCHIVE))
    expected_stage.update({compose.GUARDIAN_OFF + "/" + name: pin for name, pin in expected_guardian_off.items()})
    expected_stage[compose.GUARDIAN_OFF_ARCHIVE] = digest(read(root / compose.GUARDIAN_OFF_ARCHIVE))
    expected_stage.update({compose.ITEM_OFF + "/" + name: pin for name, pin in expected_item_off.items()})
    expected_stage[compose.ITEM_OFF_ARCHIVE] = digest(read(root / compose.ITEM_OFF_ARCHIVE))
    expected_stage.update({compose.VAULT_OFF + "/" + name: pin for name, pin in expected_vault_off.items()})
    expected_stage[compose.VAULT_OFF_ARCHIVE] = digest(read(root / compose.VAULT_OFF_ARCHIVE))
    expected_stage.update({compose.CASTLE_OFF + "/" + name: pin for name, pin in expected_castle_off.items()})
    expected_stage[compose.CASTLE_OFF_ARCHIVE] = digest(read(root / compose.CASTLE_OFF_ARCHIVE))
    expected_stage.update({compose.SCORE_OFF + "/" + name: pin for name, pin in expected_score_off.items()})
    expected_stage[compose.SCORE_OFF_ARCHIVE] = digest(read(root / compose.SCORE_OFF_ARCHIVE))
    expected_stage.update({compose.RELAY_PRESENTATION_OFF + "/" + name: pin for name,pin in expected_relay_off.items()})
    expected_stage[compose.RELAY_PRESENTATION_OFF_ARCHIVE] = digest(read(root / compose.RELAY_PRESENTATION_OFF_ARCHIVE))
    expected_stage.update({compose.BR_CANYON_OFF + "/" + name: pin for name, pin in expected_canyon_off.items()})
    expected_stage[compose.BR_CANYON_OFF_ARCHIVE] = digest(read(root / compose.BR_CANYON_OFF_ARCHIVE))
    expected_stage.update({compose.ROLE_READABILITY_OFF + "/" + name: pin for name, pin in expected_role_off.items()})
    expected_stage[compose.ROLE_READABILITY_OFF_ARCHIVE] = digest(read(root / compose.ROLE_READABILITY_OFF_ARCHIVE))
    expected_stage.update({compose.FIELD_PROMPT_OFF + "/" + name: pin for name, pin in expected_field_off.items()})
    expected_stage[compose.FIELD_PROMPT_OFF_ARCHIVE] = digest(read(root / compose.FIELD_PROMPT_OFF_ARCHIVE))
    expected_stage.update({compose.NEUTRAL_NAMES_OFF + "/" + name: pin for name, pin in expected_neutral_off.items()})
    expected_stage[compose.NEUTRAL_NAMES_OFF_ARCHIVE] = digest(read(root / compose.NEUTRAL_NAMES_OFF_ARCHIVE))
    expected_stage.update({compose.GUARDIAN_WALL_OFF + "/" + name: pin for name, pin in expected_wall_off.items()})
    expected_stage[compose.GUARDIAN_WALL_OFF_ARCHIVE] = digest(read(root / compose.GUARDIAN_WALL_OFF_ARCHIVE))
    expected_stage.update({compose.COMBAT_VISUAL_OFF + "/" + name: pin for name, pin in expected_combat_off.items()})
    expected_stage[compose.COMBAT_VISUAL_OFF_ARCHIVE] = digest(read(root / compose.COMBAT_VISUAL_OFF_ARCHIVE))
    expected_stage.update({compose.GROWTH_MUSOU_OFF + "/" + name: pin for name, pin in expected_growth_off.items()})
    expected_stage[compose.GROWTH_MUSOU_OFF_ARCHIVE] = digest(read(root / compose.GROWTH_MUSOU_OFF_ARCHIVE))
    expected_stage.update({compose.ART_POLISH_OFF + "/" + name: pin for name, pin in expected_art_off.items()})
    expected_stage[compose.ART_POLISH_OFF_ARCHIVE] = digest(read(root / compose.ART_POLISH_OFF_ARCHIVE))
    expected_stage.update({compose.MAGE_CONTACT_OFF + "/" + name: pin for name, pin in expected_mage_off.items()})
    expected_stage[compose.MAGE_CONTACT_OFF_ARCHIVE] = digest(read(root / compose.MAGE_CONTACT_OFF_ARCHIVE))
    expected_stage.update({compose.RELAY_ELIGIBILITY_OFF + "/" + name: pin for name, pin in expected_eligibility_off.items()})
    expected_stage[compose.RELAY_ELIGIBILITY_OFF_ARCHIVE] = digest(read(root / compose.RELAY_ELIGIBILITY_OFF_ARCHIVE))
    expected_stage.update({compose.MOGURON_OFF + "/" + name: pin for name, pin in expected_moguron_off.items()})
    expected_stage[compose.MOGURON_OFF_ARCHIVE] = digest(read(root / compose.MOGURON_OFF_ARCHIVE))
    expected_stage.update({compose.PRIVATE_TOUCH_OFF + "/" + name: pin for name, pin in expected_touch_off.items()})
    expected_stage[compose.PRIVATE_TOUCH_OFF_ARCHIVE] = digest(read(root / compose.PRIVATE_TOUCH_OFF_ARCHIVE))
    expected_stage.update({compose.PORTRAIT_OFF + "/" + name: pin for name, pin in expected_portrait_off.items()})
    expected_stage[compose.PORTRAIT_OFF_ARCHIVE] = digest(read(root / compose.PORTRAIT_OFF_ARCHIVE))
    expected_stage.update({compose.SHOREFOAM_OFF + "/" + name: pin for name, pin in expected_shorefoam_off.items()})
    expected_stage[compose.SHOREFOAM_OFF_ARCHIVE] = digest(read(root / compose.SHOREFOAM_OFF_ARCHIVE))
    expected_stage.update({compose.TEAM_WIN_RULE_OFF + "/" + name: pin for name, pin in expected_team_win_off.items()})
    expected_stage[compose.TEAM_WIN_RULE_OFF_ARCHIVE] = digest(read(root / compose.TEAM_WIN_RULE_OFF_ARCHIVE))
    expected_stage.update({compose.FRACTIONAL_HP_OFF + "/" + name: pin for name, pin in expected_hp_off.items()})
    expected_stage[compose.FRACTIONAL_HP_OFF_ARCHIVE] = digest(read(root / compose.FRACTIONAL_HP_OFF_ARCHIVE))
    expected_stage.update({compose.MAGE_PROJECTILES_OFF + "/" + name: pin
                           for name, pin in expected_projectile_off.items()})
    expected_stage[compose.MAGE_PROJECTILES_OFF_ARCHIVE] = digest(read(root / compose.MAGE_PROJECTILES_OFF_ARCHIVE))
    expected_stage.update({compose.MAGE_WATER_CHAIN_OFF + "/" + name: pin
                           for name, pin in expected_water_chain_off.items()})
    expected_stage[compose.MAGE_WATER_CHAIN_OFF_ARCHIVE] = digest(read(root / compose.MAGE_WATER_CHAIN_OFF_ARCHIVE))
    expected_stage.update({compose.NINJA_S4_OFF + "/" + name: pin
                           for name, pin in expected_ninja_s4_off.items()})
    expected_stage[compose.NINJA_S4_OFF_ARCHIVE] = digest(read(root / compose.NINJA_S4_OFF_ARCHIVE))
    expected_stage.update({compose.WING_WARRIOR_OFF + "/" + name: pin
                           for name, pin in expected_wing_warrior_off.items()})
    expected_stage[compose.WING_WARRIOR_OFF_ARCHIVE] = digest(read(root / compose.WING_WARRIOR_OFF_ARCHIVE))
    expected_stage.update({compose.FIELD_LOADOUTS_OFF + "/" + name: pin
                           for name, pin in expected_field_loadouts_off.items()})
    expected_stage[compose.FIELD_LOADOUTS_OFF_ARCHIVE] = digest(read(root / compose.FIELD_LOADOUTS_OFF_ARCHIVE))
    expected_stage.update({compose.RETURN_CONVERT_OFF + "/" + name: pin
                           for name, pin in expected_return_convert_off.items()})
    expected_stage[compose.RETURN_CONVERT_OFF_ARCHIVE] = digest(read(root / compose.RETURN_CONVERT_OFF_ARCHIVE))
    expected_stage.update({compose.GROUND_NIGHT_OFF + "/" + name: pin
                           for name, pin in expected_ground_night_off.items()})
    expected_stage[compose.GROUND_NIGHT_OFF_ARCHIVE] = digest(read(root / compose.GROUND_NIGHT_OFF_ARCHIVE))
    expected_stage.update({compose.COVER_ORDERS_OFF + "/" + name: pin
                           for name, pin in expected_cover_orders_off.items()})
    expected_stage[compose.COVER_ORDERS_OFF_ARCHIVE] = digest(read(root / compose.COVER_ORDERS_OFF_ARCHIVE))
    expected_stage.update({compose.MAGE_FIELD_ARCS_OFF + "/" + name: pin
                           for name, pin in expected_mage_field_arcs_off.items()})
    expected_stage[compose.MAGE_FIELD_ARCS_OFF_ARCHIVE] = digest(read(root / compose.MAGE_FIELD_ARCS_OFF_ARCHIVE))
    expected_stage.update({compose.ECLIPSE_SWEEP_OFF + "/" + name: pin
                           for name, pin in expected_eclipse_sweep_off.items()})
    expected_stage[compose.ECLIPSE_SWEEP_OFF_ARCHIVE] = digest(read(root / compose.ECLIPSE_SWEEP_OFF_ARCHIVE))
    expected_stage.update({compose.BUILDER_FORMS_OFF + "/" + name: pin
                           for name, pin in expected_builder_forms_off.items()})
    expected_stage[compose.BUILDER_FORMS_OFF_ARCHIVE] = digest(read(root / compose.BUILDER_FORMS_OFF_ARCHIVE))
    expected_stage.update({compose.FOOTING_WARDS_OFF + "/" + name: pin
                           for name, pin in expected_footing_wards_off.items()})
    expected_stage[compose.FOOTING_WARDS_OFF_ARCHIVE] = digest(read(root / compose.FOOTING_WARDS_OFF_ARCHIVE))
    expected_stage.update({compose.NINJA_BEAST_CASTLE_OFF + "/" + name: pin
                           for name, pin in expected_ninja_beast_castle_off.items()})
    expected_stage[compose.NINJA_BEAST_CASTLE_OFF_ARCHIVE] = digest(read(root / compose.NINJA_BEAST_CASTLE_OFF_ARCHIVE))
    expected_stage.update({compose.SPRING_MIST_FOREST_OFF + "/" + name: pin
                           for name, pin in expected_spring_mist_forest_off.items()})
    expected_stage[compose.SPRING_MIST_FOREST_OFF_ARCHIVE] = digest(read(root / compose.SPRING_MIST_FOREST_OFF_ARCHIVE))
    expected_stage.update({compose.NINJA_STEPS_OBJECTIVES_OFF + "/" + name: pin
                           for name, pin in expected_ninja_steps_objectives_off.items()})
    expected_stage[compose.NINJA_STEPS_OBJECTIVES_OFF_ARCHIVE] = digest(read(root / compose.NINJA_STEPS_OBJECTIVES_OFF_ARCHIVE))
    expected_stage.update({compose.WARRIOR_FIELD_HORDE_OFF + "/" + name: pin
                           for name, pin in expected_warrior_field_horde_off.items()})
    expected_stage[compose.WARRIOR_FIELD_HORDE_OFF_ARCHIVE] = digest(read(root / compose.WARRIOR_FIELD_HORDE_OFF_ARCHIVE))
    expected_stage.update({compose.TRAPPER_CAST_AUDIO_OFF + "/" + name: pin
                           for name, pin in expected_trapper_cast_audio_off.items()})
    expected_stage[compose.TRAPPER_CAST_AUDIO_OFF_ARCHIVE] = digest(read(root / compose.TRAPPER_CAST_AUDIO_OFF_ARCHIVE))
    expected_stage.update({compose.ZOMBIE_FORMATION_CAMERA_OFF + "/" + name: pin
                           for name, pin in expected_zombie_formation_camera_off.items()})
    expected_stage[compose.ZOMBIE_FORMATION_CAMERA_OFF_ARCHIVE] = digest(read(root / compose.ZOMBIE_FORMATION_CAMERA_OFF_ARCHIVE))
    expected_stage.update({compose.PROJECT: lock["project"], compose.PLACE: lock["final_place"],
                           compose.OFF_ARCHIVE: digest(read(root / compose.OFF_ARCHIVE))})
    require(core.get("staged_payload_verified_after_all_commands") is True
            and core.get("staged_payload") == expected_stage, "CORE_FINAL_STAGED_PAYLOAD")
    expected_root = {**expected_stage, compose.RECEIPT: digest(read(root / compose.RECEIPT)),
                     "CORE_BUILD_REPORT.json": digest(read(root / "CORE_BUILD_REPORT.json"))}
    require(files(root) == expected_root, "CURRENT_ROOT_PAYLOAD_SET_OR_IDENTITY")
    commands = core.get("commands", [])
    require(len(commands) == core["compile_count"] + core["rojo_build_count"]
            and all(c.get("exit") == 0 for c in commands), "CORE_COMMAND_COMPLETION")
    compile_commands = [c for c in commands if len(c.get("command", [])) == 3 and c["command"][1] == "--text"]
    rojo_commands = [c for c in commands if len(c.get("command", [])) == 5 and c["command"][1] == "build"
                     and c["command"][3] == "-o"]
    require(len(compile_commands) == core["compile_count"]
            and len(rojo_commands) == core["rojo_build_count"], "CORE_COMMAND_TYPES")
    stage = core.get("build_command_namespace", {}).get("executed_stage")
    require(isinstance(stage, str) and Path(stage).is_absolute()
            and core["build_command_namespace"].get("committed_root") == str(root)
            and core["build_command_namespace"].get("commands_are_actual_pre_rename_paths") is True,
            "CORE_COMMAND_NAMESPACE")
    selected_sources = {"": lock["sources"], compose.OFF: lock["sources"],
                        compose.BOT_OFF: [compose.BOT_SOURCE], compose.HUD_OFF: [compose.HUD_SOURCE],
                        compose.BEAST_OFF: [compose.BEAST_SOURCE], compose.GUARDIAN_OFF: [compose.GUARDIAN_SOURCE],
                        compose.ITEM_OFF: [compose.ITEM_SOURCE], compose.VAULT_OFF: [compose.VAULT_SOURCE],
                        compose.CASTLE_OFF: [compose.VAULT_SOURCE], compose.SCORE_OFF: [compose.SCORE_SOURCE],
                        compose.RELAY_PRESENTATION_OFF: [name for name in lock["sources"]
                                                        if name in compose.RELAY_PRESENTATION_SOURCES],
                        compose.BR_CANYON_OFF: [name for name in lock["sources"] if name in compose.BR_CANYON_SOURCES],
                        compose.ROLE_READABILITY_OFF: [name for name in lock["sources"]
                                                        if name in compose.ROLE_READABILITY_SOURCES],
                        compose.FIELD_PROMPT_OFF: [compose.VAULT_SOURCE],
                        compose.NEUTRAL_NAMES_OFF: [name for name in lock["sources"]
                                                    if name in compose.VISUAL_READABILITY_SOURCES],
                        compose.GUARDIAN_WALL_OFF: [compose.GUARDIAN_SOURCE],
                        compose.COMBAT_VISUAL_OFF: [name for name in lock["sources"]
                                                  if name in compose.COMBAT_VISUAL_SOURCES],
                        compose.GROWTH_MUSOU_OFF: [name for name in lock["sources"]
                                                if name in compose.GROWTH_MUSOU_SOURCES],
                        compose.ART_POLISH_OFF: [name for name in lock["sources"]
                                               if name in compose.ART_POLISH_SOURCES],
                        compose.MAGE_CONTACT_OFF: [name for name in lock["sources"]
                                                 if name in compose.MAGE_CONTACT_SOURCES],
                        compose.RELAY_ELIGIBILITY_OFF: [name for name in lock["sources"]
                                                       if name in compose.RELAY_ELIGIBILITY_SOURCES],
                        compose.MOGURON_OFF: [compose.MOGURON_SOURCE],
                        compose.PRIVATE_TOUCH_OFF: [compose.PRIVATE_TOUCH_SOURCE],
                        compose.PORTRAIT_OFF: [compose.PORTRAIT_SOURCE],
                        compose.SHOREFOAM_OFF: [compose.SHOREFOAM_SOURCE],
                        compose.TEAM_WIN_RULE_OFF: [compose.VAULT_SOURCE],
                        compose.FRACTIONAL_HP_OFF: [compose.HUD_SOURCE],
                        compose.MAGE_PROJECTILES_OFF: [name for name in lock["sources"]
                                                      if name in compose.MAGE_PROJECTILES_SOURCES],
                        compose.MAGE_WATER_CHAIN_OFF: [name for name in lock["sources"]
                                                      if name in compose.MAGE_WATER_CHAIN_SOURCES],
                        compose.NINJA_S4_OFF: [name for name in lock["sources"]
                                              if name in compose.NINJA_S4_SOURCES],
                        compose.WING_WARRIOR_OFF: [name for name in lock["sources"]
                                                   if name in compose.WING_WARRIOR_SOURCES],
                        compose.FIELD_LOADOUTS_OFF: [name for name in lock["sources"]
                                                     if name in compose.FIELD_LOADOUTS_SOURCES],
                        compose.RETURN_CONVERT_OFF: [name for name in lock["sources"]
                                                     if name in compose.RETURN_CONVERT_SOURCES],
                        compose.GROUND_NIGHT_OFF: [name for name in lock["sources"]
                                                    if name in compose.GROUND_NIGHT_SOURCES],
                        compose.COVER_ORDERS_OFF: [name for name in lock["sources"]
                                                    if name in compose.COVER_ORDERS_SOURCES],
                        compose.MAGE_FIELD_ARCS_OFF: [name for name in lock["sources"]
                                                    if name in compose.MAGE_FIELD_ARCS_SOURCES],
                        compose.ECLIPSE_SWEEP_OFF: [name for name in lock["sources"]
                                                   if name in compose.ECLIPSE_SWEEP_SOURCES],
                        compose.BUILDER_FORMS_OFF: [name for name in lock["sources"]
                                                   if name in compose.BUILDER_FORMS_SOURCES],
                        compose.FOOTING_WARDS_OFF: [name for name in lock["sources"]
                                                   if name in compose.FOOTING_WARDS_SOURCES],
                        compose.NINJA_BEAST_CASTLE_OFF: [name for name in lock["sources"]
                                                        if name in compose.NINJA_BEAST_CASTLE_SOURCES],
                        compose.SPRING_MIST_FOREST_OFF: [name for name in lock["sources"]
                                                        if name in compose.SPRING_MIST_FOREST_SOURCES],
                        compose.NINJA_STEPS_OBJECTIVES_OFF: [name for name in lock["sources"]
                                                             if name in compose.NINJA_STEPS_OBJECTIVES_SOURCES],
                        compose.WARRIOR_FIELD_HORDE_OFF: [name for name in lock["sources"]
                                                            if name in compose.WARRIOR_FIELD_HORDE_SOURCES],
                        compose.TRAPPER_CAST_AUDIO_OFF: [name for name in lock["sources"]
                                                            if name in compose.TRAPPER_CAST_AUDIO_SOURCES],
                        compose.ZOMBIE_FORMATION_CAMERA_OFF: [name for name in lock["sources"]
                                                            if name in compose.ZOMBIE_FORMATION_CAMERA_SOURCES]}
    # The independently verified payload must contain exactly these build stages.
    # Derive the three command checks from one ordered verifier-owned source map.
    expected_place_stages = {"" if name == compose.PLACE else name.rsplit("/", 1)[0]
                             for name in expected_stage
                             if name == compose.PLACE or
                             (name.count("/") == 1 and name.endswith("/" + compose.PLACE))}
    require(set(selected_sources) == expected_place_stages
            and all(selected and len(selected) == len(set(selected))
                    and set(selected) <= set(lock["sources"])
                    for selected in selected_sources.values()), "CORE_BUILD_STAGE_MAP")
    expected_order = []
    expected_compile = set()
    expected_rojo = set()
    for prefix, selected in selected_sources.items():
        folder = Path(stage) / prefix
        paths = [str(folder / "sources" / name) for name in selected
                 if prefix != compose.OFF or name not in expected_reuse]
        expected_compile.update(paths)
        expected_order.extend(("--text", path) for path in paths)
        project, place = str(folder / compose.PROJECT), str(folder / compose.PLACE)
        expected_rojo.add((project, place))
        expected_order.append(("build", project))
    require({c["command"][2] for c in compile_commands} == expected_compile, "CORE_COMPILED_SOURCE_SET")
    require({(c["command"][2], c["command"][4]) for c in rojo_commands} == expected_rojo,
            "CORE_ROJO_PROJECT_SET")
    require([(c["command"][1], c["command"][2]) for c in commands] == expected_order,
            "CORE_BUILD_STAGE_ORDER")
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
    rows = verified["lock"]["art_polish_followup"]["donors"]
    def art_author(name):
        donor = rows[name]
        return visual_author(donor["path"], donor["identity"], "ART_POLISH_NEGATIVE_" + name)
    art_author("skill").self_test()
    art_author("field").selftest()
    sys.path.insert(0, str(REPO / "quality_gameplay/gq8_rc85_rc86_real68_nonloss_20261120"))
    try:
        art_author("ridge").selftest()
    finally:
        sys.path.pop(0)
    prior = root / compose.ART_POLISH_OFF / "sources"
    current = root / "sources"
    guard, _, twin, result, _ = compose.ART_POLISH_SOURCES
    twin_cases = art_author("twin").verify_selftest(read(prior / twin).decode())
    require(twin_cases["mutations_rejected"] == 9, "ART_POLISH_TWIN_NEGATIVE_CASES")
    require(art_author("guardian_gate").negative(read(prior / guard), read(current / guard)) == 6,
            "ART_POLISH_GUARDIAN_NEGATIVE_CASES")
    require(art_author("result_gate").negative_tests(read(prior / result).decode(), read(current / result).decode()) == 8,
            "ART_POLISH_RESULT_NEGATIVE_CASES")
    for origin in verified["lock"]["combat_visual_followup"]["origins"].values():
        author = visual_author(origin["path"], origin["python_bytes"], "COMBAT_VISUAL_ORIGINAL")
        getattr(author, origin["selftest"])()
    require(neutral_names_author(verified["lock"]).selftest() == 11, "NEUTRAL_NAMES_AUTHOR_NEGATIVE_CASES")
    plaza = verified["lock"]["neutral_names_followup"]["plaza"]
    visual_author(plaza["author_file"], plaza["author_transform"], "LOBBY_PLAZA_AUTHOR").self_test()
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
    if suite_name == "combined_clear_los":
        fixture = read(HERE / "native/fixtures/guardian_wall_geometry.luau")
        require(digest(fixture) == pins["fixtures"]["guardian_wall_geometry.luau"], "GUARDIAN_WALL_FIXTURE_IDENTITY")
        program.extend(fixture + b"\n")
    if suite_name == "beast_target_selection":
        fixture = read(HERE / "native/beast_fixture.luau")
        require(digest(fixture) == pins["suites"][suite_name]["fixture"], "BEAST_EXECUTED_FIXTURE_IDENTITY")
        program.extend(fixture + b"\n")
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
                  "objective_full_clear_los": "objective_full_cases_clear_los.luau",
                  "beast_target_selection": "beast_cases.luau"}
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
    """Independently bind the historic pre-portrait layout test to its exact source stage."""
    folder = native / "selected_hud_layout"
    result = data(folder / "receipt.json")
    profile = compose.load_lock()
    old_policy = profile["portrait_followup"]["rows"][compose.PORTRAIT_SOURCE]["parent"]["after"]
    old_traversal = profile["shorefoam_followup"]["rows"][compose.SHOREFOAM_SOURCE]["parent"]["after"]
    old_host = profile["team_win_rule_followup"]["rows"][compose.VAULT_SOURCE]["parent"]["after"]
    old_hud = profile["fractional_hp_followup"]["rows"][compose.HUD_SOURCE]["parent"]["after"]
    source_pins = pins["sources"] | {compose.PORTRAIT_SOURCE: old_policy, compose.SHOREFOAM_SOURCE: old_traversal,
                                    compose.VAULT_SOURCE: old_host, compose.HUD_SOURCE: old_hud}
    source_stage = root / compose.PORTRAIT_OFF / "sources"
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
        raw = read(source_stage / path)
        require(raw == read(folder / "sources" / name) and digest(raw) == source_pins[path],
                "NATIVE_SELECTED_LAYOUT_FINAL_SOURCE")
        selected[path] = digest(raw)
    tree = ast.parse(generator.decode("utf-8"))
    values = [ast.literal_eval(node.value) for node in tree.body
              if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "TEST"
                                                     for t in node.targets)]
    require(len(values) == 1 and isinstance(values[0], str) and values[0].count("__SOURCE__") == 1,
            "NATIVE_SELECTED_LAYOUT_TEST_TEMPLATE")
    policy = read(source_stage / compose.PORTRAIT_SOURCE)
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


def independent_bot_contract(pins):
    """Read immutable data directly; never import the supplement's decisions."""
    require({name: digest(read(HERE / "native" / name)) for name in BOT_INPUTS} == BOT_INPUTS,
            "BOT_IMMUTABLE_INPUTS")
    contract = data(HERE / "native/bot_vault_cases.json")
    template = read(HERE / "native/bot_vault_base.template.luau")
    modules = contract["modules_in_load_order"]
    names = [m["module"] for m in modules]
    paths = [m["relative_source_path"] for m in modules]
    require(contract["schema"] == "BOT_VAULT_NATIVE_SUPPLEMENT_CASES_V1"
            and tuple(s["scenario_id"] for s in contract["scenarios"]) == BOT_SCENARIOS
            and len(names) == len(set(names)) == len(set(paths)) == 16
            and all(p in pins["sources"] for p in paths), "BOT_FIXED_SCENARIO_AND_BODY_SET")
    original = {"ServerScriptService/EGGRUMBLE_" + p + ".luau"
                for p in pins["modules_in_load_order"] + ["LobbyCastleModesPreview.server"]}
    policy = "ReplicatedStorage/EGGRUMBLE_HudPresentationPolicy.luau"
    require(len(original) == 28 and len(original & set(paths)) == 14
            and set(paths) - original == {compose.BOT_SOURCE, "ServerScriptService/EGGRUMBLE_BotPathRouter.luau"}
            and len(original | set(paths)) == 30 and policy in pins["sources"]
            and len(original | set(paths) | {policy}) == 31, "BOT_DISTINCT_BODY_COVERAGE")
    for item in modules:
        pinned = pins["sources"][item["relative_source_path"]]
        if item["module"] == "BotActors":
            require(pinned == {"bytes": 20012, "sha256": "06e5197b826d1cd279d27ce019a92d9dcc5b9b651c6933587e69a6ecff5cdc23"},
                    "BOT_EXACT_DISPLAY_SOURCE")
        if item["module"] == "BotPathRouter":
            require(pinned == item["historical_candidate"], "BOT_ORIGINAL_ROUTER")
    corpora = contract["corpora"]
    require(len(corpora) == len({c["id"] for c in corpora}) == 6
            and all(digest(c["raw_text"].encode("utf-8")) == c["identity"] for c in corpora),
            "BOT_CORPUS_BYTES")
    expected = {
        "schema": "UNION22_BOT_VAULT_SUPPLEMENT_LOCK_V1", "input_files": BOT_INPUTS,
        "output_directory": "bot_vault", "module_order": names,
        "selected_sources": {p: pins["sources"][p] for p in paths},
        "scenario_order": list(BOT_SCENARIOS),
        "scenarios": {s["scenario_id"]: {
            "configuration_substitutions": s["configuration_substitutions"],
            "case_assembly": s["case_assembly_identity"],
            "expected_case_names": s["expected_ordered_CASE_names"],
            "expected_check_names": s["expected_ordered_CHECK_names"]} for s in contract["scenarios"]},
        "expected_totals": {"scenarios": 9, "CASE_rows": 13, "CHECK_rows": 43, "warning_rows": 0,
                            "stderr_bytes": 0, "each_exit_code": 0, "evidence_files": 37},
        "full_bodies_each_scenario": 16, "original_dual28_full_bodies": 28,
        "distinct_server_full_bodies": 30, "hud_policy_separate_from_server_body_count": True,
        "preserve_original_dual28_generated_programs": True, "same_fresh_F46_binary_required": True,
        "source_only": True,
    }
    require(pins.get("bot_vault_supplement") == expected, "BOT_LOCK_SCENARIO_BINDING")
    return contract, template


def independent_bot_generated(root, pins, scenario_id):
    """Rebuild from frozen tokens and current complete bodies, then locate ranges."""
    contract, template = independent_bot_contract(pins)
    require(len(pins["sources"]) == 69 and files(root / "sources") == pins["sources"], "BOT_SOURCE_PROFILE")
    matches = [s for s in contract["scenarios"] if s["scenario_id"] == scenario_id]
    require(len(matches) == 1, "BOT_UNKNOWN_SCENARIO")
    item = matches[0]
    corpora = {c["id"]: c["raw_text"].encode("utf-8") for c in contract["corpora"]}
    case = b"".join(corpora[p["corpus_id"]] if "corpus_id" in p else p["literal_utf8"].encode("utf-8")
                    for p in item["case_assembly_order"])
    require(digest(case) == item["case_assembly_identity"], "BOT_CASE_ASSEMBLY")
    replacements = {key.encode(): value.encode() for key, value in item["configuration_substitutions"].items()}
    replacements[item["case_token"].encode()] = case
    bodies = {}
    for module_row in contract["modules_in_load_order"]:
        path = module_row["relative_source_path"]
        bodies[path] = read(root / "sources" / path)
        replacements[module_row["token"].encode()] = bodies[path]
    token = re.compile(rb"@@[A-Za-z0-9_]+@@")
    observed = token.findall(template)
    require(len(observed) == len(set(observed)) == len(replacements) == 20
            and set(observed) == set(replacements), "BOT_TEMPLATE_TOKEN_SET")
    generated = token.sub(lambda match: replacements[match.group()], template)
    require(not token.search(generated), "BOT_UNRESOLVED_TOKEN")
    ranges, lines, previous = {}, {}, -1
    for module_row in contract["modules_in_load_order"]:
        path, name = module_row["relative_source_path"], module_row["module"]
        body = bodies[path]
        require(digest(body) == pins["sources"][path] and generated.count(body) == 1, "BOT_FULL_BODY_EXACT_ONCE")
        start = generated.index(body)
        require(start > previous, "BOT_FULL_BODY_ORDER")
        end = start + len(body)
        ranges[path] = {"module": name, "start": start, "end": end, **digest(body)}
        first = generated[:start].count(b"\n") + 1
        lines[name] = {"first": first, "last": first + body.count(b"\n")}
        previous = end
    return generated, {"scenario_id": scenario_id,
                       "configuration_substitutions": item["configuration_substitutions"],
                       "case_assembly": digest(case), "full_body_byte_ranges": ranges,
                       "source_line_ranges": lines, "generated": digest(generated)}


def independent_bot_vectors(item, stdout, stderr, exit_code):
    """Interpret raw process bytes; receipt PASS fields cannot supply a row."""
    require(type(stdout) is bytes and type(stderr) is bytes, "BOT_RAW_PROCESS_BYTES")
    require(type(exit_code) is int and exit_code == 0 and stderr == b"", "BOT_PROCESS_EXIT_OR_STDERR")
    vectors = {"CASE": [], "CHECK": []}
    for line in stdout.decode("utf-8").splitlines():
        require(not line.lstrip().upper().startswith("WARN"), "BOT_RUNTIME_WARNING")
        if line.lstrip().upper().startswith(("CASE", "CHECK")):
            parts = line.split("\t", 3)
            require(len(parts) == 4 and parts[0] in vectors and parts[2] == "PASS", "BOT_RAW_VECTOR_ROW")
            vectors[parts[0]].append(parts)
    for kind, rows in vectors.items():
        require([row[1] for row in rows] == item["expected_ordered_" + kind + "_names"],
                "BOT_RAW_" + kind + "_VECTOR")
    return {"case_rows": vectors["CASE"], "check_rows": vectors["CHECK"], "warning_rows": [],
            "exit_code": exit_code, "stderr_bytes": 0, "exact_complete_pass_vectors": True}


def verify_bot_vault_supplement(native, root, pins, build, aggregate, context):
    """Bind all nine executions to current sources and the already verified F46."""
    contract, _ = independent_bot_contract(pins)
    folder = native / "bot_vault"
    observed = files(folder)
    expected_files = {"receipt.json"} | {scenario + "/" + name for scenario in BOT_SCENARIOS
                      for name in ("generated.luau", "stdout.log", "stderr.log", "receipt.json")}
    require(len(expected_files) == 37 and set(observed) == expected_files, "BOT_EVIDENCE_FILE_SET")
    source_receipt = digest(read(root / compose.RECEIPT))
    binary_pin = build["binary_before_suites"]
    require(build.get("bot_vault_input_files") == BOT_INPUTS
            and digest(read(build["binary_path"])) == binary_pin, "BOT_SAME_ACTUAL_BUILD_AND_INPUTS")
    common = {
        "execution_context": context, "source_receipt": source_receipt, "input_files": BOT_INPUTS,
        "source_count_pinned": 69, "source_count_executed_full_body": 16,
        "caller_fresh_build": {k: build[k] for k in
            ("schema", "source_commit", "source_tree", "binary_before_suites", "target_build_started_ns")},
        "source_only": True, "formal_rc_adoption_proven": False, "engine_boundary": contract["engine_boundary"],
    }
    layout = data(native / "selected_hud_layout/receipt.json")
    execution_root = Path(layout["execution_directory"]).parent
    require(execution_root.is_absolute() and ".." not in execution_root.parts, "BOT_EXECUTION_NAMESPACE")
    def utc(value):
        require(isinstance(value, str), "BOT_PROCESS_TIME_TYPE")
        result = datetime.fromisoformat(value)
        require(result.tzinfo is not None and result.utcoffset().total_seconds() == 0, "BOT_PROCESS_TIME_UTC")
        return result
    previous_finish = utc(layout["commands"]["native"]["started_at_utc"])
    build_start = datetime.fromtimestamp(build["target_build_started_ns"] / 1_000_000_000, timezone.utc)
    results, case_count, check_count = {}, 0, 0
    for item in contract["scenarios"]:
        scenario_id = item["scenario_id"]
        path = folder / scenario_id
        result = data(path / "receipt.json")
        expected_program, assembly = independent_bot_generated(root, pins, scenario_id)
        generated = read(path / "generated.luau")
        require(generated == expected_program
                and all(result.get(k) == value for k, value in assembly.items()), "BOT_GENERATED_PROGRAM_AND_RANGES")
        process = result.get("process", {})
        require(set(process) == {"argv", "exit_code", "timed_out", "started_at_utc", "finished_at_utc", "elapsed_ns"}
                and process["argv"] == [build["binary_path"], str(execution_root / "bot_vault" / scenario_id / "generated.luau")]
                and type(process["elapsed_ns"]) is int and process["elapsed_ns"] > 0
                and process["timed_out"] is False, "BOT_EXECUTED_COMMAND")
        started, finished = utc(process["started_at_utc"]), utc(process["finished_at_utc"])
        require(build_start <= started <= finished and previous_finish <= started, "BOT_PROCESS_ORDER_AND_BUILD_TIME")
        previous_finish = finished
        stdout, stderr = read(path / "stdout.log"), read(path / "stderr.log")
        parsed = independent_bot_vectors(item, stdout, stderr, process["exit_code"])
        expected = {**common, **assembly, "schema": "BOT_VAULT_NATIVE_SCENARIO_V1", "status": "PASS",
                    "native": binary_pin, "process": process, "result": parsed,
                    "source_inputs_unchanged": True, "generated_and_binary_unchanged": True,
                    "stdout": digest(stdout), "stderr": digest(stderr)}
        require(result == expected and result.get("source_only") is True
                and result.get("formal_rc_adoption_proven") is False
                and result.get("source_inputs_unchanged") is True and result.get("generated_and_binary_unchanged") is True
                and result.get("result", {}).get("exact_complete_pass_vectors") is True, "BOT_SCENARIO_RECEIPT_BINDING")
        case_count += len(parsed["case_rows"])
        check_count += len(parsed["check_rows"])
        results[scenario_id] = {"case_count": len(parsed["case_rows"]), "check_count": len(parsed["check_rows"]),
                                "receipt": digest(read(path / "receipt.json"))}
    require((len(results), case_count, check_count) == (9, 13, 43), "BOT_COMPLETE_SCENARIO_VECTORS")
    totals = {"scenarios": 9, "CASE_rows": case_count, "CHECK_rows": check_count, "warning_rows": 0,
              "full_bodies_per_scenario": 16, "distinct_full_bodies_with_existing_dual28": 30}
    summary = data(folder / "receipt.json")
    expected_summary = {**common, "schema": "BOT_VAULT_NATIVE_SUPPLEMENT_V1", "status": "PASS", "totals": totals,
                        "ordered_scenarios": list(BOT_SCENARIOS), "source_profile": pins["sources"],
                        "source_inputs_unchanged": True, "native": binary_pin, "output_files_including_this_receipt": 37,
                        "scenario_files": {name: pin for name, pin in observed.items() if name != "receipt.json"}}
    require(summary == expected_summary and summary.get("source_inputs_unchanged") is True
            and summary.get("source_only") is True and summary.get("formal_rc_adoption_proven") is False,
            "BOT_SUPPLEMENT_RECEIPT_BINDING")
    require(aggregate.get("bot_vault_supplement") == digest(read(folder / "receipt.json"))
            and aggregate.get("bot_vault_input_files") == BOT_INPUTS, "BOT_SUPPLEMENT_AGGREGATE_BINDING")
    require(files(folder) == observed and files(root / "sources") == pins["sources"]
            and digest(read(build["binary_path"])) == binary_pin
            and {name: digest(read(HERE / "native" / name)) for name in BOT_INPUTS} == BOT_INPUTS,
            "BOT_INPUT_OR_OUTPUT_CHANGED_DURING_VALIDATION")
    return {"totals": totals, "scenarios": results, "receipt": digest(read(folder / "receipt.json")),
            "same_fresh_binary": True, "engine_boundary": contract["engine_boundary"], "files": expected_files}


def verify_guardian_program_frame(program, ranges, contract, role, mode):
    cursor = 0
    def consume_literal(expected):
        nonlocal cursor
        require(program[cursor:cursor + len(expected)] == expected, "GUARDIAN_PROGRAM_FRAME")
        cursor += len(expected)

    def consume_pinned(pin):
        nonlocal cursor
        stop = cursor + pin["bytes"]
        require(digest(program[cursor:stop]) == pin, "GUARDIAN_PROGRAM_PINNED_FIXTURE")
        cursor = stop

    for fixture in contract["execution_fixture_order"]:
        consume_pinned(fixture["identity"])
        consume_literal(b"\n")
    for name in contract["modules_in_load_order"]:
        if name == "LobbyCastleModesPreview.server":
            span = ranges["Host"]
            consume_literal(b"\ninstallApiObservers()\nloadingModule='Host'\ndo local _=(function()\n")
            closing = b"\nend)()end\n"
        else:
            span = ranges[name]
            consume_literal(
                (f"\nloadingModule='{name}'\n"
                 f"fullSourceRanges.{name}={{first={span['line_first']},last={span['line_last']}}}\n"
                 f"dependencies.EGGRUMBLE_{name}=(function()\n").encode())
            closing = b"\nend)()\n"
        require(cursor == span["byte_start"], "GUARDIAN_PROGRAM_SOURCE_START")
        cursor = span["byte_end_exclusive"]
        consume_literal(closing)
    expected = contract["guardian_roles"][role]
    consume_literal((f"\nlocal GUARDIAN_ROLE='{role}'\n"
                     f"local GUARDIAN_EXPECT={{hp={expected['hp']},damage={expected['damage']}}}\n").encode())
    consume_pinned(contract["package_pins"]["fixture_boundary.luau"])
    consume_literal((f"\n\nlocal MODE='{mode}'\n").encode())
    consume_pinned(contract["package_pins"]["case.luau"])
    require(cursor == len(program), "GUARDIAN_PROGRAM_TRAILING_BYTES")


def verify_guardian_target(native, root, profile, input_pins, build, aggregate, context):
    folder = native / "guardian_target"
    if not folder.exists():
        require(context["kind"] == "LOCAL_SOURCE_REVIEW" and "guardian_target_diagnostic" not in aggregate,
                "MISSING_GUARDIAN_TARGET_EVIDENCE")
        return None, set()
    summary_name, contract_name = "GUARDIAN_DIAGNOSTIC_RECEIPT.json", "GUARDIAN_DONOR_CONTRACT.json"
    summary_path, contract_path = folder / summary_name, folder / contract_name
    summary, contract = data(summary_path), data(contract_path)
    repair = profile["guardian_followup_repair"]
    contract_pin = {"bytes": 39478,
                    "sha256": "f37a9500da30d08fcd1baf30fec340d86733b18fd9c9d34f5e5917f271347dcb"}
    require(digest(read(contract_path)) == contract_pin == summary["contract"], "GUARDIAN_MATRIX_DONOR_LOCK")
    package = contract["existing_package_relative_path"]
    donor_inputs = {"stealth_target/INPUT_LOCK.json": contract_pin,
                    "stealth_target/run.py": {"bytes": 18363,
                        "sha256": "fbe55545d5d427a37ae3bf7d30d6f7bc6a427d4d3dd997516970c140a666ef09"}}
    donor_inputs.update({f"stealth_target/{name}": contract["package_pins"][name]
                         for name in ("apply_stealth_target.py", "case.luau", "fixture_boundary.luau")})
    originals = contract["existing_pr_files"]
    require(package == "quality_gameplay/gq8_guardian_runtime_20261118" and len(originals) == 12
            and all(path.startswith((f"{package}/role_los/", f"{package}/role_session/")) for path in originals),
            "GUARDIAN_MATRIX_ORIGINAL_DEPENDENCIES")
    donor_inputs.update({path.removeprefix(package + "/"): pin for path, pin in originals.items()})
    require(summary["donor_inputs"] == donor_inputs
            and summary["donor_head"] == repair["donor_head"]
            and summary["schema"] == "UNION22_GUARDIAN_DONOR_MATRIX_V1"
            and summary["status"] == "SOURCE_NATIVE_PASS" and summary["studio"] == "NOT_TESTED"
            and summary["gameplay_delivery_status_inferred"] is False and summary["context"] == context
            and summary["binary"] == build["binary_before_suites"]
            and summary["native_build_receipt"] == digest(read(native / "build_receipt.json"))
            and summary["source_receipt"] == digest(read(root / compose.RECEIPT))
            and summary["source_pin"] == repair["repaired_guardian"]
            == profile["guardian_wall_followup"]["rows"][compose.GUARDIAN_SOURCE]["parent"]["after"]
            == digest(read(root / compose.GUARDIAN_WALL_OFF / "sources" / compose.GUARDIAN_SOURCE))
            and input_pins["sources"][compose.GUARDIAN_SOURCE] == profile["sources"][compose.GUARDIAN_SOURCE]["after"]
            and summary["place"] == repair["repaired_place"]
            and summary["immediate_inverse_place"] == repair["parent_place"]
            and summary["unchanged_other_sources"] == 68
            and aggregate["guardian_target_diagnostic"] == digest(read(summary_path)),
            "GUARDIAN_MATRIX_PROVENANCE")
    matrix = contract["matrix"]
    require(len(matrix) == len(summary["results"]) == summary["native_executions"] == 40
            and len({(case["role"], case["mode"]) for case in matrix}) == summary["unique_scenarios"] == 13,
            "GUARDIAN_MATRIX_SCENARIO_SET")
    observed, counts = {}, Counter()
    guard_source = compose.GUARDIAN_SOURCE
    # The Guardian matrix keeps its recorded historical parent context. The
    # current Host is exercised separately by the full and Bot/Vault suites.
    guardian_context_pins = compose.trial_sources_before(profile, "mage_projectile_followup") | {
        name: row["parent"]["after"] for name, row in profile["fractional_hp_followup"]["rows"].items()
    } | {
        name: row["parent"]["after"] for name, row in profile["shorefoam_followup"]["rows"].items()
    } | {
        name: row["parent"]["after"] for name, row in profile["portrait_followup"]["rows"].items()
    } | {
        name: row["parent"]["after"] for name, row in profile["relay_eligibility_followup"]["rows"].items()
    } | {
        name: row["parent"]["after"] for name, row in profile["mage_contact_followup"]["rows"].items()
    } | {
        name: row["parent"]["after"] for name, row in profile["art_polish_followup"]["rows"].items()
    } | {
        name: row["parent"]["after"] for name, row in profile["growth_musou_followup"]["rows"].items()
    } | {
        name: row["parent"]["after"] for name, row in profile["combat_visual_followup"]["rows"].items()
    } | {
        guard_source: repair["repaired_guardian"],
    } | {
        name: row["parent"]["after"] for name, row in profile["neutral_names_followup"]["rows"].items()
    } | {
        name: row["parent"]["after"] for name, row in profile["role_readability_followup"]["rows"].items()
    } | {
        name: row["parent"]["after"] for name, row in profile["br_canyon_followup"]["rows"].items()
    } | {
        compose.HUD_SOURCE: profile["relay_presentation_followup"]["rows"][compose.HUD_SOURCE]["parent"]["after"],
        compose.SCORE_SOURCE: profile["score_relay_followup"]["parent_score_row"]["after"],
        compose.VAULT_SOURCE: profile["empty_vault_followup"]["parent_host_row"]["after"],
        compose.ITEM_SOURCE: profile["item_cleanup_followup"]["parent_item_row"]["after"],
    }
    source_names = {"ServerScriptService/EGGRUMBLE_" + name + ".luau" for name in contract["modules_in_load_order"]}
    for case, result in zip(matrix, summary["results"], strict=True):
        group, role, mode = (case[key] for key in ("group", "role", "mode"))
        kind, variant = group.split("_", 1)
        relative = f"matrix/{group}/{role}/{mode}"
        prefix = folder / relative
        raw = {name: read(prefix / name) for name in ("receipt.json", "generated.luau", "stdout.log", "stderr.log")}
        require(all(f"{relative}/{name}" not in observed for name in raw), "GUARDIAN_MATRIX_DUPLICATE")
        observed.update({f"{relative}/{name}": digest(payload) for name, payload in raw.items()})
        receipt = compose.strict_json(raw["receipt.json"])
        red = case["expected_exit"] == 1
        row_id = {"group": group, "role": role, "mode": mode, "expected_baseline_red": red,
                  "native_exit_code": case["expected_exit"]}
        require(result == (row_id | {"receipt_path": relative + "/receipt.json",
                                    "receipt": observed[relative + "/receipt.json"]})
                and all(receipt[key] == value for key, value in row_id.items())
                and receipt["expected_process_result"] is True and receipt["exact_case_vector"] is True
                and receipt["expected_exit_code"] == case["expected_exit"]
                and all(receipt[key] == digest(raw[name]) for key, name in
                        (("generated", "generated.luau"), ("stdout", "stdout.log"), ("stderr", "stderr.log"))),
                "GUARDIAN_SCENARIO_RECEIPT:" + relative)
        cases = [line for line in raw["stdout.log"].decode().splitlines() if line.startswith("CASE\t")]
        rows = [line.split("\t", 3) for line in cases]
        require(receipt["cases"] == cases and all(len(row) == 4 for row in rows)
                and [row[1:3] for row in rows] == case["expected_case_vector"]
                and (case["baseline_error"].encode() in raw["stderr.log"] and case["baseline_error"] in cases[-1]
                     if red and cases else not red and not raw["stderr.log"]), "GUARDIAN_MATRIX_OBSERVED_VECTOR")
        spans = list(receipt["full_source_ranges"].values())
        require(receipt["full_source_body_count"] == len(spans) == len(source_names) == 28
                and {span["path"] for span in spans} == source_names, "GUARDIAN_MATRIX_28_SOURCE_BODIES")
        program = raw["generated.luau"]
        end = 0
        for span in sorted(spans, key=lambda row: row["byte_start"]):
            path, first, last = (span[key] for key in ("path", "byte_start", "byte_end_exclusive"))
            expected = (contract["guardian"]["variants"][variant]["input" if kind == "baseline" else "candidate"]
                        if path == guard_source else guardian_context_pins[path])
            body = program[first:last]
            require(end <= first < last <= len(program) and digest(body) == expected ==
                    {key: span[key] for key in ("bytes", "sha256")}
                    and span["line_first"] == program[:first].count(b"\n") + 1
                    and span["line_last"] == span["line_first"] + body.count(b"\n"),
                    "GUARDIAN_MATRIX_SOURCE_SPAN:" + path)
            end = last
        verify_guardian_program_frame(program, receipt["full_source_ranges"], contract, role, mode)
        counts["expected_baseline_failure" if red else
               "candidate_pass" if kind == "candidate" else "baseline_control_pass"] += 1
    require(counts == summary["counts"] == {"expected_baseline_failure": 8, "candidate_pass": 26, "baseline_control_pass": 6}
            and len(observed) == 160 and observed == summary["files"]
            and set(files(folder)) == {*observed, summary_name, contract_name}, "GUARDIAN_MATRIX_COMPLETE")
    return {"native_executions": 40, "unique_scenarios": 13, "counts": dict(counts),
            "receipt": digest(read(summary_path))}, {"guardian_target/" + name for name in files(folder)}


def verify_relay_presentation(native, root, profile, build, aggregate, context):
    evidence = native / "relay_presentation"
    repair = profile["relay_presentation_followup"]
    client = read(root / compose.RELAY_ELIGIBILITY_OFF / "sources" / compose.HUD_SOURCE)
    begin = b"task.spawn(function()\n"
    end = b"\nend)\n"
    offset = client.index(begin)
    hud_start = client.index(b'local Players=game:GetService("Players")\n')
    selected = client[offset:hud_start]
    require(offset == repair["client_start"] and hud_start == repair["client_end"]
            and selected.startswith(begin) and selected.endswith(end)
            and digest(selected[len(begin):-len(end)]) == repair["client_original_body"]
            and digest(selected) == repair["client_wrapper"]
            and digest(client) == profile["relay_eligibility_followup"]["rows"][compose.HUD_SOURCE]["parent"]["after"],
            "RELAY_PRESENTATION_VERIFIED_ORIGINAL_AND_STARTUP")
    fixture = read(HERE / "native/relay_presentation_cases.luau")
    first, separator, rest = fixture.partition(b"-- @RELAY_PRESENTATION_MOUNTED@\n")
    require(separator and separator not in rest and digest(fixture) == repair["native_case"],
            "RELAY_PRESENTATION_VERIFIED_FIXTURE")
    actual, out, err = (read(evidence / name) for name in ("generated.luau","stdout.log","stderr.log"))
    require(actual == first + selected + rest and digest(actual) == repair["native_program"]
            and digest(out.replace(b"\r\n",b"\n")) == {
                "bytes": 1567, "sha256": "07337ca815254902b5b8e9b4359787ffe175bdae73cc59d1487c07aff4cd0473"}
            and err == b"", "RELAY_PRESENTATION_VERIFIED_PROGRAM_AND_RUN")
    receipt_file = evidence / "receipt.json"
    receipt = {"source": digest(client), "native": build["binary_after_suites"], "execution_context": context,
               "generated": digest(actual), "stdout": digest(out), "stderr": digest(err), "exit": 0, "cases": 22}
    pin = digest(read(receipt_file))
    names = {"generated.luau","stdout.log","stderr.log","receipt.json"}
    require(data(receipt_file) == receipt and aggregate["relay_presentation"] == pin and set(files(evidence)) == names,
            "RELAY_PRESENTATION_VERIFIED_RECEIPT")
    return {"receipt": pin, "client_region_only": True, "cases": 22}, {"relay_presentation/" + name for name in names}


def verify_score_regressions(native, root, lock, build, aggregate, context):
    folder = native / "score_relay"
    source = read(root / "sources" / compose.SCORE_SOURCE)
    source_pin = digest(source)
    require(source_pin == lock["sources"][compose.SCORE_SOURCE]["after"], "SCORE_VERIFIED_SOURCE_PIN")
    expected = {
        "EGGRUMBLE_ScoreBalance": b"EGGRUMBLE_V3_MATCH_RESULTS_NATIVE_PASS assertions=107\n",
        "EGGRUMBLE_RelayScoreRegression": b"EGGRUMBLE_RELAY_SCORE_NATIVE_REGRESSION_PASS assertions=16\n",
    }
    donor = compose.REPO / compose.SCORE_REGRESSION_DONOR / "native"
    repair = lock["score_relay_followup"]
    require(set(repair["regression_specs"]) == {f"native/{item}.spec.luau" for item in expected},
            "SCORE_VERIFIED_SPEC_SET")
    results = {}
    required_files = {"receipt.json"}
    for prefix, marker in expected.items():
        name = prefix + ".spec.luau"
        filenames = [prefix + suffix for suffix in (".luau", ".stdout.log", ".stderr.log")]
        program, stdout, stderr = (read(folder / filename) for filename in filenames)
        spec = read(donor / name)
        require(digest(spec) == repair["regression_specs"]["native/" + name], "SCORE_VERIFIED_SPEC_PIN")
        exact = b"\n".join((b"local score=(function()", source, b"end)()", b"local spec=(function()",
                            spec, b"end)()", b"assert(spec(score))", b""))
        require(program == exact and stdout == marker.replace(b"\n", os.linesep.encode()) and stderr == b"",
                "SCORE_VERIFIED_EXACT_PROGRAM_AND_RUN")
        required_files.update(filenames)
        results[name] = {"spec": digest(spec), "program": digest(program), "stdout": digest(stdout),
                         "stderr": digest(stderr), "exit": 0}
    receipt_path = folder / "receipt.json"
    receipt = {"source": source_pin, "native": build["binary_after_suites"], "execution_context": context,
               "results": results}
    require(data(receipt_path) == receipt and aggregate["score_relay_regressions"] == digest(read(receipt_path))
            and set(files(folder)) == required_files, "SCORE_VERIFIED_RECEIPT_AND_FILES")
    return {"receipt": digest(read(receipt_path)), "independent_spec_count": 2, "assertions": 123,
            "full_score_body": source_pin}, {"score_relay/" + name for name in required_files}


def verify_br_canyon(native, root, profile, build, aggregate, context, adapter):
    folder = native / "br_canyon"
    program, pins = adapter.br_canyon_program(root / "sources", profile, compose)
    output = read(folder / "stdout.log")
    stderr = read(folder / "stderr.log")
    require(read(folder / "generated.luau") == program and not stderr
            and output.decode().splitlines() == [
                "PASS TEAM CENTER_AND_FOUR_LANES",
                "PASS TEAM 16_CASTLE_FRONT_APPROACHES",
                "PASS BATTLE_ROYALE CENTER_AND_FOUR_LANES",
                "PASS BATTLE_ROYALE 16_CASTLE_FRONT_APPROACHES"], "BR_CANYON_NATIVE_PROGRAM_AND_RUN")
    receipt = folder / "receipt.json"
    wanted = {"sources": pins, "native": build["binary_after_suites"], "execution_context": context,
              "generated": digest(program), "stdout": digest(output), "stderr": digest(stderr),
              "exit": 0, "cases": 4}
    names = {"generated.luau", "stdout.log", "stderr.log", "receipt.json"}
    pin = digest(read(receipt))
    require(data(receipt) == wanted and aggregate["br_canyon"] == pin
            and set(files(folder)) == names, "BR_CANYON_NATIVE_RECEIPT")
    return {"receipt": pin, "placement_cases": 4, "physical_studio": "NOT_TESTED"}, {
        "br_canyon/" + name for name in names
    }


def verify_role_readability(native, root, profile, build, aggregate, context):
    spec = importlib.util.spec_from_file_location("union22_role_readability_verify", HERE / "native/role_readability_native.py")
    contract = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(contract)
    path = native / "role_readability"
    receipt = path / "receipt.json"
    expected = contract.check_runs(root / "sources", path, profile, compose, build["binary_after_suites"], context)
    pin = digest(read(receipt))
    require(data(receipt) == expected and aggregate["role_readability"] == pin
            and set(files(path)) == contract.FILE_NAMES, "ROLE_READABILITY_EXACT_NATIVE")
    return {"receipt": pin, "motion_cases": 20, "weapon_rows": 96, "studio": "NOT_TESTED"}, {
        "role_readability/" + name for name in contract.FILE_NAMES
    }


def verify_field_prompt(native, root, lock, build, aggregate, context):
    spec = importlib.util.spec_from_file_location("union22_field_prompt_verify", HERE / "native/field_prompt_native.py")
    contract = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(contract)
    folder = native / "field_prompt"
    receipt = folder / "receipt.json"
    expected = contract.verify(root / "sources", folder, build["binary_before_suites"], context, lock, compose)
    require(data(receipt) == expected and aggregate["field_prompt"] == digest(read(receipt))
            and set(files(folder)) == contract.FILE_NAMES, "FIELD_PROMPT_EXACT_NATIVE")
    return expected, {"field_prompt/" + name for name in contract.FILE_NAMES}


def verify_foliage_readability(native, root, lock, build, aggregate, context):
    spec = importlib.util.spec_from_file_location("union22_foliage_verify", HERE / "native/foliage_readability.py")
    contract = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(contract)
    folder = native / "foliage_readability"
    report = contract.check(root / "sources", folder, build["binary_before_suites"], context, lock, compose)
    name = "receipt.json"
    require(aggregate["foliage_readability"] == digest(read(folder / name))
            and set(files(folder)) == {name}, "FOLIAGE_EXACT_NATIVE")
    return report, {"foliage_readability/" + name}


def verify_guardian_wall(native, root, lock, build, aggregate, context):
    spec = importlib.util.spec_from_file_location("union22_guardian_wall_verify", HERE / "native/guardian_wall.py")
    contract = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(contract)
    folder = native / "guardian_wall"
    report = contract.check(root / "sources", folder, build["binary_before_suites"], context, lock, compose)
    receipt = folder / "receipt.json"
    require(report == data(receipt) and digest(read(receipt)) == aggregate["guardian_wall"]
            and set(files(folder)) == contract.FILE_NAMES, "GUARDIAN_WALL_EXACT_NATIVE")
    return report, {"guardian_wall/" + name for name in contract.FILE_NAMES}


def verify_combat_visual(native, root, lock, build, aggregate, context):
    spec = importlib.util.spec_from_file_location("union22_combat_visual_verify", HERE / "native/combat_visual_native.py")
    contract = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(contract)
    folder = native / "combat_visual"
    receipt = folder / "receipt.json"
    expected, *_ = contract.expected(root / "sources", build["binary_before_suites"], context, lock, compose)
    require(data(receipt) == expected and digest(read(receipt)) == aggregate["combat_visual"]
            and set(files(folder)) == {"receipt.json"}, "COMBAT_VISUAL_EXACT_NATIVE")
    return expected, {"combat_visual/receipt.json"}


def verify_growth_musou_native(native, root, lock, build, aggregate, context):
    spec = importlib.util.spec_from_file_location("union22_growth_musou_verify", HERE / "native/growth_musou.py")
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    growth, aura, aura_fixture = adapter.load_contracts(lock, compose)
    authored = growth.load_native_contract()
    historic = growth.validate_historical_inputs(authored["historical_inputs"])
    original = json.loads(historic[growth.HISTORICAL_PREFIX + "/INPUT_LOCK.json"])
    binary = build["binary_before_suites"]
    folder = native / "growth_musou"
    packed = files(folder)
    receipt = data(folder / "receipt.json")
    require(digest(read(folder / "receipt.json")) == aggregate["growth_musou"], "GROWTH_MUSOU_AGGREGATE")
    expected_files = {"receipt.json"}
    aura_status = {}
    count = 0
    for label, sources, pins in adapter.profile_sources(root, lock, compose):
        branch = "positive" if label == "ON" else "negative"
        expected = {f"{label}_legacy_{name}": (
                        {"exit": 0, "cases": [[case, "PASS"] for case in suite["expected_case_names"]]}, 28)
                    for name, suite in original["suites"].items()}
        for name in authored["server_profiles"][label]:
            suite = authored["server_variants"][name]
            expected[f"{label}_server_{name}"] = (suite[branch], 28 + len(suite.get("extra_modules", [])))
        expected[f"{label}_ui"] = (authored["ui"][branch], 31)
        for name, (vector, body_count) in expected.items():
            result = folder / name
            claim = data(result / "receipt.json")
            program = read(result / "generated.luau")
            stdout = read(result / "stdout.log")
            stderr = read(result / "stderr.log")
            lines = stdout.decode("utf-8").splitlines()
            cases, _ = growth.vector(lines, "CASE")
            assertions, _ = growth.vector(lines, "EXPECTATION")
            failure = vector["exit"] != 0
            require(claim["generated"] == digest(program) and claim["native"] == binary
                    and claim["source_profile"] == pins and len(claim["full_body_byte_ranges"]) == body_count
                    and claim["stdout"] == digest(stdout) and claim["stderr"] == digest(stderr)
                    and claim["native_exit"] == claim["expected_exit"] == vector["exit"]
                    and cases == claim["actual_cases"] == vector["cases"]
                    and assertions == claim["actual_expectations"] == vector.get("expectations", [])
                    and claim["status"] == ("PASS_FIXED_NEGATIVE_CONTROL" if failure else "PASS_NATIVE_ONLY")
                    and not any(line.startswith("WARN\t") for line in lines), "GROWTH_MUSOU_VECTOR:" + name)
            require(vector["failure_marker"].encode() in stdout + stderr if failure else not stderr,
                    "GROWTH_MUSOU_NATIVE_EXIT_EVIDENCE:" + name)
            end = 0
            for relative, span in sorted(claim["full_body_byte_ranges"].items(), key=lambda item: item[1]["start"]):
                lo, hi = span["start"], span["end"]
                require(end <= lo < hi <= len(program) and program[lo:hi] == read(sources / relative)
                        and digest(program[lo:hi]) == pins[relative], "GROWTH_MUSOU_BODY_SPAN:" + relative)
                end = hi
            expected_files.update(f"{name}/{file}" for file in
                                  ("receipt.json", "generated.luau", "stdout.log", "stderr.log"))
            count += 1
        name = "candidate" if label == "ON" else "baseline"
        prefix = "aura/" + name
        client, controller = sources / adapter.CLIENT, sources / adapter.CONTROLLER
        program, _ = aura.build_program(aura_fixture, read(client), read(controller), client, controller)
        require(program == read(folder / (prefix + ".exact.luau")), "MUSOU_AURA_EXACT_PROGRAM")
        output = read(folder / (prefix + ".stdout.txt")).decode("utf-8").splitlines()
        stderr = read(folder / (prefix + ".stderr.txt"))
        rows = [line.split("\t", 2) for line in output if line.startswith(("PASS\t", "FAIL\t"))]
        names = [row[1] for row in rows]
        failed = frozenset(row[1] for row in rows if row[0] == "FAIL")
        require(len(names) == len(set(names)) and set(names) == aura.EXPECTED_CASES
                and failed == (frozenset() if label == "ON" else aura.EXPECTED_BASELINE_FAILURES)
                and (b"Lifecycle regression expectations failed" in stderr if failed else not stderr),
                "MUSOU_AURA_EXPECTED_VECTOR")
        aura_status[name] = {"passed": len(rows) - len(failed), "expected_failure": len(failed)}
        expected_files.update(prefix + extension for extension in (".exact.luau", ".stdout.txt", ".stderr.txt"))
    require(count == 24 and len(expected_files) == 103 and set(packed) == expected_files
            and receipt == {"context": context, "binary": binary, "source_only": True, "growth_runs": count,
                            "aura": aura_status, "files": {p: pin for p, pin in packed.items() if p != "receipt.json"}},
            "GROWTH_MUSOU_NATIVE_COMPLETE")
    return receipt, {"growth_musou/" + name for name in expected_files}


def verify_art_polish_skillfx(native, root, lock, build, aggregate, context):
    spec = importlib.util.spec_from_file_location("union22_art_polish_skillfx_verify",
                                                 HERE / "native/art_polish_skillfx.py")
    contract = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(contract)
    folder = native / "art_polish_skillfx"
    receipt = folder / "receipt.json"
    expected = contract.observed(root / "sources", folder, build["binary_before_suites"], context, lock, compose)
    require(set(files(folder)) == contract.FILES and data(receipt) == expected
            and digest(read(receipt)) == aggregate["art_polish_skillfx"], "ART_POLISH_SKILLFX_RECEIPT")
    return expected, {"art_polish_skillfx/" + name for name in contract.FILES}


def verify_mage_contact_native(native, root, lock, build, aggregate, context):
    folder = native / "mage_contact"
    sys.path.insert(0, str(HERE / "native"))
    try:
        from mage_contact_native import collect

        expected, evidence = collect(root, folder, build["binary_before_suites"], context, lock, compose)
    finally:
        sys.path.pop(0)
    receipt = folder / "receipt.json"
    require(set(files(folder)) == evidence and data(receipt) == expected
            and digest(read(receipt)) == aggregate["mage_contact"], "MAGE_CONTACT_EXACT_RECEIPT")
    return expected, {"mage_contact/" + name for name in evidence}


def verify_relay_eligibility_native(native, root, lock, build, aggregate, context):
    spec = importlib.util.spec_from_file_location("union22_relay_eligibility_verify",
                                                  HERE / "native/relay_eligibility_native.py")
    contract = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(contract)
    folder = native / "relay_eligibility"
    receipt = folder / "receipt.json"
    expected, evidence = contract.observe(root, folder, build["binary_before_suites"], context, lock, compose)
    require(set(files(folder)) == evidence and data(receipt) == expected
            and digest(read(receipt)) == aggregate["relay_eligibility"], "RELAY_ELIGIBILITY_EXACT_RECEIPT")
    return expected, {"relay_eligibility/" + name for name in evidence}


def verify_private_touch_native(native, root, lock, build, aggregate, context):
    spec = importlib.util.spec_from_file_location("union22_private_touch_verify", HERE / "native/private_touch_native.py")
    contract = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(contract)
    folder = native / "private_touch"
    receipt = folder / "receipt.json"
    expected = contract.observe(root / "sources", folder, Path(build["binary_path"]),
                                build["binary_before_suites"], context, lock, compose)
    require(set(files(folder)) == contract.FILES and data(receipt) == expected
            and digest(read(receipt)) == aggregate["private_touch"], "PRIVATE_TOUCH_EXACT_RECEIPT")
    return expected, {"private_touch/" + name for name in contract.FILES}


def verify_portrait_native(native, root, lock, build, aggregate, context):
    spec = importlib.util.spec_from_file_location("union22_portrait_verify", HERE / "native/portrait_native.py")
    contract = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(contract)
    folder = native / "portrait"
    receipt = folder / "receipt.json"
    expected = contract.observe(root / "sources", folder, Path(build["binary_path"]),
                                build["binary_before_suites"], context, lock, compose)
    require(set(files(folder)) == contract.FILES and data(receipt) == expected
            and digest(read(receipt)) == aggregate["portrait"], "PORTRAIT_EXACT_RECEIPT")
    return expected, {"portrait/" + name for name in contract.FILES}


def verify_team_win_rule_native(native, root, lock, build, aggregate, context):
    spec = importlib.util.spec_from_file_location("union22_team_win_rule_verify", HERE / "native/team_win_rule_native.py")
    contract = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(contract)
    folder = native / "team_win_rule"
    receipt = folder / "receipt.json"
    expected = contract.observe(root / "sources", folder, Path(build["binary_path"]),
                                build["binary_before_suites"], context, lock, compose)
    require(set(files(folder)) == contract.FILES and data(receipt) == expected
            and digest(read(receipt)) == aggregate["team_win_rule"], "TEAM_WIN_RULE_EXACT_RECEIPT")
    return expected, {"team_win_rule/" + name for name in contract.FILES}


def verify_fractional_hp_native(native, root, lock, build, aggregate, context):
    spec = importlib.util.spec_from_file_location("union22_fractional_hp_verify", HERE / "native/fractional_hp_native.py")
    contract = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(contract)
    folder = native / "fractional_hp"
    receipt = folder / "receipt.json"
    expected = contract.observe(root / "sources", folder, Path(build["binary_path"]),
                                build["binary_before_suites"], context, lock, compose)
    require(set(files(folder)) == contract.FILES and data(receipt) == expected
            and digest(read(receipt)) == aggregate["fractional_hp"], "FRACTIONAL_HP_EXACT_RECEIPT")
    return expected, {"fractional_hp/" + name for name in contract.FILES}


def verify_native(native, root, lock, context):
    """Verify concrete body ranges, case logs and new-build receipt, not PASS alone."""
    native = Path(native).resolve()
    input_lock_path = HERE / "native/INPUT_LOCK.json"
    # The adapter exposes its literal lock digest; source bytes are part of this candidate.
    spec = importlib.util.spec_from_file_location("union22_native_contract", HERE / "native/run_profile.py")
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    projectile_spec = importlib.util.spec_from_file_location(
        "union22_mage_projectiles_verify", HERE / "native/mage_projectiles/__init__.py")
    projectiles = importlib.util.module_from_spec(projectile_spec)
    projectile_spec.loader.exec_module(projectiles)
    water_chain_spec = importlib.util.spec_from_file_location(
        "union22_mage_water_chain_verify", HERE / "native/mage_water_chain/__init__.py")
    water_chain = importlib.util.module_from_spec(water_chain_spec)
    water_chain_spec.loader.exec_module(water_chain)
    ninja_s4_spec = importlib.util.spec_from_file_location(
        "union22_ninja_s4_verify", HERE / "native/ninja_s4/__init__.py")
    ninja_s4 = importlib.util.module_from_spec(ninja_s4_spec)
    ninja_s4_spec.loader.exec_module(ninja_s4)
    stage_native = {}
    for name in ("wing_warrior", "fixed_cues", "field_loadouts", "first90_role", "return_convert", "ground_night",
                 "cover_orders", "mage_field_arcs", "eclipse_sweep", "builder_forms", "footing_wards",
                 "ninja_beast_castle", "spring_mist_forest", "ninja_steps_objectives", "warrior_field_horde", "trapper_cast_audio", "zombie_formation_camera"):
        selected_spec = importlib.util.spec_from_file_location(
            "union22_" + name + "_verify", HERE / ("native/" + name + "/__init__.py"))
        contract = importlib.util.module_from_spec(selected_spec)
        selected_spec.loader.exec_module(contract)
        stage_native[name] = contract
    stage_native_files = sum(len(contract.FILES) for contract in stage_native.values())
    stage_native_runs = sum(contract.PROCESS_COUNT for contract in stage_native.values())
    require(digest(read(input_lock_path))["sha256"] == adapter.INPUT_LOCK_SHA256, "NATIVE_LOCK_IDENTITY")
    pins = data(input_lock_path)
    require(pins.get("schema") == "UNION22_NATIVE_DUAL_CLEAR_LOS_SOURCE_BUILD_INPUTS_V3"
            and pins.get("sources") == {p: row["after"] for p, row in lock["sources"].items()}, "NATIVE_SOURCE_LOCK")
    variants = {"combined_clear_los": "BOUNDED_CLEAR_LOS_APPROACH_INPUT",
                "objective_full_clear_los": "BOUNDED_CLEAR_LOS_MELEE_APPROACH_INPUT",
                "beast_target_selection": "GQ618_TARGET_ELIGIBILITY_CASES"}
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
    require(aggregate.get("source_count_executed_full_body_basis") == "original_dual28_suites_and_beast_target_selection"
            and aggregate.get("full_body_coverage") == {
                "original_dual28": 28, "beast_target_selection": 28, "bot_vault_each": 16, "distinct_server_union": 30,
                "selected_hud_policy": 1, "hud_policy_separate": True, "distinct_all_full_bodies": 31,
                "hud_client_runtime_executed_in_original_suites": False,
                "growth_ui_full_bodies_each": 31, "hud_client_runtime_executed_in_growth": True}
            and aggregate.get("native_process_count") == 99 + projectiles.PROCESS_COUNT
            + water_chain.PROCESS_COUNT + ninja_s4.PROCESS_COUNT + stage_native_runs
            and aggregate.get("native_evidence_file_count") == 316 + len(projectiles.FILES)
            + len(water_chain.FILES) + len(ninja_s4.FILES) + stage_native_files,
            "NATIVE_AGGREGATE_BODY_AND_PROCESS_COVERAGE")
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
                and result.get("fixture_pins") == (
                    pins["fixtures"] | {"beast_fixture.luau": suite["fixture"]}
                    if suite_name == "beast_target_selection" else pins["fixtures"]
                ), "NATIVE_SUITE_RECEIPT_FACTS")
        require(result.get("source_profile") == pins["sources"]
                and result.get("runner") == digest(read(HERE / "native/run_profile.py")), "NATIVE_SUITE_SOURCE_RUNNER_BINDING")
        require(aggregate.get("suites", {}).get(suite_name) == digest(read(folder / "receipt.json")), "NATIVE_SUITE_BINDING")
        results[suite_name] = {"case_count": len(parts), "receipt": digest(read(folder / "receipt.json"))}
    require(set(results) == set(variants), "NATIVE_ALL_ORIGINAL_PLUS_BEAST_SUITES")
    layout = verify_selected_hud_layout(native, root, pins, build, aggregate, context)
    bot = verify_bot_vault_supplement(native, root, pins, build, aggregate, context)
    expected_files = set(build["evidence_files"]) | {"build_receipt.json", "receipt.json"}
    expected_files |= {suite + "/" + name for suite in pins["suites"]
                       for name in ("generated.luau", "stdout.log", "stderr.log", "receipt.json")}
    expected_files |= {"selected_hud_layout/" + name for name in layout["files"]}
    expected_files |= {"bot_vault/" + name for name in bot["files"]}
    score, score_files = verify_score_regressions(native, root, lock, build, aggregate, context)
    expected_files |= score_files
    relay, relay_files = verify_relay_presentation(native, root, lock, build, aggregate, context)
    expected_files |= relay_files
    canyon, canyon_files = verify_br_canyon(native, root, lock, build, aggregate, context, adapter)
    expected_files |= canyon_files
    role, role_files = verify_role_readability(native, root, lock, build, aggregate, context)
    expected_files |= role_files
    field_prompt, field_files = verify_field_prompt(native, root, lock, build, aggregate, context)
    expected_files |= field_files
    foliage, foliage_files = verify_foliage_readability(native, root, lock, build, aggregate, context)
    expected_files |= foliage_files
    wall, wall_files = verify_guardian_wall(native, root, lock, build, aggregate, context)
    expected_files |= wall_files
    combat_visual, visual_files = verify_combat_visual(native, root, lock, build, aggregate, context)
    expected_files |= visual_files
    growth_musou, growth_files = verify_growth_musou_native(native, root, lock, build, aggregate, context)
    expected_files |= growth_files
    art_polish_skillfx, skillfx_files = verify_art_polish_skillfx(native, root, lock, build, aggregate, context)
    expected_files |= skillfx_files
    mage_contact, mage_files = verify_mage_contact_native(native, root, lock, build, aggregate, context)
    expected_files |= mage_files
    relay_eligibility, eligibility_files = verify_relay_eligibility_native(native, root, lock, build, aggregate, context)
    expected_files |= eligibility_files
    private_touch, touch_files = verify_private_touch_native(native, root, lock, build, aggregate, context)
    expected_files |= touch_files
    portrait, portrait_files = verify_portrait_native(native, root, lock, build, aggregate, context)
    expected_files |= portrait_files
    team_win_rule, team_win_rule_files = verify_team_win_rule_native(native, root, lock, build, aggregate, context)
    expected_files |= team_win_rule_files
    hp, hp_files = verify_fractional_hp_native(native, root, lock, build, aggregate, context)
    expected_files |= hp_files
    projectile_folder = native / "mage_projectiles"
    projectile_receipt = projectile_folder / "receipt.json"
    projectile_result = projectiles.observe(root / "sources", projectile_folder, Path(build["binary_path"]),
                                            build["binary_before_suites"], context, lock, compose)
    require(set(files(projectile_folder)) == projectiles.FILES
            and data(projectile_receipt) == projectile_result
            and digest(read(projectile_receipt)) == aggregate["mage_projectiles"], "MAGE_PROJECTILES_EXACT_RECEIPT")
    expected_files |= {"mage_projectiles/" + name for name in projectiles.FILES}
    water_chain_folder = native / "mage_water_chain"
    water_chain_receipt = water_chain_folder / "receipt.json"
    water_chain_result = water_chain.observe(root / "sources", water_chain_folder, Path(build["binary_path"]),
                                             build["binary_before_suites"], context, lock, compose)
    require(set(files(water_chain_folder)) == water_chain.FILES
            and data(water_chain_receipt) == water_chain_result
            and digest(read(water_chain_receipt)) == aggregate["mage_water_chain"], "MAGE_WATER_CHAIN_EXACT_RECEIPT")
    expected_files |= {"mage_water_chain/" + name for name in water_chain.FILES}
    ninja_s4_folder = native / "ninja_s4"
    ninja_s4_receipt = ninja_s4_folder / "receipt.json"
    ninja_s4_result = ninja_s4.observe(root / "sources", ninja_s4_folder, Path(build["binary_path"]),
                                        build["binary_before_suites"], context, lock, compose)
    require(set(files(ninja_s4_folder)) == ninja_s4.FILES
            and data(ninja_s4_receipt) == ninja_s4_result
            and digest(read(ninja_s4_receipt)) == aggregate["ninja_s4"], "NINJA_S4_EXACT_RECEIPT")
    expected_files |= {"ninja_s4/" + name for name in ninja_s4.FILES}
    stage_native_results = {}
    for name, contract in stage_native.items():
        folder = native / name
        receipt = folder / "receipt.json"
        observed = contract.observe(root / "sources", folder, Path(build["binary_path"]),
                                    build["binary_before_suites"], context, lock, compose)
        require(set(files(folder)) == contract.FILES and data(receipt) == observed
                and digest(read(receipt)) == aggregate[name], name.upper() + "_EXACT_RECEIPT")
        expected_files |= {name + "/" + filename for filename in contract.FILES}
        stage_native_results[name] = observed
    guardian, guardian_files = verify_guardian_target(native, root, lock, pins, build, aggregate, context)
    require(len(expected_files) == 316 + len(projectiles.FILES) + len(water_chain.FILES)
            + len(ninja_s4.FILES) + stage_native_files
            and set(files(native)) == expected_files | guardian_files,
            "NATIVE_RESULT_FILE_SET")
    return {"results": results, "build": build, "payload": files(native), "aggregate": aggregate,
            "guardian_target_diagnostic": guardian,
            "score_relay_regressions": score,
            "relay_presentation": relay,
            "br_canyon": canyon,
            "role_readability": role,
            "field_prompt": field_prompt,
            "foliage_readability": foliage,
            "guardian_wall": wall,
            "combat_visual": combat_visual,
            "growth_musou": growth_musou,
            "art_polish_skillfx": art_polish_skillfx,
            "mage_contact": mage_contact,
            "relay_eligibility": relay_eligibility,
            "private_touch": private_touch,
            "portrait": portrait,
            "team_win_rule": team_win_rule,
            "fractional_hp": hp,
            "mage_projectiles": projectile_result,
            "mage_water_chain": water_chain_result,
            "ninja_s4": ninja_s4_result,
            **stage_native_results,
            "selected_hud_layout": {key: value for key, value in layout.items() if key != "files"},
            "bot_vault_supplement": {key: value for key, value in bot.items() if key != "files"}}


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
    score_donor = compose.REPO / compose.SCORE_REGRESSION_DONOR / "native"
    score_donor_before = files(score_donor)
    prior_before = compose.load_inputs(base, reports)["snapshot"]
    def unchanged(phase):
        require(files(root) == before and files(native) == native_before
                and files(HERE) == contract_before
                and files(score_donor) == score_donor_before
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
    retained_build_files = (compose.PROJECT, compose.PLACE, compose.RECEIPT, compose.OFF_ARCHIVE,
                            compose.HUD_OFF_ARCHIVE, compose.BOT_OFF_ARCHIVE, compose.BEAST_OFF_ARCHIVE,
                            compose.GUARDIAN_OFF_ARCHIVE, compose.ITEM_OFF_ARCHIVE, compose.VAULT_OFF_ARCHIVE,
                            compose.CASTLE_OFF_ARCHIVE, compose.SCORE_OFF_ARCHIVE,
                            compose.RELAY_PRESENTATION_OFF_ARCHIVE, compose.BR_CANYON_OFF_ARCHIVE,
                            compose.ROLE_READABILITY_OFF_ARCHIVE, compose.FIELD_PROMPT_OFF_ARCHIVE,
                            compose.NEUTRAL_NAMES_OFF_ARCHIVE,
                            compose.GUARDIAN_WALL_OFF_ARCHIVE, compose.COMBAT_VISUAL_OFF_ARCHIVE,
                            compose.GROWTH_MUSOU_OFF_ARCHIVE,
                            compose.ART_POLISH_OFF_ARCHIVE,
                            compose.MAGE_CONTACT_OFF_ARCHIVE,
                            compose.RELAY_ELIGIBILITY_OFF_ARCHIVE, compose.MOGURON_OFF_ARCHIVE,
                            compose.PRIVATE_TOUCH_OFF_ARCHIVE,
                            compose.PORTRAIT_OFF_ARCHIVE, compose.SHOREFOAM_OFF_ARCHIVE,
                            compose.TEAM_WIN_RULE_OFF_ARCHIVE, compose.FRACTIONAL_HP_OFF_ARCHIVE,
                            compose.MAGE_PROJECTILES_OFF_ARCHIVE, compose.MAGE_WATER_CHAIN_OFF_ARCHIVE,
                            compose.NINJA_S4_OFF_ARCHIVE, compose.WING_WARRIOR_OFF_ARCHIVE,
                            compose.FIELD_LOADOUTS_OFF_ARCHIVE, compose.RETURN_CONVERT_OFF_ARCHIVE,
                            compose.GROUND_NIGHT_OFF_ARCHIVE, compose.COVER_ORDERS_OFF_ARCHIVE,
                            compose.MAGE_FIELD_ARCS_OFF_ARCHIVE, compose.ECLIPSE_SWEEP_OFF_ARCHIVE,
                            compose.BUILDER_FORMS_OFF_ARCHIVE, compose.FOOTING_WARDS_OFF_ARCHIVE,
                            compose.NINJA_BEAST_CASTLE_OFF_ARCHIVE, compose.SPRING_MIST_FOREST_OFF_ARCHIVE,
                            compose.NINJA_STEPS_OBJECTIVES_OFF_ARCHIVE,
                            compose.WARRIOR_FIELD_HORDE_OFF_ARCHIVE,
                            compose.TRAPPER_CAST_AUDIO_OFF_ARCHIVE,
                            compose.ZOMBIE_FORMATION_CAMERA_OFF_ARCHIVE,
                            "CORE_BUILD_REPORT.json")
    expected_stage = {name: pin for name, pin in before.items()
                      if name.startswith(("sources/", "prior_boundary/"))
                      or name in retained_build_files}
    expected_stage.update({"native_evidence/" + name: pin for name, pin in native_before.items()})
    expected_stage["UNION22_PROFILE_LOCK.json"] = digest(profile_before)
    stage = Path(tempfile.mkdtemp(prefix=".union22-delivery-", dir=root.parent))
    try:
        for relative in ("sources", "prior_boundary"):
            shutil.copytree(root / relative, stage / relative)
        for name in retained_build_files:
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
            "source_count": 69, "changed_sources": 37, "unchanged_sources": 32, "instances": 75,
            "current_place": verified["lock"]["final_place"], "inverse_place": verified["lock"]["prior_place"],
            "inverse_archive_extracted_members": len(verified["archive_members"]),
            "followup_repair": verified["lock"]["followup_repair"],
            "hud_only_current_rc_inverse_place": verified["lock"]["followup_repair"]["current_place"],
            "hud_only_current_rc_inverse_archive": digest(read(root / compose.HUD_OFF_ARCHIVE)),
            "hud_only_current_rc_inverse_archive_members": 71,
            "hud_stage_changed_sources_from_current_rc": 1, "hud_stage_unchanged_sources_from_current_rc": 68,
            "bot_followup_repair": verified["lock"]["bot_followup_repair"],
            "beast_followup_repair": verified["lock"]["beast_followup_repair"],
            "beast_only_h72_parent_inverse_place": verified["lock"]["beast_followup_repair"]["parent_place"],
            "beast_only_h72_parent_inverse_archive": digest(read(root / compose.BEAST_OFF_ARCHIVE)),
            "beast_only_h72_parent_inverse_archive_members": 71,
            "guardian_followup_repair": verified["lock"]["guardian_followup_repair"],
            "guardian_only_beast_parent_inverse_place": verified["lock"]["guardian_followup_repair"]["parent_place"],
            "guardian_only_beast_parent_inverse_archive": digest(read(root / compose.GUARDIAN_OFF_ARCHIVE)),
            "guardian_only_beast_parent_inverse_archive_members": 71,
            "item_cleanup_followup": verified["lock"]["item_cleanup_followup"],
            "item_cleanup_only_inverse_place": verified["lock"]["item_cleanup_followup"]["parent_place"],
            "item_cleanup_only_inverse_archive": digest(read(root / compose.ITEM_OFF_ARCHIVE)),
            "item_cleanup_only_inverse_archive_members": 71,
            "empty_vault_followup": verified["lock"]["empty_vault_followup"],
            "empty_vault_only_inverse_place": verified["lock"]["empty_vault_followup"]["parent_place"],
            "empty_vault_only_inverse_archive": digest(read(root / compose.VAULT_OFF_ARCHIVE)),
            "empty_vault_only_inverse_archive_members": 71,
            "castle_release_stock_followup": verified["lock"]["castle_release_stock_followup"],
            "castle_release_stock_inverse_place": verified["lock"]["castle_release_stock_followup"]["parent_place"],
            "castle_release_stock_inverse_archive": digest(read(root / compose.CASTLE_OFF_ARCHIVE)),
            "castle_release_stock_inverse_archive_members": 71,
            "score_relay_followup": verified["lock"]["score_relay_followup"],
            "score_relay_inverse_place": verified["lock"]["score_relay_followup"]["parent_place"],
            "score_relay_inverse_archive": digest(read(root / compose.SCORE_OFF_ARCHIVE)),
            "score_relay_inverse_archive_members": 71,
            "relay_presentation_followup": verified["lock"]["relay_presentation_followup"],
            "relay_presentation_inverse_place": verified["lock"]["relay_presentation_followup"]["parent_place"],
            "relay_presentation_inverse_archive": digest(read(root / compose.RELAY_PRESENTATION_OFF_ARCHIVE)),
            "relay_presentation_inverse_archive_members": 71,
            "br_canyon_followup": verified["lock"]["br_canyon_followup"],
            "br_canyon_inverse_place": verified["lock"]["br_canyon_followup"]["parent_place"],
            "br_canyon_inverse_archive": digest(read(root / compose.BR_CANYON_OFF_ARCHIVE)),
            "br_canyon_inverse_archive_members": 71,
            "role_readability_followup": verified["lock"]["role_readability_followup"],
            "role_readability_inverse_place": verified["lock"]["role_readability_followup"]["parent_place"],
            "role_readability_inverse_archive": digest(read(root / compose.ROLE_READABILITY_OFF_ARCHIVE)),
            "role_readability_inverse_archive_members": 71,
            "field_prompt_followup": verified["lock"]["field_prompt_followup"],
            "field_prompt_inverse_place": verified["lock"]["field_prompt_followup"]["parent_place"],
            "field_prompt_inverse_archive": digest(read(root / compose.FIELD_PROMPT_OFF_ARCHIVE)),
            "field_prompt_inverse_archive_members": 71,
            "neutral_names_followup": verified["lock"]["neutral_names_followup"],
            "neutral_names_inverse_place": verified["lock"]["neutral_names_followup"]["parent_place"],
            "neutral_names_inverse_archive": digest(read(root / compose.NEUTRAL_NAMES_OFF_ARCHIVE)),
            "neutral_names_inverse_archive_members": 71,
            "guardian_wall_followup": verified["lock"]["guardian_wall_followup"],
            "guardian_wall_inverse_place": verified["lock"]["guardian_wall_followup"]["parent_place"],
            "guardian_wall_inverse_archive": digest(read(root / compose.GUARDIAN_WALL_OFF_ARCHIVE)),
            "guardian_wall_inverse_archive_members": 71,
            "combat_visual_followup": verified["lock"]["combat_visual_followup"],
            "combat_visual_inverse_place": verified["lock"]["combat_visual_followup"]["parent_place"],
            "combat_visual_inverse_archive": digest(read(root / compose.COMBAT_VISUAL_OFF_ARCHIVE)),
            "combat_visual_inverse_archive_members": 71,
            "growth_musou_followup": verified["lock"]["growth_musou_followup"],
            "growth_musou_inverse_place": verified["lock"]["growth_musou_followup"]["parent_place"],
            "growth_musou_inverse_archive": digest(read(root / compose.GROWTH_MUSOU_OFF_ARCHIVE)),
            "growth_musou_inverse_archive_members": 71,
            "art_polish_followup": verified["lock"]["art_polish_followup"],
            "art_polish_inverse_place": verified["lock"]["art_polish_followup"]["parent_place"],
            "art_polish_inverse_archive": digest(read(root / compose.ART_POLISH_OFF_ARCHIVE)),
            "art_polish_inverse_archive_members": 71,
            "mage_contact_followup": verified["lock"]["mage_contact_followup"],
            "mage_contact_inverse_place": verified["lock"]["mage_contact_followup"]["parent_place"],
            "mage_contact_inverse_archive": digest(read(root / compose.MAGE_CONTACT_OFF_ARCHIVE)),
            "mage_contact_inverse_archive_members": 71,
            "relay_eligibility_followup": verified["lock"]["relay_eligibility_followup"],
            "relay_eligibility_inverse_place": verified["lock"]["relay_eligibility_followup"]["parent_place"],
            "relay_eligibility_inverse_archive": digest(read(root / compose.RELAY_ELIGIBILITY_OFF_ARCHIVE)),
            "moguron_followup": verified["lock"]["moguron_followup"],
            "moguron_inverse_place": verified["lock"]["moguron_followup"]["parent_place"],
            "moguron_inverse_archive": digest(read(root / compose.MOGURON_OFF_ARCHIVE)),
            "private_touch_followup": verified["lock"]["private_touch_followup"],
            "private_touch_inverse_place": verified["lock"]["private_touch_followup"]["parent_place"],
            "private_touch_inverse_archive": digest(read(root / compose.PRIVATE_TOUCH_OFF_ARCHIVE)),
            "portrait_followup": verified["lock"]["portrait_followup"],
            "portrait_inverse_place": verified["lock"]["portrait_followup"]["parent_place"],
            "portrait_inverse_archive": digest(read(root / compose.PORTRAIT_OFF_ARCHIVE)),
            "shorefoam_followup": verified["lock"]["shorefoam_followup"],
            "shorefoam_inverse_place": verified["lock"]["shorefoam_followup"]["parent_place"],
            "shorefoam_inverse_archive": digest(read(root / compose.SHOREFOAM_OFF_ARCHIVE)),
            "team_win_rule_followup": verified["lock"]["team_win_rule_followup"],
            "team_win_rule_inverse_place": verified["lock"]["team_win_rule_followup"]["parent_place"],
            "team_win_rule_inverse_archive": digest(read(root / compose.TEAM_WIN_RULE_OFF_ARCHIVE)),
            "fractional_hp_followup": verified["lock"]["fractional_hp_followup"],
            "fractional_hp_inverse_place": verified["lock"]["fractional_hp_followup"]["parent_place"],
            "fractional_hp_inverse_archive": digest(read(root / compose.FRACTIONAL_HP_OFF_ARCHIVE)),
            "mage_projectile_followup": verified["lock"]["mage_projectile_followup"],
            "mage_projectile_inverse_place": verified["lock"]["mage_projectile_followup"]["parent_place"],
            "mage_projectile_inverse_archive": digest(read(root / compose.MAGE_PROJECTILES_OFF_ARCHIVE)),
            "mage_water_chain_followup": verified["lock"]["mage_water_chain_followup"],
            "mage_water_chain_inverse_place": verified["lock"]["mage_water_chain_followup"]["parent_place"],
            "mage_water_chain_inverse_archive": digest(read(root / compose.MAGE_WATER_CHAIN_OFF_ARCHIVE)),
            "ninja_s4_followup": verified["lock"]["ninja_s4_followup"],
            "ninja_s4_inverse_place": verified["lock"]["ninja_s4_followup"]["parent_place"],
            "ninja_s4_inverse_archive": digest(read(root / compose.NINJA_S4_OFF_ARCHIVE)),
            "wing_warrior_followup": verified["lock"]["wing_warrior_followup"],
            "wing_warrior_inverse_place": verified["lock"]["wing_warrior_followup"]["parent_place"],
            "wing_warrior_inverse_archive": digest(read(root / compose.WING_WARRIOR_OFF_ARCHIVE)),
            "field_loadouts_followup": verified["lock"]["field_loadouts_followup"],
            "field_loadouts_inverse_place": verified["lock"]["field_loadouts_followup"]["parent_place"],
            "field_loadouts_inverse_archive": digest(read(root / compose.FIELD_LOADOUTS_OFF_ARCHIVE)),
            "return_convert_followup": verified["lock"]["return_convert_followup"],
            "return_convert_inverse_place": verified["lock"]["return_convert_followup"]["parent_place"],
            "return_convert_inverse_archive": digest(read(root / compose.RETURN_CONVERT_OFF_ARCHIVE)),
            "ground_night_followup": verified["lock"]["ground_night_followup"],
            "ground_night_inverse_place": verified["lock"]["ground_night_followup"]["parent_place"],
            "ground_night_inverse_archive": digest(read(root / compose.GROUND_NIGHT_OFF_ARCHIVE)),
            "cover_orders_followup": verified["lock"]["cover_orders_followup"],
            "cover_orders_inverse_place": verified["lock"]["cover_orders_followup"]["parent_place"],
            "cover_orders_inverse_archive": digest(read(root / compose.COVER_ORDERS_OFF_ARCHIVE)),
            "mage_field_arcs_followup": verified["lock"]["mage_field_arcs_followup"],
            "mage_field_arcs_inverse_place": verified["lock"]["mage_field_arcs_followup"]["parent_place"],
            "mage_field_arcs_inverse_archive": digest(read(root / compose.MAGE_FIELD_ARCS_OFF_ARCHIVE)),
            "eclipse_sweep_followup": verified["lock"]["eclipse_sweep_followup"],
            "eclipse_sweep_inverse_place": verified["lock"]["eclipse_sweep_followup"]["parent_place"],
            "eclipse_sweep_inverse_archive": digest(read(root / compose.ECLIPSE_SWEEP_OFF_ARCHIVE)),
            "builder_forms_followup": verified["lock"]["builder_forms_followup"],
            "builder_forms_inverse_place": verified["lock"]["builder_forms_followup"]["parent_place"],
            "builder_forms_inverse_archive": digest(read(root / compose.BUILDER_FORMS_OFF_ARCHIVE)),
            "footing_wards_followup": verified["lock"]["footing_wards_followup"],
            "footing_wards_inverse_place": verified["lock"]["footing_wards_followup"]["parent_place"],
            "footing_wards_inverse_archive": digest(read(root / compose.FOOTING_WARDS_OFF_ARCHIVE)),
            "ninja_beast_castle_followup": verified["lock"]["ninja_beast_castle_followup"],
            "ninja_beast_castle_inverse_place": verified["lock"]["ninja_beast_castle_followup"]["parent_place"],
            "ninja_beast_castle_inverse_archive": digest(read(root / compose.NINJA_BEAST_CASTLE_OFF_ARCHIVE)),
            "spring_mist_forest_followup": verified["lock"]["spring_mist_forest_followup"],
            "spring_mist_forest_inverse_place": verified["lock"]["spring_mist_forest_followup"]["parent_place"],
            "spring_mist_forest_inverse_archive": digest(read(root / compose.SPRING_MIST_FOREST_OFF_ARCHIVE)),
            "ninja_steps_objectives_followup": verified["lock"]["ninja_steps_objectives_followup"],
            "ninja_steps_objectives_inverse_place": verified["lock"]["ninja_steps_objectives_followup"]["parent_place"],
            "ninja_steps_objectives_inverse_archive": digest(read(root / compose.NINJA_STEPS_OBJECTIVES_OFF_ARCHIVE)),
            "warrior_field_horde_followup": verified["lock"]["warrior_field_horde_followup"],
            "warrior_field_horde_inverse_place": verified["lock"]["warrior_field_horde_followup"]["parent_place"],
            "warrior_field_horde_inverse_archive": digest(read(root / compose.WARRIOR_FIELD_HORDE_OFF_ARCHIVE)),
            "trapper_cast_audio_followup": verified["lock"]["trapper_cast_audio_followup"],
            "trapper_cast_audio_inverse_place": verified["lock"]["trapper_cast_audio_followup"]["parent_place"],
            "trapper_cast_audio_inverse_archive": digest(read(root / compose.TRAPPER_CAST_AUDIO_OFF_ARCHIVE)),
            "zombie_formation_camera_followup": verified["lock"]["zombie_formation_camera_followup"],
            "zombie_formation_camera_inverse_place": verified["lock"]["zombie_formation_camera_followup"]["parent_place"],
            "zombie_formation_camera_inverse_archive": digest(read(root / compose.ZOMBIE_FORMATION_CAMERA_OFF_ARCHIVE)),
            "relay_eligibility_inverse_archive_members": 71,
            "changed_sources_from_h72_parent": 1, "unchanged_sources_from_h72_parent": 68,
            "bot_only_hud_parent_inverse_place": verified["lock"]["bot_followup_repair"]["parent_place"],
            "bot_only_hud_parent_inverse_archive": digest(read(root / compose.BOT_OFF_ARCHIVE)),
            "bot_only_hud_parent_inverse_archive_members": 71,
            "changed_sources_from_hud_parent": 1, "unchanged_sources_from_hud_parent": 68,
            "server_native_suites_are_not_hud_behavior_verification": True,
            "prior_reports_are_prior_boundary_only": True, "prior_opaque_rollback_archives_preserved": 8,
            "fresh_final_marker_retention": 17, "unchanged_all48_auditor_executed_on_final": 48,
            "visual_source_retention": 3, "native_suites": runtime["results"],
            "selected_hud_layout": runtime["selected_hud_layout"],
            "bot_vault_supplement": runtime["bot_vault_supplement"],
            "guardian_target_diagnostic": runtime["guardian_target_diagnostic"],
            "score_relay_regressions": runtime["score_relay_regressions"],
            "relay_presentation": runtime["relay_presentation"],
            "br_canyon": runtime["br_canyon"],
            "role_readability": runtime["role_readability"],
            "field_prompt": runtime["field_prompt"],
            "foliage_readability": runtime["foliage_readability"],
            "guardian_wall": runtime["guardian_wall"],
            "combat_visual": runtime["combat_visual"],
            "growth_musou": runtime["growth_musou"],
            "art_polish_skillfx": runtime["art_polish_skillfx"],
            "mage_contact": runtime["mage_contact"],
            "relay_eligibility": runtime["relay_eligibility"],
            "private_touch": runtime["private_touch"],
            "portrait": runtime["portrait"],
            "team_win_rule": runtime["team_win_rule"],
            "fractional_hp": runtime["fractional_hp"],
            "mage_projectiles": runtime["mage_projectiles"],
            "mage_water_chain": runtime["mage_water_chain"],
            "ninja_s4": runtime["ninja_s4"],
            "wing_warrior": runtime["wing_warrior"],
            "fixed_cues": runtime["fixed_cues"],
            "field_loadouts": runtime["field_loadouts"],
            "first90_role": runtime["first90_role"],
            "return_convert": runtime["return_convert"],
            "ground_night": runtime["ground_night"],
            "cover_orders": runtime["cover_orders"],
            "mage_field_arcs": runtime["mage_field_arcs"],
            "eclipse_sweep": runtime["eclipse_sweep"],
            "builder_forms": runtime["builder_forms"],
            "footing_wards": runtime["footing_wards"],
            "ninja_beast_castle": runtime["ninja_beast_castle"],
            "spring_mist_forest": runtime["spring_mist_forest"],
            "ninja_steps_objectives": runtime["ninja_steps_objectives"],
            "warrior_field_horde": runtime["warrior_field_horde"],
            "trapper_cast_audio": runtime["trapper_cast_audio"],
            "zombie_formation_camera": runtime["zombie_formation_camera"],
            "native_full_body_coverage": runtime["aggregate"]["full_body_coverage"],
            "native_process_count": runtime["aggregate"]["native_process_count"],
            "native_evidence_file_count": runtime["aggregate"]["native_evidence_file_count"],
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
