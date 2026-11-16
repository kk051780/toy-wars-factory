#!/usr/bin/env python3
"""Exact-original #482 Combat overlay; never edits any authoritative game file."""
import argparse
import hashlib
from pathlib import Path

AUTHOR = Path("handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_SevenRoleCombat.luau")
SOURCE_BLOB = "66e666418b7c23d41f87faa5d61eb6e2770a463e"
HEAD = "fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9"
HELPER = '''-- NINJA stealth stops human targeting as it already stops bots; carrying a real
-- egg always reveals the player. This function never trusts client attributes
-- for egg ownership: caller passes server-owned castle state.
local function humanCombatTargetable(castle:any,player:Player):boolean
 return castle.heldEggs>0 or os.clock()>=(player:GetAttribute("EGGRUMBLE_StealthUntil") or 0)
end
'''
HIT_OLD = '''  if enemyPlayer~=p and enemyState and enemyState.alive
   and (session.mode~="TEAM" or enemyState.team~=state.team)'''
HIT_NEW = '''  if enemyPlayer~=p and enemyState and enemyState.alive
   and humanCombatTargetable(enemyState,enemyPlayer)
   and (session.mode~="TEAM" or enemyState.team~=state.team)'''
STATUS_OLD = '''  if targetPlayer~=p and target and target.alive and enemyChar and enemyRoot and hum
   and (session.mode~="TEAM" or target.team~=state.team)'''
STATUS_NEW = '''  if targetPlayer~=p and target and target.alive and enemyChar and enemyRoot and hum
   and humanCombatTargetable(target,targetPlayer)
   and (session.mode~="TEAM" or target.team~=state.team)'''

def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def patch(original: str) -> str:
    start = "local function hitHumanHeroes("
    assert original.count(start)==1
    for needle in (HIT_OLD,STATUS_OLD):
        assert original.count(needle)==1, "original author drift: " + needle
    assert "humanCombatTargetable" not in original
    fixed = original.replace(start, HELPER + start, 1)
    fixed = fixed.replace(HIT_OLD,HIT_NEW,1).replace(STATUS_OLD,STATUS_NEW,1)
    assert fixed.count("humanCombatTargetable(")==3
    assert fixed.count("function HeroCombat.equip(")==1
    return fixed

def section(src: str, first: str, next_one: str) -> str:
    assert src.count(first)==1 and src.count(next_one)==1
    return first + src.split(first,1)[1].split(next_one,1)[0]

