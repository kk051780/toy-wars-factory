#!/usr/bin/env python3
"""Fail-closed read-only inspection of an actual P0D RC82 Rojo Place and its source lock.

This is actual source evidence, NOT a Roblox engine test or OWNER acceptance.
"""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile, BadZipFile

ROLE_IDS = ("WARRIOR", "MAGE", "NINJA", "TRAPPER", "BUILDER", "BEAST_TAMER", "NECROMANCER")
SOURCE_ROLE_EXPECTATIONS = {
    "WARRIOR": "heavy multi-target hit + mobility",
    "MAGE": "ally healing and downed-ally revival",
    "NINJA": "visible Assassin label, server stealth and ambush",
    "TRAPPER": "placed traps and directed warp",
    "BUILDER": "traversable bridge and destructible blocking wall",
    "BEAST_TAMER": "independent summoned companion that follows and attacks",
    "NECROMANCER": "independent zombie squad that can be commanded",
}
SCRIPT_CLASSES = {"Script", "LocalScript", "ModuleScript"}

def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()

def inspect(place_data, source_lock, official_head):
    fail = []
    if not re.fullmatch(r"[0-9a-f]{40}", official_head or ""):
        fail.append("OFFICIAL_HEAD_NOT_PINNED")
    try:
        root = ET.fromstring(place_data)
    except ET.ParseError:
        return {"decision": "SOURCE_INTEGRITY_NO_GO", "problems": ["INVALID_PLACE_XML"],
                "gameplay_engine_pass": False, "role_source_findings": {}}
    scripts = []
    for item in root.iter("Item"):
        if item.get("class") not in SCRIPT_CLASSES:
            continue
        props = item.find("Properties")
        if props is None:
            fail.append("SCRIPT_MISSING_PROPERTIES")
            continue
        name = props.findtext("string[@name='Name']")
        source = props.findtext("string[@name='Source']")
        if not isinstance(name, str) or source is None:
            fail.append("SCRIPT_MISSING_NAME_OR_SOURCE")
            continue
        scripts.append((name, git_blob(source.encode("utf-8")), source))
    locks = source_lock.get("blobs") if isinstance(source_lock, dict) else None
    if not isinstance(locks, dict) or not locks:
        fail.append("SOURCE_LOCK_MISSING")
        locks = {}
    expected_count = source_lock.get("total_scripts") if isinstance(source_lock, dict) else None
    if len(scripts) != expected_count or len(locks) != expected_count:
        fail.append("SOURCE_COUNT_MISMATCH")
    if Counter(s[1] for s in scripts) != Counter(locks.values()):
        fail.append("PLACE_SOURCE_GITBLOBS_DO_NOT_MATCH_LOCK")
    def get_script(name):
        matches = [s[2] for s in scripts if s[0] == name]
        if len(matches) != 1:
            fail.append("EXPECTED_EXACTLY_ONE_SCRIPT:" + name)
            return ""
        return matches[0]
    game = get_script("Game")
    rules = get_script("SevenJobsRules")
    hud = get_script("TrapRaidersHUD")
    begin = game.find("local function useSevenJob(")
    end = game.find("\nlocal function applyModeVote(", begin + 1)
    if begin < 0 or end < 0:
        fail.append("SEVEN_JOB_DISPATCH_NOT_FOUND")
        block = ""
    else:
        block = game[begin:end]
    # Ignore the preceding BUILDER eligibility guard: the real seven-way skill
    # dispatch begins after the authoritative cooldown charge and FX setup.
    dispatch_start = block.find('if job=="WARRIOR" then')
    dispatch = block[dispatch_start:] if dispatch_start >= 0 else ""
    def segment(role):
        m = re.search(r'(?:if|elseif)\s+job\s*==\s*"' + role + r'"\s+then', dispatch)
        if not m:
            return ""
        follow = re.search(r'\belseif\s+job\s*==\s*"[A-Z_]+"\s+then', dispatch[m.end():])
        return dispatch[m.end():m.end() + follow.start()] if follow else dispatch[m.end():]
    seg = {r: segment(r) for r in ROLE_IDS}
    for r in ROLE_IDS:
        if not seg[r]:
            fail.append("ROLE_BRANCH_NOT_FOUND:" + r)
    source_findings = {}
    # These conditions intentionally detect *only* narrow author-defined MVP code.
    # No branch gets FULL_PASS from static inspection.
    for role in ROLE_IDS:
        source_findings[role] = {
            "expectation": SOURCE_ROLE_EXPECTATIONS[role],
            "present_in_dispatch": bool(seg[role]),
            "full_gameplay_status": "ENGINE_NOT_VERIFIED",
            "source_gap": None,
        }
    if seg["MAGE"] and "sevenJobStrike(" in seg["MAGE"] and not any(x in seg["MAGE"] for x in ("Health", "healAlly", "revive", "MageSupport")):
        source_findings["MAGE"]["source_gap"] = "PVE_FAN_ATTACK_ONLY_NO_HEAL_OR_REVIVE_IN_BRANCH"
    if seg["NINJA"] and "sevenJobStrike(" in seg["NINJA"] and not any(x in game for x in ("NinjaStealthService", "AssassinStealth", "NINJA_STEALTH")):
        source_findings["NINJA"]["source_gap"] = "PVE_STRIKE_ONLY_NO_STEALTH_SERVICE_REFERENCE"
    if seg["TRAPPER"] and "sevenJobStrike(" in seg["TRAPPER"] and not any(x in seg["TRAPPER"].lower() for x in ("warp", "teleport", "pivotto", "cframe=")):
        source_findings["TRAPPER"]["source_gap"] = "PVE_RING_ATTACK_ONLY_NO_WARP_IN_BRANCH"
    if seg["BUILDER"] and "wall.CanCollide=false" in seg["BUILDER"] and not any(x in seg["BUILDER"] for x in ("Bridge", "BuilderRoutesService")):
        source_findings["BUILDER"]["source_gap"] = "NONCOLLIDING_TURRET_ONLY_NOT_WALL_BRIDGE"
    if seg["BEAST_TAMER"] and "sevenJobStrike(" in seg["BEAST_TAMER"] and "BeastCompanionService" not in game:
        source_findings["BEAST_TAMER"]["source_gap"] = "PVE_STRIKE_ONLY_NO_ROLE_COMPANION_SERVICE"
    if seg["NECROMANCER"] and "sevenJobStrike(" in seg["NECROMANCER"] and "ZombieSquadService" not in game:
        source_findings["NECROMANCER"]["source_gap"] = "PVE_STRIKE_ONLY_NO_REAL_ZOMBIE_SQUAD_SERVICE"
    # Lobby and job selection security regressions from the OWNER's actual RC.
    pick = game.split("local function selectSevenJob(", 1)[-1].split("\nlocal function sevenJobFlash(", 1)[0]
    ready = game.split("local function applyReady(", 1)[-1].split("\nremote.OnServerEvent:Connect(", 1)[0]
    use = block
    if "sevenJobSelected[player]" not in ready:
        fail.append("UNSELECTED_PLAYER_CAN_READY_PRIVATE_JOB_TRIAL")
    if "sevenJobSelected[player]" not in use:
        fail.append("UNSELECTED_PLAYER_CAN_USE_PRIVATE_JOB")
    if "sevenJobSelected[other]==true" not in pick:
        fail.append("UNSELECTED_WARRIOR_CAN_RESERVE_CLASS_SLOT")
    if "roundReady[player]=false" not in pick and "roundReady[player] = false" not in pick:
        fail.append("JOB_CHANGE_DOES_NOT_CANCEL_OLD_READY")
    if 'label="暗殺者"' not in rules or "NINJA" not in rules or "暗殺者" not in hud:
        fail.append("ASSASSIN_DISPLAY_OR_INTERNAL_KEY_INCONSISTENT")
    gaps = sorted(r for r, rec in source_findings.items() if rec["source_gap"] is not None)
    return {
        "schema": "P0D_ACTUAL_PLACE_ROLE_SOURCE_AUDIT_V1",
        "official_rc_head": official_head,
        "place_bytes": len(place_data),
        "place_sha256": hashlib.sha256(place_data).hexdigest(),
        "scripts_examined": len(scripts),
        "source_lock_exact": not any(k in fail for k in
             ("SOURCE_COUNT_MISMATCH", "SOURCE_LOCK_MISSING", "PLACE_SOURCE_GITBLOBS_DO_NOT_MATCH_LOCK")),
        "role_source_findings": source_findings,
        "role_source_gaps": gaps,
        "problems": sorted(set(fail)),
        "decision": "SOURCE_INTEGRITY_NO_GO" if any(k in fail for k in
                    ("INVALID_PLACE_XML", "SOURCE_COUNT_MISMATCH",
                     "SOURCE_LOCK_MISSING", "PLACE_SOURCE_GITBLOBS_DO_NOT_MATCH_LOCK"))
                    else "GAMEPLAY_SOURCE_REMEDIATION_REQUIRED",
        "gameplay_engine_pass": False,
        "human_approved": False,
        "note": "Source anchored to genuine Place and lock; static gaps do not replace Roblox Studio, Android, art, competitive or OWNER FUN tests.",
    }

