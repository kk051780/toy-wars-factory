#!/usr/bin/env python3
"""Integrate optional real gameplay features into ONE official source-built RC.

This overlays new modules into the already assembled, source-locked author H1
build; it never alters Game, Remote, Store or any original 51 source bytes.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FEATURES = ROOT / "FEATURE_SWITCHES.json"
def gitblob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def sources(root):
    return {p.relative_to(root / "src").as_posix(): p.read_bytes()
            for p in sorted((root / "src").rglob("*.luau"))}

def integrate(profile, dist):
    flags = json.loads(FEATURES.read_text(encoding="utf-8"))
    assert flags["schema"] == "P0D_RC_FEATURE_SWITCHES_V1"
    assert profile in ("rich51", "rich47", "legacy21")
    assert dist.is_dir() and (dist / "default.project.json").is_file()
    before = sources(dist)
    count = {"rich51": 51, "rich47": 47, "legacy21": 21}[profile]
    assert len(before) == count, ("WRONG_PROFILE_BASE_COUNT", len(before), count)
    lock = dist / "SOURCE_LOCK.json"
    if profile == "rich51":
        original_lock = json.loads(lock.read_text(encoding="utf-8"))
        assert original_lock["total_scripts"] == 51
        assert original_lock["blobs"] == {p: gitblob(v) for p, v in sorted(before.items())}
        assert sum(p == "server/Game.server.luau" for p in before) == 1
        assert "server/V4TrainingBridge.server.luau" in before
    if profile != "rich51":
        print("P0D_RC_FEATURES_FALLBACK_PROFILE_UNMODIFIED", profile)
        return 0
    cfg = json.loads((dist / "default.project.json").read_text(encoding="utf-8"))
    starter = cfg["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    assert starter["V4TrialOverlay"]["$path"] == "src/client/V4TrialOverlay.client.luau"
    chosen = flags["features"]["REALM_HUNT_V1"]
    assert chosen["source"] and len(chosen["source"]) == 2
    if not chosen["enabled"]:
        assert "RealmHuntHUD" not in starter
        print("P0D_RC_FEATURE_REALM_HUNT_DISABLED_BASE51_INTACT")
        return 0
    added = []
    for spec in chosen["source"]:
        origin = ROOT.parent / spec["path"]
        data = origin.read_bytes()
        assert gitblob(data) == spec["blob"], ("FEATURE_BLOB_DRIFT", spec["path"])
        dest = dist / "src" / spec["dest"]
        assert not dest.exists(), ("DUPLICATE_FEATURE_PATH", dest)
        txt = data.decode("utf8")
        assert 'if not RunService:IsStudio() then return end' in txt
        for forbidden in ("DataStoreService", "GetDataStore(", "UpdateAsync(",
                          "FireServer(", "OnServerEvent:Connect(", 'Instance.new("RemoteEvent")',
                          "MarketplaceService", "PromptProductPurchase(", "TakeDamage(",
                          "WalkSpeed =", "JumpPower ="):
            assert forbidden not in txt, (forbidden, spec["path"])
        dest.write_bytes(data)
        added.append(spec["dest"])
    assert "RealmHuntHUD" not in starter
    starter["RealmHuntHUD"] = {"$path": "src/client/RealmHuntHUD.client.luau"}
    cfg["name"] = "P0D_CANONICAL_RC_RICH51_REALM_HUNT_V1"
    (dist / "default.project.json").write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    after = sources(dist)
    assert len(after) == 53
    assert all(after[path] == data for path, data in before.items()), "AUTHOR_51_MODIFIED"
    assert sorted(set(after) - set(before)) == sorted(added)
    assert sum(p == "server/Game.server.luau" for p in after) == 1
    assert sum(p.endswith(".server.luau") for p in after) == 4
    assert sum(p.endswith(".client.luau") for p in after) == 9
    # The V4 safety overlay (if enabled) is applied FIRST while the original
    # author 51 source lock is intact. We append our two independent files
    # afterwards, preserving that overlay's 49-script provenance and receipt.
    updated_lock = json.loads(lock.read_text(encoding="utf8"))
    v4_patch = updated_lock.get("rc_overlay")
    assert updated_lock["total_scripts"] == 51
    assert updated_lock["blobs"] == {p: gitblob(v) for p, v in sorted(before.items())}
    updated_lock["total_scripts"] = 53
    updated_lock["blobs"] = {p: gitblob(v) for p, v in sorted(after.items())}
    updated_lock["rc_extra_feature"] = {
        "id": "REALM_HUNT_V1",
        "extra_source_count": 2,
        "original_51_paths_preserved": True,
        "other_v4_overlay_present": bool(v4_patch),
        "no_new_Game_Remote_Store": True,
    }
    lock.write_text(
        json.dumps(updated_lock, ensure_ascii=False, indent=2) + "\n",
        encoding="utf8")
    evidence = {"schema": "P0D_RC_FEATURE_OVERLAY_V1",
        "base_source_count": 51, "original_51_byte_identical": not bool(v4_patch),
        "original_49_byte_identical_when_v4_overlaid": bool(v4_patch),
        "extra": added, "total_sources": 53,
        "feature_flags": {"REALM_HUNT_V1": True},
        "fallback": "disable flag to return to 51",
        "no_new_game_or_store_or_remote": True,
        "roblox_engine_studio": "NOT_TESTED",
        "source_gitblobs": {p: gitblob(v) for p, v in sorted(after.items())}}
    (dist / "RC_FEATURE_LOCK.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print("P0D_RC_REALM_HUNT_OVERLAY_BASE51_EXACT_NEW2_TOTAL53_PASS")
    return len(added)

if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--profile", required=True, choices=["rich51", "rich47", "legacy21"])
    cli.add_argument("--dist", type=Path, required=True)
    args = cli.parse_args()
    integrate(args.profile, args.dist)
