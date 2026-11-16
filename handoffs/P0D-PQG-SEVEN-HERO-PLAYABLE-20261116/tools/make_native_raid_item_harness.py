#!/usr/bin/env python3
"""Native Luau functional QA for cross-lane item intake; no Roblox Studio claim."""
from pathlib import Path
import argparse
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"EGGRUMBLE_RaidItemIntake.luau"
def build(out:Path):
    src=SOURCE.read_text(encoding="utf-8").rstrip()
    if not src.endswith("\nreturn RaidItems"):
        raise RuntimeError("source return contract changed")
    suite=r'''
local vec={}
vec.__index=vec
function vec.new(x,y,z) return setmetatable({X=x,Y=y,Z=z},vec) end
function vec.__add(a,b) return vec.new(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end
Vector3=vec
assert(RaidItems.validate())
local offsets=RaidItems.offsets()
assert(#offsets==9)
local first=offsets[1].x
offsets[1].x=99999
assert(RaidItems.offsets()[1].x==first,"item plan must be immutable by consumers")
local calls=0
local function fakeItems()
 return {start=function(session,points)
  calls+=1
  assert(session.rules.phase=="ACTIVE")
  assert(#points==9)
  local seen={}
  for _,pos in ipairs(points) do
   local id=tostring(pos.X)..":"..tostring(pos.Z)
   assert(not seen[id],"duplicate physical pickup position")
   seen[id]=true
  end
  session.itemPositions=points
 end}
end
local origin=vec.new(0,4,0)
local team={rules={phase="ACTIVE"},mode="TEAM"}
local royal={rules={phase="ACTIVE"},mode="BATTLE_ROYALE"}
assert(RaidItems.start(team,origin,fakeItems())==9)
assert(RaidItems.start(royal,origin,fakeItems())==9)
assert(calls==2)
assert(team.itemPositions[1].X==-760)
assert(royal.itemPositions[1].X==480)
assert(royal.itemPositions[1].X-team.itemPositions[1].X==1240)
assert(not pcall(function() RaidItems.start(team,origin,fakeItems()) end),"one-world-only guard")
assert(not pcall(function() RaidItems.start({rules={phase="LOBBY"},mode="TEAM"},origin,fakeItems()) end),"not in lobby")
assert(not pcall(function() RaidItems.start({rules={phase="ACTIVE"},mode="INVALID"},origin,fakeItems()) end),"invalid mode")
local failures=0
local broken={start=function() failures+=1;error("test injection") end}
local state={rules={phase="ACTIVE"},mode="TEAM"}
assert(not pcall(function() RaidItems.start(state,origin,broken) end))
assert(failures==1 and state.itemIntakeStarted==false,"failed insertion may retry")
print("[EGGRUMBLE NATIVE ROUTE ITEM INTAKE] PASS",9,"balanced sites x 2 match modes and fault guards")
'''
    out.write_text(src[:-len("\nreturn RaidItems")]+suite,encoding="utf-8")
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    build(args.out)
