#!/usr/bin/env python3
"""FB-011 sea visuals: source-locked optional RC66 -> private RC67 assembly.

Append one Studio-only H1 scenic script to the real assembled RC66 Place.
Game, Config, MapBuilder, HUD, Store and all 66 original Luau sources remain
byte-identical. OFF does not read/write the dist. Only #220 can adopt official.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ID = "FB011_H1_COASTAL_SEASCAPE_V1"
SRC_PATH = Path(__file__).resolve().parent / "features/fb011_seascape/H1CoastalSeascape.server.luau"
DEST = "server/FB011_H1CoastalSeascape.server.luau"
SCRIPT_BLOB = "44b39c3d8b0df9290c86a139318ca1bf68356814"

def blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def scripts(dist: Path) -> dict[str, bytes]:
    root = dist / "src"
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*.luau"))}

def apply(dist: Path, enabled: bool) -> bool:
    if not enabled:
        print("FB011_SEASCAPE_OFF_ALL66_BYTE_EXACT_NO_TOUCH")
        return False
    before = scripts(dist)
    assert len(before) == 66, ("REQUIRE_FULL_ASSEMBLED_RC66", len(before))
    assert DEST not in before, "DUPLICATE_SEASCAPE"
    assert all(p in before for p in (
        "server/Game.server.luau", "server/MapBuilder.luau",
        "server/H1FunWorld.server.luau", "client/HUD.client.luau",
        "shared/Config.luau"
    )), "MISSING_REAL_H1_SEA_OR_GAME"
    # Validate that full RC66 SourceLock / feature lock agrees exactly.
    lp, fp = dist / "SOURCE_LOCK.json", dist / "RC_FEATURE_LOCK.json"
    lock = json.loads(lp.read_text(encoding="utf8"))
    features = json.loads(fp.read_text(encoding="utf8"))
    pins = {p: blob(b) for p, b in sorted(before.items())}
    assert lock["total_scripts"] == 66 and lock["blobs"] == pins, "S1_SOURCE_LOCK_DRIFT"
    assert features["total_sources"] == 66 and features["source_gitblobs"] == pins, "S1_FEATURE_LOCK_DRIFT"
    assert ID not in features["feature_flags"], "ALREADY_ADOPTED"
    project = json.loads((dist / "default.project.json").read_text("utf8"))
    assert project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"] == "src/server", "MISMATCHED_SERVER_MOUNT"

    source = SRC_PATH.read_bytes()
    assert blob(source) == SCRIPT_BLOB, "AUTHORED_SCENE_CHANGED_WITHOUT_PIN"
    text = source.decode("utf8")
    for required in ("COSMETIC_SEA", "Enum.Material.Water", "terra:FillBlock(",
                     "OCEAN_SHOAL_SURFACE", "FORESHORE_SAND_", "OUTER_COAST_SAND_",
                     "SURF_BREAK_", "SEA_BOARDWALK_DECK_", "REEF_ROCK_",
                     "FISHING_BOAT_HULL_", "FB011_SEA_GEOMETRY_DRIFT_FAIL_CLOSED",
                     "if not RunService:IsStudio() then return end"):
        assert required in text, ("NOT_REAL_SEA_ART", required)
    for forbidden in ("RemoteEvent", "OnServerEvent:Connect(", "DataStoreService",
                      "UpdateAsync(", "TakeDamage(", "PromptProductPurchase("):
        assert forbidden not in text, ("SECOND_GAME_OR_REWARD_AUTHORITY", forbidden)
    after = {**before, DEST: source}
    pins_after = {p: blob(b) for p, b in sorted(after.items())}
    assert len(after) == 67
    assert all(after[p] == raw for p, raw in before.items())
    lock["total_scripts"] = 67
    lock["blobs"] = pins_after
    lock["fb011_seascape_private"] = {
        "feedback_id": "FB-011",
        "source_id": ID,
        "source_blob": SCRIPT_BLOB,
        "script_added": DEST,
        "other_existing_sources_identical": 66,
        "other_world_upgrades_not_merged": True,
        "studio": "NOT_TESTED",
        "human_visual_acceptance": "FUN_NO_GO",
        "rollback": "omit optional seascape build step; restores original exact RC66"
    }
    features["total_sources"] = 67
    features["source_gitblobs"] = pins_after
    features["feature_flags"][ID] = True
    # No disk writes until all pins and expected source-contract values validate.
    path = dist / "src" / DEST
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(source)
    lp.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    fp.write_text(json.dumps(features, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    assert scripts(dist) == after
    print("FB011_SEASCAPE_REAL_3D_WATER_66_TO_67_SOURCE_LOCK_PASS")
    return True

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dist", required=True, type=Path)
    p.add_argument("--enabled", required=True, choices=("true", "false"))
    args = p.parse_args()
    apply(args.dist, args.enabled == "true")
