#!/usr/bin/env python3
"""FB-008/015 ART-COMBAT private SOURCE-EXACT 66->67 transaction.

One original Horde receives ONLY a server-confirmed cosmetic hit cue;
one Studio-only LocalScript renders VFX. No damage, score, Game, Store,
client-to-server handler, HP, egg or match rules are altered.
One server-to-client cosmetic RemoteEvent is created under original Horde.
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
PIN = "c8aa1c4ff740ca46b85fc78dbb99c2a2a82a6eba"
HORDE_PATCH_PIN = "6c613406c4c72be31b2a5c38177d54f1af78e617"
ORIGINAL_HORDE_PIN = "fc6ca46d36bb81ce5f1cd3d327ad2ab714b4be38"
BASE = 66

def require(ok, reason):
    if not ok:
        raise RuntimeError(str(reason))


def blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def sources(dist: Path) -> dict[str, bytes]:
    src = dist / "src"
    return {p.relative_to(src).as_posix(): p.read_bytes()
            for p in sorted(src.rglob("*.luau"))}

def backup_dir(dist: Path) -> Path:
    return dist.with_name(dist.name + ".art_combat_original66")

def validate_visual(raw: bytes) -> None:
    require(blob(raw) == PIN, "ART_COMBAT_SOURCE_DRIFT")
    src = raw.decode("utf8")
    for marker in (
        "if not RunService:IsStudio() then return end",
        'arena:WaitForChild("EGG_RUMBLE_NEUTRAL_MUSOU_EXPERIMENT")',
        'mobs:WaitForChild("P0D_ART_COMBAT_SIGNAL_V1")',
        "visualConnection=cue.OnClientEvent:Connect(onConfirmedHit)",
        "serial<=(lastByMob[id] or 0)",
        "lastByMob[id]=serial",
        "makeArc(hitPos,fromPos,isKO)",
        "typeof(hitPos)~=\"Vector3\"",
        "cue:IsA(\"RemoteEvent\")",
        "MAX_BURSTS_PER_SECOND = 9",
        "MAX_LIVE = 8",
        "if UserInputService.TouchEnabled then 1 else 2",
        'Instance.new("Beam")',
        "Debris:AddItem(holder, .22)",
        "holder.CanCollide = false",
        "holder.CanQuery = false",
        "holder.CanTouch = false",
    ):
        require(marker in src, ("ART_COMBAT_REQUIRED_MARKER_MISSING", marker))
    for forbidden in (
        'Instance.new("RemoteEvent")', "FireServer(", "OnServerEvent",
        "DataStoreService", "MarketplaceService", "TakeDamage(",
        "UpdateAsync(", "Humanoid.Health =", "SetAttribute(",
        "Camera.CFrame =", "HumanoidRootPart.CFrame =",
        'GetPropertyChangedSignal("Text")',
        'FireServer(',
        'OnServerEvent:Connect(',
    ):
        require(forbidden not in src, ("ART_COMBAT_FORBIDDEN_AUTHORITY", forbidden))

def validate_horde_patch(before: bytes, after: bytes) -> None:
    require(blob(before) == ORIGINAL_HORDE_PIN, "ORIGINAL_HORDE_DRIFT")
    require(blob(after) == HORDE_PATCH_PIN, "ART_HORDE_DRIFT")
    old, new = before.decode("utf8"), after.decode("utf8")
    old_ctor = '''    folder.Parent=world
    return setmetatable({folder=folder,world=world,mobs={},round=-1,lastTick=0,kills=0},Horde)'''
    new_ctor = '''    folder.Parent=world
    -- Pure outbound visual delivery. No OnServerEvent handler or game authority.
    local visualCue=Instance.new("RemoteEvent")
    visualCue.Name="P0D_ART_COMBAT_SIGNAL_V1"
    visualCue.Parent=folder
    return setmetatable({folder=folder,world=world,mobs={},round=-1,lastTick=0,kills=0,artCue=visualCue},Horde)'''
    seam = '                    m.body.Color=Color3.fromRGB(253,231,111)'
    extra = '''
                    -- A reliable outbound message for EACH real server hit.
                    -- Unlike replicated Attributes it cannot coalesce quick hits.
                    -- This Remote has NO OnServerEvent listener / hit authority.
                    m.artHitSeq=(m.artHitSeq or 0)+1
                    self.artCue:FireAllClients(m.id,m.pos,origin,m.hp<=0,m.artHitSeq,self.round)'''
    require(old.count(old_ctor) == 1 and old.count(seam) == 1,
            "UNEXPECTED_ORIGINAL_HORDE_SEAMS")
    require(old.replace(old_ctor, new_ctor).replace(seam, seam + extra) == new,
            "UNEXPECTED_HORDE_COMBAT_CHANGE")
    require(new.count('Instance.new("RemoteEvent")') == 1 and
            new.count("self.artCue:FireAllClients(") == 1 and
            'OnServerEvent:Connect(' not in new,
            "COSMETIC_REMOTE_MUST_BE_SERVER_OUTBOUND_ONLY")


def _check_original(dist: Path):
    old = sources(dist)
    require(len(old) == BASE and DEST not in old, "REQUIRE_CLEAN_RC66")
    visual = AUTHOR.read_bytes()
    horde = HORDE_AUTHOR.read_bytes()
    validate_visual(visual)
    validate_horde_patch(old[HORDE], horde)
    require(old["server/Game.server.luau"].count(b"remote.OnServerEvent:Connect(") == 1, "NONUNIQUE_GAME_REMOTE")
    original = {n: blob(raw) for n, raw in sorted(old.items())}
    sp = json.loads((dist / "SOURCE_LOCK.json").read_text("utf8"))
    fp = json.loads((dist / "RC_FEATURE_LOCK.json").read_text("utf8"))
    pr = json.loads((dist / "default.project.json").read_text("utf8"))
    require(sp["total_scripts"] == BASE and sp["blobs"] == original, "ART_COMBAT_FAIL_CLOSED")
    require(fp["total_sources"] == BASE and fp["source_gitblobs"] == original, "ART_COMBAT_FAIL_CLOSED")
    require(FEATURE not in fp.get("feature_flags", {}), "FEATURE_ALREADY_PRESENT")
    starter = pr["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    require(starter["ResultNextStep"]["$path"] == "src/client/ResultNextStep.client.luau", "ART_COMBAT_FAIL_CLOSED")
    require("ArtCombatSlash" not in starter, "ART_COMBAT_FAIL_CLOSED")
    require(pr["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"] == "src/server", "ART_COMBAT_FAIL_CLOSED")
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
    require(len(new) == BASE + 1, "ART_COMBAT_FAIL_CLOSED")
    require(all(new[n] == raw for n, raw in old.items() if n != HORDE), "ART_COMBAT_FAIL_CLOSED")
    require(blob(new[HORDE]) == HORDE_PATCH_PIN and blob(new[DEST]) == PIN, "ART_COMBAT_FAIL_CLOSED")
    require({n: blob(raw) for n, raw in sorted(new.items())} == next_blobs, "ART_COMBAT_FAIL_CLOSED")
    return receipt

def apply(dist: Path, enabled: bool) -> bool:
    dist = dist.resolve()
    backup = backup_dir(dist)
    disabled = dist.with_name(dist.name + ".art_combat_disabling")
    # Recover an interrupted OFF without losing either valid tree.
    if disabled.exists():
        require(not enabled, "INTERRUPTED_OFF_RECOVERY_REQUIRES_DISABLED_MODE")
        if not dist.exists() and backup.exists():
            _check_original(backup)  # Validate backup before replacing anything.
            os.rename(backup, dist)
            shutil.rmtree(disabled)
            print("ART_COMBAT_OFF_INTERRUPTED_SWAP_RECOVERED")
            return True
        if dist.exists() and not backup.exists():
            _check_original(dist)
            shutil.rmtree(disabled)
            print("ART_COMBAT_OFF_INTERRUPTED_CLEANUP_RECOVERED")
            return True
        raise RuntimeError("AMBIGUOUS_INTERRUPTED_OFF_STATE_KEEP_ALL_DATA")
    if not dist.exists() and backup.exists():
        _check_original(backup)
        os.rename(backup, dist)
        raise RuntimeError("PREVIOUS_INTERRUPTED_APPLY_RECOVERED_RERUN")
    if not enabled:
        if not backup.exists():
            if dist.exists():
                require(DEST not in sources(dist), "ENABLED_OVERLAY_WITHOUT_BACKUP")
            print("ART_COMBAT_OFF_CLEAN_ZERO_WRITE")
            return False
        # Fail-closed: corrupt original must NEVER replace known-good candidate.
        _check_original(backup)
        require(dist.exists() and (dist / "src" / DEST).exists(), "OFF_BACKUP_STATE_INVALID")
        require(blob((dist / "src" / DEST).read_bytes()) == PIN, "ART_COMBAT_FAIL_CLOSED")
        require(blob((dist / "src" / HORDE).read_bytes()) == HORDE_PATCH_PIN, "ART_COMBAT_FAIL_CLOSED")
        require(not disabled.exists(), "PREVIOUS_DISABLE_INCOMPLETE")
        os.rename(dist, disabled)
        try:
            os.rename(backup, dist)
        except BaseException:
            os.rename(disabled, dist)
            raise
        _check_original(dist)
        shutil.rmtree(disabled)
        print("ART_COMBAT_OFF_EXACT_ORIGINAL66_RESTORED")
        return True
    require(dist.is_dir() and not backup.exists(), "ART_COMBAT_ALREADY_APPLIED_OR_BACKUP_EXISTS")
    prior = _check_original(dist)
    # All source and author preflight validation precedes writing a candidate.
    with tempfile.TemporaryDirectory(prefix=".art_combat_stage_", dir=dist.parent) as tmp:
        staged = Path(tmp) / dist.name
        _stage_candidate(dist, staged, prior)
        require(not backup.exists(), "ART_COMBAT_FAIL_CLOSED")
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
