#!/usr/bin/env python3
"""Native Luau exercises EXACT final Game round-start and role authorities.

Mocks synchronous Roblox helpers/LoadCharacter yield to model the dangerous
interleaving. This is not physical Roblox Studio or true multiplayer networking.
"""
from __future__ import annotations
import argparse
from pathlib import Path

def extract(s,start,end):
    assert s.count(start)==1,("MISSING_OR_DUPLICATE_SOURCE_START",start,s.count(start))
    a=s.split(start,1)[1]
    assert end in a,("SOURCE_END_DRIFT",end)
    return a.split(end,1)[0]

def emit(game:Path,out:Path):
    g=game.read_text("utf8")
    reset="local function resetRound()"+extract(g,"local function resetRound()","local function chooseTeam(")
    assert reset.count("local startupSerial=match.serial")==1
    assert reset.count("if match.phase~=\"ACTIVE\" or match.serial~=startupSerial then return end")==1
    # Run EXACT source statements that span the yielding Player:LoadCharacter
    # and the earliest subsequent epoch guard. Avoid unrelated progression
    # subsystems in the native mock; full Game compile is a separate CI gate.
    begin=reset.index("    match.serial += 1")
    first=reset.index("    if RunService:IsStudio()",begin)
    serial=reset[begin:first]
    match_line='    match.phase = "ACTIVE"\n'
    assert reset.count(match_line)==1
    load=reset.index("p:LoadCharacter()",first)
    loop_start=reset.rfind("    for _, p in ipairs(Players:GetPlayers()) do",first,load)
    assert loop_start>=0
    loop_end=reset.index("    end\n",load)+len("    end\n")
    loop=reset[loop_start:loop_end]
    guard_start=reset.index("    -- FB005_PRIVATE78_ROUND_EPOCH_SPECTATOR_ROLE_QA:",loop_end)
    guard_end=reset.index("    -- All previous epoch egg carriers",guard_start)
    assert loop_end==guard_start,"ROUND_GUARD_NOT_IMMEDIATELY_AFTER_CHARACTER_LOAD"
    guard=reset[guard_start:guard_end]
    assert "match.serial~=startupSerial" in guard
    for check in ('setObjectiveEnabled(true)','startCanonical()','beginProgressRounds('):
        assert reset.index("match.serial~=startupSerial")<reset.index(check)
    enable=reset[reset.index('    setObjectiveEnabled(true)'):].split('\n',1)[0]
    canonical=reset[reset.index('    startCanonical()'):].split('\n',1)[0]
    startup=serial+match_line+loop+guard+enable+'\n'+canonical+'\n'
    role="local function applyRole(player: Player, data)"+extract(g,
        "local function applyRole(player: Player, data)",
        "remote.OnServerEvent:Connect(function(player: Player, data)")
    assert 'player:GetAttribute("P0D_LateJoinSpectator")==true' in role
    assert role.index('P0D_LateJoinSpectator') < role.index('Rules.validSeq')
    assert 'local function applyReady(' in role
    promotion=extract(g,'                    chooseTeam(entrant)\n','                    roundReady[entrant]=false')
    assert 'roles[entrant]="RAIDER"' in promotion
    assert 'lastRoleChange[entrant]=-math.huge' in promotion
    assert "local function scheduleLobbyRecovery(" in g
    assert g.count("remote.OnServerEvent:Connect(")==1
    pre=r'''--!nocheck
-- Real authored final Game source, deterministic coroutine race tests.
local match={serial=17,phase="LOBBY",startedAt=0,deadline=0}
local RunService={IsStudio=function() return true end}
local ModeVote={SCORE="SCORE",CLASSIC="CLASSIC"}
function ModeVote.tally(votes,participants) return "CLASSIC" end
local modeVotes={}
local EXPERIMENTAL_FIVE_EGG_MODE=false
local studioSoloRoundStarted=false
local function beginProgressRounds() end
local Players={online={}}
function Players:GetPlayers() return self.online end
local function eligibleSoloPlayers() return Players:GetPlayers() end
local Config={MatchSeconds=900,CastleMaxHp=100,RoleSelectCooldown=3}
local t=1
local function serverNow() return t end
local lastAttack,lastTrap,botEggOwners={},{},{}
local function dropEgg(player) end
local objectives=false
local starts=0
local eggResets=0
local function resetEgg(team) eggResets+=1 end
local function setObjectiveEnabled(value) objectives=value end
local function startCanonical() starts+=1 end
local roles,lastSeq,lastRoleChange={},{},{}
local Rules={}
function Rules.validSeq(new,old) return type(new)=="number" and new>old end
local remote={sent=0}
function remote:FireClient(player,snapshot) self.sent+=1 end
local function snapshotFor(player) return {} end
local function getTeamName(player)
 return player.Team and player.Team.Name or "NONE"
end
local warnCount=0
local function warn(...) warnCount+=1 end
local function clearTraps() end
local function stopCanonical() end
local function stopWind(player) end
local earnedPower,lastWind,lastNet,netImmuneUntil={}, {}, {}, {}
local mobCombo,mobComboUntil,mobLastHits,mobLastKOs={}, {}, {}, {}
local guideProgress={}
local Power={endRound=function(state) end}
local First90Guide={newRound=function(serial) return {serial=serial} end}
local function clearEarnedPowerVisual(player) end
local SoloTeamBots={stop=function() end,start=function() return true end}
local function check(condition,label) assert(condition,"ROUND_EPOCH_ROLE_"..label) end
local pause=false
local player={Team={Name="RED"},attrs={},loads=0}
function player:GetAttribute(k) return self.attrs[k] end
function player:LoadCharacter()
 self.loads+=1
 if pause then coroutine.yield("LOADING") end
end
Players.online={player}
local function beginLoad()
'''
    post=r'''
end
'''
    before=pre+startup+post
    roleTest=r'''
local entrant={Team=nil,attrs={P0D_LateJoinSpectator=true}}
function entrant:GetAttribute(k) return self.attrs[k] end
local function chooseTeam(p) p.Team={Name="BLUE"} end
local roundReady={}
local function promote(p)
 local entrant=p
 chooseTeam(entrant)
''' + promotion + r'''
 roundReady[entrant]=false
end
-- 1: Normal start after loading all players enables objectives and canonical.
pause=false
match.phase="LOBBY";match.serial=17
starts=0;eggResets=0;objectives=false
beginLoad()
check(match.phase=="ACTIVE" and starts==1 and objectives,"NORMAL_START")
check(eggResets==2,"BOTH_EGGS_RESET_NORMAL")
-- 2: Force a leaver RESULT while :LoadCharacter coroutine is suspended.
pause=true;starts=0;eggResets=0;objectives=false
match.phase="LOBBY"
local oldSerial=match.serial
local co=coroutine.create(beginLoad)
local ok,why=coroutine.resume(co)
check(ok and why=="LOADING","SIMULATED_CHARACTER_LOAD_YIELDED")
check(match.serial==oldSerial+1,"ROUND_SERIAL_FROZEN")
match.phase="RESULTS"
ok=coroutine.resume(co)
check(ok and coroutine.status(co)=="dead","RESULTS_RACE_ENDED_COROUTINE")
check(not objectives and eggResets==0 and starts==0,
    "RESULTS_MUST_NOT_REENABLE_OBJECTIVES_AFTER_YIELD")
-- 3: Even another new ACTIVE match with DIFFERENT serial must invalidate
--    the previously suspended startup.
starts=0;eggResets=0;objectives=false
match.phase="LOBBY"
co=coroutine.create(beginLoad)
ok,why=coroutine.resume(co)
check(ok and why=="LOADING","SECOND_CHARACTER_LOAD_YIELD")
match.serial+=1
match.phase="ACTIVE"
ok=coroutine.resume(co)
check(ok and coroutine.status(co)=="dead","EPOCH_FENCED_COROUTINE")
check(not objectives and starts==0 and eggResets==0,"OLD_EPOCH_REACTIVATED_ROUND")
-- 4: Neutral flagged spectator ROLE cannot change and cannot burn shared seq.
pause=false
match.phase="COUNTDOWN"
lastSeq[entrant]=0
lastRoleChange[entrant]=-math.huge
roles[entrant]="RAIDER"
applyRole(entrant,{action="ROLE",role="GUARDIAN",seq=20})
check(roles[entrant]=="RAIDER" and lastSeq[entrant]==0,
    "FLAGGED_SPECTATOR_ROLE_BLOCK_BEFORE_SEQ")
-- 5: Even a neutral no-flag player is ineligible for ROLE.
entrant.attrs.P0D_LateJoinSpectator=nil
applyRole(entrant,{action="ROLE",role="GUARDIAN",seq=21})
check(roles[entrant]=="RAIDER" and lastSeq[entrant]==0,
    "NEUTRAL_NONCOMBAT_ROLE_BLOCK")
-- 6: A genuine combat player is still allowed to choose a role.
match.phase="LOBBY";t=100
lastSeq[player]=0;lastRoleChange[player]=-math.huge
roles[player]="RAIDER"
applyRole(player,{action="ROLE",role="GUARDIAN",seq=1})
check(roles[player]=="GUARDIAN" and lastSeq[player]==1 and remote.sent==1,
    "ELIGIBLE_FIGHTER_ROLE_ALLOWED")
-- 7: Upon observer promotion, default to RAIDER and reset role cooldown.
entrant.Team=nil
entrant.attrs.P0D_LateJoinSpectator=nil
lastRoleChange[entrant]=1000
roles[entrant]="GUARDIAN"
promote(entrant)
check(roles[entrant]=="RAIDER" and lastRoleChange[entrant]==-math.huge,
    "PROMOTION_RESETS_ROLE_AND_COOLDOWN")
-- 8: Promoted combat human can legitimately pick a ROLE next lobby.
match.phase="LOBBY"
applyRole(entrant,{action="ROLE",role="GUARDIAN",seq=1})
check(roles[entrant]=="GUARDIAN" and lastSeq[entrant]==1,
    "PROMOTED_PLAYER_CAN_CHOOSE_ROLE")
-- 9: Invalid role during ACTIVE never mutates combat role.
match.phase="ACTIVE"
local previous=lastSeq[player]
applyRole(player,{action="ROLE",role="RAIDER",seq=2})
check(roles[player]=="GUARDIAN","ACTIVE_ROLE_CHANGE_REJECTED")
print("P0_PRIVATE78_ROUND_EPOCH_ROLE_NATIVE_9_SCENARIOS_PASS")
'''
    source=before+"\n"+role+"\n"+roleTest
    out.write_text(source,"utf8")
    print("P0_PRIVATE78_ROUND_EPOCH_ROLE_ACTUAL_SOURCE_EXTRACT_PASS",len(source))

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--game",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    p=a.parse_args()
    emit(p.game,p.out)
