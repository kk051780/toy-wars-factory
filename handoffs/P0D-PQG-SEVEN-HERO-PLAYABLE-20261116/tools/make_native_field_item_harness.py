#!/usr/bin/env python3
"""Run ORIGINAL ITEM + ORIGINAL InteractionGuard in headless native Luau VM.

No substitute gameplay implementation; deterministic Roblox service stubs only.
This is NOT Roblox Studio, Android or actual physics engine evidence.
"""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "EGGRUMBLE_InteractionGuard.luau"
ITEM = ROOT / "EGGRUMBLE_FieldItemPickups.luau"
PRELUDE = r'''
local now=100
local scheduled={}
local function schedule(time,fn,co)
 table.insert(scheduled,{at=time,fn=fn,co=co})
end
local task={}
function task.delay(seconds,fn) schedule(now+seconds,fn,nil) end
function task.spawn(fn)
 local co=coroutine.create(fn)
 schedule(now,nil,co)
end
function task.wait(seconds) return coroutine.yield(seconds) end
local function runTo(target)
 while true do
  local nextIndex=nil
  for i,event in ipairs(scheduled) do
   if event.at<=target and (not nextIndex or event.at<scheduled[nextIndex].at) then
    nextIndex=i
   end
  end
  if not nextIndex then break end
  local e=table.remove(scheduled,nextIndex)
  now=e.at
  if e.co then
   local ok,delay=coroutine.resume(e.co)
   assert(ok,"native scheduled coroutine failure: "..tostring(delay))
   if coroutine.status(e.co)~="dead" then schedule(now+(delay or 0),nil,e.co) end
  else
   e.fn()
  end
 end
 now=target
end
local os={clock=function() return now end}
local vec={}
function vec.new(x,y,z) return setmetatable({X=x,Y=y,Z=z},vec) end
vec.__add=function(a,b) return vec.new(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end
vec.__sub=function(a,b) return vec.new(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end
-- Lua vector magnitude is accessed as a property.
vec.__index=function(v,key)
 if key=="Magnitude" then return math.sqrt(v.X*v.X+v.Y*v.Y+v.Z*v.Z) end
 return vec[key]
end
local Vector3=vec
local Enum={PartType={Ball="Ball"},Material={Neon="Neon"},
 RaycastFilterType={Exclude="Exclude"}}
local Color3={fromRGB=function() return {} end}
local RaycastParams={new=function() return {} end}
local studio=true
local mockPlayers={}
local runService={IsStudio=function() return studio end}
local game={}
function game:GetService(name)
 if name=="Players" then return mockPlayers end
 if name=="RunService" then return runService end
 error("unexpected game:GetService("..name..")")
end
local wall=false
local wallObject={}
local workspace={}
function workspace:Raycast(_origin,_cast,_params)
 if wall then return {Instance=wallObject} end
 return nil
end
local created={}
local forces={}
local Instance={}
function Instance.new(className)
 local obj={ClassName=className,CanQuery=true,Parent=nil}
 function obj:Destroy() self.Parent=nil;self.destroyed=true end
 function obj:IsA(class) return self.ClassName==class end
 function obj:GetClosestPointOnSurface(_position) return self.Position end
 function obj:FindFirstChild(_name) return nil end
 if className=="ProximityPrompt" then
  obj.Triggered={Connect=function(_,callback) obj.trigger=callback;return {} end}
 end
 if className=="ForceField" then table.insert(forces,obj) end
 if className=="Part" then table.insert(created,obj) end
 return obj
end
local SharedGuard=nil
local script={Parent={hasGuard=true}}
function script.Parent:FindFirstChild(name)
 if self.hasGuard and name=="EGGRUMBLE_InteractionGuard" then
  return {tag="ORIGINAL_GUARD"}
 end
 return nil
end
local require=function(mod)
 assert(mod and mod.tag=="ORIGINAL_GUARD","a second Guard cannot be substituted")
 assert(SharedGuard,"original Guard has not been loaded")
 return SharedGuard
end
'''
SUITE = r'''
local assertions=0
local function check(ok,reason)
 assertions+=1
 assert(ok,reason)
end
local human={UserId=101,Parent=mockPlayers}
local humanoid={Health=40,MaxHealth=100,WalkSpeed=16}
local avatar={}
local root={Position=Vector3.new(4,0,0),ClassName="BasePart"}
function root:IsA(class) return class=="BasePart" end
function avatar:FindFirstChildOfClass(class)
 if class=="Humanoid" then return humanoid end
end
function avatar:FindFirstChild(name)
 if name=="HumanoidRootPart" then return root end
end
humanoid.Parent=avatar
human.Character=avatar
local function makeSession(mode)
 return {world={Parent=true},mode=mode,
  rules={phase="ACTIVE",castles={["101"]={alive=true,heldEggs=0}}}}
end
local session=makeSession("TEAM")
FieldItems.start(session,{
 Vector3.new(0,0,0),Vector3.new(4,0,0),Vector3.new(8,0,0)})
local heal,dash,shield=created[1],created[2],created[3]
check(heal and dash and shield,"three original ITEM parts")
check(heal.Name=="ITEM_1_HEAL" and dash.Name=="ITEM_2_DASH"
 and shield.Name=="ITEM_3_SHIELD","source's REAL HEAL/DASH/SHIELD mapping")
-- Server-owned cargo rejects both movement and invulnerability, but HEAL remains.
session.rules.castles["101"].heldEggs=1
-- Every original pickup gets exactly one server-owned ProximityPrompt.
check(#createdPrompts==3,"each original item spawns one real prompt")
local function getPrompt(part)
 for _,item in ipairs(createdPrompts) do
  if item.Parent==part then return item end
 end
 error("missing original item prompt")
end
local healPrompt=getPrompt(heal)
local dashPrompt=getPrompt(dash)
local shieldPrompt=getPrompt(shield)
dashPrompt.trigger(human)
shieldPrompt.trigger(human)
check(dash.CanQuery and shield.CanQuery and humanoid.WalkSpeed==16,
 "carrying eggs must not consume DASH or SHIELD")
check(#forces==0,"carrying egg cannot obtain a ForceField")
healPrompt.trigger(human)
check(humanoid.Health==75 and not heal.CanQuery,"carrying eggs may HEAL")
-- Client prompt proximity alone is not authorization: real shared raycast blocks.
session.rules.castles["101"].heldEggs=0
wall=true
dashPrompt.trigger(human)
check(dash.CanQuery and humanoid.WalkSpeed==16,"solid wall blocks pickup")
wall=false
dashPrompt.trigger(human)
check(not dash.CanQuery and humanoid.WalkSpeed==27,"DASH physically consumed")
session.rules.castles["101"].heldEggs=1
runTo(now+0.25)
check(humanoid.WalkSpeed==16,"egg acquired AFTER DASH cancels speed in 250ms")
-- Original 35 sec item respawn; all effects and cooldown end within interval.
runTo(now+35)
check(dash.CanQuery and dashPrompt.Enabled,"original 35-second respawn retained")
-- BR mode has its own roster and also uses the original shared guard.
session.itemStop()
local battle=makeSession("BATTLE_ROYALE")
FieldItems.start(battle,{
 Vector3.new(0,0,0),Vector3.new(4,0,0),Vector3.new(8,0,0)})
local nextShield=created[#created]
local nextPrompt=getPrompt(nextShield)
nextPrompt.trigger(human)
check(#forces==1 and forces[1].Parent==avatar,"BR acquires real original SHIELD")
battle.rules.castles["101"].heldEggs=1
runTo(now+0.25)
check(forces[1].Parent==nil and forces[1].destroyed==true,
 "egg acquired AFTER SHIELD destroys original ForceField")
-- Terminating the match must not re-enable a consumed pickup via a timer.
battle.itemStop()
runTo(now+40)
check(nextShield.CanQuery==false and nextPrompt.Enabled==false,
 "old mode must not respawn an item after termination")
-- V3 MUST fail closed if original guard absent. Independent item-only mode remains.
script.Parent.hasGuard=false
local missing=makeSession("TEAM")
check(not pcall(function() FieldItems.start(missing,{Vector3.new(0,0,0)}) end),
 "integrated TEAM requires original server guard")
local isolated=makeSession(nil)
FieldItems.start(isolated,{Vector3.new(0,0,0)})
check(created[#created].Name=="ITEM_1_HEAL",
 "original independent item-only preview still runs without shared guard")
isolated.itemStop()
-- Regression: a DASH callback scheduled in a retired arena must NOT undo
-- another round's equally fast DASH, even if humanoid/avatar are reused.
script.Parent.hasGuard=true
local retired=makeSession("TEAM")
FieldItems.start(retired,{
 Vector3.new(0,0,0),Vector3.new(4,0,0),Vector3.new(8,0,0)})
local retiredDash=created[#created-1]
getPrompt(retiredDash).trigger(human)
check(humanoid.WalkSpeed==27,"old round DASH activated")
runTo(now+2)
retired.itemStop()
-- This assignment represents ORIGINAL RoundReplay.resetHuman's speed baseline.
humanoid.WalkSpeed=16
local fresh=makeSession("TEAM")
FieldItems.start(fresh,{
 Vector3.new(0,0,0),Vector3.new(4,0,0),Vector3.new(8,0,0)})
local freshDash=created[#created-1]
getPrompt(freshDash).trigger(human)
check(humanoid.WalkSpeed==27,"new round DASH activated")
runTo(now+3.25)
check(humanoid.WalkSpeed==27,
 "retired round timer must not overwrite new round active DASH")
fresh.itemStop()
print("[EGGRUMBLE ORIGINAL ITEM + ORIGINAL GUARD VM] PASS",assertions,
 "server-authoritative cargo, wall LOS, HEAL/DASH/SHIELD, respawn, 2 modes, cleanup")
'''

