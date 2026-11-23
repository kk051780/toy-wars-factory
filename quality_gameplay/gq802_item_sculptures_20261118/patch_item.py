#!/usr/bin/env python3
"""Existing FieldItemPickups silhouette-only overlay; real original31 source pinned.

Three original items keep their original gameplay, cooldowns and ownership.
The new visual meshes never affect player physics, querying or pickup tokens.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path

FEATURE="GQ802_ITEM_EXISTING_3D_IDENTITY_20261118"
MARKER="GQ802_ITEM_EXISTING_3D_IDENTITY_20261118"
BEFORE_HELPER=""" local serial=0
"""
HELPER=""" -- GQ802_ITEM_EXISTING_3D_IDENTITY_20261118: visual only, 3 pieces per item.
 -- Original server pickup, session, score and cooldown authorities stay intact.
 local function makeItemSculpture(anchor:BasePart,kind:string,accent:Color3):{BasePart}
  local pieces:{BasePart}={}
  local ivory=Color3.fromRGB(246,251,245)
  local ink=Color3.fromRGB(64,66,113)
  local function piece(name:string,sz:Vector3,offset:CFrame,tint:Color3,wedge:boolean)
   local v=Instance.new(wedge and "WedgePart" or "Part")
   v.Name="ItemArt_"..name
   v.Size=sz
   v.Color=tint
   v.Material=Enum.Material.SmoothPlastic
   v.Anchored=true
   v.CanCollide=false;v.CanTouch=false;v.CanQuery=false
   v.CFrame=anchor.CFrame*offset
   v.Parent=anchor
   table.insert(pieces,v)
  end
  if kind=="HEAL" then
   -- White medical cross and capped flask silhouette.
   piece("ReliefCrossV",Vector3.new(.30,1.05,.24),CFrame.new(0,.05,-1.15),ivory,false)
   piece("ReliefCrossH",Vector3.new(1.05,.30,.24),CFrame.new(0,.05,-1.25),ivory,false)
   piece("FlaskCap",Vector3.new(.68,.46,.68),CFrame.new(0,1.16,0),accent,false)
  elseif kind=="DASH" then
   -- Pair of angled feather-wings, instantly distinct from a healing flask.
   piece("FeatherLeft",Vector3.new(1.24,.25,.63),
    CFrame.new(-1.07,.25,0)*CFrame.Angles(0,0,math.rad(-25)),ivory,true)
   piece("FeatherRight",Vector3.new(1.24,.25,.63),
    CFrame.new(1.07,.25,0)*CFrame.Angles(0,0,math.rad(25)),ivory,true)
   piece("FlightTip",Vector3.new(.38,.98,.27),CFrame.new(0,.14,-1.08),ink,false)
  elseif kind=="SHIELD" then
   -- Raised diamond/crest, readable without purple color discrimination.
   piece("Crest",Vector3.new(1.18,1.18,.27),
    CFrame.new(0,.07,-1.10)*CFrame.Angles(0,0,math.rad(45)),ivory,false)
   piece("RimLeft",Vector3.new(.30,1.15,.30),
    CFrame.new(-.75,0,-.72)*CFrame.Angles(0,0,math.rad(-25)),ink,true)
   piece("RimRight",Vector3.new(.30,1.15,.30),
    CFrame.new(.75,0,-.72)*CFrame.Angles(0,0,math.rad(25)),ink,true)
  else
   error("RED_GQ802_UNKNOWN_ITEM_TYPE")
  end
  return pieces
 end
"""
OLD_ITEM="""  part.Material=Enum.Material.Neon;part.Color=def.color
  part.Anchored=true;part.CanCollide=false;part.Position=pos
  part.Parent=folder
"""
NEW_ITEM="""  part.Material=Enum.Material.SmoothPlastic;part.Color=def.color
  part.Anchored=true;part.CanCollide=false;part.Position=pos
  part.Parent=folder
  local itemArt=makeItemSculpture(part,kind,def.color)
"""
OLD_HIDE="""   part.Transparency=1;part.CanQuery=false
"""
NEW_HIDE="""   part.Transparency=1;part.CanQuery=false
   for _,v in ipairs(itemArt) do v.Transparency=1 end
"""
OLD_SHOW="""    part.Transparency=0;part.CanQuery=true;prompt.Enabled=true
"""
NEW_SHOW="""    part.Transparency=0;part.CanQuery=true;prompt.Enabled=true
    for _,v in ipairs(itemArt) do v.Transparency=0 end
