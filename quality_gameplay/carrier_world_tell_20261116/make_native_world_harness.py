#!/usr/bin/env python3
"""Execute the EXACT authored CarrierWorldTell & Policy Luau in a mocked native VM.

This exercises the actual world-indicator module, not only a hand-written
policy mirror. It cannot prove Roblox Studio rendering or Android performance.
"""
import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent

PRELUDE = r'''
-- Minimal fake Roblox host. This suite runs with the real Luau native CLI.
local __players = {}
local __instances = {}
local __threads = {}
local __spawned = 0

local Players = {}
function Players:GetPlayerByUserId(id)
 return __players[id]
end
game = {}
function game:GetService(name)
 assert(name == "Players", "unexpected Roblox service "..tostring(name))
 return Players
end
script = {Parent={}}
function script.Parent:WaitForChild(name)
 assert(name == "EGGRUMBLE_CarrierTellPolicy")
 return name
end
require = function(_)
 return NativePolicy
end

Instance = {}
function Instance.new(kind)
 assert(kind == "BillboardGui" or kind == "TextLabel", "unapproved instance "..tostring(kind))
 local item={__class=kind, destroyed=false}
 function item:Destroy()
  self.destroyed=true
  self.Parent=nil
 end
 table.insert(__instances,item)
 return item
end
UDim2 = {}
function UDim2.fromOffset(x,y) return {x=x,y=y} end
function UDim2.fromScale(x,y) return {sx=x,sy=y} end
Vector3 = {}
function Vector3.new(x,y,z) return {x=x,y=y,z=z} end
Color3 = {}
function Color3.fromRGB(r,g,b) return {r=r,g=g,b=b} end
Enum = {Font={GothamBold="GothamBold"}}
task = {}
function task.spawn(f)
 __spawned+=1
 table.insert(__threads,coroutine.create(f))
end
function task.wait(seconds)
 assert(seconds>=0.25 and seconds<=0.5,"unbounded or per-frame tick")
 return coroutine.yield()
end

local function step()
 local running=__threads
 __threads={}
 for _,thread in ipairs(running) do
  if coroutine.status(thread)~="dead" then
   local ok,err=coroutine.resume(thread)
   assert(ok,"actual world module VM error: "..tostring(err))
   if coroutine.status(thread)~="dead" then
    table.insert(__threads,thread)
   end
  end
 end
end
local function makeAvatar(name)
 local root={Name="HumanoidRootPart",avatarName=name}
 function root:IsA(kind) return kind=="BasePart" end
 local hum={Health=100}
 local char={Name=name}
 function char:IsA(kind) return kind=="Model" end
 function char:FindFirstChild(key)
  if key=="HumanoidRootPart" then return root end
  return nil
 end
 function char:FindFirstChildOfClass(key)
  if key=="Humanoid" then return hum end
  return nil
 end
 return char,root,hum
end
local function liveOn(root)
 local count=0
 local gui
 for _,item in ipairs(__instances) do
  if item.__class=="BillboardGui" and item.Parent==root and not item.destroyed then
   count+=1
   gui=item
  end
 end
 return count,gui
end
local function countLiveAll()
 local count=0
 for _,item in ipairs(__instances) do
  if item.__class=="BillboardGui" and item.Parent~=nil and not item.destroyed then count+=1 end
 end
 return count
end
local checks=0
local function eq(name,value,expected)
 checks+=1
 assert(value==expected,name.." expected="..tostring(expected).." got="..tostring(value))
end
'''

