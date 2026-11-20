#!/usr/bin/env python3
"""Source-derived actual Luau VM tests for Mage rescue; 3-second hold is
engine-owned by ProximityPrompt, tested here for server-side acceptance only."""
from pathlib import Path
import argparse
SOURCE=Path(__file__).with_name("EGGRUMBLE_MageRevive.luau")
HARNESS=r'''
local time=100
local os={clock=function() return time end}
local function signal()
 local a={subs={}}
 function a:Connect(f)
  local entry={fn=f,on=true}
  table.insert(self.subs,entry)
  return {Disconnect=function() entry.on=false end}
 end
 function a:Fire(...)
  for _,entry in ipairs(self.subs) do if entry.on then entry.fn(...) end end
 end
 return a
end
local Players={roster={}}
function Players:GetPlayers() return self.roster end
local Heartbeat=signal()
local RunService={Heartbeat=Heartbeat}
local Workspace={blocked=false}
function Workspace:Raycast() return self.blocked and {Instance={}} or nil end
local game={GetService=function(self,name)
 if name=="Players" then return Players end
 if name=="RunService" then return RunService end
 if name=="Workspace" then return Workspace end
 error("RED_UNRECOGNIZED_SERVICE:"..name)
end}
local Enum={RaycastFilterType={Exclude=1},Font={GothamBold=1}}
local RaycastParams={new=function() return {} end}
local UDim2={fromOffset=function(x,y)return{x=x,y=y} end,
 fromScale=function(x,y)return{x=x,y=y} end}
local Color3={fromRGB=function(r,g,b)return {r,g,b} end}
local Vector3={new=function(x,y,z)return setmetatable({x=x,y=y,z=z},{
 __sub=function(a,b)
  local dx,dy,dz=a.x-b.x,a.y-b.y,a.z-b.z
  return {Magnitude=math.sqrt(dx*dx+dy*dy+dz*dz)}
 end})end}
local Instance={}
function Instance.new(kind)
 local o={ClassName=kind,children={},Destroy=function(self)self.Parent=nil end}
 function o:IsA(n) return self.ClassName==n end
 function o:FindFirstChild(n) return self.children[n] end
 if kind=="ProximityPrompt" then o.Triggered=signal() end
 return o
end
__MODULE__
local mod=Rescue
local spec=mod.policy()
assert(spec.threshold==.20 and spec.window==60,"RED_DOWNED_CONTRACT")
assert(spec.hold==3 and spec.heal==.35 and spec.cooldown==40,"RED_REVIVE_CONTRACT")
local function player(id,role,team,x)
 local p={Parent=Players,UserId=id,attrs={
  EGGRUMBLE_Role=role,EGGRUMBLE_QueuedMode="TEAM",
  EGGRUMBLE_Eliminated=false},
  CharacterRemoving=signal()}
 function p:GetAttribute(k)return self.attrs[k] end
 function p:SetAttribute(k,v)self.attrs[k]=v end
 function p:FindFirstChildOfClass(n)
  if n=="Backpack" then return self.bag end
 end
 local h={Health=100,MaxHealth=100,WalkSpeed=16,
  JumpPower=50,JumpHeight=7.2,AutoRotate=true,
  HealthChanged=signal(),Died=signal(),attrs={}}
 function h:GetAttribute(k)return self.attrs[k] end
 function h:SetAttribute(k,v)self.attrs[k]=v end
 local root={ClassName="Part",Position=Vector3.new(x,0,0)}
 function root:IsA(n)return n=="BasePart" end
 local c={children={},primary=root,hum=h}
 function c:FindFirstChild(n)
  if n=="HumanoidRootPart" then return root end
  return self.children[n]
 end
 function c:FindFirstChildOfClass(n)
  if n=="Humanoid" then return h end
 end
 function c:GetChildren()return {}end
 h.Parent=c
 p.Character=c
 p.bag={GetChildren=function()return {}end}
 return p,h,c,root
end
local patient,h,c,root=player(11,"WARRIOR","RED",0)
local healer,mage,mc,mr=player(12,"MAGE","RED",4)
local enemy,eh,ec,er=player(13,"MAGE","BLUE",3)
Players.roster={patient,healer,enemy}
local session={world={Parent={},Destroying=signal()},
 mode="TEAM",rules={phase="ACTIVE",castles={
 ["11"]={alive=true,team="RED"},
 ["12"]={alive=true,team="RED"},
 ["13"]={alive=true,team="BLUE"}}}}
mod.attach(session,patient,"WARRIOR")
h.Health=18;h.HealthChanged:Fire(18)
assert(patient:GetAttribute("EGGRUMBLE_Downed")==true,"RED_NO_DOWNED")
assert(h.WalkSpeed==0 and h.JumpPower==0,"RED_DOWNED_CAN_MOVE")
local prompt=active[patient].prompt
assert(prompt.HoldDuration==3,"RED_FAST_REVIVE")
assert(prompt.MaxActivationDistance<=12,"RED_PROMPT_TOO_FAR")
time=104
prompt.Triggered:Fire(enemy)
assert(patient:GetAttribute("EGGRUMBLE_Downed")==true,"RED_ENEMY_REVIVE")
Workspace.blocked=true
prompt.Triggered:Fire(healer)
assert(patient:GetAttribute("EGGRUMBLE_Downed")==true,"RED_WALLHACK_REVIVE")
Workspace.blocked=false
prompt.Triggered:Fire(patient)
assert(patient:GetAttribute("EGGRUMBLE_Downed")==true,"RED_SELF_REVIVE")
prompt.Triggered:Fire(healer)
assert(patient:GetAttribute("EGGRUMBLE_Downed")==false,"RED_MAGE_REVIVE_FAILED")
assert(h.Health>=35,"RED_REVIVE_HP")
assert(h.WalkSpeed==16 and h.JumpPower==50,"RED_MOVEMENT_NOT_RESTORED")
assert(patient:GetAttribute("EGGRUMBLE_RevivedBy")==12,"RED_FALSE_REVIVE_CREDIT")
h.Health=18;h.HealthChanged:Fire(18)
assert(patient:GetAttribute("EGGRUMBLE_Downed")==true,"RED_SECOND_DOWN")
local second=active[patient].prompt
time=105
second.Triggered:Fire(healer)
assert(patient:GetAttribute("EGGRUMBLE_Downed")==true,"RED_MAGE_COOLDOWN")
time=145
second.Triggered:Fire(healer)
assert(patient:GetAttribute("EGGRUMBLE_Downed")==false,"RED_MAGE_COOLDOWN_NEVER_EXPIRES")
h.Health=18;h.HealthChanged:Fire(18)
assert(patient:GetAttribute("EGGRUMBLE_Downed")==true,"RED_THIRD_DOWN")
time=206
Heartbeat:Fire(.25)
assert(h.Health==0 and patient:GetAttribute("EGGRUMBLE_Downed")==false,
 "RED_RESCUE_EXPIRED_NO_NORMAL_DEATH")
print("GQ8_MAGE_REVIVE_REAL_VM_TEAM_CROSS_TEAM_LOS_COOLDOWN_60S_PASS")
'''
def generate(out:Path):
 src=SOURCE.read_text(encoding="utf-8")
 if not src.rstrip().endswith("return Rescue"):raise ValueError("RED_RESCUE_RETURN")
 body=src.rstrip()[:-len("return Rescue")]
 # Emit actual runtime source, with no fabricated implementation.
 out.mkdir(parents=True,exist_ok=True)
 good=HARNESS.replace("__MODULE__",body)
 (out/"good.luau").write_text(good,encoding="utf-8")
 mutant=body.replace('local MAGE_COOLDOWN_SECONDS=40','local MAGE_COOLDOWN_SECONDS=0')
 if mutant==body:raise ValueError("RED_MUTANT_PATTERN_MISSING")
 (out/"mutant.luau").write_text(HARNESS.replace("__MODULE__",mutant).replace("spec.cooldown==40","spec.cooldown==0"),encoding="utf-8")
 print("GQ8_MAGE_REVIVE_SOURCE_DERIVED_HARNESS_READY")
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--out",type=Path,required=True)
 generate(p.parse_args().out)
