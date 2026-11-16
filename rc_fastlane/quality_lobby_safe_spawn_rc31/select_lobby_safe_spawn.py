#!/usr/bin/env python3
"""GQ648: ground the Studio lobby and return only non-active avatars to lobby.

The original V3 host creates role/defence stands and TEAM/BR portals, but no
lobby floor or reliable spawn. The same Host remains the only session authority.
The selected 31-source Place keeps all other 30 scripts byte-exact.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

TARGET = "EGGRUMBLE_LobbyCastleModesPreview"
OUTPUT_NAME = "GQ648_LOBBY_SAFE_SPAWN_HOST.server.luau"
RECEIPT = "GQ648_LOBBY_SAFE_SPAWN_RC31_RECEIPT.json"
TAG = "-- GQ648_LOBBY_SAFE_SPAWN_ONLY_20261117"
ANCHOR = "\nlocal function board("
PATCH = """
-- GQ648_LOBBY_SAFE_SPAWN_ONLY_20261117
-- Server-owned neutral lobby floor covers both portals, seven role stands,
-- five defence stands and the default spawn. The battle maps are +/-620 away.
local safeLobbyFloor=block(folder,"GQ648_LOBBY_SAFE_FLOOR",
 root+Vector3.new(0,-4,26),Vector3.new(118,4,144),Color3.fromRGB(73,87,94))
safeLobbyFloor.Material=Enum.Material.Slate
safeLobbyFloor.CanCollide=true
local safeLobbySpawn=Instance.new("SpawnLocation")
safeLobbySpawn.Name="GQ648_LOBBY_NEUTRAL_SPAWN"
safeLobbySpawn.Size=Vector3.new(10,1,10)
safeLobbySpawn.Position=root+Vector3.new(0,-1,-19)
safeLobbySpawn.Anchored=true
safeLobbySpawn.Neutral=true
safeLobbySpawn.AllowTeamChangeOnTouch=false
safeLobbySpawn.Duration=0
safeLobbySpawn.Parent=folder
-- Existing SpawnLocations can still be present; route freshly spawned avatars
-- to the protected lobby but never override an active TEAM or BR session.
local function gq648BindLobbyCharacter(player:Player)
 local function onCharacter(character:Model)
  task.defer(function()
   local rootPart=character:FindFirstChild("HumanoidRootPart")
    or character:WaitForChild("HumanoidRootPart",5)
   local humanoid=character:FindFirstChildOfClass("Humanoid")
    or character:WaitForChild("Humanoid",5)
   if player.Parent~=Players or player.Character~=character
    or not rootPart or not humanoid or humanoid.Health<=0 then return end
   local matchMode=joined[player.UserId]
   if matchMode and sessions[matchMode] then return end
   character:PivotTo(CFrame.new(root+Vector3.new(0,7,-19)))
  end)
 end
 player.CharacterAdded:Connect(onCharacter)
 if player.Character then task.defer(onCharacter,player.Character) end
end
Players.PlayerAdded:Connect(gq648BindLobbyCharacter)
for _,player in ipairs(Players:GetPlayers()) do
 gq648BindLobbyCharacter(player)