def build(out: Path):
    guard = GUARD.read_text(encoding="utf-8").rstrip()
    item = ITEM.read_text(encoding="utf-8").rstrip()
    if not guard.endswith("\nreturn Guard") or not item.endswith("\nreturn Items"):
        raise RuntimeError("Original author module termination changed")
    for token in (
        'function Guard.allow(', 'workspace:Raycast(',
        'function Items.start(', 'carryingEnemyEggs(',
        'interactionGuard.allow(player,part,"拾う",part.Name)',
        'task.delay(RESPAWN_SECONDS,function()',
    ):
        if token not in (guard + item):
            raise RuntimeError("Original item/guard functional contract drift: " + token)
    # Expose original prompt objects created by the source without replacing the source:
    # the stub Instance.new sees them; no monkey-patches to game rules.
    prelude = PRELUDE.replace('local forces={}', 'local forces={}\nlocal createdPrompts={}')
    prelude = prelude.replace(
        'if className=="ProximityPrompt" then',
        'if className=="ProximityPrompt" then table.insert(createdPrompts,obj)'
    )
    guard = guard[:-len("\nreturn Guard")] + "\nSharedGuard=Guard"
    item = item[:-len("\nreturn Items")] + "\nlocal FieldItems=Items"
    out.write_text(prelude + "\n" + guard + "\n" + item + "\n" + SUITE, encoding="utf-8")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    build(args.out)
    print("Generated original ITEM + original InteractionGuard Luau VM harness", args.out)
