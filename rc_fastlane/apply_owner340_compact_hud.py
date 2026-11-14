#!/usr/bin/env python3
"""OFF-by-default, private 65->66 compact-HUD preview overlay for owner #340.

Never writes repository branches. Mutates ONLY a scratch Rojo dist supplied by the
caller, after independently validating all baseline source bodies and locks.
The original Game/HUD/Store/Remote are not rewritten; OFF is byte-exact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FEATURE = "OWNER340_COMPACT_HUD_V1"
REL = "client/CompactHUD.client.luau"
SCRIPT = ROOT / "features/owner340_compact_hud/CompactHUD.client.luau"
SCRIPT_BLOB = "fcc678d5f0cbfdd1df1cd2f6fc948e1e9431b118"


def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def sources(dist: Path) -> dict[str, bytes]:
    root = dist / "src"
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*.luau"))}


def apply(dist: Path, enabled: bool) -> dict:
    before = sources(dist)
    assert len(before) == 65, ("EXPECTED_OFFICIAL65", len(before))
    assert "server/Game.server.luau" in before
    assert "client/HUD.client.luau" in before
    assert REL not in before
    assert before["server/Game.server.luau"].count(b"remote.OnServerEvent:Connect(") == 1

    source_lock_path = dist / "SOURCE_LOCK.json"
    feature_lock_path = dist / "RC_FEATURE_LOCK.json"
    project_path = dist / "default.project.json"
    raw_source_lock = source_lock_path.read_bytes()
    raw_feature_lock = feature_lock_path.read_bytes()
    raw_project = project_path.read_bytes()

    source_lock = json.loads(raw_source_lock)
    feature_lock = json.loads(raw_feature_lock)
    project = json.loads(raw_project)
    original_pins = {key: blob(value) for key, value in sorted(before.items())}
    assert source_lock["total_scripts"] == 65
    assert source_lock["blobs"] == original_pins, "BASE_SOURCE_SHA_MISMATCH"
    assert feature_lock["total_sources"] == 65
    assert feature_lock["source_gitblobs"] == original_pins, "BASE_FEATURE_LOCK_MISMATCH"
    assert FEATURE not in feature_lock["feature_flags"]
    starter = project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    assert "CompactHUD" not in starter
    assert project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"] == "src/server"

    if not enabled:
        # No output files, project, lock, or script bytes changed.
        assert source_lock_path.read_bytes() == raw_source_lock
        assert feature_lock_path.read_bytes() == raw_feature_lock
        assert project_path.read_bytes() == raw_project
        return {"enabled": False, "scripts": 65, "original_unchanged": 65}

    new_source = SCRIPT.read_bytes()
    assert blob(new_source) == SCRIPT_BLOB, "HUD_SOURCE_BLOB_MISMATCH"
    for forbidden in (b"FireServer(", b"OnServerEvent:Connect(",
                      b"DataStoreService", b"MarketplaceService",
                      b"TakeDamage(", b"UpdateAsync(", b"SetAsync("):
        assert forbidden not in new_source, ("AUTHORITY_FORBIDDEN", forbidden)
    for needed in (b"RunService:IsStudio()", b"TrapRaidersS1HUD",
                   b'FindFirstChild("Instructions")',
                   b'GetPropertyChangedSignal("Visible")'):
        assert needed in new_source, ("MISSING_OWNER340_GUARD", needed)

    after = dict(before)
    after[REL] = new_source
    pins = {key: blob(value) for key, value in sorted(after.items())}
    assert len(after) == 66
    assert all(after[p] == body for p, body in before.items()), "BASE_REWRITTEN"
    starter["CompactHUD"] = {"$path": "src/" + REL}
    source_lock["total_scripts"] = 66
    source_lock["blobs"] = pins
    source_lock["owner340_compact_hud_preview"] = {
        "feature_id": FEATURE, "stage": "PREP_SOURCE_ONLY_NOT_OFFICIAL_RC",
        "previous_exact_scripts": 65, "new_scripts": [REL],
        "source_gitblob": SCRIPT_BLOB, "studio_only": True,
        "rollback": "omit this optional LocalScript; original65 source and profile unchanged",
        "engine_2client_android_fun": "NOT_TESTED"}
    feature_lock["total_sources"] = 66
    feature_lock["source_gitblobs"] = pins
    feature_lock["feature_flags"][FEATURE] = True

    # All source/input checks complete before any scratch writes.
    destination = dist / "src" / REL
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(new_source)
    project_path.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", "utf8")
    source_lock_path.write_text(json.dumps(source_lock, ensure_ascii=False, indent=2) + "\n", "utf8")
    feature_lock_path.write_text(json.dumps(feature_lock, ensure_ascii=False, indent=2) + "\n", "utf8")
    assert sources(dist) == after
    assert json.loads(project_path.read_text("utf8")) == project
    assert json.loads(source_lock_path.read_text("utf8"))["blobs"] == pins
    return {"enabled": True, "scripts": 66, "previous_unchanged": 65,
            "added": REL, "source_gitblob": SCRIPT_BLOB}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--enabled", choices=("on", "off"), required=True)
    options = parser.parse_args()
    print("P0D_OWNER340_COMPACT_HUD_PREP", apply(options.dist, options.enabled == "on"))
