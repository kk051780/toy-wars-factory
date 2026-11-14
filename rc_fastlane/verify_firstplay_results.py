#!/usr/bin/env python3
"""Source-exact Game stopRound + RESULTS->LOBBY + real assignSpawn native Luau QA.

Includes bounded respawn failure/auto-respawn grace and late-join spectator
cases. No synthetic stopRound/LOBBY placement in the tests. Physical Roblox
Studio/Android performance remains NOT TESTED.
"""
from __future__ import annotations
import argparse
from pathlib import Path


def between(src: str, start: str, end: str, offset: int=0) -> str:
    i=src.index(start,offset)
    j=src.index(end,i+len(start))
    assert j>i
    return src[i:j]


def verify(dist: Path, output: Path):
    src=(dist/"src/server/Game.server.luau").read_text("utf8")
    assert src.count('local function stopRound(')==1
    assert src.count('local function assignSpawn(')==1
    assert src.count('local function tickRound()')==1
    assert src.count('remote.OnServerEvent:Connect(')==1

    stopper=between(src,'local function stopRound(',
                    '-- FB005: Bot requests are local SERVER callbacks')
    # A real stopRound function call, NOT a standalone copy of its READY
    # clearing statement: regression if that statement becomes unreachable.
    assert 'if match.phase ~= "ACTIVE" then return end' in stopper
    assert 'readyForMatch[participant] = false' in stopper
    assert 'match.phase = "RESULTS"' in stopper
    assert 'SoloTeamBots.stop()' in stopper
    assert 'broadcast()' in stopper

    spawning=between(src,'local function assignSpawn(player: Player, character: Model)',
                     '-- EGG RAID RUMBLE')
    assert 'root.CFrame = if RunService:IsStudio() and match.phase~="ACTIVE"' in spawning
    assert 'then LobbyIsland.spawn(team)' in spawning
    assert 'player:GetAttribute("P0D_LateJoinSpectator")==true' in spawning
    assert 'root.CFrame=LobbyIsland.spawn("RED")' in spawning
    assert 'hum.Died:Connect(' in spawning
    assert 'p:LoadCharacter()' in src
    assert 'player.CharacterAdded:Connect(function(character)' in src
    assert 'task.spawn(assignSpawn, player, character)' in src

    helper=between(src,'-- FB006: shared guarded post-results lobby character recovery.',
                   'local function tickRound()')
    assert helper.count('local function scheduleLobbyRecovery(')==1
    assert 'Players.CharacterAutoLoads' in helper
    assert 'Players.RespawnTime' in helper
    assert 'player.Character~=originalCharacter' in helper
    assert 'number < 3' in helper
    assert 'lobbyRecoveryPending[player]' in helper
    assert 'task.delay(' in helper

    tick=src.index('local function tickRound()')
    results=between(src,'elseif match.phase == "RESULTS" then',
                    '-- Recovery uses the existing server-only authoritative tick',tick)
    assert results.count('match.phase = "LOBBY"')==1
    assert 'if now >= match.phaseUntil then' in results
    assert 'root.CFrame=LobbyIsland.spawn(team)' in results
    assert 'scheduleLobbyRecovery(p)' in results
    assert 'p:GetAttribute("P0D_LateJoinSpectator")==true' in results
    assert 'match.winner = ""' in results and 'match.reason = ""' in results

    # A real late-join spectator's promotion into a team MUST call the same
    # recovery scheduler if dead. Test uses source structural proof of this.
    lobby=between(src,'if match.phase == "LOBBY" then',
                  'elseif match.phase == "COUNTDOWN" then',tick)
    assert 'scheduleLobbyRecovery(entrant)' in lobby
    assert 'readyForMatch[entrant]=false' in lobby

    results=results.replace('elseif match.phase == "RESULTS" then',
                            'if match.phase == "RESULTS" then',1)
    native=("\n".join([MOCK,stopper,spawning,helper,
            'local function realResultsStep(now)',results,'end',CASES]))
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(native,"utf8")
    print("P0D_FIRSTPLAY_RESULTS_REAL_STOP_SPAWN_RECOVERY_SOURCE_EXACT_PASS")
    print("P0D_FIRSTPLAY_RESULT_NATIVE_ACTUAL_SOURCE",output)


