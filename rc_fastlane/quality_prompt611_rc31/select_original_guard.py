#!/usr/bin/env python3
"""GQ611 one existing InteractionGuard source-select after current 31 authors.

This is a packager for immutable PR #611, NOT an independent gameplay author.
No additional Script or authority. Current source-lock or duplicate fails RED.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET

N = 31
TARGET = "EGGRUMBLE_InteractionGuard"
AUTHOR_HEAD = "f41246191d35f64fe6c1c097999562f37ccaa1fc"
BASE_ORIGINAL_BLOB = "ac51ce2077814c7509b8eaf6dafbd05b04a9a1fe"
OUTPUT_SOURCE = "GQ611_CURRENT_InteractionGuard.luau"
RECEIPT = "GQ611_RC31_RECEIPT.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def scan(project: Path):
    obj = json.loads(project.read_text(encoding="utf8"))
    result = {}
    def visit(node, route=()):
        for name, part in node.items():
            if name.startswith("$"):
                continue
            if not isinstance(part, dict):
                raise ValueError("RED_BAD_ROJO_NODE")
            key = route + (name,)
            if "$path" in part:
                if set(part) != {"$path"} or key in result:
                    raise ValueError("RED_DUPLICATE_SOURCE_ROUTE")
                result[key] = (project.parent / part["$path"]).resolve(strict=True)
            else:
                visit(part, key)
    visit(obj["tree"])
    if len(result) != N or len({key[-1] for key in result}) != N:
        raise ValueError("RED_NOT_EXACT_CURRENT31")
    targets = [key for key in result if key[-1] == TARGET]
    if len(targets) != 1:
        raise ValueError("RED_NOT_SINGLE_ORIGINAL_GUARD")
    for singleton in ("EGGRUMBLE_LobbyCastleModesPreview", "EGGRUMBLE_SevenRoleCombat",
                      "EGGRUMBLE_SwarmCombat", "EGGRUMBLE_BotActors",
                      "EGGRUMBLE_FieldItemPickups", "EGGRUMBLE_MatchResultService"):
        if sum(k[-1] == singleton for k in result) != 1:
            raise ValueError("RED_DUPLICATE_RUNTIME_AUTHORITY_" + singleton)
    return obj, result, targets[0]


def expected(current: bytes, original: bytes, patched: bytes, verifier: Path) -> bytes:
    if blob(original) != BASE_ORIGINAL_BLOB:
        raise ValueError("RED_ORIGINAL_BLOB_NOT_PINNED")
    if current != original:
        raise ValueError("RED_CURRENT31_GUARD_DRIFT_OR_ALREADY_SELECTED")
    spec = importlib.util.spec_from_file_location("gq611_original_checker", verifier)
    if spec is None or spec.loader is None:
        raise ValueError("RED_ORIGINAL_VERIFIER_NOT_LOADABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = module.select(original.decode("utf8")).encode("utf8")
    if patched != source or source == original:
        raise ValueError("RED_PATCH_NOT_IMMUTABLE_AUTHOR611")
    reverted = source.decode("utf8")
    for before, after in reversed(list(zip(module.OLD, module.NEW))):
        if reverted.count(after) != 1:
            raise ValueError("RED_CANNOT_INVERT_AUTHOR611")
        reverted = reverted.replace(after, before, 1)
    if reverted.encode("utf8") != original:
        raise ValueError("RED_GUARD_OFF_NOT_BYTE_EXACT")
    return source


def prepare(base: Path, out: Path, original: Path, patched: Path, verifier: Path):
    base, out = base.resolve(strict=True), out.resolve()
    if out == base or out.exists() or out.parent != base.parent:
        raise ValueError("RED_OUTPUT_NOT_NEW_SIBLING")
    obj, current, target = scan(base)
    chosen = expected(current[target].read_bytes(), original.read_bytes(), patched.read_bytes(), verifier)
    dst = out.parent / OUTPUT_SOURCE
    if dst.exists():
        raise ValueError("RED_OUTPUT_SOURCE_ALREADY_EXISTS")
    dst.write_bytes(chosen)
    project = copy.deepcopy(obj)
    part = project["tree"]
    for key in target:
        part = part[key]
    part["$path"] = OUTPUT_SOURCE
    out.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    _, new, new_target = scan(out)
    if set(new) != set(current) or new_target != target:
        raise ValueError("RED_LAYOUT_SOURCE_31_CHANGED")
    changed = [key for key in current if current[key].read_bytes() != new[key].read_bytes()]
    if changed != [target]:
        raise ValueError("RED_OTHER30_OR_GUARD_NOT_UNIQUE")
    receipt = {
        "author_pr":611,"author_head":AUTHOR_HEAD,"original_blob":BASE_ORIGINAL_BLOB,
        "source_count":31,"new_script_count":0,"only_changed_existing_script":TARGET,
        "other_30_byte_exact":True,"guard_off_rollback_byte_exact":True,
        "source_before_sha256":sha(current[target].read_bytes()),
        "source_after_sha256":sha(chosen),
        "rojo_source_class_exact":"NOT_TESTED",
        "official_rc_adopted":False,"engine_android_fun_owner":"NOT_TESTED"
    }
    (out.parent / RECEIPT).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("GQ611_ONE_GUARD_OTHER30_EXACT_OFF_ROLLBACK_PASS")


def verify(base: Path, out: Path, place: Path, original: Path, patched: Path, verifier: Path):
    _, old, target = scan(base)
    _, new, new_target = scan(out)
    if set(old)!=set(new) or target!=new_target:
        raise ValueError("RED_CHANGED_SCRIPT_LAYOUT")
    selected = expected(old[target].read_bytes(),original.read_bytes(),patched.read_bytes(),verifier)
    if new[target].read_bytes()!=selected:
        raise ValueError("RED_SELECTED_GUARD_NOT_ORIGINAL")
    if [k for k in old if old[k].read_bytes()!=new[k].read_bytes()]!=[target]:
        raise ValueError("RED_OTHER30_CHANGED")
    embedded={}
    for item in ET.parse(place).getroot().iter("Item"):
        typ=item.attrib.get("class")
        if typ not in ("Script","LocalScript","ModuleScript"):
            continue
        props=item.find("Properties")
        if props is None:
            raise ValueError("RED_ROJO_PROPERTIES")
        name=props.findtext("string[@name='Name']")
        code=props.findtext("ProtectedString[@name='Source']")
        if code is None:
            code=props.findtext("string[@name='Source']")
        if not name or code is None or name in embedded:
            raise ValueError("RED_DUPLICATE_OR_MISSING_ROJO_SCRIPT")
        embedded[name]=(typ,code.replace("\r\n","\n"))
    if len(embedded)!=N or set(embedded)!={k[-1] for k in new}:
        raise ValueError("RED_NOT_REAL31_ROJO")
    for key,path in new.items():
        kind=("Script" if path.name.endswith(".server.luau") else
              "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if embedded[key[-1]]!=(kind,path.read_text(encoding="utf8").replace("\r\n","\n")):
            raise ValueError("RED_ROJO_SOURCE_OR_CLASS_MISMATCH_"+key[-1])
    receipt=json.loads((out.parent/RECEIPT).read_text())
    if not receipt["other_30_byte_exact"] or not receipt["guard_off_rollback_byte_exact"]:
        raise ValueError("RED_RECEIPT_OFF_DRIFT")
    receipt.update(rojo_source_class_exact="31/31",place_bytes=place.stat().st_size,
                   place_sha256=sha(place.read_bytes()),source_provenance_valid=True)
    (out.parent/RECEIPT).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("GQ611_TRUE_ROJO31_SELECTED_SINGLE_GUARD_EXACT_PASS",receipt["place_bytes"])


def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("prepare","verify"))
    for key in ("base","out","original","patched","verifier"):
        p.add_argument("--"+key,required=True,type=Path)
    p.add_argument("--place",type=Path)
    a=p.parse_args()
    if a.action=="prepare":
        prepare(a.base,a.out,a.original,a.patched,a.verifier)
    else:
        if a.place is None:
            p.error("--place needed for verify")
        verify(a.base,a.out,a.place,a.original,a.patched,a.verifier)
if __name__=="__main__":
    main()
