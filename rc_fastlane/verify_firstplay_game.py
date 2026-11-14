#!/usr/bin/env python3
"""Exercise the *actual composed* firstplay73 READY+COUNTDOWN branch with Luau.

Do not independently retype Game transition logic: extract it from real source
after all three authored patches + QA, bind minimal mocks, compile & execute
with pinned native Luau. Also assert original ACTIVE LoadCharacter spawn and
exact 370x294 castle recovery, separate-lobby/latejoin, single Game authority.
This is native unit QA, NOT real Studio/physics/OWNER FUN.
"""
from __future__ import annotations
import argparse
from pathlib import Path

def extract(src: str, a: str, b: str, offset: int = 0) -> str:
    i=src.index(a,offset)
    j=src.index(b,i+len(a))
    assert j>i
    return src[i:j]

def verify(dist: Path, output: Path) -> None:
    game=(dist/"src/server/Game.server.luau").read_text(encoding="utf8")
    bot=(dist/"src/server/SoloTeamBots.luau").read_text(encoding="utf8")
    proj=(dist/"default.project.json").read_text(encoding="utf8")
    assert game.count('remote.OnServerEvent:Connect(')==1
    assert game.count('local function tickRound()')==1
    assert game.count('local function resetRound()')==1
    assert 'local function allPlayersReadyForRound(): boolean' in game
    assert 'local readyForMatch: {[Player]: boolean} = {}' in game

    # Exact real transition. Changes to authored ready function or gating
    # naturally change or fail the executed native harness below.
    start=game.index('local function tickRound()')
    pregame=extract(game,'local function allPlayersReadyForRound(): boolean',
                    'local function tickRound()',0)
    branch=extract(game,'if match.phase == "LOBBY" then',
                   'elseif match.phase == "ACTIVE" then',start)
    toggle=extract(game,'local function toggleMatchReady(player: Player, data)',
                   'remote.OnServerEvent:Connect(')
    hud=(dist/"src/client/HUD.client.luau").read_text("utf8")
    assert 's.phase == "COUNTDOWN" and s.ready == true' in hud
    assert 'readyButton.Visible = s.phase == "LOBBY"' in hud
    assert '出撃中止' in hud
    assert toggle.index('if match.phase ~= "LOBBY"') < toggle.index('lastSeq[player] = data.seq')
    assert 'match.phaseUntil=0' in toggle
    assert 'broadcast()' in toggle

    assert 'if allPlayersReadyForRound() then' in branch
    assert 'if not allPlayersReadyForRound() then' in branch
    assert 'readyForMatch[entrant]=false' in branch
    assert 'rebalanceLobbyTeams()' in branch

    reset=extract(game,'local function resetRound()','local function chooseTeam(')
    assert reset.index('match.phase = "ACTIVE"') < reset.index('p:LoadCharacter()')
    assert reset.count('p:LoadCharacter()')==1
    spawn=extract(game,'local function assignSpawn(player: Player, character: Model)',
                  '-- EGG RAID RUMBLE')
    assert 'match.phase~="ACTIVE"' in spawn
    assert 'else map.teams[team].spawn + Vector3.new(0, 2, 0)' in spawn
    assert 'player:GetAttribute("P0D_LateJoinSpectator")==true' in spawn
    lobby=extract(game,'local function rebalanceLobbyTeams()',
                  'local function assignSpawn(')
    assert 'then LobbyIsland.spawn(move.to)' in lobby
    onjoin=extract(game,'local function onJoin(player: Player)',
                   'Players.PlayerAdded:Connect(onJoin)')
    assert 'player.Team=nil' in onjoin and 'player.Neutral=true' in onjoin
    assert 'player:SetAttribute("P0D_LateJoinSpectator",true)' in onjoin
    assert 'root.CFrame=LobbyIsland.spawn(getTeamName(entrant))' in branch
    assert 'math.abs(position.X) > 182 or math.abs(position.Z) > 145' in game
    assert 'math.abs(position.X) > 130 or math.abs(position.Z) > 76' not in game
    assert 'not LobbyIsland.inLobby(position)' in game
    assert 'not SoloTeamBots.isActive()' in game
    assert 'stopRound("DRAW","SOLO_BOTS_RUNTIME_FAILURE")' in game
    assert 'if eligible~=1 then Bot.stop();return end' in bot
    assert 'params.FilterDescendantsInstances={attackerCharacter}' in bot
    assert 'if hit and hit.Instance:IsDescendantOf(bot.model) then' in bot
    assert 'MAX_INFLIGHT_PATHS=10' in bot
    assert 'PATH_TIMEOUT_SECONDS=8' in bot
    assert 'Bot.stop()' in bot
    assert 'StarterPlayerScripts' in proj

    native=StringRawNativeHead+"\n"+pregame+"\n"+toggle+"\n"+StringRawNativeMiddle+"\n"+branch+"\n"+StringRawNativeTail
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(native,encoding="utf8")
    print("P0D_FIRSTPLAY_COMPOSED_GAME_REAL_SOURCE_P0P1_ASSERTIONS_PASS")
    print("P0D_FIRSTPLAY_NATIVE_READY_HARNESS_FROM_ACTUAL_GAME",output)


