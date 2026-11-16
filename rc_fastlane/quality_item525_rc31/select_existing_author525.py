#!/usr/bin/env python3
"""Source-select EXISTING PR #525's predicate into latest official 31-script Rojo project.

No original-author source edits; this is an intake adapter, not a new item system.
Fail closed on source or authority drift. No direct RC/main writes.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "quality_deposit_membership_20261116"))
from select_deposit import flatten, embedded_scripts

HOST = ("ServerScriptService", "EGGRUMBLE_LobbyCastleModesPreview")
ITEM = ("ServerScriptService", "EGGRUMBLE_FieldItemPickups")
EXPECTED_AUTHOR_HEAD = "253aa73530eea5c3954c07b546b67e49292c4639"
EXPECTED_ORIGINAL_525_SOURCE = "quality_gameplay/v3_item_mode_ownership_20261116/patch_sources.py"
RECEIPT = "GQ525_RC31_AUTHOR_REUSE_RECEIPT.json"
FLAG = "GQ_V3_ITEM_MODE_OWNERSHIP_20261116"

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def author_module(path: Path):
    path = path.resolve(strict=True)
    if path.as_posix().endswith("/" + EXPECTED_ORIGINAL_525_SOURCE) is False:
        raise ValueError("RED_525_AUTHOR_FILE_NOT_EXPECTED")
    spec = importlib.util.spec_from_file_location("gq525_original_author", path)
    if not spec or not spec.loader:
        raise ValueError("RED_525_IMPORT")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if mod.MARKER != "-- " + FLAG:
        raise ValueError("RED_525_AUTHOR_FLAG_DRIFT")
    return mod

def inspect(base: Path, author: Path):
    data, files = flatten(base)
    if HOST not in files or ITEM not in files:
        raise ValueError("RED_EXPECTED_EXISTING_SINGLETON_MISSING")
    host = files[HOST].read_text(encoding="utf-8")
    item = files[ITEM].read_text(encoding="utf-8")
    if host.count('GQ_DEPOSIT_CURRENT_MATCH_586') != 1:
        raise ValueError("RED_GQ586_CURRENT_HOST_NOT_SELECTED")
    if 'HEAL_NO_WASTE' not in item and 'fullHealth' not in item and 'hum.Health>=hum.MaxHealth' not in item:
        # The exact #517 cure may use a different helper; reject until verified.
        raise ValueError("RED_CURRENT_517_HEAL_ANCHOR_UNVERIFIED")
    author525 = author_module(author)
    updated_host, updated_item = author525.patch_sources(host, item)
    if updated_host.replace(author525.HOST_INSERT, "", 1) != host:
        raise ValueError("RED_HOST_NOT_EXACT_ORIGINAL_525_HUNK")
    if updated_item.replace(author525.ITEM_INSERT, "", 1) != item:
        raise ValueError("RED_ITEM_NOT_EXACT_ORIGINAL_525_HUNK")
    if updated_host.count(FLAG) != 1 or updated_item.count(FLAG) != 1:
        raise ValueError("RED_525_NOT_EXACT_TWO_SITES")
    if "joined[actor.UserId]==mode" not in updated_host or "pcall(authorize,player)" not in updated_item:
        raise ValueError("RED_525_SESSION_AUTHORIZATION_LOST")
    return data, files, author525, updated_host, updated_item

def prepare(base: Path, out: Path, author: Path):
    base = base.resolve(strict=True)
    out = out.resolve()
    if base == out or out.parent != base.parent or out.exists():
        raise ValueError("RED_NOT_FRESH_SIBLING_OUTPUT")
    data, files, mod, host, item = inspect(base, author)
    for name in ("GQ525_RC31_LIVE_HOST.server.luau", "GQ525_RC31_LIVE_ITEM.luau"):
        if (out.parent / name).exists():
            raise ValueError("RED_REUSED_OUTPUT_FILE")
    pairs = [(HOST, "GQ525_RC31_LIVE_HOST.server.luau", host),
             (ITEM, "GQ525_RC31_LIVE_ITEM.luau", item)]
    next_data = copy.deepcopy(data)
    for key, new_name, source in pairs:
        (out.parent / new_name).write_text(source, encoding="utf-8", newline="")
        next_data["tree"]["ServerScriptService"][key[-1]]["$path"] = new_name
    out.write_text(json.dumps(next_data, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    _, selected = flatten(out)
    changed = [k for k in files if files[k].read_bytes() != selected[k].read_bytes()]
    if set(files) != set(selected) or set(changed) != {HOST, ITEM} or len(changed) != 2:
        raise ValueError("RED_UNEXPECTED_OTHER_29_SOURCE_EDIT")
    receipt = {
        "feature_id": FLAG, "source_author_pr": 525,
        "source_author_head": EXPECTED_AUTHOR_HEAD,
        "source_count":31, "only_changed":["/".join(HOST),"/".join(ITEM)],
        "other_29_byte_identical":True, "two_hunk_rollback_exact":True,
        "original_current31_host_sha256":sha(files[HOST].read_bytes()),
        "original_current31_item_sha256":sha(files[ITEM].read_bytes()),
        "selected_host_sha256":sha(selected[HOST].read_bytes()),
        "selected_item_sha256":sha(selected[ITEM].read_bytes()),
        "rc_branch_adopted":False, "studio_android_owner_fun":"NOT_TESTED",
        "rollback":"Drop existing #525 HOST_INSERT and ITEM_INSERT only; restore current #607 Host and #517 Item"
    }
    (out.parent / RECEIPT).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ525_ORIGINAL_AUTHOR_SELECTED_CURRENT31_OTHER29_EXACT_PASS")

def verify(base: Path, out: Path, author: Path, place: Path):
    _, original, mod, host, item = inspect(base, author)
    _, selected = flatten(out)
    if set(original) != set(selected):
        raise ValueError("RED_CURRENT31_SCRIPT_SET_DRIFT")
    changed = {k for k in original if original[k].read_bytes() != selected[k].read_bytes()}
    if changed != {HOST, ITEM}:
        raise ValueError("RED_OTHER_29_CHANGED")
    if selected[HOST].read_text(encoding="utf-8") != host or selected[ITEM].read_text(encoding="utf-8") != item:
        raise ValueError("RED_AUTHOR525_SELECTED_SOURCE_DIFF")
    place_sources = embedded_scripts(place)
    if len(place_sources)!=31 or set(place_sources) != {key[-1] for key in selected}:
        raise ValueError("RED_ROJO_NOT_31_SOURCE")
    for key, path in selected.items():
        kind = ("Script" if path.name.endswith(".server.luau") else
                "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        expected = (kind, path.read_text(encoding="utf-8").replace("\r\n","\n"))
        if place_sources[key[-1]] != expected:
            raise ValueError("RED_ROJO_SOURCE_CLASS_MISMATCH_"+key[-1])
    proofpath = out.parent / RECEIPT
    proof = json.loads(proofpath.read_text(encoding="utf-8"))
    if not proof["two_hunk_rollback_exact"] or not proof["other_29_byte_identical"]:
        raise ValueError("RED_SOURCE_RECEIPT_INVALID")
    proof.update(place_bytes=place.stat().st_size, place_sha256=sha(place.read_bytes()),
                 source_class_exact="31/31")
    proofpath.write_text(json.dumps(proof,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ525_TRUE_ROJO31_NATIVE_SELECTION_PASS", proof["place_bytes"])

def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=["prepare","verify"])
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--author",type=Path,required=True)
    p.add_argument("--place",type=Path)
    a=p.parse_args()
    if a.action=="prepare":
        prepare(a.base,a.out,a.author)
    elif a.place is None:
        p.error("--place required for verify")
    else:
        verify(a.base,a.out,a.author,a.place)

if __name__=="__main__":
    main()
