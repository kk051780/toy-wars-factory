#!/usr/bin/env python3
"""Run immutable #500 pure policy tests + a small executable real Live module
server simulation. This is Native Luau VM evidence, NOT Roblox Studio/Android.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from select_defense import blob,POLICY_BLOB,LIVE_BLOB

SIMULATOR=r'''
-- Native fake-service harness, created ONLY around exact original author source.
local __threads={}
local __players={}
local __blocked=false
local __v={}
__v.__index=function(self,key)
 if key=="Magnitude" then return math.sqrt(self.X*self.X+self.Y*self.Y+self.Z*self.Z) end
 return __v[key]
end
__v.__add=function(a,b)return setmetatable({X=a.X+b.X,Y=a.Y+b.Y,Z=a.Z+b.Z},__v)end
__v.__sub=function(a,b)return setmetatable({X=a.X-b.X,Y=a.Y-b.Y,Z=a.Z-b.Z},__v)end
Vector3={new=function(x,y,z)return setmetatable({X=x,Y=y,Z=z},__v)end}
Color3={fromRGB=function(r,g,b)return {r,g,b}end}
Enum={PartType={Ball="Ball",Block="Block"},Material={Neon="Neon"},
 RaycastFilterType={Exclude="Exclude"}}
RaycastParams={new=function()return {}end}
workspace={Raycast=function(_,from,direction,params)
 if __blocked then return {} end
 return nil
end}
Instance={new=function(kind)
 local x={ClassName=kind}
 function x:Destroy()self.Parent=nil;self.Destroyed=true end
 return x
end}
local Services={}
Services.Players={GetPlayerByUserId=function(_,id)return __players[id]end}
Services.RunService={IsStudio=function()return true end}
Services.Debris={AddItem=function()end}
game={GetService=function(_,service)
 assert(Services[service],"RED_UNEXPECTED_SERVICE_"..tostring(service))
 return Services[service]
end}
task={}
function task.spawn(f)table.insert(__threads,coroutine.create(f))end
function task.wait(seconds) assert(seconds>=.3 and seconds<=.5,"RED_UNBOUNDED_TICK");return coroutine.yield()end
function task.delay(_,f)end
local function step()
 local running=__threads
 __threads={}
 for _,co in ipairs(running)do
  if coroutine.status(co)~="dead" then
   local ok,err=coroutine.resume(co)
   assert(ok,"RED_LIVE_NATIVE_ERROR_"..tostring(err))
   if coroutine.status(co)~="dead" then table.insert(__threads,co) end
  end
 end
end
local n=0
local function eq(v,w,label)
 n+=1
 assert(v==w,label.." expected="..tostring(w).." got="..tostring(v))
end
local function makeHuman(id,pos)
 local h={Health=100,WalkSpeed=16,attrs={}}
 function h:TakeDamage(damage)self.Health-=damage end
 function h:GetAttribute(k)return self.attrs[k]end
 function h:SetAttribute(k,v)self.attrs[k]=v end
 local root={Position=pos,Parent={}}
 function root:IsA(kind)return kind=="BasePart"end
 local char={Parent={}}
 function char:FindFirstChildOfClass(kind)
  if kind=="Humanoid" then return h end
 end
 function char:FindFirstChild(kind)
  if kind=="HumanoidRootPart" then return root end
 end
 local p={UserId=tonumber(id),Character=char,attrs={}}
 function p:GetAttribute(k)return self.attrs[k]end
 function p:SetAttribute(k,v)self.attrs[k]=v end
 __players[tonumber(id)]=p
 return h,p
end
local function scenario(modules,enemyPosition,friendPosition,stealth)
 local world={Parent={}}
 local owner={id="1",team="RED",isAI=false,alive=true,modules=modules}
 local enemy={id="2",team="BLUE",isAI=false,alive=true,modules={}}
 local friend={id="3",team="RED",isAI=false,alive=true,modules={}}
 local castleModels={["1"]={model={Parent={}}},["2"]={model={Parent={}}},["3"]={model={Parent={}}}}
 local session={world=world,roster={{id="1"},{id="2"},{id="3"}},mode="TEAM",
  rules={phase="ACTIVE",castles={["1"]=owner,["2"]=enemy,["3"]=friend}},
  castleModels=castleModels,
  castleLocations={["1"]=Vector3.new(0,0,0),["2"]=Vector3.new(300,0,0),["3"]=Vector3.new(180,0,0)}}
 makeHuman("1",Vector3.new(-100,0,0))
 local enemyHum,enemyPlayer=makeHuman("2",enemyPosition)
 local friendHum=makeHuman("3",friendPosition)
 enemyPlayer:SetAttribute("EGGRUMBLE_StealthUntil",stealth or 0)
 return session,enemyHum,friendHum,enemyPlayer
end

-- Original source #500 actual Defense.start, not a policy-only fantasy.
local a,e,f=scenario({"TURRET"},Vector3.new(25,6,-18),Vector3.new(25,6,-18),0)
local stop=Defense.start(a)
eq(type(stop),"function","REAL_STOP_HANDLE")
step()
eq(e.Health,88,"REAL_TURRET_12_DAMAGE")
eq(f.Health,100,"REAL_TEAM_ALLY_NOT_HIT")
step()
eq(e.Health,88,"REAL_COOLDOWN_NO_DOUBLE_DAMAGE")
stop()
eq(a.castleDefenseStop,stop,"REAL_MATCH_STOP_HOOK")
step()

__blocked=true
local b,eb=scenario({"TURRET"},Vector3.new(25,6,-18),Vector3.new(25,6,-18),0)
Defense.start(b);step()
eq(eb.Health,100,"REAL_SOLID_WALL_BLOCKS_TURRET")
b.castleDefenseStop()
__blocked=false

local c,ec,fc,pc=scenario({"SENSOR","TURRET"},Vector3.new(-10,4,-18),Vector3.new(-10,4,-18),os.clock()+50)
Defense.start(c);step()
eq(pc:GetAttribute("EGGRUMBLE_StealthUntil")<=os.clock(),true,"REAL_SENSOR_REVEAL")
eq(ec.Health,88,"REAL_SENSOR_THEN_TURRET_VISIBLE_TARGET")
eq(fc.Health,100,"REAL_SAME_TEAM_FRIEND_SAFE")
c.castleDefenseStop()

local d,ed,fd=scenario({"TRAP"},Vector3.new(0,1,-29),Vector3.new(0,1,-29),0)
Defense.start(d);step()
eq(ed.Health,92,"REAL_TRAP_8_DAMAGE")
eq(ed.WalkSpeed<16,true,"REAL_TRAP_SPEED_REDUCTION")
eq(fd.Health,100,"REAL_TRAP_TEAM_FRIEND_SAFE")
d.castleDefenseStop()

local noModule,em=scenario({},Vector3.new(25,6,-18),Vector3.new(25,6,-18),0)
Defense.start(noModule);step()
eq(em.Health,100,"REAL_NO_UNPURCHASED_TURRET")
noModule.castleDefenseStop()

local closed,ee=scenario({"TURRET"},Vector3.new(25,6,-18),Vector3.new(25,6,-18),0)
closed.rules.phase="FINISHED"
Defense.start(closed);step()
eq(ee.Health,100,"REAL_POSTMATCH_NO_DAMAGE")
closed.castleDefenseStop()
print("GQ500_ORIGINAL_LIVE_SERVER_NATIVE_VM_PASS checks="..tostring(n))
'''
def make(policy:Path,live:Path,spec:Path,outpolicy:Path,outmutant:Path,outlive:Path):
    a=policy.read_bytes();b=live.read_bytes()
    if blob(a)!=POLICY_BLOB or blob(b)!=LIVE_BLOB:raise ValueError("RED_GQ500_ORIGINAL_SOURCE_DRIFT")
    p=a.decode("utf8");l=b.decode("utf8")
    tests=spec.read_text(encoding="utf8")
    needle='local P=require("../EGGRUMBLE_CastleDefensePolicy")'
    if tests.count(needle)!=1 or p.count("return Policy\n")!=1:
        raise ValueError("RED_GQ500_AUTHOR_SPEC_DRIFT")
    pure=p.replace("return Policy\n","local P=Policy\n",1)
    suite=tests.replace(needle,"",1)
    outpolicy.write_text(pure+"\n"+suite,encoding="utf8")
    mutated=pure.replace('if owner.team==intruder.team then return false end',
                         'if false then return false end',1)
    if mutated==pure:raise ValueError("RED_GQ500_TEAM_MUTANT_UNAVAILABLE")
    outmutant.write_text(mutated+"\n"+suite,encoding="utf8")
    importline='local Policy=require(script.Parent:WaitForChild("EGGRUMBLE_CastleDefensePolicy"))\n'
    if l.count(importline)!=1 or l.count("return Defense\n")!=1:
        raise ValueError("RED_GQ500_LIVE_IMPORT_CHANGED")
    module=l.replace(importline,"",1).replace("return Defense\n","",1)
    outlive.write_text(p.replace("return Policy\n","",1)+"\n"+SIMULATOR[:SIMULATOR.index('-- Original source #500 actual Defense.start')].replace(
        'local a,e,f=scenario','local a,e,f=scenario')+
        module+"\n"+SIMULATOR[SIMULATOR.index('-- Original source #500 actual Defense.start'):],encoding="utf8")
    print("GQ500_ORIGINAL_AUTHOR_POLICY_SPEC_MUTANT_AND_ACTUAL_LIVE_NATIVE_VM_GENERATED")
if __name__=="__main__":
    x=argparse.ArgumentParser()
    for s in ("policy","live","spec","outpolicy","outmutant","outlive"):
        x.add_argument("--"+s,type=Path,required=True)
    z=x.parse_args()
    make(z.policy,z.live,z.spec,z.outpolicy,z.outmutant,z.outlive)
