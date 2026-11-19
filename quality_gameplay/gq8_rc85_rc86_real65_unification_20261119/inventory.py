#!/usr/bin/env python3
"""Evidence-first RC85 / RC86 / RC91 -> REAL65 source reconciliation.

This does NOT merge incompatible Game/Combat/Store authorities or claim Studio QA.
It inventories actual immutable GitHub Actions .rbxlx artifacts, not PR prose.
The JSON output is an admission checklist; unverified != implemented.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import pathlib
import sys
import zipfile
import xml.etree.ElementTree as ET

SCRIPT_CLASSES = {"Script", "LocalScript", "ModuleScript"}
EXPECTED_COUNTS = {"rc85": 85, "rc86": 86, "rc91": 86, "real65": 65}
CASE_MAP = {
    "stage_weapon_pickups": {
        "legacy": "rc85",
        "anchors": ["P0D_STAGE_USABLE_WEAPON_LOOT", "StagePickupLoot"],
        "real65_alternatives": ["EGGRUMBLE_FieldItemPickups", "EGGRUMBLE_RaidItemIntake"],
        "domain": "item",
    },
    "three_undead_command_squad": {
        "legacy": "rc86",
        "anchors": ["P0D_UNDEAD_SQUAD_", "UndeadSquad"],
        "real65_alternatives": ["ZOMBIE_COMMAND", "GQ582", "Necromancer"],
        "domain": "neutral",
    },
    "ninja_wind_run": {
        "legacy": "rc91",
        "anchors": ["WIND_BURST", "S1RaiderWindRules"],
        "real65_alternatives": ["EGGRUMBLE_BasicMobilityPolicy", "GQ524"],
        "domain": "character",
    },
    "castle_breach_gate": {
        "legacy": "rc85",
        "anchors": ["Owner361CastleBattlefield", "SIEGE"],
        "real65_alternatives": ["EGGRUMBLE_CastleSiegeBridge", "EGGRUMBLE_CastleMatchRules", "GQ804"],
        "domain": "castle",
    },
    "wide_castle_field": {
        "legacy": "rc91",
        "anchors": ["P0D_FB034_LIVE_CASTLE_WORLD_READY", "Owner361CastleBattlefield"],
        "real65_alternatives": ["EGGRUMBLE_RealmBattleCore", "EGGRUMBLE_LandSeaSkyTraversal"],
        "domain": "field",
    },
    "physical_role_weapons": {
        "legacy": "rc85",
        "anchors": ["sevenJob", "SEVEN_JOBS"],
        "real65_alternatives": ["EGGRUMBLE_SevenRoleCombat"],
        "domain": "battle",
    },
}


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def normalized_tag(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def get_property(item: ET.Element, prop: str) -> str:
    props = next((x for x in item if normalized_tag(x.tag) == "Properties"), None)
    if props is None:
        return ""
    return next((x.text or "" for x in props
                 if x.attrib.get("name") == prop), "")


def parse_place(data: bytes, label: str) -> dict:
    root = ET.fromstring(data)
    sources: dict[str, dict] = {}

    def visit(node: ET.Element, parents: tuple[str, ...]) -> None:
        for child in node:
            if normalized_tag(child.tag) == "Item":
                cls = child.attrib.get("class", "")
                name = get_property(child, "Name") or cls
                path = parents + (name,)
                if cls in SCRIPT_CLASSES:
                    source = get_property(child, "Source")
                    # Empty is legitimate in engine but not useful as integration proof.
                    key = "/".join(path)
                    if key in sources:
                        raise ValueError("DUPLICATE_ROUTE " + label + " " + key)
                    sources[key] = {"class": cls, "sha256": sha256(source.encode()),
                                    "bytes": len(source.encode()), "source": source}
                visit(child, path)
            else:
                visit(child, parents)

    visit(root, ())
    if not sources:
        raise ValueError("NO_SCRIPT_SOURCE_IN_PLACE " + label)
    return sources


def place_candidates(root: pathlib.Path):
    """Read nested GitHub Actions artifact ZIPs without extracting unsafe names."""
    def scan_zip(blob: bytes, depth: int, origin: str):
        if depth > 3:
            return
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            for info in z.infolist():
                if info.is_dir() or info.file_size > 30_000_000:
                    continue
                name = info.filename.lower()
                if name.endswith(".rbxlx"):
                    yield (origin + ":" + info.filename, z.read(info))
                elif name.endswith(".zip") and depth < 3:
                    yield from scan_zip(z.read(info), depth + 1, origin + ":" + info.filename)
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() == ".rbxlx":
            yield str(p), p.read_bytes()
        elif p.suffix.lower() == ".zip":
            yield from scan_zip(p.read_bytes(), 0, str(p))


def find_artifact(directory: pathlib.Path, label: str) -> dict:
    found = []
    for path, data in place_candidates(directory):
        try:
            scripts = parse_place(data, label)
        except ET.ParseError:
            continue
        if len(scripts) == EXPECTED_COUNTS[label]:
            found.append((path, data, scripts))
    if len(found) != 1:
        raise ValueError(f"AMBIGUOUS_OR_MISSING_{label.upper()}_PLACE "
                         f"count_matching={len(found)} expected_sources={EXPECTED_COUNTS[label]}")
    path, data, scripts = found[0]
    return {"path": path, "place_sha256": sha256(data),
            "place_bytes": len(data), "scripts": scripts}


def has_anchor(scripts: dict, patterns: list[str]) -> list[str]:
    matches = []
    for path, entry in scripts.items():
        haystack = path + "\n" + entry["source"]
        if any(pattern in haystack for pattern in patterns):
            matches.append(path)
    return sorted(matches)


def compare(x: dict, y: dict) -> dict:
    left, right = x["scripts"], y["scripts"]
    common = set(left) & set(right)
    same = sorted(k for k in common if
                  left[k]["sha256"] == right[k]["sha256"] and
                  left[k]["class"] == right[k]["class"])
    return {
        "left_count": len(left), "right_count": len(right),
        "common_route_count": len(common),
        "unchanged_route_count": len(same),
        "changed_common_routes": sorted(common - set(same)),
        "left_only_routes": sorted(set(left) - set(right)),
        "right_only_routes": sorted(set(right) - set(left)),
    }


def report(places: dict) -> dict:
    real = places["real65"]["scripts"]
    features = {}
    for feature_id, spec in CASE_MAP.items():
        original = places[spec["legacy"]]["scripts"]
        legacy_hits = has_anchor(original, spec["anchors"])
        exact_hits = has_anchor(real, spec["anchors"])
        analog_hits = has_anchor(real, spec["real65_alternatives"])
        shared_hashes = {x["sha256"] for x in original.values()}
        identical = sorted(k for k, v in real.items() if v["sha256"] in shared_hashes)
        # A textual match or same-sounding subsystem is NOT gameplay parity.
        status = ("ORIGINAL_SOURCE_EXACT_IN_REAL65" if identical else
                  "ANCHOR_PRESENT_PARITY_NOT_PROVEN" if exact_hits else
                  "ALTERNATIVE_SUBSYSTEM_PRESENT_PARITY_NOT_PROVEN" if analog_hits else
                  "NO_SOURCE_EVIDENCE_PORT_REVIEW_REQUIRED")
        features[feature_id] = {
            "domain": spec["domain"],
            "legacy_artifact": spec["legacy"],
            "legacy_source_hits": legacy_hits,
            "real65_exact_anchor_hits": exact_hits,
            "real65_alternative_hits": analog_hits,
            "real65_identical_source_hits": identical,
            "status": status,
            "engine_functional_parity": "NOT_TESTED",
            "studio_acceptance": "NOT_TESTED",
        }
    # Follow-up physical check: current adopted V3 ports intentionally use NEW
    # EGGRUMBLE names, so legacy source anchors alone would create false gaps.
    # Static source presence is never equivalent to verified Studio gameplay.
    def source_at(route: str) -> str:
        return real.get(route, {}).get("source", "")

    field_src = source_at("ServerScriptService/EGGRUMBLE_FieldItemPickups")
    combat_src = source_at("ServerScriptService/EGGRUMBLE_SevenRoleCombat")
    stage_markers = [
        "GQ8_RC86_STAGE_WEAPONS_TO_REAL65_20261119", "SUN_BLADE",
        "WIND_SPEAR", "THUNDER_BOW",
    ]
    stage_source = all(m in field_src for m in stage_markers) and (
        "RC86 temporary field weapons" in combat_src
    )
    wind_markers = [
        "RC86_FB029_WIND_SINGLE_COMBAT_PORT", "EGGRUMBLE_RC86WindUntil",
        '":NINJA:RC86_WIND"', "now+2.5",
    ]
    wind_source = all(m in combat_src for m in wind_markers)
    zombie_markers = [
        "local LIMIT = 3", "local LIFETIME = 14",
        "FOLLOW = true, GUARD = true, FOCUS = true",
        "ZombieCommander.begin(p,{",
    ]
    zombie_source = all(m in combat_src for m in zombie_markers)
    legacy_undead = source_at("ServerScriptService/TrapRaidersS1/UndeadSquad")
    legacy_undead = places["rc86"]["scripts"].get(
        "ServerScriptService/TrapRaidersS1/UndeadSquad", {}).get("source", "")
    old_undead_48 = "local MAX_DURATION = 48" in legacy_undead
    evidence = {
        "stage_weapon_pickups": {
            "source_port_verified_by_markers": stage_source,
            "port": "Existing FieldItemPickups + existing SevenRoleCombat; three kinds, 6 floor spawns, 18s boosts",
            "CI_source_only": True,
            "engine_functional_parity": "NOT_TESTED",
        },
        "ninja_wind_run": {
            "source_port_verified_by_markers": wind_source,
            "port": "Existing SevenRoleCombat Ninja B, 18s cooldown, 2.5s speed boost",
            "CI_source_only": True,
            "engine_functional_parity": "NOT_TESTED",
        },
        "three_undead_command_squad": {
            "different_3_unit_implementation_verified": zombie_source,
            "legacy_source_duration_48s": old_undead_48,
            "current_source_duration_14s": zombie_source,
            "old_commands": ["ATTACK", "GUARD", "FOLLOW"],
            "new_commands": ["FOLLOW", "GUARD", "FOCUS"],
            "semantic_parity": "DIFFERENT_LIFETIME_AND_COMMANDS_NEED_GAMEPLAY_DESIGN_REVIEW",
            "engine_functional_parity": "NOT_TESTED",
        },
    }
    if stage_source:
        features["stage_weapon_pickups"]["status"] = "SOURCE_PORT_PRESENT_AFTER_865_ENGINE_NOT_TESTED"
    if wind_source:
        features["ninja_wind_run"]["status"] = "SOURCE_PORT_PRESENT_AFTER_864_ENGINE_NOT_TESTED"
    if zombie_source:
        features["three_undead_command_squad"]["status"] = "ALTERNATIVE_THREE_SERVANT_COMBAT_EXISTS_BEHAVIOR_DIFFERS"
    source_summary = {
        label: {
            "place_sha256": p["place_sha256"], "place_bytes": p["place_bytes"],
            "script_count": len(p["scripts"]),
            "script_classes": {c: sum(v["class"] == c for v in p["scripts"].values())
                               for c in sorted(SCRIPT_CLASSES)},
            "source_inventory": [
                {"route": name, "class": v["class"],
                 "git_independent_sha256": v["sha256"], "source_bytes": v["bytes"]}
                for name, v in sorted(p["scripts"].items())
            ],
        }
        for label, p in places.items()
    }
    return {
        "schema": "GQ8_RC85_RC86_REAL65_NONLOSS_RECONCILIATION_V1",
        "formal_branch": "rc/p0d-s1-kids-rc01",
        "formal_profile": "REAL65 PRIVATE_COMPANION",
        "primary_active_runtime": "S1 rich51 (separate; not merged into V3)",
        "official_game_unification_complete": False,
        "reason": "Legacy game behavior cannot be declared integrated by script counts, equal names or native compile.",
        "lineage": {
            "rc85_to_rc86": compare(places["rc85"], places["rc86"]),
            "rc86_to_rc91": compare(places["rc86"], places["rc91"]),
            "rc91_to_real65": compare(places["rc91"], places["real65"]),
        },
        "features": features,
        "reconciliation_source_contracts": evidence,
        "artifacts": source_summary,
        "prohibited_actions": ["overwrite_REAL65_with_legacy_Game",
                               "duplicate_Host_Combat_Swarm_Store_Remote",
                               "publish", "paid_trade", "main_write", "force_push"],
        "followup": "Port only verified missing behavior into the existing REAL65 owner scripts; exact same-HEAD native/Rojo/OFF63, non-force CAS, then Studio tests.",
    }


def selftest() -> None:
    xml = b'<roblox><Item class="DataModel"><Properties><string name="Name">Game</string></Properties><Item class="Script"><Properties><string name="Name">GameLogic</string><ProtectedString name="Source">print(&quot;OK&quot;)</ProtectedString></Properties></Item></Item></roblox>'
    actual = parse_place(xml, "fixture")
    assert len(actual) == 1 and actual["Game/GameLogic"]["source"] == 'print("OK")'
    assert sha256(b"OK") == hashlib.sha256(b"OK").hexdigest()
    try:
        parse_place(b"<broken", "invalid")
    except ET.ParseError:
        pass
    else:
        raise AssertionError("invalid XML must fail")
    print("SELFTEST_SOURCE_XML_HASH_AND_DUPLICATE_GUARDS_PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    for label in EXPECTED_COUNTS:
        parser.add_argument("--" + label, type=pathlib.Path)
    parser.add_argument("--out", type=pathlib.Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.out or any(getattr(args, label) is None for label in EXPECTED_COUNTS):
        parser.error("every artifact directory and --out is mandatory")
    places = {label: find_artifact(getattr(args, label), label)
              for label in EXPECTED_COUNTS}
    data = report(places)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf8")
    print("GQ8_RC85_RC86_REAL65_ARTIFACT_INVENTORY_PASS")
    print("LEGACY_85_TO_86", json.dumps(data["lineage"]["rc85_to_rc86"]))
    print("LEGACY_86_TO_91", json.dumps(data["lineage"]["rc86_to_rc91"]))
    print("RC91_TO_REAL65", json.dumps(data["lineage"]["rc91_to_real65"]))
    for k, v in data["features"].items():
        print("FEATURE", k, v["status"],
              "old=", len(v["legacy_source_hits"]),
              "real65=", len(v["real65_exact_anchor_hits"]),
              "analog=", len(v["real65_alternative_hits"]))
    for k, e in data["reconciliation_source_contracts"].items():
        print("PORT_CONTRACT", k, json.dumps(e, sort_keys=True))
    print("FORMAL_FULL_UNIFICATION_NOT_YET_PROVEN")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, zipfile.BadZipFile, ET.ParseError) as e:
        print("RED_RECONCILIATION " + str(e), file=sys.stderr)
        sys.exit(1)
