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
local __warnings = {}
warn = function(message)
 table.insert(__warnings, tostring(message))
end

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
function Vector3.new(x,y,z) return {x=x,y=y,z=z,X=x,Y=y,Z=z} end
local function makeWorld(mode)
 local x=if mode=="TEAM" then -620 else 620
 local world={Parent={}}
 local field={
  Position=Vector3.new(x,0,465),
  Size=Vector3.new(890,2,1050),
  Parent=world,
 }
 function field:IsA(kind) return kind=="BasePart" end
 function world:FindFirstChild(name)
  if name=="TacticalBattlefield" then return field end
  return nil
 end
 return world
end
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
 local root={Name="HumanoidRootPart",avatarName=name,Position=Vector3.new(-620,5,465)}
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
 mode="TEAM", world=makeWorld("TEAM"),
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
eq("human label near head",hgui and hgui.StudsOffsetWorldSpace.y,4)
eq("not always-on-top over wall",hgui and hgui.AlwaysOnTop,false)
eq("one marker on bot",liveOn(br),1)
eq("AI carrier label avoids original BotObjective board",select(2,liveOn(br)).StudsOffsetWorldSpace.y,10.2)
eq("two markers total",countLiveAll(),2)

-- The original match may outlive a client cosmetic cleanup / character visual
-- replacement. Losing a single billboard must not hide held eggs indefinitely.
hgui:Destroy()
step()
eq("externally deleted human marker recreated",liveOn(hr),1)
local _,newGui=liveOn(hr)
eq("recreated GUI identity differs",newGui~=hgui,true)
eq("recreated GUI still server count 2",a.rules.castles["100"].heldEggs,2)
eq("no duplicate marker after repair",countLiveAll(),2)
hgui=newGui

-- Bad UI parent/Adornee must not create a wallhack or a leaked third marker.
local foreign={Name="WrongDisplayParent"}
hgui.Parent=foreign
step()
eq("externally reparented marker repaired",liveOn(hr),1)
eq("externally moved GUI explicitly destroyed",hgui.destroyed,true)
eq("reparent repair leaves two live world markers",countLiveAll(),2)
hgui=select(2,liveOn(hr))
hgui.Adornee=br
step()
eq("wrong Adornee repaired",liveOn(hr),1)
eq("wrong Adornee GUI destroyed",hgui.destroyed,true)
hgui=select(2,liveOn(hr))
local countLabel=nil
for _,item in ipairs(__instances) do
 if item.__class=="TextLabel" and item.Parent==hgui then countLabel=item end
end
eq("current marker owns count TextLabel",countLabel~=nil,true)
countLabel.Parent=nil
step()
eq("lost TextLabel repaired",liveOn(hr),1)
eq("damaged parent marker destroyed",hgui.destroyed,true)
hgui=select(2,liveOn(hr))
eq("all UI repairs leave one human and one AI badge",countLiveAll(),2)

-- Server-side visual drift while the actual egg count stays at 2: repair
-- render visibility/geometry and the authoritative caption without creating
-- another BillboardGui, sending Remotes, or modifying egg ownership.
local markerBeforeDrift=select(2,liveOn(hr))
local labelBeforeDrift=nil
for _,item in ipairs(__instances) do
 if item.__class=="TextLabel" and item.Parent==markerBeforeDrift then
  labelBeforeDrift=item
 end
end
eq("label exists for drift repair",labelBeforeDrift~=nil,true)
markerBeforeDrift.AlwaysOnTop=true
markerBeforeDrift.MaxDistance=9999
markerBeforeDrift.Enabled=false
labelBeforeDrift.Visible=false
labelBeforeDrift.Text="🥚×999"
step()
eq("server corrects invalid always-on-top marker",markerBeforeDrift.AlwaysOnTop,false)
eq("server corrects global-distance label",markerBeforeDrift.MaxDistance,70)
eq("server re-enables cosmetic GUI",markerBeforeDrift.Enabled,true)
eq("server re-enables cosmetic text",labelBeforeDrift.Visible,true)
eq("real server count restores caption",labelBeforeDrift.Text,"🥚×2")
eq("drift corrected without new GUI",select(2,liveOn(hr)),markerBeforeDrift)
eq("drift corrected without extra markers",countLiveAll(),2)
eq("drift corrected without new egg units",a.rules.castles["100"].heldEggs,2)
eq("second tick is idempotent",NativeTell.start(a),false)
step()
eq("steady visual correction still one human marker",liveOn(hr),1)
eq("steady visual correction still one bot marker",liveOn(br),1)

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

