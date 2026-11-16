#!/usr/bin/env python3
"""GQ646: preview lobby safe ground/spawn, one current Host source only.

Prep candidate, not a direct formal RC writer. Original 31-source game remains
one Host, one Combat, one Bot, one Swarm; OFF restores the exact prior Host.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

TARGET = "EGGRUMBLE_LobbyCastleModesPreview"
ANCHOR = "local function block(parent:Instance,name:string,pos:Vector3,size:Vector3,color:Color3):Part"
MARKER = "-- GQ646_LOBBY_SAFE_SPAWN_BEGIN"
OUTPUT_NAME = "EGGRUMBLE_LobbyCastleModesPreview_GQ646.server.luau"
RECEIPT_NAME = "GQ646_LOBBY_SAFE_SPAWN_RC31_RECEIPT.json"

INSERT = r'''-- GQ646_LOBBY_SAFE_SPAWN_BEGIN: isolated from both battlefields and role/queue writers.
-- The original V3 lobby constructs gates and role stands, but no supporting floor.
local lobbyGround=Instance.new("Part")
lobbyGround.Name="GQ646_LOBBY_SAFE_GROUND"
lobbyGround.Anchored=true
lobbyGround.Size=Vector3.new(154,2,156)
lobbyGround.Position=root+Vector3.new(0,-5,21)
lobbyGround.Material=Enum.Material.Grass
lobbyGround.Color=Color3.fromRGB(88,139,104)
lobbyGround.CanCollide=true
lobbyGround.Parent=folder
local lobbySpawn=Instance.new("SpawnLocation")
lobbySpawn.Name="GQ646_LOBBY_NEUTRAL_SPAWN"
lobbySpawn.Anchored=true
lobbySpawn.Size=Vector3.new(12,1,12)
lobbySpawn.Position=root+Vector3.new(0,-2,-27)
lobbySpawn.Neutral=true
lobbySpawn.Enabled=true
lobbySpawn.AllowTeamChangeOnTouch=false
lobbySpawn.Duration=0
lobbySpawn.Material=Enum.Material.SmoothPlastic
lobbySpawn.Color=Color3.fromRGB(232,230,178)
lobbySpawn.CanCollide=true
lobbySpawn.Parent=folder
local function bindGQ646LobbyCharacter(player:Player)
 local function tryPlace(character:Model)
  task.defer(function()
   if not player.Parent or player.Character~=character then return end
   -- The match's existing respawn handler owns every in-session character.
   local mode=joined[player.UserId]
   if mode and sessions[mode] then return end
   local hrp=character:FindFirstChild("HumanoidRootPart") or character:WaitForChild("HumanoidRootPart",6)
   local humanoid=character:FindFirstChildOfClass("Humanoid")
   if not hrp or not hrp:IsA("BasePart") or not humanoid or humanoid.Health<=0 then return end
   if player.Character~=character then return end
   mode=joined[player.UserId]
   if mode and sessions[mode] then return end
   hrp.CFrame=CFrame.new(root+Vector3.new(0,5,-27))
  end)
 end
 player.CharacterAdded:Connect(tryPlace)
 if player.Character then tryPlace(player.Character) end
end
Players.PlayerAdded:Connect(bindGQ646LobbyCharacter)
for _,presentPlayer in ipairs(Players:GetPlayers()) do
 bindGQ646LobbyCharacter(presentPlayer)
end
-- GQ646_LOBBY_SAFE_SPAWN_END

'''

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def mapping(project:Path):
    project=project.resolve(strict=True)
    obj=json.loads(project.read_text(encoding="utf8"))
    found={}
    def walk(node,route=()):
        for name,value in node.items():
            if name.startswith("$"):continue
            if not isinstance(value,dict):raise ValueError("RED_NON_TREE_NODE")
            path=route+(name,)
            if "$path" in value:
                if set(value)!={"$path"} or path in found:raise ValueError("RED_BAD_SOURCE_NODE")
                found[path]=(project.parent/value["$path"]).resolve(strict=True)
            else:walk(value,path)
    walk(obj["tree"])
    if len(found)!=31 or len({k[-1] for k in found})!=31:raise ValueError("RED_NOT_31_UNIQUE_SOURCES")
    target=[key for key in found if key[-1]==TARGET]
    if len(target)!=1:raise ValueError("RED_NOT_SINGLE_HOST")
    return obj,found,target[0]

def transform(source:str)->str:
    if MARKER in source or "GQ646_LOBBY_NEUTRAL_SPAWN" in source:
        raise ValueError("RED_DUPLICATE_SAFE_SPAWN")
    if source.count(ANCHOR)!=1:raise ValueError("RED_HOST_INSERT_ANCHOR_DRIFT")
    if source.count('local folder=Instance.new("Folder");folder.Name="EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW";folder.Parent=workspace')!=1:
        raise ValueError("RED_ORIGINAL_LOBBY_MODEL_DRIFT")
    if "local joined:" not in source or "local sessions:" not in source:
        raise ValueError("RED_MATCH_MEMBERSHIP_NOT_PRESENT")
    changed=source.replace(ANCHOR,INSERT+ANCHOR,1)
    if changed.replace(INSERT,"",1)!=source:
        raise ValueError("RED_OFF_ROLLBACK_NOT_BYTE_EXACT")
    return changed

def prepare(base:Path,out:Path):
    base=base.resolve(strict=True)
    out=out.resolve()
    if out.exists() or out.parent!=base.parent or out==base:
        raise ValueError("RED_OUTPUT_NOT_NEW_SIBLING")
    source,old,target=mapping(base)
    original=old[target].read_bytes()
    after=transform(original.decode("utf8")).encode("utf8")
    out_host=out.parent/OUTPUT_NAME
    if out_host.exists():raise ValueError("RED_OUTPUT_HOST_EXISTS")
    out_host.write_bytes(after)
    obj=copy.deepcopy(source)
    node=obj["tree"]
    for key in target:node=node[key]
    node["$path"]=OUTPUT_NAME
    out.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    _,new,next_target=mapping(out)
    if set(new)!=set(old) or next_target!=target:
        raise ValueError("RED_31_SCRIPT_MAP_CHANGED")
    if [k for k in old if new[k].read_bytes()!=old[k].read_bytes()]!=[target]:
        raise ValueError("RED_NOT_ONE_HOST_CHANGED")
    receipt={
        "feature_id":"GQ646_LOBBY_SAFE_SPAWN_20261117",
        "candidate_after":"GQ527_SIEGE_SELECTED31",
        "source_count":31,"existing_host_changed_only":True,
        "other_30_original_scripts_byte_exact":True,"off_exact_rollback":True,
        "base_host_sha256":sha(original),"selected_host_sha256":sha(after),
        "safe_floor_size":[154,2,156],"neutral_spawn":True,
        "match_teleport_authority_unchanged":True,"gameplay_score_store_remote_unchanged":True,
        "rojo_source_class_exact":"NOT_VERIFIED",
        "formal_rc_adopted":False,"studio_android_fun_owner":"NOT_TESTED"
    }
    (out.parent/RECEIPT_NAME).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("GQ646_PREP_ONE_HOST_OFF_BYTES_EXACT_OTHER30_PRESERVED")

def verify(base:Path,out:Path,place:Path):
    _,old,target=mapping(base)
    _,new,new_target=mapping(out)
    if set(old)!=set(new) or target!=new_target:raise ValueError("RED_SCRIPT_SET_DRIFT")
    expected=transform(old[target].read_text(encoding="utf8"))
    if new[target].read_text(encoding="utf8")!=expected:raise ValueError("RED_HOST_NOT_EXPECTED")
    if [key for key in old if old[key].read_bytes()!=new[key].read_bytes()]!=[target]:
        raise ValueError("RED_CHANGED_OTHER_SOURCES")
    embedded={}
    for item in ET.parse(place).getroot().iter("Item"):
        cls=item.attrib.get("class")
        if cls not in ("Script","ModuleScript","LocalScript"):continue
        props=item.find("Properties")
        if props is None:raise ValueError("RED_NO_PROPERTIES")
        name=props.findtext("string[@name='Name']")
        code=props.findtext("ProtectedString[@name='Source']")
        if code is None:code=props.findtext("string[@name='Source']")
        if not name or code is None or name in embedded:raise ValueError("RED_DUPLICATE_EMBED")
        embedded[name]=(cls,code.replace("\r\n","\n"))
    if len(embedded)!=31 or {k[-1] for k in new}!=set(embedded):
        raise ValueError("RED_PLACE_NOT_31")
    for key,path in new.items():
        cls=("Script" if path.name.endswith(".server.luau") else
             "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if embedded[key[-1]]!=(cls,path.read_text(encoding="utf8").replace("\r\n","\n")):
            raise ValueError("RED_CLASS_OR_SOURCE_"+key[-1])
    receipt_path=out.parent/RECEIPT_NAME
    receipt=json.loads(receipt_path.read_text())
    receipt.update(rojo_source_class_exact="31/31",place_bytes=place.stat().st_size,
                   place_sha256=sha(place.read_bytes()))
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("GQ646_REAL_ROJO31_ONLY_HOST_SAFE_LOBBY_SOURCE_EXACT_PASS",receipt["place_bytes"])

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("command",choices=("prepare","verify"))
    parser.add_argument("--base",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--place",type=Path)
    arg=parser.parse_args()
    if arg.command=="prepare":prepare(arg.base,arg.out)
    else:
        if arg.place is None:parser.error("--place needed")
        verify(arg.base,arg.out,arg.place)
