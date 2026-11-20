#!/usr/bin/env python3
"""Execute the actual pinned #484 BotActors tryHeroAttack source (not a fake rewrite).

Real bot target predicate plus actual #482 patched host membership callback are
extracted byte-for-byte. Spatial geometry/Raycast is intentionally stubbed:
actual Roblox physics and 2-client movement remain NOT_TESTED.
"""
import argparse
from pathlib import Path
import re

p=argparse.ArgumentParser()
p.add_argument("--patched-host",type=Path,required=True)
p.add_argument("--patched-bot",type=Path,required=True)
p.add_argument("--out",type=Path,required=True)
p.add_argument("--mutant",action="store_true")
a=p.parse_args()
host=a.patched_host.read_text(encoding="utf-8")
bot=a.patched_bot.read_text(encoding="utf-8")
callbacks=re.findall(r"  session\.isCurrentHuman=function\(player:Player\):boolean\n.*?\n  end",host,re.DOTALL)
if len(callbacks)!=1: raise SystemExit("RED: exact server-authoritative callback not found")
functions=re.findall(
    r"local function tryHeroAttack\(actor:Model,my:any,session:any,lastHit:\{\[string\]:number\},bots:\{\[string\]:Model\}\):boolean\n.*?\nend\n-- Neutral combat",
    bot,re.DOTALL,
)
if len(functions)!=1: raise SystemExit("RED: #484 actual AI-duel capable tryHeroAttack signature missing")
fn=functions[0].removesuffix("\n-- Neutral combat")
if fn.count("targetHumanoid:TakeDamage(BOT_HERO_DAMAGE)")!=1: raise SystemExit("RED: real #484 AI duel lost")
if fn.count("session.isCurrentHuman(player)")!=1: raise SystemExit("RED: human membership gate lost")
if a.mutant:
    needle="   and session.isCurrentHuman~=nil and session.isCurrentHuman(player)\n"
    if fn.count(needle)!=1: raise SystemExit("RED: mutant insertion point drift")
    fn=fn.replace(needle,"",1)

harness=r'''
-- Mock Roblox-only spatial values; actual attack routing, team, membership and
-- bot-to-bot duel code below is extracted from exact real patched Luau sources.
local function v(x)
 local z={x=x}
 return setmetatable(z,{
  __sub=function(l,r)return {Magnitude=math.abs(l.x-r.x)} end,
  __add=function(l,r)return v(l.x+r.x) end,
 })
end
local Vector3={new=function(x,y,z)return v(x) end}
local BOT_ATTACK_INTERVAL=1.15
local BOT_HERO_DAMAGE=13
local strikeClear=true
local function clearHeroStrike(a,b,c,d)return strikeClear end
local Players={}
local mode="TEAM"
local humanHealth={Health=100,damage=0}
function humanHealth:TakeDamage(d)self.damage+=d end
local root={Position=v(3)}
local character={}
function character:FindFirstChild(name)
 if name=="HumanoidRootPart" then return root end
 return nil
end
function character:FindFirstChildOfClass(class)
 return class=="Humanoid" and humanHealth or nil
end
local player={UserId=101,Parent=Players,Character=character,stealthUntil=0}
function player:GetAttribute(key)
 if key=="EGGRUMBLE_StealthUntil" then return self.stealthUntil end
 return nil
end
local playerList={player}
function Players:GetPlayers() return playerList end
local my={id="AI_1",team="RED"}
local session={
 mode="TEAM",
 rules={phase="ACTIVE",castles={
   ["101"]={id="101",alive=true,isAI=false,team="BLUE"},
   ["AI_1"]={id="AI_1",alive=true,isAI=true,team="RED"},
   ["AI_2"]={id="AI_2",alive=true,isAI=true,team="BLUE"},
 }},
}
local sessions={TEAM=session,BATTLE_ROYALE={}}
local joined={[101]="TEAM"}
local actor={}
function actor:GetPivot()return {Position=v(0)} end
local hitAt={["AI_1"]=-100}
local enemyHealth={Health=100,damage=0}
function enemyHealth:TakeDamage(d)self.damage+=d end
local targetActor={Parent=true,PrimaryPart={Position=v(4)}}
function targetActor:FindFirstChildOfClass(c)return c=="Humanoid" and enemyHealth or nil end
''' 
harness+=callbacks[0].strip()+"\n"+fn+"\n"+r'''
local checks=0
local function verify(label,wantHit,wantHumanDamage,wantBotDamage,bots)
 humanHealth.damage=0
 enemyHealth.damage=0
 hitAt.AI_1=-100
 local got=tryHeroAttack(actor,my,session,hitAt,bots or {})
 assert(got==wantHit,label..": hit mismatch")
 assert(humanHealth.damage==wantHumanDamage,label..": human HP mismatch: "..humanHealth.damage)
 assert(enemyHealth.damage==wantBotDamage,label..": AI duel damage mismatch: "..enemyHealth.damage)
 checks+=1
end
verify("same mode live human receives genuine 13HP attack",true,13,0)
joined[101]=nil
verify("disconnected old castle cannot receive human hit",false,0,0)
joined[101]="BATTLE_ROYALE"
verify("wrong-mode rejoin cannot receive human hit",false,0,0)
joined[101]="TEAM"
player.Parent=nil
verify("detached player cannot receive hit",false,0,0)
player.Parent=Players
session.rules.castles["101"].isAI=true
verify("old seat under AI takeover cannot receive human hit",false,0,0)
session.rules.castles["101"].isAI=false
sessions.TEAM={}
verify("replaced session cannot hit old human",false,0,0)
sessions.TEAM=session
session.rules.phase="FINISHED"
verify("finished match no human hit",false,0,0)
session.rules.phase="ACTIVE"
session.rules.castles["101"].team="RED"
verify("same team human fire blocked",false,0,0)
session.rules.castles["101"].team="BLUE"
player.stealthUntil=os.clock()+999
verify("legitimate stealth blocks bot human hit",false,0,0)
player.stealthUntil=0
strikeClear=false
verify("solid wall LoS blocks human hit",false,0,0)
strikeClear=true
humanHealth.Health=0
verify("dead target receives zero damage",false,0,0)
humanHealth.Health=100
joined[101]="BATTLE_ROYALE"
verify("existing AI-vs-AI duel survives new human membership gate",true,0,13,{AI_2=targetActor})
session.rules.castles["AI_2"].team="RED"
verify("same-team AI duel fire blocked",false,0,0,{AI_2=targetActor})
session.rules.castles["AI_2"].team="BLUE"
joined[101]="TEAM"
humanHealth.damage=0
hitAt.AI_1=os.clock()
assert(tryHeroAttack(actor,my,session,hitAt,{})==false,"AI attack cooldown failed")
assert(humanHealth.damage==0,"cooldown hit human")
checks+=1
print("GQ #484 REAL BOT HIT + #482 HOST MEMBERSHIP native PASS "..checks.."/"..checks)
'''
a.out.write_text(harness,encoding="utf-8")
print("GQ native bot-hit generated:",a.out, "MUTANT" if a.mutant else "REAL")
