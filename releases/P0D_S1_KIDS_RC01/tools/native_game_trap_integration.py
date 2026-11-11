#!/usr/bin/env python3
"""Actual immutable S1 Roblox Game.server Luau controller lifecycle test.

Authentic stage Game.server and real S1Rules/LobbyTeamRecovery/Config/S1TrapRules modules
run with TEST-ONLY Roblox API fakes and a manual heartbeat scheduler. MapBuilder
is the sole gameplay geometry fake, alongside non-gameplay services. This is
NOT Roblox Studio, real network delivery, or human/mobile gameplay evidence.
"""
import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

RC="e60c9668de9f5c758f5cf0429df944fc32b2bb16"
ROOT="releases/P0D_S1_KIDS_RC01/"
BLOBS={
    "src/server/Game.server.luau":"7c5229f600f17537bc1bbbb0b96b6a2435875374",
    "src/server/S1Rules.luau":"5652b5b43d753c2fcbd27b6c040a34a3642f71ee",
    "src/server/LobbyTeamRecovery.luau":"db1a369133550bc8356a4ee3ac22b97fcb1b46c4",
    "src/shared/Config.luau":"62023303118454fa395f6bfce4c3a50552f840da",
    "src/server/S1TrapRules.luau":"feabd705e4cfa5483d440e506277080f226343ef",
}
SOURCES={
"Config":"local Config = require(ReplicatedStorage:WaitForChild(\"TrapRaidersShared\"):WaitForChild(\"Config\"))",
"Rules":"local Rules = require(script.Parent:WaitForChild(\"S1Rules\"))",
"MapBuilder":"local MapBuilder = require(script.Parent:WaitForChild(\"MapBuilder\"))",
"LobbyTeamRecovery":"local LobbyTeamRecovery = require(script.Parent:WaitForChild(\"LobbyTeamRecovery\"))",
"TrapRules":"local TrapRules = require(script.Parent:WaitForChild(\"S1TrapRules\"))",
"CanonicalHost":"local CanonicalHost = require(script.Parent:WaitForChild(\"S1CanonicalRoundHost\"))",
"BossBinding":"local BossBinding = require(script.Parent:WaitForChild(\"S1GoroganLiveBindings\"))",
}
FAKES=r'''
-- All of these APIs are external test doubles; the Game source and server
-- authority functions are the actual production Luau code.
local V={}
V.__index=function(s,k)
 if k=="Position" then return s end
  if k=="Magnitude" then return math.sqrt(s.X*s.X+s.Y*s.Y+s.Z*s.Z) end
 if k=="Unit" then
  local d=math.sqrt(s.X*s.X+s.Y*s.Y+s.Z*s.Z)
  if d<0.000001 then return setmetatable({X=0,Y=0,Z=0,__type="Vector3"},V) end
  return setmetatable({X=s.X/d,Y=s.Y/d,Z=s.Z/d,__type="Vector3"},V)
 end
 return V[k]
end
function V.new(x,y,z) return setmetatable({X=x,Y=y,Z=z,__type="Vector3"},V) end
function V:Dot(b) return self.X*b.X+self.Y*b.Y+self.Z*b.Z end
V.__add=function(a,b) return V.new(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end
V.__sub=function(a,b) return V.new(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end
local Vector3=V
local UDim2={fromOffset=function() return {} end,fromScale=function() return {} end}
local Color3={fromRGB=function(r,g,b) return {r,g,b} end,new=function(r,g,b) return {r,g,b} end}
local BrickColor={new=function(c) return c end}
local Enum={RaycastFilterType={Exclude="Exclude"}, Material={Neon="Neon"}}
local RaycastParams={new=function() return {} end}
local function signal()
 local s={listeners={}}
 function s:Connect(fn) table.insert(self.listeners,fn) end
 function s:Fire(...)
  for _,fn in ipairs(self.listeners) do fn(...) end
 end
 return s
end
local rootTasks={}
local task={}
function task.spawn(fn,...)
 if select("#",...)>0 then return fn(...) end
 local co=coroutine.create(fn)
 table.insert(rootTasks,co)
 return co
end
function task.wait(n) return coroutine.yield() end
local tickClock=0
local workspace={}
function workspace:GetServerTimeNow() return tickClock end
local blockedRay=false
function workspace:Raycast(origin,direction,params)
 if blockedRay then return {Instance={IsDescendantOf=function() return false end}} end
 return nil
end
local Teams={__type="Instance"}
function Teams:FindFirstChild(name) return nil end
local Players={__type="Instance",users={},PlayerAdded=signal(),PlayerRemoving=signal()}
function Players:GetPlayers()
 local result={}
 for _,p in ipairs(self.users) do table.insert(result,p) end
 return result
end
local ReplicatedStorage={__type="Instance"}
function ReplicatedStorage:FindFirstChild(name) return nil end
local game={}
function game:GetService(name)
 if name=="Players" then return Players end
 if name=="Teams" then return Teams end
 if name=="ReplicatedStorage" then return ReplicatedStorage end
 error("FAKE_SERVICE_NOT_SUPPORTED_"..tostring(name))
end
local remotes={}
local Instance={}
function Instance.new(class)
 local obj={ClassName=class,__type="Instance"}
 function obj:Destroy() self.Destroyed=true end
 if class=="RemoteEvent" then
  obj.OnServerEvent=signal()
  obj.sent={}
  function obj:FireClient(player,record)
   table.insert(player.inbox,record)
   player.last=record
   table.insert(self.sent,{player=player,record=record})
  end
  table.insert(remotes,obj)
 end
 return obj
end
local function makePart(pos)
 local root={Position=pos,__type="Instance"}
 local fields={CFrame={LookVector=V.new(1,0,0)}}
 setmetatable(root,{
  __index=function(self,key) return fields[key] end,
  __newindex=function(self,key,value)
   if key=="CFrame" then
    if type(value)=="table" and value.__type=="Vector3" then self.Position=value end
    fields.CFrame={LookVector=V.new(1,0,0)}
   else rawset(self,key,value) end
  end
 })
 function root:IsA(which) return which=="BasePart" end
 return root
end
local function makePlayer(uid)
 local p={UserId=uid,Parent=Players,Character=nil,CharacterAdded=signal(),inbox={}}
 function p:LoadCharacter()
  local root=makePart(V.new(0,0,0))
  local head=makePart(V.new(0,1,0))
  local hum={Health=100,MaxHealth=100,Died=signal(),__type="Instance"}
  function hum:IsA(which) return which=="Humanoid" end
  function hum:TakeDamage(amount)
   self.Health-=amount
   if self.Health<=0 then self.Died:Fire() end
  end
  local ch={root=root,head=head,hum=hum,__type="Instance"}
  hum.Parent=ch -- TEST DOUBLE for real Roblox humanoid parenting; required by slow restore
  function ch:FindFirstChild(name)
   if name=="HumanoidRootPart" then return self.root end
   if name=="Head" then return self.head end
  end
  function ch:FindFirstChildOfClass(name)
   if name=="Humanoid" then return self.hum end
  end
  function ch:WaitForChild(name,n)
   if name=="HumanoidRootPart" then return self.root end
   if name=="Humanoid" then return self.hum end
  end
  self.Character=ch
  self.CharacterAdded:Fire(ch)
 end
 p:LoadCharacter()
 return p
end
local pRed=makePlayer(201)
local pBlue=makePlayer(202)
Players.users={pRed,pBlue}
local function prompt() return {Triggered=signal(),Enabled=false} end
local arena={teams={}}
for _,team in ipairs({"RED","BLUE"}) do
 local x=if team=="RED" then 0 else 40
 arena.teams[team]={
  spawn=V.new(x,0,0),
  egg={Position=V.new(x,0,4),Transparency=0},
  eggPrompt=prompt(),
  scorePad={Position=V.new(x,0,6)},
  scorePrompt=prompt(),
  core={Position=V.new(x+(if team=="RED" then -10 else 10),0,0)}
 }
end
local MapBuilder={build=function() return arena end}
local CanonicalHost={new=function() error("D08_BOSS_DISABLED_BY_RC") end}
local BossBinding={new=function() error("D07_BOSS_DISABLED_BY_RC") end}
local function warn(...) end
local function tick(now)
 tickClock=now
 for _,co in ipairs(rootTasks) do
  if coroutine.status(co)~="dead" then
   local ok,err=coroutine.resume(co)
   if not ok then error("NATIVE_REAL_GAME_HEARTBEAT_FAILED "..tostring(err),0) end
  end
 end
end
local function movePlayer(player,place)
 player.Character.root.Position=place
end
local function send(player,action,seq,attrs)
 local msg=attrs or {}
 msg.action=action
 msg.seq=seq
 remotes[1].OnServerEvent:Fire(player,msg)
end
'''
LUAU_TEST=r'''
local checks=0
local function eq(actual,want,label)
 checks+=1
 if actual~=want then
  error("GAME_S1_ASSERT_"..label.." got="..tostring(actual).." want="..tostring(want),0)
 end
end
local function last(player) return player.last end
local function setNear(player,world) movePlayer(player,V.new(world.X,world.Y,world.Z)) end
local function promptSteal(player,side)
 arena.teams[side].eggPrompt.Triggered:Fire(player)
end
local function promptScore(player,side)
 arena.teams[side].scorePrompt.Triggered:Fire(player)
end
eq(#remotes,1,"one_canonical_remote")
eq(#rootTasks,1,"single_heartbeat_loop")
-- Trap uses existing heartbeat; no second scheduler.
eq(pRed.Team.Name,"RED","red_team")
eq(pBlue.Team.Name,"BLUE","blue_team")
eq(last(pRed).phase,"LOBBY","join_lobby")
eq(last(pBlue).phase,"LOBBY","blue_lobby")
-- Only a legitimate ROLE action in LOBBY can change role.
send(pBlue,"ROLE",1,{role="GUARDIAN"})
eq(last(pBlue).role,"GUARDIAN","role_lobby_allowed")
send(pBlue,"ROLE",1,{role="RAIDER"})
eq(last(pBlue).role,"GUARDIAN","role_seq_replay_rejected")
send(pBlue,"ROLE",2,{role="NO_SUCH_ROLE"})
eq(last(pBlue).role,"GUARDIAN","invalid_role_rejected")
tick(0)
eq(last(pRed).phase,"COUNTDOWN","two_player_countdown")
tick(6.99)
eq(last(pRed).phase,"COUNTDOWN","countdown_not_early")
tick(7)
eq(last(pRed).phase,"ACTIVE","active_round")
eq(last(pRed).serial,1,"first_round")
eq(last(pRed).scores.RED,0,"initial_score_zero")
eq(last(pBlue).hp.BLUE,300,"initial_castle_full")
eq(pBlue.Character.hum.MaxHealth,135,"guardian_hp_from_server")
-- GUARDIAN-only server trap uses authoritative positions and shared seq.
-- Client-selected score/damage and client-selected position are not API actions.
local beforeLast=#remotes[1].sent
send(pRed,"SCORE",100,{score=999,team="RED",targetId=202})
send(pRed,"DAMAGE",101,{damage=999,playerId=202})
eq(last(pRed).scores.RED,0,"no_client_scores")
eq(pBlue.Character.hum.Health,135,"no_client_damage")
eq(#remotes[1].sent,beforeLast,"invalid_remote_silent")
-- Active game must refuse role change and must NOT heal character.
local blueHp=pBlue.Character.hum.Health
send(pBlue,"ROLE",3,{role="RAIDER"})
eq(last(pBlue).role,"GUARDIAN","active_role_change_rejected")
eq(pBlue.Character.hum.Health,blueHp,"active_role_no_heal")
-- Own egg cannot be stolen; opponent egg can be stolen only by spatial proximity.
setNear(pRed,arena.teams.RED.egg.Position)
promptSteal(pRed,"RED")
eq(last(pRed).carrying,"","cannot_take_own_egg")
promptSteal(pRed,"BLUE")
eq(last(pRed).carrying,"","cannot_steal_from_far")
setNear(pRed,arena.teams.BLUE.egg.Position)
promptSteal(pRed,"BLUE")
eq(last(pRed).carrying,"BLUE","stolen_enemy_egg")
eq(arena.teams.BLUE.egg.Transparency,1,"stolen_egg_hidden")
promptSteal(pRed,"RED")
eq(last(pRed).carrying,"BLUE","cannot_carry_two_eggs")
-- Enemy carrier has a stolen egg, but scoring is disallowed while own egg away.
setNear(pBlue,arena.teams.RED.egg.Position)
promptSteal(pBlue,"RED")
eq(last(pBlue).carrying,"RED","blue_steals_red_egg")
setNear(pRed,arena.teams.RED.scorePad.Position)
promptScore(pRed,"RED")
eq(last(pRed).scores.RED,0,"own_egg_missing_blocks_score")
eq(last(pRed).carrying,"BLUE","blocked_score_keeps_egg")
pBlue.Character.hum:TakeDamage(999)
eq(arena.teams.RED.egg.Transparency,0,"dead_carrier_returns_home_egg")
eq(arena.teams.RED.eggPrompt.Enabled,true,"returned_egg_interactable")
promptScore(pRed,"RED")
eq(last(pRed).scores.RED,1,"first_score")
eq(last(pRed).carrying,"","score_clears_carrier")
eq(arena.teams.BLUE.egg.Transparency,0,"score_restores_stolen_egg")
eq(last(pRed).phase,"ACTIVE","one_capture_not_winner")
-- Repeat enemy egg heist to the second winning capture.
setNear(pRed,arena.teams.BLUE.egg.Position)
promptSteal(pRed,"BLUE")
eq(last(pRed).carrying,"BLUE","second_enemy_egg")
setNear(pRed,arena.teams.RED.scorePad.Position)
promptScore(pRed,"RED")
eq(last(pRed).scores.RED,2,"winning_two_captures")
eq(last(pRed).phase,"RESULTS","winning_result_phase")
eq(last(pRed).winner,"RED","winning_red")
eq(last(pBlue).winner,"RED","winner_broadcast_blue")
eq(last(pRed).reason,"EGG_CAPTURE","real_game_result_reason")
eq(arena.teams.BLUE.eggPrompt.Enabled,false,"objective_off_in_results")
setNear(pRed,arena.teams.BLUE.egg.Position)
promptSteal(pRed,"BLUE")
eq(last(pRed).carrying,"","results_no_theft")
-- Results remain visible until SERVER time passes; then lobby -> countdown -> ACTIVE.
tick(15.99)
eq(last(pRed).phase,"RESULTS","results_visible_until_timer")
tick(16)
eq(last(pRed).phase,"LOBBY","result_ends_to_lobby")
tick(16.1)
eq(last(pRed).phase,"COUNTDOWN","new_countdown")
tick(23.1)
eq(last(pRed).phase,"ACTIVE","rematch_automatically_started")
eq(last(pRed).serial,2,"new_serial_for_rematch")
eq(last(pRed).scores.RED,0,"rematch_score_reset")
eq(last(pRed).winner,"","rematch_winner_reset")
eq(last(pRed).hp.RED,300,"rematch_castle_hp_reset")
eq(last(pRed).carrying,"","rematch_inventory_reset")
-- Live server damage: stale / forged seq rejected, cooldown and distance enforced.
-- Fresh round t23.1: spawn protection blocks target for 2.5 sec.
tick(26)
setNear(pBlue,V.new(20,5,0))
send(pBlue,"PLACE_TRAP",4,{position={x=-999,z=9},damage=999})
tick(26.05)
eq(last(pBlue).trapCooldown,20,"guardian_trap_server_placed")
send(pBlue,"PLACE_TRAP",5,{position={x=200,z=100}})
eq(last(pBlue).trapCooldown,20,"trap_cooldown_enforced")
setNear(pRed,V.new(20,5,0))
tick(26.1)
eq(pRed.Character.hum.WalkSpeed,10,"enemy_trap_server_slow")
tick(26.2)
eq(pBlue.Character.hum.WalkSpeed,15,"friendly_trap_no_slow")
setNear(pRed,V.new(5,0,0))
setNear(pBlue,V.new(10,0,0))
local preHp=pBlue.Character.hum.Health
send(pRed,"ATTACK",1,{targetId=202,damage=999,position={x=10,y=0,z=0}})
eq(pBlue.Character.hum.Health,preHp-24,"real_server_melee_damage")
send(pRed,"ATTACK",1,{targetId=202,damage=999})
eq(pBlue.Character.hum.Health,preHp-24,"replay_attack_seq_blocked")
send(pRed,"ATTACK",2,{targetId=202,damage=999})
eq(pBlue.Character.hum.Health,preHp-24,"attack_cooldown")
-- Replay the SAME seq after cooldown expires: old packet must NEVER hit.
tick(26.9)
send(pRed,"ATTACK",1,{targetId=202,damage=999})
eq(pBlue.Character.hum.Health,preHp-24,"replay_attack_seq_after_cooldown")
tick(27)
send(pRed,"ATTACK",3,{targetId=202,damage=999})
eq(pBlue.Character.hum.Health,preHp-48,"second_legitimate_melee")
-- Direction/range and block raycast forbid remote-suggested damage.
tick(28)
setNear(pBlue,V.new(30,0,0))
send(pRed,"ATTACK",4,{targetId=202,damage=999})
eq(pBlue.Character.hum.Health,preHp-48,"no_hit_out_of_reach")
tick(29)
setNear(pBlue,V.new(10,0,0))
blockedRay=true
send(pRed,"ATTACK",5,{targetId=202,damage=999})
eq(pBlue.Character.hum.Health,preHp-48,"no_hit_through_wall")
blockedRay=false
tick(29.4)
eq(pRed.Character.hum.WalkSpeed,19,"trap_slow_restored_after_three_seconds")
-- On player disconnect, existing match ends by SERVER authority.
Players.users={pRed}
Players.PlayerRemoving:Fire(pBlue)
eq(last(pRed).phase,"RESULTS","disconnect_ends_round")
eq(last(pRed).winner,"RED","disconnect_survivor_wins")
eq(last(pRed).reason,"OPPONENT_LEFT","disconnect_reason")
if checks<60 then error("GAME_S1_TOO_FEW_ASSERTIONS "..tostring(checks),0) end
print("P0D_NATIVE_ACTUAL_GAME_SERVER_LIFECYCLE_PASS assertions="..tostring(checks))
'''
# Mutations must cause an actual test failure. Always mutate exact source bytes
# in memory, never RC or any tracked game file.
MUTATIONS=[
 ("client_replay_seq_bypass","Game",
  "if not Rules.validSeq(data.seq, lastSeq[player] or 0) then return end",
  "if false then return end","GAME_S1_ASSERT_replay_attack_seq_after_cooldown"),
 ("steal_own_egg","Rules",
  "and team ~= eggTeam and not carrying and eggAtBase",
  "and not carrying and eggAtBase","GAME_S1_ASSERT_cannot_take_own_egg"),
 ("score_while_home_egg_missing","Rules",
  "and team == padTeam and carriedEggTeam == Rules.opponent(team) and ownEggAtBase",
  "and team == padTeam and carriedEggTeam == Rules.opponent(team)",
  "GAME_S1_ASSERT_own_egg_missing_blocks_score"),
 ("disable_winning_result","Game",
  'if winner then stopRound(winner, "EGG_CAPTURE") else broadcast() end',
  'if false then stopRound(winner, "EGG_CAPTURE") else broadcast() end',
  "GAME_S1_ASSERT_winning_result_phase"),
 ("role_switch_during_active","Game",
  'if match.phase == "ACTIVE" then return end',
  'if false then return end',
  "GAME_S1_ASSERT_active_role_change_rejected"),
]
def original(repo):
    modules={}
    for path,sha_expected in BLOBS.items():
        p=subprocess.run(["git","-C",repo,"show",RC+":"+ROOT+path],capture_output=True,check=False)
        if p.returncode:
            raise RuntimeError("OFFICIAL_GAME_SOURCE_NOT_FOUND "+path)
        raw=p.stdout
        digest=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
        if digest!=sha_expected:
            raise RuntimeError("OFFICIAL_SOURCE_BLOB_CHANGED "+path+" "+digest)
        modules[{"Game.server.luau":"Game","S1Rules.luau":"Rules",
                 "LobbyTeamRecovery.luau":"Lobby","Config.luau":"Config",
                  "S1TrapRules.luau":"TrapRules"}[path.rsplit("/",1)[1]]]=raw.decode("utf-8")
    return modules

