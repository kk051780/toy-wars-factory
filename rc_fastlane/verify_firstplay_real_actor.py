#!/usr/bin/env python3
"""Source-exact production bot actor factory + Bot.start/stop native lifecycle QA.

The real makeActor/tagPart/motor, real showCarriedEgg/clearCarry, actual
Bot.start/stop and releasePathLease are exercised with Roblox Instance/CFrame
emulation. Tests model/parts/joints/Humanoids/parent cleanup, not Studio render
or physics.
"""
from __future__ import annotations
import argparse
from pathlib import Path

def part(text: str,begin: str,end: str) -> str:
    a=text.index(begin); b=text.index(end,a+len(begin))
    assert b>a; return text[a:b]

def verify(dist: Path,out: Path):
    s=(dist/"src/server/SoloTeamBots.luau").read_text("utf8")
    actor=part(s,'local function tagPart(', 'local function releasePathLease(')
    lease=part(s,'local function releasePathLease(', 'local function invalidatePath(')
    carry=part(s,'local function showCarriedEgg(', 'function Bot.stop()')
    stop=part(s,'function Bot.stop()','function Bot.start(')
    start=part(s,'function Bot.start(','local function alive(bot)')
    for term in ('Instance.new("Part")','Instance.new("Model")',
        'Instance.new("Humanoid")','Instance.new("WeldConstraint")',
        'Instance.new("Motor6D")','m.PrimaryPart=root',
        'm:GetDescendants()','part:SetNetworkOwner(nil)'):
        assert term in actor,("ACTOR_FACTORY_DRIFT",term)
    assert 'releasePathLease(bot)' in stop
    assert 'clearCarry(bot)' in stop
    assert 'bot.model:Destroy()' in stop
    assert 'folder:Destroy()' in stop
    assert '#bots==MAX_BOTS' in start
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text("\n".join((MOCK,actor,lease,carry,stop,start,CASES)),"utf8")
    print("P0D_SOLO_ACTUAL_PRODUCTION_ACTOR_AND_STOP_EXACT_PASS")

