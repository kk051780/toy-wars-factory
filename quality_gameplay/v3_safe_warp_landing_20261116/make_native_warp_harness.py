#!/usr/bin/env python3
"""Execute the ACTUAL patched safeMove function under a native Luau Roblox-API simulation."""
from __future__ import annotations
import argparse
from pathlib import Path

PREFIX = r'''--!strict
-- Original patched function is injected verbatim below (not a Python reimplementation).
local Vec = {}
Vec.__index = Vec
local function vec(x:number,y:number,z:number)
 return setmetatable({X=x,Y=y,Z=z},Vec)
end
function Vec.__add(a:any,b:any)
 return vec(a.X+b.X,a.Y+b.Y,a.Z+b.Z)
end
function Vec.__mul(a:any,b:any)
 if type(a)=="number" then return vec(a*b.X,a*b.Y,a*b.Z) end
 if type(b)=="number" then return vec(a.X*b,a.Y*b,a.Z*b) end
 error("unsupported vector scale")
end
Vector3={new=vec}
CFrame={new=function(pos:any,look:any) return {Position=pos,LookVector=look} end}
RaycastParams={new=function() return {} end}
OverlapParams={new=function() return {} end}
Enum={RaycastFilterType={Exclude="Exclude"}}
local config=""
local castCount=0
local footprintCount=0
local floorY=0
local arena={Position=vec(0,0,0),Size=vec(890,2,1050),CanCollide=true,Parent=true}
function arena:IsA(kind:string) return kind=="BasePart" end
local world={}
function world:FindFirstChild(name:string)
 if config=="no_arena" then return nil end
 if name=="TacticalBattlefield" then return arena end
 return nil
end
workspace={}
function workspace:Raycast(origin:any,delta:any,params:any)
 if delta.Y < -10 then
  if config=="no_floor" then return nil end
  return {Instance={CanCollide=true},Position=vec(origin.X,floorY,origin.Z)}
 end
 castCount+=1
 local obstruct=false
 if config=="foot_wall" and math.abs(origin.Y-1.9)<0.01 then obstruct=true end
 if config=="side_wall" and math.abs(origin.Z-1.3)<0.01 then obstruct=true end
 if config=="low_roof" and math.abs(origin.Y-7.6)<0.01 then obstruct=true end
 if config=="near_wall" then obstruct=true end
 if obstruct then
  return {Distance=if config=="near_wall" then 2 else 5}
 end
 return nil
end
function workspace:GetPartBoundsInBox(destination:any,extent:any,params:any)
 footprintCount+=1
 if extent.X~=3.2 or extent.Y~=4.5 or extent.Z~=3.2 then error("bad body extent") end
 if config=="solid_landing" then return {{CanCollide=true}} end
 if config=="visual_landing" then return {{CanCollide=false}} end
 return {}
end
local avatar={pivot=nil,pivots=0}
function avatar:PivotTo(cf:any)
 self.pivot=cf
 self.pivots+=1
end
local root={Position=vec(0,3,0),CFrame={LookVector=vec(1,0,0),RightVector=vec(0,0,1)}}
local session={world=world}
'''

SUFFIX = r'''
local cases={
 {"free_route",true,20,20},
 {"foot_wall",false,20,nil},
 {"side_wall",false,20,nil},
 {"low_roof",false,20,nil},
 {"near_wall",false,20,nil},
 {"solid_landing",false,20,nil},
 {"visual_landing",true,20,20},
 {"no_arena",false,20,nil},
 {"no_floor",false,20,nil},
 {"out_of_bounds",false,20,nil},
 {"cliff_over_eight",false,20,nil},
}
local n=0
for _,case in ipairs(cases) do
 config=case[1]
 castCount=0
 footprintCount=0
 avatar.pivot=nil;avatar.pivots=0
 root.Position=if config=="out_of_bounds" then vec(435,3,0) else vec(0,3,0)
 floorY=if config=="cliff_over_eight" then 14 else 0
 local result=safeMove(session,avatar,root,case[3])
 assert(result==case[2],case[1].." actual Luau function should return "..tostring(case[2]))
 assert(avatar.pivots==(if case[2] then 1 else 0),case[1].." must never pivot on failure")
 if case[4] then
  assert(avatar.pivot and math.abs(avatar.pivot.Position.X-case[4])<0.001,case[1].." actual destination wrong")
 end
 if config=="no_arena" then
  assert(castCount==0 and footprintCount==0,"reject arena missing before physics")
 elseif config=="foot_wall" or config=="side_wall" or config=="low_roof" or config=="near_wall" then
  assert(castCount==9 and footprintCount==0,case[1].." short-circuit after corridor")
 elseif config=="solid_landing" or config=="visual_landing" or config=="free_route" then
  assert(castCount==9 and footprintCount==1,case[1].." full corridor + footprint")
 end
 n+=1
end
print("GQ_SAFE_WARP_ORIGINAL_PATCHED_LUAU_11_SCENARIOS_PASS",n)
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--patched", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    source = args.patched.read_text(encoding="utf-8")
    marker = "local function safeMove("
    after = "\nlocal function healAllies("
    assert source.count(marker) == 1 and source.count(after) == 1, "source drift"
    fn = marker + source.split(marker, 1)[1].split(after, 1)[0]
    assert "GetPartBoundsInBox" in fn and "TacticalBattlefield" in fn
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(PREFIX + "\n" + fn + "\n" + SUFFIX, encoding="utf-8")
    print("GQ_SAFE_WARP_SOURCE_EXTRACTED_NATIVE_HARNESS_PREPARED")


if __name__ == "__main__":
    main()