HARNESS = r'''
local clock=100
local os={clock=function() return clock end}
local mt={}
mt.__index=function(v,k)
 if k=="Magnitude" then return math.sqrt(v.X*v.X+v.Y*v.Y+v.Z*v.Z) end
 return rawget(v,k)
end
mt.__sub=function(a,b) return setmetatable({X=a.X-b.X,Y=a.Y-b.Y,Z=a.Z-b.Z},mt) end
mt.__add=function(a,b) return setmetatable({X=a.X+b.X,Y=a.Y+b.Y,Z=a.Z+b.Z},mt) end
local function v(x,y,z) return setmetatable({X=x,Y=y,Z=z},mt) end
local Vector3={new=v}
local pList={}
local game={GetService=function(_,name)
 assert(name=="Players")
 return {GetPlayers=function() return pList end}
end}
local AttackGeometry={allowed=function() return true end}
local ImpactFeedback={hit=function() end}
local blocked=false
local function lineClear() return not blocked end
local function makeHuman(id,x)
 local obj={UserId=id,attrs={},Character={},root={Position=v(x,0,0)}}
 obj.h={Health=100,MaxHealth=100,attrs={}}
 function obj:GetAttribute(key) return self.attrs[key] end
 function obj.h:GetAttribute(key) return self.attrs[key] end
 function obj.h:SetAttribute(key,value) self.attrs[key]=value end
 function obj.h:TakeDamage(value) self.Health-=value end
 return obj
end
local function characterOf(other)
 if not other.Character or other.h.Health<=0 then return nil,nil,nil end
 return other.Character,other.root,other.h
end
'''
TESTS = r'''
local p=makeHuman(1,0)
local enemy=makeHuman(2,8)
local ally=makeHuman(3,7)
local stranger=makeHuman(4,9)
pList={p,enemy,ally,stranger}
local session={mode="TEAM",rules={phase="ACTIVE",castles={
 ["1"]={id="1",team="RED",alive=true,heldEggs=0},
 ["2"]={id="2",team="BLUE",alive=true,heldEggs=0},
 ["3"]={id="3",team="RED",alive=true,heldEggs=0},
}}}
local function attack()
 return hitHumanHeroes(session,p,p.root,p.Character,v(8,0,0),22,20,"CONE")
end
local function status()
 secondaryEffect(session,p,p.root,p.Character,v(8,0,0),22,"MARK","CONE")
end
-- 1 + 2: stealth prevents real PvP damage and its debuff, just like bot targeting.
enemy.attrs.EGGRUMBLE_StealthUntil=103
assert(attack()==0 and enemy.h.Health==100,"HIDDEN_HUMAN_WAS_DAMAGED")
status()
assert(enemy.h:GetAttribute("EGGRUMBLE_MarkedUntil")==nil,"HIDDEN_HUMAN_WAS_DEBUFFED")
-- 3 + 4: the authoritative egg carrier is targetable during the same 3 seconds.
session.rules.castles["2"].heldEggs=1
assert(attack()==1 and enemy.h.Health==80,"EGG_CARRIER_INVULNERABILITY")
status()
assert(enemy.h:GetAttribute("EGGRUMBLE_MarkedUntil")==104,"EGG_CARRIER_DEBUFF_BYPASS")
-- 5: dropped or deposited eggs restore the still-active stealth protection.
session.rules.castles["2"].heldEggs=0
enemy.h.Health=100;enemy.h.attrs={}
assert(attack()==0 and enemy.h.Health==100,"RESTORED_STEALTH_FAILED")
-- 6: expiry at the exact time boundary restores ordinary PvP.
clock=103
assert(attack()==1 and enemy.h.Health==80,"STEALTH_EXPIRY_FAILED")
-- 7: TEAM never hits a live same-team ally.
enemy.h.Health=100
session.rules.castles["2"].team="RED"
assert(attack()==0 and enemy.h.Health==100,"FRIENDLY_FIRE_REGRESSION")
session.rules.castles["2"].team="BLUE"
-- 8: map wall LOS still blocks a non-stealthed target.
blocked=true
assert(attack()==0 and enemy.h.Health==100,"WALL_LOS_REGRESSION")
blocked=false
-- 9: BATTLE_ROYALE permits hostile combat with no teams.
session.mode="BATTLE_ROYALE";session.rules.castles["2"].heldEggs=0
assert(attack()==1 and enemy.h.Health==80,"BR_HOSTILE_DUEL_REGRESSION")
-- 10: target outside this session's castle roster cannot be hit.
assert(stranger.h.Health==100,"OTHER_SESSION_TARGETED")
-- 11: fallen castle forbids its owner from dealing damage.
session.rules.castles["1"].alive=false
assert(attack()==0,"FALLEN_CASTLE_ATTACK_REGRESSION")
-- 12: dead target cannot be attacked.
session.rules.castles["1"].alive=true
enemy.h.Health=0
assert(attack()==0,"DEAD_TARGET_ATTACK_REGRESSION")
print("GQ_HUMAN_STEALTH_PVP_REAL_SOURCE_12_CASES_PASS")
'''

def harness(source: str, fixed: bool) -> str:
    begin_hit="local function hitHumanHeroes("
    end_hit="\nlocal function neutralAndBotHit("
    begin_status="local function secondaryEffect("
    end_status="\nlocal function execute("
    helper=HELPER if fixed else ""
    return HARNESS + helper + section(source,begin_hit,end_hit) + "\n" + section(source,begin_status,end_status) + "\n" + TESTS

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--patched",type=Path,required=True)
    ap.add_argument("--fixed-harness",type=Path,required=True)
    ap.add_argument("--original-harness",type=Path,required=True)
    a=ap.parse_args()
    original=AUTHOR.read_bytes()
    assert git_blob(original)==SOURCE_BLOB,"RED: original #482 source drift; stop"
    raw=original.decode("utf-8")
    fixed=patch(raw)
    for dest,text in ((a.patched,fixed),
                      (a.fixed_harness,harness(fixed,True)),
                      (a.original_harness,harness(raw,False))):
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(text,encoding="utf-8")
    assert len(fixed)>len(raw) and raw!=fixed
    print("GQ_HUMAN_STEALTH_SOURCE_EXACT_PATCHED", SOURCE_BLOB,
          "original_author_head",HEAD, "source_scripts_added",0)

if __name__=="__main__":
    main()
