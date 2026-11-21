#!/usr/bin/env python3
"""Source-exact 69->70 PRIVATE preview, never official RC, never Studio.
Safe A candidate for B220 sole certified writer after playable P0 priority.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

BASE = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
PLACE_SHA256 = "fc63171149a86f6b39779ba6ebe7e18fcb7099fbde98ad2ec33a7cb92b3a9934"
PLACE_BYTES = 798390
PROJECT = "EGGRUMBLE_REAL69.project.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
ROUTE = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_PlayerTeamCrest"
REL = "sources/StarterPlayer/StarterPlayerScripts/EGGRUMBLE_PlayerTeamCrest.client.luau"
PACK = "B220_AVATAR_TEAM_CREST_ONE_CLIENT_NOT_FORMAL"
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "EGGRUMBLE_PlayerTeamCrest.client.luau"
sys.path.insert(0, str(ROOT.parent / "gq8_rc85_rc86_real68_nonloss_20261120"))
from verify_nonloss import project_scan  # Same canonical project/source scanner.


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("RED_GQ470_CREST_" + message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compose(official: Path, out: Path) -> dict:
    official, out = official.resolve(), out.resolve()
    require(official.is_dir() and not out.exists() and official != out,
            "NONEXISTENT_OUTPUT_ORIGINAL")
    original_place = (official / PLACE).read_bytes()
    require(len(original_place) == PLACE_BYTES and
            sha256(original_place) == PLACE_SHA256, "ORIGINAL_PLACE_IDENTITY")
    official_receipt = json.loads((official / RECEIPT).read_text(encoding="utf-8"))
    require(official_receipt.get("canonical_build") is True and
            official_receipt.get("build_head") == BASE and
            official_receipt.get("selected_source_count") == 69 and
            official_receipt.get("official_branch") == "rc/p0d-s1-kids-rc01",
            "OFFICIAL_RECEIPT_IDENTITY")
    source_map = project_scan(official, PROJECT)
    require(len(source_map) == 69 and ROUTE not in source_map and
            set(source_map) == set(official_receipt["source_hashes"]) ==
            set(official_receipt["source_classes"]), "ORIGINAL_SELECTION_SET")
    require(all(source_map[k]["sha256"] == official_receipt["source_hashes"][k] and
                source_map[k]["class"] == official_receipt["source_classes"][k]
                for k in source_map), "ORIGINAL_SOURCE_HASHES")
    require(len(SRC.read_bytes()) > 0, "NEW_SOURCE_EMPTY")
    shutil.copytree(official, out)
    project_path = out / PROJECT
    project = json.loads(project_path.read_text(encoding="utf-8"))
    scripts = project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    require(isinstance(scripts, dict) and "$path" not in scripts and
            "EGGRUMBLE_PlayerTeamCrest" not in scripts,
            "EXISTING_STARTER_SCRIPT_COLLISION")
    scripts["EGGRUMBLE_PlayerTeamCrest"] = {"$path": REL}
    destination = out / REL
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(SRC.read_bytes())
    project_path.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    candidate = project_scan(out, PROJECT)
    require(len(candidate) == 70 and
            set(candidate) == set(source_map) | {ROUTE} and
            all(candidate[k] == source_map[k] for k in source_map),
            "ONE_ADDED_AND_69_EXACT_ORIGINAL")
    require(candidate[ROUTE]["class"] == "LocalScript" and
            candidate[ROUTE]["sha256"] == sha256(SRC.read_bytes()),
            "NEW_CLIENT_EXACT_SOURCE_CLASS")
    result = {
        "schema": "GQ470_FB015_AVATAR_TEAM_CREST_REAL70_A_ONLY_V1",
        "official_branch": "rc/p0d-s1-kids-rc01",
        "base_head": BASE,
        "source_profile": "PRIVATE_COMPANION_REAL70_A_ONLY",
        "original_selected_source_count": 69,
        "original_sources_preserved": 69,
        "candidate_source_count": 70,
        "optional_added_route": ROUTE,
        "optional_source_sha256": candidate[ROUTE]["sha256"],
        "new_server_script_count": 0,
        "new_remote_count": 0,
        "max_client_parts_per_avatar": 2,
        "official_place_bytes": PLACE_BYTES,
        "official_place_sha256": PLACE_SHA256,
        "formal_rc_adopted": False,
        "player_spawn_fixed": False,
        "studio": "NOT_TESTED",
        "android": "NOT_TESTED",
        "human_art": "NOT_TESTED",
        "screenshots": "0/32",
        "owner_accepted": False,
        "art_gate": "ART_NO_GO",
        "product_gate": "PRODUCT_NO_GO"
    }
    (out / "GQ470_AVATAR_CREST_A_RECEIPT.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def export_packet(candidate: Path, place: Path) -> dict:
    candidate, place = candidate.resolve(), place.resolve()
    receipt = json.loads((candidate / "GQ470_AVATAR_CREST_A_RECEIPT.json")
                         .read_text(encoding="utf-8"))
    original = project_scan(candidate, PROJECT)
    raw = (candidate / REL).read_bytes()
    require(len(original) == 70 and original[ROUTE]["sha256"] == sha256(raw) and
            original[ROUTE]["class"] == "LocalScript" and raw == SRC.read_bytes(),
            "PACKET_SOURCE_EXACT")
    require(receipt["base_head"] == BASE and
            receipt["original_sources_preserved"] == 69 and
            receipt["formal_rc_adopted"] is False and
            receipt["owner_accepted"] is False and
            receipt["art_gate"] == "ART_NO_GO", "PACKET_STATUS_NOT_HONEST")
    require(place.is_file() and place.stat().st_size > PLACE_BYTES and
            sha256(place.read_bytes()) != PLACE_SHA256, "PACKET_NEEDS_BUILT_PLACE")
    packet = candidate / PACK
    require(not packet.exists(), "PACKET_MUST_NOT_OVERWRITE")
    target = packet / "selected_sources" / REL.removeprefix("sources/")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    result = {
        "schema": "GQ470_FB015_CREST_B220_SELECTED_SOURCE_V1",
        "source_only": True,
        "formal_branch": "rc/p0d-s1-kids-rc01",
        "formal_base_head": BASE,
        "new_script_route": ROUTE,
        "new_source_class": "LocalScript",
        "source_path": target.relative_to(packet).as_posix(),
        "source_sha256": sha256(raw),
        "source_bytes": len(raw),
        "original_unchanged": 69,
        "candidate_sources": 70,
        "candidate_place_bytes": place.stat().st_size,
        "candidate_place_sha256": sha256(place.read_bytes()),
        "formal_rc_adopted": False,
        "certified_b220_fresh_cas_required": True,
        "admission": "DEFER_PLAYER_SPAWN_AND_P0_910_AND_ART16",
        "art_status": "ART_NO_GO",
        "studio_android_fun": "NOT_TESTED",
        "owner_accepted": False,
    }
    (packet / "SOURCE_SELECT_MANIFEST.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    verify_packet(candidate, place)
    return result


def verify_packet(candidate: Path, place: Path) -> None:
    candidate, place = candidate.resolve(), place.resolve()
    packet = candidate / PACK
    r = json.loads((packet / "SOURCE_SELECT_MANIFEST.json").read_text(encoding="utf-8"))
    raw = (candidate / REL).read_bytes()
    selected = packet / r["source_path"]
    require(selected.resolve().is_relative_to(packet) and
            selected.read_bytes() == raw and raw == SRC.read_bytes() and
            r["schema"] == "GQ470_FB015_CREST_B220_SELECTED_SOURCE_V1" and
            r["formal_base_head"] == BASE and r["new_script_route"] == ROUTE and
            r["new_source_class"] == "LocalScript" and
            r["source_sha256"] == sha256(raw) and r["source_bytes"] == len(raw) and
            r["original_unchanged"] == 69 and r["candidate_sources"] == 70 and
            r["formal_rc_adopted"] is False and
            r["certified_b220_fresh_cas_required"] is True and
            r["art_status"] == "ART_NO_GO" and
            r["owner_accepted"] is False and
            r["candidate_place_bytes"] == place.stat().st_size and
            r["candidate_place_sha256"] == sha256(place.read_bytes()),
            "PACKET_MANIFEST_INTEGRITY")
    found = {p.relative_to(packet).as_posix() for p in packet.rglob("*") if p.is_file()}
    require(found == {"SOURCE_SELECT_MANIFEST.json", r["source_path"]},
            "PACKET_UNEXPECTED_FILES")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--official", type=Path)
    p.add_argument("--out", type=Path)
    p.add_argument("--export-b", type=Path)
    p.add_argument("--verify-b", type=Path)
    p.add_argument("--place", type=Path)
    opt = p.parse_args()
    if opt.export_b:
        require(opt.place is not None, "MISSING_BUILT_PLACE")
        print(json.dumps(export_packet(opt.export_b, opt.place), indent=2))
    elif opt.verify_b:
        require(opt.place is not None, "MISSING_BUILT_PLACE")
        verify_packet(opt.verify_b, opt.place)
        print("B220_ONE_SOURCE_PACKET_EXACT_PASS")
    else:
        require(opt.official is not None and opt.out is not None, "INPUTS_REQUIRED")
        print(json.dumps(compose(opt.official, opt.out), indent=2))
