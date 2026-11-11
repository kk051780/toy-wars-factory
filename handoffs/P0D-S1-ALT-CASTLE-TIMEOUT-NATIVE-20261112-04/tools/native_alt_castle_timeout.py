#!/usr/bin/env python3
"""Actual immutable S1 Roblox Game.server alternative castle & time-limit test.

Authentic 559-line Game.server and real S1Rules/LobbyTeamRecovery/Config modules
run with TEST-ONLY Roblox API fakes and a manual heartbeat scheduler. MapBuilder
is the sole gameplay geometry fake, alongside non-gameplay services. This is
NOT Roblox Studio, actual raycast geometry, real network, or mobile evidence.
"""
import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

RC="5dc6c958ea5549b1e859d6d250e6179e731181fb"
ROOT="releases/P0D_S1_KIDS_RC01/"
BLOBS={
    "src/server/Game.server.luau":"3d3c5934e110099517fc4a7eb5aa914fcd52f145",
    "src/server/S1Rules.luau":"5652b5b43d753c2fcbd27b6c040a34a3642f71ee",
    "src/server/LobbyTeamRecovery.luau":"db1a369133550bc8356a4ee3ac22b97fcb1b46c4",
    "src/shared/Config.luau":"ef10e4288e4732588116cd3e55d3d871ca803ff4",
}
SOURCES={
"Config":"local Config = require(ReplicatedStorage:WaitForChild(\"TrapRaidersShared\"):WaitForChild(\"Config\"))",
"Rules":"local Rules = require(script.Parent:WaitForChild(\"S1Rules\"))",
"MapBuilder":"local MapBuilder = require(script.Parent:WaitForChild(\"MapBuilder\"))",
"LobbyTeamRecovery":"local LobbyTeamRecovery = require(script.Parent:WaitForChild(\"LobbyTeamRecovery\"))",
"CanonicalHost":"local CanonicalHost = require(script.Parent:WaitForChild(\"S1CanonicalRoundHost\"))",
"BossBinding":"local BossBinding = require(script.Parent:WaitForChild(\"S1GoroganLiveBindings\"))",
}
FAKES=r'''
-- All of these APIs are external test doubles; the Game source and server
-- authority functions are the actual production Luau code.
local V={}
V.__index=function(s,k)
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
local Color3={fromRGB=function(r,g,b) return {r,g,b} end}
local BrickColor={new=function(c) return c end}
local Enum={RaycastFilterType={Exclude="Exclude"}}
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
 if actual~=want then error("GAME_ALT_ASSERT_"..label.." got="..tostring(actual).." want="..tostring(want),0) end
end
local function last(player) return player.last end
local function near(player,place) movePlayer(player,V.new(place.X,place.Y,place.Z)) end
eq(#remotes,1,"one_game_remote_only")
eq(#rootTasks,1,"one_game_heartbeat")
eq(last(pRed).phase,"LOBBY","lobby_red")
eq(last(pBlue).phase,"LOBBY","lobby_blue")
tick(0)
eq(last(pRed).phase,"COUNTDOWN","first_countdown")
tick(7)
eq(last(pRed).phase,"ACTIVE","first_round")
eq(last(pRed).serial,1,"serial1")
-- DIFFERENT outcome: 360 seconds with no score nor damage must be DRAW.
tick(366.99)
eq(last(pRed).phase,"ACTIVE","timeout_not_early")
tick(367)
eq(last(pRed).phase,"RESULTS","timeout_results")
eq(last(pRed).winner,"DRAW","time_limit_exact_draw")
eq(last(pBlue).winner,"DRAW","draw_broadcast_both")
eq(last(pRed).reason,"TIME_LIMIT","time_limit_reason")
eq(last(pRed).scores.RED,0,"draw_score_red_zero")
eq(last(pRed).scores.BLUE,0,"draw_score_blue_zero")
tick(375.99)
eq(last(pRed).phase,"RESULTS","draw_result_timer_hold")
tick(376)
eq(last(pRed).phase,"LOBBY","draw_lobby_reset")
tick(376.1)
eq(last(pRed).phase,"COUNTDOWN","draw_rematch_countdown")
tick(383.1)
eq(last(pRed).phase,"ACTIVE","round2_active")
eq(last(pRed).serial,2,"round2_serial")
eq(last(pRed).hp.BLUE,300,"castle_initial_hp")
-- The map fake's BLUE core is x50. RED attacker looks +X.
-- BLUE enemy is moved away, otherwise the server correctly prioritizes melee.
movePlayer(pBlue,V.new(-60,0,40))
tick(386)
local core=arena.teams.BLUE.core.Position
-- Too far, from behind, or with a solid raycast occlusion -> NO castle damage.
movePlayer(pRed,V.new(20,0,0))
send(pRed,"ATTACK",1,{damage=999,target="BLUE_CASTLE",position={x=50,y=0,z=0}})
eq(last(pRed).hp.BLUE,300,"distance_reject_castle")
tick(387.2)
movePlayer(pRed,V.new(60,0,0))
send(pRed,"ATTACK",2,{damage=999,target="BLUE_CASTLE"})
eq(last(pRed).hp.BLUE,300,"facing_reject_castle")
tick(388.3)
movePlayer(pRed,V.new(36,0,0))
blockedRay=true
send(pRed,"ATTACK",3,{damage=999,target="BLUE_CASTLE"})
eq(last(pRed).hp.BLUE,300,"wall_reject_castle")
blockedRay=false
-- Genuine 14 server-authoritative damage per Raider ATTACK, not client damage999.
tick(389.4)
send(pRed,"ATTACK",4,{damage=999,targetId=202,target="BLUE_CASTLE"})
eq(last(pRed).hp.BLUE,286,"server_bounded_castle_damage")
send(pRed,"ATTACK",4,{damage=999,target="BLUE_CASTLE"})
eq(last(pRed).hp.BLUE,286,"castle_seq_replay_reject")
tick(389.5)
send(pRed,"ATTACK",5,{damage=999,target="BLUE_CASTLE"})
eq(last(pRed).hp.BLUE,286,"castle_attack_cooldown_reject")
-- 21 more valid hits x14 after at least .9s each: castle hp reaches zero on hit22.
local seq=6
for hitNo=2,22 do
 tick(390.4+(hitNo-2)*0.9)
 send(pRed,"ATTACK",seq,{target="CHEAT",damage=999})
 seq+=1
 local hp=math.max(0,300-14*hitNo)
 eq(last(pRed).hp.BLUE,hp,"castle_hp_hit_"..tostring(hitNo))
 if hitNo<22 then
  eq(last(pRed).phase,"ACTIVE","castle_not_destroyed_early_"..tostring(hitNo))
 end
end
eq(last(pRed).phase,"RESULTS","castle_destroyed_results")
eq(last(pRed).winner,"RED","castle_destroyed_winner")
eq(last(pBlue).winner,"RED","castle_destroyed_blue_receives_red_win")
eq(last(pRed).reason,"CASTLE_DESTROYED","castle_destroyed_reason")
eq(last(pRed).scores.RED,0,"castle_win_without_egg_capture")
eq(last(pRed).hp.BLUE,0,"castle_zero_clamped")
-- Rematch starts with clean castle health after official RESULTS timer.
tick(417.39)
eq(last(pRed).phase,"RESULTS","castle_results_not_early")
tick(417.4)
eq(last(pRed).phase,"LOBBY","castle_results_exit")
tick(417.5)
eq(last(pRed).phase,"COUNTDOWN","round3_countdown")
tick(424.5)
eq(last(pRed).phase,"ACTIVE","round3_active")
eq(last(pRed).serial,3,"round3_serial")
eq(last(pRed).hp.BLUE,300,"round3_castle_reset")
-- ONE castle hit creates an objective tiebreaker without egg capture.
tick(427.5)
movePlayer(pBlue,V.new(-60,0,40))
movePlayer(pRed,V.new(36,0,0))
send(pRed,"ATTACK",27,{target="BLUE_CASTLE",damage=999})
eq(last(pRed).hp.BLUE,286,"round3_one_hit")
tick(784.49)
eq(last(pRed).phase,"ACTIVE","tiebreaker_timeout_not_early")
tick(784.5)
eq(last(pRed).phase,"RESULTS","round3_timeout")
eq(last(pRed).reason,"TIME_LIMIT","tiebreaker_reason")
eq(last(pRed).winner,"RED","castle_hp_tiebreaker_winner")
eq(last(pBlue).winner,"RED","castle_hp_tiebreaker_broadcast")
eq(last(pRed).scores.RED,0,"tiebreaker_zero_eggs")
eq(last(pRed).scores.BLUE,0,"tiebreaker_zero_eggs_blue")
if checks<65 then error("GAME_ALT_TOO_FEW_ASSERTIONS "..tostring(checks),0) end
print("P0D_OFFICIAL_RC_NATIVE_ALTERNATE_CASTLE_TIMEOUT_PASS assertions="..tostring(checks))
'''
# Negative mutations on source READ from official ref, never source edits in repo.
MUTATIONS=[
 ("always_RED_on_timeout","Game",
  'stopRound(if red == blue then "DRAW" else (if red > blue then "RED" else "BLUE"), "TIME_LIMIT")',
  'stopRound("RED", "TIME_LIMIT")',
  "GAME_ALT_ASSERT_time_limit_exact_draw"),
 ("skip_castle_win","Game",
  'if winner then stopRound(winner, "CASTLE_DESTROYED") else broadcast() end',
  'if false then stopRound(winner, "CASTLE_DESTROYED") else broadcast() end',
  "GAME_ALT_ASSERT_castle_destroyed_results"),
 ("unsafe_castle_through_wall","Game",
  'if hit and hit.Instance ~= core then return end',
  'if false then return end',
  "GAME_ALT_ASSERT_wall_reject_castle"),
 ("castle_aim_bypass","Rules",
  'return dx <= reach and dx >= 0 and dot >= 0.1',
  'return dx <= reach and dx >= 0',
  "GAME_ALT_ASSERT_facing_reject_castle"),
 ("castle_client_damage_trust","Game",
  'match.hp[enemy] = math.max(0, match.hp[enemy] - Config.CastleAttackDamage[roles[player] or "RAIDER"])',
  'match.hp[enemy] = math.max(0, match.hp[enemy] - (data.damage or Config.CastleAttackDamage[roles[player] or "RAIDER"]))',
  "GAME_ALT_ASSERT_server_bounded_castle_damage"),
 ("castle_cooldown_bypass","Rules",
  'and now - previousTime >= cooldown',
  'and true',
  "GAME_ALT_ASSERT_castle_attack_cooldown_reject"),
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
                 "LobbyTeamRecovery.luau":"Lobby","Config.luau":"Config"}[path.rsplit("/",1)[1]]]=raw.decode("utf-8")
    return modules

