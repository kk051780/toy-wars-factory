#!/usr/bin/env python3
"""Exercise the REAL observer Luau source with headless Roblox service/event mocks.

Native Luau VM verifies behavior, not visual Roblox Studio or Android rendering.
No game source or competing #488 integrity observer is copied/reimplemented.
"""
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "EGGRUMBLE_StudioLiveObserver.server.luau"
ANCHOR = "snapshot()\ntask.spawn(function()"

PRELUDE = r"""
-- Native Luau mock services; original observer source follows without function stubs.
local function signal()
 local obj={listeners={}}
 function obj:Connect(fn)
  table.insert(self.listeners,fn)
  return {Disconnect=function() end}
 end
 function obj:Fire(...)
  for _,fn in ipairs(self.listeners) do fn(...) end
 end
 return obj
end
local function node(className,name)
 local o={ClassName=className,Name=name,Parent=nil,children={},attributes={},
  ChildAdded=signal(),DescendantAdded=signal()}
 function o:IsA(x) return self.ClassName==x end
 function o:FindFirstChild(name)
  for _,v in ipairs(self.children) do
   if v.Parent==self and v.Name==name then return v end
  end
  return nil
 end
 function o:FindFirstChildOfClass(c)
  for _,v in ipairs(self.children) do
   if v.Parent==self and v:IsA(c) then return v end
  end
  return nil
 end
 function o:GetDescendants()
  local found={}
  local function visit(parent)
   for _,v in ipairs(parent.children) do
    if v.Parent==parent then
     table.insert(found,v)
     visit(v)
    end
   end
  end
  visit(self)
  return found
 end
 function o:GetAttribute(k) return self.attributes[k] end
 function o:GetPropertyChangedSignal(k)
  self.propertySignals=self.propertySignals or {}
  if not self.propertySignals[k] then self.propertySignals[k]=signal() end
  return self.propertySignals[k]
 end
 return o
end
local function attach(parent,child)
 child.Parent=parent
 table.insert(parent.children,child)
 parent.ChildAdded:Fire(child)
 local cursor=parent
 while cursor do
  cursor.DescendantAdded:Fire(child)
  cursor=cursor.Parent
 end
end
local function detach(parent,child)
 for i,v in ipairs(parent.children) do
  if v==child then table.remove(parent.children,i) break end
 end
 child.Parent=nil
end
local workspace=node("Workspace","Workspace")
local previewRoot=node("Folder","EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW")
attach(workspace,previewRoot)
local ServerStorage=node("ServerStorage","ServerStorage")
local Players={list={}}
function Players:GetPlayers() return self.list end
local RunService={}
function RunService:IsStudio() return true end
local lastEncodedData=nil
local HttpService={}
function HttpService:JSONEncode(data)
 lastEncodedData=data
 return "NATIVE_MOCK_JSON"
end
local game={}
function game:GetService(which)
 if which=="RunService" then return RunService end
 if which=="Players" then return Players end
 if which=="ServerStorage" then return ServerStorage end
 if which=="HttpService" then return HttpService end
 error("unexpected GetService: "..tostring(which))
end
local Instance={}
function Instance.new(className) return node(className,className) end
local task={}
function task.spawn(_callback) end -- do not run an infinite polling loop in headless VM.
function task.wait(_seconds) error("unexpected background loop") end
"""

