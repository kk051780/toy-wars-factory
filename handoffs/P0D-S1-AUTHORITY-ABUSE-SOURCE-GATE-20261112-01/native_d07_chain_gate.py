#!/usr/bin/env python3
"""Run 4 genuine SHA-locked D07 Luau modules together with TEST-ONLY Roblox doubles.

No game sources are modified. This is not Roblox Studio, network or real physics.
"""
import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

BASE = "b103389e2089f9ff5a08984fe2f8f6f02aa8b1bc"
ROOT = "handoffs/P0D-S1-FTUE-ON-D07D08-SPATIAL-LOBBY-20261112-01/candidate/src/server/"
BLOBS = {
    "GoroganServerAICore.luau": "f0ecf36242f1543eccf915948129f21f99a6bc92",
    "GoroganAttackReceiptWindow.luau": "bc8e4e954c06c1db8778649a84cda135ff56e9d1",
    "GoroganDamageBoundary.luau": "031b0c4a5370a891434de42ada8d76642c080433",
    "GoroganCombinedRuntime.luau": "f10dedf357476e658857131c0843f237825a1c0f",
}

LUAU_PREAMBLE = r'''
-- Only below are test shims. The four authoring modules are byte-exact
-- original Luau except Combined's single require(...) source-loader binding.
local V3 = {}
V3.__index=function(self,key)
 if key=="Magnitude" then return math.sqrt(self.X*self.X+self.Y*self.Y+self.Z*self.Z) end
end
function V3.new(x,y,z) return setmetatable({X=x,Y=y,Z=z,__type="Vector3"},V3) end
V3.__add=function(a,b) return V3.new(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end
V3.__sub=function(a,b) return V3.new(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end
local Vector3=V3
local Vector2={}
function Vector2.new(x,y)
 return {X=x,Y=y,Dot=function(self,b) return self.X*b.X+self.Y*b.Y end}
end
local function typeof(obj)
 if type(obj)=="table" and obj.__type then return obj.__type end
 return type(obj)
end
local currentBlock=false
local workspace={}
function workspace:Raycast(origin,direction,params)
 if currentBlock then return {Instance={IsDescendantOf=function() return false end}} end
 return nil
end
local RaycastParams={new=function() return {} end}
local Enum={RaycastFilterType={Exclude="Exclude"}}
local Players={__type="Instance"}
local game={}
function game:GetService(name) assert(name=="Players");return Players end
'''
LUAU_TEST = r'''
local scenarios=0
local checks=0
local function eq(actual,expected,what)
 checks+=1
 if actual~=expected then
  error("D07_CHAIN_ASSERT_"..what.." got="..tostring(actual).." expected="..tostring(expected),0)
 end
end
local function ok(v,what) eq(v,true,what) end
local function no(v,what) eq(v,false,what) end
local function newFixture(opts)
 opts=opts or {}
 local now=0
 local liveRound=true
 local safe=false
 local immune=false
 local activeCombat=true
 local block=false
 local canSee=true
 local playerPresent=true
 local invalidRoster=false
 local health=100
 local damageCalls=0
 local visuals={}
 local driverStops=0
 local id=opts.id or "test_round"
 local eid=opts.event or "boss_event"
 local root={__type="Instance",Position=Vector3.new(3,0,0)}
 function root:IsA(which) return which=="BasePart" end
 local hum={__type="Instance",Health=health}
 function hum:TakeDamage(n)
  self.Health-=n
  damageCalls+=1
 end
 local character={__type="Instance"}
 function character:FindFirstChildOfClass(which)
  if which=="Humanoid" then return hum end
  return nil
 end
 function character:FindFirstChild(which)
  if which=="HumanoidRootPart" then return root end
  return nil
 end
 local player={__type="Instance",Parent=Players,Character=character}
 function player:IsA(which) return which=="Player" end
 local function roundEvent(r,e) return liveRound and r==id and e==eid end
 local window=Window.new()
 local gate=Gate.new({
  integrationApproved=true,
  isRealRoundEvent=roundEvent,
  resolvePlayerFromTrustedId=function(p)
   if playerPresent and p=="P1" then return player end
   return nil
  end,
  isSafeZone=function() return safe end,
  isDamageImmune=function() return immune end,
  isActiveCombatant=function() return activeCombat end,
  getBossPosition=function() return Vector3.new(0,0,0) end,
  getAttackCenter=function(r,e,a) return window:center(r,e,a) end,
  isCanonicalAttackReceipt=function(r,e,a) return window:attests(r,e,a) end,
 })
 local driver={
  start=function(self,snapshot) return true,"RIG_STARTED" end,
  stop=function(self,r,e) driverStops+=1; return true end,
  getPosition=function() return {x=0,y=0,z=0} end,
  requestNavigation=function() end,
  checkLifetime=function() return false end,
 }
 local function roster()
  if invalidRoster then
   return {{playerId="P1",team="RED",alive=true,position={x=3,y=0,z=0}},
           {playerId="P1",team="BLUE",alive=true,position={x=3,y=0,z=0}}}
  end
  return {{playerId="P1",team="RED",alive=true,inSafeZone=false,position={x=3,y=0,z=0}}}
 end
 local activation={event="ACTIVATE",kind="BOSS",subtype="GOROGAN",
    matchId=id,untilAt=13}
 local deps={
  integrationApproved=true,
  isCanonicalActivation=function(a) return a==activation end,
  isRoundActive=roundEvent,
  getCurrentRoundId=function() return id end,
  getStageId=function() return "S1" end,
  getNow=function() return now end,
  getGroundAnchor=function() return Vector3.new(0,0,0) end,
  getRoster=roster,
  isLineOfSight=function() return canSee end,
  broadcastVisual=function(x) table.insert(visuals,x.kind) end,
  mintServerEventId=function() return eid end,
  driver=driver,
  damageGate=gate,
  receiptWindow=window,
 }
 local combined=Combined.new(deps)
 local f={gate=gate,window=window,combined=combined,player=player,hum=hum,
  root=root,activation=activation,visuals=visuals}
 function f:setNow(n) now=n end
 function f:setLive(n) liveRound=n end
 function f:setSafe(n) safe=n end
 function f:setImmune(n) immune=n end
 function f:setActive(n) activeCombat=n end
 function f:setWall(n) currentBlock=n end
 function f:setCanSee(n) canSee=n end
 function f:setPlayerPresent(n) playerPresent=n end
 function f:setInvalidRoster(n) invalidRoster=n end
 function f:damageCalls() return damageCalls end
 function f:driverStops() return driverStops end
 return f
end

-- No test can forge the canonical activation, re-enable an inactive stage,
-- replay the same round on the exact original Core, or skip owner gate.
local denyOk=pcall(function() Combined.new({integrationApproved=false}) end)
no(denyOk,"disabled_by_default")
local fake = newFixture({id="forged_round"})
local forged={event="ACTIVATE",kind="BOSS",subtype="GOROGAN",
 matchId="forged_round",untilAt=13}
local fakeStart,fakeWhy=fake.combined:start(forged)
no(fakeStart,"fake_activation")
eq(fakeWhy,"NOT_CANONICAL_V40_ACTIVATE","fake_activation_reason")
local realOk,realWhy=fake.combined:start(fake.activation)
ok(realOk,"real_start")
eq(realWhy,"STARTED","start_reason")
local repeatOk,repeatWhy=fake.combined:start(fake.activation)
no(repeatOk,"already_active")
eq(repeatWhy,"ALREADY_ACTIVE","already_active_reason")
local staleStop,whyStale=fake.combined:stop("forged_round","wrong_event")
no(staleStop,"stale_stop")
eq(whyStale,"STALE_STOP","stale_stop_reason")
local didStop=fake.combined:stop("forged_round","boss_event")
ok(didStop,"valid_stop")
eq(fake.hum.Health,100,"no_damage_before_attack")
eq(fake:driverStops(),1,"stop_driver")
no(fake.window:attests("forged_round","boss_event",1),"stop_closed_receipt")
local replay,replayWhy=fake.combined:start(fake.activation)
no(replay,"no_replay_same_round")
eq(replayWhy,"DAMAGE_GATE_START_INVALID_BEGIN","replay_gate_rejection")

local function firstStomp(f)
 local started,reason=f.combined:start(f.activation)
 ok(started,"start_"..tostring(reason))
 f:setNow(2)
 local warning,why=f.combined:heartbeat()
 eq(warning and warning.kind,"STOMP_WARNING","windup_kind")
 eq(warning.attackId,1,"first_attack_id")
 no(f.window:attests(f.activation.matchId,"boss_event",1),"warning_is_not_damage_receipt")
 return warning
end
local function resolve(f)
 f:setNow(4)
 local cmd,why=f.combined:heartbeat()
 eq(cmd and cmd.kind,"STOMP_RESOLVE","stomp_resolves")
 eq(cmd.attackId,1,"resolve_attack_id")
 no(f.window:attests(f.activation.matchId,"boss_event",1),"receipt_always_closed")
end
for i=1,20 do
 local f=newFixture({id="safe_positive_"..tostring(i)})
 firstStomp(f)
 local bad,badWhy=f.gate:applyServerDamage("P1",8,1,f.activation.matchId,"boss_event")
 no(bad,"cannot_hit_while_window_not_open")
 eq(badWhy,"UNTRUSTED_ATTACK","no_warning_attestation")
 resolve(f)
 eq(f.hum.Health,92,"one_authoritative_damage")
 eq(f:damageCalls(),1,"single_hit")
 -- Replay after closed window must not damage again.
 local badAgain,whyAgain=f.gate:applyServerDamage("P1",8,1,f.activation.matchId,"boss_event")
 no(badAgain,"replay_stomp_after_window")
 eq(whyAgain,"UNTRUSTED_ATTACK","untrusted_closed_attestation")
 eq(f.hum.Health,92,"no_duplicate_hp_delta")
end

local cases={
 {name="safe_zone",setup=function(f) f:setSafe(true) end},
 {name="immune",setup=function(f) f:setImmune(true) end},
 {name="not_combatant",setup=function(f) f:setActive(false) end},
 {name="no_server_player",setup=function(f) f:setPlayerPresent(false) end},
 {name="wall_occlusion",setup=function(f) f:setWall(true) end},
 {name="combined_los",setup=function(f) f:setCanSee(false) end},
 {name="far_player_root",setup=function(f) f.root.Position=Vector3.new(28,0,0) end},
 {name="dead_humanoid",setup=function(f) f.hum.Health=0 end},
}
for i,case in ipairs(cases) do
 local f=newFixture({id="denied_"..case.name})
 firstStomp(f)
 case.setup(f)
 local before=f.hum.Health
 resolve(f)
 eq(f.hum.Health,before,"blocked_health_"..case.name)
 eq(f:damageCalls(),0,"blocked_calls_"..case.name)
end

-- Duplicate roster after legit warning: fail closed, full cleanup; never hit.
local duplicate=newFixture({id="duplicate_roster"})
firstStomp(duplicate)
duplicate:setInvalidRoster(true)
duplicate:setNow(4)
local noCmd,fail=duplicate.combined:heartbeat()
eq(noCmd,nil,"roster_no_command")
eq(fail,"HEARTBEAT_FAIL_CLOSED","roster_fail_closed")
eq(duplicate.hum.Health,100,"roster_cannot_hit")
no(duplicate.window:attests("duplicate_roster","boss_event",1),"roster_receipt_closed")
eq(duplicate:driverStops(),1,"roster_driver_cleanup")
-- Round invalidation between WARNING and RESOLVE => terminal no damage.
local invalid=newFixture({id="stale_round"})
firstStomp(invalid)
invalid:setLive(false)
invalid:setNow(4)
local endCmd,endWhy=invalid.combined:heartbeat()
eq(endCmd and endCmd.kind,"END","stale_round_end")
eq(invalid.hum.Health,100,"stale_no_hit")
eq(invalid:driverStops(),1,"stale_cleanup")
if checks < 400 then error("INSUFFICIENT_INTEGRATED_CHECKS "..tostring(checks),0) end
print("P0D_NATIVE_D07_FOUR_MODULE_PASS assertions="..checks)
'''

