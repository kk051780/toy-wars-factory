#!/usr/bin/env python3
"""GQ LOBBY SAFE SPAWN: one existing EGGRUMBLE V3 Host source, no second Game.

The V3 Studio Host derives an origin from any existing SpawnLocation or (0,4,0),
but does not guarantee a traversable lobby floor or a lobby spawn. The player
may appear in the void, die before interacting, or respawn away from the gates.

This adapter runs AFTER canonical GQ527 and changes exactly ONE existing Host
Script. It creates a private Studio-only platform and neutral SpawnLocation
within the existing lobby folder and re-centers only non-active participants.
No new script, matchmaking authority, Remote, combat, egg or store is added.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET

HOST = "EGGRUMBLE_LobbyCastleModesPreview"
MARK = "GQ_LOBBY_SAFE_SPAWN_20261117"
OUTPUT = "GQ_LOBBY_SAFE_SPAWN_FINAL.server.luau"
RECEIPT = "GQ_LOBBY_SAFE_SPAWN_RC31_RECEIPT.json"

BEFORE_ROOT = 'local root=spawn and spawn.Position or Vector3.new(0,4,0)'
BEFORE_FOLDER = 'local folder=Instance.new("Folder");folder.Name="EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW";folder.Parent=workspace'
BEFORE_QUEUE = 'local queueEpoch:{[string]:number}={TEAM=0,BATTLE_ROYALE=0}'

PLATFORM = r"""
-- GQ_LOBBY_SAFE_SPAWN_20261117: privately playable Studio lobby, not a battle arena.
-- The platform covers spawn, two mode portals, seven role stands and defense pads.
-- TEAM and BR castles begin far outside this platform; no field geometry changes.
local lobbyFloor=Instance.new("Part")
lobbyFloor.Name="GQ_LOBBY_SAFE_FLOOR"
lobbyFloor.Size=Vector3.new(190,6,180)
lobbyFloor.Position=root+Vector3.new(0,-4,40)
lobbyFloor.Anchored=true
lobbyFloor.CanCollide=true
lobbyFloor.Material=Enum.Material.Grass
lobbyFloor.Color=Color3.fromRGB(76,126,85)
lobbyFloor.Parent=folder

local lobbySpawn=Instance.new("SpawnLocation")
lobbySpawn.Name="GQ_LOBBY_NEUTRAL_SPAWN"
lobbySpawn.Size=Vector3.new(12,1,12)
lobbySpawn.Position=root+Vector3.new(0,1,0)
lobbySpawn.Anchored=true
lobbySpawn.CanCollide=true
lobbySpawn.Neutral=true
lobbySpawn.AllowTeamChangeOnTouch=false
lobbySpawn.Duration=0
lobbySpawn.Parent=folder
""".strip("\n")

BIND = r"""
-- Do not move an ACTIVE TEAM/BR participant from their actual battle spawn.
-- A lobby-only participant can arrive even when the base Place had no SpawnLocation.
local function gqBindLobbyArrival(player:Player)
 local function onLobbyCharacter(character:Model)
  task.defer(function()
   if player.Parent~=Players or player.Character~=character then return end
   local mode=joined[player.UserId]
   if mode and sessions[mode] then return end
   local part=character:FindFirstChild("HumanoidRootPart") or character:WaitForChild("HumanoidRootPart",5)
   local humanoid=character:FindFirstChildOfClass("Humanoid")
   if not part or not humanoid or humanoid.Health<=0 then return end
   if player.Parent~=Players or player.Character~=character then return end
   mode=joined[player.UserId]
   if mode and sessions[mode] then return end
   character:PivotTo(CFrame.new(lobbySpawn.Position+Vector3.new(0,5,0)))
  end)
 end
 player.RespawnLocation=lobbySpawn
 player.CharacterAdded:Connect(onLobbyCharacter)
 if player.Character then onLobbyCharacter(player.Character) end
end
Players.PlayerAdded:Connect(gqBindLobbyArrival)
for _,gqPlayer in ipairs(Players:GetPlayers()) do
 gqBindLobbyArrival(gqPlayer)
