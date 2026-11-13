#!/usr/bin/env python3
"""Apply one source-locked Crystal Canyon Script AFTER the successful 57-source RC assembly.
No Game, Remote, Store, reward, combat, or saved-data modifications.
The build flag controls whether the Script exists; Studio missing/false attribute is the default-OFF boot gate, explicit true is required.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FEATURE_ID = "WCS_F01_C01"
FEATURE_PATH = ROOT / "features/wcs_f01_c01/WCS_CrystalCanyon.server.luau"
FEATURE_GIT_BLOB = "96ff818b8c4148a565cfd2a721475a20119e1a28"
DEST_REL = "server/WCS_CrystalCanyon.server.luau"

def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def sources(dist: Path) -> dict[str, bytes]:
    root = dist / "src"
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*.luau"))}

def apply(dist: Path, profile: str, enabled_override: bool | None = None) -> bool:
    if profile != "rich51":
        print("WCS_NOT_IN_FALLBACK_PROFILE", profile)
        return False
    flags = json.loads((ROOT / "FEATURE_SWITCHES.json").read_text(encoding="utf8"))["features"]
    enabled = flags[FEATURE_ID]["enabled"] if enabled_override is None else enabled_override
    assert type(enabled) is bool
    if not enabled:
        print("WCS_DISABLED_EXACT_RICH57")
        return False
    data = FEATURE_PATH.read_bytes()
    assert git_blob(data) == FEATURE_GIT_BLOB, "WCS_SOURCE_BLOB_DRIFT"
    text = data.decode("utf8")
    assert 'if not RunService:IsStudio() then' in text
    assert 'ServerStorage:GetAttribute("P0D_RC_ENABLE_WCS_F01_C01") ~= true' in text
    assert text.count('local function playerIsInGateClosureZone()') == 1
    assert text.count("nextOpenAllowed = os.clock() + REOPEN_COOLDOWN") == 1
    assert "nextOpenAllowed = now + OPEN_SECONDS + REOPEN_COOLDOWN" not in text
    for forbidden in ('GetDataStore(', 'UpdateAsync(', 'Instance.new("RemoteEvent")',
                      'OnServerEvent:Connect(', 'horde:hit(', 'MarketplaceService',
                      'PromptProductPurchase(', 'TakeDamage('):
        assert forbidden not in text, ("WCS_FORBIDDEN_AUTHORITY", forbidden)
    before = sources(dist)
    assert len(before) == 57, ("WCS_REQUIRES_RICH57", len(before))
    assert "server/Game.server.luau" in before
    assert DEST_REL not in before
    lock_path = dist / "SOURCE_LOCK.json"
    lock = json.loads(lock_path.read_text(encoding="utf8"))
    assert lock["total_scripts"] == 57
    assert lock["rc_scout_species_overlay"]["id"] == "SCOUT_SPECIES_V1"
    assert lock["blobs"] == {p: git_blob(v) for p, v in sorted(before.items())}, "BASE57_LOCK_MISMATCH"
    cfg = json.loads((dist / "default.project.json").read_text(encoding="utf8"))
    assert cfg["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"] == "src/server"
    target = dist / "src" / DEST_REL
    assert not target.exists()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    after = sources(dist)
    assert len(after) == 58
    assert set(after) - set(before) == {DEST_REL}
    assert all(after[p] == v for p, v in before.items()), "ORIGINAL57_SCRIPT_DRIFT"
    assert sum(p == "server/Game.server.luau" for p in after) == 1
    lock["total_scripts"] = 58
    lock["blobs"] = {p: git_blob(v) for p, v in sorted(after.items())}
    lock["rc_wcs_f01_c01_overlay"] = {
        "id": FEATURE_ID, "author_script_blob": FEATURE_GIT_BLOB,
        "previous_57_scripts_byte_identical": True,
        "single_game_remote_store": True,
        "studio_only": True, "engine_test": "NOT_TESTED",
        "rollback": "Disable FEATURE_SWITCHES.features.WCS_F01_C01.enabled and rebuild",
    }
    lock_path.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    feature_lock_path = dist / "RC_FEATURE_LOCK.json"
    if feature_lock_path.exists():
        feature_lock = json.loads(feature_lock_path.read_text(encoding="utf8"))
        assert feature_lock["total_sources"] == 57
        feature_lock["total_sources"] = 58
        feature_lock["source_gitblobs"] = {p: git_blob(v) for p, v in sorted(after.items())}
        feature_lock["feature_flags"][FEATURE_ID] = True
        feature_lock_path.write_text(json.dumps(feature_lock, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print("P0D_WCS_RICH58_ONE_ADDITIONAL_SCRIPT_SOURCE_LOCK_PASS")
    return True

if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--profile", choices=("rich51", "rich47", "legacy21"), required=True)
    cli.add_argument("--dist", type=Path, required=True)
    a = cli.parse_args()
    apply(a.dist, a.profile)
