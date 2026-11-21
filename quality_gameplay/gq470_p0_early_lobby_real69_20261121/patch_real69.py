#!/usr/bin/env python3
"""P0: safely create the existing lobby floor/SpawnLocation *before* Host requires.

This is a reversible REAL69 source-only A PREP, not a Studio spawn fix verdict.
All original 69 scripts, project, egg, game, score and authority are preserved
except the one Host's creation *ordering*. No extra Part/SpawnLocation exists.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

OFFICIAL = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
ROUTE = "ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview"
OLD_HOST_SHA = "8d8f6a63db5dd24740f787437b7aa88edfbaaa9c2aae062b07a884e59c06ad85"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
FEATURE = "GQ470_P0_EARLY_EXISTING_LOBBY_SPAWN_REAL69_20261121"
START = 'if not RunService:IsStudio() then return end\n'
OLD_ROOT = '''local spawn=workspace:FindFirstChildWhichIsA("SpawnLocation",true)::SpawnLocation?
local root=spawn and spawn.Position or Vector3.new(0,4,0)
local folder=Instance.new("Folder");folder.Name="EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW";folder.Parent=workspace
'''
FLOOR_START = 'local lobbyGround=Instance.new("Part")\n'
FLOOR_END = 'lobbySpawn.Parent=folder\n'
NEW_ROOT = '''local spawn=gqEarlyOriginalSpawn
local root=gqEarlyRoot
local folder=gqEarlyFolder
'''
REUSE = '''local lobbyGround=gqEarlyGround
local lobbySpawn=gqEarlySpawn
'''
EARLY = '''-- GQ470_P0_EARLY_EXISTING_LOBBY_SPAWN_REAL69_20261121
-- Preserve the actual preexisting spawn/root; create exactly the original
-- GQ646 floor+neutral SpawnLocation before potentially blocking module requires.
local gqEarlyOriginalSpawn=workspace:FindFirstChildWhichIsA("SpawnLocation",true)::SpawnLocation?
local gqEarlyRoot=gqEarlyOriginalSpawn and gqEarlyOriginalSpawn.Position or Vector3.new(0,4,0)
local gqEarlyFolder=Instance.new("Folder")
gqEarlyFolder.Name="EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW"
gqEarlyFolder.Parent=workspace
'''


def sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def need(condition: bool, detail: str) -> None:
    if not condition:
        raise ValueError("RED_P0_EARLY_LOBBY_" + detail)


def selected(root: Path) -> dict[str, tuple[Path, str]]:
    tree = json.loads((root / PROJECT).read_text())["tree"]
    paths: dict[str, tuple[Path, str]] = {}
    def walk(node: dict, prefix: str = "") -> None:
        if "$path" in node:
            path = (root / node["$path"]).resolve()
            need(path.is_relative_to(root.resolve()) and path.is_file(), "PATH_ESCAPED")
            need(prefix not in paths, "DUPLICATE_ROUTE")
            paths[prefix] = (path, node.get("$className", ""))
        for name, sub in node.items():
            if not name.startswith("$") and isinstance(sub, dict):
                walk(sub, f"{prefix}/{name}" if prefix else name)
    walk(tree)
    return paths


def transform(source: str) -> str:
    need(FEATURE not in source, "ALREADY_PATCHED")
    for fragment, label in [(START, "STUDIO_FENCE"), (OLD_ROOT, "ROOT"),
                            (FLOOR_START, "GROUND"), (FLOOR_END, "SPAWN_END")]:
        need(source.count(fragment) == 1, "ANCHOR_" + label)
    begin = source.index(FLOOR_START)
    end = source.index(FLOOR_END, begin) + len(FLOOR_END)
    original_floor = source[begin:end]
    need(original_floor.count('Instance.new("Part")') == 1, "GROUND_PART_COUNT")
    need(original_floor.count('Instance.new("SpawnLocation")') == 1, "SPAWN_PART_COUNT")
    need("lobbyGround.Parent=folder" in original_floor and
         "lobbySpawn.Parent=folder" in original_floor and
         "lobbySpawn.Enabled=true" in original_floor, "LOBBY_SAFE_SETUP")
    relocated_floor = (original_floor
                       .replace("lobbyGround", "gqEarlyGround")
                       .replace("lobbySpawn", "gqEarlySpawn")
                       .replace("root+Vector3", "gqEarlyRoot+Vector3")
                       .replace("Parent=folder", "Parent=gqEarlyFolder"))
    need(relocated_floor.count('Instance.new("Part")') == 1 and
         relocated_floor.count('Instance.new("SpawnLocation")') == 1,
         "RELOCATED_INSTANCE_COUNT")
    source = source[:begin] + REUSE + source[end:]
    source = source.replace(OLD_ROOT, NEW_ROOT, 1)
    source = source.replace(START, START + EARLY + relocated_floor, 1)
    need(source.count(FEATURE) == 1, "MARKER_COUNT")
    need(source.count('Instance.new("SpawnLocation")') == 1 and
         source.count('Name="GQ646_LOBBY_SAFE_GROUND"') == 1,
         "EXACT_ONE_LOBBY_PAIR")
    need(source.index("gqEarlySpawn.Parent=gqEarlyFolder") <
         source.index('local Rules=require'), "EARLY_BEFORE_REQUIRE")
    need(source.index("local lobbyGround=gqEarlyGround") >
         source.index('local GQ802StageManifest=require'), "ORIGINAL_LATER_REUSE")
    return source


def rollback(candidate: str, original: str) -> bool:
    """We compare byte-exact to the original full Host instead of trusting a marker."""
    return transform(original) == candidate


def patch(root: Path, expected_head: str) -> dict:
    need(expected_head == OFFICIAL, "OFFICIAL_HEAD_MISMATCH")
    receipt = json.loads((root / RECEIPT).read_text())
    scripts = selected(root)
    need(receipt.get("build_head") == OFFICIAL and
         receipt.get("canonical_build") is True and
         receipt.get("selected_source_count") == len(scripts) == 69,
         "OFFICIAL_RECEIPT_NOT_VALID")
    need(receipt["source_classes"][ROUTE] == "Script" and
         receipt["source_hashes"][ROUTE] == OLD_HOST_SHA, "HOST_SOURCE_CLASS_LOCK")
    need(set(receipt["source_hashes"]) == set(scripts), "ROUTE_SET_MISMATCH")
    for route, (path, _kind) in scripts.items():
        need(sha(path.read_bytes()) == receipt["source_hashes"][route],
             "SOURCE_SHA_DRIFT_" + route)
    original = scripts[ROUTE][0].read_bytes()
    need(sha(original) == OLD_HOST_SHA, "HOST_SHA_DRIFT")
    candidate = transform(original.decode("utf-8")).encode("utf-8")
    need(rollback(candidate.decode(), original.decode()), "ROLLBACK_NOT_EXACT")
    scripts[ROUTE][0].write_bytes(candidate)
    updated = {key: sha(path.read_bytes()) for key, (path, _) in scripts.items()}
    need({key for key in updated if updated[key] != receipt["source_hashes"][key]}
         == {ROUTE}, "NONOVERLAP_SOURCE_BREACH")
    # Crucial: retain canonical input receipt immutable for B source-lock checking.
    # New candidate receipt is a separate file, never impersonates official.
    note = {
        "feature_id": FEATURE, "formal_rc_head": OFFICIAL,
        "official_host_sha256": OLD_HOST_SHA, "new_host_sha256": sha(candidate),
        "changed_selected_routes": [ROUTE], "unchanged_routes": 68,
        "selected_sources": 69, "new_script_count": 0,
        "new_lobby_world_instances": 0,
        "original_ground_and_spawn_created_before_requires": True,
        "original_ground_and_spawn_reused_after_requires": True,
        "game_score_hp_egg_ai_save_authority_changed": False,
        "studio_player_visibility_fix_proven": False,
        "studio": "NOT_TESTED", "android": "NOT_TESTED",
        "owner_accepted": False, "art_gate": "ART_NO_GO",
        "rollback": "restore original Host bytes with old SHA and rerun original project",
    }
    (root / "GQ470_P0_EARLY_LOBBY_CANDIDATE_RECEIPT.json").write_text(
        json.dumps(note, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    return note


def self_test() -> None:
    old = (START + 'local Rules=require(script.Parent:WaitForChild("EGGRUMBLE_CastleMatchRules"))\n'
           + 'local GQ802StageManifest=require(script.Parent:WaitForChild("GQ802_StageManifestPolicy"))\n'
           + OLD_ROOT + 'local joined={}\n'
           + FLOOR_START +
           'lobbyGround.Name="GQ646_LOBBY_SAFE_GROUND"\n'
           + 'lobbyGround.Position=root+Vector3.new(0,-5,21)\n'
           + 'lobbyGround.Parent=folder\n'
           + 'local lobbySpawn=Instance.new("SpawnLocation")\n'
           + 'lobbySpawn.Enabled=true\n'
           + 'lobbySpawn.Position=root+Vector3.new(0,-2,-27)\n'
           + FLOOR_END +
           'local function bindGQ646LobbyCharacter(p) end\n')
    new = transform(old)
    need(rollback(new, old), "SELFTEST_ROLLBACK")
    need("gqEarlySpawn.Position=gqEarlyRoot+Vector3.new(0,-2,-27)" in new,
         "SELFTEST_SPAWN_OFFSET")
    for mutant in (new, old.replace(OLD_ROOT, ""),
                   old.replace("lobbySpawn.Enabled=true", "lobbySpawn.Enabled=false"),
                   old.replace(FLOOR_START, ""),
                   old.replace(FLOOR_END, ""),
                   old.replace('Instance.new("SpawnLocation")', 'Instance.new("Part")')):
        try:
            transform(mutant)
        except ValueError:
            continue
        raise AssertionError("RED_P0_LOBBY_MUTANT_ACCEPTED")
    print("GQ470_P0_EARLY_LOBBY_6_NEGATIVES_PASS")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path)
    ap.add_argument("--head", default=OFFICIAL)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
    else:
        need(args.root is not None, "MISSING_INPUT")
        print("GQ470_P0_EARLY_LOBBY_SELECTED_REAL69_PREP", json.dumps(
            patch(args.root, args.head), ensure_ascii=False))
