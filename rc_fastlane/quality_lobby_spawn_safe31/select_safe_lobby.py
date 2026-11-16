#!/usr/bin/env python3
"""GQ8 P0 lobby safety overlay: patch ONLY the selected current31 Host.

Reuses the existing authoritative Host + its spawn origin. The canonical Rojo
source selection retains 31 scripts and changes only the existing lobby Host.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "quality_bot_siege527_rc31"))
from select_original_siege_inline import mapping

HOST = "EGGRUMBLE_LobbyCastleModesPreview"
ANCHOR = 'local queueEpoch:{[string]:number}={TEAM=0,BATTLE_ROYALE=0}\n'
MARKER = "-- GQ8_LOBBY_SAFE_SPAWN_P0_VOID_REPAIR"
OUT_SOURCE = "GQ8_LOBBY_SAFE_HOST.server.luau"
RECEIPT = "GQ8_LOBBY_SAFE_SOURCE_RECEIPT.json"

SAFE_BLOCK = """-- GQ8_LOBBY_SAFE_SPAWN_P0_VOID_REPAIR
-- Canonical V3 has no Workspace SpawnLocation or lobby floor in its Rojo
-- project. Create one traversable safe surface, rather than falling at (0,4,0).
local lobbyFloor=Instance.new("Part")
lobbyFloor.Name="EGGRUMBLE_LobbySafetyFloor"
lobbyFloor.Anchored=true
lobbyFloor.CanCollide=true
lobbyFloor.Size=Vector3.new(120,4,150)
lobbyFloor.CFrame=CFrame.new(root+Vector3.new(0,-4,35))
lobbyFloor.Color=Color3.fromRGB(78,99,108)
lobbyFloor.Material=Enum.Material.Slate
lobbyFloor.Parent=folder
local lobbySpawn=Instance.new("SpawnLocation")
lobbySpawn.Name="EGGRUMBLE_LobbySafeSpawn"
lobbySpawn.Size=Vector3.new(12,1,12)
lobbySpawn.CFrame=CFrame.new(root+Vector3.new(0,-1.5,-22))
lobbySpawn.Anchored=true
lobbySpawn.CanCollide=true
lobbySpawn.Neutral=true
lobbySpawn.Enabled=true
lobbySpawn.Duration=0
lobbySpawn.Color=Color3.fromRGB(112,186,178)
lobbySpawn.Parent=workspace
-- Studio can create the first avatar before this Script starts. Rescue only
-- players outside live rounds; the original session owns arena spawn/respawn.
local function rescueToLobby(p:Player,character:Model)
 task.defer(function()
  local hum=character:FindFirstChildOfClass("Humanoid") or character:WaitForChild("Humanoid",5)
  local hip=character:FindFirstChild("HumanoidRootPart") or character:WaitForChild("HumanoidRootPart",5)
  if p.Parent~=Players or p.Character~=character or not hum or not hip then return end
  if not hum:IsA("Humanoid") or hum.Health<=0 then return end
  local activeMode=joined[p.UserId]
  if activeMode and sessions[activeMode] then return end
  (hip::BasePart).CFrame=CFrame.new(root+Vector3.new(0,6,-22))
 end)
end
local function attachLobbyRescue(p:Player)
 p.CharacterAdded:Connect(function(ch) rescueToLobby(p,ch) end)
 if p.Character then rescueToLobby(p,p.Character) end
