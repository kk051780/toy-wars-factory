#!/usr/bin/env python3
"""REAL63 -> successor fail-closed source regression gate.

Actual official Real63 source/receipt are read from immutable same-head GitHub
Actions artifact, NOT recreated from a stale Real62/Real55 author PR.
This gate cannot certify Roblox Studio, art or FUN.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

BASE_HEAD = "ad602cebafc1a9d8caed078ab86c7a58b0fbbbef"
HOST = "ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview"
COMBAT = "ServerScriptService/EGGRUMBLE_SevenRoleCombat"
SWARM = "ServerScriptService/EGGRUMBLE_SwarmCombat"
INVUL = "ServerScriptService/EGGRUMBLE_InvulRuntime"
POLICY = "ServerScriptService/EGGRUMBLE_BasicMobilityPolicy"
HUD = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_HudIntelRuntime"

# Source-presence evidence only, inherited from verified original Real55/59/62.
DOMAINS = {
    "characters": [COMBAT, "ServerScriptService/EGGRUMBLE_CurseConversionPolicy"],
    "field": ["ServerScriptService/EGGRUMBLE_RealmBattleCore",
              "ServerScriptService/GQ802_StageTileVisualRenderer",
              "ServerScriptService/EGGRUMBLE_MapVisibilityPolicy"],
    "combat": [COMBAT, INVUL, "ServerScriptService/EGGRUMBLE_MusouFeverPolicy"],
    "castles": [HOST, "ServerScriptService/EGGRUMBLE_CastleGuardianRuntime"],
    "neutrals": [SWARM, "ServerScriptService/EGGRUMBLE_CurseConversionPolicy"],
    "items": ["ServerScriptService/EGGRUMBLE_FieldItemPickups",
              "ServerScriptService/GQ8_TradeJournalContract",
              "ServerScriptService/GQ8_TradeEscrowReducer"],
    "lobby": ["ServerScriptService/GQ8_LobbySocialPlaza",
              "ServerScriptService/GQ805_LobbyGuildShop"],
    "ui": [HUD, "ReplicatedStorage/EGGRUMBLE_HudPresentationPolicy",
           "ServerScriptService/EGGRUMBLE_MapIntelBridge"],
    "balance": ["ServerScriptService/EGGRUMBLE_InvulnerabilityPolicy",
                "ServerScriptService/EGGRUMBLE_MusouFeverPolicy"],
}
# The currently pending Real64 proposal is allowed to touch exactly these
# original owners; NO version of the proposal may drop Real63 basic/dodge.
ALLOW_OWNER_PATCHES = {HOST, COMBAT, INVUL, HUD}

def require(predicate, code):
    if not predicate:
        raise ValueError("RED_" + code)

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def read_place(path: Path):
    """Parse actual Rojo .rbxlx, retaining Script/ModuleScript/LocalScript classes."""
    sources = {}
    def walk(item, prefix):
        properties = item.find("Properties")
        name = properties.findtext("string[@name='Name']") if properties is not None else None
        require(bool(name and re.fullmatch(r"[A-Za-z0-9_]+", name)), "BAD_ROUTE")
        route = prefix + (name,)
        kind = item.get("class")
        if kind in ("Script", "LocalScript", "ModuleScript"):
            source = properties.findtext("string[@name='Source']")
            if source is None:
                source = properties.findtext("ProtectedString[@name='Source']")
            require(source is not None, "NO_SOURCE")
            key = "/".join(route)
            require(key not in sources, "DUPLICATE_ROUTE")
            sources[key] = (kind, source.replace("\r\n", "\n").encode("utf-8"))
        for child in item.findall("Item"):
            walk(child, route)
    for top in ET.parse(path).getroot().findall("Item"):
        walk(top, ())
    return sources

def evidence(sources):
    require(len(DOMAINS) == 9, "NINE_DOMAIN_CONFIG")
    coverage = {}
    for area, routes in DOMAINS.items():
        require(all(k in sources for k in routes), "DOMAIN_MISSING_" + area.upper())
        coverage[area] = "SOURCE_PRESENT_STUDIO_NOT_TESTED"
    return coverage

def require_basic_dodge(sources):
    require(HOST in sources and sources[HOST][0] == "Script", "HOST_INERT")
    require(COMBAT in sources and sources[COMBAT][0] == "ModuleScript", "COMBAT_OWNER_CLASS")
    require(HUD in sources and sources[HUD][0] == "LocalScript", "HUD_OWNER_CLASS")
    require(POLICY in sources and sources[POLICY][0] == "ModuleScript", "LOST_REAL63_POLICY")
    combat = sources[COMBAT][1]
    hud = sources[HUD][1]
    for name, token in [
        ("BASIC_TOOL", b"EGGRUMBLE_BASIC_ATTACK"),
        ("DODGE_TOOL", b"EGGRUMBLE_DODGE_STEP"),
        ("BASIC_SERVER_POLICY", b"EGGRUMBLE_BasicMobilityPolicy"),
        ("SERVER_TOOL_CALLBACK", b"executeCoreAction(session,p,role,action,core)"),
    ]:
        require(token in combat, "LOST_REAL63_" + name)
    for name, token in [
        ("DODGE_CLICK", b"actions.DODGE.Activated:Connect("),
        ("DODGE_TOOL_LOOKUP", b"EGGRUMBLE_DODGE_STEP"),
        ("BASIC_TOOL_LOOKUP", b"EGGRUMBLE_BASIC_ATTACK"),
        ("SKILL_SEPARATION", b"local reserved=p.CONTEXT"),
    ]:
        require(token in hud, "LOST_REAL63_HUD_" + name)
    require(combat.count(b"executeCoreAction(session,p,role,action,core)") == 1,
            "DUPLICATE_BASIC_DODGE_SERVER_CALLBACK")
    require(hud.count(b"actions.DODGE.Activated:Connect(") == 1,
            "DUPLICATE_DODGE_TOUCH_CALLBACK")
    for root in (HOST, COMBAT, SWARM):
        name = root.split("/")[-1]
        require(sum(k.split("/")[-1] == name for k in sources) == 1,
                "DUPLICATE_AUTHORITY_" + name)
    return evidence(sources)

def verify_real63(place: Path, receipt: Path, expected_head: str = BASE_HEAD):
    require(re.fullmatch("[a-f0-9]{40}", expected_head) is not None, "BAD_SHA")
    source = read_place(place)
    report = json.loads(receipt.read_text(encoding="utf-8"))
    require(len(source) == 63, "BASE63_SOURCE_COUNT")
    require(report.get("candidate_git_head") == expected_head and
            report.get("official_rc_adopted") is True and
            report.get("native") == "PASS" and report.get("rojo") == "PASS" and
            report.get("off62") == "PASS", "NOT_VERIFIED_FORMAL63")
    require(report.get("candidate_sources") == 63 and
            report.get("parent_original_sources") == 62 and
            report.get("place_sha256") == digest(place.read_bytes()),
            "REAL63_PHYSICAL_IDENTITY")
    require(report.get("robuxtx_enabled") is False and
            report.get("roblox_published") is False, "FALSE_PAID_OR_PUBLISH_CLAIM")
    index = {}
    rows = report.get("on_sources", [])
    require(isinstance(rows, list) and len(rows) == 63, "REAL63_LEDGER_COUNT")
    for row in rows:
        key = row.get("route")
        require(key not in index, "DUPLICATE_LEDGER")
        index[key] = row
    require(set(index) == set(source), "REAL63_LEDGER_ROUTES")
    for key, (kind, data) in source.items():
        r = index[key]
        require(r.get("class") == kind and r.get("sha256") == digest(data)
                and r.get("bytes") == len(data),
                "REAL63_LEDGER_CLASS_BYTES_" + key.replace("/", "_"))
    coverage = require_basic_dodge(source)
    return source, {"formal_real63_sha": expected_head,
                    "formal_real63_sources": 63,
                    "source_domain_evidence": coverage,
                    "roblox_studio": "NOT_TESTED",
                    "android_15min": "NOT_TESTED",
                    "fun": "NO_GO"}

def verify_successor(base, candidate, allowed_modified=ALLOW_OWNER_PATCHES,
                     max_additions=2):
    """Successor admissions must preserve all canonical 63 routes and real Tools.

    A future Real65 may modify exactly current Host/Combat/Invul/HUD owner bodies.
    Replacements of 63 sources with Real55/62 snapshots are rejected.
    """
    require(len(base) == 63, "INVALID_BASE63")
    require(len(candidate) >= 63 and len(candidate) <= 63 + max_additions,
            "SUCCESSOR_SOURCE_COUNT")
    require(set(base) <= set(candidate), "REAL63_SOURCE_DROPPED")
    for route, old in base.items():
        new = candidate[route]
        require(new[0] == old[0], "REAL63_CLASS_DRIFT")
        if new[1] != old[1]:
            require(route in allowed_modified, "UNAUTHORIZED_63_OWNER_CHANGE_" +
                    route.replace("/", "_"))
    added = set(candidate) - set(base)
    require(all(candidate[x][0] in ("Script", "LocalScript", "ModuleScript")
                for x in added), "INVALID_ADDED_CLASS")
    coverage = require_basic_dodge(candidate)
    return {"candidate_count": len(candidate), "added_routes": sorted(added),
            "modified_authorities": sorted(k for k in base if base[k] != candidate[k]),
            "nine_domain_source_evidence": coverage,
            "real63_normal_attack_and_dodge_retained": True,
            "studio_2client": "NOT_TESTED", "art_fun": "NO_GO"}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--real63-place", required=True, type=Path)
    p.add_argument("--real63-receipt", required=True, type=Path)
    p.add_argument("--expected-head", default=BASE_HEAD)
    p.add_argument("--successor-place", type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    base, report = verify_real63(a.real63_place, a.real63_receipt, a.expected_head)
    if a.successor_place:
        report["successor"] = verify_successor(base, read_place(a.successor_place))
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    print("GQ8_REAL63_NINE_DOMAIN_SOURCE_BASIC_DODGE_SUCCESSOR_FENCE_PASS")

if __name__ == "__main__":
    main()
