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
                IsDescendantOf=function(self) return false end,
                IsA=function(self,k)
                    return k==self.ClassName or (k=="BasePart" and self.ClassName=="Part")
                end
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
local arena=Instance.new("Part")
arena.Position=vec(0,-3,0)
arena.Size=vec(250,4,142)
local road=Instance.new("Part")
road.Position=vec(0,-.85,0)
road.Size=vec(226,.3,24)
local world={
    FindFirstChild=function(self,name)
        if name=="GrassArena" then return arena end
        if name=="CenterRoad" then return road end
        return nil
    end
}
local h=Horde.new(world)
h:reset(1,0)
eq(h:livingCount(),9,"spawn nine")
eq(math.abs(h.mobs[1].pos.Y-1.65-(-1))<.00001,true,"minion feet touch source arena")
eq(math.abs(h.mobs[9].pos.Y-2.5-(-.7))<.00001,true,"elite feet touch road")
eq(h.mobs[9].pos.Y<h.mobs[1].pos.Y+2.5,true,"real map height not hardcoded 3.4")
eq(#h.mobs,9,"record nine")
local firstLook=h.mobs[1]
eq(#firstLook.arms,2,"original V6 has two waving visible claws")
eq(#firstLook.eyes,2,"original V6 has two blinkable toy eyes")
eq(firstLook.arms[1].CanCollide,false,"visual claws never collide")
eq(firstLook.arms[1].CanQuery,false,"visual claws never hide raycast targets")
eq(firstLook.eyes[1].CanQuery,false,"facial detail cannot block LOS")
h:tick(.2,{},emptyHealth)
eq(type(firstLook.arms[1].Orientation.X),"number","real source animates visible arms")
eq(type(firstLook.eyes[1].Transparency),"number","real source controls blinking")
local elite=h.mobs[9]
eq(elite.zone~=nil,true,"elite radius visual exists")
eq(elite.zone.Size.X,18,"warning radius exactly 9 stud")
eq(elite.zone.CanQuery,false,"warning visual does not affect raycasts")
eq(elite.zone.CanCollide,false,"warning visual never blocks runners")
eq(elite.zone.Transparency,1,"warning hidden outside windup")
eq(h:eliteWarningSeconds(0),0,"no bogus elite warning")
local origin=vec(-34,2.7,-18)
local forward=vec(1,0,0)
local first=h.mobs[1]
local nick,none=h:hit(origin,forward,5,.25,nil)
eq(nick,1,"nonfatal visible sword hit")
eq(none,0,"nonfatal hit grants no defeated credit")
eq(first.hp,19,"actual minion takes real 5HP")
eq(first.attackAt,.9,"hit minion cannot instant counterattack")
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
e.zone.Transparency=.62
local eliteHits,eliteKills=h:hit(vec(-10,3.4,0),forward,40,12,nil)
eq(eliteHits,1,"elite hit")
eq(eliteKills,0,"elite not one-shot")
local hit2,ko2=h:hit(vec(-10,3.4,0),forward,40,12.9,nil)
eq(hit2,1,"elite second hit")
eq(ko2,1,"elite second hit ko")
eq(e.tellUntil,0,"kill cancels old telegraph")
eq(e.target,nil,"kill clears old target")
eq(e.zone.Transparency,1,"kill hides elite ground warning immediately")
eq(h:eliteWarningSeconds(12.95),0,"dead elite cannot show warning")
h:tick(20.8,{victim},emptyHealth)
eq(e.hp,0,"elite not early respawn")
h:tick(21,{},emptyHealth)
eq(e.hp,72,"elite respawns after eight")
eq(e.target,nil,"elite target clean on respawn")
eq(e.attackAt,22.5,"elite reentry grace")
eq(e.zone.Transparency,1,"respawn warning hidden")
-- Check real telegraph state transition, with line-of-sight and dodge.
local impacts0=h:tick(22.5,{victim},emptyHealth)
eq(e.tellUntil,24,"elite winds up 1.5s")
eq(e.zone.Transparency,.62,"elite red 9stud warning visible")
eq(h:eliteWarningSeconds(23),1,"server remaining-second snapshot")
eq(#impacts0,0,"no instant elite strike")
workspace.blocked=true
local impactedBlocked=h:tick(24,{victim},emptyHealth)
eq(#impactedBlocked,0,"no hit through wall")
eq(e.cue.Text,"✨ 強撃を回避！","elite emits truthful dodge feedback")
eq(e.zone.Transparency,1,"elite red ring closes after blocked strike")
eq(h:eliteWarningSeconds(24),0,"no stale warning after strike")
workspace.blocked=false
e.tellUntil=25
e.target=victim
e.attackAt=29
local impacted=h:tick(25,{victim},emptyHealth)
local eliteCount=0
for _,impact in ipairs(impacted) do if impact.kind=="ELITE" then eliteCount+=1 end end
eq(eliteCount,1,"visible elite strike after telegraph")
eq(e.cue.Text,"⚠ 強撃命中！","elite feedback truthfully reports landed strike")
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
-- Actual minion chase moves across the original grass->road boundary.
-- Floor y must follow MapBuilder, not remain at its original spawn.
local runner={alive=true,root={Position=vec(-24,3,0)}}
h:tick(30,{runner},emptyHealth)
h:tick(31,{runner},emptyHealth)
h:tick(32,{runner},emptyHealth)
h:tick(33,{runner},emptyHealth)
eq(first.pos.Z>-12,true,"minion actually crossed onto road")
eq(math.abs(first.pos.Y-(1.65-.7))<.001,true,"chase snaps feet to road top")
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