def wrap(n,source):
    return "local "+n+"=(function()\n"+source+"\nend)()\n"
def build(modules):
    original_game=modules["Game"]
    for name,anchor in SOURCES.items():
        if original_game.count(anchor)!=1:
            raise RuntimeError("NONUNIQUE_REQUIRE_ANCHOR_"+name)
        replacement=("local "+name+" = __real_"+name if name in ("Config","Rules","LobbyTeamRecovery","TrapRules")
                     else "local "+name+" = "+name)
        original_game=original_game.replace(anchor,replacement,1)
    return (FAKES
        +wrap("__real_Config",modules["Config"])
        +wrap("__real_Rules",modules["Rules"])
        +wrap("__real_LobbyTeamRecovery",modules["Lobby"])
        +wrap("__real_TrapRules",modules["TrapRules"])
        +wrap("__real_game_controller",original_game)
        +LUAU_TEST)

def run(luau,path,modules):
    path.write_text(build(modules),encoding="utf-8")
    p=subprocess.run([luau,str(path)],capture_output=True,text=True,check=False,timeout=30)
    return p.returncode,p.stdout+p.stderr

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",required=True)
    p.add_argument("--luau",required=True)
    args=p.parse_args()
    sources=original(args.repo)
    with TemporaryDirectory(prefix="p0d_native_server_") as folder:
        path=Path(folder)/"authentic_game_controller.luau"
        code,output=run(args.luau,path,sources)
        match=re.search(r"P0D_NATIVE_ACTUAL_GAME_SERVER_LIFECYCLE_PASS assertions=(\d+)",output)
        if code!=0 or not match or int(match.group(1))<60:
            raise RuntimeError("GAME_LIFECYCLE_REAL_SOURCE_FAILED "+output[-1600:])
        print(match.group(0))
        for name,module,old,new,expected in MUTATIONS:
            src=sources[module]
            expected_count=2 if name=="client_replay_seq_bypass" else 1
            if src.count(old)!=expected_count:
                raise RuntimeError("AMBIGUOUS_MUTATION_ANCHOR_"+name+" "+str(src.count(old)))
            bad=dict(sources);bad[module]=src.replace(old,new,1)
            code,out=run(args.luau,path,bad)
            if code==0 or expected not in out:
                raise RuntimeError("UNDETECTED_MUTATION_"+name+" "+out[-400:])
            print("GAME_SERVER_MUTATION_REJECTED "+name)
        print("P0D_NATIVE_ACTUAL_GAME_SERVER_NEGATIVE_CONTROLS="+str(len(MUTATIONS)))
        print("P0D_OFFICIAL_RC_ACTUAL_GAME_SERVER_SOURCE_PASS")
    return 0

if __name__=="__main__":
    try: sys.exit(main())
    except (RuntimeError,UnicodeError,OSError,subprocess.TimeoutExpired) as e:
        print("P0D_ACTUAL_GAME_SERVER_NATIVE_BLOCKED "+str(e),file=sys.stderr)
        sys.exit(1)
