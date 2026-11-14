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
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from fb015_fs_guard import strict_inventory

ROOT = Path(__file__).resolve().parent
FEATURE = "ART_COMBAT_SLASH_READONLY_V1"
AUTHOR = ROOT / "features/fb015_combat/ArtCombatSlash.client.luau"
HORDE_AUTHOR = ROOT / "features/fb015_combat/MusouHordeArtSignal.luau"
DEST = "client/ArtCombatSlash.client.luau"
HORDE = "server/MusouHorde.luau"
PIN = "c3e3c89b781d446fd8952bee51ec3a2cac46d1ff"
HORDE_PATCH_PIN = "a2d07936bd9fe5bdf3630498c39d61d5a8560d99"
ORIGINAL_HORDE_PIN = "fc6ca46d36bb81ce5f1cd3d327ad2ab714b4be38"
BASE = 66
TRANSACTION = "P0D_ART_COMBAT_FULL_TREE_MANIFEST.json"

def whole_tree(dist: Path) -> dict[str, str]:
    return strict_inventory(dist, exclude=TRANSACTION)

def validate_candidate_tree(dist: Path) -> dict:
    path = dist / TRANSACTION
    require(path.is_file(), "MISSING_ART_COMBAT_FULL_TREE_MANIFEST")
    receipt = json.loads(path.read_text("utf8"))
    require(receipt.get("id") == "P0D_FB015_COMBAT_PRIVATE67_FULL_TREE"
            and receipt.get("candidate") == whole_tree(dist),
            "ART_COMBAT_CANDIDATE_EXTRA_OR_CHANGED_FILE")
    return receipt

def validate_saved_original(original: Path, receipt: dict) -> None:
    require(original.is_dir() and whole_tree(original) == receipt["original"],
            "ART_COMBAT_SAVED_ORIGINAL_EXTRA_OR_CHANGED_FILE")


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
        "state.seen[serial]",
        "state.max=math.max(state.max,serial)",
        "serial<=state.max-16",
        "state.seen[serial]=true",
        "if lastRound==nil then",
        "lastEpoch=epoch",
        'historyConnection=cue:GetAttributeChangedSignal("P0D_ART_RECENT_V1")',
        "replayRecent()",
        "syncServerEpoch()",
        "local MAX_PENDING_CUES=16",
        "sparks:Emit(if isKO then 10 else 4)",
        "HttpService:JSONDecode(encoded)",
        "workspace:GetServerTimeNow()",
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
    header = '''-- No RemoteEvent, no task scheduler, no XP/egg/score/damage-player authority.
local Combat=require(script.Parent:WaitForChild("MusouCombatRules"))'''
    new_header = '''-- In Studio only: outbound cosmetic RemoteEvent and server BindableEvent.
-- No OnServerEvent listener, scheduler, XP/egg/score/damage-player authority.
local RunService=game:GetService("RunService")
local HttpService=game:GetService("HttpService")
local Combat=require(script.Parent:WaitForChild("MusouCombatRules"))'''
    old_ctor = '''    folder.Parent=world
    return setmetatable({folder=folder,world=world,mobs={},round=-1,lastTick=0,kills=0},Horde)'''
    new_ctor = '''    folder.Parent=world
    -- Studio-only visuals; in production no unused remote or server bus exists.
    local visualCue=nil
    local hitBus=nil
    if RunService:IsStudio() then
        visualCue=Instance.new("RemoteEvent")
        visualCue.Name="P0D_ART_COMBAT_SIGNAL_V1"
        visualCue:SetAttribute("P0D_ART_EPOCH_V1",0)
        visualCue:SetAttribute("P0D_ART_RECENT_V1","[]")
        visualCue.Parent=folder
        hitBus=Instance.new("BindableEvent")
        hitBus.Name="P0D_ART_HIT_BUS_V1"
        hitBus.Parent=folder
    end
    return setmetatable({folder=folder,world=world,mobs={},round=-1,lastTick=0,kills=0,artCue=visualCue,artHitBus=hitBus,artEpoch=0,artRecent={}},Horde)'''
    old_reset = '''    self.round=round
    self.lastTick=now'''
    new_reset = '''    self.round=round
    -- Match epochs are monotonic even when the game reuses/lower round IDs.
    -- Reset the snapshot BEFORE this round can create new hit packets.
    if self.artCue then
        self.artEpoch+=1
        table.clear(self.artRecent)
        self.artCue:SetAttribute("P0D_ART_EPOCH_V1",self.artEpoch)
        self.artCue:SetAttribute("P0D_ART_RECENT_V1","[]")
    end
    self.lastTick=now'''
    helper = '''-- BEGIN_ACTUAL_RECENT_HIT_RING
-- Bounded Studio-only snapshot for a slow-joining visual LocalScript.
-- Live reliable packets still carry every individual hit; replay is deduped.
local function appendRecentHit(list,hit,now)
    table.insert(list,hit)
    for i=#list,1,-1 do
        if now-list[i][12]>2.5 then table.remove(list,i) end
    end
    while #list>12 do table.remove(list,1) end
end
-- END_ACTUAL_RECENT_HIT_RING
'''
    seam = '''                    m.body.Color=Color3.fromRGB(253,231,111)'''
    extra = '''
                    -- Every confirmed hit produces a separate private Studio
                    -- client arc packet and a separate server-only BindableEvent.
                    -- A property/Attribute would coalesce back-to-back hits.
                    -- Both channels are appearance-only; no OnServerEvent handler.
                    if self.artCue and self.artHitBus then
                        -- Cosmetic APIs must NEVER abort original HP/KO accounting.
                        local visualOK,visualError=pcall(function()
                            m.artHitSeq=(m.artHitSeq or 0)+1
                            self.artHitBus:Fire(m.body,m.artHitSeq,m.hp<=0,self.round)
                            local stamp=workspace:GetServerTimeNow()
                            appendRecentHit(self.artRecent,{
                                m.id,m.pos.X,m.pos.Y,m.pos.Z,
                                origin.X,origin.Y,origin.Z,
                                m.hp<=0,m.artHitSeq,self.round,self.artEpoch,stamp
                            },stamp)
                            self.artCue:SetAttribute("P0D_ART_RECENT_V1",
                                HttpService:JSONEncode(self.artRecent))
                            self.artCue:FireAllClients(
                                m.id,m.pos,origin,m.hp<=0,m.artHitSeq,self.round,self.artEpoch)
                        end)
                        if not visualOK then
                            warn("P0D_ART_VISUAL_CUE_NON_BLOCKING",visualError)
                        end
                    end'''
    require(old.count(header)==1 and old.count(old_ctor)==1
            and old.count(old_reset)==1 and old.count(seam)==1
            and old.count("function Horde.new(world: Instance)")==1,
            "ORIGINAL_HORDE_SEAM_DRIFT")
    require(old.replace(header,new_header)
            .replace("function Horde.new(world: Instance)",
                     helper+"function Horde.new(world: Instance)")
            .replace(old_ctor,new_ctor).replace(old_reset,new_reset)
            .replace(seam,seam+extra) == new,
            "UNEXPECTED_HORDE_COMBAT_CHANGE")
    require(new.count('Instance.new("RemoteEvent")')==1
            and new.count('Instance.new("BindableEvent")')==1
            and new.count("self.artHitBus:Fire(")==1
            and new.count("self.artCue:FireAllClients(")==1
            and "P0D_ART_VISUAL_CUE_NON_BLOCKING" in new
            and "pcall(function()" in new
            and new.count('HttpService:JSONEncode(')==1
            and new.count('P0D_ART_RECENT_V1')>=2
            and new.count('P0D_ART_EPOCH_V1')>=2
            and "if RunService:IsStudio() then" in new
            and 'OnServerEvent:Connect(' not in new,
            "COSMETIC_HIT_REPLAY_STUDIO_ONLY_NO_AUTHORITY")


