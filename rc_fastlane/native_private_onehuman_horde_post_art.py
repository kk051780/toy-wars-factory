#!/usr/bin/env python3
"""Generate native Luau tests from the REAL source of Game + original StudioSolo.

Uses exact authored ready roster and policies and exact Game calls, verifying
private 1 human can READY->COUNTDOWN and play original neutral Horde. No Roblox
engine is executed; this is deterministic native Luau SOURCE contract only.
"""
from __future__ import annotations
import argparse,re
from pathlib import Path
from apply_private_onehuman_horde_post_art import (
  GAME,SOLO,GAME_PIN,SOLO_PIN,OWNER_ATTR,NEW_DECL,
  NEW_LATCH,NEW_START,NEW_EMPTY,blob
)

CAN=re.compile(
  r'StudioSolo\.canStart\(RunService:IsStudio\(\) or privateHordeTrialAllowed\(\), count,\s+'
  r'teamCount\("RED"\), teamCount\("BLUE"\), Config.MinPlayers\)'
)
LATCH=re.compile(
  r'StudioSolo\.isSoloRound\(RunService:IsStudio\(\) or privateHordeTrialAllowed\(\),\s+'
  r'#Players:GetPlayers\(\), teamCount\("RED"\), teamCount\("BLUE"\)\)'
)
EMPTY=re.compile(
  r'StudioSolo\.emptyWinner\(RunService:IsStudio\(\) or '
  r'\(studioSoloRoundStarted and privateHordeTrialAllowed\(\)\),\s+'
  r'studioSoloRoundStarted, count,\s+'
  r'teamCount\("RED"\), teamCount\("BLUE"\)\)'
)