CASES = r'''
local human,hr,hh=makeAvatar("human100")
local bot,br,bh=makeAvatar("AI_1")
__players[100]={Character=human}
local a={
 mode="TEAM", world={Parent={}},
 roster={{id="100",isAI=false},{id="AI_1",isAI=true}},
 botActors={AI_1=bot},
 rules={phase="ACTIVE",winner=nil,castles={
  ["100"]={alive=true,heldEggs=0,team="RED"},
  ["AI_1"]={alive=true,heldEggs=0,team="BLUE"},
 }},
}
eq("must start active",NativeTell.start(a),true)
eq("do not double start",NativeTell.start(a),false)
step()
eq("no marker for empty human",liveOn(hr),0)
eq("no marker for empty bot",liveOn(br),0)
a.rules.castles["100"].heldEggs=2
a.rules.castles["AI_1"].heldEggs=1
step()
local nc,hgui=liveOn(hr)
eq("real human marker",nc,1)
eq("actual real count",hgui and hgui.Adornee,hr)
eq("actual server egg text",hgui and hgui.__class,"BillboardGui")
eq("limited distance",hgui and hgui.MaxDistance,70)
eq("not always-on-top over wall",hgui and hgui.AlwaysOnTop,false)
eq("one marker on bot",liveOn(br),1)
eq("two markers total",countLiveAll(),2)

a.rules.castles["100"].heldEggs=3
step()
local n,updated=liveOn(hr)
eq("same gui on count change",updated,hgui)
eq("one marker on update",n,1)
eq("egg count still authoritative",a.rules.castles["100"].heldEggs,3)
a.rules.castles["100"].heldEggs=0
step()
eq("drop cleans human marker",liveOn(hr),0)
eq("drop destroys old marker",hgui.destroyed,true)
eq("bot unaffected by human egg drop",liveOn(br),1)

-- Player avatar death and replacement use the same original session.
a.rules.castles["100"].heldEggs=1
step()
eq("reappears after collecting",liveOn(hr),1)
hh.Health=0
step()
eq("human death removes marker",liveOn(hr),0)
local human2,hr2,hh2=makeAvatar("respawn100")
__players[100].Character=human2
step()
eq("new avatar has a marker",liveOn(hr2),1)
eq("old avatar marker remains absent",liveOn(hr),0)

-- The existing original bot system may replace an AI model after a death.
local oldBotGui=select(2,liveOn(br))
local bot2,br2,bh2=makeAvatar("AI_1_reborn")
a.botActors["AI_1"]=bot2
step()
eq("old AI marker removed after bot model replacement",liveOn(br),0)
eq("new AI model marker created",liveOn(br2),1)
eq("old AI marker destroyed",oldBotGui.destroyed,true)

-- Former human becomes server AI controlled after disconnect.
__players[100]=nil
local takeover,tkr,tkh=makeAvatar("takeover100")
a.botActors["100"]=takeover
step()
eq("old human avatar marker cleared on takeover",liveOn(hr2),0)
eq("takeover AI marker retained for real castle",liveOn(tkr),1)
eq("original human ownership remains",a.rules.castles["100"].heldEggs,1)

-- Independent BR arena runs concurrently; teardown must not remove another mode.
local solo,sr,sh=makeAvatar("human201")
__players[201]={Character=solo}
local b={
 mode="BATTLE_ROYALE",world={Parent={}},
 roster={{id="201",isAI=false}},
 botActors={},
 rules={phase="ACTIVE",winner=nil,castles={["201"]={alive=true,heldEggs=2,team=nil}}},
}
eq("second real mode starts",NativeTell.start(b),true)
step()
eq("new BR world marker",liveOn(sr),1)
eq("TEAM takeover retained during BR",liveOn(tkr),1)
eq("two modes isolated (3 total carriers)",countLiveAll(),3)
a.rules.phase="FINISHED"
a.rules.winner="BLUE"
step()
eq("TEAM human-takeover cleaned on finish",liveOn(tkr),0)
eq("TEAM bot cleaned on finish",liveOn(br2),0)
eq("BR still running after TEAM finish",liveOn(sr),1)
eq("TEAM loop released",a._carrierWorldTellStarted,nil)

-- A destroyed castle stops its marker inside the still-active BR match.
b.rules.castles["201"].alive=false
step()
eq("fallen castle marker removed",liveOn(sr),0)
b.rules.castles["201"].alive=true
step()
eq("marker restored to living player",liveOn(sr),1)
-- Removing the arena while still active must clean surviving avatar labels.
b.world.Parent=nil
step()
eq("arena destruction cleans all world labels",countLiveAll(),0)
eq("BR loop released",b._carrierWorldTellStarted,nil)
eq("exactly two spawned loops",__spawned,2)
eq("no pending coroutines",#__threads,0)

-- Stale match start protection and no sign of client-owned egg values.
a.rules.phase="FINISHED"
eq("cannot start finished match",NativeTell.start(a),false)
local inactive={world={Parent={}},roster={},rules={phase="LOBBY",winner=nil,castles={}}}
eq("cannot start from lobby",NativeTell.start(inactive),false)
local ended={world={Parent={}},roster={},rules={phase="ACTIVE",winner="BLUE",castles={}}}
eq("cannot start after winner",NativeTell.start(ended),false)
print("NATIVE_CARRIER_WORLD_ACTUAL_MODULE_PASS checks="..tostring(checks))
'''

def write_harness(out: Path) -> None:
    policy=(HERE/"EGGRUMBLE_CarrierTellPolicy.luau").read_text(encoding="utf-8")
    source=(HERE/"EGGRUMBLE_CarrierWorldTell.luau").read_text(encoding="utf-8")
    assert policy.count("\nreturn Policy\n")==1
    assert source.count("\nreturn Tell\n")==1
    native_policy=policy.replace("\nreturn Policy\n","\nlocal NativePolicy=Policy\n",1)
    native_tell=source.replace("\nreturn Tell\n","\nlocal NativeTell=Tell\n",1)
    out.write_text(native_policy+"\n"+PRELUDE+"\n"+native_tell+"\n"+CASES,encoding="utf-8")

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    opts=p.parse_args()
    write_harness(opts.out)
