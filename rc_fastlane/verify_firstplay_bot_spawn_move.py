#!/usr/bin/env python3
"""Executable source-exact SoloTeamBots.start/move native Luau acceptance.

Executes the REAL compiled feature's Bot.start with Roblox instance/model stub,
plus REAL move and invalidatePath with deterministic physics-stall simulation.
This is not Roblox Studio physics nor actual PathfindingService execution.
"""
from __future__ import annotations
import argparse
from pathlib import Path

def piece(src: str,start: str,end: str) -> str:
    a=src.index(start)
    b=src.index(end,a+len(start))
    assert b>a
    return src[a:b]

def verify(dist: Path,output: Path) -> None:
    bot=(dist/"src/server/SoloTeamBots.luau").read_text("utf8")
    start=piece(bot,"function Bot.start(world,humanTeam,authority)",
                "local function alive(bot)")
    invalid=piece(bot,"local function invalidatePath(bot)",
                  "local function respawn(bot)")
    move=piece(bot,"local function move(bot,goal,now)",
               "local function nearestEnemyBot(bot,maxDistance)")
    assert "local function eligibleSoloPlayers()" not in start
    assert 'if eligible~=1 then return false end' in start
    assert 'P0D_LateJoinSpectator' in start
    assert 'table.insert(bots,makeActor(' in start
    assert 'assert(#bots==MAX_BOTS)' in start
    assert 'bot.unstuckAttempts=((bot.unstuckAttempts or 0)%4)+1' in move
    assert 'bot.hum:MoveTo(bot.detourGoal)' in move
    assert 'now<bot.detourUntil and gap>2.5' in move
    assert 'bot.hum.Jump=true' in move
    assert 'if bot.lastGoal==nil or (bot.lastGoal-goal).Magnitude>8 then' in move
    assert 'pathTo(bot,goal,now)' in move
    assert 'bot.pathGeneration+=1' in invalid
    assert bot.count('function Bot.start(')==1
    assert bot.count('local function move(')==1
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text("\n".join((PRELUDE,invalid,start,PATH_MOCK,move,CASES)),"utf8")
    print("P0D_SOLO_REAL_BOT_START_AND_STALL_MOVE_SOURCE_EXACT_PASS")

