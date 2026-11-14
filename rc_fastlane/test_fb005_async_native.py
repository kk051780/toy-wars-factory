#!/usr/bin/env python3
"""Executable Luau behavioral regression from ACTUAL authored bot functions.

Mocks only Roblox PathfindingService/async scheduler/Vector3 environment; runs
original invalidatePath(), pathTo(), and move() without modifying their source.
This is not real Roblox Studio physics or full multiplayer engine testing.
"""
from __future__ import annotations
import argparse
from pathlib import Path

SRC=Path(__file__).resolve().parent/"features/fb005_solo/SoloTeamBots.luau"

def segment(raw: str, start: str, end: str)->str:
    assert raw.count(start)==raw.count(end)==1,("NATIVE_SOURCE_DRIFT",start,end)
    return raw.split(start,1)[1].split(end,1)[0]

def generate():
    s=SRC.read_text("utf8")
    a="local function invalidatePath(bot)"
    b="local function respawn(bot)"
    c="local function pathTo(bot,goal,now)"
    d="local function move(bot,goal,now)"
    e="local function nearestEnemyBot(bot,maxDistance)"
    first=a+segment(s,a,b)
    path=c+segment(s,c,d)
    moving=d+segment(s,d,e)
    assert "pathGeneration" in first and "epoch==token" in path
    assert "bot.lastGoal-goal" in path
    assert "bot.lastGoal=goal" in moving
    return "\n".join([r'''-- Generated runnable from exact authored SoloTeamBots functions.
-- All async scheduling runs on REAL Luau coroutines with a suspended ComputeAsync.
local function v(x)
    local meta={}
    meta.__sub=function(a,b) return {Magnitude=math.abs(a.x-b.x)} end
    return setmetatable({x=x},meta)
end
local tasks={}
local task={}
function task.spawn(f)
    local co=coroutine.create(f)
    table.insert(tasks,co)
    local ok,err=coroutine.resume(co)
    assert(ok,tostring(err))
    assert(coroutine.status(co)=="suspended","MOCK_COMPUTE_MUST_YIELD")
end
local function finish(n)
    assert(tasks[n], "MISSING_PENDING_COMPUTE")
    local ok,err=coroutine.resume(tasks[n])
    assert(ok,tostring(err))
    assert(coroutine.status(tasks[n])=="dead","MOCK_COMPUTE_MUST_FINISH")
end
local Enum={PathStatus={Success="SUCCESS"},PathWaypointAction={Jump="JUMP"}}
local PathfindingService={}
function PathfindingService:CreatePath(options)
    local p={Status=Enum.PathStatus.Success}
    function p:ComputeAsync(from,goal)
        self.goal=goal
        self.from=from
        coroutine.yield("PATH_PENDING")
    end
    function p:GetWaypoints()
        return {{Position=self.goal,Action="WALK"},{Position=self.goal,Action="WALK"}}
    end
    return p
end
local REPATH_SECONDS=3.1
local active=true
local epoch=10
local function alive(bot)
    return bot.hum.Health>0 and bot.model.Parent~=nil
end
local function newBot()
    local hum={Health=100}
    function hum:MoveTo(where) self.target=where end
    return {root={Position=v(0)},hum=hum,model={Parent=true},
        nextRepath=0,path={},pathIndex=1,planning=false,
        lastGoal=nil,pathGeneration=0}
end
''',first,path,moving,r'''
-- 1. Target changes while OLD ComputeAsync yields, stale waypoints discarded,
--    new planner remains locked until its own result arrives.
local bot=newBot()
move(bot,v(100),1)
assert(#tasks==1 and bot.planning==true,"INITIAL_YIELD_MISSING")
local firstGeneration=bot.pathGeneration
move(bot,v(250),2)
assert(#tasks==2 and bot.pathGeneration>firstGeneration,
    "NEW_GOAL_DID_NOT_INVALIDATE_OLD_PATH")
finish(1)
assert(#bot.path==0 and bot.planning==true,
    "STALE_PLANNER_ADOPTED_OR_UNLOCKED_NEW_PLANNER")
finish(2)
assert(#bot.path==2 and bot.path[2].Position.x==250 and bot.planning==false,
    "CURRENT_PLANNER_NOT_APPLIED")

-- 2. Old callback cannot affect a bot that respawned into a DIFFERENT root
--    even if a programmer accidentally leaves a stale generation unchanged.
local b=newBot()
move(b,v(75),6)
local idx=#tasks
local oldGen=b.pathGeneration
b.root={Position=v(0)}
b.path={}
b.pathGeneration=oldGen+1
b.planning=true
finish(idx)
assert(#b.path==0 and b.planning==true,"RESPAWN_GHOST_PATH_OR_UNLOCK")

-- 3. Minor moving-target jitter does not continuously thrash replans;
--    an eight-stud adjustment can use the existing computed route.
local c=newBot()
move(c,v(120),10)
idx=#tasks
local g=c.pathGeneration
move(c,v(124),10.3)
assert(c.pathGeneration==g and #tasks==idx,"SMALL_JITTER_REPLAN_THRASH")
finish(idx)
assert(#c.path==2 and c.path[1].Position.x==120,"JITTER_FALSE_REJECT")

-- 4. Goal identity guard independently refuses stale waypoints if lastGoal
--    changes without a generation update during a yielding planner.
local d=newBot()
move(d,v(88),20)
idx=#tasks
d.lastGoal=v(230)
finish(idx)
assert(#d.path==0,"OLD_GOAL_ACCEPTED_WITH_SAME_GENERATION")

-- 5. Entire-match epoch changes invalidate still-yielding planned routes.
local eBot=newBot()
move(eBot,v(95),30)
idx=#tasks
epoch+=1
active=false
finish(idx)
assert(#eBot.path==0,"OLD_MATCH_PATH_ACCEPTED")
print("FB005_ASYNC_LIFECYCLE_NATIVE_BEHAVIOR_PASS")
'''])

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--emit",required=True,type=Path)
    args=p.parse_args()
    code=generate()
    args.emit.write_text(code,encoding="utf8")
    print("FB005_NATIVE_SOURCE_EXTRACT_GENERATED",len(code))
