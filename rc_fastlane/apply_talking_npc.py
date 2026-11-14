#!/usr/bin/env python3
"""PREP-only talking NPC overlay: exact source-lock + reversible latest RC -> preview (+3).

This does not alter canonical RC. The caller must use a COPY of the verified
official RC distribution. It never modifies existing Game, Store, Remote, HUD
or any previously source-locked Luau, and never adds game/score ownership.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FEATURE_ROOT = ROOT / "features" / "talking_npc"
FEATURE_ID = "P0D-TALKING-NPC-V1"
FLAG = "P0D_RC_ENABLE_TALKING_NPC_V1"
SCRIPTS = {
    "TalkingNPCDirector.luau": "server/TalkingNPCDirector.luau",
    "TalkingNPCRuntime.server.luau": "server/TalkingNPCRuntime.server.luau",
    "TalkingNPCClient.client.luau": "client/TalkingNPCClient.client.luau",
}

def git_blob(b: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()

def source_bytes(dist: Path) -> dict[str, bytes]:
    src = dist / "src"
    return {p.relative_to(src).as_posix(): p.read_bytes()
            for p in sorted(src.rglob("*.luau"))}

def _apply_inplace(dist: Path, enabled: bool = True) -> bool:
    """Internal only. Mutates a private temporary candidate, never caller dist."""
    if not enabled:
        print("P0D_TALKING_NPC_OFF_PREVIOUS_RC_BYTES_UNCHANGED")
        return False
    if not dist.is_dir():
        raise ValueError("PREVIEW_DISTRIBUTION_MISSING")
    locked = json.loads((FEATURE_ROOT / "PREP_SOURCE_LOCK.json").read_text("utf8"))
    assert locked["schema"] == "P0D_TALKING_NPC_PREP_SOURCE_LOCK_V1"
    assert locked["feature_id"] == FEATURE_ID
    assert locked["canonical_rc_unmodified"] and not locked["runtime_enabled_in_rc"]
    assert set(locked["files"]) == set(SCRIPTS), "TALKING_NPC_LOCK_FILES_DRIFT"
    data = {}
    for origin, dest in SCRIPTS.items():
        raw = (FEATURE_ROOT / origin).read_bytes()
        assert git_blob(raw) == locked["files"][origin], ("SOURCE_BLOB_DRIFT", origin)
        data[dest] = raw

    server = data["server/TalkingNPCRuntime.server.luau"].decode("utf8")
    client = data["client/TalkingNPCClient.client.luau"].decode("utf8")
    dialogue = data["server/TalkingNPCDirector.luau"].decode("utf8")
    for needle in ('RunService:IsStudio()', 'ServerStorage:GetAttribute(FLAG) ~= true',
                   'remote:FireClient(player,', 'Workspace:Raycast(', 'Director.Compose',
                   'speaker == "NAVI"', 'speaker == "ORACLE"'):
        assert needle in server, ("PREP_SERVER_CONTRACT_DRIFT", needle)
    for needle in ('AudioTextToSpeech', 'AudioDeviceOutput', 'Wire',
                   'packet.kind ~= "P0D_NPC_TALK_V1"', 'message.Text = packet.text',
                   'VoiceToggle'):
        assert needle in client, ("PREP_CLIENT_CONTRACT_DRIFT", needle)
    for needle in ('observedByTeam == true', 'itemKnownByTeam == true',
                   'hintUnlocked == true', 'isGeneratedAI = false'):
        assert needle in dialogue, ("PREP_DIALOGUE_CONTRACT_DRIFT", needle)

    for origin, raw in data.items():
        s = raw.decode("utf8")
        for bad in ('Instance.new("RemoteEvent")', 'DataStoreService',
                    'UpdateAsync(', 'SetAsync(', 'GetDataStore(', 'OnServerEvent:Connect(',
                    'TakeDamage(', 'MarketplaceService', 'PromptProductPurchase(',
                    'FireServer(', 'TeleportService', 'HttpService'):
            assert bad not in s, ("ILLEGAL_SECOND_AUTHORITY_OR_SPENDING", origin, bad)

    existing = source_bytes(dist)
    assert 64 <= len(existing) <= 90, ("REQUIRE_CURRENT_RC_FEATURES", len(existing))
    base_count = len(existing)
    assert all(path not in existing for path in data), "TALKING_NPC_DUPLICATE_SCRIPT"
    assert sum(path == "server/Game.server.luau" for path in existing) == 1
    assert "server/TwinBiomes.server.luau" in existing, "REQUIRE_CURRENT_PRIVATE64"
    assert "server/RealmHunt.server.luau" in existing, "REQUIRE_REALM_HUNT_DIALOGUE"
    lock_path = dist / "SOURCE_LOCK.json"
    source_lock = json.loads(lock_path.read_text("utf8"))
    old_pins = {path: git_blob(raw) for path, raw in sorted(existing.items())}
    assert source_lock["total_scripts"] == base_count, "PREVIOUS_SOURCE_COUNT_DRIFT"
    assert source_lock["blobs"] == old_pins, "PREVIOUS_RC_SOURCE_LOCK_DRIFT"
    feature_lock_path = dist / "RC_FEATURE_LOCK.json"
    feature_lock = json.loads(feature_lock_path.read_text("utf8"))
    assert feature_lock["total_sources"] == base_count
    assert feature_lock["source_gitblobs"] == old_pins
    assert FEATURE_ID not in feature_lock["feature_flags"]
    assert feature_lock["feature_flags"].get("REALM_HUNT_V1") is True, "REALM_HUNT_NOT_ENABLED"

    project_path = dist / "default.project.json"
    project = json.loads(project_path.read_text("utf8"))
    tree = project["tree"]
    assert tree["ServerScriptService"]["TrapRaidersS1"]["$path"] == "src/server"
    starter = tree["StarterPlayer"]["StarterPlayerScripts"]
    assert "P0DTalkingNPCClient" not in starter
    storage = tree["ServerStorage"]
    flags = storage["$attributes"]
    assert FLAG not in flags, "ALREADY_TALKING_NPC_ENABLED"
    assert flags["P0D_RC_ENABLE_STAR_SHARDS_V1"] is True
    assert "TrapRaidersS1Remote" not in tree.get("ReplicatedStorage", {}), "REMOTE_MISCONFIGURED"

    # All prior guards passed: only now mutate the staging COPY, not official RC.
    for dest, raw in data.items():
        target = dist / "src" / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        assert not target.exists()
        target.write_bytes(raw)
    flags[FLAG] = True # local/private preview only; runtime STILL Studio guarded.
    starter["P0DTalkingNPCClient"] = {
        "$path": "src/client/TalkingNPCClient.client.luau"
    }
    project["name"] = "P0D_PREP_TALKING_NPC_LATEST_PLUS3_NOT_CANONICAL"
    project_path.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", "utf8")
    current = source_bytes(dist)
    assert len(current) == base_count + 3
    assert all(current[path] == raw for path, raw in existing.items()), "PREVIOUS64_BODY_DRIFT"
    assert set(current) - set(existing) == set(data), "ADDED_FILES_DRIFT"
    new_pins = {path: git_blob(raw) for path, raw in sorted(current.items())}
    source_lock["total_scripts"] = base_count + 3
    source_lock["blobs"] = new_pins
    source_lock["rc_talking_npc_PREP_overlay"] = {
        "feature_id": FEATURE_ID,
        "predecessor_script_count": base_count,
        "new_source_files": list(SCRIPTS.values()),
        "previous_sources_byte_identical": True,
        "match_round_egg_store_remote_unchanged": True,
        "private_studio_opt_in": True,
        "rollback": "Set preview flag false / omit 3 scripts to recover exact predecessor",
        "engine_studio": "NOT_TESTED",
        "mobile_tts": "NOT_TESTED",
        "official_rc_adopted": False,
    }
    lock_path.write_text(json.dumps(source_lock, ensure_ascii=False, indent=2) + "\n", "utf8")
    feature_lock["total_sources"] = base_count + 3
    feature_lock["source_gitblobs"] = new_pins
    feature_lock["feature_flags"][FEATURE_ID] = True
    feature_lock_path.write_text(json.dumps(feature_lock, ensure_ascii=False, indent=2) + "\n", "utf8")
    print("P0D_TALKING_NPC_PREP_LATEST_PLUS3_EXACT_SOURCES_PASS", base_count, len(current))
    return True

def apply(dist: Path, enabled: bool = True, output_dist: Path | None = None) -> bool:
    """Transactional overlay: read-only predecessor, atomically publish new dir."""
    dist = dist.resolve()
    if not enabled:
        print("P0D_TALKING_NPC_OFF_PREVIOUS_RC_BYTES_UNCHANGED")
        return False
    if not dist.is_dir():
        raise ValueError("PREVIEW_DISTRIBUTION_MISSING")
    if output_dist is None:
        raise ValueError("OUTPUT_DIST_REQUIRED_FOR_IMMUTABLE_PREVIEW")
    output_dist = output_dist.resolve()
    if output_dist.exists() or output_dist == dist or output_dist in dist.parents:
        raise ValueError("OUTPUT_DIST_EXISTS_OR_ALIASES_INPUT")
    output_dist.parent.mkdir(parents=True, exist_ok=True)
    temp_root = Path(tempfile.mkdtemp(prefix=".p0d-talk-", dir=output_dist.parent))
    try:
        staged = temp_root / "candidate"
        shutil.copytree(dist, staged)
        _apply_inplace(staged, True)
        if output_dist.exists():
            raise ValueError("OUTPUT_RACED_WITH_ANOTHER_WRITER")
        os.replace(staged, output_dist)
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
    print("P0D_TALKING_NPC_TRANSACTIONAL_PUBLISH_PASS", output_dist)
    return True

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", type=Path, required=True)
    ap.add_argument("--enabled", choices=["true", "false"], default="true")
    ap.add_argument("--output-dist", type=Path)
    a = ap.parse_args()
    apply(a.dist, a.enabled == "true", a.output_dist)

if __name__ == "__main__":
    main()
