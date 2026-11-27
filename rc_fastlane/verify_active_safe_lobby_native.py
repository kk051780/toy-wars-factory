"""Exercise the mounted physical-lobby, placement and training Lua."""

import argparse
from pathlib import Path

from apply_active_safe_lobby import GAME, ISLAND, TRAINING
from test_p0_ready_composed_native import unique_function


SETUP = r'''
local workspace={}
local Vector3={}
function Vector3.new(x,y,z) return {X=x,Y=y,Z=z} end
Vector3.zero=Vector3.new(0,0,0)
local CFrame={}
local transform={}
function CFrame.new(x,y,z) return setmetatable({Position=Vector3.new(x,y,z)},transform) end
function transform.__add(a,b)
    local p=a.Position
    return CFrame.new(p.X+b.X,p.Y+b.Y,p.Z+b.Z)
end
local Players={roster={}}
local teamInstances={RED={Name="RED"},BLUE={Name="BLUE"}}
function Players:GetPlayers() return self.roster end
local studio=true
local RunService={}
function RunService:IsStudio() return studio end
local match={phase="LOBBY"}
local map={teams={RED={spawn=CFrame.new(-68,5,0)},BLUE={spawn=CFrame.new(68,5,0)}}}
local queued={}
local task={}
function task.defer(fn) table.insert(queued,coroutine.create(fn)) end
function task.wait(t) coroutine.yield(t) end
local function resume(thread,expectedDelay)
    local ok,nextDelay=coroutine.resume(thread)
    assert(ok and nextDelay==expectedDelay,tostring(nextDelay))
end
local roles,invulnUntil,carry={},{},{}
local modeVotes,lastModeVote,lobbyRecoveryRound={},{},{}
local function warn() error("UNEXPECTED_LOBBY_RECOVERY_WARNING") end
local Config={RoleHealth={RAIDER=100},RoleWalkSpeed={RAIDER=16},RespawnInvulnerability=2}
local function serverNow() return 42 end
local function stopWind() end
local function restoreSlow() end
local function dropEgg() end
local V4XP={SKILLS={"BEAST","WEAPON","MAGIC","ZOMBIE","VEHICLE","BUILDING"}}

local function makePlayer(side,spectator)
    local p={Parent=Players,Team=teamInstances[side],Neutral=side==nil}
    p.spectator=spectator
    function p:GetAttribute(key) return key=="P0D_LateJoinSpectator" and self.spectator end
    local ch={}
    local raw={Parent=ch}
    local root=setmetatable({},{
        __index=raw,
        __newindex=function(_,key,value)
            raw[key]=value
            if key=="CFrame" then raw.Position=value.Position end
        end
    })
    function root:IsA(class) return class=="BasePart" end
    root.CFrame=CFrame.new(0,7,0)
    local hum={Parent=ch,Health=100,Died={Connect=function()end}}
    function hum:IsA(class) return class=="Humanoid" end
    function ch:WaitForChild(name)
        return if name=="HumanoidRootPart" then root else hum
    end
    function ch:IsDescendantOf(ancestor) return ancestor==workspace end
    p.Character=ch
    roles[p]="RAIDER"
    return p,ch,root,hum
end

local function healthy(p)
    if p.spectator or p.dead then return false,nil end
    return true,p.Character:WaitForChild("HumanoidRootPart")
end

local function at(root,x,y,z)
    local p=root.Position
    assert(p.X==x and p.Y==y and p.Z==z,("WRONG_CFRAME %.2f %.2f %.2f"):format(p.X,p.Y,p.Z))
end
'''

