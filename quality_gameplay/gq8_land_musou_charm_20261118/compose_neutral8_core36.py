#!/usr/bin/env python3
"""GQ800 real neutral-actor visual bridge: one existing Swarm, eight distinct species.

Source selector only. The official Core36 RBXLX is the only input for current
runtime Source/Class. No independent spawner, combat, scoring or Remote owner.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

SPECIES=("BANNER_KNIGHT","TINY_SHIELD","SPIKE_BOAR","ACORN_IMP",
         "SHY_WRAITH","ICE_SLIME","SPARK_GOBLIN","BABY_GOLEM")
SWARM=("ServerScriptService","EGGRUMBLE_SwarmCombat")
CLASSES={"Script":".server.luau","LocalScript":".client.luau","ModuleScript":".luau"}
BASE="f77b4d4393d9e9b19b65566413432a7a9f13962b"

STYLES = """
local NEUTRAL_ORDER={"BANNER_KNIGHT","TINY_SHIELD","SPIKE_BOAR","ACORN_IMP",
 "SHY_WRAITH","ICE_SLIME","SPARK_GOBLIN","BABY_GOLEM"}
-- Fixed 3-part original rig with at most one new non-collidable part/actor.
-- Silhouettes differ in body and head proportions; color is not the only cue.
local NEUTRAL_VISUALS={
 BANNER_KNIGHT={body=Color3.fromRGB(85,105,169),head=Color3.fromRGB(245,204,130),width=1.7,height=2.5,headScale=1.2,style="BANNER"},
 TINY_SHIELD={body=Color3.fromRGB(115,178,151),head=Color3.fromRGB(254,215,152),width=1.1,height=1.65,headScale=1.0,style="SHIELD"},
 SPIKE_BOAR={body=Color3.fromRGB(153,92,71),head=Color3.fromRGB(225,145,99),width=2.5,height=1.3,headScale=1.1,style="SNOUT"},
 ACORN_IMP={body=Color3.fromRGB(167,129,76),head=Color3.fromRGB(242,188,85),width=1.25,height=1.45,headScale=1.7,style="CAP"},
 SHY_WRAITH={body=Color3.fromRGB(142,133,198),head=Color3.fromRGB(218,207,255),width=1.1,height=2.0,headScale=1.45,style="GHOST"},
 ICE_SLIME={body=Color3.fromRGB(109,188,218),head=Color3.fromRGB(189,241,248),width=1.8,height=1.3,headScale=1.6,style="SLIME"},
 SPARK_GOBLIN={body=Color3.fromRGB(235,160,73),head=Color3.fromRGB(246,226,99),width=1.2,height=1.75,headScale=1.05,style="HORN"},
 BABY_GOLEM={body=Color3.fromRGB(125,132,151),head=Color3.fromRGB(201,204,209),width=2.2,height=2.35,headScale=1.2,style="ROCK"},
}
"""
VISUAL = """
 local visual=NEUTRAL_VISUALS[species] or NEUTRAL_VISUALS.BANNER_KNIGHT
 m:SetAttribute("EGGRUMBLE_Species",species)
 m:SetAttribute("EGGRUMBLE_NeutralId",actorId)
 root.Color=visual.body;root.Size=Vector3.new(visual.width,visual.height,1.5)
 head.Color=visual.head;head.Size=Vector3.new(visual.headScale,visual.headScale,visual.headScale)
 head.Position=root.Position+Vector3.new(0,visual.height*.73,0)
 local shield=m:FindFirstChild("Shield")
 if shield and shield:IsA("BasePart") then
  shield.Size=if visual.style=="SHIELD" then Vector3.new(.55,1.8,1.7)
   else Vector3.new(.3,1,.8)
  shield.Transparency=if visual.style=="GHOST" or visual.style=="SLIME" then 1 else 0
  shield.Color=visual.body
 end
 if visual.style=="GHOST" then
  root.Transparency=.38;head.Transparency=.3
 elseif visual.style=="SLIME" then
  root.Shape=Enum.PartType.Ball;root.Transparency=.23
 end
 local ornament=if visual.style=="BANNER" then "FlagTip"
  elseif visual.style=="SNOUT" then "Snout"
  elseif visual.style=="CAP" then "AcornCap"
  elseif visual.style=="HORN" then "SparkHorn"
  elseif visual.style=="ROCK" then "StoneShoulder" else nil
 if ornament then
  local detail=piece(m,ornament,head.Position+Vector3.new(0,visual.headScale*.67,0),
   Vector3.new(.8,.4,.7),visual.head)
  detail.CanTouch=false;detail.CanQuery=false
  if visual.style=="CAP" or visual.style=="SNOUT" then detail.Shape=Enum.PartType.Ball end
 end
