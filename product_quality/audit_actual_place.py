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
# Paths are the actual Rojo locations. Four historical source-file aliases have
# intentional different Roblox Instance names; no fuzzy basename matching.
SCRIPT_ROOTS = {
    ("ServerScriptService", "TrapRaidersS1"): "server",
    ("StarterPlayer", "StarterPlayerScripts"): "client",
    ("ReplicatedStorage", "TrapRaidersShared"): "shared",
}
SCRIPT_ALIASES = {
    ("client", "TrapRaidersHUD"): "client/HUD.client.luau",
    ("client", "P0DConfirmedCombatFX"): "client/ConfirmedSlashFX.client.luau",
    ("client", "TrapRaidersCoach"): "client/FirstMinuteCoach.client.luau",
    ("client", "FB015GoroganVisual"): "client/FB015CharacterArt.client.luau",
}

def lock_path(ancestors, name, script_class):
    lane = SCRIPT_ROOTS.get(tuple(ancestors))
    if lane is None:
        return None
    suffix = (".server.luau" if script_class == "Script"
              else ".client.luau" if script_class == "LocalScript"
              else ".luau")
    return SCRIPT_ALIASES.get((lane, name), lane + "/" + name + suffix)

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
    by_path = {}
    def walk(parent, ancestors):
        for item in parent.findall("Item"):
            props = item.find("Properties")
            name = props.findtext("string[@name='Name']") if props is not None else None
            script_class = item.get("class")
            if script_class in SCRIPT_CLASSES:
                source = props.findtext("string[@name='Source']") if props is not None else None
                if not isinstance(name, str) or source is None:
                    fail.append("SCRIPT_MISSING_NAME_OR_SOURCE")
                else:
                    blob = git_blob(source.encode("utf-8"))
                    scripts.append((name, blob, source))
                    path = lock_path(ancestors, name, script_class)
                    if path is None:
                        fail.append("SCRIPT_UNEXPECTED_LOCATION:" + name)
                    elif path in by_path:
                        fail.append("DUPLICATE_SOURCE_PATH:" + path)
                    else:
                        by_path[path] = blob
            walk(item, ancestors + [name or ""])
    walk(root, [])
    locks = source_lock.get("blobs") if isinstance(source_lock, dict) else None
    if not isinstance(locks, dict) or not locks:
        fail.append("SOURCE_LOCK_MISSING")
        locks = {}
    expected_count = source_lock.get("total_scripts") if isinstance(source_lock, dict) else None
    if len(scripts) != expected_count or len(locks) != expected_count:
        fail.append("SOURCE_COUNT_MISMATCH")
    if Counter(s[1] for s in scripts) != Counter(locks.values()):
        fail.append("PLACE_SOURCE_GITBLOBS_DO_NOT_MATCH_LOCK")
    # Multiset equality alone can be fooled by swapping code between Scripts.
    # Require same path, Script/LocalScript/ModuleScript kind, and byte content.
    if set(by_path) != set(locks):
        fail.append("PLACE_SOURCE_PATH_SET_MISMATCH")
    if any(by_path[p] != locks[p] for p in set(by_path) & set(locks)):
        fail.append("PLACE_SOURCE_PATH_BLOB_MISMATCH")
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
    integrity = ("SOURCE_COUNT_MISMATCH", "SOURCE_LOCK_MISSING",
                 "PLACE_SOURCE_GITBLOBS_DO_NOT_MATCH_LOCK",
                 "PLACE_SOURCE_PATH_SET_MISMATCH", "PLACE_SOURCE_PATH_BLOB_MISMATCH")
    integrity_failed = any(k in fail for k in integrity) or any(
        f.startswith(("SCRIPT_UNEXPECTED_LOCATION:", "DUPLICATE_SOURCE_PATH:"))
        for f in fail)
    return {
        "schema": "P0D_ACTUAL_PLACE_ROLE_SOURCE_AUDIT_V1",
        "official_rc_head": official_head,
        "place_bytes": len(place_data),
        "place_sha256": hashlib.sha256(place_data).hexdigest(),
        "scripts_examined": len(scripts),
        "source_lock_exact": not integrity_failed,
        "source_path_exact": not integrity_failed,
        "source_paths_matched": sum(
            by_path[p] == locks[p] for p in set(by_path) & set(locks)),
        "role_source_findings": source_findings,
        "role_source_gaps": gaps,
        "problems": sorted(set(fail)),
        "decision": "SOURCE_INTEGRITY_NO_GO" if integrity_failed
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
