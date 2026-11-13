#!/usr/bin/env python3
"""Add source-exact Starfall six-shard session collection, after genuine meteor+Starfall private62.

One new Studio-only Script, no changes to original Game/HUD/Remote/Store/DataStore.
All OFF and failed source guards preserve bytes of the pre-existing build.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/"features/star_shards/StarShardHunt.server.luau"
SOURCE_GIT_BLOB="20dc741a00c0cf40d014df70468864b1695e66e1"
PRIOR_STAR_BLOB="311d4c75e38f896f24c982afbc6f9d5c35e90cb4"
FEATURE="STAR_SHARDS_V1"
DEST="server/StarShardHunt.server.luau"
ATTR="P0D_RC_ENABLE_STAR_SHARDS_V1"

def blob(b:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\x00"+b).hexdigest()

def sources(dist:Path)->dict[str,bytes]:
    root=dist/"src"
    return {p.relative_to(root).as_posix():p.read_bytes()
            for p in sorted(root.rglob("*.luau"))}

def apply(dist:Path,profile:str,enabled_override:bool|None=None)->bool:
    if profile!="rich51":
        print("SHARD_HUNT_FALLBACK_PROFILE_OFF",profile)
        return False
    flags=json.loads((ROOT/"FEATURE_SWITCHES.json").read_text("utf8"))["features"]
    enabled=flags[FEATURE]["enabled"] if enabled_override is None else enabled_override
    assert type(enabled) is bool,"SHARDS_FLAG_NOT_BOOL"
    if not enabled:
        print("P0D_SHARD_HUNT_OFF_PRESERVES_REAL61")
        return False
    assert all(flags[k]["enabled"] for k in
        ("WCS_F01_C01","STARRY_PATH_V1","SEVEN_JOBS_PVE_V1","EGG_RELAY_CLASSIC_V1","METEOR_FOURTH_V1")), "SHARDS_REQUIRE_METEOR_PRIVATE62"
    data=SOURCE.read_bytes()
    assert blob(data)==SOURCE_GIT_BLOB,"SHARDS_SOURCE_GIT_BLOB_DRIFT"
    script=data.decode("utf8")
    for marker in (
        'if not RunService:IsStudio() then return end',
        'ServerStorage:GetAttribute("P0D_RC_ENABLE_STAR_SHARDS_V1")~=true',
        'ServerStorage:GetAttribute("P0D_RC_ENABLE_STARRY_PATH_V1")~=true',
        'stage:GetAttribute("PathOpen")~=true',
        'if not stone.CanCollide then return end',
        '-- BEGIN_P0D_STAR_SHARDS_POLICY',
        '-- END_P0D_STAR_SHARDS_POLICY',
        'local locations={1,3,5,6,8,10}',
        'local TOTAL=6',
        'not humanoid or humanoid.Health<=0',
        'player:SetAttribute("P0D_StarShardCount",count)',
    ):
        assert marker in script,("SHARDS_SAFETY_DRIFT",marker)
    for forbidden in ('GetDataStore(', 'UpdateAsync(', 'DataStoreService',
                      'Instance.new("RemoteEvent")','OnServerEvent:Connect(',
                      'TakeDamage(', 'MarketplaceService', 'PromptProductPurchase(',
                      'horde:hit(', 'match.scores', 'carry[target]',
                      'player.leaderstats', 'SetAsync(', 'TeleportService'):
        assert forbidden not in script,("DUPLICATE_AUTHORITY",forbidden)
    before=sources(dist)
    assert len(before)==62,("REQUIRE_REAL62_GAME",len(before))
    required=("server/Game.server.luau","server/WCS_CrystalCanyon.server.luau",
              "server/SevenJobsRules.luau","server/EggRelayPolicy.luau",
              "server/StarfallPath.server.luau","server/MeteorFourth.server.luau")
    assert all(p in before for p in required),"REQUIRED_PREVIOUS_SOURCES_MISSING"
    assert blob(before["server/StarfallPath.server.luau"])==PRIOR_STAR_BLOB,"STAR_PARENT_SOURCE_DRIFT"
    assert DEST not in before,"DUPLICATE_SHARD_SCRIPT"
    lock_path=dist/"SOURCE_LOCK.json"
    lock=json.loads(lock_path.read_text("utf8"))
    pins={p:blob(v) for p,v in sorted(before.items())}
    assert lock["total_scripts"]==62 and lock["blobs"]==pins,"SHARDS_PREVIOUS_SOURCE_LOCK_DRIFT"
    assert lock["rc_star_path_overlay"]["id"]=="STARRY_PATH_V1"
    assert lock["rc_meteor_fourth_overlay"]["id"]=="METEOR_FOURTH_V1"
    assert lock["rc_wcs_f01_c01_overlay"]["id"]=="WCS_F01_C01"
    assert lock["rc_seven_jobs_pve_overlay"]["id"]=="SEVEN_JOBS_PVE_V1"
    assert lock["relay_classic_preview"]["feature_id"]=="EGG_RELAY_CLASSIC_V1"
    feature_path=dist/"RC_FEATURE_LOCK.json"
    feature=None
    if feature_path.exists():
        feature=json.loads(feature_path.read_text("utf8"))
        assert feature["total_sources"]==62 and feature["source_gitblobs"]==pins,"SHARDS_PREVIOUS_FEATURE_LOCK_DRIFT"
        assert FEATURE not in feature["feature_flags"],"SHARDS_ALREADY_INCLUDED"
    cfgpath=dist/"default.project.json"
    cfg=json.loads(cfgpath.read_text("utf8"))
    assert cfg["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    server=cfg["tree"]["ServerStorage"]
    attrs=server["$attributes"]
    assert attrs.get("P0D_RC_ENABLE_STARRY_PATH_V1") is True,"MISSING_STAR_BOOT_FLAG"
    assert attrs["P0D_RC_ENABLE_WCS_F01_C01"] is True
    assert server["P0D_ENABLE_METEOR_SHORTCUT_V1"]["$properties"]["Value"] is True,"MISSING_METEOR_BOOT"
    assert "Workspace:WaitForChild(\"P0D_STARRY_PATH\",170)" in script,"SHARD_170S_BOOT_BUDGET_DRIFT"
    assert ATTR not in attrs,"SHARDS_DUPLICATE_RUNTIME_FLAG"
    # No writes before all source, boot, authority and prior-lock checks.
    attrs[ATTR]=True
    target=dist/"src"/DEST
    target.write_bytes(data)
    cfgpath.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    after=sources(dist)
    assert len(after)==63 and set(after)-set(before)=={DEST},"SHARDS_NOT_EXACTLY_ONE_NEW_SCRIPT"
    assert all(after[p]==before[p] for p in before),"ORIGINAL61_BODY_DRIFT"
    afterpins={p:blob(v) for p,v in sorted(after.items())}
    lock["total_scripts"]=63
    lock["blobs"]=afterpins
    lock["rc_star_shards_overlay"]={
        "id":FEATURE,"source_git_blob":SOURCE_GIT_BLOB,
        "original_star_path_git_blob":PRIOR_STAR_BLOB,
        "prior_62_scripts_byte_identical":True,
        "single_Game_Remote_Store_authority":True,
        "session_only_6_unique_fragments":True,
        "no_saved_level_or_score":True,
        "real_studio":"NOT_TESTED",
        "rollback":"Set FEATURE_SWITCHES.features.STAR_SHARDS_V1.enabled=false"
    }
    lock_path.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    if feature is not None:
        feature["total_sources"]=63
        feature["source_gitblobs"]=afterpins
        feature["feature_flags"][FEATURE]=True
        feature_path.write_text(json.dumps(feature,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("P0D_STAR_SHARDS_PRIVATE63_PRIOR62_SCRIPT_BYTES_EXACT_PASS")
    return True

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--profile",choices=("rich51","rich47","legacy21"),required=True)
    a.add_argument("--dist",type=Path,required=True)
    args=a.parse_args()
    apply(args.dist,args.profile)