"""

def transform(src:str)->str:
    # Patch the soldier constructor rather than the caller. Other quality
    # writers legitimately changed addEnemy and terrain clearance in #707.
    if any(marker in src for marker in ("EGGRUMBLE_NeutralId","NEUTRAL_VISUALS",
                                      "GQ800_NEUTRAL8_REAL_ACTOR")):
        raise ValueError("RED_DUPLICATE_NEUTRAL8_BRIDGE")
    anchors={
        "local function soldier(parent:Instance,at:Vector3):Model":1,
        " m.PrimaryPart=root\n":1,
    }
    for needle,n in anchors.items():
        if src.count(needle)!=n:
            raise ValueError("RED_ORIGINAL_SWARM_SOURCE_CHANGED:"+needle)
    src=src.replace("local function soldier(parent:Instance,at:Vector3):Model",
       STYLES+"\nlocal nextNeutralActorId=0\n"+
       "local function soldier(parent:Instance,at:Vector3):Model\n"+
       " nextNeutralActorId+=1\n"+
       " local species=NEUTRAL_ORDER[((nextNeutralActorId-1)%#NEUTRAL_ORDER)+1]\n"+
       ' local actorId="N"..tostring(nextNeutralActorId)',1)
    src=src.replace(" m.PrimaryPart=root\n",VISUAL+" m.PrimaryPart=root\n",1)
    return "-- GQ800_NEUTRAL8_REAL_ACTOR: existing sole Swarm soldier constructor, cosmetic-only\n"+src

def project_routes(project:dict)->dict[tuple[str,...],dict]:
    result={}
    def walk(tree,prefix=()):
        for name,child in tree.items():
            if name.startswith("$"):continue
            if not isinstance(child,dict):raise ValueError("RED_BAD_ROJO_TREE")
            path=prefix+(name,)
            if "$path" in child:
                if path in result:raise ValueError("RED_DUPLICATE_ROUTE")
                result[path]=child
            else:walk(child,path)
    walk(project["tree"])
    return result

def source_from_place(place:Path)->dict[tuple[str,...],tuple[str,str]]:
    from xml.etree.ElementTree import ParseError
    from collections import Counter
    root=ET.parse(place).getroot()
    if root.get("version")!="4":raise ValueError("RED_NOT_RBXLX_V4")
    result={}
    def visit(item,prefix):
        props=item.find("Properties")
        name=props.findtext("string[@name='Name']") if props is not None else None
        if not name:raise ValueError("RED_BAD_NAME")
        path=prefix+(name,)
        cls=item.get("class")
        if cls in CLASSES:
            source=props.findtext("string[@name='Source']")
            if source is None:source=props.findtext("ProtectedString[@name='Source']")
            if source is None or path in result:raise ValueError("RED_MISSING_DUPLICATE_SOURCE")
            result[path]=(cls,source.replace("\r\n","\n"))
        for child in item.findall("Item"):visit(child,path)
    for item in root.findall("Item"):visit(item,())
    return result

def build(place:Path,project_file:Path,receipt_file:Path,out:Path,head:str):
    if head!=BASE:raise ValueError("RED_BASE_MOVED_REPLAN_REQUIRED")
    if out.exists():raise ValueError("RED_REFUSE_OVERWRITE")
    receipt=json.loads(receipt_file.read_text())
    if receipt.get("build_sha")!=head or not receipt.get("selected_in_formal_rc_branch"):
        raise ValueError("RED_NOT_SAME_HEAD_FORMAL_ARTIFACT")
    actual=source_from_place(place)
    model=json.loads(project_file.read_text())
    routes=project_routes(model)
    if len(actual)!=36 or len(routes)!=36 or set(routes)!=set(actual) or SWARM not in actual:
        raise ValueError("RED_NOT_EXACT_CANONICAL36")
    if actual[SWARM][0]!="ModuleScript":
        raise ValueError("RED_SWARM_NOT_SINGLE_MODULE")
    out.mkdir(parents=True)
    base=out/"OFF36";base.mkdir()
    src_dir=base/"sources";src_dir.mkdir()
    on=out/"ON36";on.mkdir()
    on_sources=on/"sources";on_sources.mkdir()
    off_project=copy.deepcopy(model)
    on_project=copy.deepcopy(model)
    off_routes=project_routes(off_project)
    on_routes=project_routes(on_project)
    locks={}
    for route,(cls,source) in sorted(actual.items()):
        ext=CLASSES[cls];name=route[-1]+ext
        f=src_dir/name
        if f.exists():raise ValueError("RED_SOURCE_NAME_COLLISION")
        f.write_text(source,encoding="utf-8",newline="\n")
        g=on_sources/name
        g.write_text(transform(source) if route==SWARM else source,
                     encoding="utf-8",newline="\n")
        off_routes[route]["$path"]="sources/"+name
        on_routes[route]["$path"]="sources/"+name
        locks["/".join(route)]={
            "original_sha256":hashlib.sha256(f.read_bytes()).hexdigest(),
            "selected_sha256":hashlib.sha256(g.read_bytes()).hexdigest(),
            "changed":route==SWARM,
            "class":cls}
    if sum(int(v["changed"]) for v in locks.values())!=1:
        raise ValueError("RED_MULTI_WRITER")
    (base/"OFF36.project.json").write_text(json.dumps(off_project,ensure_ascii=False,indent=2)+"\n")
    (on/"GQ800_NEUTRAL8_ON36.project.json").write_text(json.dumps(on_project,ensure_ascii=False,indent=2)+"\n")
    (out/"GQ800_NEUTRAL8_SOURCE_LOCK.json").write_text(json.dumps({
        "schema":"GQ800_NEUTRAL8_REAL_ACTOR_SOURCE_LOCK_V1",
        "official_rc_sha":head,"source_count_on":36,"source_count_off":36,
        "changed_existing_source":"ServerScriptService/EGGRUMBLE_SwarmCombat",
        "new_server_game_or_ai_owner":0,"new_remote_or_score_owner":0,
        "faction_conversion_connected":False,
        "real_studio_measured":False,"formal_rc_written":False,
        "source_sha256":locks},ensure_ascii=False,indent=2)+"\n")
    print("GQ800_NEUTRAL8_REAL_ACTOR_SELECTION_1_OF_36_CHANGED_OFF36_READY")
    return on/"GQ800_NEUTRAL8_ON36.project.json"

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--place",type=Path,required=True)
    parser.add_argument("--project",type=Path,required=True)
    parser.add_argument("--receipt",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--head",required=True)
    args=parser.parse_args()
    build(args.place,args.project,args.receipt,args.out,args.head)
