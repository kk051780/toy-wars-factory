#!/usr/bin/env python3
"""Test the REAL composed Game botAuthority classic egg transaction callbacks.

Native Luau exercises source-exact steal/drop/deposit functions from final
private73 Game, not a second reimplementation of egg game logic. World and
Roblox engine path/physics are mocked; Studio FUN and AI navigation remain
NOT TESTED.
"""
from __future__ import annotations
import argparse
from pathlib import Path

def verify(dist: Path, output: Path):
    game=(dist/"src/server/Game.server.luau").read_text("utf8")
    bot=(dist/"src/server/SoloTeamBots.luau").read_text("utf8")
    assert game.count('local botAuthority={')==1
    first=game.index('local botAuthority={')
    end=game.index('local function resetRound()',first)
    authority=game[first:end]
    assert 'steal=function(bot,eggTeam)' in authority
    assert 'drop=function(bot,eggTeam)' in authority
    assert 'deposit=function(bot,homeTeam,eggTeam)' in authority
    assert 'attackHuman=function(bot,target,amount)' in authority
    assert 'attackBot=function(bot,target,amount)' in authority
    assert 'match.scores[homeTeam]+=1' in authority
    assert 'Rules.winner(match.scores,match.hp,Config.CapturesToWin)' in authority
    assert 'stopRound(winner,"STUDIO_BOT_EGG_CAPTURE")' in authority
    assert 'match.eggOwners[homeTeam]~=nil' in authority
    assert 'botEggOwners[homeTeam]~=nil' in authority
    assert not any(x in authority for x in (
        'Instance.new("RemoteEvent")','OnServerEvent:Connect(',
        'DataStoreService','MarketplaceService','UpdateAsync('))
    assert 'callbacks.steal(bot,enemy)' in bot
    assert 'callbacks.deposit(bot,bot.team,bot.carry)' in bot
    assert 'callbacks.drop(bot,bot.carry)' in bot
    assert 'local MAX_BOTS=5' in bot
    assert game.count('remote.OnServerEvent:Connect(')==1
    out=MOCK+"\n"+authority+"\n"+CASES
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(out,"utf8")
    print("P0D_FIRSTPLAY_REAL_GAME_BOT_AUTHORITY_SOURCE_EXACT_PASS")