"""
GAMEPLAY_ANCHORS=(
    'local kind=({"HEAL","DASH","SHIELD"})[(i-1)%3+1]',
    'local key=tostring(player.UserId)..":"..kind',
    'consumed[id]=true;lastUse[key]=now',
    'prompt.Enabled=false',
    'if isV3Match and not interactionGuard.allow(player,part,"拾う",part.Name) then return end',
    'session.itemStop=function()',
    'cancelBuffIfCarrier(player,5,restoreSpeed)',
    'if not healUseful(kind,hum.Health,hum.MaxHealth) then return end',
)

def git_blob_sha(data:bytes):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def apply(original:bytes)->bytes:
    text=original.decode("utf-8")
    if MARKER in text:
        raise ValueError("RED_GQ802_DOUBLE_PATCH")
    for snippet in GAMEPLAY_ANCHORS:
        if snippet not in text:
            raise ValueError("RED_GQ802_OFFICIAL_ITEM_SOURCE_DRIFT_"+snippet)
    for old in (BEFORE_HELPER,OLD_ITEM,OLD_HIDE,OLD_SHOW):
        if text.count(old)!=1:
            raise ValueError("RED_GQ802_ITEM_VISUAL_ANCHOR_CHANGED_"+old.strip()[:25])
    modified=(text.replace(BEFORE_HELPER,HELPER+BEFORE_HELPER,1)
        .replace(OLD_ITEM,NEW_ITEM,1)
        .replace(OLD_HIDE,NEW_HIDE,1)
        .replace(OLD_SHOW,NEW_SHOW,1)).encode()
    if inverse(modified)!=original:
        raise ValueError("RED_GQ802_INVERSE_NOT_EXACT")
    return modified

def inverse(selected:bytes)->bytes:
    body=selected.decode("utf-8")
    if body.count(HELPER)!=1 or body.count(NEW_ITEM)!=1 or body.count(NEW_HIDE)!=1 or body.count(NEW_SHOW)!=1:
        raise ValueError("RED_GQ802_SELECTED_ITEM_DRIFT")
    original=(body.replace(NEW_SHOW,OLD_SHOW,1).replace(NEW_HIDE,OLD_HIDE,1)
        .replace(NEW_ITEM,OLD_ITEM,1).replace(HELPER,"",1)).encode()
    if MARKER.encode() in original:
        raise ValueError("RED_GQ802_ROLLBACK_MARKER")
    return original

def native_harness(selected:bytes)->str:
    src=selected.decode("utf-8")
    assert src.count(HELPER)==src.count(NEW_ITEM)==src.count(NEW_HIDE)==src.count(NEW_SHOW)==1
    vm=r'''local classes={}
local Instance={new=function(kind)
  assert(kind=="Part" or kind=="WedgePart")
  local p={ClassName=kind}
  table.insert(classes,p)
  return p
end}
local Color3={fromRGB=function(r,g,b) return {R=r,G=g,B=b} end}
local Enum={Material={SmoothPlastic="SmoothPlastic"}}
local Vector3={new=function(x,y,z) return {X=x,Y=y,Z=z} end}
local cfmt={}
cfmt.__mul=function(a,b) return setmetatable({ok=true},cfmt) end
local CFrame={
 new=function(x,y,z) return setmetatable({ok=true},cfmt) end,
 Angles=function(x,y,z) return setmetatable({ok=true},cfmt) end,
}
local root={CFrame=CFrame.new(0,0,0)}
local accent=Color3.fromRGB(120,200,245)
'''
    vm+=HELPER
    vm+=r'''
local names={}
for _,kind in ipairs({"HEAL","DASH","SHIELD"}) do
 local parts=makeItemSculpture(root,kind,accent)
 assert(#parts==3,"exactly 3 decoration Parts per original item")
 local wings=0
 for _,v in ipairs(parts) do
  assert(v.Parent==root and v.Anchored==true)
  assert(v.CanCollide==false and v.CanTouch==false and v.CanQuery==false)
  assert(v.Material==Enum.Material.SmoothPlastic and v.CFrame.ok)
  assert(v.Name:sub(1,8)=="ItemArt_")
  assert(not names[v.Name],"unique silhouettes for each kind")
  names[v.Name]=true
  if v.ClassName=="WedgePart" then wings+=1 end
 end
 if kind=="HEAL" then assert(wings==0) end
 if kind=="DASH" then assert(wings==2) end
 if kind=="SHIELD" then assert(wings==2) end
 -- Duplicate of the exact selected source's visibility statements below:
 local itemArt=parts
'''
    vm+=NEW_HIDE
    vm+=r'''
 for _,v in ipairs(parts) do assert(v.Transparency==1) end
'''
    vm+=NEW_SHOW
    vm+=r'''
 for _,v in ipairs(parts) do assert(v.Transparency==0) end
end
assert(#classes==9,"3 decoration parts x 3 items = 9 total")
local ok=pcall(function() makeItemSculpture(root,"CHEAT",accent) end)
assert(not ok,"unknown item must not mint visual or new capability")
print("GQ802_REAL_ITEM_ART_NATIVE_VM_PASS_3_TYPES_9_PIECES_HIDE_RESPAWN")
'''
    # The exact source hide/show includes references to part, prompt; mock them.
    vm=vm.replace("local names={}",'local part={Transparency=0,CanQuery=true}\nlocal prompt={Enabled=true}\nlocal names={}',1)
    return vm

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--rollback",action="store_true")
    ap.add_argument("--harness",type=Path)
    args=ap.parse_args()
    content=args.source.read_bytes()
    new=inverse(content) if args.rollback else apply(content)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(new)
    if args.harness:
        args.harness.write_text(native_harness(new))
    print(FEATURE,"OFF" if args.rollback else "ON","original_git_blob",git_blob_sha(content),
          "new_git_blob",git_blob_sha(new), "bytes",len(new))

if __name__=="__main__":
    main()
