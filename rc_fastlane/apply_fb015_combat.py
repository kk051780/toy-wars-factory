#!/usr/bin/env python3
"""FB-008/015 ART-COMBAT private-only source-exact 66->67 overlay.

Insert precisely one visually read-only LocalScript into the real assembled
RC66 source. The existing Game, damage, Horde, HP, egg, Remote, Store and
camera/input controls remain byte-identical. OFF is truly ZERO WRITE.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FEATURE = "ART_COMBAT_SLASH_READONLY_V1"
AUTHOR = ROOT / "features/fb015_combat/ArtCombatSlash.client.luau"
DEST = "client/ArtCombatSlash.client.luau"
PIN = "2edae20c45ca712c344fdcd3093837c7ac37f59d"
ORIGINAL_HORDE_PIN = "fc6ca46d36bb81ce5f1cd3d327ad2ab714b4be38"
BASE = 66


def blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def sources(dist: Path) -> dict[str, bytes]:
    src = dist / "src"
    return {p.relative_to(src).as_posix(): p.read_bytes() for p in sorted(src.rglob("*.luau"))}


def validate_visual(raw: bytes) -> None:
    assert blob(raw) == PIN, "ART_COMBAT_SOURCE_DRIFT"
    src = raw.decode("utf8")
    for marker in (
        "if not RunService:IsStudio() then return end",
        'arena:WaitForChild("EGG_RUMBLE_NEUTRAL_MUSOU_EXPERIMENT", 45)',
        'core:FindFirstChild("RealDamagePopup")',
        'popup:GetPropertyChangedSignal("Enabled")',
        'label:GetPropertyChangedSignal("Text")',
        'string.find(cue, "撃破", 1, true)',
        "MAX_BURSTS_PER_SECOND = 9",
        "MAX_LIVE = 8",
        "if UserInputService.TouchEnabled then 1 else 2",
        'Instance.new("Beam")',
        "Debris:AddItem(holder, .22)",
        "onConfirmedHit(core, popup, label, state)",
        'model.Destroying:Connect(function() detach(model) end)',
        "holder.CanCollide = false",
        "holder.CanQuery = false",
        "holder.CanTouch = false",
    ):
        assert marker in src, ("ART_COMBAT_REQUIRED_MARKER_MISSING", marker)
    for forbidden in (
        'Instance.new("RemoteEvent")', "FireServer(", "OnServerEvent",
        "DataStoreService", "MarketplaceService", "TakeDamage(",
        "UpdateAsync(", "Humanoid.Health =", "SetAttribute(",
        "Camera.CFrame =", "HumanoidRootPart.CFrame =",
    ):
        assert forbidden not in src, ("ART_COMBAT_FORBIDDEN_AUTHORITY", forbidden)


def apply(dist: Path, enabled: bool) -> bool:
    if not enabled:
        print("ART_COMBAT_OFF_ZERO_WRITE_OLD_SOURCE_INTACT")
        return False
    old_bytes = sources(dist)
    assert len(old_bytes) == BASE, ("REQUIRE_OFFICIAL_RC66_SOURCES", len(old_bytes))
    assert DEST not in old_bytes, "ART_COMBAT_DUPLICATE"
    assert blob(old_bytes["server/MusouHorde.luau"]) == ORIGINAL_HORDE_PIN, "HORDE_SOURCE_DRIFT"
    assert old_bytes["server/Game.server.luau"].count(b"remote.OnServerEvent:Connect(") == 1, "NONUNIQUE_GAME_REMOTE"
    original = {name: blob(raw) for name, raw in sorted(old_bytes.items())}
    sp = dist / "SOURCE_LOCK.json"
    fp = dist / "RC_FEATURE_LOCK.json"
    project_path = dist / "default.project.json"
    source_lock = json.loads(sp.read_text("utf8"))
    feature_lock = json.loads(fp.read_text("utf8"))
    project = json.loads(project_path.read_text("utf8"))
    assert source_lock["total_scripts"] == BASE and source_lock["blobs"] == original, "ORIGINAL_LOCK_DRIFT"
    assert feature_lock["total_sources"] == BASE and feature_lock["source_gitblobs"] == original, "FEATURE_LOCK_DRIFT"
    assert FEATURE not in feature_lock.get("feature_flags", {}), "DUPLICATE_FEATURE_ID"
    assert "src/client" in json.dumps(project), "NO_CLIENT_SCRIPT_DESTINATION"
    visual = AUTHOR.read_bytes()
    validate_visual(visual)
    new_blobs = dict(original)
    new_blobs[DEST] = PIN
    receipt = {
        "id": FEATURE,
        "feedback": ["FB-008", "FB-015"],
        "input_scripts": BASE,
        "output_scripts": BASE + 1,
        "base_horde_git_blob": ORIGINAL_HORDE_PIN,
        "source_git_blob": PIN,
        "one_original_game_remote_store": True,
        "all_original_66_bytes_preserved": True,
        "studio": "NOT_TESTED",
        "android": "NOT_TESTED",
        "owner_fun": "ART_NO_GO",
        "rollback": "--enabled false / omit overlay, preserving 66 original bytes",
    }
    # All fail-closed preflight checks run before the first file write.
    (dist / "src" / DEST).write_bytes(visual)
    source_lock["total_scripts"] = BASE + 1
    source_lock["blobs"] = new_blobs
    source_lock["art_combat"] = receipt
    feature_lock["total_sources"] = BASE + 1
    feature_lock["source_gitblobs"] = new_blobs
    feature_lock.setdefault("feature_flags", {})[FEATURE] = True
    feature_lock["art_combat"] = receipt
    sp.write_text(json.dumps(source_lock, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    fp.write_text(json.dumps(feature_lock, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    new_bytes = sources(dist)
    assert len(new_bytes) == BASE + 1
    assert all(new_bytes[name] == raw for name, raw in old_bytes.items())
    assert blob(new_bytes[DEST]) == PIN
    print("ART_COMBAT_PRIVATE67_SOURCE_EXACT_ALL66_PRESERVED")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--enabled", required=True, choices=["true", "false"])
    args = parser.parse_args()
    apply(args.dist, enabled=args.enabled == "true")


if __name__ == "__main__":
    main()
