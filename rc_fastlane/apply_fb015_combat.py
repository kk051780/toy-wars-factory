#!/usr/bin/env python3
"""FB-008/015 ART-COMBAT private SOURCE-EXACT 66->67 transaction.

One original Horde receives ONLY a server-confirmed cosmetic hit cue;
one Studio-only LocalScript renders VFX. No damage, score, Game, Store,
Remote, HP, egg or match rules are altered.
Apply is staged in a sibling and swaps a single directory on same filesystem.
A persisted complete original distribution allows exact OFF restoration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parent
FEATURE = "ART_COMBAT_SLASH_READONLY_V1"
AUTHOR = ROOT / "features/fb015_combat/ArtCombatSlash.client.luau"
HORDE_AUTHOR = ROOT / "features/fb015_combat/MusouHordeArtSignal.luau"
DEST = "client/ArtCombatSlash.client.luau"
HORDE = "server/MusouHorde.luau"
PIN = "7650d205ecba6cf0bccb50859407633227c57aa1"
HORDE_PATCH_PIN = "acf72809877595921ba2f45f9e4d0220a6338853"
ORIGINAL_HORDE_PIN = "fc6ca46d36bb81ce5f1cd3d327ad2ab714b4be38"
BASE = 66

def blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def sources(dist: Path) -> dict[str, bytes]:
    src = dist / "src"
    return {p.relative_to(src).as_posix(): p.read_bytes()
            for p in sorted(src.rglob("*.luau"))}

def backup_dir(dist: Path) -> Path:
    return dist.with_name(dist.name + ".art_combat_original66")

def validate_visual(raw: bytes) -> None:
    assert blob(raw) == PIN, "ART_COMBAT_SOURCE_DRIFT"
    src = raw.decode("utf8")
    for marker in (
        "if not RunService:IsStudio() then return end",
        'arena:WaitForChild("EGG_RUMBLE_NEUTRAL_MUSOU_EXPERIMENT")',
        'core:GetAttributeChangedSignal("P0D_ART_HIT_V1")',
        'core:GetAttribute("P0D_ART_HIT_V1")',
        "serial <= state.lastSerial",
        "state.lastSerial = serial",
        'raw:match("^(%d+)|([KH])|([^|]+)|([^|]+)$")',
        "core.Position + Vector3.new(dx, 0, dz)",
        "model:WaitForChild(\"Core\", 15)",
        'model.Destroying:Connect(function() detach(model) end)',
        "MAX_BURSTS_PER_SECOND = 9",
        "MAX_LIVE = 8",
        "if UserInputService.TouchEnabled then 1 else 2",
        'Instance.new("Beam")',
        "Debris:AddItem(holder, .22)",
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
        'GetPropertyChangedSignal("Text")',
    ):
        assert forbidden not in src, ("ART_COMBAT_FORBIDDEN_AUTHORITY", forbidden)

def validate_horde_patch(before: bytes, after: bytes) -> None:
    assert blob(before) == ORIGINAL_HORDE_PIN, "ORIGINAL_HORDE_DRIFT"
    assert blob(after) == HORDE_PATCH_PIN, "ART_HORDE_DRIFT"
    old, new = before.decode("utf8"), after.decode("utf8")
    seam = '                    m.body.Color=Color3.fromRGB(253,231,111)'
    extra = '''
                    -- Server-only confirmation: one changing cue per REAL hit.
                    -- Encodes serial, hit/KO and true attack origin vector in ONE
                    -- replicated attribute, so identical damage popups still fire.
                    m.artHitSeq=(m.artHitSeq or 0)+1
                    local artFrom=origin-m.pos
                    m.body:SetAttribute("P0D_ART_HIT_V1",string.format(
                        "%d|%s|%.2f|%.2f",m.artHitSeq,
                        if m.hp<=0 then "K" else "H",artFrom.X,artFrom.Z))'''
    assert old.count(seam) == 1
    assert old.replace(seam, seam + extra) == new, "UNEXPECTED_HORDE_COMBAT_CHANGE"
    assert new.count('m.body:SetAttribute("P0D_ART_HIT_V1"') == 1

def _check_original(dist: Path):
    old = sources(dist)
    assert len(old) == BASE and DEST not in old, "REQUIRE_CLEAN_RC66"
    visual = AUTHOR.read_bytes()
    horde = HORDE_AUTHOR.read_bytes()
    validate_visual(visual)
    validate_horde_patch(old[HORDE], horde)
    assert old["server/Game.server.luau"].count(b"remote.OnServerEvent:Connect(") == 1, "NONUNIQUE_GAME_REMOTE"
    original = {n: blob(raw) for n, raw in sorted(old.items())}
    sp = json.loads((dist / "SOURCE_LOCK.json").read_text("utf8"))
    fp = json.loads((dist / "RC_FEATURE_LOCK.json").read_text("utf8"))
    pr = json.loads((dist / "default.project.json").read_text("utf8"))
    assert sp["total_scripts"] == BASE and sp["blobs"] == original
    assert fp["total_sources"] == BASE and fp["source_gitblobs"] == original
    assert FEATURE not in fp.get("feature_flags", {}), "FEATURE_ALREADY_PRESENT"
    starter = pr["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    assert starter["ResultNextStep"]["$path"] == "src/client/ResultNextStep.client.luau"
    assert "ArtCombatSlash" not in starter
    assert pr["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"] == "src/server"
    return old, original, sp, fp, pr, visual, horde

def _stage_candidate(dist: Path, stage: Path, prior):
    old, original, sp, fp, pr, visual, horde = prior
    shutil.copytree(dist, stage)
    (stage / "src" / DEST).parent.mkdir(parents=True, exist_ok=True)
    (stage / "src" / DEST).write_bytes(visual)
    (stage / "src" / HORDE).write_bytes(horde)
    pr["tree"]["StarterPlayer"]["StarterPlayerScripts"]["ArtCombatSlash"] = {
        "$path": "src/client/ArtCombatSlash.client.luau"}
    (stage / "default.project.json").write_text(
        json.dumps(pr, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    next_blobs = dict(original)
    next_blobs[DEST] = PIN
    next_blobs[HORDE] = HORDE_PATCH_PIN
    receipt = {
        "id": FEATURE,
        "fb_ids": ["FB-008", "FB-015"],
        "input_sources": BASE,
        "output_sources": BASE + 1,
        "original_horde_blob": ORIGINAL_HORDE_PIN,
        "modified_horde_blob": HORDE_PATCH_PIN,
        "client_gitblob": PIN,
        "unchanged_original_sources": BASE - 1,
        "only_original_source_modified": HORDE,
        "single_game_remote_store": True,
        "rollback": "toggle OFF restores persisted original66 directory",
        "studio": "NOT_TESTED", "android": "NOT_TESTED", "owner_fun": "ART_NO_GO"
    }
    sp["total_scripts"] = BASE + 1
    sp["blobs"] = next_blobs
    sp["art_combat"] = receipt
    fp["total_sources"] = BASE + 1
    fp["source_gitblobs"] = next_blobs
    fp.setdefault("feature_flags", {})[FEATURE] = True
    fp["art_combat"] = receipt
    (stage / "SOURCE_LOCK.json").write_text(
        json.dumps(sp, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    (stage / "RC_FEATURE_LOCK.json").write_text(
        json.dumps(fp, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    new = sources(stage)
    assert len(new) == BASE + 1
    assert all(new[n] == raw for n, raw in old.items() if n != HORDE)
    assert blob(new[HORDE]) == HORDE_PATCH_PIN and blob(new[DEST]) == PIN
    assert {n: blob(raw) for n, raw in sorted(new.items())} == next_blobs
    return receipt

def apply(dist: Path, enabled: bool) -> bool:
    dist = dist.resolve()
    backup = backup_dir(dist)
    if not dist.exists() and backup.exists():
        os.rename(backup, dist)
        raise RuntimeError("PREVIOUS_INTERRUPTED_SWAP_RECOVERED_RERUN")
    if not enabled:
        if not backup.exists():
            if dist.exists():
                assert DEST not in sources(dist), "ENABLED_OVERLAY_WITHOUT_BACKUP"
            print("ART_COMBAT_OFF_CLEAN_ZERO_WRITE")
            return False
        assert dist.exists() and (dist / "src" / DEST).exists(), "OFF_BACKUP_STATE_INVALID"
        assert blob((dist / "src" / DEST).read_bytes()) == PIN
        assert blob((dist / "src" / HORDE).read_bytes()) == HORDE_PATCH_PIN
        disabled = dist.with_name(dist.name + ".art_combat_disabling")
        assert not disabled.exists(), "PREVIOUS_DISABLE_INCOMPLETE"
        os.rename(dist, disabled)
        try:
            os.rename(backup, dist)
        except BaseException:
            os.rename(disabled, dist)
            raise
        shutil.rmtree(disabled)
        _check_original(dist)
        print("ART_COMBAT_OFF_EXACT_ORIGINAL66_RESTORED")
        return True
    assert dist.is_dir() and not backup.exists(), "ART_COMBAT_ALREADY_APPLIED_OR_BACKUP_EXISTS"
    prior = _check_original(dist)
    # All source and author preflight validation precedes writing a candidate.
    with tempfile.TemporaryDirectory(prefix=".art_combat_stage_", dir=dist.parent) as tmp:
        staged = Path(tmp) / dist.name
        _stage_candidate(dist, staged, prior)
        assert not backup.exists()
        os.rename(dist, backup)
        try:
            os.rename(staged, dist)
        except BaseException:
            os.rename(backup, dist)
            raise
    print("ART_COMBAT_PRIVATE67_SOURCEXACT_65_ORIGINALS_UNCHANGED")
    return True

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--enabled", required=True, choices=["true", "false"])
    args = parser.parse_args()
    apply(args.dist, enabled=args.enabled == "true")

if __name__ == "__main__":
    main()
