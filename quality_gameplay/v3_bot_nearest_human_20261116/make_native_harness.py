#!/usr/bin/env python3
"""Run the ACTUAL patched BotActors tryHeroAttack function in native Luau."""
from pathlib import Path
import argparse
from patch_nearest import apply

BEFORE = r'''
local v
local mt={}
mt.__index=function(t,k)
 if k=="Magnitude" then return math.sqrt(t.X*t.X+t.Y*t.Y+t.Z*t.Z) end
end
v=function(x,y,z) return setmetatable({X=x,Y=y,Z=z},mt) end
mt.__sub=function(a,b) return v(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end
mt.__add=function(a,b) return v(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end
Vector3={new=v}
local humans={}
local Players={}
function Players:GetPlayers() return humans end
local BOT_HERO_DAMAGE=13
local BOT_ATTACK_INTERVAL=1.15
local function clearHeroStrike(_,target,_,_) return target.blocked~=true end
local actor={Parent=true}
function actor:GetPivot() return {Position=v(0,0,0)} end
local my={id="AI_1",team="RED"}
local function human(id,x)
 local h={Health=100,hits=0}
 function h:TakeDamage(d) self.Health-=d;self.hits+=1 end
 local char={position=v(x,0,0),blocked=false}
 function char:FindFirstChild(k)
  if k=="HumanoidRootPart" then return {Position=self.position} end
 end
 function char:FindFirstChildOfClass(k) if k=="Humanoid" then return h end end
 local p={UserId=id,Character=char,active=true,stealth=0}
 function p:GetAttribute(k) if k=="EGGRUMBLE_StealthUntil" then return self.stealth end end
 return p,h,char
end
local function scenario(list,bot)
 humans=list
 local castles={AI_1={id="AI_1",team="RED",alive=true}}
 for _,p in ipairs(list) do
  castles[tostring(p.UserId)]={id=tostring(p.UserId),alive=true,team="BLUE"}
 end
 if bot then castles.AI_2={id="AI_2",team="BLUE",alive=true} end
 local s={mode="TEAM",rules={castles=castles}}
 function s.isCurrentHuman(p) return p.active end
 local bots={}
 if bot then bots.AI_2=bot end
 return s,bots
end
'''
AFTER = r'''
local far,farH=human(100,10)
local near,nearH=human(101,3)
local s,b=scenario({far,near},nil)
assert(tryHeroAttack(actor,my,s,{AI_1=-1000},b)==true)
assert(nearH.hits==1 and farH.hits==0,"nearest must win over player enumeration")

local p1,h1,c1=human(102,3)
local p2,h2=human(103,9)
c1.blocked=true
s,b=scenario({p1,p2},nil)
assert(tryHeroAttack(actor,my,s,{AI_1=-1000},b))
assert(h1.hits==0 and h2.hits==1,"blocked nearest must fall back to visible")

local p3,h3=human(104,2)
local p4,h4=human(105,8)
p3.active=false
s,b=scenario({p3,p4},nil)
assert(tryHeroAttack(actor,my,s,{AI_1=-1000},b))
assert(h3.hits==0 and h4.hits==1,"not-current human must be ineligible")

local p5,h5=human(106,2)
local p6,h6=human(107,8)
p5.stealth=math.huge
s,b=scenario({p5,p6},nil)
assert(tryHeroAttack(actor,my,s,{AI_1=-1000},b))
assert(h5.hits==0 and h6.hits==1,"existing stealth rule must be preserved")

local hb={Health=100,hits=0}
function hb:TakeDamage(d) self.Health-=d;self.hits+=1 end
local bot={Parent=true,PrimaryPart={Position=v(4,0,0)}}
function bot:FindFirstChildOfClass(k) if k=="Humanoid" then return hb end end
s,b=scenario({},bot)
assert(tryHeroAttack(actor,my,s,{AI_1=-1000},b))
assert(hb.hits==1,"original bot-versus-bot fallback must remain")

s,b=scenario({},nil)
assert(tryHeroAttack(actor,my,s,{AI_1=-1000},b)==false)
print("GQ_REAL_BOT_HUMAN_NEAREST_NATIVE_6_CASES_PASS")
'''
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--bot",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    a=ap.parse_args()
    src=a.bot.read_text()
    begin=src.index("local function tryHeroAttack(")
    end=src.index("-- Neutral combat is optional",begin)
    function=src[begin:end]
    for guard in ("nearestHumanoid", "session.isCurrentHuman(player)",
                  "targetHumanoid:TakeDamage(BOT_HERO_DAMAGE)"):
        assert guard in function
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(BEFORE+"\n"+function+"\n"+AFTER,encoding="utf-8")
    print("NATIVE_HARNESS_FROM_EXACT_REAL_BOT_SOURCE",len(function))
if __name__=="__main__":
    main()