StringRawNativeHead=r'''
--!nocheck
-- ONLY mocks the public Roblox services. The READY and countdown functions
-- below are extracted byte-identically from the ACTUAL 73-source Game.
local Players={online={}}
function Players:GetPlayers() return self.online end
local RunService={}
function RunService:IsStudio() return true end
local Config={MinPlayers=2,IntermissionSeconds=2}
local readyForMatch={}
local lastSeq={}
local Rules={}
function Rules.validSeq(seq,last)
  return type(seq)=="number" and seq>last and seq<=last+99999
end
local broadcastCount=0
local function broadcast() broadcastCount+=1 end
local match={phase="LOBBY",phaseUntil=0}
local function teamCount(side)
  local n=0
  for _,p in ipairs(Players:GetPlayers()) do
    if p.Team and p.Team.Name==side then n+=1 end
  end
  return n
end
local function rebalanceLobbyTeams() end
local function chooseTeam(p)
  local team=if teamCount("RED")<=teamCount("BLUE") then "RED" else "BLUE"
  p.Team={Name=team}
end
local function getTeamName(p) return p.Team and p.Team.Name or "NONE" end
local function healthy(p) return false,nil end
local LobbyIsland={spawn=function(side) return side end}
local resetCount=0
local function resetRound()
  resetCount+=1
  match.phase="ACTIVE"
end
local function makeP(team)
  local p={Team={Name=team},ready=false,attrs={}}
  function p:GetAttribute(key) return self.attrs[key] end
  function p:SetAttribute(key,value) self.attrs[key]=value end
  return p
end
local p1=makeP("RED")
local p2=makeP("BLUE")
'''
StringRawNativeMiddle=r'''
local function tickRealReadyTransition(now)
  local count=#Players:GetPlayers()
'''
StringRawNativeTail=r'''
end
end
local function reset()
  match.phase="LOBBY"
  match.phaseUntil=0
  readyForMatch[p1]=false
  readyForMatch[p2]=false
end
local function check(condition,name)
  assert(condition,"ACTUAL_GAME_READY_NATIVE_CASE_FAILED_"..name)
end
Players.online={}
reset()
tickRealReadyTransition(0)
check(match.phase=="LOBBY","EMPTY_LOBBY_NOT_START")
Players.online={p1}
reset()
tickRealReadyTransition(1)
check(match.phase=="LOBBY","SOLO_UNREADY_NO_AUTOSTART")
readyForMatch[p1]=true
tickRealReadyTransition(2)
check(match.phase=="COUNTDOWN","SOLO_OPT_IN_COUNTS")
readyForMatch[p1]=false
tickRealReadyTransition(3)
check(match.phase=="LOBBY","SOLO_CANCEL_COUNTDOWN")
readyForMatch[p1]=true
tickRealReadyTransition(4)
check(match.phase=="COUNTDOWN","SOLO_REARMED_COUNTDOWN")
tickRealReadyTransition(7)
check(match.phase=="ACTIVE" and resetCount==1,"SOLO_TRUE_READY_START")
Players.online={p1,p2}
reset()
readyForMatch[p1]=true
tickRealReadyTransition(10)
check(match.phase=="LOBBY","TEAMMATE_UNREADY_NO_START")
readyForMatch[p2]=true
tickRealReadyTransition(11)
check(match.phase=="COUNTDOWN","BOTH_READY_START_COUNTDOWN")
readyForMatch[p2]=false
tickRealReadyTransition(12)
check(match.phase=="LOBBY","TWO_CLIENT_COUNTDOWN_CANCEL")
readyForMatch[p2]=true
tickRealReadyTransition(13)
check(match.phase=="COUNTDOWN","TWO_CLIENT_REARMED")
tickRealReadyTransition(16)
check(match.phase=="ACTIVE" and resetCount==2,"TWO_CLIENT_START")
print("P0D_FIRSTPLAY_ACTUAL_GAME_READY_10_NATIVE_BEHAVIOR_CASES_PASS")
Players.online={p1}
reset()
lastSeq[p1]=0
local countBefore=broadcastCount
toggleMatchReady(p1,{action="READY_TOGGLE",seq=1})
check(readyForMatch[p1]==true and lastSeq[p1]==1,"INPUT_SOLO_READY_ACCEPTED")
tickRealReadyTransition(18)
check(match.phase=="COUNTDOWN","INPUT_SOLO_STARTED_COUNTDOWN")
toggleMatchReady(p1,{action="READY_TOGGLE",seq=2})
check(match.phase=="LOBBY" and readyForMatch[p1]==false,"INPUT_SOLO_CANCEL_IMMEDIATELY")
check(match.phaseUntil==0,"INPUT_SOLO_CANCEL_CLEAR_TIMER")
check(broadcastCount==countBefore+2,"INPUT_SOLO_CANCEL_BROADCAST")
local previousSeq=lastSeq[p1]
match.phase="ACTIVE"
toggleMatchReady(p1,{action="READY_TOGGLE",seq=9000})
check(lastSeq[p1]==previousSeq,"INPUT_ACTIVE_READY_CANNOT_POISON_ATTACK_SEQ")
check(broadcastCount==countBefore+2,"INPUT_ACTIVE_READY_NO_BROADCAST")
Players.online={p1,p2}
reset()
lastSeq[p2]=0
readyForMatch[p1]=true
local previousPeerBroadcast=broadcastCount
toggleMatchReady(p2,{action="READY_TOGGLE",seq=1})
check(readyForMatch[p2]==true,"INPUT_TWO_PLAYER_READY")
tickRealReadyTransition(22)
check(match.phase=="COUNTDOWN","INPUT_TWO_PLAYER_COUNTDOWN")
toggleMatchReady(p2,{action="READY_TOGGLE",seq=2})
check(match.phase=="LOBBY" and not readyForMatch[p2],"INPUT_TWO_PLAYER_CANCEL_IMMEDIATE")
check(broadcastCount==previousPeerBroadcast+2,"INPUT_TWO_PLAYER_CANCEL_NOTIFIES_PEER")
print("P0D_FIRSTPLAY_ACTUAL_GAME_READY_INPUT_11_NATIVE_CASES_PASS")
'''

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    verify(args.dist,args.out)