MUTATIONS = [
 ("skip_authenticated_stomp", "if self.deps.isCanonicalAttackReceipt(roundId,eventId,attackId)~=true then",
  "if false then", "no_warning_attestation"),
 ("bypass_safe_zone", "or self.deps.isSafeZone(player)~=false or self.deps.isDamageImmune(player)~=false",
  "or self.deps.isDamageImmune(player)~=false", "blocked_health_safe_zone"),
 ("bypass_wall_raycast", "if hit and not hit.Instance:IsDescendantOf(character) then",
  "if false and hit and not hit.Instance:IsDescendantOf(character) then", "blocked_health_wall_occlusion"),
]

def verified_source(repo):
 files={}
 for name, expected in BLOBS.items():
  args=["git","-C",repo,"show",BASE+":"+ROOT+name]
  out=subprocess.run(args,capture_output=True,check=False)
  if out.returncode!=0:
   raise RuntimeError("MISSING_FIXED_SOURCE "+name)
  raw=out.stdout
  blob=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
  if blob!=expected:
   raise RuntimeError("FIXED_SOURCE_BLOB_MISMATCH "+name+" "+blob)
  files[name]=raw.decode("utf-8")
 return files

def build(files):
 src=files["GoroganCombinedRuntime.luau"]
 old="local Core = require(script.Parent.GoroganServerAICore)"
 if src.count(old)!=1:
  raise RuntimeError("COMBINED_REQUIRE_ANCHOR_NOT_UNIQUE")
 src=src.replace(old,"local Core = __p0d_official_core",1)
 def wrap(name,code):
  return "local "+name+"=(function()\n"+code+"\nend)()\n"
 return (LUAU_PREAMBLE
  +wrap("__p0d_official_core",files["GoroganServerAICore.luau"])
  +wrap("Window",files["GoroganAttackReceiptWindow.luau"])
  +wrap("Gate",files["GoroganDamageBoundary.luau"])
  +wrap("Combined",src)
  +LUAU_TEST)

