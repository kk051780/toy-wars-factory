#!/usr/bin/env python3
"""Native Luau harness from ACTUAL V3 server combat function, not rewritten policy mock.

The source under test is the genuine patched secondaryEffect body. Roblox types,
world geometry and scheduler are small fakes. This proves async gate behavior in
a Luau VM, not Studio physics or end-to-end player UX.
"""
import argparse
import pathlib

ROOT=pathlib.Path(__file__).resolve().parents[1]
PATCH=ROOT/"EGGRUMBLE_SevenRoleCombat.patched.luau"
MARKER="local function secondaryEffect("
AFTER="\nlocal function execute("
HEADER=r'''--!strict
-- Generated from the exact patched original server secondaryEffect function.
local StatusTickFence=require("./StatusFence")
local vecMeta={}
vecMeta.__index=function(v,k)
 if k=="Magnitude" then return math.sqrt(v.x*v.x+v.y*v.y+v.z*v.z) end
 return nil
end
vecMeta.__sub=function(a,b)
 return setmetatable({x=a.x-b.x,y=a.y-b.y,z=a.z-b.z},vecMeta)
end
vecMeta.__add=function(a,b)
 return setmetatable({x=a.x+b.x,y=a.y+b.y,z=a.z+b.z},vecMeta)
end
local Vector3={}
function Vector3.new(x,y,z) return setmetatable({x=x,y=y,z=z},vecMeta) end
local position=Vector3.new(2,0,0)
local AttackGeometry={allowed=function(...) return true end}
local function lineClear(...) return true end
local pending={}
local task={}
function task.delay(seconds,cb)
 assert(type(seconds)=="number" and type(cb)=="function")
 table.insert(pending,cb)
end
local players={}
local playersService={}
function playersService:GetPlayers() return players end
function playersService:GetPlayerByUserId(uid)
 for _,p in ipairs(players) do
  if p.UserId==uid then return p end
 end
 return nil
end
local game={}
function game:GetService(name)
 assert(name=="Players")
 return playersService
end
local function newHum()
 local h={Health=100,WalkSpeed=16,MaxHealth=100,Parent=true,damage=0,attrs={}}
 function h:GetAttribute(k) return self.attrs[k] end
 function h:SetAttribute(k,v) self.attrs[k]=v end
 function h:TakeDamage(v) self.damage+=v;self.Health-=v end
 return h
end
local function newChar(h)
 local c={Humanoid=h,Root={Position=position}}
 function c:FindFirstChildOfClass(t)
  assert(t=="Humanoid")
  return self.Humanoid
 end
 return c
end
local function characterOf(p)
 local c=p.Character
 if not c then return nil,nil,nil end
 return c,c.Root,c.Humanoid
end
local function newBot(h)
 local b={Humanoid=h,PrimaryPart={Position=position},attrs={}}
 function b:FindFirstChildOfClass(t) assert(t=="Humanoid");return self.Humanoid end
 function b:GetAttribute(k) return self.attrs[k] end
 function b:SetAttribute(k,v) self.attrs[k]=v end
 return b
end
'''
TESTS=r'''
local numCases=0
local function expect(name,actual,want)
 numCases+=1
 assert(actual==want,string.format("%s: got %s wanted %s",name,tostring(actual),tostring(want)))
end
local function setup(mode,kind,targetTeam)
 pending={}
 local meH=newHum()
 local enemyH=newHum()
 local attacker={UserId=1,Character=newChar(meH)}
 local target={UserId=2,Character=newChar(enemyH)}
 local rules={phase="ACTIVE",winner=nil,castles={
  ["1"]={alive=true,team="RED"},
  ["2"]={alive=true,team=targetTeam or "BLUE"},
  ["AI_1"]={alive=true,team=targetTeam or "BLUE"},
 }}
 local session={mode=mode,rules=rules,botActors={}}
 local bot
 if kind=="bot" then
  bot=newBot(enemyH)
  session.botActors["AI_1"]=bot
  players={attacker}
 else
  players={attacker,target}
 end
 return session,attacker,target,enemyH,bot,rules
end
local function schedule(mode,kind,effect,team)
 local session,attacker,target,h,bot,rules=setup(mode,kind,team)
 secondaryEffect(session,attacker,attacker.Character.Root,attacker.Character,position,25,effect or "BURN_3S","ARC")
 return session,attacker,target,h,bot,rules
end
local function fire()
 for _,callback in ipairs(pending) do callback() end
end
do
 local s,a,t,h,b,r=schedule("TEAM","human")
 expect("human scheduled",#pending,3)
 fire();expect("human BURN valid 3 ticks",h.damage,12)
end
do
 local s,a,t,h,b,r=schedule("BATTLE_ROYALE","human","BURN_3S","RED")
 expect("BR enemies no team restriction",#pending,3)
 fire();expect("BR BURN valid",h.damage,12)
end
do
 local s,a,t,h,b,r=schedule("TEAM","human","BURN_3S","RED")
 expect("TEAM friendly zero callbacks",#pending,0)
end
do
 local s,a,t,h,b,r=schedule("TEAM","human")
 r.castles["2"].alive=false
 fire();expect("castle fallen blocks original DOT",h.damage,0)
end
do
 local s,a,t,h,b,r=schedule("TEAM","human")
 r.castles["2"]={alive=true,team="BLUE"}
 fire();expect("new castle at old id cannot inherit DOT",h.damage,0)
end
do
 local s,a,t,h,b,r=schedule("TEAM","human")
 r.phase="FINISHED"
 fire();expect("terminal round blocks DOT",h.damage,0)
end
do
 local s,a,t,h,b,r=schedule("BATTLE_ROYALE","human")
 r.winner="1"
 fire();expect("winner blocks DOT",h.damage,0)
end
do
 local s,a,t,h,b,r=schedule("TEAM","human")
 s.rules={phase="ACTIVE",winner=nil,castles=r.castles}
 fire();expect("cross-round session replace blocks DOT",h.damage,0)
end
do
 local s,a,t,h,b,r=schedule("TEAM","human")
 t.Character=newChar(newHum())
 fire();expect("respawn Avatar identity blocks old DOT",h.damage,0)
end
do
 local s,a,t,h,b,r=schedule("TEAM","human")
 players={a}
 fire();expect("disconnect blocks DOT",h.damage,0)
end
do
 local s,a,t,h,b,r=schedule("TEAM","human")
 h.Health=0
 fire();expect("dead humanoid blocks DOT",h.damage,0)
end
do
 local s,a,t,h,b,r=schedule("TEAM","bot")
 expect("bot scheduled",#pending,3)
 fire();expect("bot valid BURN",h.damage,12)
end
do
 local s,a,t,h,b,r=schedule("TEAM","bot","PREDATOR")
 fire();expect("bot valid PREDATOR 5x3",h.damage,15)
end
do
 local s,a,t,h,b,r=schedule("TEAM","bot")
 s.botActors["AI_1"]=newBot(newHum())
 fire();expect("bot replacement blocks old DOT",h.damage,0)
end
do
 local s,a,t,h,b,r=schedule("TEAM","bot")
 b.Humanoid=newHum()
 fire();expect("bot Humanoid replacement blocks DOT",h.damage,0)
end
do
 local s,a,t,h,b,r=schedule("TEAM","bot")
 r.castles["AI_1"].alive=false
 fire();expect("bot castle fallen blocks DOT",h.damage,0)
end
do
 local s,a,t,h,b,r=schedule("TEAM","bot")
 r.castles["AI_1"]={alive=true,team="BLUE"}
 fire();expect("new bot castle at old id cannot inherit DOT",h.damage,0)
end
do
 local s,a,t,h,b,r=schedule("TEAM","bot")
 r.phase="FINISHED"
 fire();expect("bot terminal round blocks DOT",h.damage,0)
end
print("GQ_V3_ACTUAL_SERVER_STATUS_CALLBACK_NATIVE_18_SCENARIOS_PASS",numCases)
'''
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=pathlib.Path)
    parser.add_argument("--source",type=pathlib.Path,default=PATCH)
    args=parser.parse_args()
    text=args.source.read_text(encoding="utf8")
    assert text.count(MARKER)==1 and text.count(AFTER)==1
    start=text.index(MARKER)
    end=text.index(AFTER,start)
    original=text[start:end]
    assert "StatusTickFence.canTick(session.rules,originalRules," in original
    assert original.count("h:TakeDamage(tick)")==1
    assert original.count("task.delay(i,function()")==1
    assert 'castleAtApplication=originalRules.castles and originalRules.castles[targetId]' in original
    assert 'sameTarget=(session.botActors or {})[targetId]==bot' in original
    assert 'player.Character:FindFirstChildOfClass("Humanoid")==h' in original
    out=args.out.resolve()
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(HEADER+original+"\n"+TESTS,encoding="utf8")
    print("GQ_V3_ACTUAL_SERVER_DOT_CALLBACK_EXTRACTED",len(original))
if __name__=="__main__":
    main()
