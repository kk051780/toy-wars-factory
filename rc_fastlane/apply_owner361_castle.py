#!/usr/bin/env python3
"""OWNER #361 P0-C: reversible, exact-source 3D castle/route map overlay.

A PREP only. No official RC write; no Game/Remote/Store or objective coordinate
changes. Requires the real official-rich66 assembled map and matching locks.
Studio collision/FUN validation is still required before B acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FEATURE = "OWNER361_CASTLE_ROUTES_V2"
MAP = "server/MapBuilder.luau"
OLD_BLOB = "d2127b8c20c8abd880a21f84aeeb706feeb14ce8"
NEW_BLOB = "f8a81c2ccd7014da3918d9e9a75765f90feaa6f6"
AUTHOR = ROOT / "features/owner361_castle/MapBuilderCastleV2.luau"
COUNT = 66


def gitblob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def sources(dist: Path) -> dict[str, bytes]:
    source = dist / "src"
    return {
        path.relative_to(source).as_posix(): path.read_bytes()
        for path in sorted(source.rglob("*.luau"))
    }


def check_authored_map(data: bytes) -> None:
    assert gitblob(data) == NEW_BLOB, "AUTHOR_CASTLE_MAP_DRIFT"
    txt = data.decode("utf8")
    for marker in (
        "GrassArena", "Vector3.new(370, 4, 294)",
        "FRONT_CURTAIN_WALL_", "FRONT_TOWER_", "GREAT_KEEP",
        "GATE_ARCH", "NORTH_WOODLAND_TRAIL", "SOUTH_WETLAND_TRAIL",
        "NORTH_LOOKOUT_PLATEAU_", "SOUTH_SHALLOW_WATER_",
        "CENTER_STREAM", "b.MaxDistance = 26",
        'eggPrompt = prompt(egg, "Steal egg", name .. " treasure")',
        'scorePrompt = prompt(pad, "Deliver egg", name .. " scoring pad")',
        'spawn = CFrame.new(sign * 68, 5, 0)',
        'name .. "_CASTLE_CORE", Vector3.new(10, 13, 10)',
        'name .. "_EGG", Vector3.new(4, 5, 4)',
        'name .. "_SCORE_PAD", Vector3.new(12, .5, 12)',
    ):
        assert marker in txt, ("MISSING_MAP_CONTRACT", marker)
    assert txt.count("function MapBuilder.build(config)") == 1
    assert txt.count("return MapBuilder") == 1
    assert txt.count('Instance.new("RemoteEvent")') == 0
    assert "DataStoreService" not in txt and "MarketplaceService" not in txt


def apply(dist: Path, enabled: bool) -> bool:
    if not enabled:
        print("OWNER361_CASTLE_MAP_OFF_BYTE_IDENTICAL_PASS")
        return False
    before = sources(dist)
    assert len(before) == COUNT, ("EXPECTED_RICH66", len(before))
    assert MAP in before and gitblob(before[MAP]) == OLD_BLOB, "MAP_ORIGINAL_BLOB_DRIFT"
    authored = AUTHOR.read_bytes()
    check_authored_map(authored)
    original = {p: gitblob(data) for p, data in sorted(before.items())}
    source_path = dist / "SOURCE_LOCK.json"
    feature_path = dist / "RC_FEATURE_LOCK.json"
    source_lock = json.loads(source_path.read_text(encoding="utf8"))
    feature_lock = json.loads(feature_path.read_text(encoding="utf8"))
    assert source_lock["total_scripts"] == COUNT
    assert source_lock["blobs"] == original, "SOURCE_LOCK_BASE_MISMATCH"
    assert feature_lock["total_sources"] == COUNT
    assert feature_lock["source_gitblobs"] == original, "FEATURE_LOCK_BASE_MISMATCH"
    assert FEATURE not in feature_lock.get("feature_flags", {}), "DUPLICATE_MAP_PATCH"
    # Source-diff contract: MapBuilder only, Game/HP/egg/Remote/Store unchanged.
    next_blobs = dict(original)
    next_blobs[MAP] = NEW_BLOB
    (dist / "src" / MAP).write_bytes(authored)
    receipt = {
        "id": FEATURE,
        "base_source_count": COUNT,
        "source_count": COUNT,
        "only_changed_source": MAP,
        "old_map_gitblob": OLD_BLOB,
        "new_map_gitblob": NEW_BLOB,
        "original_game_and_objectives_untouched": True,
        "castle_count": 2,
        "routes": ["CENTER_ROAD", "NORTH_WOODLAND", "SOUTH_WETLAND"],
        "arena_dimensions_studs": [370, 294],
        "existing_dojo_move": "NOT_INCLUDED",
        "studio_visual_collision_fun": "NOT_TESTED",
    }
    source_lock["blobs"] = next_blobs
    source_lock["rc_owner361_castle"] = receipt
    feature_lock["source_gitblobs"] = next_blobs
    feature_lock["feature_flags"][FEATURE] = True
    feature_lock["rc_owner361_castle"] = receipt
    source_path.write_text(json.dumps(source_lock, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    feature_path.write_text(json.dumps(feature_lock, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    print("OWNER361_CASTLE_ROUTES_RICH66_SOURCE_LOCK_UPDATED_PASS")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--enabled", choices=("true", "false"), required=True)
    args = parser.parse_args()
    apply(args.dist, args.enabled == "true")


if __name__ == "__main__":
    main()
