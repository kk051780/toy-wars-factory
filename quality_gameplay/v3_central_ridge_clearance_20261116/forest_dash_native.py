#!/usr/bin/env python3
"""Run REAL #482 authored forest loop and original ITEM FIXED list in native Luau.

Replaces only one authored expression in a private copy. Not Roblox physics.
Companion to #520 native ridge VM, deliberately avoids #523 egg/other author work.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from patch_ridge import ORIGINAL_GIT_BLOB, OLD as RIDGE_OLD, NEW as RIDGE_NEW, git_blob
from forest_dash_overlay import OLD_FOREST,NEW_FOREST,patch_forest

VEC=r'''
local Vector3={}
local vecMt={}
function Vector3.new(x,y,z) return setmetatable({X=x,Y=y,Z=z},vecMt) end
vecMt.__add=function(a,b) return Vector3.new(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end
local Color3={fromRGB=function(r,g,b) return {r=r,g=g,b=b} end}
local Enum={Material={Grass="Grass",Slate="Slate"}}
local root=Vector3.new(0,0,0)
local session={world={}}
local function createPart(collection,parent,name,pos,size,color)
 assert(parent==session.world)
 local p={Name=name,Position=pos,Size=size,Color=color,Anchored=true,CanCollide=true}
 table.insert(collection,p)
 return p
end
'''

TEST=r'''
local treesOld=createOldForest()
local treesNew=createNewForest()
local ridgeOld=createOldRidge()
local ridgeNew=createNewRidge()
assert(#treesOld==7 and #treesNew==7)
assert(#ridgeOld==1 and #ridgeNew==2)
for n=1,7 do
 local a,b=treesOld[n],treesNew[n]
 assert(a.Name=="ForestAmbushCover_"..n and b.Name==a.Name)
 assert(a.Size.X==7 and a.Size.Y==24 and a.Size.Z==7)
 assert(a.Anchored and b.Anchored and a.CanCollide and b.CanCollide)
 assert(a.Position.X==b.Position.X and a.Position.Y==b.Position.Y)
 if n==1 then
  assert(a.Position.X==-762 and a.Position.Y==11 and a.Position.Z==470)
  assert(b.Position.X==-762 and b.Position.Z==488)
 else
  assert(b.Position.Z==a.Position.Z,"non-DASH tree moved "..n)
 end
end
local teamSites=itemPositions("TEAM")
local brSites=itemPositions("BATTLE_ROYALE")
assert(#teamSites==9 and #brSites==9)
local function intersects(p,at,r)
 return math.abs(p.Position.X-at.X)<=p.Size.X/2+r
  and math.abs(p.Position.Y-at.Y)<=p.Size.Y/2+r
  and math.abs(p.Position.Z-at.Z)<=p.Size.Z/2+r
end
local function collides(parts,site,r)
 for _,p in ipairs(parts) do
  if p.CanCollide and intersects(p,site,r) then return p.Name end
 end
 return nil
end
local function overlaps(trees,ridge,sites)
 local out={}
 for k,site in ipairs(sites) do
  local tree=collides(trees,site,1.1)
  local mountain=collides(ridge,site,1.1)
  if tree or mountain then
   out[#out+1]=k
  end
 end
 return out
end
-- Original ITEM source FIXED ordering: index 5 DASH at (-760,470), 6 SHIELD center.
assert(teamSites[5].X==-760 and teamSites[5].Y==1.8 and teamSites[5].Z==470)
assert(teamSites[6].X==-620 and teamSites[6].Z==470)
local original=overlaps(treesOld,ridgeOld,teamSites)
assert(#original==2 and original[1]==5 and original[2]==6,
 "original TEAM item geometry must reproduce two independent obstacles")
local ridgeFixedOnly=overlaps(treesOld,ridgeNew,teamSites)
assert(#ridgeFixedOnly==1 and ridgeFixedOnly[1]==5,
 "ridge alone must NOT silently certify unrelated tree/DASH obstacle")
local forestAndRidge=overlaps(treesNew,ridgeNew,teamSites)
assert(#forestAndRidge==0,"forest+ridgetopology must leave all 9 ITEM sites clear")
-- Other mode is intentionally unaffected. Item world X origin is the original Lua code.
for _,site in ipairs(brSites) do
 assert(site.X>=480 and site.X<=760)
end
-- DASH item center-to-tree physical gap after 18-stud source-original movement.
local dash=teamSites[5]
local forest=treesNew[1]
local gap=math.abs(dash.Z-forest.Position.Z)-forest.Size.Z/2-1.1
assert(gap==13.4)
-- Validate a 2-stud character approaching forest DASH along lane center around z470.
for z=455,482 do
 assert(not collides(treesNew,Vector3.new(dash.X,dash.Y,z),2)
         or z>=483,"new forest cannot block approach to pickup within original lane")
end
print("GQ520_REAL_LUAU_ORIGINAL_FOREST_ITEM_VM_PASS 7_trees 9_TEAM_items 9_BR_items")
print("GQ520_FOREST_DASH_COLLISION_NEGATIVE_PASS before_TEAM_2 ridge_only_1 ridge_forest_0")
'''

def extract_forest(source:str):
    start="  for n=1,7 do\n"
    stop="  end\n end\n sessions[mode]=session"
    if source.count(start)!=1 or source.count(stop)!=1:
        raise ValueError("RED: original #482 TREE loop drift")
    a=source.index(start)
    b=source.index(stop,a)+len("  end")
    chunk=source[a:b]
    if chunk.count(OLD_FOREST)!=1 or chunk.count(NEW_FOREST) not in (0,1):
        raise ValueError("RED: unexpected exact tree expression")
    # NEW_FOREST contains OLD_FOREST as a prefix; count the old/new exact
    # alternatives without double-counting that shared prefix.
    if chunk.count(NEW_FOREST)==1 and chunk.count(OLD_FOREST)!=1:
        raise ValueError("RED: duplicate forest expression")
    return chunk

def extract_item_list(source:str):
    start="local FIXED={\n"
    stop="\n}\nfunction RaidItems.offsets()"
    if source.count(start)!=1 or source.count(stop)!=1:
        raise ValueError("RED: original ITEM site list drift")
    i=source.index(start)
    j=source.index(stop,i)+len("\n}")
    return source[i:j]

def extract_item_position_source(source:str):
    start=' local xCenter=if session.mode=="TEAM" then -620 else 620\n'
    stop=" -- Mark first, to prevent reentrant startup spawning a second item set."
    if source.count(start)!=1 or source.count(stop)!=1:
        raise ValueError("RED: original ITEM position source drift")
    return source[source.index(start):source.index(stop)].rstrip()

def inspect(original:str,ridge34:str,forest34:str,item:str):
    if git_blob(original)!=ORIGINAL_GIT_BLOB:
        raise ValueError("RED: original author blob not locked")
    if (original.count(RIDGE_OLD)!=1 or ridge34.count(RIDGE_NEW)!=1
        or forest34.count(RIDGE_NEW)!=1):
        raise ValueError("RED: original ridgeline author source mismatch")
    if forest34.replace(NEW_FOREST,OLD_FOREST)!=ridge34:
        raise ValueError("RED: forest overlay modified another source hunk")
    if ridge34.replace(RIDGE_NEW,RIDGE_OLD).count(OLD_FOREST)!=1:
        raise ValueError("RED: previous ridge overlay was not reversible")
    if patch_forest(ridge34,original,item)!=forest34:
        raise ValueError("RED: generator disagrees with real private forest source")
    return (extract_forest(original),extract_forest(forest34),
            extract_item_list(item),extract_item_position_source(item))

def write_vm(original:Path,ridge:Path,forest:Path,item:Path,out:Path):
    for p in (original,ridge,forest,item):
        if not p.is_file():
            raise ValueError("RED: missing immutable owner source")
    a,b,fixed,points=inspect(original.read_text(encoding="utf-8"),
       ridge.read_text(encoding="utf-8"),
       forest.read_text(encoding="utf-8"),item.read_text(encoding="utf-8"))
    def func(name,source):
        return ("local function "+name+"()\n local spawned={}\n"
                " local function block(parent,name,pos,size,color)\n"
                "  return createPart(spawned,parent,name,pos,size,color)\n"
                " end\n"+source+"\n return spawned\nend\n")
    def item_func():
        return ("local function itemPositions(mode)\n"
                " local session={mode=mode}\n local origin=root\n"
                +points+"\n return points\nend\n")
    result=VEC+fixed+"\n"+item_func()+func("createOldForest",a)+func("createNewForest",b)
    result+=func("createOldRidge",RIDGE_OLD)+func("createNewRidge",RIDGE_NEW)+TEST
    out=out.resolve()
    if out in (p.resolve() for p in (original,ridge,forest,item)):
        raise ValueError("RED: refusing overwrite of author input")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(result,encoding="utf-8")
    print("GQ520_REAL_LUAU_FOREST_VM_GENERATED",len(result))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for k in ("original","ridge","forest","item","out"):
        ap.add_argument("--"+k,type=Path,required=True)
    a=ap.parse_args()
    write_vm(a.original,a.ridge,a.forest,a.item,a.out)

if __name__=="__main__":main()
