#!/usr/bin/env python3
"""Extract actual composed Game mode selector + Game botAuthority + real Bot.tick.

Executes source-exact code in pinned native Luau, but mocks movement instantly;
therefore proves intent/transactions only, NOT physical Roblox pathfinding.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from verify_firstplay_bot_eggs import MOCK

def extract(s: str, a: str,b: str, offset: int=0) -> str:
    i=s.index(a,offset)
    j=s.index(b,i+len(a))
    assert j>i
    return s[i:j]

def verify(dist: Path, out: Path):
    game=(dist/"src/server/Game.server.luau").read_text("utf8")
    bot=(dist/"src/server/SoloTeamBots.luau").read_text("utf8")
    selector=extract(game,"local chosenMode=ModeVote.tally(modeVotes,Players:GetPlayers())",
        "if RunService:IsStudio() then\n        beginProgressRounds")
    assert "#Players:GetPlayers()>1 and chosenMode==ModeVote.SCORE" in selector
    assert "EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio()" in selector
    source_authority=extract(game,"local botAuthority={","local function resetRound()")
    assert "callbacks.steal(" in bot and "callbacks.deposit(" in bot
    tick=extract(bot,"function Bot.tick(now)","function Bot.tryHumanHit(")
    assert "callbacks.steal(bot,enemy)" in tick
    assert "callbacks.deposit(bot,bot.team,bot.carry)" in tick
    assert "if eligible~=1 then Bot.stop();return end" in tick
    assert "if not active then return end" in tick
    assert "move(bot,waypoint,now)" in tick
    ui=(dist/"src/client/HUD.client.luau").read_text("utf8")
    assert "soloFiveEggUnavailable" in ui
    assert "5個卵モードは2人以上" in ui
    assert 'soloFiveEggUnavailable = RunService:IsStudio()' in game
    assert game.count("remote.OnServerEvent:Connect(")==1
    merged="\n".join((MOCK,PRELUDE,source_authority,SELECT_START,selector,SELECT_END,
                      tick,CASES))
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(merged,encoding="utf8")
    print("P0D_SOLO_MODE_GAME_BOT_TICK_SOURCE_EXACT_PASS")

PRELUDE=r'''
local Players={online={}}
function Players:GetPlayers() return self.online end
local RunService={IsStudio=function() return true end}
local ModeVote={SCORE="SCORE",CLASSIC="CLASSIC",
  tally=function() return "SCORE" end}
local modeVotes={}
local human={attrs={}}
function human:GetAttribute(key) return self.attrs[key] end
local spectator={attrs={P0D_LateJoinSpectator=true}}
function spectator:GetAttribute(key) return self.attrs[key] end
local extraHuman={attrs={}}
function extraHuman:GetAttribute(key) return self.attrs[key] end
local EXPERIMENTAL_FIVE_EGG_MODE=false
local guardCalls=0
'''
SELECT_START=r'''
local function actualModeDecision()
'''
SELECT_END=r'''
end
local Bot={}
local bots={}
local active=true
local lastTick=-math.huge
local TICK_MIN=.35
local callbacks=botAuthority
local travelLog={}
local function alive(bot)
  return bot.hum and bot.hum.Health>0
end
local function nearestEnemyBot(bot,radius) return nil,radius end
local function nearestHuman(bot,radius) return nil,radius end
local function invalidatePath(bot)
  bot.generation=(bot.generation or 0)+1
end
local function move(bot,goal,now)
  table.insert(travelLog,goal)
  bot.root.Position=goal
end
local function showCarriedEgg(bot,show)
  bot.carryVisual=show
end
local function clearCarry(bot)
  if bot.carry then callbacks.drop(bot,bot.carry);bot.carry=nil end
end
local function respawn(bot) error("unexpected bot death in simulated journey") end
function Bot.stop()
  guardCalls+=1
  active=false
  for _,b in ipairs(bots) do clearCarry(b) end
  table.clear(bots)
end
'''
CASES=r'''
local function check(cond,label)
  assert(cond,"ACTUAL_BOT_TICK_JOURNEY_FAILED_"..label)
end
Players.online={human}
actualModeDecision()
check(EXPERIMENTAL_FIVE_EGG_MODE==false,"SOLO_SCORE_VOTE_CANNOT_START_BOTLESS_H2")
Players.online={human,extraHuman}
actualModeDecision()
check(EXPERIMENTAL_FIVE_EGG_MODE==true,"TWO_PLAYER_SCORE_VOTE_PRESERVED")
Players.online={human}
actualModeDecision()
check(EXPERIMENTAL_FIVE_EGG_MODE==false,"SOLO_CLASSIC_MODE_RESTORED")
local b={id="runner",team="RED",style="RAIDER",hum={Health=100},
  root={Position=V(-58,0,0)},carry=nil,lastAttack=0}
bots={b}
Bot.tick(1)
check(#travelLog==1,"REAL_BOT_TICK_PURSUES_ENEMY_EGG")
check(b.root.Position.X==50,"MOVE_TO_BLUE_EGG")
check(botEggOwners.BLUE==nil,"NO_DISTANCE_TELESTEAL")
Bot.tick(1.5)
check(botEggOwners.BLUE=="runner","REAL_BOT_TICK_STEALS_EGG")
check(b.carry=="BLUE" and b.carryVisual==true,"BOT_CARRIES_VISIBLE_EGG")
check(b.root.Position.X==-58,"REAL_BOT_TICK_RETURNS_TO_HOME_SCORE")
Bot.tick(2)
check(match.scores.RED==1,"REAL_BOT_TICK_SCORES_ON_RETURN")
check(b.carry==nil and not b.carryVisual,"DROP_CARRY_VISUAL_AFTER_DEPOSIT")
check(map.teams.BLUE.egg.Transparency==0,"EGG_RESETS_AFTER_DEPOSIT")
check(#winners==0 and match.phase=="ACTIVE","FIRST_CAPTURE_NO_AUTO_WIN")
EXPERIMENTAL_FIVE_EGG_MODE=true
Bot.tick(2.5)
check(botEggOwners.BLUE==nil and match.scores.RED==1,
  "BOT_CANNOT_STEAL_WHILE_H2_UNSUPPORTED")
EXPERIMENTAL_FIVE_EGG_MODE=false
Players.online={human,spectator}
Bot.tick(3)
check(active and guardCalls==0,"LATE_SPECTATOR_DOES_NOT_KILL_SOLO_BOTS")
Players.online={human,extraHuman}
Bot.tick(3.5)
check(not active and guardCalls==1,"SECOND_ELIGIBLE_PLAYER_FAIL_CLOSED")
check(#bots==0,"BOT_STOP_CLEANS_ROSTER")
print("P0D_SOLO_REAL_GAME_BOT_TICK_15_NATIVE_CASES_PASS")
'''
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    verify(a.dist,a.out)
