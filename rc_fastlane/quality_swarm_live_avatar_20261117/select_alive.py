#!/usr/bin/env python3
"""GQ8: Never select a dead human avatar as a V3 Swarm spawn/chase target.

Source-select exactly one pre-existing EGGRUMBLE_SwarmCombat in current 31.
No new combat/neutral/Game/Remote/Store author, and OFF restores all 31 bytes.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

FEATURE = "GQ8_SWARM_LIVING_HUMAN_TARGET_20261117"
SWARM = ("ServerScriptService", "EGGRUMBLE_SwarmCombat")
BEFORE = '''    local ch=p.Character
    local root=ch and ch:FindFirstChild("HumanoidRootPart")::BasePart?
    if root then table.insert(a,root.Position) end'''
AFTER = '''    local ch=p.Character
    local root=ch and ch:FindFirstChild("HumanoidRootPart")::BasePart?
    local humanoid=ch and ch:FindFirstChildOfClass("Humanoid")
    if root and humanoid and humanoid.Health>0 then table.insert(a,root.Position) end'''
OUTPUT_SOURCE = "GQ8_SWARM_LIVING_AVATAR_SELECTED.luau"
OUTPUT_RECEIPT = "GQ8_SWARM_LIVING_AVATAR_RECEIPT.json"


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def scan(project: Path):
    doc = json.loads(project.read_text(encoding="utf-8"))
    found = {}
    def walk(branch, route=()):
        for name, node in branch.items():
            if name.startswith("$"):
                continue
            if not isinstance(node, dict):
                raise ValueError("RED_SCRIPT_TREE_SHAPE")
            key = route + (name,)
            if "$path" in node:
                if set(node) != {"$path"} or key in found:
                    raise ValueError("RED_DUPLICATE_SCRIPT_ENTRY")
                found[key] = (project.parent / node["$path"]).resolve(strict=True)
            else:
                walk(node, key)
    walk(doc["tree"])
    if len(found) != 31 or len({k[-1] for k in found}) != 31 or SWARM not in found:
        raise ValueError("RED_NOT_EXACT_SINGLE_SWARM31")
    return doc, found


def scoped(source: str) -> str:
    matches = list(re.finditer(
        r" local function aliveTargets\(\):\{Vector3\}\n.*?\n  return a\n end", source, re.S
    ))
    if len(matches) != 1:
        raise ValueError("RED_LIVE_TARGET_FUNCTION_DRIFT")
    return matches[0].group(0)


def patch(source: str) -> str:
    original = scoped(source)
    if source.count(BEFORE) != 1 or original.count(BEFORE) != 1 or AFTER in source:
        raise ValueError("RED_LIVE_TARGET_ANCHOR_OR_ALREADY_APPLIED")
    if 'local c=session.rules.castles[tostring(p.UserId)]' not in original:
        raise ValueError("RED_CASTLE_OWNER_BOUNDARY_DRIFT")
    if 'for id,m in pairs(session.botActors or {}) do' not in original:
        raise ValueError("RED_BOT_TARGET_AUTHORITY_DRIFT")
    result = source.replace(BEFORE, AFTER, 1)
    if unpatch(result) != source:
        raise ValueError("RED_OFF_NOT_BYTE_EXACT")
    return result


def unpatch(selected: str) -> str:
    if selected.count(AFTER) != 1 or scoped(selected).count(AFTER) != 1:
        raise ValueError("RED_SELECTED_LIVE_TARGET_DRIFT")
    return selected.replace(AFTER, BEFORE, 1)


def compare(base: Path, out: Path):
    _, previous = scan(base)
    _, current = scan(out)
    if set(previous) != set(current):
        raise ValueError("RED_ADDITIONAL_SCRIPT")
    differences = [key for key in previous if previous[key].read_bytes() != current[key].read_bytes()]
    if differences != [SWARM]:
        raise ValueError("RED_OTHER30_SOURCES_MODIFIED")
    before = previous[SWARM].read_text(encoding="utf-8")
    after = current[SWARM].read_text(encoding="utf-8")
    if patch(before) != after or unpatch(after) != before:
        raise ValueError("RED_SINGLE_SWARM_INVERSE_NOT_EXACT")
    return before, after


def prepare(base: Path, out: Path):
    base = base.resolve(strict=True)
    out = out.resolve()
    if out.parent != base.parent or out.exists() or (out.parent / OUTPUT_SOURCE).exists():
        raise ValueError("RED_CANDIDATE_OUTPUT_COLLISION")
    doc, files = scan(base)
    before = files[SWARM].read_text(encoding="utf-8")
    after = patch(before)
    (out.parent / OUTPUT_SOURCE).write_text(after, encoding="utf-8")
    candidate = copy.deepcopy(doc)
    candidate["tree"]["ServerScriptService"][SWARM[-1]]["$path"] = OUTPUT_SOURCE
    out.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    compare(base, out)
    receipt = {
        "feature_id": FEATURE, "base_project": base.name,
        "selected_project": out.name, "source_count": 31,
        "changed_source": "EGGRUMBLE_SwarmCombat",
        "other30_byte_exact": True, "off_rollback_exact": True,
        "before_sha256": sha256(before.encode()), "after_sha256": sha256(after.encode()),
        "new_game_combat_remote_store": 0,
        "scope": "dead human avatar excluded from Swarm spawn/chase target positions; live players and active bots preserved",
        "native": "PENDING", "rojo": "PENDING",
        "formal_rc_adopted": False,
        "studio_android_owner_fun": "NOT_TESTED"
    }
    (out.parent / OUTPUT_RECEIPT).write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print("GQ8_SWARM_LIVING_AVATAR_ONE_EXISTING_SWARM_OTHER30_EXACT_OFF_PASS")


def verify(base: Path, out: Path, place: Path):
    before, after = compare(base.resolve(strict=True), out.resolve(strict=True))
    _, sources = scan(out.resolve(strict=True))
    embedded = {}
    for item in ET.parse(place).getroot().iter("Item"):
        kind = item.get("class")
        if kind not in ("Script", "LocalScript", "ModuleScript"):
            continue
        props = item.find("Properties")
        if props is None:
            raise ValueError("RED_ROJO_SCRIPT_PROPERTIES")
        name = props.findtext("string[@name='Name']")
        src = props.findtext("ProtectedString[@name='Source']")
        if src is None:
            src = props.findtext("string[@name='Source']")
        if not name or src is None or name in embedded:
            raise ValueError("RED_ROJO_DUPLICATE_OR_EMPTY")
        embedded[name] = (kind, src.replace("\r\n", "\n"))
    if len(embedded) != 31 or set(embedded) != {p[-1] for p in sources}:
        raise ValueError("RED_ROJO_NOT31")
    for namepath, source in sources.items():
        kind = ("Script" if source.name.endswith(".server.luau")
                else "LocalScript" if source.name.endswith(".client.luau") else "ModuleScript")
        if embedded[namepath[-1]] != (kind, source.read_text(encoding="utf-8").replace("\r\n", "\n")):
            raise ValueError("RED_ROJO_CLASS_OR_SOURCE_MISMATCH_" + namepath[-1])
    receipt_path = out.parent / OUTPUT_RECEIPT
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt["before_sha256"] != sha256(before.encode()) or receipt["after_sha256"] != sha256(after.encode()):
        raise ValueError("RED_PREP_RECEIPT_DRIFT")
    receipt.update(native="31/31", rojo="31/31", place_bytes=place.stat().st_size,
                   place_sha256=sha256(place.read_bytes()))
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print("GQ8_SWARM_LIVING_AVATAR_CURRENT31_NATIVE_ROJO_EXACT_PASS", receipt["place_bytes"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=("prepare", "verify"))
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--place", type=Path)
    opts = ap.parse_args()
    if opts.action == "prepare":
        prepare(opts.base, opts.out)
    else:
        if not opts.place:
            ap.error("verify requires --place")
        verify(opts.base, opts.out, opts.place)


if __name__ == "__main__":
    main()
