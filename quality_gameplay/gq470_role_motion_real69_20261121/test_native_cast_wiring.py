#!/usr/bin/env python3
"""Observe an unchanged full client Source using the fixed 20-case Native contract.

Fixture/case author: /root/runtime_environment. PREP packaging: /root.
This source logic check is not a Roblox engine test or independent approval.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent

FIXTURE_TEXT = r'''-- Native fixture authored by /root/runtime_environment. Product Source is injected
-- byte-exact by run_contract.py. This does not simulate Roblox rendering,
-- Animator scheduling, network replication, or a match/character network epoch.
local Fixture={environments={}}
local Vec={}
local Vector3={}
Vec.__index=function(v,k)
 if k=="Magnitude" then return math.sqrt(v.X*v.X+v.Y*v.Y+v.Z*v.Z) end
 return Vec[k]
end
function Vector3.new(x,y,z) return setmetatable({X=x or 0,Y=y or 0,Z=z or 0},Vec) end
Vec.__add=function(a,b) return Vector3.new(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end
Vec.__sub=function(a,b) return Vector3.new(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end
Vec.__unm=function(a) return Vector3.new(-a.X,-a.Y,-a.Z) end
local function matrixProduct(a,b)
 local r={}
 for row=1,3 do for col=1,3 do
  local n=0
  for k=1,3 do n+=a[(row-1)*3+k]*b[(k-1)*3+col] end
  r[(row-1)*3+col]=n
 end end
 return r
end
local function rotated(m,v)
 return Vector3.new(m[1]*v.X+m[2]*v.Y+m[3]*v.Z,
  m[4]*v.X+m[5]*v.Y+m[6]*v.Z,m[7]*v.X+m[8]*v.Y+m[9]*v.Z)
end
local CFrame={}
local Frame={}
Frame.__index=function(f,k) if k=="Position" then return f.p end return Frame[k] end
local function frame(p,r) return setmetatable({p=p,r=r},Frame) end
function CFrame.new(x,y,z) return frame(Vector3.new(x,y,z),{1,0,0,0,1,0,0,0,1}) end
function CFrame.Angles(x,y,z)
 local sx,cx=math.sin(x),math.cos(x)
 local sy,cy=math.sin(y),math.cos(y)
 local sz,cz=math.sin(z),math.cos(z)
 return frame(Vector3.new(),matrixProduct(matrixProduct({1,0,0,0,cx,-sx,0,sx,cx},
  {cy,0,sy,0,1,0,-sy,0,cy}),{cz,-sz,0,sz,cz,0,0,0,1}))
end
Frame.__mul=function(a,b) return frame(a.p+rotated(a.r,b.p),matrixProduct(a.r,b.r)) end
function Frame:Inverse()
 local m=self.r;local t={m[1],m[4],m[7],m[2],m[5],m[8],m[3],m[6],m[9]}
 return frame(rotated(t,-self.p),t)
end
function Frame:ToObjectSpace(b) return self:Inverse()*b end
function Frame:ToAxisAngle()
 local m=self.r;local angle=math.acos(math.clamp((m[1]+m[5]+m[9]-1)/2,-1,1))
 if angle<1e-8 then return Vector3.new(1,0,0),0 end
 local scale=2*math.sin(angle)
 return Vector3.new((m[8]-m[6])/scale,(m[3]-m[7])/scale,(m[4]-m[2])/scale),angle
end
function Fixture.frameNear(a,b)
 if (a.Position-b.Position).Magnitude>1e-7 then return false end
 for i=1,9 do if math.abs(a.r[i]-b.r[i])>1e-7 then return false end end
 return true
end
local function signal(label)
 local s={label=label,connections={}}
 function s:Connect(fn)
  local c={Connected=true,fn=fn}
  function c:Disconnect() self.Connected=false end
  table.insert(self.connections,c)
  return c
 end
 function s:Fire(...)
  local snapshot=table.clone(self.connections)
  for _,c in ipairs(snapshot) do if c.Connected then c.fn(...) end end
 end
 function s:Count()
  local n=0
  for _,c in ipairs(self.connections) do if c.Connected then n+=1 end end
  return n
 end
 function s:Capture()
  local callbacks={}
  for _,c in ipairs(self.connections) do
   if c.Connected then table.insert(callbacks,c.fn) end
  end
  return callbacks
 end
 return s
end
local function attrs(object)
 object._attrs={}
 function object:GetAttribute(name) return self._attrs[name] end
 function object:SetAttribute(name,value) self._attrs[name]=value end
 return object
end
function Fixture.newRig(env,kind,legacy,distance)
 local rig={kind=kind or "Motor6D",legacy=legacy==true,writes=0,joints={},history={}}
 local model=attrs({Name="Character_"..tostring(#env.rigs+1),Parent=env.workspace})
 local humanoid=attrs({Health=100,Parent=model})
 function humanoid:IsA(name) return name=="Humanoid" end
 local root={Name="HumanoidRootPart",Position=Vector3.new(distance or 0,0,0),Parent=model}
 function root:IsA(name) return name=="BasePart" or name=="Part" end
 local names=if legacy then {"Right Shoulder","Left Shoulder","RootJoint"}
  else {"RightShoulder","LeftShoulder","Waist"}
 local lookup={HumanoidRootPart=root}
 for i,key in ipairs({"right","left","waist"}) do
  local joint={Name=names[i],Parent=model,_Transform=CFrame.new(),writes=0}
  function joint:IsA(name) return name==rig.kind end
  setmetatable(joint,{
   __index=function(t,k) if k=="Transform" then return rawget(t,"_Transform") end end,
   __newindex=function(t,k,v)
    if k=="Transform" then
     rig.writes+=1;env.writes+=1;t.writes+=1
     rawset(t,"_Transform",v)
     table.insert(rig.history,{time=env.now,joint=key,value=v})
    else rawset(t,k,v) end
   end,
  })
  rig.joints[key]=joint;lookup[names[i]]=joint
 end
 function model:FindFirstChild(name,_recursive) return lookup[name] end
 function model:FindFirstChildOfClass(name) return if name=="Humanoid" then humanoid else nil end
 function model:IsA(name) return name=="Model" end
 rig.model=model;rig.humanoid=humanoid;rig.root=root
 function rig:Snapshot()
  return {right=self.joints.right.Transform,left=self.joints.left.Transform,waist=self.joints.waist.Transform}
 end
 function rig:IsIdentity()
  for _,joint in pairs(self.joints) do
   if not Fixture.frameNear(joint.Transform,CFrame.new()) then return false end
  end
  return true
 end
 function rig:Moved() return not self:IsIdentity() end
 table.insert(env.rigs,rig)
 return rig
end
function Fixture.samePose(a,b)
 for _,key in ipairs({"right","left","waist"}) do
  if not Fixture.frameNear(a[key],b[key]) then return false end
 end
 return true
end
function Fixture.new(options)
 options=options or {}
 local env={now=0,writes=0,controlledCallbacks=0,rigs={},roster={}}
 env.workspace={CurrentCamera={CFrame=CFrame.new()}}
 local Players={PlayerAdded=signal("Players.PlayerAdded"),PlayerRemoving=signal("Players.PlayerRemoving")}
 function Players:GetPlayers() return table.clone(env.roster) end
 function Players:GetPlayerByUserId(uid)
  for _,p in ipairs(env.roster) do if p.UserId==uid then return p end end
  return nil
 end
 env.Players=Players
 local RunService={PreSimulation=signal("RunService.PreSimulation")}
 function RunService:IsStudio() return true end
 env.RunService=RunService
 local services={Players=Players,RunService=RunService}
 env.game={}
 function env.game:GetService(name)
  assert(services[name],"UNSUPPORTED_SERVICE:"..name)
  return services[name]
 end
 function env:NewPlayer(uid,role,settings)
  settings=settings or {}
  local p={UserId=uid,Name="Player_"..tostring(uid),Parent=nil,_attrs={EGGRUMBLE_Role=role or "WARRIOR"},_signals={}}
  p.CharacterAdded=signal(p.Name..".CharacterAdded")
  p.CharacterRemoving=signal(p.Name..".CharacterRemoving")
  p.AncestryChanged=signal(p.Name..".AncestryChanged")
  function p:IsA(name) return name=="Player" end
  function p:GetAttribute(name) return self._attrs[name] end
  function p:GetAttributeChangedSignal(name)
   if not self._signals[name] then self._signals[name]=signal(self.Name.."."..name) end
   return self._signals[name]
  end
  function p:SetAttribute(name,value)
   local old=self._attrs[name];self._attrs[name]=value
   if old~=value and self._signals[name] then self._signals[name]:Fire() end
  end
  function p:SetSilently(name,value) self._attrs[name]=value end
  p._rig=Fixture.newRig(self,settings.kind,settings.legacy,settings.distance)
  p.Character=p._rig.model
  if settings.serial~=nil then p._attrs.EGGRUMBLE_BasicCastSerial=settings.serial end
  return p
 end
 function env:AddPlayer(p,fire)
  p.Parent=Players;table.insert(self.roster,p)
  if fire~=false then Players.PlayerAdded:Fire(p) end
 end
 function env:RemovePlayer(p)
  Players.PlayerRemoving:Fire(p)
  for i=#self.roster,1,-1 do if self.roster[i]==p then table.remove(self.roster,i) end end
  p.Parent=nil;p.AncestryChanged:Fire(p,nil)
 end
 function env:RemoveCharacter(p)
  local old=p.Character
  if old then p.CharacterRemoving:Fire(old) end
  p.Character=nil
  if old then old.Parent=nil end
  return p._rig
 end
 function env:AddCharacter(p,settings)
  settings=settings or {}
  local rig=Fixture.newRig(self,settings.kind,settings.legacy,settings.distance)
  p._rig=rig;p.Character=rig.model
  p.CharacterAdded:Fire(rig.model)
  return rig
 end
 function env:SetTime(t) assert(t>=self.now,"CLOCK_MOVED_BACKWARDS");self.now=t end
 function env:Step(t)
  assert(t>=self.now,"CLOCK_MOVED_BACKWARDS")
  local dt=t-self.now;self.now=t
  RunService.PreSimulation:Fire(dt)
 end
 function env:Basic(p,serial) p:SetAttribute("EGGRUMBLE_BasicCastSerial",serial) end
 function env:Skill(p,slot,serial)
  p:SetAttribute("EGGRUMBLE_SkillCastSignature",p:GetAttribute("EGGRUMBLE_Role")..":"..slot..":"..tostring(serial))
 end
 function env:Captured(p,attribute)
  local s=p._signals[attribute]
  return if s then s:Capture() else {}
 end
 function env:DeliverCaptured(callbacks,...)
  -- Controlled local observer scheduling: invoke the ACTUAL saved closures after
  -- disconnect/rebind. No synthetic attribute-value argument is supplied.
  for _,fn in ipairs(callbacks) do self.controlledCallbacks+=1;fn(...) end
 end
 function env:SignalCount(p,attribute)
  local s=p._signals[attribute]
  return if s then s:Count() else 0
 end
 local first=env:NewPlayer(1,options.role,options)
 Players.LocalPlayer=first;env.localPlayer=first
 env:AddPlayer(first,false)
 table.insert(Fixture.environments,env)
 return env
end
local checkCount=0
local function expect(ok,message)
 checkCount+=1
 if not ok then error(message,0) end
end
local function boot(body,options)
 local env=Fixture.new(options)
 body(env)
 return env,env.localPlayer
end
local function poseEquals(rig,expected,message)
 expect(Fixture.samePose(rig:Snapshot(),expected),message)
end
local DURATION={A=.26,B=.48,C=.82}
local ROLES={"WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE"}
local function freshBasic(env,p,serial,time)
 env:SetTime(time);env:Basic(p,serial);env:Step(time+.13)
 return p._rig:Moved()
end
'''
CASES_TEXT = r'''-- Public events and per-rig observations only. No production locals are exported,
-- replaced or directly invoked. Candidate and reference boot their whole Sources.
local cases={}
local function case(name,fn) table.insert(cases,{name=name,fn=fn}) end

case("SKILL_ABC_REFERENCE_TRAJECTORY",function()
 for _,role in ipairs(ROLES) do for _,slot in ipairs({"A","B","C"}) do
  local e,p=boot(candidateBody,{role=role});local c,q=boot(referenceBody,{role=role})
  e:Skill(p,slot,1);c:Skill(q,slot,1)
  for _,t in ipairs({.18,.42,.8}) do
   e:Step(DURATION[slot]*t);c:Step(DURATION[slot]*t)
   poseEquals(p._rig,q._rig:Snapshot(),role..slot.."_REFERENCE_TRAJECTORY_CHANGED")
  end
  expect(p._rig.writes>0 and p._rig:Moved(),role..slot.."_SKILL_POSITIVE_MISSING")
  e:Step(DURATION[slot]+.02);c:Step(DURATION[slot]+.02)
  expect(p._rig:IsIdentity() and q._rig:IsIdentity(),role..slot.."_CLEANUP_CHANGED")
 end end
end)

case("BASIC_SEVEN_ROLES_MATCH_A",function()
 for _,role in ipairs(ROLES) do
  local e,p=boot(candidateBody,{role=role});local c,q=boot(candidateBody,{role=role})
  e:Basic(p,1);c:Skill(q,"A",1)
  for _,t in ipairs({.18,.42,.8}) do
   e:Step(.26*t);c:Step(.26*t)
   poseEquals(p._rig,q._rig:Snapshot(),role.."_BASIC_NOT_OWN_A_CURVE")
  end
  expect(p._rig.writes>0 and p._rig:Moved(),role.."_BASIC_POSITIVE_MISSING")
  e:Step(.3);expect(p._rig:IsIdentity(),role.."_BASIC_NOT_CLEANED")
 end
end)

case("WATCH_TIME_SERIAL_BASELINE",function()
 local e,p=boot(candidateBody,{serial=37})
 e:Step(.13);expect(p._rig.writes==0,"INITIAL_SERIAL_REPLAYED_AT_WATCH")
 e:Basic(p,37);e:Step(.2);expect(p._rig.writes==0,"DUPLICATE_INITIAL_SERIAL_REPLAYED")
 expect(freshBasic(e,p,38,.3),"NEXT_SERIAL_AFTER_WATCH_NOT_ANIMATED")
end)

case("PLAYER_ADDED_SEEDED_BASELINE",function()
 local e=boot(candidateBody)
 local p=e:NewPlayer(99,"MAGE",{serial=77})
 e:AddPlayer(p);e:Step(.13)
 expect(p.Parent==e.Players and p._rig.writes==0,"PLAYER_ADDED_BASELINE_REPLAY_OR_BAD_PARENT")
 expect(freshBasic(e,p,78,.3),"PLAYER_ADDED_FRESH_SERIAL_NOT_ANIMATED")
end)

case("INVALID_SERIAL_DOES_NOT_POISON",function()
 local invalid={{name="NaN",value=0/0},{name="Inf",value=math.huge},
  {name="NegInf",value=-math.huge},{name="Fraction",value=3.5},
  {name="Negative",value=-1},{name="Zero",value=0},{name="String",value="99"},
  {name="Boolean",value=true},{name="Removed",value=nil}}
 for _,row in ipairs(invalid) do
  local e,p=boot(candidateBody,{serial=3})
  e:Basic(p,row.value);e:Step(.13)
  expect(p._rig.writes==0,row.name.."_INVALID_SERIAL_ANIMATED")
  expect(freshBasic(e,p,4,.3),row.name.."_INVALID_POISONED_GOOD_SERIAL")
 end
end)

case("DUPLICATE_AND_REVERSE_SERIAL",function()
 local e,p=boot(candidateBody,{serial=10})
 expect(freshBasic(e,p,11,0),"FRESH_SERIAL11_MISSING")
 e:Step(.3);local writes=p._rig.writes
 e:Basic(p,10);e:Step(.4);e:Basic(p,11);e:Step(.5)
 expect(p._rig.writes==writes and p._rig:IsIdentity(),"DUPLICATE_OR_REVERSE_REPLAYED")
 expect(freshBasic(e,p,12,.6),"SERIAL12_MISSING_AFTER_REVERSE")
end)

case("COUNTERS_BASIC_THEN_SKILL",function()
 local e,p=boot(candidateBody)
 expect(freshBasic(e,p,100,0),"HIGH_BASIC_SEQUENCE_MISSING")
 e:Step(.3);e:Skill(p,"A",1);e:Step(.43)
 expect(p._rig:Moved(),"BASIC_COUNTER_SUPPRESSED_LOWER_SKILL_COUNTER")
end)

case("COUNTERS_SKILL_THEN_BASIC",function()
 local e,p=boot(candidateBody)
 e:Skill(p,"C",50);e:Step(.3444)
 expect(p._rig:Moved(),"HIGH_SKILL_POSITIVE_MISSING")
 e:Step(.9)
 expect(freshBasic(e,p,1,1),"SKILL_COUNTER_SUPPRESSED_FIRST_BASIC")
end)

case("CHARACTER_DROP_AND_NEW_BASELINE",function()
 local e,p=boot(candidateBody)
 expect(freshBasic(e,p,1,0),"OLD_CHARACTER_BASIC_POSITIVE_MISSING")
 local old=e:RemoveCharacter(p)
 expect(old:IsIdentity(),"OLD_CHARACTER_NOT_RESET")
 e:Basic(p,2);e:Step(.2)
 local writes=old.writes;local new=e:AddCharacter(p)
 e:Step(.25)
 expect(new.writes==0 and old.writes==writes,"CHARACTER_ADDED_REPLAYED_PRESENT_SERIAL")
 e:Basic(p,1);e:Basic(p,2);e:Step(.3)
 expect(new.writes==0,"NO_CHARACTER_DROPPED_SERIAL_REPLAYED")
 expect(freshBasic(e,p,3,.4),"NEW_CHARACTER_FRESH_SERIAL_MISSING")
 expect(old.writes==writes,"OLD_RIG_WRITTEN_AFTER_REPLACEMENT")
end)

case("CHARACTER_TOKEN_OLD_CALLBACK",function()
 local e,p=boot(candidateBody,{serial=1})
 local oldCallbacks=e:Captured(p,"EGGRUMBLE_BasicCastSerial")
 expect(#oldCallbacks==1,"BASIC_CALLBACK_NOT_CAPTURED")
 local old=e:RemoveCharacter(p);local new=e:AddCharacter(p)
 local oldWrites=old.writes
 p:SetSilently("EGGRUMBLE_BasicCastSerial",2)
 e:DeliverCaptured(oldCallbacks);e:Step(.13)
 expect(new.writes==0 and old.writes==oldWrites,"OLD_CHARACTER_CALLBACK_WROTE_A_RIG")
 p:GetAttributeChangedSignal("EGGRUMBLE_BasicCastSerial"):Fire()
 e:Step(.26)
 expect(new:Moved(),"OLD_CALLBACK_POISONED_NEW_CHARACTER_SEQUENCE")
 expect(old.writes==oldWrites,"NEW_EVENT_WROTE_OLD_RIG")
end)

case("SAME_UID_NEW_PLAYER_TOKEN",function()
 local e=boot(candidateBody);local old=e:NewPlayer(99,"WARRIOR",{serial=1});e:AddPlayer(old)
 local attr=e:Captured(old,"EGGRUMBLE_BasicCastSerial")
 local removing=old.CharacterRemoving:Capture();local adding=old.CharacterAdded:Capture()
 expect(#attr==1,"OLD_PLAYER_BASIC_CALLBACK_NOT_CAPTURED")
 e:RemovePlayer(old)
 local new=e:NewPlayer(99,"NINJA",{serial=9});e:AddPlayer(new)
 local oldWrites=old._rig.writes
 old:SetSilently("EGGRUMBLE_BasicCastSerial",100)
 new:SetSilently("EGGRUMBLE_BasicCastSerial",10)
 e:DeliverCaptured(attr);e:DeliverCaptured(adding,old.Character);e:Step(.13)
 expect(old._rig.writes==oldWrites and new._rig.writes==0,"OLD_PLAYER_CALLBACK_WROTE_AFTER_REJOIN")
 new:GetAttributeChangedSignal("EGGRUMBLE_BasicCastSerial"):Fire();e:Step(.26)
 expect(new._rig:Moved(),"OLD_PLAYER_CALLBACK_CHANGED_NEW_BINDING_OR_SEQUENCE")
 local pose=new._rig:Snapshot()
 e:DeliverCaptured(removing,old.Character)
 poseEquals(new._rig,pose,"OLD_CHARACTER_REMOVING_CLEARED_NEW_PLAYER_POSE")
 expect(old._rig.writes==oldWrites,"SAME_UID_REJOIN_WROTE_OLD_RIG")
 e:Step(.5)
 expect(freshBasic(e,new,11,.6),"OLD_REMOVING_CALLBACK_BROKE_NEXT_NEW_PLAYER_BASIC")
end)

case("C_PRIORITY_ALL_JOINTS",function()
 local e,p=boot(candidateBody,{role="WARRIOR"});local c,q=boot(candidateBody,{role="WARRIOR"})
 e:Skill(p,"C",1);c:Skill(q,"C",1)
 e:SetTime(.1);e:Basic(p,1)
 for _,t in ipairs({.13,.36,.6,.81}) do
  if t==.36 then e:SetTime(.35);e:Basic(p,2) end
  e:Step(t);c:Step(t)
  poseEquals(p._rig,q._rig:Snapshot(),"BASIC_RESTARTED_SHORTENED_OR_REPLACED_C")
 end
 e:Step(.9);c:Step(.9);local writes=p._rig.writes
 e:Basic(p,1);e:Basic(p,2);e:Step(.95)
 expect(p._rig.writes==writes and p._rig:IsIdentity(),"C_SUPPRESSED_BASIC_SERIAL_NOT_CONSUMED")
 expect(freshBasic(e,p,3,1),"POST_C_FRESH_BASIC_MISSING")
end)

case("EXPIRED_C_RECORD_FRESH_BASIC",function()
 local e,p=boot(candidateBody);local c,q=boot(candidateBody)
 e:Skill(p,"C",1);e:Step(.2)
 e:SetTime(.9);e:Basic(p,1)
 c:SetTime(.9);c:Skill(q,"A",1)
 e:Step(1.03);c:Step(1.03)
 expect(p._rig:Moved(),"EXPIRED_UNRETIRED_C_BLOCKED_FRESH_BASIC")
 poseEquals(p._rig,q._rig:Snapshot(),"EXPIRED_C_DID_NOT_YIELD_TO_FRESH_A")
end)

case("DEAD_DROP_CONSUMES_SERIAL",function()
 local e,p=boot(candidateBody)
 p._rig.humanoid.Health=0;e:Basic(p,1);e:Step(.13)
 expect(p._rig.writes==0,"DEAD_CHARACTER_BASIC_ANIMATED")
 p._rig.humanoid.Health=100;e:Basic(p,0);e:Basic(p,1);e:Step(.2)
 expect(p._rig.writes==0,"DEAD_DROPPED_SERIAL_REPLAYED_ON_REVIVAL")
 expect(freshBasic(e,p,2,.3),"REVIVED_FRESH_SERIAL_MISSING")
end)

case("BUDGET16_DROP_CONSUMES_SERIAL",function()
 local e=boot(candidateBody);local actors={}
 for i=1,17 do local p=e:NewPlayer(100+i,"WARRIOR");e:AddPlayer(p);actors[i]=p end
 for i=1,16 do e:Basic(actors[i],1) end
 e:Step(.13)
 for i=1,16 do expect(actors[i]._rig:Moved(),"IN_BUDGET_BASIC_MISSING_"..i) end
 e:Basic(actors[17],1);e:Step(.2)
 expect(actors[17]._rig.writes==0,"SEVENTEENTH_AVATAR_EXCEEDED_CAP")
 e:Step(.5);e:Basic(actors[17],0);e:Basic(actors[17],1);e:Step(.6)
 expect(actors[17]._rig.writes==0,"OVER_CAP_DROPPED_SERIAL_REPLAYED")
 expect(freshBasic(e,actors[17],2,.7),"AVAILABLE_BUDGET_DID_NOT_ACCEPT_FRESH_SERIAL")
end)

case("DISTANCE130_BOUNDARY",function()
 local e=boot(candidateBody)
 local near=e:NewPlayer(98,"WARRIOR",{distance=130})
 local far=e:NewPlayer(99,"WARRIOR",{distance=130.01})
 e:AddPlayer(near);e:AddPlayer(far);e:Basic(near,1);e:Basic(far,1);e:Step(.13)
 expect(near._rig:Moved(),"130_STUD_BOUNDARY_NOT_INCLUDED")
 expect(far._rig.writes==0,"OUTSIDE130_AVATAR_ANIMATED")
 far._rig.root.Position=Vector3.new();e:Step(.2)
 expect(far._rig.writes==0,"OFFSCREEN_DROPPED_POSE_REPLAYED_ON_RETURN")
 expect(freshBasic(e,far,2,.3),"RETURNED_NEAR_FRESH_BASIC_MISSING")
end)

case("PLAYER_TEARDOWN_DISCONNECTS",function()
 local e=boot(candidateBody);local p=e:NewPlayer(99,"WARRIOR");e:AddPlayer(p)
 e:Skill(p,"A",1);e:Step(.13);expect(p._rig:Moved(),"TEARDOWN_SKILL_POSITIVE_MISSING")
 e:RemovePlayer(p)
 expect(p._rig:IsIdentity(),"REMOVED_PLAYER_POSE_NOT_RESET")
 expect(e:SignalCount(p,"EGGRUMBLE_BasicCastSerial")==0,"BASIC_CONNECTION_LEAK")
 expect(e:SignalCount(p,"EGGRUMBLE_SkillCastSignature")==0,"SKILL_CONNECTION_LEAK")
 expect(p.CharacterAdded:Count()==0 and p.CharacterRemoving:Count()==0,"CHARACTER_CONNECTION_LEAK")
 expect(e.RunService.PreSimulation:Count()==1,"ADDED_OR_REMOVED_RENDER_LOOP")
end)

case("LOCAL_ANCESTRY_TEARDOWN",function()
 local e,localPlayer=boot(candidateBody);local p=e:NewPlayer(99,"WARRIOR");e:AddPlayer(p)
 local saved=e:Captured(p,"EGGRUMBLE_BasicCastSerial")
 e:Skill(p,"C",1);e:Step(.2);expect(p._rig:Moved(),"ANCESTRY_TEARDOWN_POSITIVE_MISSING")
 localPlayer.Parent=nil;localPlayer.AncestryChanged:Fire(localPlayer,nil)
 expect(p._rig:IsIdentity(),"ANCESTRY_TEARDOWN_DID_NOT_RESET")
 for _,actor in ipairs(e.Players:GetPlayers()) do
  expect(e:SignalCount(actor,"EGGRUMBLE_BasicCastSerial")==0,"ANCESTRY_BASIC_CONNECTION_LEAK")
  expect(e:SignalCount(actor,"EGGRUMBLE_SkillCastSignature")==0,"ANCESTRY_SKILL_CONNECTION_LEAK")
  expect(actor.CharacterAdded:Count()==0 and actor.CharacterRemoving:Count()==0,"ANCESTRY_CHARACTER_CONNECTION_LEAK")
 end
 local writes=e.writes;p:SetSilently("EGGRUMBLE_BasicCastSerial",10)
 e:DeliverCaptured(saved);e:Step(.4)
 expect(e.writes==writes,"OLD_CALLBACK_WROTE_AFTER_SCRIPT_TEARDOWN")
end)

case("MOTOR6D_AND_ANIMATIONCONSTRAINT",function()
 for _,settings in ipairs({{kind="Motor6D",legacy=true},{kind="AnimationConstraint",legacy=false}}) do
  settings.role="ZOMBIE"
  local e,p=boot(candidateBody,settings);local c,q=boot(candidateBody,settings)
  e:Basic(p,1);c:Skill(q,"A",1);e:Step(.13);c:Step(.13)
  expect(p._rig:Moved(),settings.kind.."_BASIC_POSE_MISSING")
  poseEquals(p._rig,q._rig:Snapshot(),settings.kind.."_BASIC_DIFFERS_FROM_A")
  e:Step(.3);expect(p._rig:IsIdentity(),settings.kind.."_BASIC_CLEANUP_FAILED")
 end
end)

case("REPEATED_WATCH_CONNECTION_STABILITY",function()
 local e,p=boot(candidateBody,{serial=7})
 e.Players.PlayerAdded:Fire(p);e.Players.PlayerAdded:Fire(p)
 p.CharacterAdded:Fire(p.Character);p.CharacterAdded:Fire(p.Character);e:Step(.13)
 expect(p._rig.writes==0,"REPEATED_WATCH_REPLAYED_PRESENT_SERIAL")
 expect(e:SignalCount(p,"EGGRUMBLE_BasicCastSerial")==1,"BASIC_SUBSCRIPTION_NOT_EXACTLY_ONE")
 expect(e:SignalCount(p,"EGGRUMBLE_SkillCastSignature")==1,"SKILL_SUBSCRIPTION_NOT_EXACTLY_ONE")
 expect(p.CharacterAdded:Count()==1 and p.CharacterRemoving:Count()==1,"LIFECYCLE_SUBSCRIPTION_NOT_EXACTLY_ONE")
 expect(freshBasic(e,p,8,.3),"REPEATED_WATCH_DROPPED_FRESH_BASIC")
 expect(e.RunService.PreSimulation:Count()==1,"REPEATED_WATCH_ADDED_LOOP")
end)

assert(#cases==20,"CONTRACT_CASE_COUNT_CHANGED")
local passed,failed=0,0
for _,entry in ipairs(cases) do
 checkCount=0;Fixture.environments={}
 local ok,reason=pcall(entry.fn)
 local writes,callbacks=0,0
 for _,e in ipairs(Fixture.environments) do writes+=e.writes;callbacks+=e.controlledCallbacks end
 if ok then passed+=1 else failed+=1 end
 local status=if ok then "PASS" else "FAIL"
 local detail=if ok then "OBSERVED_PUBLIC_EVENT_CONTRACT" else tostring(reason):gsub("[\t\r\n]"," ")
 print("CASE",entry.name,status,detail)
 print("TRACE",entry.name,"checks",checkCount,"joint_writes",writes,"controlled_callbacks",callbacks)
end
print("CONTRACT_SUMMARY",#cases,passed,failed)
if failed>0 then error("BASIC_PRESENTATION_CONTRACT_NOT_SATISFIED",0) end
'''
LUAU_SOURCE_COMMIT = "f46d879e28302a430029304f7f6a162aed66f103"
LUAU_SOURCE_TREE = "2432c996fc9fa73680b5e2cfe172d36114fe3746"
REFERENCES = {
    "95e5dba544a759547ea41e8ecec1984317fc61b35281f4533b2323df1951491f": "H93_ORIGINAL_6764",
    "1856594a79d2e7ab7d4f6ac386c9379a45a8647a4168f65354246e888428bffb": "ORIGINAL943_8662",
}
CASES = [
    "SKILL_ABC_REFERENCE_TRAJECTORY", "BASIC_SEVEN_ROLES_MATCH_A",
    "WATCH_TIME_SERIAL_BASELINE", "PLAYER_ADDED_SEEDED_BASELINE",
    "INVALID_SERIAL_DOES_NOT_POISON", "DUPLICATE_AND_REVERSE_SERIAL",
    "COUNTERS_BASIC_THEN_SKILL", "COUNTERS_SKILL_THEN_BASIC",
    "CHARACTER_DROP_AND_NEW_BASELINE", "CHARACTER_TOKEN_OLD_CALLBACK",
    "SAME_UID_NEW_PLAYER_TOKEN", "C_PRIORITY_ALL_JOINTS",
    "EXPIRED_C_RECORD_FRESH_BASIC", "DEAD_DROP_CONSUMES_SERIAL",
    "BUDGET16_DROP_CONSUMES_SERIAL", "DISTANCE130_BOUNDARY",
    "PLAYER_TEARDOWN_DISCONNECTS", "LOCAL_ANCESTRY_TEARDOWN",
    "MOTOR6D_AND_ANIMATIONCONSTRAINT", "REPEATED_WATCH_CONNECTION_STABILITY",
]
REL = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_ProceduralSkills.client.luau"


def identity(raw: bytes) -> dict:
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def snapshot(root: Path) -> dict:
    found = {}
    for path in sorted(root.rglob("*.luau")):
        if path.is_symlink() or not path.is_file():
            raise ValueError("SOURCE_REGULAR_FILE_REQUIRED:" + str(path))
        found[path.relative_to(root).as_posix()] = identity(path.read_bytes())
    if len(found) != 69 or REL not in found:
        raise ValueError("EXPECTED_ACTUAL69_SOURCE_SNAPSHOT")
    return found


def command(argv: list[str], output: Path, prefix: str, timeout: int = 60) -> dict:
    started = utc()
    result = subprocess.run(argv, capture_output=True, timeout=timeout)
    (output / (prefix + ".stdout.log")).write_bytes(result.stdout)
    (output / (prefix + ".stderr.log")).write_bytes(result.stderr)
    return {"argv": argv, "started_at_utc": started, "finished_at_utc": utc(),
            "exit_code": result.returncode, "stdout": identity(result.stdout),
            "stderr": identity(result.stderr)}


def parse_output(raw: bytes) -> tuple[list[dict], list[dict], dict]:
    lines = raw.decode("utf-8").splitlines()
    case_rows, traces, summaries = [], [], []
    for line in lines:
        values = line.split("\t")
        if values[0] == "CASE":
            if len(values) != 4 or values[2] not in {"PASS", "FAIL"}:
                raise ValueError("MALFORMED_CASE_ROW")
            case_rows.append({"name": values[1], "status": values[2], "detail": values[3]})
        elif values[0] == "TRACE":
            if (len(values) != 8 or values[2::2] != ["checks", "joint_writes", "controlled_callbacks"]
                    or not all(x.isdigit() for x in values[3::2])):
                raise ValueError("MALFORMED_FIXED_TRACE_ROW")
            traces.append({"name": values[1], **{values[i]: int(values[i + 1]) for i in (2, 4, 6)}})
        elif values[0] == "CONTRACT_SUMMARY":
            if len(values) != 4 or not all(x.isdigit() for x in values[1:]):
                raise ValueError("MALFORMED_SUMMARY")
            summaries.append({"total": int(values[1]), "passed": int(values[2]), "failed": int(values[3])})
        else:
            raise ValueError("UNEXPECTED_NATIVE_OUTPUT:" + line[:120])
    if [x["name"] for x in case_rows] != CASES or [x["name"] for x in traces] != CASES:
        raise ValueError("EXACT_CASE_AND_TRACE_ORDER_REQUIRED")
    if len(summaries) != 1:
        raise ValueError("EXACT_ONE_SUMMARY_REQUIRED")
    summary = summaries[0]
    passed = sum(x["status"] == "PASS" for x in case_rows)
    if summary != {"total": 20, "passed": passed, "failed": 20 - passed}:
        raise ValueError("SUMMARY_NOT_OBSERVED_CASE_VECTOR")
    return case_rows, traces, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--luau", type=Path, required=True)
    parser.add_argument("--compiler", type=Path, required=True)
    parser.add_argument("--luau-source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--expect", choices=("red", "green"), required=True)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    source_root, reference, luau, compiler, luau_source, out = [
        value.absolute() for value in (args.source_root, args.reference, args.luau,
                                      args.compiler, args.luau_source, args.out)]
    if out.exists() or out.is_symlink() or out.is_relative_to(source_root):
        raise ValueError("NEW_OUTPUT_OUTSIDE_SOURCE_ROOT_REQUIRED")
    source = source_root / REL
    before = snapshot(source_root)
    source_raw, reference_raw = source.read_bytes(), reference.read_bytes()
    reference_id = identity(reference_raw)
    if reference_id["sha256"] not in REFERENCES:
        raise ValueError("REFERENCE_MUST_BE_UNCHANGED_H93_OR_ORIGINAL943")
    fixture_raw = FIXTURE_TEXT.encode()
    cases_raw = CASES_TEXT.encode()
    runner_raw = Path(__file__).read_bytes()
    source_head = subprocess.check_output(["git", "-C", str(luau_source), "rev-parse", "HEAD"], text=True).strip()
    source_tree = subprocess.check_output(["git", "-C", str(luau_source), "rev-parse", "HEAD^{tree}"], text=True).strip()
    source_dirty = subprocess.check_output(["git", "-C", str(luau_source), "status", "--porcelain", "--untracked-files=no"], text=True)
    if source_head != LUAU_SOURCE_COMMIT or source_tree != LUAU_SOURCE_TREE or source_dirty:
        raise ValueError("PINNED_CLEAN_F46_SOURCE_REQUIRED")
    out.mkdir(parents=True, exist_ok=False)
    segments = [fixture_raw]
    embeddings = {}
    for name, raw in (("candidateBody", source_raw), ("referenceBody", reference_raw)):
        wrapper = ("\nlocal function " + name + "(env)\n"
                   " local game=env.game\n local workspace=env.workspace\n"
                   " local os={clock=function() return env.now end}\n"
                   " -- BEGIN BYTE-EXACT PRODUCT SOURCE\n").encode()
        segments.append(wrapper)
        start = sum(len(x) for x in segments)
        segments.append(raw)
        embeddings[name] = {"start": start, "end": start + len(raw), **identity(raw)}
        segments.append(b"\n -- END BYTE-EXACT PRODUCT SOURCE\nend\n")
    segments.append(b"\n" + cases_raw)
    generated = b"".join(segments)
    for name, raw in (("candidateBody", source_raw), ("referenceBody", reference_raw)):
        row = embeddings[name]
        if generated[row["start"]:row["end"]] != raw:
            raise ValueError("EMBEDDED_SOURCE_NOT_EXACT")
    program = out / "contract.luau"
    program.write_bytes(generated)
    compile_result = command([str(compiler), "--text", str(program)], out, "compile")
    if compile_result["exit_code"] != 0:
        raise ValueError("GENERATED_PROGRAM_COMPILE_FAILED")
    native_result = command([str(luau), str(program)], out, "native")
    case_rows, traces, summary = parse_output((out / "native.stdout.log").read_bytes())
    by_name = {row["name"]: row for row in case_rows}
    if args.expect == "green":
        expected = native_result["exit_code"] == 0 and summary["failed"] == 0
    else:
        expected = (native_result["exit_code"] != 0 and summary["failed"] > 0
                    and by_name["SKILL_ABC_REFERENCE_TRAJECTORY"]["status"] == "PASS"
                    and by_name["BASIC_SEVEN_ROLES_MATCH_A"]["status"] == "FAIL")
    input_unchanged = (before == snapshot(source_root) and reference.read_bytes() == reference_raw
                       and FIXTURE_TEXT.encode() == fixture_raw
                       and CASES_TEXT.encode() == cases_raw
                       and Path(__file__).read_bytes() == runner_raw)
    report = {
        "schema": "BASIC_PRESENTATION_FULL_CLIENT_OBSERVER_CONTRACT_V1",
        "label": args.label, "observed_at_utc": utc(), "expected_result": args.expect,
        "expectation_observed": expected, "all_twenty_contracts_passed": summary["failed"] == 0,
        "fixture_author_context": "/root/runtime_environment", "approval_claimed": False,
        "product_source_modified": False, "source_root": str(source_root),
        "source": {"path": str(source), **identity(source_raw)},
        "reference": {"path": str(reference), "profile": REFERENCES[reference_id["sha256"]], **reference_id},
        "fixture": {"path": "EMBEDDED:fixture.luau", **identity(fixture_raw)},
        "cases": {"path": "EMBEDDED:cases.luau", **identity(cases_raw)},
        "runner": identity(runner_raw), "generated": identity(generated),
        "embeddings": embeddings, "case_names": CASES, "case_results": case_rows,
        "fixed_trace_schema": ["TRACE", "case_name", "checks", "integer", "joint_writes", "integer", "controlled_callbacks", "integer"],
        "traces": traces, "summary": summary, "compile": compile_result, "native": native_result,
        "cached_native_binary": {"path": str(luau), **identity(luau.read_bytes())},
        "compiler": {"path": str(compiler), **identity(compiler.read_bytes())},
        "luau_source": {"path": str(luau_source), "commit": source_head, "tree": source_tree, "tracked_clean": True},
        "all69_sources_before": before, "all_inputs_unchanged": input_unchanged,
        "fresh_toolchain_build_admission": False, "official_rc_adoption_proven": False,
        "studio_verified": False, "android_verified": False, "rendering_verified": False,
        "observer_scheduling_scope": "Captured actual local callbacks invoked after disconnect/rebind without an invented event-value argument",
        "network_stale_event_fence_proven": False,
        "limitations": [
            "Motor6D/AnimationConstraint branch and property behavior only; no engine rendering or Animator order",
            "A serial has no originating avatar/match/role snapshot; delayed larger replicated serial cannot be attributed by this fixture",
            "Invalid attributes are synthetic observer-contract inputs, not proof Roblox transports every invalid value",
            "Expected RED preserves the missing BASIC defect; it is not a green product contract result",
        ],
    }
    (out / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"label": args.label, "summary": summary, "expected": args.expect,
                      "expectation_observed": expected, "inputs_unchanged": input_unchanged,
                      "native_exit": native_result["exit_code"], "report": str(out / "REPORT.json")}))
    return 0 if expected and input_unchanged else 1


if __name__ == "__main__":
    raise SystemExit(main())
