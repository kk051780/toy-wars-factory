#!/usr/bin/env python3
"""Source-locked, reversible two-source patch on latest #796 portable41.

Authoritative #811 StageRenderer already receives original #803 seed/manifest.
The original single #764/#797 RealmBattleCore already owns all actual weather,
warnings and vehicle effects. No second clock/HP/lightning/Remote writer.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re

PARENT_HEAD="940b99543d17e9ed6beb66e4a91a70e478868e3c"
REVIEWED_PR_MERGE_SHA="31ba113bcad3149cafb2555049aa811203171109"
STAGE_RENDER_BLOB="0284e40646e800727963667fca5148044cad881f"
REALM=("ServerScriptService","EGGRUMBLE_RealmBattleCore")
RENDER=("ServerScriptService","GQ802_StageTileVisualRenderer")
OTHER_SOURCE_COUNT=39
EXPECTED_NUM=41

STAGE_OLD=' root:SetAttribute("SourceSeed",manifest.seed)\n'
STAGE_INSERT=''' -- GQ8_SEEDED_WEATHER_REALM_BRIDGE_BEGIN
 -- The #803 server-generated seed is only an input; Realm remains the
 -- sole authority applying rain, wind, lightning and damage.
 local phases=manifest.weather
 local validWeather={CLEAR=true,RAIN=true,STORM=true,SNOW=true,
     METEOR=true,AURORA=true}
 if type(phases)~="table" or #phases~=3
     or type(phases[1])~="table" or type(phases[2])~="table"
     or type(phases[3])~="table"
     or phases[1].id~="CLEAR"
     or phases[1].startsAtSeconds~=0
     or phases[2].startsAtSeconds~=120
     or phases[3].startsAtSeconds~=240
     or not validWeather[phases[2].id]
     or not validWeather[phases[3].id]
     or phases[2].id==phases[3].id then
     root:Destroy()
     return nil,"RED_UNVERIFIED_WEATHER_PHASES"
 end
 root:SetAttribute("GQ802_WeatherPolicy","DW_STAGE_V1")
 root:SetAttribute("GQ802_WeatherStart",os.clock())
 root:SetAttribute("GQ802_WeatherPhase2",phases[2].id)
 root:SetAttribute("GQ802_WeatherPhase3",phases[3].id)
 -- GQ8_SEEDED_WEATHER_REALM_BRIDGE_END
'''
REALM_OLD='''  local phase=math.floor((now-state.started)/WEATHER_PHASE_SECONDS)%4
  local weather=phase==3 and "THUNDER" or phase==2 and "RAIN"
   or phase==1 and "WIND" or "CLEAR"
'''
REALM_NEW='''  local weather,weatherTheme=weatherFromVerifiedStage(now,state.started,world)
  if state.weatherTheme~=weatherTheme then
   state.weatherTheme=weatherTheme
   core:SetAttribute("RealmWeatherTheme",weatherTheme)
  end
'''
HELPER_ANCHOR='local function part(parent,name,cf,size,color,collide,alpha)\n'
REALM_HELPER='''-- GQ8_SEEDED_WEATHER_REALM_BRIDGE_BEGIN
-- Read only the server-owned one-seed world child. In absence of a verified
-- stage keep the original 35-second Realm sequence unchanged and safe.
local function weatherFromVerifiedStage(now,realmStart,world)
 local stage=world:FindFirstChild("GQ802_VISUAL_TILE_STAGE_V1")
 if stage and stage.Parent==world
    and stage:GetAttribute("GQ802_WeatherPolicy")=="DW_STAGE_V1" then
  local started=stage:GetAttribute("GQ802_WeatherStart")
  local second=stage:GetAttribute("GQ802_WeatherPhase2")
  local third=stage:GetAttribute("GQ802_WeatherPhase3")
  local approved={CLEAR=true,RAIN=true,STORM=true,SNOW=true,
   METEOR=true,AURORA=true}
  if type(started)=="number" and started==started
      and type(second)=="string" and type(third)=="string"
      and approved[second] and approved[third] and second~=third
      and now>=started and now-started<3600 then
   local elapsed=now-started
   local theme=if elapsed<120 then "CLEAR"
     elseif elapsed<240 then second else third
   -- Only existing Realm effects are legal. Cosmetic snow/aurora/meteor
   -- assets are NOT implemented; never claim their real rendering.
   local effect=if theme=="STORM" or theme=="METEOR" then "THUNDER"
     elseif theme=="RAIN" then "RAIN"
     elseif theme=="SNOW" then "WIND" else "CLEAR"
   return effect,theme
  end
 end
 local phase=math.floor((now-realmStart)/WEATHER_PHASE_SECONDS)%4
 local fallback=phase==3 and "THUNDER" or phase==2 and "RAIN"
   or phase==1 and "WIND" or "CLEAR"
 return fallback,"LEGACY"
end
-- GQ8_SEEDED_WEATHER_REALM_BRIDGE_END

'''
STORM_FENCE='''   if weather~="THUNDER" then
    state.pendingLightning=nil
    core:SetAttribute("LightningWarning",false)
   end
'''


def gitblob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()


def flatten(project:Path):
    path=project.resolve(strict=True)
    doc=json.loads(path.read_text(encoding="utf-8"))
    found={}
    def visit(node,route=()):
        for key,val in node.items():
            if key.startswith("$"):continue
            r=route+(key,)
            if "$path" in val:
                if r in found:raise ValueError("RED_DUPLICATE_SOURCE")
                found[r]=(path.parent/val["$path"]).resolve(strict=True)
            else:visit(val,r)
    visit(doc["tree"])
    return doc,found


def verify_author(project:Path,receipt:Path):
    doc,files=flatten(project)
    info=json.loads(receipt.read_text(encoding="utf-8"))
    if len(files)!=EXPECTED_NUM or info.get("candidate_sha")!=REVIEWED_PR_MERGE_SHA or info.get("source_count")!=41:
        raise ValueError("RED_NOT_LATEST_DRI_41: "+str((len(files),info.get("candidate_sha"),info.get("source_count"))))
    expected={tuple(v["route"].split("/")):v for v in info["sources"]}
    if set(expected)!=set(files):raise ValueError("RED_AUTHOR_SOURCE_ROUTES")
    for k,p in files.items():
        blob=p.read_bytes();entry=expected[k]
        if hashlib.sha256(blob).hexdigest()!=entry["sha256"] or gitblob(blob)!=entry["git_blob"]:
            raise ValueError("RED_ORIGINAL_AUTHOR_SOURCE_DRIFT:"+"/".join(k))
    if gitblob(files[RENDER].read_bytes())!=STAGE_RENDER_BLOB:
        raise ValueError("RED_STAGE_811_WRONG_ORIGIN")
    if STORM_FENCE not in files[REALM].read_text(encoding="utf-8"):
        raise ValueError("RED_MISSING_797_THUNDER_CANCEL")
    return doc,files


def patch(render:str,realm:str)->tuple[str,str]:
    if render.count(STAGE_OLD)!=1 or STAGE_INSERT in render:
        raise ValueError("RED_811_STAGE_INSERTION_ANCHOR")
    if realm.count(HELPER_ANCHOR)!=1 or realm.count(REALM_OLD)!=1:
        raise ValueError("RED_REALM_WEATHER_LOOP_DRIFT")
    if STORM_FENCE not in realm:
        raise ValueError("RED_797_STORM_FENCE_MISSING")
    changed_render=render.replace(STAGE_OLD,STAGE_INSERT+STAGE_OLD,1)
    changed_realm=realm.replace(HELPER_ANCHOR,REALM_HELPER+HELPER_ANCHOR,1).replace(
        REALM_OLD,REALM_NEW,1)
    if (changed_render.replace(STAGE_INSERT,"",1)!=render
         or changed_realm.replace(REALM_HELPER,"",1).replace(REALM_NEW,REALM_OLD,1)!=realm
         or changed_realm.count(STORM_FENCE)!=1):
        raise ValueError("RED_UNRELATED_REALM_OR_STAGE_CHANGE")
    return changed_render,changed_realm


def compose(project:Path,receipt:Path,out:Path):
    doc,base=verify_author(project,receipt)
    if out.exists():raise ValueError("RED_REFUSE_OVERWRITE")
    render,realm=patch(base[RENDER].read_text(encoding="utf-8"),
                       base[REALM].read_text(encoding="utf-8"))
    out.parent.mkdir(parents=True,exist_ok=True)
    new_files={}
    for route,data,ext in ((RENDER,render,".luau"),(REALM,realm,".server.luau")):
        target=out.parent/("GQ8_SeededWeather_"+route[-1]+ext)
        if target.exists():raise ValueError("RED_NEW_SOURCE_PATH_EXISTS")
        target.write_text(data,encoding="utf-8",newline="\n")
        new_files[route]=target
    selected=copy.deepcopy(doc)
    selected["name"]="GQ8_LATEST_DRI_REAL41_SEEDED_WEATHER_PREP_NOT_RC"
    # Full source portability: project directory changes, so all 41 existing
    # path references must be rebased, not merely the two changed source paths.
    def relink(node,route=()):
        for key,val in node.items():
            if key.startswith("$"):continue
            r=route+(key,)
            if "$path" in val:
                p=new_files.get(r,base[r])
                val["$path"]=os.path.relpath(p,out.parent).replace(os.sep,"/")
            else:relink(val,r)
    relink(selected["tree"])
    out.write_text(json.dumps(selected,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,now=flatten(out)
    changed={r for r in base if now[r].read_bytes()!=base[r].read_bytes()}
    if len(now)!=41 or changed!={REALM,RENDER}:
        raise ValueError("RED_NOT_EXACT_TWO_EXISTING_SOURCE_DELTA")
    for k in base:
        if k not in changed and now[k].read_bytes()!=base[k].read_bytes():
            raise ValueError("RED_UNRELATED_REAL41_SOURCE_CHANGED")
    evidence={
        "feature_id":"GQ8_GQ802_SEEDED_WEATHER_REALM_BRIDGE_20261118",
        "base_latest_dri_pr":796,"base_head":PARENT_HEAD,
        "source_count":41,"modified_existing":["/".join(k) for k in sorted(changed)],
        "unmodified_original_dri_scripts":OTHER_SOURCE_COUNT,
        "new_remote_damage_store_game_ownership":0,
        "weather_cycle_authority":"EXISTING_REALM_ONLY",
        "random_schedule_seed_owner":"EXISTING_GQ802_HOST_811_ONLY",
        "fake_new_weather_cosmetics":False,
        "formally_integrated":False,"studio_2client":"NOT_TESTED",
        "android15":"NOT_TESTED","owner_fun":"NO_GO",
        "rollback":"Select exact upstream PR796 portable Real41 source/class, no additional scripts",
    }
    out.with_suffix(".receipt.json").write_text(
        json.dumps(evidence,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ8_GQ802_DRI_REAL41_TWO_SOURCE_WEATHER_BRIDGE_SOURCE_LOCK_PASS")
    return out


if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--original41",type=Path,required=True)
    a.add_argument("--receipt",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    args=a.parse_args()
    compose(args.original41,args.receipt,args.out)