end
""".strip("\n")

def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def mapping(project:Path):
    project=project.resolve(strict=True)
    obj=json.loads(project.read_text(encoding="utf-8"))
    files={}
    def walk(node,route=()):
        for key,value in node.items():
            if key.startswith("$"):continue
            if not isinstance(value,dict):raise ValueError("RED_BAD_PROJECT_NODE")
            p=route+(key,)
            if "$path" in value:
                if set(value)!={"$path"} or p in files:
                    raise ValueError("RED_BAD_SOURCE_NODE")
                files[p]=(project.parent/value["$path"]).resolve(strict=True)
            else:walk(value,p)
    walk(obj["tree"])
    if len(files)!=31 or len({x[-1] for x in files})!=31:
        raise ValueError("RED_NOT_31_SINGLETON_SOURCES")
    target=[key for key in files if key[-1]==HOST]
    if len(target)!=1 or target[0][0]!="ServerScriptService":
        raise ValueError("RED_MISSING_SINGLE_EXISTING_HOST")
    return obj,files,target[0]

def transform(before:str)->str:
    if MARK in before:raise ValueError("RED_DUPLICATE_GQ_LOBBY_PATCH")
    for required in (BEFORE_ROOT,BEFORE_FOLDER,BEFORE_QUEUE,
                     'joinQueue("TEAM",p)', 'joinQueue("BATTLE_ROYALE",p)',
                     'SevenRoleCombat.roleOrder()'):
        if before.count(required)!=1:
            raise ValueError("RED_LOBBY_HOST_ANCHOR_DRIFT_"+required[:24])
    after=before.replace(BEFORE_FOLDER,BEFORE_FOLDER+"\n"+PLATFORM,1)
    after=after.replace(BEFORE_QUEUE,BEFORE_QUEUE+"\n"+BIND,1)
    if after.replace(BEFORE_QUEUE+"\n"+BIND,BEFORE_QUEUE,1).replace(
            BEFORE_FOLDER+"\n"+PLATFORM,BEFORE_FOLDER,1)!=before:
        raise ValueError("RED_ROLLBACK_NOT_EXACT")
    if after.count(MARK)!=1 or after.count('Players.PlayerAdded:Connect(gqBindLobbyArrival)')!=1:
        raise ValueError("RED_DUPLICATE_LOBBY_HOOK")
    return after

def prepare(base:Path,out:Path):
    base=base.resolve(strict=True);out=out.resolve()
    if out.exists() or base==out or out.parent!=base.parent:
        raise ValueError("RED_NOT_NEW_SIBLING_PROJECT")
    obj,old,route=mapping(base)
    original=old[route].read_bytes()
    updated=transform(original.decode("utf-8")).encode("utf-8")
    newsource=out.parent/OUTPUT
    if newsource.exists():raise ValueError("RED_HOST_OUTPUT_EXISTS")
    newsource.write_bytes(updated)
    selected=copy.deepcopy(obj)
    node=selected["tree"]
    for p in route:node=node[p]
    node["$path"]=OUTPUT
    out.write_text(json.dumps(selected,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,new,newroute=mapping(out)
    changed=[k for k in old if old[k].read_bytes()!=new[k].read_bytes()]
    if set(old)!=set(new) or newroute!=route or changed!=[route]:
        raise ValueError("RED_OTHER_30_RUNTIME_SOURCES_CHANGED")
    evidence={
      "feature_id":MARK,"base_script_count":31,"new_script_count":0,
      "changed_existing_host_only":True,"other30_script_bytes_identical":True,
      "rollback_exact":True,"before_sha256":sha(original),
      "after_sha256":sha(updated),"root_covers_existing_or_missing_spawn":True,
      "has_collision_floor":True,"neutral_spawn_created":True,
      "active_match_teleport_guard":True,"owner_studio_retest":"NOT_TESTED",
      "android":"NOT_TESTED","formal_rc_adopted":False,
      "rojo_source_class_exact":"NOT_TESTED"}
    (out.parent/RECEIPT).write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n")
    print("GQ_LOBBY_SAFE_SPAWN_HOST_ONLY_30_OTHER_EXACT_OFF_REVERSIBLE_PASS")

def verify(base:Path,out:Path,place:Path):
    _,old,route=mapping(base)
    _,new,newroute=mapping(out)
    if set(old)!=set(new) or route!=newroute:raise ValueError("RED_SOURCE_MAP_CHANGED")
    if [k for k in old if old[k].read_bytes()!=new[k].read_bytes()]!=[route]:
        raise ValueError("RED_CHANGED_MORE_THAN_ONE_SCRIPT")
    if new[route].read_text()!=transform(old[route].read_text()):
        raise ValueError("RED_PATCH_NOT_SOURCE_EXACT")
    embedded={}
    for item in ET.parse(place).getroot().iter("Item"):
        cls=item.attrib.get("class")
        if cls not in ("Script","ModuleScript","LocalScript"):continue
        props=item.find("Properties")
        if props is None:raise ValueError("RED_ROJO_PROPERTIES")
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:source=props.findtext("string[@name='Source']")
        if not name or source is None or name in embedded:
            raise ValueError("RED_ROJO_DUPLICATE_OR_MISSING_SOURCE")
        embedded[name]=(cls,source.replace("\r\n","\n"))
    if len(embedded)!=31:raise ValueError("RED_NOT_TRUE_ROJO31")
    for route,path in new.items():
        cls=("Script" if path.name.endswith(".server.luau") else
             "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if embedded.get(route[-1])!=(cls,path.read_text().replace("\r\n","\n")):
            raise ValueError("RED_ROJO_CLASS_SOURCE_"+route[-1])
    receipt_path=out.parent/RECEIPT
    receipt=json.loads(receipt_path.read_text())
    receipt.update(rojo_source_class_exact="31/31",
                   place_bytes=place.stat().st_size,
                   place_sha256=sha(place.read_bytes()))
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("GQ_LOBBY_SAFE_SPAWN_RC31_ROJO_SOURCE_EXACT_PASS",receipt["place_bytes"])

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("prepare","verify"))
    p.add_argument("--base",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--place",type=Path)
    a=p.parse_args()
    if a.action=="prepare":prepare(a.base,a.out)
    else:
        if a.place is None:p.error("verify needs --place")
        verify(a.base,a.out,a.place)
