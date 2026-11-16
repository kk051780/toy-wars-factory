#!/usr/bin/env python3
"""GQ RARE FIELD EGGS (P0D-006): bounded 60pt unique pickups; two mirrored eggs.

Single current canonical Host + existing ScoreBalance; never rewrites Rules,
Game, Item, Combat, AI, neutral, store, Remote, or adds scripts. Source-only
selection from current 31-script project, fail-closed with byte-exact OFF.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

FEATURE="GQ_RARE_FIELD_EGGS_20261117"
COUNT=31
HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
SCORE=("ServerScriptService","EGGRUMBLE_ScoreBalance")
RARE_IDS=("FIELD_4","FIELD_5")
HOST_OLD=('  local egg=block(session.world,"FieldEgg_"..i,at,Vector3.new(2.6,3.3,2.6),Color3.fromRGB(238,214,108))\n'
          '  egg.Shape=Enum.PartType.Ball\n'
          '  prompt(egg,"卵を拾う","フィールドの卵",function(p)\n')
HOST_NEW=('  -- Two mirrored rare field eggs; game-owned FIELD_4/5 tokens unchanged.\n'
          '  local rareFieldEgg=i==4 or i==5\n'
          '  local eggTint=if rareFieldEgg then Color3.fromRGB(174,119,210) else Color3.fromRGB(238,214,108)\n'
          '  local egg=block(session.world,"FieldEgg_"..i,at,Vector3.new(2.6,3.3,2.6),eggTint)\n'
          '  egg.Shape=Enum.PartType.Ball\n'
          '  if rareFieldEgg then egg.Material=Enum.Material.Glass end\n'
          '  prompt(egg,"卵を拾う",(if rareFieldEgg then "レア卵｜60点" else "フィールドの卵"),function(p)\n')
SCORE_CHANGES=[
 (' EGG_DEPOSIT_CAP=8, EGG_DEPOSIT_RATE=120,\n',
  ' EGG_DEPOSIT_CAP=8, EGG_DEPOSIT_RATE=120,\n RARE_FIELD_EGG_CAP=2, RARE_FIELD_EGG_RATE=60,\n'),
 ('  {name="卵運搬",value=math.min(SCORE.EGG_DEPOSIT_CAP,row.deposited)*SCORE.EGG_DEPOSIT_RATE},\n',
  '  {name="卵運搬",value=math.min(SCORE.EGG_DEPOSIT_CAP,row.deposited)*SCORE.EGG_DEPOSIT_RATE},\n'
  '  {name="希少卵",value=math.min(SCORE.RARE_FIELD_EGG_CAP,row.rareEggs)*SCORE.RARE_FIELD_EGG_RATE},\n'),
 ('  +math.min(SCORE.EGG_DEPOSIT_CAP,row.deposited)*SCORE.EGG_DEPOSIT_RATE\n',
  '  +math.min(SCORE.EGG_DEPOSIT_CAP,row.deposited)*SCORE.EGG_DEPOSIT_RATE\n'
  '  +math.min(SCORE.RARE_FIELD_EGG_CAP,row.rareEggs)*SCORE.RARE_FIELD_EGG_RATE\n'),
 ('    deposited=0,castlesDestroyed=0,teamCastleSupport=0,won=false,score=0}\n',
  '    deposited=0,rareEggs=0,castlesDestroyed=0,teamCastleSupport=0,won=false,score=0}\n'),
 (' local fallenSoFar={} -- replay source-true event order; future deaths are not retroactive\n',
  ' local fallenSoFar={} -- replay source-true event order; future deaths are not retroactive\n'
  ' local claimedRareFieldEggs={} -- per-match idempotency across both teams and all owners\n'),
 ('   if row then row.pendingField+=1 end\n',
  '   if row then\n'
  '    row.pendingField+=1 -- actual egg custody and deposit provenance unchanged\n'
  '    local id=event.eggId\n'
  '    if (id=="FIELD_4" or id=="FIELD_5") and not claimedRareFieldEggs[id] then\n'
  '     claimedRareFieldEggs[id]=true\n'
  '     row.rareEggs+=1 -- match-only score; no buffs, inventory or extra eggs\n'
  '    end\n'
  '   end\n'),
 ('   +math.min(SCORE.EGG_DEPOSIT_CAP,row.deposited)*SCORE.EGG_DEPOSIT_RATE\n',
  '   +math.min(SCORE.EGG_DEPOSIT_CAP,row.deposited)*SCORE.EGG_DEPOSIT_RATE\n'
  '   +math.min(SCORE.RARE_FIELD_EGG_CAP,row.rareEggs)*SCORE.RARE_FIELD_EGG_RATE\n'),
]

def digest(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def apply_hunk(original:str,old:str,new:str)->str:
    if original.count(old)!=1 or original.count(new)!=0:
        raise ValueError("RED_SOURCE_ANCHOR_MISSING_DUPLICATED_OR_ALREADY_SELECTED")
    out=original.replace(old,new,1)
    if out.replace(new,old,1)!=original:
        raise ValueError("RED_INVERSE_NOT_EXACT")
    return out

def apply_host(source:str)->str:
    if "rareFieldEgg" in source:
        raise ValueError("RED_ALREADY_HAS_RARE_EGGS")
    if source.count('local eggId="FIELD_"..i')!=1:
        raise ValueError("RED_ORIGINAL_FIELD_TOKEN_AUTHORITY_NOT_PRESENT")
    if source.count('Rules.takeFieldEgg(session.rules,tostring(p.UserId),eggId)')!=1:
        raise ValueError("RED_ORIGINAL_TAKE_SERVER_GATE_NOT_PRESENT")
    out=apply_hunk(source,HOST_OLD,HOST_NEW)
    for v in ('local eggId="FIELD_"..i','Rules.takeFieldEgg(session.rules,tostring(p.UserId),eggId)'):
        if out.count(v)!=source.count(v):
            raise ValueError("RED_ORIGINAL_EGG_AUTHORITY_MUTATED")
    return out

def apply_score(source:str)->str:
    if "RARE_FIELD_EGG_RATE" in source or "claimedRareFieldEggs" in source:
        raise ValueError("RED_SCORE_ALREADY_SELECTED")
    out=source
    for old,new in SCORE_CHANGES:
        out=apply_hunk(out,old,new)
    if inverse_score(out)!=source:
        raise ValueError("RED_SCORE_OFF_INVERSE_NOT_EXACT")
    if source.count('elseif kind=="FIELD_EGG_TAKEN"')!=1:
        raise ValueError("RED_ORIGINAL_SCORE_EGG_EVENT_AUTHORITY_MISSING")
    if out.count('elseif kind=="FIELD_EGG_TAKEN"')!=1:
        raise ValueError("RED_SCORE_EVENT_CONTROLLER_DUPLICATED")
    return out

def inverse_score(source:str)->str:
    out=source
    for old,new in reversed(SCORE_CHANGES):
        if out.count(new)!=1:
            raise ValueError("RED_SCORE_REVERSE_ANCHOR_COLLISION")
        out=out.replace(new,old,1)
    return out

def mapping(project:Path):
    project=project.resolve(strict=True)
    root=json.loads(project.read_text(encoding="utf-8"))
    if not isinstance(root.get("tree"),dict):
        raise ValueError("RED_NOT_A_ROJO_PROJECT")
    mapping={}
    def scan(node,route=()):
        for k,v in node.items():
            if k.startswith("$"):
                continue
            if not isinstance(v,dict):
                raise ValueError("RED_BAD_ROJO_TREE_CHILD")
            p=route+(k,)
            if "$path" in v:
                if set(v)!={"$path"} or p in mapping:
                    raise ValueError("RED_SCRIPT_AUTHORITY_COLLISION")
                mapping[p]=(project.parent/v["$path"]).resolve(strict=True)
            else:
                scan(v,p)
    scan(root["tree"])
    if len(mapping)!=COUNT or len({k[-1] for k in mapping})!=COUNT:
        raise ValueError("RED_NOT_EXACT_31_EXISTING_SCRIPTS")
    if HOST not in mapping or SCORE not in mapping:
        raise ValueError("RED_EXISTING_HOST_OR_SCORE_MISSING")
    if not mapping[HOST].name.endswith(".server.luau") or not mapping[SCORE].name.endswith(".luau"):
        raise ValueError("RED_SCRIPT_CLASS_CHANGE")
    return root,mapping

def selected(base:Path,out:Path):
    if out.exists() or out.resolve()==base.resolve() or out.parent.resolve()!=base.parent.resolve():
        raise ValueError("RED_NEW_SIBLING_PROJECT_REQUIRED")
    root,before=mapping(base)
    originalHost=before[HOST].read_text(encoding="utf-8")
    originalScore=before[SCORE].read_text(encoding="utf-8")
    newHost=apply_host(originalHost)
    newScore=apply_score(originalScore)
    if newHost.replace(HOST_NEW,HOST_OLD,1)!=originalHost or inverse_score(newScore)!=originalScore:
        raise ValueError("RED_OFF_TO_CURRENT_NOT_BYTE_EXACT")
    hostPath=out.parent/"GQ_RARE_FIELD_ONE_HOST.server.luau"
    scorePath=out.parent/"GQ_RARE_FIELD_ONE_SCORE.luau"
    if hostPath.exists() or scorePath.exists():
        raise ValueError("RED_NO_SOURCE_OVERWRITE")
    hostPath.write_text(newHost,encoding="utf-8")
    scorePath.write_text(newScore,encoding="utf-8")
    project=copy.deepcopy(root)
    def rebase(node,route=()):
        for k,v in node.items():
            if k.startswith("$"): continue
            path=route+(k,)
            if "$path" in v:
                target=hostPath if path==HOST else scorePath if path==SCORE else before[path]
                v["$path"]=os.path.relpath(target,out.parent).replace(os.sep,"/")
            else:
                rebase(v,path)
    rebase(project["tree"])
    out.write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,now=mapping(out)
    diff=[k for k in before if before[k].read_bytes()!=now[k].read_bytes()]
    if set(before)!=set(now) or set(diff)!={HOST,SCORE}:
        raise ValueError("RED_OTHER29_OR_SINGLE_AUTHORITY_MODIFIED")
    proof={
        "feature":FEATURE,
        "source_count":31,"existing_script_changes":2,"other29_byte_exact":True,
        "current_host_off_exact":True,"current_score_off_exact":True,
        "new_scripts":0,"new_game_remote_store":0,"extra_eggs":0,
        "rare_ids":list(RARE_IDS),"rare_eggs_per_session":2,
        "rare_score_per_egg":60,"max_player_rare_points":120,
        "host_sha256_before":digest(originalHost.encode()),
        "host_sha256_after":digest(newHost.encode()),
        "score_sha256_before":digest(originalScore.encode()),
        "score_sha256_after":digest(newScore.encode()),
        "actual_rojo_31_source_class":False,
        "official_rc_adopted":False,
        "studio_android_fun_owner":"NOT_TESTED"
    }
    (out.parent/"GQ_RARE_FIELD_SOURCE_RECEIPT.json").write_text(json.dumps(proof,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ_RARE_FIELD_2_EXISTING_SCRIPTS_29_OTHER_EXACT_OFF_BOTH_PASS")

def embedded(place:Path):
    xml=ET.parse(place)
    found={}
    def txt(node,name):
        props=node.find("Properties")
        if props is None:return None
        for kind in ("string","ProtectedString"):
            val=props.find(f"{kind}[@name='{name}']")
            if val is not None:return val.text or ""
        return None
    def scan(item,route=()):
        if item.tag=="Item":
            name=txt(item,"Name")
            if not name: raise ValueError("RED_NAMELESS_ROJO_INSTANCE")
            route=route+(name,)
            kind=item.get("class")
            if kind in ("Script","LocalScript","ModuleScript"):
                src=txt(item,"Source")
                if src is None or route in found:raise ValueError("RED_BAD_ROJO_EMBEDDED_SOURCE")
                found[route]=(kind,src.replace("\r\n","\n"))
        for child in item:
            if child.tag=="Item":scan(child,route)
    scan(xml.getroot())
    if len(found)!=COUNT:raise ValueError("RED_NOT_EXACT_31_PLACE_SCRIPTS")
    return found

def verify(base:Path,out:Path,place:Path):
    _,before=mapping(base)
    _,after=mapping(out)
    if set(before)!=set(after) or len(after)!=COUNT:
        raise ValueError("RED_SOURCE_TREE_NOT_EXACT_31")
    if after[HOST].read_text()!=apply_host(before[HOST].read_text()) or after[SCORE].read_text()!=apply_score(before[SCORE].read_text()):
        raise ValueError("RED_NOT_AUTHENTIC_APPLIED_TWO_SOURCES")
    if {k for k in before if before[k].read_bytes()!=after[k].read_bytes()}!={HOST,SCORE}:
        raise ValueError("RED_OTHER29_MUTATED")
    found=embedded(place)
    if set(found)!=set(after): raise ValueError("RED_ROJO_PATH_MISMATCH")
    for path,sourceFile in after.items():
        kind=("Script" if sourceFile.name.endswith(".server.luau") else
              "LocalScript" if sourceFile.name.endswith(".client.luau") else "ModuleScript")
        if found[path]!=(kind,sourceFile.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED_ROJO_CLASS_OR_SOURCE_"+path[-1])
    receipt=out.parent/"GQ_RARE_FIELD_SOURCE_RECEIPT.json"
    details=json.loads(receipt.read_text(encoding="utf-8"))
    details.update(actual_rojo_31_source_class=True,rojo_count=31,
                   private_place_bytes=place.stat().st_size,
                   private_place_sha256=digest(place.read_bytes()))
    receipt.write_text(json.dumps(details,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ_RARE_FIELD_ACTUAL_ROJO_31_31_29_OTHER_EXACT_PASS")

def score_native_harness(source:Path,out:Path):
    content=source.read_text(encoding="utf-8")
    if content.count("return Results")!=1:
        raise ValueError("RED_SCORE_MODULE_RETURN_MISSING")
    prefix=content.replace("return Results","",1)
    cases=r'''
local function state(mode,events)
 local castleA={id="A",team=if mode=="TEAM" then "RED" else nil,alive=true,isAI=false,
                  depositedEggs=0,heldEggs=0,vaultEggs=3}
 local castleB={id="B",team=if mode=="TEAM" then "BLUE" else nil,alive=true,isAI=false,
                  depositedEggs=0,heldEggs=0,vaultEggs=3}
 return {mode=mode,phase="ACTIVE",winner=nil,castles={A=castleA,B=castleB},
         ids={"A","B"},events=events}
end
local function event(owner,id)
 return {type="FIELD_EGG_TAKEN",owner=owner,eggId=id}
end
local function row(report,id)
 for _,r in ipairs(report.rows) do if r.id==id then return r end end
 error("row missing")
end
local cases=0
local function check(condition,label)
 if not condition then error("GQ_RARE_TEST_FAIL_"..label) end
 cases+=1
end
local none=Results.build(state("TEAM",{}),{})
check(row(none,"A").rareEggs==0,"no_claim")
check(row(none,"A").score==Results.SCORE.SURVIVE,"no_score_inflation")
local first=Results.build(state("TEAM",{event("A","FIELD_4")}),{})
check(row(first,"A").rareEggs==1,"first_rare")
check(row(first,"A").score==Results.SCORE.SURVIVE+60,"sixty_only")
check(row(first,"B").score==Results.SCORE.SURVIVE,"no_opponent_bonus")
local pair=Results.build(state("TEAM",{event("A","FIELD_4"),event("A","FIELD_5")}),{})
check(row(pair,"A").rareEggs==2,"mirror_two")
check(row(pair,"A").score==Results.SCORE.SURVIVE+120,"hardcap_120")
local dup=Results.build(state("TEAM",{event("A","FIELD_4"),event("B","FIELD_4"),event("A","FIELD_4")}),{})
check(row(dup,"A").rareEggs==1,"duplicate_same_owner")
check(row(dup,"B").rareEggs==0,"duplicate_other_owner")
local normal=Results.build(state("TEAM",{event("A","FIELD_6")}),{})
check(row(normal,"A").score==Results.SCORE.SURVIVE,"normal_egg_no_bonus")
local br=Results.build(state("BATTLE_ROYALE",{event("B","FIELD_5")}),{})
check(row(br,"B").rareEggs==1 and row(br,"B").score==Results.SCORE.SURVIVE+60,"br_same_rules")
local field=Results.build(state("TEAM",{event("A","FIELD_4"),{type="EGG_DROP",owner="A"}}),{})
check(row(field,"A").rareEggs==1,"score_retained_after_drop_only")
local another=Results.build(state("TEAM",{event("A","FIELD_4"),event("B","FIELD_5")}),{})
check(row(another,"A").rareEggs==1 and row(another,"B").rareEggs==1,"two_sides_equal_bonus")
print("GQ_RARE_FIELD_REAL_SCOREBALANCE_NATIVE_CASES_PASS="..cases)
'''
    out.write_text(prefix+cases,encoding="utf-8")
    print("GQ_RARE_FIELD_REAL_AUTHOR_SCORE_NATIVE_HARNESS_READY")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("prepare","verify","harness"))
    p.add_argument("--base",type=Path)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--place",type=Path)
    p.add_argument("--score",type=Path)
    a=p.parse_args()
    if a.action=="prepare":
        if not a.base:p.error("prepare requires --base")
        selected(a.base,a.out)
    elif a.action=="verify":
        if not a.base or not a.place:p.error("verify needs --base and --place")
        verify(a.base,a.out,a.place)
    else:
        if not a.score:p.error("harness needs --score")
        score_native_harness(a.score,a.out)