def run(luau,path,files):
 path.write_text(build(files),encoding="utf-8")
 p=subprocess.run([luau,str(path)],capture_output=True,text=True,check=False,timeout=25)
 return p.returncode,p.stdout+p.stderr

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument("--repo",required=True)
 parser.add_argument("--luau",required=True)
 a=parser.parse_args()
 sources=verified_source(a.repo)
 with TemporaryDirectory(prefix="p0d_four_d07_") as tmp:
  path=Path(tmp)/"four_module.luau"
  status,output=run(a.luau,path,sources)
  match=re.search(r"P0D_NATIVE_D07_FOUR_MODULE_PASS assertions=(\d+)",output)
  if status!=0 or not match or int(match.group(1))<400:
   raise RuntimeError("REAL_FOUR_MODULE_FAILED "+output[-1500:])
  print(match.group(0))
  print("4/4 EXACT PINNED SOURCE BLOBS")
  # Distinct adversarial mutations (all exact source locations unique)
  for name,before,after,expected_failure in MUTATIONS:
   source=sources["GoroganDamageBoundary.luau"]
   if source.count(before)!=1:
    raise RuntimeError("NON_UNIQUE_MUTATION "+name+" count="+str(source.count(before)))
   modified=dict(sources)
   modified["GoroganDamageBoundary.luau"]=source.replace(before,after,1)
   status,out=run(a.luau,path,modified)
   if status==0 or "D07_CHAIN_ASSERT_" not in out:
    raise RuntimeError("UNDETECTED_MUTATION "+name+" "+out[-400:])
   print("MUTATION_REJECTED "+name)
 print("P0D_D07_CHAIN_NATIVE_SUCCESS")
 return 0

if __name__=="__main__":
 try: sys.exit(main())
 except (RuntimeError,UnicodeError,OSError,subprocess.TimeoutExpired) as e:
  print("P0D_D07_FOUR_MODULE_BLOCKED "+str(e),file=sys.stderr)
  sys.exit(1)
