#!/usr/bin/env python3
"""Native execution of the ACTUAL #823 V2 policy and actual Runtime module.
Mock only Roblox instance/signal surfaces, not the gameplay code.
"""
from pathlib import Path
import argparse
RUNTIME=Path(__file__).with_name("EGGRUMBLE_InvulRuntime.luau")
HARNESS=r'''
local now=100
local os={clock=function()return now end}
local function signal()
 local s={listeners={}}
 function s:Connect(fn)
  local rec={fn=fn,connected=true}
  table.insert(self.listeners,rec)
  return {Disconnect=function()rec.connected=false end}
 end
 function s:Fire(...)
  for _,rec in ipairs(self.listeners) do
   if rec.connected then rec.fn(...) end
  end
 end
 return s
end
local Players={}
local p,character,humanoid
function Players:GetPlayerFromCharacter(char)
 if p and p.Character==char then return p end
 return nil
end
local game={GetService=function(self,name)
 assert(name=="Players","RED_RUNTIME_REQUESTS_UNKNOWN_SERVICE")
 return Players
end}
local queued={}
local task={delay=function(dt,fn)
 table.insert(queued,{at=now+dt,fn=fn})
end}
local function advance(t)
 now=t
 for _,job in ipairs(queued) do
  if job.at<=now then
   job.fn();job.at=math.huge
  end
 end
end
local Instance={}
function Instance.new(kind)
 assert(kind=="Tool","RED_RUNTIME_CREATES_UNKNOWN_INSTANCE")
 return {Activated=signal(),Parent=nil,
  Destroy=function(self) self.Parent=nil end}
end
__POLICY_SOURCE__
local Policy=M
__RUNTIME_SOURCE__
local runtime=Runtime
local backpack={}
p={UserId=7,Parent=Players,attrs={
 EGGRUMBLE_QueuedMode="TEAM",EGGRUMBLE_Role="WARRIOR",},
 CharacterRemoving=signal()}
function p:GetAttribute(key)return self.attrs[key] end
function p:SetAttribute(key,value)self.attrs[key]=value end
function p:FindFirstChildOfClass(kind)
 if kind=="Backpack" then return backpack end
 return nil
end
character={}
function character:FindFirstChildOfClass(kind)
 if kind=="Humanoid" then return humanoid end
 return nil
end
humanoid={Health=200,MaxHealth=250,Parent=character,Died=signal(),attrs={}}
function humanoid:GetAttribute(key)return self.attrs[key] end
p.Character=character
local session={mode="TEAM",
 world={Parent={},Destroying=signal()},
 rules={phase="ACTIVE",castles={["7"]={alive=true,heldEggs=0,team="RED"}}}}
runtime.attach(session,p,"WARRIOR")
local tool=runtime and backpack
assert(runtime.currentPolicySnapshot(p).phase=="NONE","RED_DEFAULT_AWAKENED")
-- The Tool must actually be enabled/activated with the server-side equipped actor.
-- Retrieve it from authored Source by instrumenting Instance.new cache.
__TOOL_BIND__
assert(tool and tool.Name=="迎撃覚醒","RED_MISSING_FREE_SKILL_TOOL")
tool.Parent=character
tool.Activated:Fire()
assert(p:GetAttribute("EGGRUMBLE_InvulPhase")=="ARMED","RED_ARM_DIDNT_REACH_SERVER")
assert(runtime.filterDamage(humanoid,21,"ENVIRONMENT","WEATHER")==21,
 "RED_WEATHER_TRIGGERED_EARLY")
assert(runtime.currentPolicySnapshot(p).phase=="ARMED","RED_ARM_NOT_PERSISTED")
advance(101)
local damage=runtime.filterDamage(humanoid,35,"PLAYER","Enemy1")
assert(damage==0,"RED_FIRST_DAMAGE_SHOULD_BE_ZERO")
assert(p:GetAttribute("EGGRUMBLE_InvulPhase")=="AWAKENED","RED_AWAKENING_MISSING")
assert(runtime.currentPolicySnapshot(p).phase=="AWAKENED","RED_POLICY_PHASE_MISSING")
assert(runtime.filterDamage(humanoid,40,"NEUTRAL","SwarmMinion")==0,
 "RED_MULTI_HIT_NEUTRAL_SHOULD_BE_ZERO")
assert(runtime.filterDamage(humanoid,18,"ENVIRONMENT","STORM")==0,
 "RED_DOT_STORM_SHOULD_BE_ZERO")
advance(109)
assert(runtime.filterDamage(humanoid,17,"PLAYER","Enemy1")==17,
 "RED_PERMANENT_IMMUNITY_AFTER_7S")
-- A new charge cannot be minted by re-equip with the same avatar.
runtime.attach(session,p,"WARRIOR")
assert(runtime.currentPolicySnapshot(p).phase=="NONE","RED_REEQUIP_CHEAT")
advance(200)
tool.Activated:Fire()
advance(200.2)
assert(runtime.filterDamage(humanoid,30,"BOSS","StoneGiant")==0,
 "RED_SECOND_CHARGE_MISSING")
assert(runtime.currentPolicySnapshot(p).uses.SKILL==2,"RED_SECOND_CHARGE_COUNTER")
advance(208)
tool.Activated:Fire()
assert(runtime.currentPolicySnapshot(p).phase=="NONE","RED_THIRD_SKILL_FOR_WARRIOR")
humanoid.Died:Fire()
assert(runtime.currentPolicySnapshot(p).phase=="NONE","RED_DEAD_LEAVES_ACTIVE")
advance(300)
assert(runtime.filterDamage(humanoid,33,"PLAYER","Enemy1")==33,
 "RED_DAMAGE_FILTER_AFTER_DEATH")
print("GQ822_REAL_RUNTIME_NATIVE_FREE_TOOL_PREHIT_ZERO_REPEAT_ZERO_EXPIRY_PASS")
'''
def build(policy_path,out):
 policy=Path(policy_path).read_text(encoding="utf-8")
 runtime=RUNTIME.read_text(encoding="utf-8")
 if not policy.rstrip().endswith("return M"):raise ValueError("RED_POLICY_RETURN")
 if not runtime.rstrip().endswith("return Runtime"):raise ValueError("RED_RUNTIME_RETURN")
 p=policy.rstrip()[:-len("return M")]
 r=runtime.rstrip()[:-len("return Runtime")]
 require='local Policy=require(script.Parent:WaitForChild("EGGRUMBLE_InvulnerabilityPolicy"))'
 if r.count(require)!=1:raise ValueError("RED_RUNTIME_IMPORT")
 r=r.replace(require,"local Policy=M",1)
 # Interpose exact mock tool factory only - do NOT rewrite the runtime's skill/damage methods.
 body=HARNESS.replace("__POLICY_SOURCE__",p).replace("__RUNTIME_SOURCE__",r)
 body=body.replace("__TOOL_BIND__","tool=lastCreatedTool")
 body=body.replace('local Instance={}\nfunction Instance.new(kind)',
   'local Instance={}\nlocal lastCreatedTool=nil\nfunction Instance.new(kind)')
 body=body.replace('return {Activated=signal(),Parent=nil,\n  Destroy=function(self) self.Parent=nil end}',
  'lastCreatedTool={Activated=signal(),Parent=nil,\n  Destroy=function(self) self.Parent=nil end}\n return lastCreatedTool')
 # 'tool' local variable exists intentionally; user-facing Tool source remains intact.
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 (out/"good.luau").write_text(body,encoding="utf-8")
 broken=body.replace('if verdict.blocked then','if false then')
 if broken==body:raise ValueError("RED_BAD_DAMAGE_MUTANT")
 (out/"damage_mutant.luau").write_text(broken,encoding="utf-8")
 print("GQ822_ACTUAL_RUNTIME_AND_UPSTREAM_POLICY_NATIVE_HARNESS_GENERATED")
if __name__=="__main__":
 a=argparse.ArgumentParser()
 a.add_argument("--policy",required=True,type=Path)
 a.add_argument("--out",required=True,type=Path)
 args=a.parse_args()
 build(args.policy,args.out)
