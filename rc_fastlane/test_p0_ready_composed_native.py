#!/usr/bin/env python3
"""Execute the authored READY/COUNTDOWN/RESULTS slices from the COMPOSED Game.

Runs genuine extracted Luau functions and phase-machine branch in native Luau;
mocks only Roblox players/remote/time. NOT a real Roblox Studio test.
"""
import argparse, re
from pathlib import Path

def unique_function(src, header):
    assert src.count(header)==1,("SOURCE_DRIFT",header,src.count(header))
    text=src.split(header,1)[1]
    end=re.search(r"(?m)^end\s*$",text)
    assert end,("FUNCTION_END_MISSING",header)
    return header+text[:end.end()]

def generate(game):
    src=game.read_text("utf8")
    ready=unique_function(src,"local function everybodyReady(): boolean")
    apply=unique_function(src,"local function applyReady(player: Player, data)")
    assert "broadcast()" in apply
    assert apply.index('match.phase ~= "LOBBY"') < apply.index('lastSeq[player] = data.seq')
    needle='for _, player in ipairs(Players:GetPlayers()) do roundReady[player] = false end'
    assert src.count(needle)==1,("RESULTS_RESET_MISSING",src.count(needle))
    tick=src.split("local function tickRound()",1)
    assert len(tick)==2
    m=re.search(r'(?m)^    if match.phase == "LOBBY" then$',tick[1])
    n=re.search(r'(?m)^    elseif match.phase == "ACTIVE" then$',tick[1])
    assert m and n and n.start()>m.end(), "COMPOSED_ROUND_PHASE_DRIFT"
    branch=tick[1][m.start():n.start()]
    assert "everybodyReady()" in branch
    assert "StudioSolo.canStart(" in branch
    assert 'match.phase = "LOBBY"' in branch
    assert "broadcast()" in branch

    return "\n".join([r'''-- Native Luau regression of exact authored Game phase and READY logic.
local player={Name="SoloTester"}
local online={player}
local Players={}
function Players:GetPlayers() return online end
local RunService={}
function RunService:IsStudio() return true end
local StudioSolo={}
function StudioSolo.canStart(studio,count,red,blue,min)
    -- Externally proven solo policy, tested in the original StudioSolo module.
    return studio and count==1 or count>=min and red>0 and blue>0
end
local Config={IntermissionSeconds=4,MinPlayers=2}
local match={phase="LOBBY",phaseUntil=0}
local roundReady={}
local lastSeq={}
local Rules={}
function Rules.validSeq(seq,last)
    return type(seq)=="number" and seq>last and seq<=100000000
end
local broadcasts=0
local function broadcast() broadcasts+=1 end
local function teamCount(team)
    return team=="RED" and #online or 0
end
local function rebalanceLobbyTeams() end
local function resetRound()
    match.phase="ACTIVE"
end
''',ready,apply,
r'''local function tickPhase(now)
    local count=#Players:GetPlayers()
''',branch,
r'''    end
end

local function finishRound()
    match.phase="RESULTS"
''',needle,r'''end

-- FIRST: no user opt-in means NO automatic countdown, even in solo Studio.
tickPhase(10)
assert(match.phase=="LOBBY" and broadcasts==0,"AUTO_START_WITHOUT_READY")

-- SECOND: consent begins countdown, then rapid reversal cancels instantly.
applyReady(player,{action="READY",ready=true,seq=1})
assert(roundReady[player] and broadcasts==1,"READY_NOT_ACCEPTED")
tickPhase(11)
assert(match.phase=="COUNTDOWN","OPT_IN_DID_NOT_START_COUNTDOWN")
local old=broadcasts
applyReady(player,{action="READY",ready=false,seq=2})
assert(match.phase=="LOBBY" and roundReady[player]==false,"CANCEL_DID_NOT_REVOKE")
assert(broadcasts>old,"CANCEL_NOT_BROADCAST_TO_ALL")
tickPhase(17)
assert(match.phase=="LOBBY","RESTART_AFTER_CANCEL")

-- THIRD: a new consent starts and enters real match.
applyReady(player,{action="READY",ready=true,seq=3})
tickPhase(20)
assert(match.phase=="COUNTDOWN","SECOND_READY_NOT_ACCEPTED")
tickPhase(25)
assert(match.phase=="ACTIVE","MATCH_DID_NOT_START_ON_COUNTDOWN")

-- FOURTH: READY in ACTIVE must NOT burn combat seq used for ATTACK.
applyReady(player,{action="READY",ready=false,seq=999999})
assert(lastSeq[player]==3,"ACTIVE_READY_POISONED_COMBAT_SEQ")
assert(Rules.validSeq(4,lastSeq[player]),"COMBAT_INPUT_BLOCKED")

-- FIFTH: game must never auto-rematch after results/return to lobby.
finishRound()
assert(not roundReady[player] and match.phase=="RESULTS","RESULTS_NOT_RESET_READY")
match.phase="LOBBY"
tickPhase(40)
assert(match.phase=="LOBBY","AUTO_REMATCH_WITHOUT_NEW_CONSENT")

-- SIXTH: invalid late opt-in during countdown cannot burn seq.
applyReady(player,{action="READY",ready=true,seq=5})
tickPhase(41)
assert(match.phase=="COUNTDOWN","READY_TO_COUNTDOWN_FAILED")
local before=lastSeq[player]
applyReady(player,{action="READY",ready=true,seq=999998})
assert(lastSeq[player]==before,"COUNTDOWN_LATE_READY_CONSUMED_SEQ")
print("P0_COMPOSED_READY_NATIVE_6_SCENARIOS_PASS")
'''])

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--game",type=Path,required=True)
    p.add_argument("--emit",type=Path,required=True)
    a=p.parse_args()
    content=generate(a.game)
    a.emit.write_text(content,"utf8")
    print("P0_COMPOSED_READY_NATIVE_SOURCE_EXTRACT_PASS",len(content))
