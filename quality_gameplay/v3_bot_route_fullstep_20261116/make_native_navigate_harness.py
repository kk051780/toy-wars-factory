#!/usr/bin/env python3
"""Native Luau regression using the EXACT authored BotPathRouter.navigate function.

Original and patched full source is run under deterministic Roblox API stubs:
the source's real Router.navigate, routeClear, MaybeCompute, path state and
PivotTo are exercised. It is NOT Studio physics or device performance proof.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from source_patch import BEFORE, AFTER

PRELUDE = r'''
-- The complete original AUTHOR LuaU source follows this server-only mock.
-- Note: all game navigation decisions use the real authored Router.navigate.
local Vec={}
Vec.__index=function(self,key)
 if key=="Magnitude" then
  return math.sqrt(self.X*self.X+self.Y*self.Y+self.Z*self.Z)
 elseif key=="Unit" then
  local n=math.sqrt(self.X*self.X+self.Y*self.Y+self.Z*self.Z)
  assert(n>0)
  return setmetatable({X=self.X/n,Y=self.Y/n,Z=self.Z/n},Vec)
 end
 return rawget(Vec,key)
end
local Vector3={}
function Vector3.new(x,y,z) return setmetatable({X=x,Y=y,Z=z},Vec) end
function Vec.__add(a,b) return Vector3.new(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end
function Vec.__sub(a,b) return Vector3.new(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end
function Vec.__mul(a,b)
 if type(a)=="number" then return Vector3.new(a*b.X,a*b.Y,a*b.Z) end
 return Vector3.new(a.X*b,a.Y*b,a.Z*b)
end
local CFrame={}
function CFrame.lookAt(position,_) return {Position=position} end
local Enum={RaycastFilterType={Exclude="Exclude"},PathStatus={Success="Success"}}
local RaycastParams={}
function RaycastParams.new()
 return {RespectCanCollide=false}
end
local worldState={wallAt=nil,lastHorizontal=nil,verticals=0}
local workspace={}
function workspace:Raycast(origin,direction,params)
 assert(params.RespectCanCollide==true,"source must ignore noncollidable visuals")
 if direction.Y<-.1 then
  worldState.verticals+=1
  return {
   Instance={CanCollide=true},
   Normal=Vector3.new(0,1,0),
   Position=Vector3.new(origin.X,0,origin.Z),
  }
 end
 local dist=direction.Magnitude
 worldState.lastHorizontal=dist
 if worldState.wallAt~=nil and dist>=worldState.wallAt then
  return {Instance={CanCollide=true}}
 end
 return nil
end
local pathfinding={}
function pathfinding:CreatePath(_)
 local path={Status=Enum.PathStatus.Success}
 function path:ComputeAsync(_,goal) self.dest=goal end
 function path:GetWaypoints() return {{Position=self.dest}} end
 function path:Destroy() self.destroyed=true end
 path.Blocked={Connect=function(_,_) return {Disconnect=function(_) end} end}
 return path
end
local runService={IsStudio=function(_)return true end}
local game={}
function game:GetService(name)
 if name=="PathfindingService" then return pathfinding end
 if name=="RunService" then return runService end
 error("unexpected engine service "..tostring(name))
end
local task={}
function task.spawn(fn) fn() end
'''

SUFFIX = r'''
-- Not a reimplemented route planner: all cases call REAL Router.navigate.
local function modelAtOrigin()
 local model={Parent=true,PrimaryPart=true,pivots=0,position=Vector3.new(0,2,0)}
 function model:GetPivot() return {Position=self.position} end
 function model:PivotTo(cf) self.pivots+=1;self.position=cf.Position end
 return model
end
local function case(id,goalDistance,dt,wallAt,expectedMoved,expectedHorizontal)
 worldState.wallAt=wallAt
 worldState.lastHorizontal=nil
 local m=modelAtOrigin()
 local remain=Router.navigate(id,m,Vector3.new(goalDistance,2,0),dt,{Name="Actors"})
 assert(remain==goalDistance,"remaining-distance reporting drifted")
 local moved=m.pivots>0
 assert(moved==expectedMoved,
   "actual Router.navigate move/block mismatch "..id.." got "..tostring(moved))
 assert(worldState.lastHorizontal~=nil,"actual routeClear ray did not execute")
 assert(math.abs(worldState.lastHorizontal-expectedHorizontal)<0.00001,
   "actual Router.navigate used wrong collision ray length "..id..
   " ray="..tostring(worldState.lastHorizontal))
 if moved then
  local step=math.min(30*math.clamp(dt,.05,.3),goalDistance)
  assert(math.abs(m.position.X-step)<0.00001,"actual PivotTo movement drifted")
  assert(m.position.Y==2,"ground snap changed")
 else
  assert(m.position.X==0 and m.position.Y==2,"blocked AI crossed obstacle")
 end
 Router.clear(id)
end
-- Root regression: 9 stud movement with wall at 8.5 studs. OLD walks through;
-- patched actual function must reject BEFORE PivotTo (not only routeClear).
case("TEAM:LAST_STUD",30,.3,8.5,EXPECT_SAFE_BLOCK,EXPECTED_MAX_RAY)
case("BATTLE_ROYALE:LAST_STUD",30,.3,8.5,EXPECT_SAFE_BLOCK,EXPECTED_MAX_RAY)
-- All other navigation decisions and two-mode namespaces remain unchanged.
case("TEAM:NEAR_WALL",30,.3,7.5,false,EXPECTED_MAX_RAY)
case("BATTLE_ROYALE:OPEN",30,.3,nil,true,EXPECTED_MAX_RAY)
case("TEAM:SHORT",3,.3,nil,true,3)
case("BATTLE_ROYALE:DT_018",30,.18,5.0,false,5.4)
print(REPORT_LABEL.." real_Router.navigate_cases=6")
'''

def build(actual_source: str, *, safe: bool) -> str:
    if actual_source.count(AFTER if safe else BEFORE)!=1:
        raise ValueError("source-specific raycast anchor drift")
    for anchor in ("function Router.navigate(", "local function routeClear(",
                   "local function maybeCompute(", "local function advanceState(",
                   "model:PivotTo(", "return Router"):
        if actual_source.count(anchor)!=1:
            raise ValueError("full original Router requirement changed: "+anchor)
    body=SUFFIX.replace("EXPECT_SAFE_BLOCK","false" if safe else "true")
    body=body.replace("EXPECTED_MAX_RAY","9" if safe else "8")
    body=body.replace("REPORT_LABEL",
                      '"GQ_FULL_NAVIGATE_SAFE_FULLSTEP"' if safe else '"GQ_FULL_NAVIGATE_OLD_LEAK"')
    main, delimiter, remainder = actual_source.rpartition("\nreturn Router")
    if not delimiter or remainder.strip():
        raise ValueError("original Router source must end in module return")
    # Native spec must append assertions *before* any top-level return.
    return PRELUDE+"\n"+main+"\n"+body


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original",type=Path,required=True)
    parser.add_argument("--patched",type=Path,required=True)
    parser.add_argument("--outdir",type=Path,required=True)
    args=parser.parse_args()
    orig=args.original.read_text(encoding="utf-8")
    fixed=args.patched.read_text(encoding="utf-8")
    if fixed.replace(AFTER,BEFORE,1)!=orig:
        raise ValueError("not exactly one source-selected full-Router delta")
    args.outdir.mkdir(parents=True,exist_ok=True)
    (args.outdir/"navigate-original.spec.luau").write_text(build(orig,safe=False),encoding="utf-8")
    (args.outdir/"navigate-fixed.spec.luau").write_text(build(fixed,safe=True),encoding="utf-8")
    # Red negative control: an unsafe ray must be rejected by the *safe* expectations.
    (args.outdir/"navigate-mutant.spec.luau").write_text(build(fixed,safe=True).replace(AFTER,BEFORE,1),encoding="utf-8")
    print("FULL_AUTHORED_ROUTER_NATIVE_SPECS_GENERATED original+fixed+mutant")


if __name__=="__main__":
    main()
