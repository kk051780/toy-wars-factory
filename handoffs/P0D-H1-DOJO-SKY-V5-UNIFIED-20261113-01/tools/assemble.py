#!/usr/bin/env python3
"""Isolated 45-script playable H1 candidate: original 45 dojo + exact V5 ground docks.

Rebuild original 45 from pinned source, then replace ONLY H1FunWorld.
NO official #220 RC/source lock, main, Roblox publish, purchases, or PC operations.
"""
from __future__ import annotations
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO = HERE.parents[3]
BASE = REPO / "handoffs/P0D-RC-B42V7-SKY-SOLO-DOJO-H1-20261113-01"
BASE_DIST = BASE / "dist/P0D_B42_V7_SKYCASTLE_LATCH_AUDIT_DOJO_H1_PRIVATE"
DEST = ROOT / "dist/P0D_B42_V7_SOLO_AUDIT_DOJO_SKY_GROUNDDOCK_V5_PRIVATE"
NEW_WORLD = ROOT / "src/H1FunWorld_V5.server.luau"
OLD_WORLD_BLOB = "0a6360392f4384dc2f0ab1e9afc1d840d66a22b8"
NEW_WORLD_BLOB = "7a90affd4eb7eebcdfba39d833a2875ff665d5cf"
BASE_45_SHA = "79804116b0a144a33c6466340cfb476eefa3ca4d"
V5_SHA = "f607cf4de4ac50e1e886adbd5b9f6070fe5c0450"

def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def scripts(root: Path):
    return {p.relative_to(root / "src").as_posix(): p.read_bytes()
            for p in sorted((root / "src").rglob("*.luau"))}

def assemble():
    if DEST.exists() or BASE_DIST.exists():
        raise RuntimeError("FAIL_CLOSED_EXISTING_BUILD_DIRECTORY")
    if blob(NEW_WORLD.read_bytes()) != NEW_WORLD_BLOB:
        raise RuntimeError("FAIL_CLOSED_WORLD_AUTHOR_SOURCE_DRIFT")
    subprocess.run([sys.executable, "-B", str(BASE / "tools/assemble.py"), "--assemble"],
                   cwd=REPO, check=True)
    old = scripts(BASE_DIST)
    old_lock = json.loads((BASE_DIST / "SOURCE_LOCK.json").read_text("utf8"))
    if len(old) != 45 or old_lock["all_scripts"] != 45 or old_lock["official_rc_adopted"] is not False:
        raise RuntimeError("FAIL_CLOSED_BASE_45_AUTHORITY")
    world_key = "server/H1FunWorld.server.luau"
    if blob(old[world_key]) != OLD_WORLD_BLOB:
        raise RuntimeError("FAIL_CLOSED_BASE_WORLD_DRIFT")
    shutil.copytree(BASE_DIST, DEST)
    (DEST / "src" / world_key).write_bytes(NEW_WORLD.read_bytes())
    cfg_path = DEST / "default.project.json"
    cfg = json.loads(cfg_path.read_text("utf8"))
    if cfg["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"] != "src/server":
        raise RuntimeError("FAIL_CLOSED_GAME_MAPPING_DRIFT")
    if cfg["tree"]["StarterPlayer"]["StarterPlayerScripts"]["P0DStudioTrialAudit"]["$path"] != "src/client/P0DStudioTrialAudit.client.luau":
        raise RuntimeError("FAIL_CLOSED_DIAGNOSTIC_MAPPING")
    cfg["name"] = "P0D_H1_B42_V7_SKY_GROUNDDOCK_V5_DOJO_PRIVATE"
    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", "utf8")
    new = scripts(DEST)
    changed = sorted(k for k in old if old[k] != new.get(k))
    if len(new) != 45 or set(old) != set(new) or changed != [world_key]:
        raise RuntimeError("FAIL_CLOSED_UNEXPECTED_GAMEPLAY_DIFF: " + repr(changed))
    if blob(new[world_key]) != NEW_WORLD_BLOB:
        raise RuntimeError("FAIL_CLOSED_NEW_WORLD_DRIFT")
    game = new["server/Game.server.luau"].decode("utf8")
    world = new[world_key].decode("utf8")
    if any(game.count(anchor) != 1 for anchor in (
        "remote.OnServerEvent:Connect(", 'remote.Name = "TrapRaidersS1Remote"',
        "local function tickRound()", "local function resetRound()",
        "studioSoloRoundStarted = StudioSolo.isSoloRound(", "Dojo.tick(")):
        raise RuntimeError("FAIL_CLOSED_DUPLICATE_GAME_AUTHORITY")
    if any(marker not in world for marker in (
        'path("SKY_GROUND_BOOT_RED"', 'path("SKY_GROUND_BOOT_BLUE"',
        'path("SKY_SCORE_DOCK_RED"', 'path("SKY_SCORE_DOCK_BLUE"',
        'box("FLOATING_SKY_ISLAND"', 'world.Name="H1_FUN_WORLD"',
        'if not RunService:IsStudio() then', 'world:SetAttribute("GroundDocksPhysical",4)')):
        raise RuntimeError("FAIL_CLOSED_MISSING_V5_PHYSICAL_ROUTE")
    if "RemoteEvent" in world or "DataStoreService" in world or "MarketplaceService" in world:
        raise RuntimeError("FAIL_CLOSED_UNEXPECTED_WORLD_AUTHORITY")
    kinds = Counter("server" if name.startswith("server/") else "client" for name in new)
    if sum(k.endswith(".server.luau") for k in new) != 2 or sum(k.endswith(".client.luau") for k in new) != 6:
        raise RuntimeError("FAIL_CLOSED_SCRIPT_LAYOUT")
    receipt = {
        "schema": "P0D_H1_RICH_DOJO_SKY_V5_ISOLATED_45",
        "game_id": "TRAP_RAIDERS", "work_id": "p0d-siege-v19",
        "base_45_author_sha": BASE_45_SHA, "v5_scene_author_sha": V5_SHA,
        "original_base_45_scripts": 45, "scripts_unchanged": 44,
        "only_changed_script": world_key, "v5_scene_author_blob": NEW_WORLD_BLOB,
        "all_scripts": 45, "server_game_count": 1, "remote_authority_count": 1,
        "sky_world_count": 1, "source_qa": "ASSEMBLED_SOURCE_CHECKS_ONLY",
        "native_luau": "NOT_TESTED_UNTIL_CI", "rojo_private_place": "NOT_BUILT_UNTIL_CI",
        "roblox_studio_one_client": "NOT_TESTED",
        "roblox_studio_two_client": "NOT_TESTED",
        "android": "NOT_TESTED", "owner_fun": "NOT_TESTED",
        "official_rc_adopted": False, "product_official_rc_selected": False,
        "published": False, "paid": False, "dojo_full_six_skill_v4": False,
        "dojo_session_only_beast_weapon": True,
        "source_blobs": {k: blob(v) for k, v in sorted(new.items())},
    }
    (DEST / "SOURCE_LOCK.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", "utf8")
    print("P0D_H1_DOJO_SKY_V5_45_SOURCE_DIFF_ONE_WORLD_PASS")
    return receipt

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--assemble", action="store_true", required=True)
    parser.parse_args()
    assemble()