-- A human's Character persists while joining the other arena or returning
-- to lobby. The same prior TEAM match must not leak its old egg count onto it.
hr2.Position=Vector3.new(620,5,465)
step()
eq("TEAM marker hidden when avatar crosses to BR",liveOn(hr2),0)
hr2.Position=Vector3.new(0,5,0)
step()
eq("TEAM marker hidden when avatar is lobby",liveOn(hr2),0)
hr2.Position=Vector3.new(-620,5,465)
step()
eq("TEAM marker restored on original battlefield",liveOn(hr2),1)


-- The existing original bot system may replace an AI model after a death.
local oldBotGui=select(2,liveOn(br))
local bot2,br2,bh2=makeAvatar("AI_1_reborn")
a.botActors["AI_1"]=bot2
step()
eq("old AI marker removed after bot model replacement",liveOn(br),0)
eq("new AI model marker created",liveOn(br2),1)
eq("new AI board spacing preserved",select(2,liveOn(br2)).StudsOffsetWorldSpace.y,10.2)

br2.Position=Vector3.new(620,5,465)
step()
eq("AI TEAM marker excluded after leaving world bounds",liveOn(br2),0)
br2.Position=Vector3.new(-620,5,465)
step()
eq("AI TEAM marker restored inside real field",liveOn(br2),1)

eq("old AI marker destroyed",oldBotGui.destroyed,true)

-- Former human becomes server AI controlled after disconnect.
__players[100]=nil
local takeover,tkr,tkh=makeAvatar("takeover100")
a.botActors["100"]=takeover
step()
eq("old human avatar marker cleared on takeover",liveOn(hr2),0)
eq("takeover AI marker retained for real castle",liveOn(tkr),1)
eq("human-to-bot takeover uses AI spacing",select(2,liveOn(tkr)).StudsOffsetWorldSpace.y,10.2)
eq("original human ownership remains",a.rules.castles["100"].heldEggs,1)

-- Independent BR arena runs concurrently; teardown must not remove another mode.
local solo,sr,sh=makeAvatar("human201")
sr.Position=Vector3.new(620,5,465)
__players[201]={Character=solo}
local b={
 mode="BATTLE_ROYALE",world=makeWorld("BATTLE_ROYALE"),
 roster={{id="201",isAI=false}},
 botActors={},
 rules={phase="ACTIVE",winner=nil,castles={["201"]={alive=true,heldEggs=2,team=nil}}},
}
eq("second real mode starts",NativeTell.start(b),true)
step()
eq("new BR world marker",liveOn(sr),1)
eq("TEAM takeover retained during BR",liveOn(tkr),1)
eq("two modes isolated (3 total carriers)",countLiveAll(),3)

sr.Position=Vector3.new(-620,5,465)
step()
eq("BR marker excluded after avatar moves to TEAM field",liveOn(sr),0)
eq("TEAM unaffected by BR cross-over",liveOn(tkr),1)
sr.Position=Vector3.new(620,5,465)
step()
eq("BR marker restored in BR field",liveOn(sr),1)

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
-- The battlefield part is removed first while the enclosing arena and
-- original match remain live. The optional GUI must NOT outlive the floor.
b.world:FindFirstChild("TacticalBattlefield").Parent=nil
step()
eq("BR marker removed if only battlefield detached",liveOn(sr),0)
eq("BR cosmetic worker released on detached battlefield",b._carrierWorldTellStarted,nil)
eq("BR parent arena still alive after floor removal",b.world.Parent~=nil,true)
eq("BR real castle retains held eggs",b.rules.castles["201"].heldEggs,2)
eq("BR original match rules still ACTIVE",b.rules.phase,"ACTIVE")
eq("BR cannot restart using detached floor",NativeTell.start(b),false)
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

