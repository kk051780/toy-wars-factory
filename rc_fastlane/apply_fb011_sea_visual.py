#!/usr/bin/env python3
"""FB-011 aesthetic-only Studio sea PREP: add one isolated server visual script.

No authoritative Game, egg, Remote, Store, MapBuilder or prior H1 code changes.
Only sole #220 authenticated B may integrate into official RC after same-HEAD
Luau/Rojo/Studio QA. OFF is a zero-write exact rollback before build.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "features/owner364_sea/FB011SeaVisual.server.luau"
FEATURE = "OWNER_FB011_SEA_VISUAL_V1"
SOURCE_BLOB = "1bf6ebd0789492fb128e97a8cee33b7445aed465"
H1_PATH = "server/H1FunWorld.server.luau"
H1_BLOB = "7a90affd4eb7eebcdfba39d833a2875ff665d5cf"
DEST = "server/FB011SeaVisual.server.luau"


def gitblob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def sources(dist: Path) -> dict[str, bytes]:
    root = dist / "src"
    assert root.is_dir(), "SOURCE_ROOT_MISSING"
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*.luau"))}


def verify_source() -> bytes:
    data = SOURCE.read_bytes()
    assert gitblob(data) == SOURCE_BLOB, "FB011_AUTHORED_BLOB_DRIFT"
    body = data.decode("utf8")
    for marker in (
        'if not RunService:IsStudio() then return end',
        '"TRAP_RAIDERS_S1"',
        '"H1_FUN_WORLD"',
        '"COSMETIC_SEA"',
        '"SEA_LOW_CAUSEWAY"',
        '"P0D_FB011_SEA_ART_V1"',
        'Workspace.Terrain:FillBlock(',
        'Enum.Material.Water',
        'original.Transparency = 1',
        'CanCollide = false',
        'CanTouch = false',
        'CanQuery = false',
        'OwnerFeedbackID", "FB-011"',
        'StudioVisualQA", "NOT_TESTED"',
    ):
        assert marker in body, ("MISSING_FB011_SEA_CONTRACT", marker)
    for forbidden in (
        "RemoteEvent", "FireServer(", "OnServerEvent:Connect(",
        "TakeDamage(", "DataStoreService", "UpdateAsync(",
        "MarketplaceService", "PromptProductPurchase(",
        "TeleportService", "LoadCharacter(",
    ):
        assert forbidden not in body, ("FORBIDDEN_SEA_VISUAL_AUTHORITY", forbidden)
    return data


def apply(dist: Path, enabled: bool) -> bool:
    if not enabled:
        print("FB011_SEA_ART_OFF_EXACT_NO_WRITE")
        return False
    addon = verify_source()
    before = sources(dist)
    assert len(before) == 66, ("FB011_EXPECTS_CANONICAL66", len(before))
    assert H1_PATH in before and gitblob(before[H1_PATH]) == H1_BLOB, "ORIGINAL_H1_DRIFT"
    assert DEST not in before, "FB011_DUPLICATE_SCENE"
    assert "server/Game.server.luau" in before
    assert "server/MapBuilder.luau" in before
    lp = dist / "SOURCE_LOCK.json"
    fp = dist / "RC_FEATURE_LOCK.json"
    proj = dist / "default.project.json"
    locks = json.loads(lp.read_text("utf8"))
    features = json.loads(fp.read_text("utf8"))
    config = json.loads(proj.read_text("utf8"))
    server = config["tree"]["ServerScriptService"]["TrapRaidersS1"]
    assert server["$path"] == "src/server", "SCRIPT_LOAD_TREE_DRIFT"
    pins = {p: gitblob(b) for p, b in sorted(before.items())}
    assert locks["total_scripts"] == 66 and locks["blobs"] == pins
    assert features["total_sources"] == 66 and features["source_gitblobs"] == pins
    assert FEATURE not in features.get("feature_flags", {}), "DUPLICATE_FB011"

    after = {**before, DEST: addon}
    assert len(after) == 67
    assert all(after[p] == b for p, b in before.items())
    pinned = {p: gitblob(b) for p, b in sorted(after.items())}
    receipt = {
        "feature": FEATURE, "feedback_id": "FB-011",
        "only_added_source": DEST, "source_count": 67,
        "base_h1_gitblob": H1_BLOB, "new_source_gitblob": SOURCE_BLOB,
        "unchanged_original66": True, "game_remote_store_unchanged": True,
        "terrain_water_studio_only": True,
        "terrain_water_engine_physics": "NOT_TESTED",
        "visual_user_acceptance": "NOT_TESTED",
        "two_client_and_mobile": "NOT_TESTED",
        "rollback": "omit adapter; fresh Studio Play resets runtime Terrain",
    }
    locks["total_scripts"] = 67
    locks["blobs"] = pinned
    locks["rc_owner_fb011_sea_visual"] = receipt
    features["total_sources"] = 67
    features["source_gitblobs"] = pinned
    features["feature_flags"][FEATURE] = True
    features["rc_owner_fb011_sea_visual"] = receipt
    dest = dist / "src" / DEST
    dest.write_bytes(addon)
    lp.write_text(json.dumps(locks, ensure_ascii=False, indent=2) + "\n", "utf8")
    fp.write_text(json.dumps(features, ensure_ascii=False, indent=2) + "\n", "utf8")
    assert sources(dist) == after
    print("FB011_SEA_ART_SOURCE67_ONLY_ADD_ORIGINAL66_IDENTICAL")
    return True


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--dist", required=True, type=Path)
    cli.add_argument("--enabled", choices=("true", "false"), required=True)
    args = cli.parse_args()
    apply(args.dist, args.enabled == "true")
