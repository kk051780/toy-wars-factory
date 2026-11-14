#!/usr/bin/env python3
"""Execute REAL combined firstplay73 RESULTS->LOBBY source in native Luau.

The code under test comes from Game.server.luau after all authored adapters
and this P0 recovery fix; no fabricated Game results branch is tested.
Roblox engine physical behavior is NOT simulated: client/physics remains NO_GO.
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path

def verify(dist: Path, output: Path) -> None:
    src=(dist/"src/server/Game.server.luau").read_text("utf8")
    assert src.count('local function stopRound(')==1
    assert src.count('local function resetRound()')==1
    assert src.count('local function tickRound()')==1
    assert src.count('remote.OnServerEvent:Connect(')==1
    start=src.index('local function stopRound(')
    reset=src.index('local function resetRound()',start)
    stopper=src[start:reset]
    clear=re.search(
        r'for _, player in ipairs\(Players:GetPlayers\(\)\) do\s+'
        r'roundReady\[player\] = false\s+end',stopper)
    assert clear, "REAL_STOP_ROUND_DOES_NOT_REVOKE_ALL_READY"
    tick=src.index('local function tickRound()')
    a=src.index('elseif match.phase == "RESULTS" then',tick)
    b=src.index('-- Recovery uses the existing server-only authoritative tick',a)
    results=src[a:b]
    assert results.count('match.phase = "LOBBY"')==1
    assert 'if now >= match.phaseUntil then' in results
    assert 'root.CFrame=LobbyIsland.spawn(team)' in results
    assert 'if not refreshed then' in results
    assert 'p:LoadCharacter()' in results
    assert 'p.Parent~=Players or match.phase~="LOBBY"' in results
    assert 'P0D_LOBBY_RESPAWN_FAIL' in results
    assert 'modeVotes' in results and 'lastModeVote' in results
    assert 'match.winner = ""' in results and 'match.reason = ""' in results
    assert 'RunService:IsStudio()' in results
    assert len(results)<3000, "RESULTS_BRANCH_UNEXPECTEDLY_LARGE"
    # The 'elseif' comes from the real tick phase switch; new wrapper provides
    # if and a test clock while preserving the EXACT inner match transitions.
    result_function=results.replace(
        'elseif match.phase == "RESULTS" then',
        'if match.phase == "RESULTS" then',1)
    native=(MOCK+"\nlocal function realRevokeReady()\n"+
            clear.group(0)+"\nend\n"+
            "local function realResultsStep(now)\n"+result_function+"\nend\n"+
            CASES)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(native,"utf8")
    print("P0_PRIVATE78_RESULTS_REAL_GAME_SOURCE_LOCK_PASS",len(results))

MOCK=r'''
--!nocheck
local Players={online={}}
function Players:GetPlayers() return self.online end
local RunService={}
function RunService:IsStudio() return true end
local Vector3={zero="ZERO"}
local LobbyIsland={}
function LobbyIsland.spawn(team) return "LOBBY_"..team end
local scheduled={}
local task={}
function task.defer(f) table.insert(scheduled,f) end
local function flush()
  local copy=scheduled
  scheduled={}
  for _,f in ipairs(copy) do f() end
end
local warnings=0
function warn(...) warnings+=1 end
local modeVotes={}
local lastModeVote={}
local match={phase="ACTIVE",phaseUntil=5,winner="BLUE",reason="CAPTURE",alarm="ALARM"}
local roundReady={}
local function getTeamName(p) return p.Team and p.Team.Name or "NONE" end
local function healthy(p)
  if p.alive then return true,p.root,{Health=100} end
  return false,nil,nil
end
local function makePlayer(team,alive)
  local p={Team=team and {Name=team},Parent=Players,alive=alive,loadCount=0}
  p.root={CFrame="BATTLE",AssemblyLinearVelocity="MOVE",AssemblyAngularVelocity="ROTATE"}
  function p:LoadCharacter()
    self.loadCount+=1
    self.alive=true
    self.root.CFrame=LobbyIsland.spawn(getTeamName(self))
  end
  return p
end
local red=makePlayer("RED",true)
local blue=makePlayer("BLUE",false)
local neutral=makePlayer(nil,true)
local function check(x,name)
  assert(x,"RESULTS_REAL_CODE_NATIVE_FAILED_"..name)
end
'''
CASES=r'''
Players.online={red,blue,neutral}
roundReady[red]=true
roundReady[blue]=true
roundReady[neutral]=true
realRevokeReady()
check(not roundReady[red] and not roundReady[blue]
  and not roundReady[neutral],"ALL_READY_REVOKED_AT_REAL_STOP")
realResultsStep(4)
check(match.phase=="ACTIVE","NOT_REAL_RESULTS_NO_CLOBBER")
match.phase="RESULTS"
realResultsStep(4)
check(match.phase=="RESULTS" and red.root.CFrame=="BATTLE",
  "RESULTS_DISPLAY_UNTIL_DEADLINE")
check(#scheduled==0,"NO_EARLY_DEAD_RESPAWN")
realResultsStep(5)
check(match.phase=="LOBBY","TIMEOUT_RETURNS_TO_LOBBY")
check(red.root.CFrame=="LOBBY_RED","ALIVE_REAL_LOBBY_TELEPORT")
check(red.root.AssemblyLinearVelocity=="ZERO"
    and red.root.AssemblyAngularVelocity=="ZERO","LOBBY_ZERO_INERTIA")
check(blue.loadCount==0 and #scheduled==1,"DEAD_RECOVERY_DEFERRED")
check(neutral.root.CFrame=="BATTLE","SPECTATOR_NOT_BATTLE_TELEPORTED")
check(match.winner=="" and match.reason=="" and match.alarm=="IDLE",
  "RESULTS_WINNER_REASON_ALARM_CLEARED")
flush()
check(blue.loadCount==1 and blue.root.CFrame=="LOBBY_BLUE",
  "DEAD_RECHARACTERIZE_TO_LOBBY")
check(not roundReady[red] and not roundReady[blue],
  "NEXT_MATCH_NOT_FORCED_READY")
-- A disconnected player must never be forcibly respawned after leave.
match.phase="RESULTS";match.phaseUntil=8
blue.alive=false
realResultsStep(8)
blue.Parent=nil
flush()
check(blue.loadCount==1,"LEAVER_NO_LATE_RESPAWN")
-- A normal Roblox auto-respawn between scheduling and callback wins the race.
blue.Parent=Players
match.phase="RESULTS";match.phaseUntil=9
blue.alive=false
realResultsStep(9)
blue.alive=true
flush()
check(blue.loadCount==1,"AUTO_RESPAWN_NOT_DUPLICATED")
check(warnings==0,"NO_FORCED_STUDIO_WARNINGS")
print("P0_PRIVATE78_REAL_RESULTS_LOBBY_15_NATIVE_CASES_PASS")
'''
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    verify(args.dist,args.out)
