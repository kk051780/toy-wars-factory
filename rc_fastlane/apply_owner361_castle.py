#!/usr/bin/env python3
"""OWNER #361 P0-C private additive castle overlay for exact assembled RC66.

Preserves every byte of original Game, Remote, Store, MapBuilder and all 66 source
files. Adds ONE pure Studio-only world geometry Script on the real RC66 build.
Never writes official RC/main. OFF touches zero bytes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FEATURE = "OWNER361_CASTLE_WORLD_ADDON_V1"
SOURCE = ROOT / "features/owner361_castle/CastleBattlefield.server.luau"
DEST = "server/Owner361CastleBattlefield.server.luau"
PIN = "3599f7a86be2956d2ecf4f14267dfbb73f8f1074"
PREVIOUS = 66


def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def sources(dist: Path) -> dict[str, bytes]:
    root = dist / "src"
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*.luau"))}


def check_authored(data: bytes) -> None:
    assert blob(data) == PIN, "AUTHOR_CASTLE_SCENE_DRIFT"
    txt = data.decode("utf8")
    for marker in (
        'if not RunService:IsStudio() then return end',
        'workspace:WaitForChild("TRAP_RAIDERS_S1", 45)',
        'world:WaitForChild("GrassArena", 10)',
        'world:WaitForChild("RED_CASTLE", 10)',
        'world:WaitForChild("BLUE_CASTLE", 10)',
        'grass.Size = Vector3.new(370, 4, 294)',
        'north.Position = Vector3.new(0, 7, -147)',
        'south.Position = Vector3.new(0, 7, 147)',
        'OWNER361_CASTLE_WORLD_V1',
        'NORTH_WOODLAND_TRAIL', 'SOUTH_WETLAND_TRAIL',
        'NORTH_LOOKOUT_PLATEAU_', 'SOUTH_SHALLOW_WATER_',
        'OPEN_GATE_ARCH', 'GRAND_KEEP', 'GATE_TOWER_',
        'descendant.MaxDistance = 26',
    ):
        assert marker in txt, ("SOURCE_MISSING_MAP_CONTRACT", marker)
    for forbidden in ('DataStoreService', 'MarketplaceService',
                      'Instance.new("RemoteEvent")', 'OnServerEvent:Connect(',
                      'TakeDamage(', 'FireServer(', 'TeleportService'):
        assert forbidden not in txt, ("SECOND_GAME_AUTHORITY_FORBIDDEN", forbidden)


def apply(dist: Path, enabled: bool) -> bool:
    if not enabled:
        print("OWNER361_CASTLE_ADDON_OFF_ALL_BYTES_IDENTICAL_PASS")
        return False
    before = sources(dist)
    assert len(before) == PREVIOUS, ("REQUIRE_RC66", len(before))
    assert DEST not in before, "DUPLICATE_WORLD_ADDON"
    originals = {path: blob(raw) for path, raw in sorted(before.items())}
    source_path = dist / "SOURCE_LOCK.json"
    feature_path = dist / "RC_FEATURE_LOCK.json"
    project_path = dist / "default.project.json"
    source_lock = json.loads(source_path.read_text("utf8"))
    feature_lock = json.loads(feature_path.read_text("utf8"))
    project = json.loads(project_path.read_text("utf8"))
    assert source_lock["total_scripts"] == PREVIOUS and source_lock["blobs"] == originals
    assert feature_lock["total_sources"] == PREVIOUS and feature_lock["source_gitblobs"] == originals
    assert FEATURE not in feature_lock.get("feature_flags", {})
    assert project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"] == "src/server"
    data = SOURCE.read_bytes()
    check_authored(data)
    next_blobs = dict(originals)
    next_blobs[DEST] = PIN
    # All validations completed: only one new source + two lock receipts written.
    (dist / "src" / DEST).write_bytes(data)
    receipt = {
        "id": FEATURE, "private": True, "base_scripts": PREVIOUS,
        "result_scripts": PREVIOUS + 1, "added_source": DEST,
        "added_blob": PIN, "original_66_unchanged": True,
        "single_original_Game_and_Remote": True,
        "mapbuilder_unchanged": True, "real_studio": "NOT_TESTED",
        "human_fun": "NO_GO", "rollback": "omit add-on or --enabled false",
    }
    source_lock["total_scripts"] = PREVIOUS + 1
    source_lock["blobs"] = next_blobs
    source_lock["rc_owner361_castle_addon"] = receipt
    feature_lock["total_sources"] = PREVIOUS + 1
    feature_lock["source_gitblobs"] = next_blobs
    feature_lock["feature_flags"][FEATURE] = True
    feature_lock["rc_owner361_castle_addon"] = receipt
    source_path.write_text(json.dumps(source_lock, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    feature_path.write_text(json.dumps(feature_lock, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    assert all(sources(dist)[path] == raw for path, raw in before.items())
    print("OWNER361_CASTLE_ADDON_PRIVATE67_EXACT_PREVIOUS66_SOURCE_PASS")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--enabled", choices=("true", "false"), required=True)
    args = parser.parse_args()
    apply(args.dist, args.enabled == "true")


if __name__ == "__main__":
    main()
