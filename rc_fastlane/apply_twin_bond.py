#!/usr/bin/env python3
"""P0D isolated official65 -> private66; no direct official/main writes.

Three-source authority policy:
- original Game single writer: strictly pinned two additive melee-PvE anchors
- one existing trained TwinBiomes world: exact original -> bonded author version
- one new pure in-memory Bond Module; no second Store/Remote/Game
When OFF, zero scratch dist writes preserving exact source/project/locks.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
FEATURE="TWIN_BOND_PVE_COMPANION_V1"
GAME="server/Game.server.luau"
TWIN="server/TwinBiomes.server.luau"
MODULE="server/TwinBondPolicy.luau"
GAME_PREV="cdc995d8a64f6a6f6df5abd43fb8210486328572"
TWIN_PREV="ff7c57aae79f03e3fbc72e043fe3f34f5ac373a5"
TWIN_NEXT="5a4b2e623a561ec2ddc72daf1371adb08a8ede27"
BOND_BLOB="e5ab733e1baadf2d79eec6ba53463a16ccd8c0c1"
TRAINING_MODULE="server/TwinCreatureTraining.luau"
SOURCE_TWIN=ROOT/"features/twin_bond/TwinBiomesBonded.server.luau"
SOURCE_BOND=ROOT/"features/twin_bond/TwinBondPolicy.luau"
PREV_COUNT=65

def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def scripts(dist:Path)->dict[str,bytes]:
    src=dist/"src"
    return {p.relative_to(src).as_posix():p.read_bytes() for p in sorted(src.rglob("*.luau"))}

def replace_once(raw:bytes,old:bytes,new:bytes)->bytes:
    assert raw.count(old)==1,("PATCH_ANCHOR_NOT_UNIQUE",old[:95],raw.count(old))
    return raw.replace(old,new)

def patch_game(before:bytes)->bytes:
    assert blob(before)==GAME_PREV,"ORIGINAL_GAME_HEAD_CHANGED_DO_NOT_PATCH"
    body=replace_once(before,
        b'local SavedPvePolicy = require(script.Parent:WaitForChild("SavedPveMasteryPolicy"))',
        b'local SavedPvePolicy = require(script.Parent:WaitForChild("SavedPveMasteryPolicy"))\n'
        b'local TwinBond = require(script.Parent:WaitForChild("TwinBondPolicy"))')
    target=b'local function applyAttack(player: Player, data)'
    helper=b'''local twinBondStorage = game:GetService("ServerStorage")
local function twinBondOnlyNeutralMobBonus(player:Player):number
    -- Source of companion state is only the server-side NPC ProximityPrompt.
    -- THIS original Game remains the single attack/HP/score/reward authority.
    local flag=twinBondStorage:FindFirstChild("P0D_ENABLE_TWIN_BOND_PVE_V1")
    if not RunService:IsStudio() or not flag or not flag:IsA("BoolValue")
        or flag.Value~=true or match.phase~="ACTIVE" or carry[player]~=nil then
        return 1
    end
    if getTeamName(player)~="RED" and getTeamName(player)~="BLUE" then return 1 end
    return math.clamp(TwinBond.pveMultiplier(player,os.clock()),1,1.2)
end

'''
    body=replace_once(body,target,helper+target)
    attack=b'''                    savedPveMinionMultiplier(player)),now,player.Character)'''
    boosted=b'''                    math.min(3.8,savedPveMinionMultiplier(player)
                    *twinBondOnlyNeutralMobBonus(player))),now,player.Character)'''
    body=replace_once(body,attack,boosted)
    assert before.count(b"remote.OnServerEvent:Connect(")==1
    assert body.count(b"remote.OnServerEvent:Connect(")==1
    assert body.count(b"twinBondOnlyNeutralMobBonus(player)")==1
    assert b'local twinBondStorage = game:GetService("ServerStorage")' in body
    assert b'math.min(3.8,savedPveMinionMultiplier(player)' in body
    assert body.count(b"TwinBond.pveMultiplier(player,os.clock())")==1
    assert b"horde:hit(root.Position,look," in body
    return body

def apply(dist:Path,profile:str="rich51",override:bool|None=None)->bool:
    if profile!="rich51":
        print("P0D_TWIN_BOND_NON_RICH_PROFILE_OFF")
        return False
    flags=json.loads((ROOT/"FEATURE_SWITCHES.json").read_text("utf8"))["features"]
    enabled=flags[FEATURE]["enabled"] if override is None else override
    assert type(enabled) is bool
    if not enabled:
        print("P0D_TWIN_BOND_OFF_PRESERVES_OFFICIAL65_ALL_BYTES_PASS")
        return False
    assert flags["TWIN_CREATURE_TRAINING_V1"]["enabled"]
    assert flags["TWIN_BIOMES_4NPC_V1"]["enabled"]
    before=scripts(dist)
    assert len(before)==PREV_COUNT,("EXPECTED_OFFICIAL65",len(before))
    assert GAME in before and TWIN in before and TRAINING_MODULE in before
    assert MODULE not in before, "DUPLICATE_BOND_MODULE"
    assert blob(before[TWIN])==TWIN_PREV, "ORIGINAL_TWIN_TRAINED_SCRIPT_DRIFT"
    assert blob(before[GAME])==GAME_PREV, "ORIGINAL_GAME_HEAD_DRIFT"
    lockfile=dist/"SOURCE_LOCK.json"
    featfile=dist/"RC_FEATURE_LOCK.json"
    projectfile=dist/"default.project.json"
    lock=json.loads(lockfile.read_text("utf8"))
    feats=json.loads(featfile.read_text("utf8"))
    project=json.loads(projectfile.read_text("utf8"))
    originals={p:blob(v) for p,v in sorted(before.items())}
    assert lock["total_scripts"]==65 and lock["blobs"]==originals,"REAL_SOURCE65_LOCK_DRIFT"
    assert feats["total_sources"]==65 and feats["source_gitblobs"]==originals,"FEATURE65_LOCK_DRIFT"
    assert lock["rc_twin_training_overlay"]["id"]=="TWIN_CREATURE_TRAINING_V1"
    assert feats["feature_flags"]["TWIN_CREATURE_TRAINING_V1"] is True
    assert FEATURE not in feats["feature_flags"],"BOND_DUPLICATE"
    storage=project["tree"]["ServerStorage"]
    assert storage["P0D_ENABLE_TWIN_BIOMES_V1"]["$properties"]["Value"] is True
    assert "P0D_ENABLE_TWIN_BOND_PVE_V1" not in storage
    assert project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    twin=SOURCE_TWIN.read_bytes()
    bond=SOURCE_BOND.read_bytes()
    assert blob(twin)==TWIN_NEXT,"AUTHORED_TWIN_BLOB_DRIFT"
    assert blob(bond)==BOND_BLOB,"AUTHORED_BOND_BLOB_DRIFT"
    assert b"require(script.Parent:WaitForChild(\"TwinBondPolicy\"))" in twin
    assert b"summonBoundCompanion(player,info,level)" in twin
    assert b"Bond.forget(player)" in twin
    assert b"BoundUserId" in twin and b"CanCollide=false" in twin
    for forbidden in (b"DataStoreService",b"UpdateAsync(",b"MarketplaceService",
                      b"Instance.new(\"RemoteEvent\")",b"OnServerEvent:Connect(",
                      b"TakeDamage(",b"PromptProductPurchase("):
        assert forbidden not in twin,("SECONDARY_DAMAGE_OR_STORE",forbidden)
        assert forbidden not in bond,("BOND_MODULE_NOT_PURE",forbidden)
    assert b"return Bond" in bond and b"function Bond.pveMultiplier(" in bond
    game=patch_game(before[GAME])
    new=dict(before)
    new[GAME]=game
    new[TWIN]=twin
    new[MODULE]=bond
    assert len(new)==66
    assert all(before[p]==new[p] for p in before if p not in {GAME,TWIN}),"OTHER63_CHANGED"
    pins={p:blob(v) for p,v in sorted(new.items())}
    storage["P0D_ENABLE_TWIN_BOND_PVE_V1"]={"$className":"BoolValue","$properties":{"Value":True}}
    lock["total_scripts"]=66
    lock["blobs"]=pins
    lock["rc_twin_bond_overlay"]={
      "id":FEATURE,"parent_count":65,"new_script":MODULE,
      "replaced_scripts":[GAME,TWIN],
      "original_game":GAME_PREV,"original_twin":TWIN_PREV,
      "bonded_twin":TWIN_NEXT,"pure_bond_policy":BOND_BLOB,
      "new_game_blob":pins[GAME],
      "pve_only_single_original_Game_attacker":True,
      "bonus_max":1.20,"one_active_visual_companion_per_player":True,
      "duration_seconds":180,"switch_wait_seconds":20,
      "studio_explicit_true_only":True,
      "rollback":"OFF preserves all 65 source/project/locks bytes",
      "studio_2player_android_fun":"NOT_TESTED",
      "official_rc_adopted":False,
    }
    feats["total_sources"]=66
    feats["source_gitblobs"]=pins
    feats["feature_flags"][FEATURE]=True
    feats["new_twin_bond_66"]={
       "one_attacker":"original Game only",
       "original_63_unchanged":True,"future_saved_collection":"NOT_IMPLEMENTED",
    }
    # Mutations are only after all current-parent source and safety preflight.
    (dist/"src"/GAME).write_bytes(game)
    (dist/"src"/TWIN).write_bytes(twin)
    (dist/"src"/MODULE).write_bytes(bond)
    projectfile.write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    lockfile.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    featfile.write_text(json.dumps(feats,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    assert scripts(dist)==new,"FINAL_SOURCE_MISMATCH"
    print("P0D_TWIN_BOND_GAME_SOLE_PVE_WRITER_OFFICIAL65_TO_PRIVATE66_PASS")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",required=True,type=Path)
    p.add_argument("--profile",default="rich51",choices=("rich51","rich47","legacy21"))
    p.add_argument("--enabled",choices=("true","false"))
    a=p.parse_args()
    apply(a.dist,a.profile,None if a.enabled is None else a.enabled=="true")
