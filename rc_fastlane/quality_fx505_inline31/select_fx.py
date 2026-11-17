#!/usr/bin/env python3
"""GQ505: source-select original server VFX fairness into ONE existing SkillFX.

The authored #505 overlay + #505 quota are reused at immutable SHAs.
Only SkillFX changes. Embed the original quota inside the same ModuleScript
rather than adding a 32nd gameplay Source or a second FX emitter.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

FEATURE = "GQ505_SERVER_MODE_FX_FAIR_INLINE31"
SOURCE = "EGGRUMBLE_SkillFX"
ORIGINAL_BLOB = "5c05738a81397cf33c9900ac088f0787c242c720"
MODULE_REQUIRE = 'local ModeFairQuota=require(script.Parent:WaitForChild("EGGRUMBLE_FXModeFairQuota"))\n'
NEW_FILE = "GQ505_FX_FAIR_SKILLFX_INLINE.luau"
RECEIPT = "GQ505_FX_FAIR_RECEIPT.json"
ORIG_HEADER = "-- EGGRUMBLE V3 vivid but bounded 7-job VFX: no heavy lights, textures or assets."
OVERLAY_HEADER = "-- EGGRUMBLE V3 original-author source-selective 2-mode FX quota overlay; vivid but bounded 7-job VFX: no heavy lights, textures or assets."
EDITS = (
    (ORIG_HEADER, OVERLAY_HEADER),
    (
        "local SkillFX={}\n",
        "local SkillFX={}\n"+MODULE_REQUIRE+"local fairQuota=ModeFairQuota.new(72,12)\n",
    ),
    (
        " if active>=ACTIVE_LIMIT then return nil end\n",
        " local lease=fairQuota:acquire(parent.Name)\n if not lease then return nil end\n",
    ),
    (
        "  active=math.max(0,active-1)\n",
        "  active=math.max(0,active-1)\n  fairQuota:release(lease)\n",
    ),
    (
        " if active>ACTIVE_LIMIT-MAX_NEW_PER_PULSE then return end\n",
        " if active>ACTIVE_LIMIT-MAX_NEW_PER_PULSE or not fairQuota:canStart(parent.Name,MAX_NEW_PER_PULSE) then return end\n",
    ),
)


def git_blob(text):
    raw = text.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def sources(project):
    doc = json.loads(project.read_text(encoding="utf-8"))
    found = {}
    def walk(node, route=()):
        for name, value in node.items():
            if name.startswith("$"):
                continue
            if not isinstance(value, dict):
                raise ValueError("RED_NON_SCRIPT_TREE_ENTRY")
            next_route = route + (name,)
            if "$path" in value:
                if set(value) != {"$path"} or next_route in found:
                    raise ValueError("RED_AMBIGUOUS_MAPPING")
                found[next_route] = (project.parent / value["$path"]).resolve(strict=True)
            else:
                walk(value, next_route)
    walk(doc["tree"])
    if len(found) != 31 or len({r[-1] for r in found}) != 31:
        raise ValueError("RED_NOT_CANONICAL_31")
    target = [route for route in found if route[-1] == SOURCE]
    if len(target) != 1 or target[0][-2] != "ServerScriptService":
        raise ValueError("RED_NOT_SINGLE_ORIGINAL_SKILLFX")
    return doc, found, target[0]


def author_overlay(original, overlay):
    if git_blob(original) != ORIGINAL_BLOB:
        raise ValueError("RED_ORIGINAL_SKILLFX_GIT_BLOB_DRIFT")
    expected = original
    for before, after in EDITS:
        if expected.count(before) != 1:
            raise ValueError("RED_AUTHOR_FX_ANCHOR_MISSING_OR_DUPLICATE")
        expected = expected.replace(before, after, 1)
    if expected != overlay:
        raise ValueError("RED_GQ505_ORIGINAL_AUTHOR_OVERLAY_DRIFT")
    return expected


def inline(original, overlay, policy):
    author_overlay(original, overlay)
    if not policy.startswith("--!strict\n") or policy.count("return Quota") != 1:
        raise ValueError("RED_ORIGINAL_POLICY_DRIFT")
    if policy.count("function Quota.new(") != 1 or "DataStoreService" in policy:
        raise ValueError("RED_POLICY_NOT_BOUNDED_QUOTA")
    if overlay.count(MODULE_REQUIRE) != 1:
        raise ValueError("RED_AUTHOR_REQUIRE_CHANGED")
    body = policy.removeprefix("--!strict\n").rstrip("\n") + "\n"
    embedded = "local ModeFairQuota=(function()\n" + body + "end)()\n"
    out = overlay.replace(MODULE_REQUIRE, embedded, 1)
    if "WaitForChild(\"EGGRUMBLE_FXModeFairQuota\")" in out:
        raise ValueError("RED_32ND_RUNTIME_MODULE_DEPENDENCY")
    for required in (
        "fairQuota:acquire(parent.Name)",
        "fairQuota:release(lease)",
        "fairQuota:canStart(parent.Name,MAX_NEW_PER_PULSE)",
        "ModeFairQuota.new(72,12)",
    ):
        if out.count(required) != 1:
            raise ValueError("RED_POLICY_LINK_OR_LEASE_COUNT")
    return out


def prepare(base, out, original_file, overlay_file, policy_file):
    base = base.resolve(strict=True)
    out = out.resolve()
    if out.exists() or out.parent != base.parent:
        raise ValueError("RED_OUTPUT_COLLISION_OR_DIFFERENT_PARENT")
    doc, before, key = sources(base)
    source = before[key].read_text(encoding="utf-8")
    orig = original_file.read_text(encoding="utf-8")
    overlay = overlay_file.read_text(encoding="utf-8")
    policy = policy_file.read_text(encoding="utf-8")
    if source != orig:
        raise ValueError("RED_CURRENT_CANONICAL_FX_NOT_ORIGINAL_482")
    new = inline(source, overlay, policy)
    target = out.parent / NEW_FILE
    if target.exists():
        raise ValueError("RED_TARGET_FILE_EXISTS")
    target.write_text(new, encoding="utf-8")
    selected = copy.deepcopy(doc)
    cursor = selected["tree"]
    for name in key:
        cursor = cursor[name]
    cursor["$path"] = NEW_FILE
    out.write_text(json.dumps(selected, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    _, after, after_key = sources(out)
    diff = [name for name in before if before[name].read_bytes() != after[name].read_bytes()]
    if key != after_key or diff != [key] or len(after) != 31:
        raise ValueError("RED_CHANGED_OTHER_RUNTIME_AUTHORITY")
    receipt = {
        "feature_id": FEATURE,
        "original_pr": 505,
        "original_head": "3ea5f4e87df7e3bb20a63026f892dd9c94f981e9",
        "original_source_blob": ORIGINAL_BLOB,
        "selected_script": SOURCE,
        "source_count": 31,
        "changed_existing_scripts": 1,
        "other_30_script_bytes_exact": True,
        "new_modules": 0,
        "unchanged_original_off_project": base.name,
        "original_source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "selected_source_sha256": hashlib.sha256(new.encode()).hexdigest(),
        "native": "PENDING", "rojo": "PENDING",
        "studio_android_owner_fun": "NOT_TESTED",
    }
    (out.parent / RECEIPT).write_text(json.dumps(receipt, sort_keys=True, indent=2)+"\n")
    print("GQ505_AUTHOR_REUSE_INLINE31_ONE_FX_OTHER30_OFF_EXACT_PASS")


def verify(base, out, place, original_file, overlay_file, policy_file):
    _, old, key = sources(base.resolve(strict=True))
    _, new, newkey = sources(out.resolve(strict=True))
    if set(old) != set(new) or key != newkey:
        raise ValueError("RED_SOURCE_MAP_CHANGED")
    original = old[key].read_text(encoding="utf-8")
    expected = inline(
        original,
        overlay_file.read_text(encoding="utf-8"),
        policy_file.read_text(encoding="utf-8"),
    )
    if original != original_file.read_text(encoding="utf-8"):
        raise ValueError("RED_ORIGINAL_SKILLFX_DRIFT")
    if new[key].read_text(encoding="utf-8") != expected:
        raise ValueError("RED_PATCHED_SOURCE_UNEXPECTED")
    if [n for n in old if old[n].read_bytes() != new[n].read_bytes()] != [key]:
        raise ValueError("RED_OTHER30_CHANGED")
    embedded = {}
    for item in ET.parse(place).getroot().iter("Item"):
        kind = item.get("class")
        if kind not in ("Script", "ModuleScript", "LocalScript"):
            continue
        props = item.find("Properties")
        if props is None:
            raise ValueError("RED_ROJO_SCRIPT_PROPERTIES")
        name = props.findtext("string[@name='Name']")
        src = props.findtext("ProtectedString[@name='Source']")
        if src is None:
            src = props.findtext("string[@name='Source']")
        if not name or src is None or name in embedded:
            raise ValueError("RED_ROJO_MISSING_OR_DUPLICATE_SCRIPT")
        embedded[name] = (kind, src.replace("\r\n", "\n"))
    if len(embedded) != 31 or set(embedded) != {n[-1] for n in new}:
        raise ValueError("RED_ROJO_NOT_REAL_31")
    for route, script in new.items():
        kind = "Script" if script.name.endswith(".server.luau") else (
            "LocalScript" if script.name.endswith(".client.luau") else "ModuleScript"
        )
        if embedded[route[-1]] != (kind, script.read_text(encoding="utf-8").replace("\r\n", "\n")):
            raise ValueError("RED_ROJO_CLASS_SOURCE_MISMATCH:" + route[-1])
    receipt_path = out.parent / RECEIPT
    data = json.loads(receipt_path.read_text(encoding="utf-8"))
    data.update(
        native="31/31", rojo="31/31",
        place_bytes=place.stat().st_size,
        place_sha256=hashlib.sha256(place.read_bytes()).hexdigest(),
        off_inverse_original_skillfx_exact=True,
    )
    receipt_path.write_text(json.dumps(data, sort_keys=True, indent=2)+"\n")
    print("GQ505_REAL_ROJO31_NATIVE31_SOURCE_EXACT_PASS", data["place_bytes"])


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "verify"))
    for n in ("base", "out", "original", "overlay", "policy"):
        parser.add_argument("--" + n, type=Path, required=True)
    parser.add_argument("--place", type=Path)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.base,args.out,args.original,args.overlay,args.policy)
    elif args.place is None:
        parser.error("--place required")
    else:
        verify(args.base,args.out,args.place,args.original,args.overlay,args.policy)
if __name__ == "__main__":
    cli()