CASES = r'''
local red,redCharacter,redRoot=makePlayer("RED",false)
local blue,blueCharacter,blueRoot=makePlayer("BLUE",false)
assignSpawn(red,redCharacter)
assignSpawn(blue,blueCharacter)
at(redRoot,-47,46,382)
at(blueRoot,47,46,382)
match.phase="COUNTDOWN"
assignSpawn(red,redCharacter)
at(redRoot,-47,46,382)
match.phase="ACTIVE"
assignSpawn(red,redCharacter)
assignSpawn(blue,blueCharacter)
at(redRoot,-68,7,0)
at(blueRoot,68,7,0)
local retired,retiredCharacter,retiredRoot=makePlayer("RED",false)
retired.Character={}
assignSpawn(retired,retiredCharacter)
at(retiredRoot,0,7,0)
studio=false
match.phase="LOBBY"
assignSpawn(blue,blueCharacter)
at(blueRoot,68,7,0)
studio=true
print("ACTIVE_SAFE_LOBBY_TEAM_PHASE_SPAWN_AND_RETIRED_PASS")

match.phase="ACTIVE"
local late,lateCharacter,lateRoot=makePlayer(nil,true)
assignSpawn(late,lateCharacter)
at(lateRoot,-47,46,382)
assert(getTeamName(late)=="NONE" and late.Neutral)
local timer=queued[#queued]
resume(timer,.25)
lateRoot.CFrame=CFrame.new(0,7,0)
resume(timer,nil)
at(lateRoot,-47,46,382)
assert(coroutine.status(timer)=="dead")
assignSpawn(late,lateCharacter)
assert(queued[#queued]==timer)
local replaced,oldCharacter,oldRoot=makePlayer(nil,true)
assignSpawn(replaced,oldCharacter)
local previous=queued[#queued]
resume(previous,.25)
oldRoot.CFrame=CFrame.new(0,7,0)
replaced.Character={}
resume(previous,nil)
at(oldRoot,0,7,0)
local admitted,admittedCharacter,admittedRoot=makePlayer(nil,true)
assignSpawn(admitted,admittedCharacter)
local old=queued[#queued]
resume(old,.25)
admitted.spectator=false
admitted.Neutral=false
admitted.Team=teamInstances.BLUE
admittedRoot.CFrame=CFrame.new(68,7,0)
resume(old,nil)
at(admittedRoot,68,7,0)
print("ACTIVE_SAFE_LOBBY_SPECTATOR_ONE_CORRECTION_AND_ADMISSION_FENCE_PASS")

Players.roster={red}
match.phase="LOBBY"
redRoot.CFrame=CFrame.new(0,5,0)
enforceBounds(6)
at(redRoot,-47,46,382)
match.phase="COUNTDOWN"
redRoot.CFrame=CFrame.new(0,5,0)
enforceBounds(6)
at(redRoot,-47,46,382)
match.phase="ACTIVE"
redRoot.CFrame=CFrame.new(0,5,0)
enforceBounds(6)
at(redRoot,0,5,0)
redRoot.CFrame=CFrame.new(0,-40,0)
enforceBounds(6)
at(redRoot,-68,9,0)
match.phase="RESULTS"
redRoot.CFrame=CFrame.new(0,5,0)
enforceBounds(6)
at(redRoot,0,5,0)
studio=false
match.phase="LOBBY"
redRoot.CFrame=CFrame.new(0,-40,0)
enforceBounds(6)
at(redRoot,-68,9,0)
studio=true
print("ACTIVE_SAFE_LOBBY_PHASE_BOUNDS_AND_FIELD_FALLBACK_PASS")

local function setPad(part,team,skill)
    local v=LobbyIsland.padPosition(team,skill)
    part.CFrame=CFrame.new(v.X,v.Y+2,v.Z)
end
for _,skill in ipairs(V4XP.SKILLS) do
    match.phase="LOBBY"
    setPad(redRoot,"RED",skill)
    assert(v4OnHomePad(red)==skill)
    setPad(blueRoot,"BLUE",skill)
    assert(v4OnHomePad(blue)==skill)
    setPad(redRoot,"BLUE",skill)
    assert(v4OnHomePad(red)==nil)
    setPad(redRoot,"RED",skill)
    match.phase="ACTIVE"
    assert(v4OnHomePad(red)==nil)
    match.phase="COUNTDOWN"
    assert(v4OnHomePad(red)==nil)
    match.phase="LOBBY"
    carry[red]="BLUE"
    assert(v4OnHomePad(red)==nil)
    carry[red]=nil
end
redRoot.CFrame=CFrame.new(-56,2,-15)
assert(v4OnHomePad(red)==nil)
print("ACTIVE_SAFE_LOBBY_TWELVE_DURABLE_PADS_AND_NON_LOBBY_REJECTION_PASS")

Players.roster={red,blue,late}
match.phase,match.phaseUntil,match.serial="RESULTS",10,9
redRoot.CFrame=CFrame.new(-68,7,0)
blueRoot.CFrame=CFrame.new(68,7,0)
blue.dead=true
local loads=0
function blue:LoadCharacter()
    loads+=1
    blue.dead=false
    assignSpawn(blue,blueCharacter)
end
finishResult(9)
assert(match.phase=="RESULTS" and loads==0)
at(redRoot,-68,7,0)
finishResult(10)
assert(match.phase=="LOBBY" and lobbyRecoveryRound[blue]==9 and lobbyRecoveryRound[late]==nil)
at(redRoot,-47,46,382)
resume(queued[#queued],nil)
assert(loads==1 and lobbyRecoveryRound[blue]==nil and getTeamName(blue)=="BLUE")
at(blueRoot,47,46,382)

match.phase,match.phaseUntil,match.serial="RESULTS",20,10
blue.dead=true
finishResult(20)
local stale=queued[#queued]
assert(lobbyRecoveryRound[blue]==10)
match.serial=11
resume(stale,nil)
assert(loads==1 and lobbyRecoveryRound[blue]==nil)
print("ACTIVE_SAFE_LOBBY_RESULTS_TIMER_AND_EXISTING_DEAD_RECOVERY_PASS")
'''


