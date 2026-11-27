#!/usr/bin/env python3
"""Run actual 73-source SoloTeamBots pathTo + lease invalidation on native Luau.

The physical PathfindingService is replaced with queued deterministic paths;
the real code controls allocation, timeout, invalidation, stale callbacks
and task accounting. This is source-level engine-mocked QA, not Studio physics.
"""
from __future__ import annotations
import argparse
from pathlib import Path

def piece(s: str, start: str,end: str) -> str:
    i=s.index(start); j=s.index(end,i+len(start))
    assert j>i
    return s[i:j]

def verify(dist: Path,out: Path):
    src=(dist/"src/server/SoloTeamBots.luau").read_text("utf8")
    lease=piece(src,'local function releasePathLease(bot)',
                'local function respawn(bot)')
    paths=piece(src,'local function pathTo(bot,goal,now)',
                'local function move(bot,goal,now)')
    assert 'releasePathLease(bot)' in lease
    assert 'if lease.held then' in paths
    assert 'MAX_PENDING_PATH_TASKS' in paths
    assert 'pendingPathTasks=math.max(0,pendingPathTasks-1)' in paths
    assert 'bot.pathLease==lease' in paths
    assert 'bot.lastGoal=goal' in paths
    assert 'pendingPathTasks+=1' in paths
    assert src.count('local function pathTo(')==1
    assert src.count('local function invalidatePath(')==1
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text("\n".join((MOCK,lease,AFTER_LEASE,paths,CASES)),"utf8")
    print("P0D_FIRSTPLAY_REAL_PATH_LEASE_GENERATION_CODE_EXACT_PASS")