end
Players.PlayerAdded:Connect(attachLobbyRescue)
for _,p in ipairs(Players:GetPlayers()) do attachLobbyRescue(p) end
-- GQ8_LOBBY_SAFE_SPAWN_P0_VOID_REPAIR_END
"""

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def transform(source: str) -> str:
    if source.count(MARKER) != 0:
        raise ValueError("RED_DUPLICATE_LOBBY_SAFETY")
    if source.count(ANCHOR) != 1 or source.count("local folder=Instance.new") != 1:
        raise ValueError("RED_ORIGINAL_LOBBY_HOST_ANCHOR")
    return source.replace(ANCHOR, ANCHOR + SAFE_BLOCK, 1)

def rollback(selected: str) -> str:
    if selected.count(SAFE_BLOCK) != 1:
        raise ValueError("RED_LOBBY_ROLLBACK_MARKER")
    return selected.replace(SAFE_BLOCK, "", 1)

def host_source_mapping(project: Path):
    project_obj, files, _bot = mapping(project)
    hosts = [k for k in files if k[-1] == HOST]
    if len(hosts) != 1:
        raise ValueError("RED_HOST_NOT_SINGLE")
    return project_obj, files, hosts[0]

def prepare(base: Path, out: Path):
    data, old, target = host_source_mapping(base)
    original = old[target].read_text(encoding="utf8")
    selected = transform(original)
    if rollback(selected) != original:
        raise ValueError("RED_ROLLBACK_DRIFT")
    out.parent.mkdir(parents=True, exist_ok=True)
    dest=out.parent / OUT_SOURCE
    if dest.exists() or out.exists():
        raise ValueError("RED_CANDIDATE_ALREADY_EXISTS")
    dest.write_text(selected, encoding="utf8")
    obj=copy.deepcopy(data)
    node=obj["tree"]
    for key in target: node=node[key]
    node["$path"]=OUT_SOURCE
    out.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    _, new, end_target=host_source_mapping(out)
    changed=[key for key in old if old[key].read_bytes()!=new[key].read_bytes()]
    if set(old)!=set(new) or end_target!=target or changed!=[target]:
        raise ValueError("RED_NOT_ONE_HOST_ONLY")
    record={
      "feature_id":"GQ8_LOBBY_SAFE_SPAWN_P0_VOID_REPAIR",
      "base_project":str(base),
      "selected_project":str(out),
      "source_count":31,
      "changed_script":HOST,
      "other_30_sources_byte_exact":True,
      "rollback_host_byte_exact":True,
      "original_host_sha256":sha(original.encode()),
      "selected_host_sha256":sha(selected.encode()),
      "studio_2client":"NOT_TESTED",
      "owner_fun":"NOT_TESTED",
      "formal_rc_adopted":False,
      "place_source_class_exact":"NOT_TESTED",
    }
    (out.parent/RECEIPT).write_text(json.dumps(record,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print("GQ8_LOBBY_SAFETY_ONE_HOST_OTHER30_OFF_EXACT_PASS")

def verify(base: Path,out:Path,place:Path):
    _,old,old_target=host_source_mapping(base)
    _,new,target=host_source_mapping(out)
    if target!=old_target or set(old)!=set(new):
        raise ValueError("RED_HOST_ROUTING_DRIFT")
    prev=old[target].read_text(encoding="utf8")
    expected=transform(prev)
    if new[target].read_text(encoding="utf8")!=expected or rollback(expected)!=prev:
        raise ValueError("RED_HOST_BAD_SOURCE_OR_ROLLBACK")
    if [key for key in old if old[key].read_bytes()!=new[key].read_bytes()] != [target]:
        raise ValueError("RED_OTHER30_CHANGED")
    embedded={}
    for item in ET.parse(place).getroot().iter("Item"):
        kind=item.attrib.get("class")
        if kind not in ("Script","ModuleScript","LocalScript"): continue
        properties=item.find("Properties")
        if properties is None: raise ValueError("RED_MISSING_PROPERTIES")
        name=properties.findtext("string[@name='Name']")
        value=properties.findtext("ProtectedString[@name='Source']")
        if value is None:value=properties.findtext("string[@name='Source']")
        if not name or value is None or name in embedded:
            raise ValueError("RED_ROJO_SOURCE_OR_DUPLICATE")
        embedded[name]=(kind,value.replace("\r\n","\n"))
    if len(embedded)!=31 or set(embedded)!={key[-1] for key in new}:
        raise ValueError("RED_ROJO31_SOURCE_COUNT")
    for key,path in new.items():
        kind=("Script" if path.name.endswith(".server.luau") else
              "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if embedded[key[-1]]!=(kind,path.read_text(encoding="utf8").replace("\r\n","\n")):
            raise ValueError("RED_ROJO_MISMATCH_"+key[-1])
    receipt_path=out.parent/RECEIPT
    receipt=json.loads(receipt_path.read_text(encoding="utf8"))
    if not receipt["other_30_sources_byte_exact"] or not receipt["rollback_host_byte_exact"]:
        raise ValueError("RED_SOURCE_LOCK_MISMATCH")
    receipt.update(place_source_class_exact="31/31",
                   place_bytes=place.stat().st_size,
                   place_sha256=sha(place.read_bytes()))
    receipt_path.write_text(json.dumps(receipt,indent=2,ensure_ascii=False,sort_keys=True)+"\n")
    print("GQ8_LOBBY_SAFETY_ACTUAL_ROJO31_SOURCE_CLASS_PASS",receipt["place_bytes"])

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("action",choices=("prepare","verify"))
    cli.add_argument("--base",required=True,type=Path)
    cli.add_argument("--out",required=True,type=Path)
    cli.add_argument("--place",type=Path)
    a=cli.parse_args()
    if a.action=="prepare": prepare(a.base,a.out)
    else:
        if not a.place:cli.error("--place required")
        verify(a.base,a.out,a.place)