local noArena={world={Parent={},FindFirstChild=function() return nil end},
 roster={},rules={phase="ACTIVE",winner=nil,castles={}}}
eq("missing real battlefield fails closed",NativeTell.start(noArena),false)
eq("no marker loop spawned for malformed arena",#__threads,0)
local orphanWorld=makeWorld("TEAM")
orphanWorld:FindFirstChild("TacticalBattlefield").Parent=nil
local orphanStart={world=orphanWorld,roster={},rules={phase="ACTIVE",winner=nil,castles={}}}
eq("detached original floor fails closed before start",NativeTell.start(orphanStart),false)
eq("detached floor does not spawn worker",#__threads,0)
local reparentedWorld=makeWorld("BATTLE_ROYALE")
reparentedWorld:FindFirstChild("TacticalBattlefield").Parent={Name="OutsideArena"}
local reparented={world=reparentedWorld,roster={},rules={phase="ACTIVE",winner=nil,castles={}}}
eq("reparented floor fails closed before start",NativeTell.start(reparented),false)
eq("reparented floor does not spawn worker",#__threads,0)


-- Exact author MODE_SEATS=16. Exercise full roster load in both live arenas:
-- no fan-out above one billboard per actor; no event subscription or leak.
local function createFullMode(mode,humanId)
 local sess={
  mode=mode,world=makeWorld(mode),
  roster={},botActors={},
  rules={phase="ACTIVE",winner=nil,castles={}},
 }
 for i=1,16 do
  local id=if i==1 then tostring(humanId) else mode.."_BOT_"..tostring(i)
  local isAI=i~=1
  local model,rt,hum=makeAvatar("max_"..mode.."_"..id)
  if mode=="BATTLE_ROYALE" then rt.Position=Vector3.new(620,5,465) end
  table.insert(sess.roster,{id=id,isAI=isAI})
  sess.rules.castles[id]={alive=true,heldEggs=1,team=if mode=="TEAM" then "RED" else nil}
  if isAI then sess.botActors[id]=model
  else __players[humanId]={Character=model} end
 end
 return sess
end
local fullTeam=createFullMode("TEAM",901)
local fullBR=createFullMode("BATTLE_ROYALE",902)
eq("16-seat TEAM starts",NativeTell.start(fullTeam),true)
eq("16-seat BR starts",NativeTell.start(fullBR),true)
step()
eq("no GUI leak at full two arenas (32 max)",countLiveAll(),32)
eq("one task per arena not per player",__spawned,4)
local aId="TEAM_BOT_7"
fullTeam.rules.castles[aId].heldEggs=0
step()
eq("individual egg drop removes exactly one GUI",countLiveAll(),31)
fullTeam.rules.castles[aId].heldEggs=2
step()
eq("egg replacement restores exactly one GUI",countLiveAll(),32)
-- TEAM floor disappears earlier than the TEAM world: the BR arena must still
-- render 16 correct carriers, no stale TEAM badge, no game-loop shutdown.
fullTeam.world:FindFirstChild("TacticalBattlefield").Parent=nil
step()
eq("TEAM floor-only removal clears its 16 UI",countLiveAll(),16)
eq("TEAM floor-only removal releases worker",fullTeam._carrierWorldTellStarted,nil)
eq("TEAM arena remains parented",fullTeam.world.Parent~=nil,true)
eq("TEAM real match rules remain active",fullTeam.rules.phase,"ACTIVE")
eq("BR 16 carriers continue after TEAM floor removed",fullBR._carrierWorldTellStarted,true)
eq("TEAM floor-only removal prohibits restarting UI",NativeTell.start(fullTeam),false)
fullTeam.rules.phase="FINISHED"
step()
eq("TEAM shutdown preserves 16 BR carriers",countLiveAll(),16)
fullBR.world.Parent=nil
step()
eq("full BR arena destroy removes all labels",countLiveAll(),0)
eq("no tasks left in full roster scenario",#__threads,0)


-- Independent server-only optional safety switch. Use the original V3 16-seat
-- arenas, not a client Remote, and never modify heldEggs or role/damage state.
local killTeam=createFullMode("TEAM",903)
local killBR=createFullMode("BATTLE_ROYALE",904)
killTeam.carrierWorldTellEnabled=false
eq("flag off before start prevents TEAM module",NativeTell.start(killTeam),false)
eq("no team spawned marker job while disabled",killTeam._carrierWorldTellStarted,nil)
eq("BR unaffected by TEAM disabled state",NativeTell.start(killBR),true)
step()
eq("BR all 16 badges while TEAM off",countLiveAll(),16)
killTeam.carrierWorldTellEnabled=true
eq("explicit team re-enable starts one isolated loop",NativeTell.start(killTeam),true)
step()
eq("BR+TEAM full 32 badges restored",countLiveAll(),32)
killTeam.carrierWorldTellEnabled=false
step()
eq("TEAM flag off cleans its own 16 badges",countLiveAll(),16)
eq("TEAM flag off frees loop",killTeam._carrierWorldTellStarted,nil)
eq("TEAM flag off does not modify real held eggs",killTeam.rules.castles["903"].heldEggs,1)
eq("BR still fully active after TEAM kill",killBR._carrierWorldTellStarted,true)
eq("false flag rejects restart",NativeTell.start(killTeam),false)
killTeam.carrierWorldTellEnabled=true
eq("true flag permits explicit new start",NativeTell.start(killTeam),true)
step()
eq("re-enabled TEAM returns to 32 visible carriers",countLiveAll(),32)
killBR.carrierWorldTellEnabled=false
step()
eq("BR flag off leaves TEAM 16 only",countLiveAll(),16)
eq("BR stopped frees only BR task",killBR._carrierWorldTellStarted,nil)
eq("BR flag off did not drain carried egg",killBR.rules.castles["904"].heldEggs,1)
killTeam.world.Parent=nil
step()
eq("TEAM world destroyed cleans final 16",countLiveAll(),0)
eq("all optional worker loops stopped",#__threads,0)


-- Fault containment: if another visual/plugin subsystem replaces a bot's
-- FindFirstChild with a throwing implementation DURING a live match, our
-- optional loop must clean up all TEAM badges and release its start lock.
-- No game Rules, HP, AI, neutral or item logic is owned by this observer.
local faultTeam=createFullMode("TEAM",905)
local faultBR=createFullMode("BATTLE_ROYALE",906)
eq("fault test TEAM starts",NativeTell.start(faultTeam),true)
eq("fault test BR starts",NativeTell.start(faultBR),true)
step()
eq("fault test two full modes live first",countLiveAll(),32)
local faultBot=faultTeam.botActors["TEAM_BOT_5"]
local oldFindChild=faultBot.FindFirstChild
local warningsBefore=#__warnings
function faultBot:FindFirstChild(name)
 error("SIMULATED_STALE_BOT_VISUAL_API")
end
step()
eq("simulated per-avatar throw stops TEAM badge loop",faultTeam._carrierWorldTellStarted,nil)
eq("all 16 TEAM badges removed by finally cleanup",countLiveAll(),16)
eq("BR remains live after separate TEAM observer exception",faultBR._carrierWorldTellStarted,true)
eq("TEAM server held eggs unaffected by visual exception",faultTeam.rules.castles["905"].heldEggs,1)
eq("BR server held eggs unaffected by visual exception",faultBR.rules.castles["906"].heldEggs,1)
eq("only one explicitly bounded optional observer warning emitted",#__warnings,warningsBefore+1)
eq("warning identifies our optional GQ lane",
 string.find(__warnings[#__warnings],"[GQ511]",1,true)~=nil,true)
eq("warning retains original error text",
 string.find(__warnings[#__warnings],"SIMULATED_STALE_BOT_VISUAL_API",1,true)~=nil,true)
faultBot.FindFirstChild=oldFindChild
eq("explicit restart after dependency recovery allowed",NativeTell.start(faultTeam),true)
step()
eq("recovered team returns its 16 badges once",countLiveAll(),32)
faultTeam.world.Parent=nil
step()
eq("TEAM fault recovery teardown preserves healthy BR",countLiveAll(),16)
faultBR.world.Parent=nil
step()
eq("fault simulation leaves no stale labels",countLiveAll(),0)
eq("fault simulation leaves no runaway coroutines",#__threads,0)

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
