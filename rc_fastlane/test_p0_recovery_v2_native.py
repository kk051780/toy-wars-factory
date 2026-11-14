#!/usr/bin/env python3
"""Real author393 helper + final actual Game RESULTS branch, native Luau coverage."""
from __future__ import annotations
import argparse
from pathlib import Path

def emit(dist:Path,out:Path):
    g=(dist/"src/server/Game.server.luau").read_text("utf8")
    assert g.count("local function scheduleLobbyRecovery(")==1
    i=g.index("-- FB006: shared guarded post-results lobby character recovery.")
    j=g.index("local function tickRound()",i)
    helper=g[i:j]
    assert helper.count("local function scheduleLobbyRecovery(")==1
    assert 'task.delay(2,function() attempt(number+1) end)' in helper
    tick=g.index('local function tickRound()')
    a=g.index('elseif match.phase == "RESULTS" then',tick)
    b=g.index('-- Recovery uses the existing server-only authoritative tick',a)
    results=g[a:b].replace('elseif match.phase == "RESULTS" then','if match.phase == "RESULTS" then',1)
    assert 'scheduleLobbyRecovery(p)' in results
    assert 'p:GetAttribute("P0D_LateJoinSpectator")==true' in results
    lobby=g[g.index('local function tickRound()'):]
    assert 'scheduleLobbyRecovery(entrant)' in lobby
    assert 'roundReady[entrant]=false' in lobby
    mock=r'''--!nocheck
local Players={online={},CharacterAutoLoads=true,RespawnTime=5}
function Players:GetPlayers() return self.online end
local RunService={}
function RunService:IsStudio() return true end
local Vector3={zero="ZERO"}
local LobbyIsland={spawn=function(team) return "LOBBY_"..team end}
local task={queue={}}
function task.delay(dt,fn) table.insert(task.queue,{delay=dt,run=fn}) end
local function flush()
  local q=task.queue
  task.queue={}
  for _,item in ipairs(q) do item.run() end
end
local failures=0
local function warn(...) failures+=1 end
local match={phase="RESULTS",phaseUntil=5,winner="RED",reason="CAPTURE",alarm="WARNING"}
local modeVotes={}
local lastModeVote={}
local roundReady={}
local function getTeamName(p) return p.Team and p.Team.Name or "NONE" end
local function healthy(p)
  if p.alive and p.Parent==Players then return true,p.root,p.hum end
  return false,nil,nil
end
local function player(team,alive,spectator)
  local p={Parent=Players, Team=team and {Name=team},alive=alive,
    Character={},attempts=0,loads=0,failuresLeft=0,
    attrs={P0D_LateJoinSpectator=spectator},
    root={CFrame="BATTLE",AssemblyLinearVelocity="MOVE",AssemblyAngularVelocity="ROTATE"}}
  function p:GetAttribute(k) return self.attrs[k] end
  function p:LoadCharacter()
    self.attempts+=1
    if self.failuresLeft>0 then
      self.failuresLeft-=1
      error("TRANSIENT_RETRY")
    end
    self.loads+=1
    self.Character={}
    self.alive=true
    self.root.CFrame=LobbyIsland.spawn(getTeamName(self))
  end
  return p
end
local red=player("RED",true,false)
local blue=player("BLUE",false,false)
local spectator=player(nil,false,true)
Players.online={red,blue,spectator}
local function check(value,label)
  assert(value,"REAL_SOURCE_RECOVERY_NATIVE_FAILED_"..label)
end
'''
    cases=r'''
local function results(now)
'''+results+r'''
end
-- 01 / 02: result display must remain visible until expiry.
results(4)
check(match.phase=="RESULTS","WAIT_RESULTS")
check(#task.queue==0,"NO_EARLY_RESPAWN")
roundReady[red]=false;roundReady[blue]=false
results(5)
check(match.phase=="LOBBY","RESULTS_ENDS")
check(red.root.CFrame=="LOBBY_RED","ALIVE_TO_LOBBY")
check(red.root.AssemblyLinearVelocity=="ZERO" and red.root.AssemblyAngularVelocity=="ZERO",
      "ALIVE_ZERO_MOVEMENT")
check(#task.queue==2,"DEAD_AND_NEUTRAL_SCHEDULED")
check(blue.loads==0 and spectator.loads==0,"NO_IMMEDIATE_DOUBLE_RESTART")
check(task.queue[1].delay>=7,"ALLOW_ENGINE_AUTORESPAWN")
flush()
check(blue.loads==1 and spectator.loads==1,"BOTH_DEAD_LOADED")
check(blue.root.CFrame=="LOBBY_BLUE","TEAM_PHYSICAL_LOBBY")
check(not roundReady[red] and not roundReady[blue],"NO_FORCED_REMATCH")
check(match.winner=="" and match.reason=="","RESULT_CLEAR_METADATA")
-- Avoid duplicated scheduled requests, no second LoadCharacter.
blue.alive=false
scheduleLobbyRecovery(blue)
scheduleLobbyRecovery(blue)
check(#task.queue==1,"PENDING_ONE_ONLY")
flush()
check(blue.loads==2 and #task.queue==0,"SINGLE_RESTART_ONCE")
-- Roblox normal auto CharacterAdded beats manual fallback.
blue.alive=false
scheduleLobbyRecovery(blue)
local oldLoads=blue.loads
blue:LoadCharacter()
flush()
check(blue.loads==oldLoads+1 and not lobbyRecoveryPending[blue],
      "AUTO_REVIVE_WINS_WITHOUT_DUPLICATE")
-- Disconnected players are never reloaded.
blue.alive=false
scheduleLobbyRecovery(blue)
blue.Parent=nil
local n=blue.attempts
flush()
check(blue.attempts==n and not lobbyRecoveryPending[blue],"DISCONNECTED_SKIP")
blue.Parent=Players
-- Transient failures retry max twice; success on the third attempt.
blue.alive=false
blue.failuresLeft=2
scheduleLobbyRecovery(blue)
n=blue.attempts
flush()
check(blue.attempts==n+1 and #task.queue==1,"FIRST_LOAD_FAIL_RETRY")
check(task.queue[1].delay==2,"TWO_SECOND_RETRY")
flush()
check(blue.attempts==n+2 and #task.queue==1,"SECOND_LOAD_FAIL_RETRY")
flush()
check(blue.attempts==n+3 and blue.alive,"THIRD_LOAD_SUCCEEDS")
check(#task.queue==0 and not lobbyRecoveryPending[blue],"PENDING_RELEASED")
-- No manual reload if results ended and a new active game has begun.
blue.alive=false
scheduleLobbyRecovery(blue)
match.phase="ACTIVE"
n=blue.attempts
flush()
check(blue.attempts==n,"NO_REVIVE_DURING_NEXT_GAME")
match.phase="LOBBY"
-- If engine CharacterAutoLoads is disabled, use fast guarded recovery.
Players.CharacterAutoLoads=false
blue.alive=false
scheduleLobbyRecovery(blue)
check(task.queue[1].delay==.1,"AUTOLOADS_FALSE_FAST_RECOVERY")
flush()
check(blue.alive,"NO_AUTO_RESTART_MAKES_PROGRESS")
Players.CharacterAutoLoads=true
check(failures==2,"ONLY_TRANSIENT_RETRY_WARNINGS")
print("P0_PRIVATE78_RECOVERY_V2_REAL_GAME_26_NATIVE_CASES_PASS")
'''
    native=mock+"\n"+helper+"\n"+cases
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(native,"utf8")
    print("P0_PRIVATE78_RECOVERY_V2_REAL_GAME_SOURCE_EXTRACT_PASS")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    emit(a.dist,a.out)
