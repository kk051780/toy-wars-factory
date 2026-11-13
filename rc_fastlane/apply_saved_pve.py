#!/usr/bin/env python3
"""Apply a ONE-file Game combat callsite patch and a pure saved-PvE policy module.

This applies only after the existing durable 54-source overlay. Rollback is
independent: OFF restores identical previous 54 script bodies. No new Remote,
damage authority, Store write, match authority or permanent player stats.
"""
import argparse, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MOD=ROOT/"features/saved_pve/SavedPveMasteryPolicy.luau"
MOD_SHA="edd50ab4b7ff3b50ca26df47c04cb51d0f96152a"
def blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
def src(dist):
    return {p.relative_to(dist/"src").as_posix():p.read_bytes()
            for p in (dist/"src").rglob("*.luau")}
def replace1(s,old,new):
    assert s.count(old)==1,("CURRENT_GAME_CONTEXT_MISMATCH",old,s.count(old))
    return s.replace(old,new,1)
def integrate(dist,profile):
    if profile!="rich51": return False
    flags=json.loads((ROOT/"FEATURE_SWITCHES.json").read_text("utf8"))["features"]
    enabled=flags["SAVED_PVE_MASTERY"]["enabled"]
    assert type(enabled) is bool
    if not enabled:
        print("P0D_SAVED_PVE_MASTERY_OFF_RICH54_UNMODIFIED")
        return False
    assert flags["SIX_SKILL_DURABLE"]["enabled"] is True, "SAVED_PVE_REQUIRES_STORE"
    assert blob(MOD.read_bytes())==MOD_SHA, "SAVED_PVE_MODULE_AUTHOR_DRIFT"
    before=src(dist)
    assert len(before)==54,("REQUIRES_RICH54",len(before))
    lockpath=dist/"SOURCE_LOCK.json"
    lock=json.loads(lockpath.read_text("utf8"))
    assert lock["total_scripts"]==54
    assert lock["rc_durable_skill_overlay"]["id"]=="SIX_SKILL_DURABLE"
    assert lock["blobs"]=={p:blob(d) for p,d in before.items()}
    original=before["server/Game.server.luau"].decode("utf8")
    assert original.count('remote.OnServerEvent:Connect(')==1
    assert original.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert original.count("PersistentHatch.settleSixSkill(")==1
    assert "P0D_SAVED_PVE_MASTERY_V1" not in original
    txt=replace1(original,
        'local PersistentHatch = require(script.Parent:WaitForChild("PersistentHatchStore"))',
        'local PersistentHatch = require(script.Parent:WaitForChild("PersistentHatchStore"))\n'
        'local SavedPvePolicy = require(script.Parent:WaitForChild("SavedPveMasteryPolicy"))')
    hook=(
        '-- P0D_SAVED_PVE_MASTERY_V1: real persisted DEV WEAPON Lv affects neutral\n'
        '-- horde damage ONLY. Existing match/seq/attack owner remains unchanged.\n'
        'local function savedPveMinionMultiplier(player: Player): number\n'
        '    if not RunService:IsStudio() or match.phase~="ACTIVE"\n'
        '        or player.UserId<=0 or carry[player]~=nil\n'
        '        or persistenceState[player]~="SAVED" then return 1 end\n'
        '    local record=persistentProfiles[player]\n'
        '    if record==nil or not PersistentHatch.validate(record) then return 1 end\n'
        '    return select(1,SavedPvePolicy.fromTraining(record.trainingV4))\n'
        'end\n'
    )
    txt=replace1(txt,'local function applyAttack(player: Player, data)',
        hook+'local function applyAttack(player: Player, data)')
    txt=replace1(txt,'*earnedDamageMultiplier(player,"MINION"),now,player.Character)',
        '*SavedPvePolicy.mergeWithEarned(\n'
        '                    earnedDamageMultiplier(player,"MINION"),\n'
        '                    savedPveMinionMultiplier(player)),now,player.Character)')
    assert txt.count("savedPveMinionMultiplier(player)")==1
    assert txt.count("SavedPvePolicy.mergeWithEarned(")==1
    assert txt.count("PersistentHatch.settleSixSkill(")==1
    assert txt.count('remote.OnServerEvent:Connect(')==1
    assert txt.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert "PvP" not in hook or "MINION" in hook
    assert "DataStoreService:GetDataStore" in txt  # exactly old Store, not a new key
    assert "P0D_SAVED_PVE_MASTERY_V1" in txt
    game=dist/"src/server/Game.server.luau"
    game.write_text(txt,encoding="utf8")
    new=dist/"src/server/SavedPveMasteryPolicy.luau"
    assert not new.exists()
    new.write_bytes(MOD.read_bytes())
    after=src(dist)
    assert len(after)==55
    assert sorted(p for p in before if before[p]!=after[p])==["server/Game.server.luau"]
    assert sorted(set(after)-set(before))==["server/SavedPveMasteryPolicy.luau"]
    assert all(before[p]==after[p] for p in before if p!="server/Game.server.luau")
    lock["total_scripts"]=55
    lock["blobs"]={p:blob(raw) for p,raw in sorted(after.items())}
    lock["rc_saved_pve_mastery_overlay"]={
        "id":"SAVED_PVE_MASTERY",
        "modified":["server/Game.server.luau"],
        "added":["server/SavedPveMasteryPolicy.luau"],
        "original_other_53_scripts_identical":True,
        "only_pve_neutral_horde_damage":True,
        "max_extra_multiplier":1.20,
        "does_not_stack_with_existing_earned_power":True,
        "author_saved_level_source":"trainingV4.totalsMicro.WEAPON",
        "real_studio":"NOT_TESTED",
        "rollback":"set SAVED_PVE_MASTERY.enabled=false and rebuild rich54"
    }
    lockpath.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n","utf8")
    extra=dist/"RC_FEATURE_LOCK.json"
    if extra.exists():
        a=json.loads(extra.read_text("utf8"))
        assert a["total_sources"]==54
        a["total_sources"]=55
        a["source_gitblobs"]={p:blob(raw) for p,raw in sorted(after.items())}
        a["feature_flags"]["SAVED_PVE_MASTERY"]=True
        a["original_54_except_Game_unchanged"]=True
        extra.write_text(json.dumps(a,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_SAVED_PVE_MASTERY_RICH55_BASE54_ONE_GAME_PATCH_NEW_MODULE_PASS")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--profile",choices=["rich51","rich47","legacy21"],required=True)
    p.add_argument("--dist",required=True,type=Path)
    args=p.parse_args()
    integrate(args.dist,args.profile)