MOCK=r'''
--!nocheck
local Players={online={},CharacterAutoLoads=true,RespawnTime=5}
function Players:GetPlayers() return self.online end
local RunService={}
function RunService:IsStudio() return true end
local Vector3={zero="ZERO",new=function(...) return "VEC" end}
local LobbyIsland={spawn=function(team) return "LOBBY_"..team end}
local map={teams={RED={spawn="BATTLE_RED"},BLUE={spawn="BATTLE_BLUE"}}}
local Config={ResultsSeconds=3,RespawnInvulnerability=2,
  RoleHealth={RAIDER=100},RoleWalkSpeed={RAIDER=17}}
local warnings={}
local function warn(...)
  table.insert(warnings,{...})
end
local task={queue={}}
function task.delay(seconds,fn)
  table.insert(task.queue,{delay=seconds,run=fn})
end
local function flush()
  local due=task.queue
  task.queue={}
  for _,item in ipairs(due) do item.run() end
end
local match={phase="ACTIVE",phaseUntil=0,winner="",reason="",alarm="ACTIVE",
  alarmUntil=10}
local readyForMatch={}
local modeVotes={}
local lastModeVote={}
local roles={}
local invulnUntil={}
local earnedPower={}
local Power={endRound=function() end}
local SoloTeamBots={stop=function() end}
local horde={clear=function() end}
local rewardEvents=0
local broadcasts=0
local function serverNow() return 1 end
local function stopCanonical() end
local function settleProgressAtRealEnd() rewardEvents+=1 end
local function giveFreeHatchAtRealEnd() end
local function cleanupScout() end
local function setObjectiveEnabled() end
local function clearTraps() end
local function stopWind() end
local function dropEgg() end
local function restoreSlow() end
local function clearEarnedPowerVisual() end
local function broadcast() broadcasts+=1 end
local function getTeamName(p)
  return p.Team and p.Team.Name or "NONE"
end
local function healthy(p)
  if p.alive and p.Parent==Players then return true,p.root,p.hum end
  return false,nil,nil
end
local function check(value,desc)
  assert(value,"P0D_REAL_RESULTS_FAILED_"..desc)
end
local function makeModel()
  local root={CFrame="BATTLE",AssemblyLinearVelocity="MOVING",
              AssemblyAngularVelocity="SPINNING"}
  function root:IsA(cls) return cls=="BasePart" end
  local hum={MaxHealth=100,Health=100,WalkSpeed=10}
  function hum:IsA(cls) return cls=="Humanoid" end
  hum.Died={Connect=function() end}
  local ch={}
  function ch:WaitForChild(n)
    if n=="HumanoidRootPart" then return root end
    if n=="Humanoid" then return hum end
    return nil
  end
  return ch,root,hum
end
'''
CASES=r'''
local function makePlayer(team,alive,late)
  local ch,root,hum=makeModel()
  local p={Parent=Players,Team=team and {Name=team},Neutral=team==nil,
    Character=ch,root=root,hum=hum,alive=alive,loadCount=0,attempts=0,
    failuresLeft=0,attrs={P0D_LateJoinSpectator=late}}
  function p:GetAttribute(key) return self.attrs[key] end
  function p:SetAttribute(key,value) self.attrs[key]=value end
  function p:LoadCharacter()
    self.attempts+=1
    if self.failuresLeft>0 then
      self.failuresLeft-=1
      error("TRANSIENT_LOADCHARACTER_FAULT")
    end
    self.loadCount+=1
    local c,r,h=makeModel()
    self.Character=c
    self.root=r
    self.hum=h
    self.alive=true
    -- Invoke EXACT real Game assignSpawn from CharacterAdded mock.
    assignSpawn(self,c)
  end
  return p
end

-- A normal real Game stopRound clears READY BEFORE RESULTS, and is
-- inoperative when called again while phase is no longer ACTIVE.
local red=makePlayer("RED",true,false)
local blue=makePlayer("BLUE",false,false)
local spectator=makePlayer(nil,false,true)
Players.online={red,blue,spectator}
readyForMatch[red]=true;readyForMatch[blue]=true
readyForMatch[spectator]=true
stopRound("RED","CAPTURE")
check(match.phase=="RESULTS","STOP_TO_RESULTS")
check(match.phaseUntil==4,"RESULTS_END_TIME")
check(not readyForMatch[red] and not readyForMatch[blue]
 and not readyForMatch[spectator],"REAL_STOP_CLEARS_ALL_READY")
check(rewardEvents==1 and broadcasts==1,"STOP_SINGLE_SETTLEMENT")
stopRound("BLUE","INVALID_REPEAT")
check(match.winner=="RED" and rewardEvents==1 and broadcasts==1,
  "STOP_NOT_REENTERED")
realResultsStep(3)
check(match.phase=="RESULTS" and #task.queue==0,"RESULTS_HOLD_UNTIL_DEADLINE")
realResultsStep(4)
check(match.phase=="LOBBY","RESULTS_TO_LOBBY")
check(red.root.CFrame=="LOBBY_RED","ALIVE_TEAM_TO_LOBBY")
check(red.root.AssemblyLinearVelocity=="ZERO"
 and red.root.AssemblyAngularVelocity=="ZERO","LOBBY_MOTION_ZERO")
check(#task.queue==2,"DEAD_TEAM_AND_SPECTATOR_SCHEDULED")
check(blue.loadCount==0 and spectator.loadCount==0,
 "DEAD_NOT_IMMEDIATE_DUPLICATE_RELOAD")
check(task.queue[1].delay>=7,"AUTO_RESPAWN_GRACE")
flush()
check(blue.loadCount==1 and blue.root.CFrame=="LOBBY_BLUE",
 "DEAD_BOT_TEAM_REAL_CHARADDED_SPAWN")
check(spectator.loadCount==1 and spectator.root.CFrame=="LOBBY_RED",
 "DEAD_SPECTATOR_REAL_CHARADDED_SPAWN")
check(match.winner=="" and match.reason=="" and match.alarm=="IDLE",
 "RESULT_METADATA_RESET")
check(not readyForMatch[red] and not readyForMatch[blue],
 "RESULTS_NOT_FORCED_RESTART")
-- Auto-respawn wins if it changes the Character before our fallback task;
-- exactly one LoadCharacter invocation remains.
match.phase="LOBBY"
blue.alive=false
scheduleLobbyRecovery(blue)
blue:LoadCharacter()
local n=blue.loadCount
flush()
check(blue.loadCount==n and not lobbyRecoveryPending[blue],
 "AUTO_RESPAWN_WINS_NO_DOUBLE_LOAD")
-- Disconnect while waiting: no forced character load after exit.
blue.alive=false
scheduleLobbyRecovery(blue)
blue.Parent=nil
local before=blue.attempts
flush()
check(blue.attempts==before and not lobbyRecoveryPending[blue],
 "LEAVER_NEVER_RELOADED")
blue.Parent=Players
-- A transient LoadCharacter failure is retried twice (max 3 attempts).
blue.alive=false
blue.failuresLeft=2
scheduleLobbyRecovery(blue)
local a=blue.attempts
flush()
check(blue.attempts==a+1 and #task.queue==1,
 "RECOVERY_FIRST_FAILURE_RETRIES")
check(task.queue[1].delay==2,"RECOVERY_RETRY_BOUNDED_DELAY")
flush()
check(blue.attempts==a+2 and #task.queue==1,
 "RECOVERY_SECOND_FAILURE_RETRIES")
flush()
check(blue.attempts==a+3 and blue.alive
 and blue.root.CFrame=="LOBBY_BLUE",
 "RECOVERY_THIRD_ATTEMPT_SUCCESS")
check(#task.queue==0 and not lobbyRecoveryPending[blue],
 "RETRY_FINITE_QUEUE")
-- Never revive a player in a new ACTIVE phase, even after a pending task.
blue.alive=false
scheduleLobbyRecovery(blue)
match.phase="ACTIVE"
local latest=blue.attempts
flush()
check(blue.attempts==latest and not lobbyRecoveryPending[blue],
 "MATCH_CHANGED_ABORTS_RELOAD")
check(#warnings==2,"ONLY_TRANSIENT_RETRY_WARNINGS")
print("P0D_FIRSTPLAY_ACTUAL_RESULTS_LOBBY_24_NATIVE_CASES_PASS")
'''
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    verify(args.dist,args.out)
