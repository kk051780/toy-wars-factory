#!/usr/bin/env python3
"""Execute real #482 Combat human-hit/status/heal with real #531 Host membership callback."""
import argparse
from pathlib import Path
from compose import HELPER

PREFIX = r'''
local clock = 100
local os={clock=function() return clock end}
local task={delay=function() end}
local mt={}
mt.__index=function(v,key)
 if key=="Magnitude" then return math.sqrt(v.X*v.X+v.Y*v.Y+v.Z*v.Z) end
 return rawget(v,key)
end
mt.__sub=function(a,b) return setmetatable({X=a.X-b.X,Y=a.Y-b.Y,Z=a.Z-b.Z},mt) end
mt.__add=function(a,b) return setmetatable({X=a.X+b.X,Y=a.Y+b.Y,Z=a.Z+b.Z},mt) end
local function v(x,y,z) return setmetatable({X=x,Y=y,Z=z},mt) end
local Vector3={new=v}
local pList={}
local Players={}
function Players:GetPlayers() return pList end
local game={GetService=function(_,name) assert(name=="Players");return Players end}
local AttackGeometry={allowed=function() return true end}
local ImpactFeedback={hit=function() end}
local function lineClear() return true end
local function characterOf(player)
 if player.h.Health<=0 then return nil,nil,nil end
 return player.Character,player.root,player.h
end
local function makeHuman(id,x)
 local p={UserId=id,Parent=Players,attrs={},Character={},root={Position=v(x,0,0)}}
 p.h={Health=100,MaxHealth=100,attrs={},WalkSpeed=16}
 function p:GetAttribute(key) return self.attrs[key] end
 function p.h:GetAttribute(key) return self.attrs[key] end
 function p.h:SetAttribute(key,value) self.attrs[key]=value end
 function p.h:TakeDamage(value) self.Health-=value end
 return p
end
'''
TESTS = r'''
local p=makeHuman(1,0)
local enemy=makeHuman(2,8)
local ally=makeHuman(3,7)
local stale=makeHuman(4,9)
pList={p,enemy,ally,stale}
local joined={[1]="TEAM",[2]="TEAM",[3]="TEAM",[4]="BATTLE_ROYALE"}
local sessions={}
local mode="TEAM"
local session={mode="TEAM",rules={phase="ACTIVE",castles={
 ["1"]={id="1",team="RED",alive=true,isAI=false,heldEggs=0},
 ["2"]={id="2",team="BLUE",alive=true,isAI=false,heldEggs=0},
 ["3"]={id="3",team="RED",alive=true,isAI=false,heldEggs=0},
 ["4"]={id="4",team="BLUE",alive=true,isAI=false,heldEggs=0},
}},botActors={}}
sessions.TEAM=session
'''
AFTER = r'''
local function hit()
 return hitHumanHeroes(session,p,p.root,p.Character,v(8,0,0),22,20,"CONE")
end
local function debuff()
 secondaryEffect(session,p,p.root,p.Character,v(8,0,0),22,"MARK","CONE")
end
-- Actual human-hit source; stale BR participant is physically in TEAM battle.
assert(hit()==1,"TEAM_VALID_EXPECT_ONE")
assert(enemy.h.Health==80 and stale.h.Health==100,"LOBBY_OTHER_MODE_MUST_NOT_BE_HIT")
-- A stale Castle ID cannot override server-side joined state.
joined[2]="BATTLE_ROYALE";enemy.h.Health=100
assert(hit()==0 and enemy.h.Health==100,"STALE_TARGET_HIT")
-- AI took over this same UserId's old castle.
joined[2]="TEAM";session.rules.castles["2"].isAI=true
assert(hit()==0 and enemy.h.Health==100,"AI_TAKEOVER_TARGET_HIT")
session.rules.castles["2"].isAI=false
-- Player object has disconnected but old castle still exists.
enemy.Parent=nil
assert(hit()==0 and enemy.h.Health==100,"DISCONNECTED_TARGET_HIT")
enemy.Parent=Players
-- Restored valid match membership: valid original combat damage retained.
assert(hit()==1 and enemy.h.Health==80,"RESTORED_PVP_NOT_DAMAGING")
-- Friendly fire remains forbidden.
enemy.h.Health=100;session.rules.castles["2"].team="RED"
assert(hit()==0 and enemy.h.Health==100,"FRIENDLY_FIRE")
session.rules.castles["2"].team="BLUE"
-- Status must not mark the old-member enemy.
joined[2]="BATTLE_ROYALE"
debuff()
assert(enemy.h:GetAttribute("EGGRUMBLE_MarkedUntil")==nil,"STALE_STATUS")
joined[2]="TEAM"
debuff()
assert(enemy.h:GetAttribute("EGGRUMBLE_MarkedUntil")==104,"VALID_STATUS_MISSING")
-- Mage heals only current human teammate, not a stale user sharing old castle.
ally.h.Health=40
p.h.Health=40
healAllies(session,p,p.root)
assert(ally.h.Health==65 and p.h.Health==65,"VALID_TEAM_HEAL")
stale.h.Health=40
session.rules.castles["4"].team="RED"
healAllies(session,p,p.root)
assert(stale.h.Health==40,"STALE_MAGE_HEAL")
-- If the #531 callback is not installed, attacks fail closed (integration RED).
session.isCurrentHuman=nil
enemy.h.Health=100
assert(hit()==0 and enemy.h.Health==100,"MISSING_HOST_CALLBACK_MUST_FAIL_CLOSED")
-- Returning a nonboolean truthy value is not accepted.
session.isCurrentHuman=function() return "true" end
assert(hit()==0,"TRUTHY_CALLBACK_BYPASS")
-- If the single server membership authority throws, no damage is done.
session.isCurrentHuman=function() error("membership backend failed") end
assert(hit()==0,"CALLBACK_EXCEPTION_BYPASS")
-- Old session snapshot is no longer active; original callback rejects it.
'''
FINAL = r'''
-- Restore original callback, then simulate host rotating the session.
'''
FINISH = r'''
sessions.TEAM={different="new round"}
assert(hit()==0,"STALE_SESSION_TARGET_HIT")
print("GQ_HUMAN_COMBAT_MEMBERSHIP_REAL_SOURCE_14_CASES_PASS")
'''

