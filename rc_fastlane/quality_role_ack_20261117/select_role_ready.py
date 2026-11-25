#!/usr/bin/env python3
"""GQ8: one-current-Host role ACK before TEAM / BR queue admission.

Stack on existing original #651 / intake #668 safe-lobby source; do not
reimplement its floor, spawn, role tools, queue, combat, AI or result.
This selector only changes the *existing* Host in a 31-script source map.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

FEATURE = "GQ8_ROLE_SELECTION_ACK_20261117"
HOST = "EGGRUMBLE_LobbyCastleModesPreview"
MARKER = "-- GQ8_ROLE_SELECTION_ACK_BEGIN"
JOIN = 'local function joinQueue(mode:string,p:Player)\n if sessions[mode] then return end\n'
JOIN_PATCH = '''local function joinQueue(mode:string,p:Player)
 if sessions[mode] then return end
 -- GQ8_ROLE_SELECTION_ACK_BEGIN: require an explicit role-stand action.
 -- No new READY owner, queue timer, Remote or UI layer.
 if chosenRole[p.UserId]==nil then
  p:SetAttribute("EGGRUMBLE_RoleSelectionRequired",true)
  return
 end
 p:SetAttribute("EGGRUMBLE_RoleSelectionRequired",nil)
 -- GQ8_ROLE_SELECTION_ACK_END
'''
ROLE = '''  chosenRole[p.UserId]=role
  p:SetAttribute("EGGRUMBLE_SelectedRole",role)'''
ROLE_PATCH = '''  chosenRole[p.UserId]=role
  p:SetAttribute("EGGRUMBLE_RoleSelectionRequired",nil)
  p:SetAttribute("EGGRUMBLE_SelectedRole",role)'''
PROMPTS = (
    ('"チーム戦（再操作で解除）"', '"職業選択後｜チーム戦（再操作で解除）"'),
    ('"BR戦（再操作で解除）"', '"職業選択後｜BR戦（再操作で解除）"'),
)
OUTPUT_HOST = "EGGRUMBLE_LobbyCastleModesPreview_GQ8_ROLE_ACK.server.luau"
RECEIPT = "GQ8_ROLE_ACK_SELECTED31_RECEIPT.json"

def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def mapping(project: Path):
    project = project.resolve(strict=True)
    obj = json.loads(project.read_text(encoding="utf-8"))
    result = {}
    def walk(node, route=()):
        for name, value in node.items():
            if name.startswith("$"):
                continue
            if not isinstance(value, dict):
                raise ValueError("RED_NON_SOURCE_NODE")
            key = route + (name,)
            if "$path" in value:
                if set(value) != {"$path"} or key in result:
                    raise ValueError("RED_DUPLICATE_OR_MIXED_SCRIPT")
                result[key] = (project.parent / value["$path"]).resolve(strict=True)
            else:
                walk(value, key)
    walk(obj["tree"])
    if len(result) != 31 or len({x[-1] for x in result}) != 31:
        raise ValueError("RED_NOT_31_UNIQUE_SOURCES")
    matched = [key for key in result if key[-1] == HOST]
    if len(matched) != 1:
        raise ValueError("RED_NOT_SINGLE_HOST")
    return obj, result, matched[0]

def apply(source: str) -> str:
    if MARKER in source or "EGGRUMBLE_RoleSelectionRequired" in source:
        raise ValueError("RED_ROLE_ACK_DUPLICATE")
    if "local chosenRole:" not in source or "local queueEpoch:" not in source:
        raise ValueError("RED_ORIGINAL_ROLE_AND_QUEUE_OWNERS_MISSING")
    if "GQ646_LOBBY_SAFE_SPAWN_BEGIN" not in source:
        raise ValueError("RED_EXPECT_ORIGINAL_651_SAFE_LOBBY_FIRST")
    if source.count(JOIN) != 1 or source.count(ROLE) != 1:
        raise ValueError("RED_ROLE_OR_QUEUE_ANCHOR_CHANGED")
    result = source.replace(JOIN, JOIN_PATCH, 1).replace(ROLE, ROLE_PATCH, 1)
    for before, after in PROMPTS:
        if result.count(before) != 1:
            raise ValueError("RED_MODE_GATE_PROMPT_CHANGED " + before)
        result = result.replace(before, after, 1)
    if revert(result) != source:
        raise ValueError("RED_ROLE_ACK_OFF_NOT_BYTE_EXACT")
    if result.count("task.delay(COUNTDOWN,") != source.count("task.delay(COUNTDOWN,"):
        raise ValueError("RED_QUEUE_TIMER_CHANGED")
    if result.count('Instance.new("ScreenGui")') != source.count('Instance.new("ScreenGui")'):
        raise ValueError("RED_NEW_HUD_DETECTED")
    return result

def revert(source: str) -> str:
    if source.count(JOIN_PATCH) != 1 or source.count(ROLE_PATCH) != 1:
        raise ValueError("RED_ROLE_ACK_REVERSION_DRIFT")
    result = source.replace(JOIN_PATCH, JOIN, 1).replace(ROLE_PATCH, ROLE, 1)
    for before, after in PROMPTS:
        if result.count(after) != 1:
            raise ValueError("RED_PROMPT_REVERSION_DRIFT")
        result = result.replace(after, before, 1)
    return result

def prepare(base: Path, out: Path):
    base, out = base.resolve(strict=True), out.resolve()
    if out.exists() or out.parent != base.parent or out == base:
        raise ValueError("RED_OUTPUT_MUST_BE_NEW_SIBLING")
    obj, old, host_key = mapping(base)
    before = old[host_key].read_bytes()
    after = apply(before.decode("utf-8")).encode("utf-8")
    new_host = out.parent / OUTPUT_HOST
    if new_host.exists():
        raise ValueError("RED_OUTPUT_HOST_EXISTS")
    new_host.write_bytes(after)
    clone = copy.deepcopy(obj)
    node = clone["tree"]
    for part in host_key:
        node = node[part]
    node["$path"] = OUTPUT_HOST
    out.write_text(json.dumps(clone, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _, selected, selected_key = mapping(out)
    if selected_key != host_key or set(selected) != set(old):
        raise ValueError("RED_SOURCE_MAPPING_CHANGED")
    if [key for key in old if old[key].read_bytes() != selected[key].read_bytes()] != [host_key]:
        raise ValueError("RED_NOT_ONE_HOST_DELTA")
    receipt = {
        "feature_id": FEATURE,
        "source_count": 31,
        "changed_existing_source": HOST,
        "other_30_byte_exact": True,
        "off_rollback_host_byte_exact": revert(after.decode("utf-8")).encode("utf-8") == before,
        "selected_role_required_before_queue": True,
        "mode_gates": ["TEAM", "BATTLE_ROYALE"],
        "original_safe_lobby_651_retained": True,
        "role_stands_and_tools_482_retained": True,
        "single_host_game_bot_swarm_combat": True,
        "additional_game_or_remotes_or_gui": 0,
        "before_host_sha256": digest(before),
        "after_host_sha256": digest(after),
        "native_luau_31": "NOT_YET_VERIFIED",
        "rojo_source_class_31": "NOT_YET_VERIFIED",
        "official_rc_adopted": False,
        "studio_android_fun_owner": "NOT_TESTED",
    }
    (out.parent / RECEIPT).write_text(json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print("GQ8_ROLE_ACK_SELECTED31_SOURCE_EXACT_OFF_ROLLBACK_PASS")

def verify(base: Path, out: Path, place: Path):
    _, old, host = mapping(base)
    _, new, new_host = mapping(out)
    if set(old) != set(new) or new_host != host:
        raise ValueError("RED_SOURCE_SET_CHANGED")
    before = old[host].read_bytes()
    after = new[host].read_bytes()
    if apply(before.decode("utf-8")).encode("utf-8") != after:
        raise ValueError("RED_SELECTED_HOST_DRIFT")
    if [key for key in old if old[key].read_bytes() != new[key].read_bytes()] != [host]:
        raise ValueError("RED_OTHER_GAME_SOURCE_CHANGED")
    actual = {}
    for item in ET.parse(place).getroot().iter("Item"):
        klass = item.attrib.get("class")
        if klass not in ("Script", "LocalScript", "ModuleScript"):
            continue
        props = item.find("Properties")
        if props is None:
            raise ValueError("RED_MISSING_PROPERTIES")
        name = props.findtext("string[@name='Name']")
        code = props.findtext("ProtectedString[@name='Source']")
        if code is None:
            code = props.findtext("string[@name='Source']")
        if not name or code is None or name in actual:
            raise ValueError("RED_DUPLICATE_OR_MISSING_EMBEDDED_SOURCE")
        actual[name] = (klass, code.replace("\r\n", "\n"))
    if len(actual) != 31 or {key[-1] for key in new} != set(actual):
        raise ValueError("RED_NOT_REAL_31_SCRIPTS_IN_PLACE")
    for key, path in new.items():
        klass = "Script" if path.name.endswith(".server.luau") else (
            "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if actual[key[-1]] != (klass, path.read_text(encoding="utf-8").replace("\r\n", "\n")):
            raise ValueError("RED_SOURCE_OR_CLASS_MISMATCH " + key[-1])
    rec_path = out.parent / RECEIPT
    rec = json.loads(rec_path.read_text(encoding="utf-8"))
    rec.update(native_luau_31="31/31", rojo_source_class_31="31/31",
               place_bytes=place.stat().st_size, place_sha256=digest(place.read_bytes()))
    rec_path.write_text(json.dumps(rec, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print("GQ8_ROLE_ACK_REAL_NATIVE_ROJO31_SOURCE_CLASS_EXACT_PASS", rec["place_bytes"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "verify"))
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--place", type=Path)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.base, args.out)
    else:
        if args.place is None:
            parser.error("--place required")
        verify(args.base, args.out, args.place)