def inspect_zip(path, official_head):
    with ZipFile(path) as z:
        names = z.namelist()
        places = [n for n in names if n.endswith(".rbxlx")]
        if len(places) != 1 or "SOURCE_LOCK.json" not in names:
            raise ValueError("EXPECTED_ONE_PLACE_AND_SOURCE_LOCK")
        if any(n.startswith("/") or ".." in Path(n).parts for n in names):
            raise ValueError("UNSAFE_ARCHIVE_PATH")
        return inspect(z.read(places[0]), json.loads(z.read("SOURCE_LOCK.json")), official_head)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--artifact", required=True)
    p.add_argument("--official-head", required=True)
    p.add_argument("--report", required=True)
    a = p.parse_args()
    try:
        result = inspect_zip(a.artifact, a.official_head)
    except (OSError, ValueError, BadZipFile, KeyError, json.JSONDecodeError) as e:
        result = {"decision": "SOURCE_INTEGRITY_NO_GO", "problems": [type(e).__name__],
                  "gameplay_engine_pass": False, "human_approved": False}
    Path(a.report).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(result["decision"], result.get("scripts_examined"), result.get("role_source_gaps"))
    return 1 if result["decision"] == "SOURCE_INTEGRITY_NO_GO" else 0

if __name__ == "__main__":
    raise SystemExit(main())
