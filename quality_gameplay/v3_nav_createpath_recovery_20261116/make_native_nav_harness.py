#!/usr/bin/env python3
"""Native Luau fault-injection harness from generated actual BotPathRouter function.

No fake alternate navigation algorithm: extracts the real maybeCompute block.
"""
from __future__ import annotations
import argparse
from pathlib import Path

BEGIN = "local function maybeCompute("
END = "\nlocal function advanceState("

PRELUDE = r'''--!strict
local states={}
local inFlight=0
local MAX_COMPUTES_IN_FLIGHT=2
local PATH_MAX_DISTANCE=2600
local RECOMPUTE_SECONDS=2.8
local CRAWL_RETRY_DELAY=1.25
local os={clock=function() return 100 end}
local task={spawn=function(f) f() end}
local Enum={PathStatus={Success="Success"}}
local function planar(_,_) return {Magnitude=5} end
local function surfaceAt(_) return 0 end
local function resetPath(s)
 s.path=nil;s.waypoints=nil;s.index=1;s.blockedConn=nil
end
local PathfindingService={throwCreate=false,throwCompute=false,created=0}
function PathfindingService:CreatePath(_)
 self.created+=1
 if self.throwCreate then error("INJECT_CREATE_PATH_FAILURE") end
 local svc=self
 return {
  Status=Enum.PathStatus.Success,
  ComputeAsync=function(_,_,_)
   if svc.throwCompute then error("INJECT_COMPUTE_FAILURE") end
  end,
  GetWaypoints=function(_) return {{Position=42}} end,
  Blocked={Connect=function(_,_) return {Disconnect=function() end} end},
  Destroy=function(self) self.destroyed=true end,
 }
end
'''

SUFFIX = r'''
local function stateFor(id)
 local s={retryAt=0,inFlight=false,index=1,blocked=false}
 states[id]=s
 return s
end
local actor={Parent=true}
local world={}
-- Two simultaneous TEAM+BR creation exceptions must not exhaust the 2-slot budget.
PathfindingService.throwCreate=true
local team=stateFor("TEAM:AI_1")
maybeCompute("TEAM:AI_1",actor,0,1,team,world)
assert(inFlight==0,"TEAM leaked global navigation slot")
assert(team.inFlight==false and team.failed==1,"TEAM actor remains stuck")
assert(team.retryAt==102.8,"TEAM did not schedule existing backoff")
local royale=stateFor("BATTLE_ROYALE:AI_1")
maybeCompute("BATTLE_ROYALE:AI_1",actor,0,1,royale,world)
assert(inFlight==0,"ROYALE leaked global navigation slot")
assert(royale.inFlight==false and royale.failed==1,"ROYALE actor remains stuck")
-- A successful create but failing ComputeAsync still uses original failure flow.
PathfindingService.throwCreate=false
PathfindingService.throwCompute=true
local compute=stateFor("TEAM:AI_2")
maybeCompute("TEAM:AI_2",actor,0,1,compute,world)
assert(inFlight==0 and compute.inFlight==false,"ComputeAsync error leaked permit")
assert(compute.failed==1 and compute.path==nil,"ComputeAsync error did not retry")
-- A recovered service must actually install a path and preserve existing ownership.
PathfindingService.throwCompute=false
local good=stateFor("BATTLE_ROYALE:AI_2")
maybeCompute("BATTLE_ROYALE:AI_2",actor,0,1,good,world)
assert(inFlight==0 and good.inFlight==false,"successful path leaked permit")
assert(good.path~=nil and good.blockedConn~=nil and #good.waypoints==1,"path success behavior regressed")
-- Session replacement during an exception may not mutate a new actor's state.
PathfindingService.throwCreate=true
local stale=stateFor("TEAM:AI_3")
local originalCreate=PathfindingService.CreatePath
PathfindingService.CreatePath=function(self,...)
 states["TEAM:AI_3"]={retryAt=0,inFlight=false}
 return originalCreate(self,...)
end
maybeCompute("TEAM:AI_3",actor,0,1,stale,world)
assert(inFlight==0 and states["TEAM:AI_3"]~=stale,"stale session leaked or revived")
assert(states["TEAM:AI_3"].inFlight==false,"replacement actor changed")
print("NATIVE_LUAU_V3_AI_NAV_CREATEPATH_RECOVERY: 5 CASES PASS")
'''


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--patched", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args=parser.parse_args()
    source=args.patched.read_text(encoding="utf-8")
    if source.count(BEGIN)!=1 or source.count(END)!=1:
        raise ValueError("actual original Router maybeCompute function marker drift")
    start=source.index(BEGIN)
    end=source.index(END,start)
    function=source[start:end]
    for marker in ("inFlight=math.max(0,inFlight-1)", "local candidate=PathfindingService:CreatePath", "state.retryAt=os.clock()+RECOMPUTE_SECONDS"):
        if marker not in function:
            raise ValueError(f"source-exact function missing {marker}")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(PRELUDE+"\n"+function+"\n"+SUFFIX,encoding="utf-8")
    print(f"EXTRACTED_REAL_BOT_ROUTER_FUNCTION_BYTES={len(function.encode())}")


if __name__=="__main__":
    main()