def emit(dist:Path,out:Path):
    source=(dist/"src"/GAME).read_bytes()
    solo=(dist/"src"/SOLO).read_bytes()
    assert blob(solo)==SOLO_PIN
    assert blob(source)!=GAME_PIN, "PRIVATE_SOLO_OVERLAY_NOT_APPLIED"
    g=source.decode("utf8")
    c=CAN.findall(g);l=LATCH.findall(g);e=EMPTY.findall(g)
    assert len(c)==2 and len(l)==len(e)==1, "REAL_GAME_MATCH_START_SOURCE_DRIFT"
    assert g.count(NEW_DECL)==1
    start=g.index("local function eligibleSoloPlayers(): {Player}")
    end=g.index("-- Job class is independent of legacy",start)
    ready=g[start:end]
    assert ready.count("local function eligibleSoloPlayers()")==1
    assert ready.count("local function everybodyReady()")==1
    assert "roundReady[player] ~= true then return false end" in ready
    assert g.count('if everybodyReady() and '+c[0])==1
    assert g.count('if not everybodyReady() then')==1
    assert g.count('if RunService:IsStudio() and studioSoloRoundStarted')==1
    assert 'function Solo.canStart(' in solo.decode("utf8")
    helper=NEW_DECL.split("local function privateHordeTrialAllowed(): boolean\n",1)[1]
    helper="local function privateHordeTrialAllowed(): boolean\n"+helper
    prefix=r'''--!nocheck
-- EXACT authored Game team roster+READY and original StudioSolo Module.
-- This native harness cannot prove Roblox private engine or Android FPS.
local studio=false
local privateId=""
local allow=false
local game={PrivateServerId=""}
local workspace={GetAttribute=function(_,key)
 assert(key=="P0D_PRIVATE_LIVE_HORDE_NINE")
 return allow
end}
local RunService={IsStudio=function()return studio end}
local Players={list={}}
function Players:GetPlayers()return self.list end
local Config={MinPlayers=2}
local roundReady={}
local function player(side)
 local p={Team={Name=side},attrs={}}
 function p:GetAttribute(name)return self.attrs[name] end
 return p
end
local function teamCount(side)
 local n=0
 for _,p in ipairs(Players:GetPlayers()) do
  if p.Team and p.Team.Name==side then n+=1 end
 end
 return n
end
local StudioSolo=(function()
'''
    middle=r'''
end)()
'''
    before=r'''
local studioSoloRoundStarted=false
local function verdict()
 local count=#eligibleSoloPlayers()
 local canStart=everybodyReady() and
'''
    latch=r'''
 studioSoloRoundStarted=
'''
    finish=r'''
 local empty=
'''
    after=r'''
 return canStart,studioSoloRoundStarted,empty
end
local function check(label,readyPlayers,studioFlag,privateFlag,serverId,wantStart,wantSolo,wantEmpty)
 Players.list=readyPlayers
 roundReady={}
 for _,p in ipairs(readyPlayers) do roundReady[p]=true end
 studio=studioFlag;game.PrivateServerId=serverId;allow=privateFlag
 local started,solo,empty=verdict()
 assert(started==wantStart,label..": CANSTART")
 assert(solo==wantSolo,label..": SOLO_LATCH")
 assert(empty==wantEmpty,label..": EMPTY_RESULT")
end
local red=player("RED")
local blue=player("BLUE")
local red2=player("RED")
check("STUDIO_SINGLE_READY",{red},true,false,"",true,true,nil)
check("PUBLIC_SINGLE_CANNOT_START",{red},false,false,"",false,false,"RED")
check("PUBLIC_ATTRIBUTE_SPOOF_NO_ID",{red},false,true,"",false,false,"RED")
check("PRIVATE_OFF",{red},false,false,"private-id",false,false,"RED")
check("PRIVATE_STRING_FALSE",{red},false,"true","private-id",false,false,"RED")
check("PRIVATE_SINGLE_READY",{red},false,true,"private-id",true,true,nil)
check("PRIVATE_SINGLE_BLUE",{blue},false,true,"private-id",true,true,nil)
check("PUBLIC_TWO_REAL_TEAMS",{red,blue},false,false,"",true,false,nil)
check("PRIVATE_TWO_REAL_TEAMS",{red,blue},false,true,"private-id",true,false,nil)
check("PRIVATE_TWO_SAME_TEAM_DENIED",{red,red2},false,true,"private-id",false,false,"RED")
-- Explicit existing READY is mandatory even in private; cannot start automatically.
Players.list={red}
roundReady={[red]=false}
studio=false;game.PrivateServerId="private-id";allow=true
assert(not (everybodyReady() and StudioSolo.canStart(true,1,1,0,2)),
 "OWNER_READY_REQUIRED_NOT_AUTO")
-- READY cancellation must remain possible.
roundReady[red]=true
assert(everybodyReady(),"READY_ACTUALLY_REQUIRED")
roundReady[red]=false
assert(not everybodyReady(),"READY_CANCELLATION_REJECTED")
-- Spectator cannot count as voluntary participant.
red.attrs.P0D_LateJoinSpectator=true
roundReady[red]=true
assert(not everybodyReady(),"SPECTATOR_MUST_NOT_READY")
red.attrs.P0D_LateJoinSpectator=nil
-- Removing owner flag must fail the continuation; old Solo win/no-op no longer applies.
Players.list={red};game.PrivateServerId="private-id";allow=false
studioSoloRoundStarted=true
local count=1
assert(StudioSolo.emptyWinner(false,studioSoloRoundStarted,count,1,0)=="RED",
 "REVOKED_PRIVATE_TRIAL_MUST_FINISH_WITHOUT_FAKE_SOLO")
-- Empty original humans never permitted to auto start.
Players.list={}
assert(not everybodyReady(),"EMPTY_LOBBY_NOT_AUTOSTART")
print("P0D_REAL_GAME_PRIVATE_ONE_HUMAN_READY_NATIVE_16_CASES_PASS")
'''
    # Use the EXACT authored source strings, unchanged in runnable tests.
    text=(prefix+solo.decode("utf8")+middle+helper+"\n"+ready+
          before+c[0]+latch+l[0]+finish+e[0]+after)
    out.write_text(text,"utf8")
    print("P0D_PRIVATE_ONE_HUMAN_TRUE_GAME_READY_AND_STUDIOSOLO_EXTRACTED",
          len(text))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();emit(a.dist,a.out)
