#!/usr/bin/env python3
"""Select the ORIGINAL #492 spectator into CURRENT official V3 31 script build.
PREP only: never edits canonical RC, Game/Combat/Host, or an original author.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

AUTHOR_HEAD = "eb38aa60b69ed0bdd80fb7ea0dd10cf230345c20"
AUTHOR_BLOB = "c39b2d3cc481052940b9d11a6fc695261a9b1e40"
NAME = "EGGRUMBLE_EliminatedSpectate"
REQUIRED_EXISTING = {"EGGRUMBLE_LobbyCastleModesPreview", "EGGRUMBLE_CastleMatchRules"}


def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def kind(path):
    if path.name.endswith(".client.luau"):
        return "LocalScript"
    if path.name.endswith(".server.luau"):
        return "Script"
    if path.suffix == ".luau":
        return "ModuleScript"
    raise ValueError("RED: unknown source class " + str(path))


def source_map(project, project_file):
    found = {}
    def visit(node):
        if not isinstance(node, dict):
            return
        for key, child in node.items():
            if key.startswith("$") or not isinstance(child, dict):
                continue
            if "$path" in child:
                if key in found:
                    raise ValueError("RED: duplicate source name " + key)
                path = (project_file.parent / child["$path"]).resolve(strict=True)
                found[key] = (path, kind(path))
            else:
                visit(child)
    visit(project["tree"])
    return found


def checked_original(source):
    if source.name != "EGGRUMBLE_Spectate.client.luau":
        raise ValueError("RED: wrong author client source")
    data = source.read_bytes()
    if git_blob(data) != AUTHOR_BLOB:
        raise ValueError("RED: #492 immutable spectator source drift")
    for anchor in ('EGGRUMBLE_Eliminated', 'getOwnArena', 'restoreCamera', 'IsStudio()'):
        if anchor not in data.decode("utf-8"):
            raise ValueError("RED: missing spectator behavior anchor " + anchor)
    return data


def prepare(base, source, out, receipt):
    base = base.resolve(strict=True)
    source = source.resolve(strict=True)
    checked_original(source)
    if out.resolve() == base:
        raise ValueError("RED: cannot overwrite canonical project")
    p = json.loads(base.read_text(encoding="utf-8"))
    originals = source_map(p, base)
    if len(originals) != 31 or not REQUIRED_EXISTING.issubset(originals):
        raise ValueError("RED: canonical 31-source V3 parent missing")
    if NAME in originals or any("Spectate" in n for n in originals):
        raise ValueError("RED: spectator already selected; no duplicate")
    if originals["EGGRUMBLE_LobbyCastleModesPreview"][1] != "Script":
        raise ValueError("RED: original Host lost server authority")
    if originals["EGGRUMBLE_CastleMatchRules"][1] != "ModuleScript":
        raise ValueError("RED: original Rules class changed")
    # Keep all runtime source objects byte-exact; only rebase Rojo path strings
    # because the proposed project lives in a different artifact directory.
    def relink(node):
        if not isinstance(node, dict):
            return
        if "$path" in node:
            real = (base.parent / node["$path"]).resolve(strict=True)
            node["$path"] = os.path.relpath(real, out.parent.resolve()).replace(os.sep, "/")
        else:
            for child in node.values():
                relink(child)
    relink(p["tree"])
    starter = p["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    if NAME in starter:
        raise ValueError("RED: duplicate StarterPlayer script")
    starter[NAME] = {"$path": os.path.relpath(source, out.parent.resolve()).replace(os.sep, "/")}
    p["name"] = "EGGRUMBLE_GQ492_SPECTATE32_PRIVATE_NOT_OFFICIAL_RC"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(p, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = source_map(p, out)
    if len(result) != 32 or set(result) != set(originals) | {NAME}:
        raise ValueError("RED: 31+1 mapping count/identity changed")
    for key, (path, cls) in originals.items():
        candidate_path, candidate_cls = result[key]
        if candidate_cls != cls or candidate_path.read_bytes() != path.read_bytes():
            raise ValueError("RED: existing 31 source mutated: " + key)
    if result[NAME] != (source, "LocalScript"):
        raise ValueError("RED: original spectator not LocalScript")
    evidence = {
        "kind": "PRIVATE_RC32_PREMERGE_NOT_OFFICIAL",
        "base_rc_head": "b0a4b95de5a501173bdbd2ce179e5901d9d78686",
        "original_spectator_author": AUTHOR_HEAD,
        "original_spectator_blob": AUTHOR_BLOB,
        "existing_gameplay_sources_unchanged": 31,
        "new_client_script": NAME,
        "source_count": 32,
        "rollback": "Unselect only " + NAME + "; original 31 source bytes and classes preserved",
        "studio_engine": "NOT_TESTED",
        "android": "NOT_TESTED",
        "owner_fun": "NO_GO",
        "formal_rc_adopted": False,
    }
    receipt.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("GQ492_PREP_31_PLUS_ONE_ONLY", len(result))


def verify(base, project, source, place, receipt):
    checked_original(source.resolve(strict=True))
    root = json.loads(project.read_text(encoding="utf-8"))
    before = source_map(json.loads(base.read_text(encoding="utf-8")), base)
    after = source_map(root, project)
    if len(before) != 31 or len(after) != 32 or set(after) != set(before) | {NAME}:
        raise AssertionError("RED: source count or identity mismatch")
    for key in before:
        if before[key][1] != after[key][1] or before[key][0].read_bytes() != after[key][0].read_bytes():
            raise AssertionError("RED: source overwrite " + key)
    if after[NAME] != (source.resolve(strict=True), "LocalScript"):
        raise AssertionError("RED: author spectator not selected")
    actual = {}
    for item in ET.parse(place).getroot().iter("Item"):
        cls = item.get("class")
        if cls not in ("Script", "LocalScript", "ModuleScript"):
            continue
        props = item.find("Properties")
        if props is None:
            continue
        name = props.findtext("string[@name='Name']")
        script = props.findtext("ProtectedString[@name='Source']")
        if script is None:
            script = props.findtext("string[@name='Source']")
        if not name or name in actual:
            raise AssertionError("RED: duplicate/missing Rojo script Name")
        actual[name] = (cls, (script or "").replace("\r\n", "\n"))
    expected = {n:(cls,path.read_text(encoding="utf-8").replace("\r\n","\n"))
                for n,(path,cls) in after.items()}
    if actual != expected:
        raise AssertionError("RED: native Rojo32 source/class mismatch: " +
                             repr({"missing":set(expected)-set(actual), "extra":set(actual)-set(expected),
                                   "mismatched":[n for n in expected.keys() & actual.keys() if expected[n]!=actual[n]]}))
    details=json.loads(receipt.read_text(encoding="utf-8"))
    if details["formal_rc_adopted"] is not False:
        raise AssertionError("RED: official state misrepresented")
    details["rojo_source_class_exact"] = "32/32"
    details["place_bytes"] = place.stat().st_size
    details["place_sha256"] = hashlib.sha256(place.read_bytes()).hexdigest()
    details["source_sha256"] = {n: hashlib.sha256(path.read_bytes()).hexdigest()
                                for n, (path,_) in after.items()}
    receipt.write_text(json.dumps(details, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("GQ492_PRIVATE_ROJO32_SOURCE_CLASS_EXACT_PASS", details["place_bytes"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["prepare","verify"])
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--place", type=Path)
    args = parser.parse_args()
    if args.operation == "prepare":
        prepare(args.base, args.source, args.out, args.receipt)
    else:
        if args.place is None:
            parser.error("verify requires --place")
        verify(args.base, args.out, args.source, args.place, args.receipt)


if __name__ == "__main__":
    main()
