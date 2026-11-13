#!/usr/bin/env python3
"""Exercise the *actual* H1 Horde Luau module under a tiny deterministic Roblox runtime mock.
Native Luau CLI executes the real module. Not real Roblox Studio, networking or FPS evidence.
"""
from pathlib import Path
import argparse
ROOT=Path(__file__).resolve().parents[1]
horde=(ROOT/"inputs/MusouHorde.luau").read_text(encoding="utf-8")
combat=(ROOT/"inputs/MusouCombatRules.luau").read_text(encoding="utf-8")
require='local Combat=require(script.Parent:WaitForChild("MusouCombatRules"))'
assert horde.count(require)==1
assert combat.count("return R")==1
horde=horde.replace(require,"local Combat=(function()\n"+combat+"\nend)()")
prefix=r'''
local function vec(x,y,z)
    return setmetatable({X=x,Y=y,Z=z},{
        __index=function(a,k)
            if k=="Magnitude" then
                return math.sqrt(a.X*a.X+a.Y*a.Y+a.Z*a.Z)
            elseif k=="Unit" then
                local n=math.sqrt(a.X*a.X+a.Y*a.Y+a.Z*a.Z)
                if n==0 then return vec(0,0,0) end
                return vec(a.X/n,a.Y/n,a.Z/n)
            elseif k=="Dot" then
                return function(self,b) return self.X*b.X+self.Y*b.Y+self.Z*b.Z end
            end
        end,
        __add=function(a,b) return vec(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end,
        __sub=function(a,b) return vec(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end,
        __mul=function(a,b)
            if type(a)=="number" then return vec(a*b.X,a*b.Y,a*b.Z) end
            if type(b)=="number" then return vec(a.X*b,a.Y*b,a.Z*b) end
            error("only number multiplication supported")
        end,
        __div=function(a,b) return vec(a.X/b,a.Y/b,a.Z/b) end,
    })
end
Vector3={new=vec,zero=vec(0,0,0)}
CFrame={
    new=function(p) return {position=p or vec(0,0,0)} end,
    lookAt=function(p,target) return {position=p,target=target} end
}
Color3={fromRGB=function(r,g,b) return {r,g,b} end}
UDim2={
    fromOffset=function(x,y) return {x,y} end,
    fromScale=function(x,y) return {x,y} end
}
Enum={
    Material={SmoothPlastic=1},
    PartType={Block=1,Ball=2},
    RaycastFilterType={Exclude=1}
}
RaycastParams={new=function() return {} end}
Instance={
    new=function(kind)
        return setmetatable({ClassName=kind,destroyed=false},{
            __index={
                Destroy=function(self) self.destroyed=true end,
                PivotTo=function(self,cf) self.pivot=cf end,
                IsDescendantOf=function(self) return false end
            }
        })
    end
}
workspace={blocked=false,rayCalls=0}
function workspace:Raycast(origin,displacement,params)
    self.rayCalls+=1
    if self.blocked then return {Instance={IsDescendantOf=function() return false end}} end
    return nil
end
local Horde=(function()
__ACTUAL_HORDE__
end)()
local passed=0
local function eq(a,b,name)
    assert(a==b,name..": got "..tostring(a).." expected "..tostring(b))
    passed+=1
end
local emptyHealth=function(p)
    if p.alive~=true then return false,nil,nil end
    return true,p.root,{Health=100}
end
local h=Horde.new({})
h:reset(1,0)
eq(h:livingCount(),9,"spawn nine")
eq(#h.mobs,9,"record nine")
local origin=vec(-34,2.7,-18)
local forward=vec(1,0,0)
local first=h.mobs[1]
local touched,killed=h:hit(origin,forward,24,1,nil)
eq(touched,1,"one minion struck")
eq(killed,1,"one minion ko")
eq(first.hp,0,"server hp zero")
eq(first.deadUntil,9,"eight-second respawn")
local t2,k2=h:hit(origin,forward,24,2,nil)
eq(t2,0,"dead minion cannot be farmed")
eq(k2,0,"no duplicate ko")
h:tick(8.9,{},emptyHealth)
eq(first.hp,0,"no early respawn")
h:tick(9,{},emptyHealth)
eq(first.hp,24,"respawn full hp")
eq(first.attackAt,10.5,"respawn grace")
eq(first.tellUntil,0,"respawn no stale telegraph")
workspace.blocked=true
local wallhits=h:hit(origin,forward,24,10,nil)
eq(wallhits,0,"wall blocks player sweep")
workspace.blocked=false
local highHits=h:hit(vec(-34,11,-18),forward,24,11,nil)
eq(highHits,0,"upper floor cannot sweep")
-- A killed elite cannot retain the old target or fire a stale post-respawn strike.
local e=h.mobs[9]
local victim={alive=true,root={Position=vec(5,3.4,0)}}
e.tellUntil=17
e.target=victim
local eliteHits,eliteKills=h:hit(vec(-10,3.4,0),forward,40,12,nil)
eq(eliteHits,1,"elite hit")
eq(eliteKills,0,"elite not one-shot")
local hit2,ko2=h:hit(vec(-10,3.4,0),forward,40,12.9,nil)
eq(hit2,1,"elite second hit")
eq(ko2,1,"elite second hit ko")
eq(e.tellUntil,0,"kill cancels old telegraph")
eq(e.target,nil,"kill clears old target")
h:tick(20.9,{victim},emptyHealth)
eq(e.hp,0,"elite not early respawn")
h:tick(21,{},emptyHealth)
eq(e.hp,72,"elite respawns after eight")
eq(e.target,nil,"elite target clean on respawn")
eq(e.attackAt,22.5,"elite reentry grace")
-- Check real telegraph state transition, with line-of-sight and dodge.
local impacts0=h:tick(22.5,{victim},emptyHealth)
eq(e.tellUntil,24,"elite winds up 1.5s")
eq(#impacts0,0,"no instant elite strike")
workspace.blocked=true
local impactedBlocked=h:tick(24,{victim},emptyHealth)
eq(#impactedBlocked,0,"no hit through wall")
workspace.blocked=false
e.tellUntil=25
e.target=victim
e.attackAt=29
local impacted=h:tick(25,{victim},emptyHealth)
local eliteCount=0
for _,impact in ipairs(impacted) do if impact.kind=="ELITE" then eliteCount+=1 end end
eq(eliteCount,1,"visible elite strike after telegraph")
e.tellUntil=26
e.target=victim
victim.root.Position=vec(22,3.4,0)
local escaped=h:tick(26,{victim},emptyHealth)
local escapedElite=0
for _,impact in ipairs(escaped) do if impact.kind=="ELITE" then escapedElite+=1 end end
eq(escapedElite,0,"distance dodge succeeds")
victim.root.Position=vec(5,12,0)
e.tellUntil=27
e.target=victim
local upstairs=h:tick(27,{victim},emptyHealth)
local upstairsElite=0
for _,impact in ipairs(upstairs) do if impact.kind=="ELITE" then upstairsElite+=1 end end
eq(upstairsElite,0,"upper-floor dodge succeeds")
h:clear()
eq(h:livingCount(),0,"cleanup clear enemy count")
eq(#h.mobs,0,"cleanup deletes references")
print("MUSOU_HORDE_NATIVE_"..tostring(passed).."_STATE_ASSERTIONS_PASS")
'''
source=prefix.replace("__ACTUAL_HORDE__",horde)
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--write",required=True)
    args=ap.parse_args()
    out=Path(args.write)
    out.write_text(source,encoding="utf-8")
    print("ACTUAL_HORDE_NATIVE_MOCK_TEST_SOURCE_GENERATED",out)
