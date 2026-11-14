#!/usr/bin/env python3
"""Execute the ACTUAL final 78-source Game's lobby team balancing function.

Standalone native Luau mocks only Players/Teams/RunService/Map (no physical
Roblox engine). Tests 7 exact behaviors: never leave lobby on team balance.
"""
import argparse
from pathlib import Path

def generate(game:Path)->str:
    src=game.read_text("utf8")
    start="local function rebalanceLobbyTeams()"
    end="local function assignSpawn("
    assert src.count(start)==src.count(end)==1,("GAME_FUNCTION_DRIFT",src.count(start),src.count(end))
    function=start+src.split(start,1)[1].split(end,1)[0]
    assert function.count("FB007_LOBBY_REBALANCE_STAYS_IN_DOJO_QA_V1")==1
    assert "LobbyIsland.spawn(move.to)" in function
    assert "player.Team = teamInstances[move.to]" in function
    assert 'if match.phase ~= "LOBBY" then return end' in function
    assert "dropEgg(player)" in function
    return "\n".join([r'''-- Exact final Game.rebalanceLobbyTeams function, native Luau.
local studio=true
local RunService={}
function RunService:IsStudio() return studio end
local fieldSpawn=setmetatable({name="FIELD_BLUE"},{
    __add=function(left,right) return "FIELD_BLUE" end
})
local Vector3={zero="ZERO"}
function Vector3.new(a,b,c) return {a,b,c} end
local LobbyIsland={}
function LobbyIsland.spawn(team) return "LOBBY_"..team end
local map={teams={BLUE={spawn=fieldSpawn},RED={spawn=fieldSpawn}}}
local match={phase="LOBBY"}
local Config={MinPlayers=2}
local teamInstances={RED={name="RED"},BLUE={name="BLUE"}}
local Players={}
local a={UserId=11,Neutral=false,Team=teamInstances.RED,Parent=Players,
  root={CFrame="START",AssemblyLinearVelocity="MOVING",AssemblyAngularVelocity="ROTATING"}}
local b={UserId=12,Neutral=false,Team=teamInstances.BLUE,Parent=Players,
  root={CFrame="OTHER",AssemblyLinearVelocity="NONE",AssemblyAngularVelocity="NONE"}}
local roster={a,b}
function Players:GetPlayers() return roster end
local function getTeamName(p)
    return p.Team and p.Team.name or "NONE"
end
local function teamCount(team)
    local n=0
    for _,p in ipairs(roster) do
        if getTeamName(p)==team then n+=1 end
    end
    return n
end
local drops=0
local function dropEgg(p) drops+=1 end
local function healthy(p)
    if p.dead then return false,nil,nil end
    return true,p.root,nil
end
local move={userId=11,from="RED",to="BLUE"}
local plan={move}
local LobbyTeamRecovery={}
function LobbyTeamRecovery.plan(rows) return plan end
''',function,r'''
-- 1. Studio LOBBY changes team AND keeps player on physically separate island.
rebalanceLobbyTeams()
assert(a.Team==teamInstances.BLUE and a.root.CFrame=="LOBBY_BLUE",
    "LOBBY_BALANCE_TELEPORTED_TO_COMBAT_FIELD")
assert(a.root.AssemblyLinearVelocity=="ZERO"
    and a.root.AssemblyAngularVelocity=="ZERO","LOBBY_BALANCE_PRESERVED_OLD_VELOCITY")
assert(drops==1,"REBALANCE_FAILED_TO_DROP_CARRIED_EGG")
-- 2. Start COUNTDOWN: never rebalance after agreement.
a.Team=teamInstances.RED
a.root.CFrame="COUNTDOWN_LOBBY"
match.phase="COUNTDOWN"
rebalanceLobbyTeams()
assert(a.Team==teamInstances.RED and a.root.CFrame=="COUNTDOWN_LOBBY",
    "COUNTDOWN_REBALANCED")
-- 3. In ACTIVE, do not shuffle or move players.
match.phase="ACTIVE"
rebalanceLobbyTeams()
assert(a.Team==teamInstances.RED and a.root.CFrame=="COUNTDOWN_LOBBY",
    "ACTIVE_REBALANCED")
-- 4. Non-Studio still uses original physical battlefield spawn.
match.phase="LOBBY"
studio=false
rebalanceLobbyTeams()
assert(a.Team==teamInstances.BLUE and a.root.CFrame=="FIELD_BLUE",
    "NON_STUDIO_ORIGINAL_LOBBY_SEMANTICS_DRIFT")
-- 5. Dead player: team may change but never teleport root or do spurious revive.
studio=true
a.Team=teamInstances.RED
a.dead=true
a.root.CFrame="DEAD_ANCHOR"
rebalanceLobbyTeams()
assert(a.Team==teamInstances.BLUE and a.root.CFrame=="DEAD_ANCHOR",
    "DEAD_PLAYER_MOVED_WITHOUT_CHARACTER")
a.dead=false
-- 6. Player left after roster snapshot, never change disconnected Player.
a.Team=teamInstances.RED
a.Parent=nil
a.root.CFrame="LEFT_ANCHOR"
rebalanceLobbyTeams()
assert(a.Team==teamInstances.RED and a.root.CFrame=="LEFT_ANCHOR",
    "DISCONNECTED_TEAM_MIGRATED")
a.Parent=Players
-- 7. Empty/one-player lobby, no forced balance.
roster={a}
a.root.CFrame="ONLY_ONE"
rebalanceLobbyTeams()
assert(a.root.CFrame=="ONLY_ONE" and a.Team==teamInstances.RED,
    "SINGLE_PLAYER_LOBBY_SHUFFLED")
print("P0_PRIVATE78_LOBBY_TEAM_REBALANCE_NATIVE_7_CASES_PASS")
'''])

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--game",type=Path,required=True)
    p.add_argument("--emit",type=Path,required=True)
    a=p.parse_args()
    txt=generate(a.game)
    a.emit.write_text(txt,"utf8")
    print("P0_LOBBY_BALANCE_REAL_GAME_NATIVE_EMITTED",len(txt))