end
"""

def digest(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def mapping(project:Path):
    project=project.resolve(strict=True)
    obj=json.loads(project.read_text(encoding="utf8"))
    files={}
    def walk(node,route=()):
        for key,value in node.items():
            if key.startswith("$"):continue
            if not isinstance(value,dict):raise ValueError("RED_BAD_PROJECT_NODE")
            next_route=route+(key,)
            if "$path" in value:
                if set(value)!={"$path"} or next_route in files:
                    raise ValueError("RED_DUPLICATE_SOURCE")
                files[next_route]=(project.parent/value["$path"]).resolve(strict=True)
            else:walk(value,next_route)
    walk(obj["tree"])
    if len(files)!=31 or len({key[-1] for key in files})!=31:
        raise ValueError("RED_NOT_CANONICAL_31")
    hosts=[key for key in files if key[-1]==TARGET]
    if len(hosts)!=1:raise ValueError("RED_NOT_ONE_HOST")
    return obj,files,hosts[0]

def transform(before:str)->str:
    if TAG in before or "GQ648_LOBBY_SAFE_FLOOR" in before:
        raise ValueError("RED_SPAWN_PATCH_ALREADY_EXISTS")
    if before.count(ANCHOR)!=1:
        raise ValueError("RED_HOST_BLOCK_BOARD_ANCHOR_DRIFT")
    required=("local Players=game:GetService(\"Players\")",
              "local function block(",
              "local folder=Instance.new(\"Folder\")",
              "local sessions:",
              "local joined:")
    for token in required:
        if token not in before:raise ValueError("RED_HOST_REQUIRED_TOKEN_"+token)
    after=before.replace(ANCHOR,"\n"+PATCH+"\nlocal function board(",1)
    # Inverse is byte-for-byte exact, not only semantically equivalent.
    if after.replace("\n"+PATCH+"\nlocal function board(",ANCHOR,1)!=before:
        raise ValueError("RED_NONREVERSIBLE_HOST_PATCH")
    if after.count("GQ648_LOBBY_SAFE_FLOOR")!=1:
        raise ValueError("RED_DUPLICATED_LOBBY_FLOOR")
    if after.count("GQ648_LOBBY_NEUTRAL_SPAWN")!=1:
        raise ValueError("RED_DUPLICATED_LOBBY_SPAWN")
    if after.count("if matchMode and sessions[matchMode] then return end")!=1:
        raise ValueError("RED_SESSION_ISOLATION_GUARD")
    return after

def prepare(base:Path,out:Path):
    base,out=base.resolve(strict=True),out.resolve()
    if out.exists() or out.parent!=base.parent or base==out:
        raise ValueError("RED_NOT_NEW_SIBLING_OUTPUT")
    obj,old,target=mapping(base)
    before=old[target].read_bytes()
    selected=transform(before.decode("utf8")).encode("utf8")
    dest=out.parent/OUTPUT_NAME
    if dest.exists():raise ValueError("RED_OUTPUT_EXISTS")
    dest.write_bytes(selected)
    latest=copy.deepcopy(obj)
    route=latest["tree"]
    for key in target:route=route[key]
    route["$path"]=OUTPUT_NAME
    out.write_text(json.dumps(latest,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    _,new,host=mapping(out)
    changed=[k for k in old if old[k].read_bytes()!=new[k].read_bytes()]
    if set(old)!=set(new) or host!=target or changed!=[target]:
        raise ValueError("RED_NOT_EXACT_ONE_HOST")
    receipt={
      "feature_id":"GQ648_LOBBY_SAFE_SPAWN_ONLY_20261117",
      "one_modified_existing_script":TARGET,"runtime_scripts":31,
      "other_30_byte_exact":True,"off_inverse_host_byte_exact":True,
      "old_host_sha256":digest(before),"new_host_sha256":digest(selected),
      "floor_studs":[118,4,144],"neutral_spawn":True,
      "active_team_br_session_protected":True,
      "studio_runtime":"NOT_TESTED","android":"NOT_TESTED",
      "formal_rc_adopted":False,"rojo_source_class":"NOT_TESTED"}
    (out.parent/RECEIPT).write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print("GQ648_ONE_HOST_OTHER30_OFF_EXACT_PREP_PASS")

def verify(base:Path,out:Path,place:Path):
    _,old,target=mapping(base)
    _,new,host=mapping(out)
    if set(old)!=set(new) or host!=target:
        raise ValueError("RED_SOURCE_MAP_CHANGED")
    expected=transform(old[target].read_text(encoding="utf8"))
    if new[target].read_text(encoding="utf8")!=expected:
        raise ValueError("RED_SELECTED_HOST_DRIFT")
    if [k for k in old if old[k].read_bytes()!=new[k].read_bytes()]!=[target]:
        raise ValueError("RED_OTHER_30_CHANGED")
    embedded={}
    for item in ET.parse(place).getroot().iter("Item"):
        klass=item.attrib.get("class")
        if klass not in ("Script","LocalScript","ModuleScript"):continue
        properties=item.find("Properties")
        if properties is None:raise ValueError("RED_MISSING_ROJO_PROPERTIES")
        name=properties.findtext("string[@name='Name']")
        source=properties.findtext("ProtectedString[@name='Source']")
        if source is None:source=properties.findtext("string[@name='Source']")
        if not name or source is None or name in embedded:
            raise ValueError("RED_DUPLICATE_OR_MISSING_ROJO_SOURCE")
        embedded[name]=(klass,source.replace("\r\n","\n"))
    if len(embedded)!=31 or set(embedded)!={k[-1] for k in new}:
        raise ValueError("RED_ROJO_SCRIPT_COUNT")
    for key,path in new.items():
        klass=("Script" if path.name.endswith(".server.luau") else
               "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if embedded[key[-1]]!=(klass,path.read_text(encoding="utf8").replace("\r\n","\n")):
            raise ValueError("RED_ROJO_SOURCE_CLASS_"+key[-1])
    receipt=out.parent/RECEIPT
    proof=json.loads(receipt.read_text())
    if not proof["other_30_byte_exact"] or not proof["off_inverse_host_byte_exact"]:
        raise ValueError("RED_ROLLBACK_MISSING")
    proof.update(rojo_source_class="31/31",place_bytes=place.stat().st_size,
                 place_sha256=digest(place.read_bytes()))
    receipt.write_text(json.dumps(proof,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("GQ648_REAL_ROJO31_LOBBY_SPAWN_SOURCE_CLASS_OFF_EXACT_PASS",proof["place_bytes"])

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("mode",choices=("prepare","verify"))
    cli.add_argument("--base",required=True,type=Path)
    cli.add_argument("--out",required=True,type=Path)
    cli.add_argument("--place",type=Path)
    a=cli.parse_args()
    if a.mode=="prepare":prepare(a.base,a.out)
    else:
        if a.place is None:cli.error("--place is required for verify")
        verify(a.base,a.out,a.place)
