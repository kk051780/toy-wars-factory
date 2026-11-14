#!/usr/bin/env python3
"""#372 ART-MINION cosmetic overlay on the actual source-locked rich66 build.

Exactly one Studio-only visual Script appended. No original Game, Horde, HP,
score, egg, Store, Remote or project authority changes. OFF is a no-op.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FEATURE = "ART_MINION_THREE_SILHOUETTES_V1"
AUTHOR = ROOT / "features/art_minion/MinionArtSilhouette.server.luau"
DEST = "server/ArtMinionSilhouette.server.luau"
PIN = "ed5cd56789abc4a7bc8ee3a44b8982aae4f3ff62"
BASE = 66


def blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def sources(dist: Path) -> dict[str, bytes]:
    src = dist / "src"
    return {p.relative_to(src).as_posix(): p.read_bytes() for p in sorted(src.rglob("*.luau"))}


def validate_scene(raw: bytes) -> None:
    assert blob(raw) == PIN, "ART_MINION_SOURCE_DRIFT"
    text = raw.decode("utf8")
    for anchor in (
        'if not RunService:IsStudio() then return end',
        'arena:WaitForChild("EGG_RUMBLE_NEUTRAL_MUSOU_EXPERIMENT", 45)',
        'model.Name:match("^MUSOU_MINION_(%d+)$")',
        'model.Name == "MUSOU_ELITE_TELEGRAPH"',
        'local function knight(model, core)',
        'local function wraith(model, core)',
        'local function brute(model, core)',
        'local function elite(model, core)',
        'mobsFolder.ChildAdded:Connect(',
        'model:SetAttribute("P0D_ART_MINION_V1", true)',
        "sparks.Rate = 0",
        'sparks:Emit(4)',
        'sparks:Emit(10)',
        'item.Size = size',
        'item.CanCollide = false',
        'item.CanQuery = false',
        'item.CanTouch = false',
        'item.AlwaysOnTop = false',
        'item.MaxDistance = 27',
    ):
        assert anchor in text, ("ART_MINION_CONTRACT_MISSING", anchor)
    assert text.count('Instance.new("RemoteEvent")') == 0
    for forbidden in (
        'DataStoreService', 'MarketplaceService', 'UpdateAsync(', 'FireServer(',
        'OnServerEvent:Connect(', 'TakeDamage(', 'match.hp[', 'match.scores[',
        'hum.Health =', 'TeleportService',
    ):
        assert forbidden not in text, ("ART_MINION_UNSAFE_AUTHORITY", forbidden)


def apply(dist: Path, enabled: bool) -> bool:
    if not enabled:
        print("ART_MINION_OFF_RETAIN_PREVIOUS66_ALL_BYTES")
        return False
    before = sources(dist)
    assert len(before) == BASE, ("REQUIRE_RC66", len(before))
    assert DEST not in before, "ART_MINION_DUPLICATE"
    horde = before.get("server/MusouHorde.luau")
    assert horde and b"MUSOU_MINION_" in horde and b"EGG_RUMBLE_NEUTRAL_MUSOU_EXPERIMENT" in horde
    assert before["server/Game.server.luau"].count(b"remote.OnServerEvent:Connect(") == 1
    old = {p: blob(raw) for p, raw in sorted(before.items())}
    sp = dist / "SOURCE_LOCK.json"
    fp = dist / "RC_FEATURE_LOCK.json"
    source_lock = json.loads(sp.read_text("utf8"))
    feature_lock = json.loads(fp.read_text("utf8"))
    project = json.loads((dist / "default.project.json").read_text("utf8"))
    assert source_lock["total_scripts"] == BASE and source_lock["blobs"] == old
    assert feature_lock["total_sources"] == BASE and feature_lock["source_gitblobs"] == old
    assert FEATURE not in feature_lock.get("feature_flags", {})
    assert project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"] == "src/server"
    visual = AUTHOR.read_bytes()
    validate_scene(visual)
    new = dict(old)
    new[DEST] = PIN
    receipt = {
        "id": FEATURE, "fb_ids": ["FB-008", "FB-012", "FB-015"],
        "input_scripts": BASE, "output_scripts": BASE+1,
        "previous_66_byte_identical": True, "single_Game_Remote_Store": True,
        "visual_script": DEST, "visual_git_blob": PIN,
        "classes": ["KNIGHT", "WRAITH", "BRUTE", "ELITE"],
        "studio_engine_animation_and_fps": "NOT_TESTED",
        "owner_fun": "ART_NO_GO",
        "rollback": "omit this source overlay or --enabled false writes zero bytes",
    }
    # Strict preflight above must finish before first write.
    (dist / "src" / DEST).write_bytes(visual)
    source_lock["total_scripts"] = BASE+1
    source_lock["blobs"] = new
    source_lock["rc_art_minion"] = receipt
    feature_lock["total_sources"] = BASE+1
    feature_lock["source_gitblobs"] = new
    feature_lock["feature_flags"][FEATURE] = True
    feature_lock["rc_art_minion"] = receipt
    sp.write_text(json.dumps(source_lock, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    fp.write_text(json.dumps(feature_lock, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    after = sources(dist)
    assert len(after) == BASE+1
    assert all(after[p] == raw for p, raw in before.items())
    assert blob(after[DEST]) == PIN
    print("ART_MINION_PRIVATE67_REAL_HORDE_SOURCE_EXACT_66_PRESERVED_PASS")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--enabled", required=True, choices=("true", "false"))
    args = parser.parse_args()
    apply(args.dist, args.enabled == "true")


if __name__ == "__main__":
    main()
