#!/usr/bin/env python3
"""Compose original PR311 meteor into already assembled private60 without rewriting Game.
Only this isolated PR branch; not an authorized canonical #220 writer.
"""
import argparse
import hashlib
import json
from pathlib import Path

SOURCE_BLOB = "9ef84d97a2a629581b3bfa214ac1ed3aefe3db55"
SOURCE_PATH = Path("_p0d_meteor_author/handoffs/P0D-WEATHER-METEOR-SHORTCUT-V1-20261114-01/MeteorShortcut.server.luau")
DEST = "server/MeteorShortcut.server.luau"
FLAG_NAME = "P0D_ENABLE_METEOR_SHORTCUT_V1"
FEATURE = "METEOR_SHORTCUT_V1"

def gitblob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def source_map(dist):
    root = dist / "src"
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*.luau"))}

def apply(dist, enabled=True):
    dist = Path(dist)
    scripts = source_map(dist)
    assert len(scripts) == 60, ("REQUIRES_PRIVATE60", len(scripts))
    assert DEST not in scripts, "METEOR_ALREADY_ADDED"
    assert len([p for p in scripts if p == "server/Game.server.luau"]) == 1
    assert "server/WCS_CrystalCanyon.server.luau" in scripts
    assert "server/SevenJobsRules.luau" in scripts
    assert "server/EggRelayPolicy.luau" in scripts
    original_game = scripts["server/Game.server.luau"]
    assert original_game.count(b'remote.OnServerEvent:Connect(') == 1, "MULTIPLE_REMOTE_HANDLERS"

    lockfile = dist / "SOURCE_LOCK.json"
    lock = json.loads(lockfile.read_text("utf8"))
    assert lock["total_scripts"] == 60
    assert lock["blobs"] == {p: gitblob(raw) for p, raw in sorted(scripts.items())}, "PREVIOUS_LOCK_DRIFT"
    assert lock["rc_wcs_f01_c01_overlay"]["id"] == "WCS_F01_C01"
    assert lock["rc_seven_jobs_pve_overlay"]["id"] == "SEVEN_JOBS_PVE_V1"

    cfgpath = dist / "default.project.json"
    cfg = json.loads(cfgpath.read_text("utf8"))
    tree = cfg["tree"]
    assert tree["ServerScriptService"]["TrapRaidersS1"]["$path"] == "src/server"
    store = tree["ServerStorage"]
    assert store["$attributes"]["P0D_RC_ENABLE_WCS_F01_C01"] is True
    egg = store["P0D_RC_ENABLE_EGG_RELAY_CLASSIC"]
    assert egg["$className"] == "BoolValue"
    assert egg["$properties"]["Value"] is True
    assert FLAG_NAME not in store, "METEOR_BOOT_VALUE_EXISTS"

    feature_file = dist / "RC_FEATURE_LOCK.json"
    feature = None
    if feature_file.exists():
        feature = json.loads(feature_file.read_text("utf8"))
        assert feature["total_sources"] == 60, "STALE_RC_FEATURE_TOTAL"
        assert feature["source_gitblobs"] == {p: gitblob(raw) for p, raw in sorted(scripts.items())}
        assert FEATURE not in feature["feature_flags"]

    if not enabled:
        print("P0D_METEOR_OFF_RETURNS_PRIVATE60_BYTE_EXACT_PASS")
        return False

    raw = SOURCE_PATH.read_bytes()
    assert gitblob(raw) == SOURCE_BLOB, "METEOR_AUTHOR_SOURCE_CHANGED"
    text = raw.decode("utf8")
    for proof in (
        "if not RunService:IsStudio() then",
        'flag ~= nil and flag:IsA("BoolValue") and flag.Value == true',
        'GetAttribute("P0D_RC_ENABLE_WCS_F01_C01") ~= true',
        'Workspace:WaitForChild("P0D_WCS_CrystalCanyon", 12)',
        'local function isBridgeOccupied(',
        'runtime:Destroy()',
    ):
        assert proof in text, ("METEOR_SAFETY_CONTRACT_DRIFT", proof)
    for forbidden in (
        "DataStoreService", "UpdateAsync(", "MarketplaceService",
        "Instance.new(\"RemoteEvent\")", "FireServer(", "OnServerEvent:Connect(",
        "TakeDamage(", "PromptProductPurchase(",
    ):
        assert forbidden not in text, ("METEOR_FORBIDDEN_AUTHORITY", forbidden)
    assert text.count("local function getAnchors()") == 1
    assert text.count("setRoute(segments, false)") == 2

    after = dict(scripts)
    after[DEST] = raw
    assert len(after) == 61
    assert all(after[p] == scripts[p] for p in scripts), "ORIGINAL60_CHANGED"
    assert after["server/Game.server.luau"] == original_game
    after_blobs = {p: gitblob(raw) for p, raw in sorted(after.items())}
    lock["total_scripts"] = 61
    lock["blobs"] = after_blobs
    lock["private_meteor_overlay"] = {
        "id": FEATURE, "author_blob": SOURCE_BLOB,
        "source_preserved": 60,
        "one_game_remote_store": True,
        "studio_only": True,
        "boot_missing_false_off": True,
        "physical_studio_2client": "NOT_TESTED",
        "official_rc_adopted": False,
        "rollback": "rebuild PRIVATE60 with METEOR_ENABLED=false",
    }
    store[FLAG_NAME] = {"$className": "BoolValue", "$properties": {"Value": True}}
    if feature is not None:
        feature["total_sources"] = 61
        feature["source_gitblobs"] = after_blobs
        feature["feature_flags"][FEATURE] = True

    # Only perform side effects after validating the original full source and flags.
    (dist / "src" / DEST).write_bytes(raw)
    cfgpath.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", "utf8")
    lockfile.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", "utf8")
    if feature is not None:
        feature_file.write_text(json.dumps(feature, ensure_ascii=False, indent=2) + "\n", "utf8")
    assert source_map(dist) == after, "AFTER_SOURCE_CHANGED"
    print("P0D_PRIVATE61_WCS_JOBS_RELAY_METEOR_EXACT_SOURCE_PASS 61")
    return True

if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--dist", type=Path, required=True)
    cli.add_argument("--enabled", choices=("true","false"), default="true")
    args = cli.parse_args()
    apply(args.dist, args.enabled == "true")