def _check_original(dist: Path):
    strict_inventory(dist)  # Reject symlink escapes BEFORE copytree or source access.
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
    (stage / TRANSACTION).write_text(json.dumps({
        "id":"P0D_FB015_COMBAT_PRIVATE67_FULL_TREE",
        "original":whole_tree(dist),
        "candidate":whole_tree(stage),
    },sort_keys=True,indent=2)+"\n",encoding="utf8")
    return receipt

def _apply_locked(dist: Path, enabled: bool) -> bool:
    dist = dist.resolve()
    backup = backup_dir(dist)
    disabled = dist.with_name(dist.name + ".art_combat_disabling")
    # Recover an interrupted OFF without losing either valid tree.
    if disabled.exists():
        require(not enabled, "INTERRUPTED_OFF_RECOVERY_REQUIRES_DISABLED_MODE")
        if not dist.exists() and backup.exists():
            record=validate_candidate_tree(disabled)
            validate_saved_original(backup,record)
            _check_original(backup)
            os.rename(backup, dist)
            validate_candidate_tree(disabled)
            shutil.rmtree(disabled)
            print("ART_COMBAT_OFF_INTERRUPTED_SWAP_RECOVERED")
            return True
        if dist.exists() and not backup.exists():
            record=validate_candidate_tree(disabled)
            validate_saved_original(dist,record)
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
        # Fail-closed: check ALL files in both trees before any delete.
        record=validate_candidate_tree(dist)
        validate_saved_original(backup,record)
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
        validate_saved_original(dist,validate_candidate_tree(disabled))
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

def apply(dist: Path, enabled: bool) -> bool:
    if dist.is_symlink():
        raise RuntimeError("FB015_SYMLINK_DISTRIBUTION_REFUSED")
    # File-less directory lock on the existing parent serializes concurrent
    # toggle calls while preserving zero-write clean OFF.
    dist=dist.resolve()
    fd=os.open(dist.parent,os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX)
        return _apply_locked(dist,enabled)
    finally:
        fcntl.flock(fd,fcntl.LOCK_UN)
        os.close(fd)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--enabled", required=True, choices=["true", "false"])
    args = parser.parse_args()
    apply(args.dist, enabled=args.enabled == "true")

if __name__ == "__main__":
    main()
