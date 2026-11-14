#!/usr/bin/env python3
"""FB-008 ART-COMBAT: single real-authority hit-confirmed visual overlay.

Attach ONE new client LocalScript to source-locked rich66 without changing
original Game/Horde/Remote/Store/MapBuilder/HUD, damage/HP/XP/egg/score.
Studio-only PREP; no official RC modifications. OFF is byte-for-byte no-op.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "features/fb008_combat/ConfirmedSlashFX.client.luau"
DEST = "client/ConfirmedSlashFX.client.luau"
BLOB = "4b1dce5635b709d349ab3f00bba7a7cf9d9883bd"
FEATURE = "FB008_CONFIRMED_HIT_SLASH_VFX_V1"
PROJECT_NAME = "P0DConfirmedCombatFX"
COUNT = 66


def gitblob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def sources(dist: Path) -> dict[str, bytes]:
    root = dist / "src"
    assert root.is_dir(), "FB008_SOURCE_DIST_MISSING"
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*.luau"))}


def source_safety() -> bytes:
    content = SOURCE.read_bytes()
    assert gitblob(content) == BLOB, "FB008_AUTHOR_BLOB_DRIFT"
    script = content.decode("utf8")
    for token in (
        "if not RunService:IsStudio() then return end",
        'horde = arena:WaitForChild("EGG_RUMBLE_NEUTRAL_MUSOU_EXPERIMENT", 45)',
        'core:FindFirstChild("RealDamagePopup")',
        'popup:GetPropertyChangedSignal("Enabled"):Connect(',
        'if not alive or not popup.Enabled',
        'model.Name:match("^MUSOU_MINION_%d+$")',
        'model.Name == "MUSOU_ELITE_TELEGRAPH"',
        'local isKO = string.find(markerText,"撃破",1,true)',
        'local function renderConfirmedHit(model,core,popup)',
        '"CONFIRMED_HIT_SLASH_"',
        '"CONFIRMED_KO_GROUND_RIPPLE"',
        "MAX_ACTIVE_PARTS = 48",
        "VIEW_DISTANCE = 115",
        "MIN_PER_TARGET_INTERVAL = .09",
        "p.CanCollide = false",
        "p.CanTouch = false",
        "p.CanQuery = false",
        'horde.ChildAdded:Connect(',
        'horde.Destroying:Connect(',
        "Debris:AddItem(p, .34)",
    ):
        assert token in script, ("FB008_REQUIRED_VISUAL_CONTRACT_MISSING", token)
    for forbidden in (
        'Instance.new("RemoteEvent")', 'FireServer(', 'OnServerEvent:Connect(',
        'DataStoreService', 'UpdateAsync(', 'MarketplaceService',
        'TakeDamage(', 'Humanoid.Health =', 'LoadCharacter(',
        'SetAttribute("Score"', 'TeleportService', 'Terrain:FillBlock',
    ):
        assert forbidden not in script, ("FB008_SECOND_AUTHORITY_FORBIDDEN", forbidden)
    return content


def apply(dist: Path, enabled: bool) -> bool:
    if not enabled:
        print("FB008_OFF_ALL_ORIGINAL66_AND_PROJECT_ZERO_WRITE")
        return False
    script = source_safety()
    old = sources(dist)
    assert len(old) == COUNT, ("FB008_EXPECT_RICH66", len(old))
    assert DEST not in old
    assert "server/Game.server.luau" in old
    assert "server/MusouHorde.luau" in old
    assert "client/HUD.client.luau" in old
    assert old["server/Game.server.luau"].count(b"remote.OnServerEvent:Connect(") == 1
    assert b"RealDamagePopup" in old["server/MusouHorde.luau"]
    assert b"EGG_RUMBLE_NEUTRAL_MUSOU_EXPERIMENT" in old["server/MusouHorde.luau"]
    pins = {p: gitblob(raw) for p, raw in sorted(old.items())}
    sl, fl = dist / "SOURCE_LOCK.json", dist / "RC_FEATURE_LOCK.json"
    pj = dist / "default.project.json"
    a = json.loads(sl.read_text("utf8"))
    b = json.loads(fl.read_text("utf8"))
    project = json.loads(pj.read_text("utf8"))
    assert a["total_scripts"] == COUNT and a["blobs"] == pins, "FB008_SOURCE_DRIFT"
    assert b["total_sources"] == COUNT and b["source_gitblobs"] == pins, "FB008_FEATURE_DRIFT"
    assert FEATURE not in b["feature_flags"], "FB008_DUPLICATE"
    client = project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    assert any(isinstance(v,dict) and v.get("$path") == "src/client/HUD.client.luau"
        for v in client.values()), "FB008_MAIN_HUD_MISSING"
    assert PROJECT_NAME not in client, "FB008_PROJECT_ENTRY_DUPLICATE"
    client[PROJECT_NAME] = {"$path": "src/" + DEST}
    updated = {**old, DEST: script}
    pins2 = {p: gitblob(raw) for p, raw in sorted(updated.items())}
    assert len(updated) == COUNT+1
    assert all(updated[p] == raw for p, raw in old.items())
    receipt = {
        "id": FEATURE, "owner_feedback": ["FB-008","FB-015"],
        "input_scripts": COUNT, "output_scripts": COUNT+1,
        "original66_unchanged": True, "original_project_changed_only_for_new_client": True,
        "one_authoritative_Game_Horde_Remote_Store": True,
        "new_client": DEST, "new_gitblob": BLOB,
        "trigger": "original server Horde RealDamagePopup.Enabled (hit/KO)",
        "live_visual_quality": "NOT_TESTED",
        "low_spec_android_fps": "NOT_TESTED",
        "owner_fun": "FUN_NO_GO",
        "rollback": "omit this adapter or --enabled false writes zero bytes",
    }
    a["total_scripts"] = COUNT+1
    a["blobs"] = pins2
    a["rc_fb008_combat"] = receipt
    b["total_sources"] = COUNT+1
    b["source_gitblobs"] = pins2
    b["feature_flags"][FEATURE] = True
    b["rc_fb008_combat"] = receipt
    # Preflight complete. Exactly one new source file, one project child,
    # two generated locks; no other source writes.
    (dist / "src" / DEST).write_bytes(script)
    sl.write_text(json.dumps(a, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    fl.write_text(json.dumps(b, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    pj.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    after = sources(dist)
    assert len(after) == COUNT+1
    assert all(after[p] == raw for p, raw in old.items()), "FB008_OLD_SCRIPT_MODIFIED"
    assert gitblob(after[DEST]) == BLOB
    print("FB008_COMBAT_VFX_PRIVATE67_ALL66_IDENTICAL_ONE_CLIENT_SOURCE_PASS")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--enabled", required=True, choices=("true","false"))
    args = parser.parse_args()
    apply(args.dist,args.enabled == "true")


if __name__ == "__main__":
    main()
