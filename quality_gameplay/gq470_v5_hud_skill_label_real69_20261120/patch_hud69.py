#!/usr/bin/env python3
"""Source-locked REAL69 HUD presentation repair. A PREP candidate, never formal RC.

Only the existing local skill-choice text changes. Server-owned Tool.Name,
Tool.Activated and combat authority remain byte-for-byte untouched.
The Roblox built-in Backpack hotbar is not modified or claimed fixed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] /
                       "gq8_rc85_rc86_real68_nonloss_20261120"))
from verify_nonloss import project_scan

PARENT = "6c2338b44db1c772bab0d688b2aece2e3aa8aae2"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
TARGET = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_HudIntelRuntime"
MARK = "GQ470_V5_HUD_SKILL_LABEL_FRIENDLY_20261120"
ANCHOR = 'if t then table.insert(options,{id=slot,name=slot.." "..t.Name:sub(19),tool=t}) end'
REPLACEMENT = '''if t then
    -- GQ470_V5_HUD_SKILL_LABEL_FRIENDLY_20261120: presentation only.
    -- Do not rename the server-owned Tool, Remote or slot identity.
    local title=t:GetAttribute("SkillDisplayName")
    if type(title)~="string" or #title==0 or #title>36
     or string.find(title,"EGGRUMBLE_",1,true)
     or string.find(title,"\\n",1,true)
     or string.find(title,"\\r",1,true) then
     title="職業技"..slot
    end
    table.insert(options,{id=slot,name=title,tool=t})
   end'''

def need(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError("RED_GQ470_HUD_" + code)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def patch(source: str) -> str:
    need(MARK not in source, "DUPLICATE_PATCH")
    need(source.count(ANCHOR) == 1, "ONE_ORIGINAL_SKILL_LABEL_ANCHOR")
    need(source.count('local function openDrawer(which)') == 1, "EXISTING_DRAWER_OWNER")
    need(source.count('activate(slotTool(selectedSlot))') == 1,
         "SERVER_OWNED_TOOL_ACTIVATION_PATH")
    need('GQ8_RC85_RC86_FB019_LOCAL_ATTACK_SWING_REAL69_20261120' in source,
         "EXISTING_FB019_ATTACK_FEEDBACK_RETAINED")
    result = source.replace(ANCHOR, REPLACEMENT, 1)
    need(result.count(MARK) == 1, "ONE_LABEL_REPLACEMENT")
    need(result.count('table.insert(options,{id=slot,name=title,tool=t})') == 1,
         "PRESENTATION_SLOT_MAPPING")
    need('SetCoreGuiEnabled' not in REPLACEMENT
         and 'Tool.Name=' not in REPLACEMENT
         and 'RemoteEvent' not in REPLACEMENT
         and ':Activate()' not in REPLACEMENT,
         "NO_AUTHORITY_OR_CORE_HOTBAR_INTERFERENCE")
    return result

def selftest() -> None:
    minimum = ('local function openDrawer(which)\n'
               + ANCHOR + '\n'
               + 'activate(slotTool(selectedSlot))\n'
               + '-- GQ8_RC85_RC86_FB019_LOCAL_ATTACK_SWING_REAL69_20261120\n')
    fixed = patch(minimum)
    need('title="職業技"..slot' in fixed and 't:GetAttribute' in fixed,
         "HUMAN_READABLE_FALLBACK")
    need('table.insert(options,{id=slot,name=title,tool=t})' in fixed,
         "PRESERVE_TOOL_REFERENCE")
    for mutant in (minimum.replace(ANCHOR, 'missing'),
                   minimum.replace(ANCHOR, ANCHOR+'\n'+ANCHOR),
                   minimum.replace('activate(slotTool(selectedSlot))', 'missing'),
                   minimum.replace('GQ8_RC85_RC86_FB019_LOCAL_ATTACK_SWING_REAL69_20261120', 'gone'),
                   fixed):
        try:
            patch(mutant)
        except ValueError:
            continue
        raise AssertionError("MUTANT_NOT_REJECTED")
    print("GQ470_V5_HUD_FIVE_NEGATIVES_AND_ORIGINAL_ACTIVATION_PASS")

def apply(root: pathlib.Path) -> None:
    before = project_scan(root, PROJECT)
    receipt_file = root / RECEIPT
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    need(len(before) == 69 and TARGET in before, "EXACTLY_69_SELECTED")
    need(receipt.get("build_head") == PARENT
         and receipt.get("selected_source_count") == 69
         and len(receipt.get("source_hashes", {})) == 69,
         "PINNED_OFFICIAL_HEAD_RECEIPT")
    need(all(receipt["source_hashes"].get(k) == v["sha256"]
             for k, v in before.items()), "ORIGINAL_ALL_69_SOURCE_LOCK")
    need(before[TARGET]["class"] == "LocalScript", "SINGLE_EXISTING_LOCAL_HUD")
    original_path = root / before[TARGET]["path"]
    old = original_path.read_bytes()
    fixed = patch(old.decode("utf-8")).encode("utf-8")
    save = root / "off69_hud"
    need(not save.exists(), "ROLLBACK_ALREADY_EXISTS")
    shutil.copytree(root / "sources", save / "sources")
    for p in (PROJECT, RECEIPT, "EGGRUMBLE_REAL69_PRIVATE.rbxlx"):
        shutil.copy2(root / p, save / p)
    original_path.write_bytes(fixed)
    after = project_scan(root, PROJECT)
    need(set(after) == set(before) and len(after) == 69, "EXACT_ROUTES")
    changed = {k for k in after if after[k]["sha256"] != before[k]["sha256"]}
    need(changed == {TARGET}, "ONLY_PREEXISTING_HUD_CHANGED")
    need(all(after[k]["class"] == before[k]["class"] for k in after),
         "SCRIPT_CLASSES_UNCHANGED")
    need(all(after[k]["sha256"] == before[k]["sha256"]
             for k in after if k != TARGET), "OTHER_68_SOURCES_EXACT")
    need((save / before[TARGET]["path"]).read_bytes() == old, "SOURCE_ROLLBACK_EXACT")
    receipt["source_hashes"][TARGET] = sha(fixed)
    receipt["build_head"] = "PREP_V5_HUD_FROM_" + PARENT
    receipt["gq470_v5_skill_label"] = {
        "feature_id": MARK,
        "original_formal_head": PARENT,
        "modified_existing_route": TARGET,
        "old_sha256": sha(old),
        "new_sha256": sha(fixed),
        "other_selected_routes_byte_exact": 68,
        "new_selected_scripts": 0,
        "internal_tool_name_unchanged": True,
        "server_gameplay_authority_changed": False,
        "covered": "existing custom skill choice menu label only",
        "not_covered": "Roblox default Backpack hotbar Tool.Name rendering",
        "rollback": "off69_hud",
        "studio": "NOT_TESTED",
        "android": "NOT_TESTED",
        "human_art_accepted": False
    }
    receipt_file.write_text(json.dumps(receipt, ensure_ascii=False,
                                       indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
    print("GQ470_V5_HUD_ONE_SELECTED_LOCAL_68_BYTE_EXACT_OFF69_PASS")

if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--self-test", action="store_true")
    cli.add_argument("--base", type=pathlib.Path)
    args = cli.parse_args()
    if args.self_test:
        selftest()
    else:
        need(args.base is not None, "BASE_ARTIFACT_REQUIRED")
        apply(args.base)