def fence(text, start, end):
    assert text.count(start) == 1
    suffix = text.split(start, 1)[1]
    assert suffix.count(end) == 1
    return suffix.split(end, 1)[0]


def program(dist, before_game=None):
    game = (dist / "src" / GAME).read_text("utf-8")
    if before_game is not None:
        previous = before_game.read_text("utf-8")
        for head in ("local function applyReady(player: Player, data)",
                     "local function resetRound()", "local function onJoin(player: Player)",
                     "local function applyEquipScout(player: Player,data:any)",
                     "local function stopRound(winner: string, reason: string)"):
            assert unique_function(game, head) == unique_function(previous, head), head
    bridge = (dist / "src" / TRAINING).read_text("utf-8")
    island = (dist / "src" / ISLAND).read_text("utf-8")
    assert bridge.count("pad.Position = LobbyIsland.padPosition(side,skill)") == 1
    assert bridge.count('if arena:GetAttribute("P0D_PHASE")~="LOBBY" then return nil end') == 1
    assert game.count('lobbyRecoveryRound[p] = endedRound') == 1
    assert game.count('root.CFrame=if RunService:IsStudio() then LobbyIsland.spawn(team)') == 1
    marker = "local spectatorSpawnPlaced ="
    waiting = marker + fence(game, marker, "local function assignSpawn(")
    tick = unique_function(game, "local function tickRound()")
    boundary = tick.split("    -- No client request or egg carry can choose a free teleport destination.\n", 1)
    assert len(boundary) == 2
    result = fence(tick, '    elseif match.phase == "RESULTS" then\n',
                   "    -- Recovery uses the existing server-only authoritative tick.")
    finish = 'local function finishResult(now)\n    if match.phase == "RESULTS" then\n' + result + "end\n"
    return "\n".join((SETUP, "local LobbyIsland=(function()", island, "end)()",
        unique_function(game, "local function getTeamName(player: Player): string"),
        waiting, unique_function(game, "local function assignSpawn(player: Player, character: Model)"),
        unique_function(game, "local function v4OnHomePad(player: Player): string?"),
        "local function enforceBounds(now)", boundary[1], finish, CASES))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--before-game", type=Path)
    args = parser.parse_args()
    args.out.write_bytes(program(args.dist, args.before_game).encode("utf-8"))