MOCK=r'''
--!nocheck
local V
V=function(x,y,z)
  return setmetatable({X=x,Y=y,Z=z},{
    __sub=function(a,b) return V(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end,
    __index=function(t,key)
      if key=="Magnitude" then
        return math.sqrt(t.X*t.X+t.Y*t.Y+t.Z*t.Z)
      end
      return nil
    end
  })
end
local Config={InteractDistance=9,CapturesToWin=2}
local botEggOwners={}
local match={phase="ACTIVE",scores={RED=0,BLUE=0},
   hp={RED=300,BLUE=300},eggOwners={}}
local EXPERIMENTAL_FIVE_EGG_MODE=false
local map={teams={
  RED={egg={Position=V(-50,0,0),Transparency=0},
       eggPrompt={Enabled=true},scorePad={Position=V(-58,0,0)}},
  BLUE={egg={Position=V(50,0,0),Transparency=0},
        eggPrompt={Enabled=true},scorePad={Position=V(58,0,0)}}}}
local function broadcast() end
local function resetEgg(team)
  botEggOwners[team]=nil
  match.eggOwners[team]=nil
  map.teams[team].egg.Transparency=0
  map.teams[team].eggPrompt.Enabled=true
end
local Rules={}
function Rules.winner(scores,hp,threshold)
  if scores.RED>=threshold then return "RED" end
  if scores.BLUE>=threshold then return "BLUE" end
  return nil
end
local winners={}
local function stopRound(winner,reason)
  match.phase="RESULTS"
  table.insert(winners,{winner=winner,reason=reason})
end
local function check(cond,name)
  assert(cond,"P0D_REAL_BOT_EGG_TRANSACTION_FAILED_"..name)
end
local red={id="red1",team="RED",root={Position=V(50,0,0)}}
local ally={id="red2",team="RED",root={Position=V(50,0,0)}}
local blue={id="blue1",team="BLUE",root={Position=V(-50,0,0)}}
'''
CASES=r'''
-- Wrong/own team cannot steal, and no score is written by either attempt.
check(not botAuthority.steal(red,"RED"),"CANNOT_STEAL_OWN")
check(not botAuthority.steal({id="bad",team="NONE",root=red.root},"BLUE"),
  "INVALID_TEAM")
check(match.scores.RED==0 and match.scores.BLUE==0,
  "REJECTED_STEAL_NO_SCORE")
red.root.Position=V(500,0,0)
check(not botAuthority.steal(red,"BLUE"),"DISTANT_EGG_NO_TELESTEAL")
red.root.Position=V(50,0,0)
match.eggOwners.BLUE="humanHolding"
check(not botAuthority.steal(red,"BLUE"),"HUMAN_HOLDS_EGG")
match.eggOwners.BLUE=nil
check(botAuthority.steal(red,"BLUE"),"REAL_RED_STEAL_BLUE")
check(botEggOwners.BLUE=="red1","BOT_EGG_OWNER_SERVER")
check(map.teams.BLUE.egg.Transparency==1
  and not map.teams.BLUE.eggPrompt.Enabled,"EGG_HIDDEN_PROMPT_OFF")
check(not botAuthority.steal(ally,"BLUE"),"NO_DUPLICATE_STEAL")
check(not botAuthority.deposit(red,"BLUE","BLUE"),
  "WRONG_HOME_DEPOSIT")
check(not botAuthority.deposit(red,"RED","RED"),
  "OWN_EGG_NOT_DEPOSITED")
check(not botAuthority.deposit(ally,"RED","BLUE"),
  "NONOWNER_CANNOT_SCORE")
check(not botAuthority.deposit(red,"RED","BLUE"),
  "NO_SCORE_AWAY_FROM_HOME")
red.root.Position=V(-58,0,0)
match.eggOwners.RED="humanHoldingOwn"
check(not botAuthority.deposit(red,"RED","BLUE"),
  "HOME_EGG_STOLEN_PREVENTS_SCORE")
match.eggOwners.RED=nil
check(botAuthority.deposit(red,"RED","BLUE"),
  "RETURNED_EGG_SCORES")
check(match.scores.RED==1 and match.phase=="ACTIVE",
  "FIRST_CAPTURE_NOT_GAMEOVER")
check(botEggOwners.BLUE==nil
  and map.teams.BLUE.egg.Transparency==0
  and map.teams.BLUE.eggPrompt.Enabled,
  "EGG_RESET_AFTER_SCORE")
check(#winners==0,"NO_EARLY_WINNER")
-- Drop after a second theft releases egg but never grants point.
red.root.Position=V(50,0,0)
check(botAuthority.steal(red,"BLUE"),"SECOND_STEAL")
botAuthority.drop(red,"BLUE")
check(botEggOwners.BLUE==nil and match.scores.RED==1,
  "DROP_RELEASES_WITHOUT_SCORE")
check(map.teams.BLUE.egg.Transparency==0
  and map.teams.BLUE.eggPrompt.Enabled,"DROP_RESETS_EGG")
-- A bot cannot clear another bot's claim.
check(botAuthority.steal(red,"BLUE"),"THIRD_STEAL")
botAuthority.drop(ally,"BLUE")
check(botEggOwners.BLUE=="red1","FOREIGN_DROP_IGNORED")
red.root.Position=V(-58,0,0)
check(botAuthority.deposit(red,"RED","BLUE"),
  "SECOND_CAPTURE_SCORES")
check(match.scores.RED==2 and match.phase=="RESULTS",
  "CAPTURE_THRESHOLD_ENDS_ROUND")
check(#winners==1 and winners[1].winner=="RED"
  and winners[1].reason=="STUDIO_BOT_EGG_CAPTURE",
  "ORIGINAL_GAME_WIN_REASON")
red.root.Position=V(50,0,0)
check(not botAuthority.steal(red,"BLUE"),"RESULTS_BLOCKS_STEAL")
match.phase="LOBBY"
check(not botAuthority.steal(red,"BLUE"),"LOBBY_BLOCKS_STEAL")
match.phase="ACTIVE"
EXPERIMENTAL_FIVE_EGG_MODE=true
check(not botAuthority.steal(red,"BLUE"),"FIVE_EGG_BOT_UNSUPPORTED")
EXPERIMENTAL_FIVE_EGG_MODE=false
check(not botAuthority.deposit(blue,"BLUE","RED"),
  "UNCLAIMED_EGG_NO_SCORE")
print("P0D_FIRSTPLAY_REAL_GAME_BOT_EGG_AUTHORITY_29_NATIVE_CASES_PASS")
'''
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    verify(args.dist,args.out)