MOCK=r'''
--!nocheck
local V
V=function(x,y,z)
  return setmetatable({X=x,Y=y,Z=z},{
    __add=function(a,b) return V(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end
  })
end
local Vector3={}
function Vector3.new(x,y,z) return V(x,y,z) end
local cfMeta={}
cfMeta.__mul=function(a,b)
  return setmetatable({Position=a.Position+b.Position},cfMeta)
end
local CFrame={}
function CFrame.new(x,y,z)
  return setmetatable({Position=V(x or 0,y or 0,z or 0)},cfMeta)
end
local Color3={}
function Color3.fromRGB(r,g,b) return {r=r,g=g,b=b} end
function Color3.new(r,g,b) return {r=r,g=g,b=b} end
local Enum={
 Material={Metal="Metal",SmoothPlastic="SmoothPlastic",Glass="Glass"},
 PartType={Ball="Ball"},HumanoidRigType={R6="R6"},
 HumanoidDisplayDistanceType={None="None"}
}
local modelsCreated=0
local humanoidsCreated=0
local motorsCreated=0
local weldsCreated=0
local partNetworkOwnershipCalls=0
local modelRefs={}
local instanceMeta={}
instanceMeta.__newindex=function(o,k,v)
  rawset(o,k,v)
  if k=="Parent" and v and v.children then table.insert(v.children,o) end
end
instanceMeta.__index=function(o,k)
  if o.children then
    for _,kid in ipairs(o.children) do
      if kid.Name==k then return kid end
    end
  end
  return nil
end
local Instance={}
function Instance.new(className)
  if className=="Model" then modelsCreated+=1 end
  if className=="Humanoid" then humanoidsCreated+=1 end
  if className=="Motor6D" then motorsCreated+=1 end
  if className=="WeldConstraint" then weldsCreated+=1 end
  local o=setmetatable({ClassName=className,children={}},instanceMeta)
  function o:SetAttribute(key,val)
    if self.attrs==nil then self.attrs={} end
    self.attrs[key]=val
  end
  function o:GetAttribute(key) return self.attrs and self.attrs[key] end
  function o:IsA(other)
    return self.ClassName==other or
      (other=="BasePart" and self.ClassName=="Part")
  end
  function o:GetDescendants()
    local result={}
    local function walk(node)
      for _,c in ipairs(node.children or {}) do
        table.insert(result,c); walk(c)
      end
    end
    walk(self)
    return result
  end
  function o:SetNetworkOwner(owner)
    partNetworkOwnershipCalls+=1
    self.networkOwner=owner
  end
  function o:Destroy() self.Parent=nil; self.destroyed=true end
  if className=="Model" then table.insert(modelRefs,o) end
  return o
end
local Players={online={}}
function Players:GetPlayers() return self.online end
local RunService={}
function RunService:IsStudio() return true end
local function makePlayer(team,late)
  local p={Team=team and {Name=team},attrs={P0D_LateJoinSpectator=late}}
  function p:GetAttribute(k) return self.attrs[k] end
  return p
end
local human=makePlayer("RED",false)
local spectator=makePlayer(nil,true)
local second=makePlayer("BLUE",false)
local Bot={}
local folder=nil
local bots={}
local map=nil
local callbacks=nil
local epoch=0
local active=false
local lastTick=-math.huge
local MAX_BOTS=5
local inflightPaths=0
local world={model=Instance.new("Folder"),
   teams={RED={spawn=CFrame.new(-30,0,0)},
          BLUE={spawn=CFrame.new(30,0,0)}}}
local authority={
 steal=function() end,deposit=function() end,drop=function() end,
 attackHuman=function() end,attackBot=function() end
}
local function check(ok,label)
  assert(ok,"P0D_ACTUAL_ACTOR_LIFECYCLE_FAILED_"..label)
end
'''
CASES=r'''
Players.online={human,spectator}
check(Bot.start(world,"RED",authority)==true,"REAL_START_SUCCEEDS")
check(active and #bots==5,"REAL_5_BOTS")
check(modelsCreated==5 and humanoidsCreated==5,
  "REAL_FACTORY_CREATED_FIVE_MODELS_AND_HUMANOIDS")
check(motorsCreated>=5*6 and weldsCreated>=5*1,
  "REAL_FACTORY_CREATED_ANIMATED_JOINTS")
check(partNetworkOwnershipCalls>=5*7,
  "REAL_FACTORY_SERVER_OWNERSHIP_SET_FOR_PARTS")
check(folder~=nil and folder.Parent==world.model,
  "REAL_BOT_FOLDER_ATTACHED_TO_MAP")
local allies=0; local opponents=0
for _,b in ipairs(bots) do
  if b.team=="RED" then allies+=1 else opponents+=1 end
  check(b.model.ClassName=="Model" and b.model.PrimaryPart==b.root,
    "ACTOR_MODEL_PRIMARYPART_REAL")
  check(b.model.Humanoid==b.hum
    and b.hum.RigType==Enum.HumanoidRigType.R6,
    "ACTOR_HAS_REAL_R6_HUMANOID")
  check(b.model.Head~=nil and b.model.Torso~=nil
    and b.model["Left Arm"]~=nil and b.model["Right Leg"]~=nil,
    "ACTOR_REAL_BODY_PARTS_PRESENT")
  check(b.model:GetAttribute("P0D_StudioSoloBot")==true
    and b.model:GetAttribute("P0D_BotTeam")==b.team,
    "ACTOR_TEAM_TAGS_PRESENT")
end
check(allies==2 and opponents==3,"REAL_FORMATION_TWO_VS_THREE")
local previousModels={}
for _,b in ipairs(bots) do table.insert(previousModels,b.model) end
local previousFolder=folder
Players.online={human,second}
check(Bot.start(world,"RED",authority)==false,
  "TWO_ELIGIBLE_START_FAIL_CLOSED")
check(not active and #bots==0 and folder==nil,
  "REAL_BOT_STOP_CLEARS_ALL_ROSTER_AND_FOLDER")
check(previousFolder.destroyed==true,
  "REAL_BOT_STOP_DESTROYS_FOLDER")
local deadModels=0
for _,m in ipairs(previousModels) do
  if m.destroyed and m.Parent==nil then deadModels+=1 end
end
check(deadModels==5,"REAL_BOT_STOP_DESTROYS_ALL_FIVE_MODELS")
Players.online={human,spectator}
check(Bot.start(world,"RED",authority)==true,
  "REAL_RESTART_AFTER_FAILED_START")
check(#bots==5 and active,"REAL_RESTART_REBUILDS_ALL_MODELS")
Bot.stop()
check(#bots==0 and folder==nil and not active,
  "REAL_STOP_IDEMPOTENT_CLEANUP")
check(inflightPaths==0,"STOP_RELEASED_ALL_LEASES")
print("P0D_REAL_BOT_ACTOR_START_STOP_19_NATIVE_CASES_PASS")
'''
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    verify(a.dist,a.out)
