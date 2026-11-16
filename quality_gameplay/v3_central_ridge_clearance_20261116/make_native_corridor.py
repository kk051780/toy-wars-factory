#!/usr/bin/env python3
"""Compile and EXECUTE the real original TEAM ridge Lua snippets in native Luau.

Source geometry behavior only: NOT Roblox engine physics/Pathfinding/Prompt certification.
Inputs are immutable original #482 host, #504 original34 composed host, GQ520
private34 host and original #482 Item source. No author source is written.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from patch_ridge import OLD, NEW, ORIGINAL_GIT_BLOB, git_blob, patch_author_host

SOURCE_HEADER = r'''
-- Native Luau source-extracted spatial safety test. Roblox engine NOT simulated.
local Vector3={}
local vecmt={}
function Vector3.new(x,y,z)
 return setmetatable({X=x,Y=y,Z=z},vecmt)
end
vecmt.__add=function(a,b)
 return Vector3.new(a.X+b.X,a.Y+b.Y,a.Z+b.Z)
end
local Color3={fromRGB=function(r,g,b) return {r=r,g=g,b=b} end}
local Enum={Material={Slate="Slate"}}
local root=Vector3.new(0,0,0)
local session={world={}}
local function makeBlock(parts,world,name,pos,size,color)
 assert(world==session.world)
 local p={Name=name,Position=pos,Size=size,Color=color,Anchored=true,CanCollide=true}
 table.insert(parts,p)
 return p
end
'''

SOURCE_FOOTER = r'''
local old=oldWorld()
local fresh=newWorld()
assert(#old==1 and #fresh==2,"original one ridge must become two shoulders")
assert(old[1].Name=="CentralRidge")
assert(old[1].Size.X==54 and old[1].Size.Y==34 and old[1].Size.Z==190)
assert(old[1].Position.X==-620 and old[1].Position.Y==15 and old[1].Position.Z==475)
local left,right=fresh[1],fresh[2]
assert(left.Name=="CentralRidge" and right.Name=="CentralRidgeRight")
assert(left.Size.X==15 and right.Size.X==15)
assert(left.Size.Y==34 and right.Size.Y==34 and left.Size.Z==190 and right.Size.Z==190)
assert(left.Position.X==-639.5 and right.Position.X==-600.5)
assert(left.Position.Z==old[1].Position.Z and right.Position.Z==old[1].Position.Z)
assert(left.Material=="Slate" and right.Material=="Slate")
assert(left.CanCollide and right.CanCollide and left.Anchored and right.Anchored)

local item=Vector3.new(-620,1.8,470)
local function occupies(p,x,y,z,r)
 return math.abs(x-p.Position.X)<=p.Size.X/2+r
    and math.abs(y-p.Position.Y)<=p.Size.Y/2+r
    and math.abs(z-p.Position.Z)<=p.Size.Z/2+r
end
local function isBlocked(parts,x,y,z,r)
 for _,p in ipairs(parts) do
  if p.CanCollide and occupies(p,x,y,z,r) then return true end
 end
 return false
end
assert(isBlocked(old,item.X,item.Y,item.Z,1.1),"old SHIELD must be embedded")
assert(not isBlocked(fresh,item.X,item.Y,item.Z,1.1),"new SHIELD must be in free space")
-- Character capsule projection r=2; follow the full central Z approach, both directions.
local previousBlockCount=0
for z=360,590,2 do
 local blockedBefore=isBlocked(old,item.X,item.Y,z,2)
 local blockedAfter=isBlocked(fresh,item.X,item.Y,z,2)
 if blockedBefore then previousBlockCount+=1 end
 assert(not blockedAfter,"new corridor blocked at Z "..tostring(z))
end
assert(previousBlockCount>80,"original authored center corridor must be blocked")
-- Closed stone shoulders must remain real obstacles; not solve by deleting the ridge.
for z=400,550,30 do
 assert(isBlocked(fresh,-639.5,1.8,z,2),"left shoulder loses collision")
 assert(isBlocked(fresh,-600.5,1.8,z,2),"right shoulder loses collision")
end
-- Strict segment-vs-AABB slab intersection for the 1.1-stud item/line-of-sight query.
local function hitsSegment(p,ax,ay,az,bx,by,bz,padding)
 local low,high=0,1
 for _,axis in ipairs({
   {a=ax,b=bx,c=p.Position.X,h=p.Size.X/2},
   {a=ay,b=by,c=p.Position.Y,h=p.Size.Y/2},
   {a=az,b=bz,c=p.Position.Z,h=p.Size.Z/2}
 }) do
  local mn=axis.c-axis.h-padding
  local mx=axis.c+axis.h+padding
  local delta=axis.b-axis.a
  if math.abs(delta)<1e-7 then
   if axis.a<mn or axis.a>mx then return false end
  else
   local t1=(mn-axis.a)/delta
   local t2=(mx-axis.a)/delta
   if t1>t2 then t1,t2=t2,t1 end
   low=math.max(low,t1)
   high=math.min(high,t2)
   if low>high then return false end
  end
 end
 return true
end
local function lineBlocked(parts,x,z,margin)
 for _,p in ipairs(parts) do
  if hitsSegment(p,x,1.8,z,item.X,item.Y,item.Z,margin) then return true end
 end
 return false
end
-- At Z=465 the center pick-up requires LOS. The original solid block blocks
-- even a close approach; new 24-wide corridor exposes LOS.
assert(lineBlocked(old,-620,465,0),"old LOS expected to be occluded")
for _,z in ipairs({370,390,430,465,505,550,580}) do
 assert(not lineBlocked(fresh,-620,z,0),"new center corridor LOS blocked at Z "..z)
end
-- 8.9 studs of humanoid r=2 + SHIELD r=1.1 combined clearance each side.
local edgeClearance=12-2-1.1
assert(edgeClearance>8.0)
print("GQ520_ORIGINAL_RIDGE_REAL_LUAU_VM_PASS before_one after_two corridor_24 shield_x-620_z470")
print("GQ520_LOS_PATH_NEGATIVE_PASS old_blocked after_clear shoulders_collidable margin="..edgeClearance)
'''

def source_readback(original_host: str, source34_host: str,
                    patched34_host: str, items: str) -> tuple[str,str]:
    if git_blob(original_host)!=ORIGINAL_GIT_BLOB:
        raise ValueError("RED: original host immutable source blob changed")
    if original_host.count(OLD)!=1:
        raise ValueError("RED: original source ridge not one exact block")
    # The real ITEM author decides center route, not a made-up test geometry.
    if ('{x=0,z=470,kind="SHIELD"}' not in items
        or 'xCenter=if session.mode=="TEAM" then -620 else 620' not in items
        or 'table.insert(points,origin+Vector3.new(xCenter+site.x,1.8,site.z))' not in items):
        raise ValueError("RED: original item real world position drift")
    if source34_host.count(OLD)!=1 or patched34_host.count(NEW)!=1:
        raise ValueError("RED: original34 / patched34 terrain source not unique")
    if patched34_host.replace(NEW,OLD)!=source34_host:
        raise ValueError("RED: unrelated Game/AI/ITEM/Boss/ART/Round/Score source changed")
    if patch_author_host(original_host,items).count(NEW)!=1:
        raise ValueError("RED: original generator does not reproduce new terrain")
    return OLD,NEW

def make_vm(original: Path, source34:Path, patched34:Path,
            items:Path, out:Path)->None:
    for x in (original,source34,patched34,items):
        if not x.is_file():
            raise ValueError("RED: missing source: "+str(x))
    orig,changed=source_readback(
        original.read_text(encoding="utf-8"),
        source34.read_text(encoding="utf-8"),
        patched34.read_text(encoding="utf-8"),
        items.read_text(encoding="utf-8"))
    def scope(name,script):
        return ("local function "+name+"()\n"
         " local spawned={}\n"
         " local function block(world,label,pos,size,color)\n"
         "  return makeBlock(spawned,world,label,pos,size,color)\n"
         " end\n"+script+"\n return spawned\nend\n")
    body=SOURCE_HEADER+scope("oldWorld",orig)+scope("newWorld",changed)+SOURCE_FOOTER
    if out.resolve() in (x.resolve() for x in (original,source34,patched34,items)):
        raise ValueError("RED: refuse write into original source")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(body,encoding="utf-8")
    print("GQ520_NATIVE_CORRIDOR_EXACT_SOURCE_VM_GENERATED",len(body))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("original","source34","patched34","items","out"):
        p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args()
    make_vm(a.original,a.source34,a.patched34,a.items,a.out)

if __name__=="__main__":main()
