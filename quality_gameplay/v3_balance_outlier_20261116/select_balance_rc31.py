#!/usr/bin/env python3
"""Private 31-slot Rojo selector: replace ONLY existing BalanceMetrics, never add authority."""
import argparse
import copy
import hashlib
import importlib.machinery
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET
from select_balance import select, git_blob_sha, ORIGINAL_GIT_BLOB

MODULE = "EGGRUMBLE_BalanceMetrics"
CLASSES = {"Script", "LocalScript", "ModuleScript"}

def official_flatten(path: Path):
    lib = importlib.machinery.SourceFileLoader(
        "canonical_gq555_selector", "rc_fastlane/select_gq555_original_bot_nearest.py").load_module()
    return lib.flatten(path)

def prepare(base: Path, out: Path):
    tree, sources = official_flatten(base)
    match = [k for k in sources if k[-1] == MODULE]
    if len(sources) != 31 or len(match) != 1:
        raise ValueError("RED: canonical one BalanceMetrics in 31 source slots required")
    slot = match[0]
    original = sources[slot].read_bytes()
    if git_blob_sha(original) != ORIGINAL_GIT_BLOB:
        raise ValueError("RED: canonical balance source not pinned original #487")
    selected_bytes = select(original)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise ValueError("RED: selected RC project already exists, no implicit overwrite")
    selected_file = out.parent / "EGGRUMBLE_BalanceMetrics_GQ568.luau"
    if selected_file.exists():
        raise ValueError("RED: selected source file already exists")
    selected_file.write_bytes(selected_bytes)
    tree = copy.deepcopy(tree)
    tree["name"] = "PRIVATE_GQ568_V3_BALANCE_OUTLIER_EXISTING31"
    def remap(children, parents=()):
        for name, node in children.items():
            if name.startswith("$"):
                continue
            route = parents + (name,)
            if "$path" in node:
                file = selected_file if route == slot else sources[route]
                node["$path"] = os.path.relpath(file, out.parent).replace(os.sep, "/")
            else:
                remap(node, route)
    remap(tree["tree"])
    out.write_text(json.dumps(tree, ensure_ascii=False, indent=2)+"\n")
    _, after = official_flatten(out)
    if set(after) != set(sources):
        raise ValueError("RED: script route or count drift")
    changed = [k for k in after if after[k].read_bytes() != sources[k].read_bytes()]
    if changed != [slot]:
        raise ValueError("RED: must modify exactly existing BalanceMetrics slot")
    receipt = {
        "original_balance_git_blob": ORIGINAL_GIT_BLOB,
        "selected_balance_git_blob": git_blob_sha(selected_bytes),
        "only_selected_source": "/".join(slot),
        "script_count": 31,
        "untouched_original_source_class": 30,
        "off_rollback_byte_exact": original == sources[slot].read_bytes(),
        "formal_rc_written": False,
        "studio_android_owner": "NOT_TESTED",
    }
    (out.parent/"GQ568_SELECTION_RECEIPT.json").write_text(
        json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print("GQ568_PRIVATE_31_SELECT_PASS", receipt["only_selected_source"])
    return receipt

def verify(base: Path, after: Path, place: Path):
    _, old = official_flatten(base)
    _, selected = official_flatten(after)
    if len(old) != 31 or set(old) != set(selected):
        raise ValueError("RED: canonical source map drift")
    slot = [k for k in old if k[-1]==MODULE]
    if len(slot) != 1 or git_blob_sha(old[slot[0]].read_bytes()) != ORIGINAL_GIT_BLOB:
        raise ValueError("RED: base BalanceMetrics is not original")
    for route in old:
        expected = select(old[route].read_bytes()) if route == slot[0] else old[route].read_bytes()
        if selected[route].read_bytes() != expected:
            raise ValueError("RED: source mismatch " + "/".join(route))
    found = {}
    for node in ET.parse(place).getroot().iter("Item"):
        cls = node.get("class")
        if cls not in CLASSES:
            continue
        props = node.find("Properties")
        if props is None:
            raise ValueError("RED: Rojo missing properties")
        name = props.findtext("string[@name='Name']")
        text = props.findtext("ProtectedString[@name='Source']")
        if text is None:
            text = props.findtext("string[@name='Source']")
        if name is None or text is None or name in found:
            raise ValueError("RED: missing source or duplicate module name")
        found[name] = (cls, text.replace("\r\n","\n"))
    if len(found)!=31 or set(found)!={r[-1] for r in selected}:
        raise ValueError("RED: not exactly canonical 31 Rojo scripts")
    for route, path in selected.items():
        source = path.read_text(encoding="utf-8").replace("\r\n","\n")
        cls = "Script" if path.name.endswith(".server.luau") else (
              "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if found[route[-1]] != (cls, source):
            raise ValueError("RED: Rojo Source/Class mismatch " + "/".join(route))
    receipt = {
      "source_class_exact": "31/31",
      "other_sources_byte_identical": "30/30",
      "slot": "/".join(slot[0]),
      "off_select_is_original_blob": True,
      "real_place_bytes":place.stat().st_size,
      "real_place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
      "formal_rc_written":False,
      "studio_android_owner":"NOT_TESTED"
    }
    (after.parent/"GQ568_ROJO_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("GQ568_PRIVATE_31_REAL_ROJO_EXACT_PASS",receipt["real_place_bytes"])
    return receipt

def main():
    a=argparse.ArgumentParser()
    a.add_argument("command",choices=("prepare","verify"))
    a.add_argument("--base",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    a.add_argument("--place",type=Path)
    args=a.parse_args()
    if args.command=="prepare":
        prepare(args.base,args.out)
    else:
        if not args.place:
            a.error("--place needed for verify")
        verify(args.base,args.out,args.place)

if __name__=="__main__":
    main()