MOCK=r'''
--!nocheck
local V
V=function(x,y,z)
  return setmetatable({X=x,Y=y,Z=z},{
    __sub=function(a,b) return V(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end,
    __index=function(t,k)
      if k=="Magnitude" then
        return math.sqrt(t.X*t.X+t.Y*t.Y+t.Z*t.Z)
      end
      return nil
    end
  })
end
local Enum={PathStatus={Success="Success"}}
local Paths={}
local shouldThrowWaypoints=false
local warnings={}
local function warn(...) table.insert(warnings,{...}) end
local PathfindingService={}
function PathfindingService:CreatePath(config)
  local p={Status=Enum.PathStatus.Success}
  function p:ComputeAsync(start,goal)
    self.start=start;self.goal=goal
    -- In the real engine ComputeAsync yields: keep the live task genuinely
    -- suspended until the harness explicitly calls runOne.
    coroutine.yield()
  end
  function p:GetWaypoints()
    if shouldThrowWaypoints then error("INJECTED_GETWAYPOINTS_ERROR") end
    return {{Position=V(0,0,0)},{Position=self.goal}}
  end
  table.insert(Paths,p)
  return p
end
local task={queue={}}
function task.spawn(fn)
  local co=coroutine.create(fn)
  local ok,err=coroutine.resume(co)
  assert(ok,err)
  if coroutine.status(co)~="dead" then table.insert(task.queue,co) end
end
local function runOne(i)
  local co=table.remove(task.queue,i or 1)
  assert(co,"missing suspended path worker")
  assert(coroutine.status(co)=="suspended","not actually suspended")
  local ok,err=coroutine.resume(co)
  assert(ok,err)
  if coroutine.status(co)~="dead" then table.insert(task.queue,co) end
end
local REPATH_SECONDS=3.1
local PATH_TIMEOUT_SECONDS=8
local MAX_INFLIGHT_PATHS=10
local MAX_PENDING_PATH_TASKS=10
local inflightPaths=0
local pendingPathTasks=0
local active=true
local epoch=1
local function alive(bot)
  return bot.hum.Health>0 and bot.model.Parent==true
end
local function check(ok,name)
  assert(ok,"P0D_REAL_PATH_LEASE_NATIVE_FAILED_"..name)
end
local function makeBot()
  return {model={Parent=true},hum={Health=100},
    root={Position=V(0,0,0)},path={},pathIndex=1,
    pathGeneration=0,lastGoal=V(50,0,0),
    nextRepath=0,planning=false,planningSince=0}
end
'''
AFTER_LEASE=r'''
'''
CASES=r'''
local a=makeBot()
local target=V(50,0,0)
pathTo(a,target,0)
check(inflightPaths==1 and pendingPathTasks==1 and #task.queue==1,
 "FIRST_REAL_PATH_SLOT_AND_PENDING_COUNT")
check(a.pathLease and a.pathLease.held and a.planning,
 "FIRST_PATH_HAS_HELD_LEASE")
local firstLease=a.pathLease
invalidatePath(a)
check(inflightPaths==0 and pendingPathTasks==1,
 "CANCEL_LOGICAL_SLOT_NOT_RAW_WORKER")
check(firstLease.held==false and a.pathLease==nil,
 "INVALIDATED_LEASE_RELEASED_ONCE")
invalidatePath(a)
check(inflightPaths==0 and pendingPathTasks==1,
 "DOUBLE_INVALIDATION_NO_DOUBLE_RELEASE")
a.lastGoal=target
runOne()
check(inflightPaths==0 and pendingPathTasks==0,
 "LATE_COMPLETION_RELEASES_ONLY_RAW_PENDING")
check(#a.path==0 and a.pathLease==nil and not a.planning,
 "OLD_GENERATION_CANNOT_CLAIM_CURRENT_PATH")

local all={}
for i=1,10 do
  local b=makeBot()
  pathTo(b,target,0)
  table.insert(all,b)
end
check(#task.queue==10 and pendingPathTasks==10
  and inflightPaths==10,"MAX_TEN_PENDING_QUEUED")
invalidatePath(all[1])
check(inflightPaths==9 and pendingPathTasks==10,
 "LOGICAL_LEASE_RELEASED_EVEN_IF_COMPUTE_HANGS")
local fresh=makeBot()
pathTo(fresh,target,0)
check(#task.queue==10 and pendingPathTasks==10,
 "RAW_WORKERS_HARD_CAPPED_NO_UNBOUNDED_COMPUTE")
check(not fresh.planning and fresh.pathLease==nil,
 "FALLBACK_CAN_CONTINUE_DIRECT_MOVE_WITHOUT_PATH_TASK")
runOne()
check(inflightPaths==9 and pendingPathTasks==9,
 "STALE_COMPLETION_NO_DOUBLE_RELEASE_OF_LEASE")
fresh.lastGoal=target
pathTo(fresh,target,3.5)
check(#task.queue==10 and pendingPathTasks==10
  and inflightPaths==10,"CAPACITY_FREED_ON_REAL_COMPLETION")
for i=1,10 do runOne() end
check(#task.queue==0 and pendingPathTasks==0
  and inflightPaths==0,"ALL_TASKS_SETTLED_NO_SLOT_LEAK")
check(fresh.pathIndex==2 and #fresh.path==2,
 "NEWER_PATH_COMPLETES_WHEN_CAPACITY_AVAILABLE")
local timebot=makeBot()
pathTo(timebot,target,0)
local old=timebot.pathLease
timebot.lastGoal=target
pathTo(timebot,target,9)
check(old.held==false and inflightPaths==0
  and pendingPathTasks==1,"TIMEOUT_INVALIDATES_LEASE")
check(timebot.lastGoal==target and not timebot.planning,
 "TIMEOUT_PRESERVES_EXACT_GOAL_AND_FREES_PLANNER_FLAG")
runOne()
check(pendingPathTasks==0 and inflightPaths==0,
 "TIMEOUT_STALE_CALLBACK_NO_DOUBLE_RELEASE")
-- Failure in GetWaypoints used to kill callback without releasing capacity.
local errorbot=makeBot()
shouldThrowWaypoints=true
pathTo(errorbot,target,0)
check(pendingPathTasks==1 and inflightPaths==1 and #task.queue==1,
  "THROWING_WAYPOINTS_SUSPENDS_WORKER_AND_HOLDS_SLOT")
runOne()
check(pendingPathTasks==0 and inflightPaths==0,
  "GETWAYPOINTS_FAILURE_RELEASES_ALL_SLOTS")
check(errorbot.pathIndex==1 and #errorbot.path==0 and not errorbot.planning,
  "GETWAYPOINTS_FAILURE_RESETS_PATH_SAFELY")
check(#warnings==1,"GETWAYPOINTS_FAILURE_WARNED")
shouldThrowWaypoints=false
-- Never create a new actual task when the suspended workers hit the cap,
-- even if every invalidated logical lease has been released.
local hung={}
for i=1,10 do
  local b=makeBot()
  pathTo(b,target,0)
  table.insert(hung,b)
end
for _,b in ipairs(hung) do invalidatePath(b) end
check(pendingPathTasks==10 and inflightPaths==0 and #task.queue==10,
  "TEN_ACTUAL_SUSPENDED_WORKERS_NOT_LOGICALLY_HELD")
local excluded=makeBot()
pathTo(excluded,target,0)
check(pendingPathTasks==10 and #task.queue==10,
  "CAP_STILL_HOLDS_WHEN_ALL_LEASES_INVALIDATED")
for i=1,10 do runOne() end
check(pendingPathTasks==0 and inflightPaths==0,
  "HUNG_CALLBACKS_RESUMED_RECLAIM_CAPACITY")
print("P0D_REAL_BOT_PATH_LEASE_25_NATIVE_CASES_PASS")
'''
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    verify(a.dist,a.out)