PRELUDE=r'''
--!nocheck
local Vector3={}
local V
V=function(x,y,z)
  local props={X=x,Y=y,Z=z}
  return setmetatable(props,{
    __sub=function(a,b) return V(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end,
    __add=function(a,b) return V(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end,
    __mul=function(a,b)
      if type(a)=="number" then return V(a*b.X,a*b.Y,a*b.Z) end
      if type(b)=="number" then return V(a.X*b,a.Y*b,a.Z*b) end
      error("vector scalar required")
    end,
    __index=function(t,k)
      local mag=math.sqrt(t.X*t.X+t.Y*t.Y+t.Z*t.Z)
      if k=="Magnitude" then return mag end
      if k=="Unit" then
        if mag<1e-8 then return V(0,0,0) end
        return V(t.X/mag,t.Y/mag,t.Z/mag)
      end
      return nil
    end
  })
end
Vector3.new=V
local CFrame={}
local spawnMeta={}
spawnMeta.__mul=function(a,b)
  return {Position=a.Position,offset=b.offset}
end
function CFrame.new(x,y,z)
  return {offset=V(x,y,z)}
end
local function spawn(x,z)
  return setmetatable({Position=V(x,0,z)},spawnMeta)
end
local Players={online={}}
function Players:GetPlayers() return self.online end
local RunService={studio=true}
function RunService:IsStudio() return self.studio end
local function person(team,late)
  local p={Team=team and {Name=team},attrs={P0D_LateJoinSpectator=late}}
  function p:GetAttribute(key) return self.attrs[key] end
  return p
end
local primary=person("RED",false)
local observer=person(nil,true)
local second=person("BLUE",false)
local Instance={}
function Instance.new(kind)
  assert(kind=="Folder")
  local f={Name="",Parent=nil}
  function f:SetAttribute(name,val) self[name]=val end
  function f:Destroy() self.Parent=nil end
  return f
end
local Bot={}
local active=false
local epoch=0
local map=nil
local callbacks=nil
local folder=nil
local bots={}
local MAX_BOTS=5
local modelCount=0
local startStops=0
function Bot.stop()
  startStops+=1
  active=false
  bots={}
  map=nil
  callbacks=nil
  folder=nil
end
local function makeActor(id,team,style,cf)
  modelCount+=1
  local model={Parent=true}
  function model:Destroy() self.Parent=nil end
  local b={id=id,team=team,style=style,
    model=model,root={Position=cf.Position},hum={Health=100},carry=nil,
    lastGoal=nil,path={},pathIndex=1,pathGeneration=0,
    planning=false,planningSince=0,nextRepath=0}
  return b
end
local authority={
  steal=function() end,deposit=function() end,
  drop=function() end,attackHuman=function() end,
  attackBot=function() end
}
local world={model={},
  teams={RED={spawn=spawn(-30,0)},BLUE={spawn=spawn(30,0)}}}
local function check(condition,name)
  assert(condition,"P0D_SOLO_REAL_BOT_START_STALL_FAILED_"..name)
end
'''
PATH_MOCK=r'''
local function pathTo(bot,goal,now)
  bot.pathCalls=(bot.pathCalls or 0)+1
end
'''
CASES=r'''
-- Actual Bot.start invocation, not just static signature presence.
Players.online={primary,observer}
check(Bot.start(world,"RED",authority)==true,
  "ACTUAL_START_WITH_LATE_SPECTATOR_SUCCEEDS")
check(active and #bots==5 and modelCount==5,
  "REAL_START_CREATES_FIVE_BOTS")
local ours=0
local enemies=0
for _,b in ipairs(bots) do
  if b.team=="RED" then ours+=1 elseif b.team=="BLUE" then enemies+=1 end
end
check(ours==2 and enemies==3,"REAL_START_TWO_ALLIES_THREE_ENEMIES")
check(folder~=nil and folder.Parent==world.model,
  "REAL_START_PHYSICAL_FOLDER_PARENTED")
Players.online={primary,second}
check(Bot.start(world,"RED",authority)==false,
  "TWO_ELIGIBLE_FAIL_CLOSED_NO_SOLO")
check(not active and #bots==0,"FAILED_START_NO_ORPHAN_ROSTER")
Players.online={primary,observer}
check(Bot.start(world,"NONE",authority)==false,
  "INVALID_TEAM_FAIL_CLOSED")
check(not active and #bots==0,"INVALID_TEAM_NO_ROSTER")
check(Bot.start(world,"RED",{steal=function() end})==false,
  "MISSING_GAME_CALLBACKS_FAIL_CLOSED")
check(Bot.start(world,"RED",authority)==true,
  "VALID_START_RECOVERS_AFTER_FAILURE")
RunService.studio=false
check(Bot.start(world,"RED",authority)==false,
  "PRODUCTION_NONSTUDIO_DISABLED")
RunService.studio=true
check(Bot.start(world,"RED",authority)==true,
  "STUDIO_CAN_REENTER_AFTER_NONSTUDIO")

-- Exact move() using a stationary mocked physics position: any direct MoveTo
-- remains stuck, then actual 5sec watchdog must jump/side-step and replan.
local function same(a,b)
  return a and b
    and math.abs(a.X-b.X)<.1 and math.abs(a.Y-b.Y)<.1
    and math.abs(a.Z-b.Z)<.1
end
local stuck={root={Position=V(0,0,0)},path={},pathIndex=1,
  pathGeneration=0,lastGoal=nil,planning=false,
  hum={Jump=false,MoveTo=function() end}}
function stuck.hum:MoveTo(destination)
  self.lastDestination=destination
  self.moveCalls=(self.moveCalls or 0)+1
end
move(stuck,V(50,0,0),0)
check(stuck.pathCalls==1 and same(stuck.hum.lastDestination,V(50,0,0)),
  "FIRST_REAL_MOVETO_TARGET")
move(stuck,V(50,0,0),4.9)
check(same(stuck.hum.lastDestination,V(50,0,0)) and stuck.unstuckAttempts==0,
  "NO_EARLY_STUCK_RECOVERY")
local generationBefore=stuck.pathGeneration
move(stuck,V(50,0,0),5.1)
check(stuck.hum.Jump==true,"STALLED_HUMANOID_JUMPS")
check(stuck.pathGeneration>generationBefore,"STALLED_INVALIDATES_OLD_PATH")
check(same(stuck.hum.lastDestination,V(0,0,7)),
  "FIRST_STUCK_LATERAL_DETOUR")
check(same(stuck.root.Position,V(0,0,0)),
  "FIRST_DETOUR_DOES_NOT_TELEPORT")
check(stuck.unstuckAttempts==1,"WATCHDOG_COUNTS_FIRST_RECOVERY")
move(stuck,V(50,0,0),5.65)
check(same(stuck.hum.lastDestination,V(0,0,7)),
  "HIGH_DETOUR_HELD_ACROSS_NEXT_TICK_NOT_CANCELED")
check(stuck.unstuckAttempts==1,"DETOUR_HOLD_DOES_NOT_COUNT_AS_SECOND_STALL")
check(same(stuck.root.Position,V(0,0,0)),
  "DETOUR_HOLD_DOES_NOT_TELEPORT")
move(stuck,V(50,0,0),10.2)
check(same(stuck.hum.lastDestination,V(0,0,-7)),
  "SECOND_STUCK_ATTEMPT_REVERSES_SIDE")
check(same(stuck.root.Position,V(0,0,0)),
  "SECOND_DETOUR_DOES_NOT_TELEPORT")
check(stuck.unstuckAttempts==2,"BOUNDED_WATCHDOG_SEQUENCE")
stuck.root.Position=V(5,0,0)
move(stuck,V(50,0,0),11)
check(stuck.unstuckAttempts==0,"ACTUAL_MOVEMENT_RESETS_STALL_COUNTER")
check(same(stuck.hum.lastDestination,V(50,0,0)),
  "PROGRESS_RESUMES_FULL_TARGET")
move(stuck,V(-50,0,0),12)
check(stuck.unstuckAttempts==0 and stuck.lastGoal.X==-50,
  "NEW_GOAL_RESETS_STUCK_STATE")
check(same(stuck.hum.lastDestination,V(-50,0,0)),
  "GOAL_CHANGE_MOVES_FULL_NEW_DESTINATION")
-- Arrival must never move a guard away from its egg.
local arrived={root={Position=V(50,0,0)},path={},pathIndex=1,
  pathGeneration=0,lastGoal=nil,planning=false,
  hum={MoveTo=function(self,v) self.lastDestination=v end,Jump=false}}
move(arrived,V(50,0,0),0)
move(arrived,V(50,0,0),20)
check(same(arrived.root.Position,V(50,0,0)),
  "ARRIVAL_NEVER_TELEPORTS")
check(same(arrived.hum.lastDestination,V(50,0,0)),
  "ARRIVAL_HOLDS_GOAL_AFTER_TWENTY_SECONDS")
check((arrived.unstuckAttempts or 0)==0 and arrived.detourGoal==nil,
  "ARRIVAL_NEVER_DETOURS")

-- XZ lateral displacement / jump height does not count toward egg objective.
local sideways={root={Position=V(0,0,0)},path={},pathIndex=1,
  pathGeneration=0,lastGoal=nil,planning=false,
  hum={MoveTo=function(self,v) self.lastDestination=v end,Jump=false}}
move(sideways,V(50,0,0),30)
sideways.root.Position=V(0,2,4)
move(sideways,V(50,0,0),31)
move(sideways,V(50,0,0),35.1)
check(sideways.unstuckAttempts==1 and sideways.detourGoal~=nil,
  "SIDEWAYS_AND_VERTICAL_DISPLACEMENT_NOT_PROGRESS")
check(same(sideways.root.Position,V(0,2,4)),
  "SIDESTEP_PHYSICS_POSITION_NEVER_FORCED")
check(sideways.detourUntil>35.1,
  "DETOUR_HAS_FINITE_HOLD_DURATION")
print("P0D_SOLO_REAL_BOT_START_AND_STALL_35_NATIVE_CASES_PASS")
'''
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    verify(args.dist,args.out)
