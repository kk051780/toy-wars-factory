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

from test_p0_ready_composed_native import unique_function


def verify(dist: Path, output: Path, active_rich51=False) -> None:
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
    assert 'p:LoadCharacter()' in results
    assert 'P0D_LOBBY_RESPAWN_FAIL' in results
    assert 'modeVotes' in results and 'lastModeVote' in results
    assert 'match.winner = ""' in results and 'match.reason = ""' in results
    if active_rich51:
        assert 'root.CFrame=map.teams[team].spawn + Vector3.new(0, 2, 0)' in results
        assert 'p.Parent == Players and match.phase == "LOBBY" and match.serial == endedRound' in results
        assert 'lobbyRecoveryRound[p] = endedRound' in results and 'local currentTeam = getTeamName(p)' in results
        assert 'root.CFrame = map.teams[team].spawn + Vector3.new(0, 2, 0)' in src
    else:
        assert 'root.CFrame=LobbyIsland.spawn(team)' in results
        assert 'if not refreshed then' in results and 'p.Parent~=Players or match.phase~="LOBBY"' in results
        assert 'RunService:IsStudio()' in results
    assert len(results)<3000, "RESULTS_BRANCH_UNEXPECTEDLY_LARGE"
    # The 'elseif' comes from the real tick phase switch; new wrapper provides
    # if and a test clock while preserving the EXACT inner match transitions.
    result_function=results.replace(
        'elseif match.phase == "RESULTS" then',
        'if match.phase == "RESULTS" then',1)
    mock = MOCK
    cases = CASES
    if active_rich51:
        mock = mock.replace('local Vector3={zero="ZERO"}', 'local Vector3={zero="ZERO"}\nfunction Vector3.new() return 0 end')
        mock = mock.replace('local scheduled={}', '''local map={teams={}}
for _,team in ipairs({"RED","BLUE"}) do
  map.teams[team]={spawn=setmetatable({team=team},{__add=function(a) return "LOBBY_"..a.team end})}
end
local scheduled={}''')
        mock = mock.replace("local roundReady={}", "local roundReady={}\nlocal lobbyRecoveryRound={}\nmatch.serial=0")
        cases = cases.replace("P0_PRIVATE78_REAL_RESULTS_LOBBY_15_NATIVE_CASES_PASS",
                              "P0_RICH51_RESULTS_LOBBY_15_NATIVE_CASES_PASS") + ACTIVE_CASES + ready_during_load(src)
    native=(mock+"\nlocal function realRevokeReady()\n"+
            clear.group(0)+"\nend\n"+
            "local function realResultsStep(now)\n"+result_function+"\nend\n"+
            cases)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(native,"utf8")
    label = "P0_RICH51" if active_rich51 else "P0_PRIVATE78"
    print(label + "_RESULTS_REAL_GAME_SOURCE_LOCK_PASS", len(results))

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
ACTIVE_CASES=r'''
match.phase="RESULTS"; match.phaseUntil=12;match.serial=4
blue.alive=false
realResultsStep(12)
match.serial=5
flush()
check(blue.loadCount==1,"STALE_MATCH_DOES_NOT_RESPAWN")
match.phase="RESULTS";match.phaseUntil=13
realResultsStep(13)
blue.Team=nil
flush()
check(blue.loadCount==1,"NEW_OBSERVER_DOES_NOT_RESPAWN")
print("ACTIVE_RESULTS_ROUND_AND_TEAM_FENCE_PASS")
'''


def ready_during_load(src):
    eligible = unique_function(src, "local function eligibleSoloPlayers(): {Player}")
    everybody = unique_function(src, "local function everybodyReady(): boolean")
    ready = unique_function(src, "local function applyReady(player: Player, data)")
    hook = "remote.OnServerEvent:Connect(function(player: Player, data)"
    assert src.count(hook) == 1
    dispatch = hook + src.split(hook, 1)[1].split("\nend)", 1)[0] + "\nend)"
    counted = "    local count = #eligibleSoloPlayers()"
    assert src.count(counted) == 1
    phase = counted + src.split(counted, 1)[1].split('    elseif match.phase == "ACTIVE" then', 1)[0]
    return "\n".join((r'''
Players.online={red,blue}
local lastSeq={}
local Rules={validSeq=function(seq,last) return type(seq)=="number" and seq>last end}
local function broadcast() end
local function getAttribute() return nil end
red.GetAttribute=getAttribute
blue.GetAttribute=getAttribute
local function teamCount() return 1 end
local function rebalanceLobbyTeams() end
local StudioSolo={canStart=function(_,count,r,b,m) return count>=m and r>0 and b>0 end}
local Config={MinPlayers=2,IntermissionSeconds=7}
local starts=0
local function resetRound() starts+=1 match.phase="ACTIVE" end
local requestReady
local remote={OnServerEvent={}}
function remote.OnServerEvent:Connect(handler) requestReady=handler end
''', eligible, everybody, ready, dispatch, "local function advance(now)", phase, "    end\nend", r'''
blue.Team={Name="BLUE"}
blue.alive=false
function blue:LoadCharacter()
    coroutine.yield()
    self.loadCount+=1
    self.alive=true
end
match.phase="RESULTS";match.phaseUntil=20;match.serial=6
realRevokeReady()
realResultsStep(20)
check(#scheduled==1 and lobbyRecoveryRound[blue]==6,"RESULTS_RESPAWN_PENDING")
local worker=coroutine.create(table.remove(scheduled,1))
check(coroutine.resume(worker) and coroutine.status(worker)=="suspended","RESULTS_RESPAWN_IN_FLIGHT")
requestReady(red,{action="READY",ready=true,seq=1})
requestReady(blue,{action="READY",ready=true,seq=1})
check(lastSeq[blue]==nil and not roundReady[blue],"PENDING_READY_MUST_KEEP_INPUT_SEQ")
roundReady[blue]=true
advance(21)
check(match.phase=="LOBBY" and starts==0,"PENDING_MUST_BLOCK_MATCH_START")
match.phase="COUNTDOWN";match.phaseUntil=22
advance(22)
check(match.phase=="LOBBY" and starts==0,"PENDING_MUST_BLOCK_COUNTDOWN_COMPLETION")
match.phase="COUNTDOWN"
requestReady(blue,{action="READY",ready=false,seq=1})
check(lastSeq[blue]==1 and not roundReady[blue] and match.phase=="LOBBY","PENDING_READY_MUST_ALLOW_CANCEL")
check(coroutine.resume(worker) and coroutine.status(worker)=="dead" and blue.alive
    and lobbyRecoveryRound[blue]==nil,"RESULTS_RESPAWN_MUST_RELEASE_FENCE")
requestReady(blue,{action="READY",ready=true,seq=2})
advance(23);advance(30)
check(lastSeq[blue]==2 and starts==1 and match.phase=="ACTIVE","READY_AFTER_RECOVERY_MUST_ALLOW_MATCH")
print("ACTIVE_RESULTS_IN_FLIGHT_READY_AND_COUNTDOWN_PASS")
'''))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--active-rich51",action="store_true")
    args=p.parse_args()
    verify(args.dist,args.out,args.active_rich51)
