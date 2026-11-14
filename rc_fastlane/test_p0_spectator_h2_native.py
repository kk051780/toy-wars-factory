#!/usr/bin/env python3
"""Execute source-exact Game eligible-roster/H2 leaving and Bot guards in Luau.

Mocks Roblox's service containers only: DOES NOT assert actual physical studio
movement, latency or live network conditions.
"""
import argparse,re
from pathlib import Path

def section(s,a,b):
    assert s.count(a)==1,("MISSING_OR_DUPLICATE",a,s.count(a))
    tail=s.split(a,1)[1]
    assert b in tail,(a,b)
    return tail.split(b,1)[0]

def emit(game:Path, bot:Path)->str:
    g=game.read_text("utf8");b=bot.read_text("utf8")
    eligible="local function eligibleSoloPlayers(): {Player}"+section(
        g,"local function eligibleSoloPlayers(): {Player}","local function everybodyReady(): boolean")
    assert 'P0D_LateJoinSpectator' in eligible
    h2=section(g,'Players.PlayerRemoving:Connect(function(player)',
        '    if match.phase == "ACTIVE" and side ~= "NONE" then')
    start=h2.index('    if RunService:IsStudio() and match.phase=="ACTIVE"')
    h2=h2[start:]
    assert 'SOLO_H2_ROSTER_CHANGED_REQUIRES_NEW_READY' in h2
    bot_start=section(b,"function Bot.start(world,humanTeam,authority)",
        '    if humanTeam~="RED"')
    bot_start=bot_start.replace("    Bot.stop()\n","",1)
    assert 'if eligible~=1 then return false end' in bot_start
    bot_guard=section(b,'function Bot.tick(now)','    for _,bot in ipairs(bots) do')
    begin=bot_guard.index("    local eligible=0")
    bot_guard=bot_guard[begin:]
    assert 'if eligible~=1 then Bot.stop();return end' in bot_guard
    near="local function nearestHuman(bot,maxDistance)"+section(b,
        "local function nearestHuman(bot,maxDistance)","function Bot.tick(now)")
    assert 'p:GetAttribute("P0D_LateJoinSpectator")~=true' in near
    assert "team and (team==\"RED\" or team==\"BLUE\")" in near
    mode=section(g,
        '#eligibleSoloPlayers()>1 and chosenMode==ModeVote.SCORE',
        '\n')
    assert mode.strip()==''
    assert "and #eligibleSoloPlayers()==1," in g
    assert "local count = #eligibleSoloPlayers()" in g
    assert "local online = eligibleSoloPlayers()" in g
    assert "if entrant:GetAttribute(\"P0D_LateJoinSpectator\")==true then" in g

    pre=r'''-- Native original authored eligibility + leaver + enemy selection.
local Players={online={}}
function Players:GetPlayers() return self.online end
local RunService={}
function RunService:IsStudio() return true end
local match={phase="LOBBY"}
local EXPERIMENTAL_FIVE_EGG_MODE=false
local ModeVote={SCORE="SCORE",CLASSIC="CLASSIC"}
local teamInstances={RED={Name="RED"},BLUE={Name="BLUE"}}
local human={Team=teamInstances.RED,attrs={}}
function human:GetAttribute(k) return self.attrs[k] end
local visitor={Team=nil,attrs={P0D_LateJoinSpectator=true}}
function visitor:GetAttribute(k) return self.attrs[k] end
local other={Team=teamInstances.BLUE,attrs={}}
function other:GetAttribute(k) return self.attrs[k] end
local function check(b,label) assert(b,"SPECTATOR_H2_NATIVE_"..label) end
local reasons={}
local function stopRound(winner,reason)
    table.insert(reasons,{winner=winner,reason=reason})
    match.phase="RESULTS"
end
local Bot={stopped=false}
function Bot.stop() Bot.stopped=true end
local humanTeam="RED"
local authority={}
local world={}
local chosenMode=ModeVote.SCORE
local function computeMode()
    EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio()
        and #eligibleSoloPlayers()>1 and chosenMode==ModeVote.SCORE
end
local function getTeamName(p)
    return p.Team and p.Team.Name or "NONE"
end
local function v(x) return setmetatable({X=x}, {
    __sub=function(a,b) return v(a.X-b.X) end,
    __index=function(t,k) if k=="Magnitude" then return math.abs(t.X) end end
}) end
local bots={}
local alive=true
local active=true
local lastTick=-math.huge
local TICK_MIN=0.35
'''
    # Bot.start has a guard only, contains early returns, test directly.
    tests=r'''
local function mayStartBots()
''' + bot_start + r'''
    return true
end
local function actualLeaving(player)
''' + h2 + r'''
end
local function actualTickGuard()
''' + bot_guard + r'''
    return true
end

-- 1: A single actual combat participant + a late spectator counts one.
Players.online={human,visitor}
check(#eligibleSoloPlayers()==1,"EXCLUDE_NEUTRAL_OBSERVER")
check(mayStartBots(),"BOT_START_ELIGIBLE_SOLO_WITH_OBSERVER")
-- 2: A SCORE vote with a spectator remains Classic for 5 AI teammates/enemies.
computeMode()
check(EXPERIMENTAL_FIVE_EGG_MODE==false,"OBSERVER_CANNOT_FORCE_SCORE_MODE")
-- 3: Genuine two human fighters may choose 5 egg mode.
Players.online={human,other}
computeMode()
check(EXPERIMENTAL_FIVE_EGG_MODE==true,"TWO_FIGHTERS_SCORE_MODE")
check(not mayStartBots(),"BOT_START_REJECTS_TWO_FIGHTERS")
-- 4: A spectator does not become a bot combat target.
Players.online={human,visitor}
local attacker={team="BLUE",root={Position=v(0)}}
human.Character={FindFirstChild=function(self,k)
    if k=="HumanoidRootPart" then return {Position=v(5)} end
end,FindFirstChildOfClass=function(self,k)
    if k=="Humanoid" then return {Health=100} end
end}
visitor.Character={FindFirstChild=function(self,k)
    if k=="HumanoidRootPart" then return {Position=v(1)} end
end,FindFirstChildOfClass=function(self,k)
    if k=="Humanoid" then return {Health=100} end
end}
local target,range=nearestHuman(attacker,8)
check(target==human and range==5,"BOT_IGNORES_NEARBY_OBSERVER")
-- 5: neutral without spectator flag is also not attacked.
visitor.attrs.P0D_LateJoinSpectator=nil
target=nearestHuman(attacker,8)
check(target==human,"BOT_IGNORES_NEUTRAL_WITHOUT_ATTRIBUTE")
-- 6: a genuine enemy team player is selected.
visitor.Team=teamInstances.RED
visitor.attrs.P0D_LateJoinSpectator=nil
target=nearestHuman(attacker,8)
check(target==visitor,"BOT_TARGETS_REAL_ENEMY")
-- 7: a team player flagged spectator still excluded.
visitor.attrs.P0D_LateJoinSpectator=true
target=nearestHuman(attacker,8)
check(target==human,"BOT_EXCLUDES_SPECTATOR_ATTR")
visitor.Team=nil
-- 8: tick keeps bots alive with observer but one real player.
Bot.stopped=false
Players.online={human,visitor}
check(actualTickGuard() and not Bot.stopped,"BOT_SURVIVES_LATE_JOIN")
-- 9: tick fails closed when no combat player remains, even if observer connected.
Bot.stopped=false
Players.online={visitor}
check(actualTickGuard()==nil and Bot.stopped,"BOT_STOPS_ON_NO_REAL_FIGHTERS")
-- 10: tick fails closed with two combat humans.
Bot.stopped=false
Players.online={human,other}
check(actualTickGuard()==nil and Bot.stopped,"BOT_STOPS_ON_TWO_REAL_FIGHTERS")
-- 11: H2 live second player exit ends DRAW for fresh READY.
Players.online={human,other}
match.phase="ACTIVE"
EXPERIMENTAL_FIVE_EGG_MODE=true
actualLeaving(other)
check(match.phase=="RESULTS","H2_EXIT_REQUIRES_RESULT")
check(#reasons==1 and reasons[1].reason=="SOLO_H2_ROSTER_CHANGED_REQUIRES_NEW_READY"
   and reasons[1].winner=="DRAW","H2_EXIT_DRAW_REASON")
-- 12: neutral spectator leaving H2 cannot force a draw.
match.phase="ACTIVE";reasons={}
Players.online={human,other,visitor}
actualLeaving(visitor)
check(match.phase=="ACTIVE" and #reasons==0,"OBSERVER_EXIT_NO_DRAW")
-- 13: H2 3 fighters -> 2 fighters is not solo; continue without a bogus draw.
local third={Team=teamInstances.RED,attrs={}}
function third:GetAttribute(k) return self.attrs[k] end
Players.online={human,other,third}
actualLeaving(third)
check(match.phase=="ACTIVE" and #reasons==0,"H2_3_TO_2_NO_DRAW")
-- 14: Classic mode leaving does not trigger H2-specific branch.
Players.online={human,other}
EXPERIMENTAL_FIVE_EGG_MODE=false
actualLeaving(other)
check(match.phase=="ACTIVE" and #reasons==0,"CLASSIC_NO_H2_FORCED_DRAW")
-- 15: AFTER draw/return lobby a survivor votes SCORE but is still alone.
Players.online={human}
match.phase="LOBBY"
computeMode()
check(EXPERIMENTAL_FIVE_EGG_MODE==false and mayStartBots(),"NEW_SOLO_READY_CAN_SPAWN_BOTS")
print("P0_PRIVATE78_SPECTATOR_H2_NATIVE_15_CASES_PASS")
'''
    return pre+eligible+near+tests

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--game",required=True,type=Path)
    p.add_argument("--bot",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    s=emit(a.game,a.bot)
    a.out.write_text(s,"utf8")
    print("P0_PRIVATE78_SPECTATOR_H2_EXACT_FUNCTIONS_EXTRACTED",len(s))