def wrap(n,source):
    return "local "+n+"=(function()\n"+source+"\nend)()\n"
def build(modules):
    original_game=modules["Game"]
    for name,anchor in SOURCES.items():
        if original_game.count(anchor)!=1:
            raise RuntimeError("NONUNIQUE_REQUIRE_ANCHOR_"+name)
        replacement=("local "+name+" = __real_"+name if name in ("Config","Rules","LobbyTeamRecovery")
                     else "local "+name+" = "+name)
        original_game=original_game.replace(anchor,replacement,1)
    return (FAKES
        +wrap("__real_Config",modules["Config"])
        +wrap("__real_Rules",modules["Rules"])
        +wrap("__real_LobbyTeamRecovery",modules["Lobby"])
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
        match=re.search(r"P0D_OFFICIAL_RC_NATIVE_ALTERNATE_CASTLE_TIMEOUT_PASS assertions=(\d+)",output)
        if code!=0 or not match or int(match.group(1))<65:
            raise RuntimeError("CASTLE_TIMEOUT_REAL_SOURCE_FAILED "+output[-1600:])
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
            print("ALT_GAME_MUTATION_REJECTED "+name)
        print("P0D_NATIVE_ALT_CASTLE_TIMEOUT_NEGATIVE_CONTROLS="+str(len(MUTATIONS)))
        print("P0D_OFFICIAL_RC_ACTUAL_ALTERNATE_RESULTS_SOURCE_PASS")
    return 0

if __name__=="__main__":
    try: sys.exit(main())
    except (RuntimeError,UnicodeError,OSError,subprocess.TimeoutExpired) as e:
        print("P0D_ALT_CASTLE_TIMEOUT_BLOCKED "+str(e),file=sys.stderr)
        sys.exit(1)