def section(source: str, start: str, end: str) -> str:
    if source.count(start) != 1 or source.count(end) != 1:
        raise ValueError("RED duplicate/missing original Luau section")
    return start + source.split(start,1)[1].split(end,1)[0]

def host_callback(host: str) -> str:
    start = "session.isCurrentHuman=function(player:Player):boolean"
    end = "\n  end\n -- Clean up only this finished match;"
    if host.count(start) != 1 or host.count(end) != 1:
        raise ValueError("RED require exact #531 Host callback")
    return host.split(start,1)[0].rsplit("\n",1)[-1] + start + host.split(start,1)[1].split(end,1)[0] + "\n  end\n"

def build(combat: str, host: str) -> str:
    if HELPER not in combat:
        raise ValueError("RED membership helper missing")
    hit = section(combat, "local function hitHumanHeroes(", "\nlocal function neutralAndBotHit(")
    heal = section(combat, "local function healAllies(", "\n-- Status effects")
    status = section(combat, "local function secondaryEffect(", "\nlocal function execute(")
    callback=host_callback(host)
    if callback.count("sessions[mode]==session")!=1 or callback.count("joined[player.UserId]==mode")!=1:
        raise ValueError("RED original #531 callback degraded")
    # The existing #529 four-author Combat has an independent stealth helper.
    # Carry it into the same native VM, never replace or duplicate its behavior.
    stealth = ""
    token = "local function humanCombatTargetable("
    if token in combat:
        if combat.count(token) != 1:
            raise ValueError("RED duplicated existing human stealth author")
        fragment = combat.split(token, 1)[1]
        if "\nend\n" not in fragment:
            raise ValueError("RED missing original #529 stealth helper end")
        stealth = token + fragment.split("\nend\n", 1)[0] + "\nend\n"
    return PREFIX + stealth + HELPER + "\n" + hit + "\n" + heal + "\n" + status + "\n" + TESTS + callback + "\n" + AFTER + FINAL + callback + "\n" + FINISH

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--combat",type=Path,required=True)
    p.add_argument("--host",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    a.out.write_text(build(a.combat.read_text(),a.host.read_text()),encoding="utf-8")
