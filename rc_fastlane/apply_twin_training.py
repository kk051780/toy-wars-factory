#!/usr/bin/env python3
"""P0D PREP: canonical TwinBiomes64 + pure session-training module -> private65.

One reviewed existing TwinBiomes Script changes to author's exact training-enabled
byte body; one pure ModuleScript added. Other 63 Luau scripts, project boot,
Game/Remote/Store/HP/score/XP and all unrelated source files are untouched.
Never updates an official branch; modifies only the scratch Rojo distribution.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
FEATURE="TWIN_CREATURE_TRAINING_V1"
TWIN="server/TwinBiomes.server.luau"
MODULE="server/TwinCreatureTraining.luau"
BASE_BLOB="ff48273db7c7f0e240e45fba8b997cad669a5143"
TRAINED_BLOB="ff7c57aae79f03e3fbc72e043fe3f34f5ac373a5"
POLICY_BLOB="b2f8275be676b46fc1ad32050832a4fcf13099af"
TRAINED=ROOT/"features/twin_training/TwinBiomesTrained.server.luau"
POLICY=ROOT/"features/twin_training/TwinCreatureTraining.luau"

def blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def sources(dist:Path)->dict[str,bytes]:
    src=dist/"src"
    return {p.relative_to(src).as_posix():p.read_bytes() for p in sorted(src.rglob("*.luau"))}

def apply(dist:Path, profile:str="rich51", override:bool|None=None)->bool:
    if profile!="rich51":
        print("P0D_TWIN_TRAINING_FALLBACK_PROFILE_OFF")
        return False
    flags=json.loads((ROOT/"FEATURE_SWITCHES.json").read_text("utf8"))["features"]
    enabled=flags[FEATURE]["enabled"] if override is None else override
    assert type(enabled) is bool, "TWIN_TRAINING_SWITCH_MUST_BE_BOOL"
    if not enabled:
        print("P0D_TWIN_TRAINING_OFF_CANONICAL64_ALL_BYTES_UNCHANGED_PASS")
        return False
    assert flags["TWIN_BIOMES_4NPC_V1"]["enabled"],"ORIGINAL_TWIN_REQUIRED"
    before=sources(dist)
    assert len(before)==64,("OFFICIAL64_SCRIPT_COUNT_DRIFT",len(before))
    assert TWIN in before and MODULE not in before,"EXPECTED_EXISTING_UNTRAINED_TWIN"
    assert blob(before[TWIN])==BASE_BLOB,"OFFICIAL_TWIN_AUTHOR_SOURCE_DRIFT"
    assert sum(p=="server/Game.server.luau" for p in before)==1,"SINGLE_GAME_REQUIRED"
    assert before["server/Game.server.luau"].count(b"remote.OnServerEvent:Connect(")==1,"SINGLE_REMOTE_WRITER_REQUIRED"

    lockpath=dist/"SOURCE_LOCK.json"
    featurepath=dist/"RC_FEATURE_LOCK.json"
    cfgpath=dist/"default.project.json"
    lock=json.loads(lockpath.read_text("utf8"))
    features=json.loads(featurepath.read_text("utf8"))
    cfg=json.loads(cfgpath.read_text("utf8"))
    pins={p:blob(v) for p,v in sorted(before.items())}
    assert lock["total_scripts"]==64 and lock["blobs"]==pins,"CANONICAL64_SOURCE_LOCK_DRIFT"
    assert features["total_sources"]==64 and features["source_gitblobs"]==pins,"CANONICAL64_FEATURE_LOCK_DRIFT"
    assert lock["rc_twin_biomes_overlay"]["id"]=="TWIN_BIOMES_4NPC_V1"
    assert lock["rc_twin_biomes_overlay"]["source_gitblob"]==BASE_BLOB
    assert features["feature_flags"]["TWIN_BIOMES_4NPC_V1"] is True
    assert FEATURE not in features["feature_flags"],"TRAINING_DUPLICATE_ADOPTION"
    tree=cfg["tree"]
    assert tree["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    boot=tree["ServerStorage"]["P0D_ENABLE_TWIN_BIOMES_V1"]
    assert boot["$className"]=="BoolValue" and boot["$properties"]["Value"] is True,"TWIN_BOOT_REQUIRED"
    trained=TRAINED.read_bytes()
    policy=POLICY.read_bytes()
    assert blob(trained)==TRAINED_BLOB,"TRAINED_SCRIPT_BLOB_DRIFT"
    assert blob(policy)==POLICY_BLOB,"PURE_POLICY_BLOB_DRIFT"
    s=trained.decode("utf8")
    for marker in (
       'require(script.Parent:WaitForChild("TwinCreatureTraining"))',
       'local level=awardPractice(player,info,npc,crest)',
       'activate(info.effect,level)',
       'player:SetAttribute("P0D_TwinLevel_"..info.id,updated.level)',
       'player:SetAttribute("P0D_TwinEvolved_"..info.id,true)',
       'npc:SetAttribute("EvolutionStage",3)',
       'player:SetAttribute("P0D_TwinCodexCount",count)',
       'entry.model:PivotTo(',
       'if not value or not value:IsA("BoolValue") or value.Value ~= true then',
       'world:SetAttribute("CharacterInstances", 8)',
       'markDiscovery(player,info)'):
        assert marker in s,("TRAINED_SCRIPT_REQUIRED_SOURCE_MISSING",marker)
    for banned in ("DataStoreService","UpdateAsync(", "SetAsync(","MarketplaceService",
                   'Instance.new("RemoteEvent")',"OnServerEvent:Connect(",
                   "TakeDamage(","PromptProductPurchase(", "Humanoid.Health =", "leaderstats"):
        assert banned not in s,("DUPLICATE_GAME_OR_SAVED_AUTHORITY",banned)
    for banned in (b"DataStoreService",b"UpdateAsync(",b"SetAttribute(",b"Instance.new",
                   b"MarketplaceService",b"RemoteEvent",b"FireServer("):
        assert banned not in policy,("TRAINING_MODULE_MUST_BE_PURE",banned)
    assert policy.count(b"function Training.advance(")==1
    assert policy.count(b"return Training")==1
    assert b"local MAX_PRACTICE = 7" in policy
    assert b"local REPEAT_WAIT_SECONDS = 20" in policy

    after=dict(before)
    after[TWIN]=trained
    after[MODULE]=policy
    assert len(after)==65
    assert all(after[p]==data for p,data in before.items() if p!=TWIN),"UNRELATED_SCRIPTS_CHANGED"
    newpins={p:blob(v) for p,v in sorted(after.items())}
    lock["total_scripts"]=65
    lock["blobs"]=newpins
    lock["rc_twin_biomes_overlay"]["previous_source_gitblob"]=BASE_BLOB
    lock["rc_twin_biomes_overlay"]["source_gitblob"]=TRAINED_BLOB
    lock["rc_twin_training_overlay"]={
      "id":FEATURE,"original_twin_blob":BASE_BLOB,"trained_twin_blob":TRAINED_BLOB,
      "pure_training_policy_blob":POLICY_BLOB,"modified_existing_scripts":[TWIN],
      "added_scripts":[MODULE],"no_other_source_changes":True,
      "xp_levels":[1,2,3],"level_up_training_counts":[3,7],
      "practice_cooldown_seconds":20,"skill_effect_seconds":[16,20,24],
      "progress":"SESSION_ONLY_NO_DATASTORE",
      "studio_2client_android_fun":"NOT_TESTED",
      "rollback":"Disable feature switch and rebuild from byte-exact prior64"
    }
    features["total_sources"]=65
    features["source_gitblobs"]=newpins
    features["feature_flags"][FEATURE]=True
    (dist/"src"/TWIN).write_bytes(trained)
    (dist/"src"/MODULE).write_bytes(policy)
    lockpath.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    featurepath.write_text(json.dumps(features,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    assert sources(dist)==after,"OUTPUT_BODIES_NOT_SOURCE_EXACT"
    assert cfgpath.read_bytes()==json.dumps(cfg,ensure_ascii=False,indent=2).encode("utf8")+b"\n" or json.loads(cfgpath.read_text("utf8"))==cfg, "ORIGINAL_ROJO_CONFIG_CHANGED"
    print("P0D_TWIN_TRAINING_CANONICAL64_TO_PRIVATE65_ONE_CHANGED_ONE_ADDED_PASS")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--profile",choices=("rich51","rich47","legacy21"),default="rich51")
    p.add_argument("--enabled",choices=("true","false"))
    a=p.parse_args()
    apply(a.dist,a.profile,None if a.enabled is None else a.enabled=="true")