TESTS = r"""
-- Injected at source's initial snapshot / background scheduling boundary.
-- All observer functions above are the ORIGINAL real-source implementations.
local checks=0
local function verify(condition,message)
 checks+=1
 if not condition then error("OBSERVER_NATIVE_ASSERT_"..tostring(checks)..": "..message) end
end
local function makeArena(mode)
 local arena=node("Folder",mode.."_Arena")
 attach(previewRoot,arena) -- event observer hooks this arena in real source
 return arena
end
local function makeHumanoid(arena,kind,index)
 local model=node("Model",if kind=="neutral" then "HordeSoldier" else "AI_Actor_"..tostring(index))
 if kind=="neutral" then
  model.attributes.EGGRUMBLE_Neutral=true
 else
  model.attributes.EGGRUMBLE_BotId=index
 end
 attach(arena,model)
 local h=node("Humanoid","Humanoid")
 h.Health=32
 h.HealthChanged=signal()
 h.Died=signal()
 attach(model,h)
 return h
end
local function makeItem(arena)
 local folder=node("Folder","EGGRUMBLE_FieldItems")
 attach(arena,folder)
 local part=node("BasePart","ITEM_1_HEAL")
 part.CanQuery=true
 part.Transparency=0
 attach(folder,part)
 return part
end
local p=node("Player","test_player")
p.UserId=70
p.attributes.EGGRUMBLE_SelectedRole="NINJA"
p.attributes.EGGRUMBLE_Role="NINJA"
p.attributes.EGGRUMBLE_QueuedMode="TEAM"
p.attributes.EGGRUMBLE_NeutralKOs=14 -- old aggregate may persist across rounds
table.insert(Players.list,p)

verify(lastEncodedData.schema=="EGGRUMBLE_STUDIO_LIVE_OBSERVER_V1","source startup snapshot")
verify(scanMode("TEAM").state=="NOT_STARTED","initially no TEAM")
local roundA=makeArena("TEAM")
verify(scanMode("TEAM").roundSequence==1,"first TEAM sequence")
local soldierA=makeHumanoid(roundA,"neutral",1)
local botA=makeHumanoid(roundA,"bot",1)
local itemA=makeItem(roundA)
local route=node("BasePart","TacticalRoute_1")
attach(roundA,route)
local castle=node("Model","Castle_70")
attach(roundA,castle)
local egg=node("BasePart","FieldEgg_1")
attach(roundA,egg)
local boss=node("Model","NEUTRAL_BOSS_STONE_GIANT")
attach(roundA,boss)
soldierA.Health=28
soldierA.HealthChanged:Fire(28)
soldierA.Health=0
soldierA.Died:Fire()
botA.Health=22
botA.HealthChanged:Fire(22)
botA.Died:Fire()
itemA.CanQuery=false
itemA:GetPropertyChangedSignal("CanQuery"):Fire()
local row=scanMode("TEAM")
verify(row.observedEvents.neutralDamageEvents==1,"real neutral HP event")
verify(row.observedEvents.neutralDeaths==1,"real neutral Died signal")
verify(row.observedEvents.botDamageEvents==1,"real bot HP event")
verify(row.observedEvents.botDeaths==1,"real bot Died signal")
verify(row.observedEvents.itemConsumeTransitions==1,"real ITEM consumed transition")
verify(row.counts.routes==1,"physical route counted")
verify(row.counts.castles==1,"physical castle model counted")
verify(row.counts.availableFieldEggs==1,"physical field egg counted")
verify(row.counts.stoneGiantModels==1,"existing original boss counted")
verify(row.counts.neutralModels==1,"physical neutral instance counted")
verify(scanPlayers().neutralKOCreditsUnscoped==14,"unscoped player attribute is honest")

local brA=makeArena("BATTLE_ROYALE")
local brSoldier=makeHumanoid(brA,"neutral",3)
brSoldier.HealthChanged:Fire(29)
verify(scanMode("BATTLE_ROYALE").observedEvents.neutralDamageEvents==1,"BR event independent")
verify(scanMode("TEAM").observedEvents.neutralDamageEvents==1,"TEAM unaffected by BR")

detach(previewRoot,roundA)
row=scanMode("TEAM")
verify(row.state=="NOT_STARTED","completed arena not live")
verify(row.observedEvents.neutralDeaths==0,"ended TEAM event counters hidden")
soldierA.HealthChanged:Fire(0)
soldierA.Died:Fire()
itemA:GetPropertyChangedSignal("CanQuery"):Fire()

local roundB=makeArena("TEAM")
row=scanMode("TEAM")
verify(row.roundSequence==2,"TEAM second round identity")
verify(row.observedEvents.neutralDeaths==0,"TEAM replay initial deaths zero")
verify(row.observedEvents.itemConsumeTransitions==0,"TEAM replay initial item zero")
verify(row.observedEvents.neutralDamageEvents==0,"TEAM replay initial hits zero")
local soldierB=makeHumanoid(roundB,"neutral",2)
soldierB.HealthChanged:Fire(18)
soldierB.Died:Fire()
itemA.CanQuery=true
itemA:GetPropertyChangedSignal("CanQuery"):Fire()
itemA.CanQuery=false
itemA:GetPropertyChangedSignal("CanQuery"):Fire()
row=scanMode("TEAM")
verify(row.observedEvents.neutralDamageEvents==1,"TEAM only new round neutral hit")
verify(row.observedEvents.neutralDeaths==1,"TEAM only new round death")
verify(row.observedEvents.itemConsumeTransitions==0,"stale item callback ignored")
verify(scanMode("BATTLE_ROYALE").roundSequence==1,"independent BR round identity")
snapshot()
verify(lastEncodedData.modes.TEAM.roundSequence==2,"published round id from original snapshot")
verify(lastEncodedData.modes.BATTLE_ROYALE.observedEvents.neutralDamageEvents==1,"published independent BR")
verify(lastEncodedData.unverified.officialRCIntegration=="NOT_CLAIMED","no false RC success")
verify(lastEncodedData.decision=="OBSERVATION_ONLY_PRODUCT_NO_GO","no fake product pass")
print("GQ_OBSERVER_NATIVE_SOURCE_EXECUTION_PASS "..tostring(checks).."/"..tostring(checks))
"""

def build(out):
    source=SOURCE.read_text(encoding="utf-8")
    if source.count(ANCHOR)!=1:
        raise ValueError("Source drift: initial snapshot/background task boundary not unique")
    if "neutralKOCreditsUnscoped" not in source:
        raise ValueError("Source drift: lifetime KO must not be mislabeled as round KO")
    # Original source untouched apart from inserting native fixtures after startup.
    data=source.replace(ANCHOR, "snapshot()\n"+TESTS+"\ntask.spawn(function()",1)
    out.write_text(PRELUDE+"\n"+data+"\n",encoding="utf-8")
    print("Prepared actual observer source native Luau VM regression:",out)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    build(parser.parse_args().out)
