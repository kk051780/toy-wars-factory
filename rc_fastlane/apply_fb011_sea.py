#!/usr/bin/env python3
"""FB-011 H1 coastal scenery: source-exact, OFF-safe post-rich66 overlay.

Adds ONE Studio-only Lua Script after official 66 build. The original Game,
H1FunWorld, HUD, Remote, Store, MapBuilder, route geometry and all prior
sources must remain bit-for-bit unchanged. No official RC/main write.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FEATURE = "FB011_H1_SEA_COASTAL_REBUILD_V1"
SRC = ROOT / "features/fb011_sea/H1SeaCoast.server.luau"
DST = "server/H1SeaCoast.server.luau"
PIN = "bb71a18326c9af1463e8ad20d3c2ef4a4f61a346"
BASE_COUNT = 66


def blob(b: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()


def sources(dist: Path) -> dict[str, bytes]:
    root = dist / "src"
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*.luau"))}


def validate_scene(b: bytes) -> None:
    assert blob(b) == PIN, "FB011_AUTHOR_BLOB_DRIFT"
    s = b.decode("utf8")
    for needle in (
        'if not RunService:IsStudio() then return end',
        'arena:WaitForChild("H1_FUN_WORLD", 45)',
        'h1:FindFirstChild("COSMETIC_SEA")',
        'h1:FindFirstChild("SEA_LOW_CAUSEWAY")',
        'math.abs(sea.Position.Z + 30)',
        'math.abs(sea.Position.Z + 49)',
        '"SHALLOW_TURQUOISE_BAY"',
        '"MIDDLE_AZURE_BAY"',
        '"DEEP_SEA_HORIZON"',
        '"SANDY_COAST_"',
        '"BREAKING_SURF_"',
        '"SUN_GLINT_"',
        '"SWELL_RIDGE_"',
        '"OFFSHORE_REEF_"',
        '"OLD_PIER_PLANK_"',
        '"DISTANT_BUOY_"',
        "count <= 142",
        "p.CanCollide = false",
        "p.CanTouch = false",
        "p.CanQuery = false",
        'scenery:SetAttribute("OriginalSeaRoutePreserved"',
        'child.AlwaysOnTop = false',
    ):
        assert needle in s, ("FB011_SCENE_CONTRACT_MISSING", needle)
    for forbidden in (
        'Terrain:FillBlock', 'ClearAllChildren(', 'TakeDamage(',
        'GetDataStore(', 'MarketplaceService', 'OnServerEvent:Connect(',
        'Instance.new("RemoteEvent")', 'FireServer(', 'LoadCharacter(',
        'hum.Health =', 'match.scores[', 'match.hp[',
    ):
        assert forbidden not in s, ("FB011_SECOND_AUTHORITY_FORBIDDEN", forbidden)


def apply(dist: Path, enabled: bool) -> bool:
    if not enabled:
        print("FB011_COAST_SCENE_OFF_FULL_BYTES_UNCHANGED")
        return False
    before = sources(dist)
    assert len(before) == BASE_COUNT, ("FB011_EXPECT_RC66", len(before))
    assert DST not in before
    old_blobs = {p: blob(v) for p, v in sorted(before.items())}
    original_h1 = before.get("server/H1FunWorld.server.luau")
    assert original_h1 is not None and b"COSMETIC_SEA" in original_h1
    assert b"SEA_LOW_CAUSEWAY" in original_h1
    assert before["server/Game.server.luau"].count(b"remote.OnServerEvent:Connect(") == 1
    source_lock_file = dist / "SOURCE_LOCK.json"
    feature_lock_file = dist / "RC_FEATURE_LOCK.json"
    source_lock = json.loads(source_lock_file.read_text(encoding="utf8"))
    feature_lock = json.loads(feature_lock_file.read_text(encoding="utf8"))
    project = json.loads((dist / "default.project.json").read_text(encoding="utf8"))
    assert source_lock["total_scripts"] == BASE_COUNT and source_lock["blobs"] == old_blobs
    assert feature_lock["total_sources"] == BASE_COUNT and feature_lock["source_gitblobs"] == old_blobs
    assert FEATURE not in feature_lock.get("feature_flags", {})
    assert project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"] == "src/server"
    scene = SRC.read_bytes()
    validate_scene(scene)

    next_blobs = dict(old_blobs)
    next_blobs[DST] = PIN
    receipt = {
        "id": FEATURE, "fb_id": "FB-011",
        "input_count": BASE_COUNT, "output_count": BASE_COUNT + 1,
        "original_66_unchanged": True, "existing_h1_scene_unchanged": True,
        "new_script": DST, "new_git_blob": PIN,
        "NoNewGameOrRemoteOrStore": True,
        "preview_only": True, "studio_visual_comparison": "NOT_TESTED",
        "engine_collision_and_visual": "NOT_TESTED",
        "rollback": "omit this adapter or --enabled false (zero bytes touched)",
    }

    # Complete preflight before first write.
    (dist / "src" / DST).write_bytes(scene)
    source_lock["total_scripts"] = BASE_COUNT + 1
    source_lock["blobs"] = next_blobs
    source_lock["rc_fb011_sea_addon"] = receipt
    feature_lock["total_sources"] = BASE_COUNT + 1
    feature_lock["source_gitblobs"] = next_blobs
    feature_lock["feature_flags"][FEATURE] = True
    feature_lock["rc_fb011_sea_addon"] = receipt
    source_lock_file.write_text(json.dumps(source_lock, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    feature_lock_file.write_text(json.dumps(feature_lock, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    after = sources(dist)
    assert len(after) == BASE_COUNT + 1
    assert all(after[p] == v for p, v in before.items()), "FB011_OLD_SOURCE_MUTATED"
    assert blob(after[DST]) == PIN
    print("FB011_H1_COASTAL_REBUILD_PRIVATE67_SOURCE_LOCK_EXACT_PASS")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--enabled", required=True, choices=("true", "false"))
    args = parser.parse_args()
    apply(args.dist, args.enabled == "true")


if __name__ == "__main__":
    main()
