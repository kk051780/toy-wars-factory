#!/usr/bin/env python3
"""Generate a standalone GENUINE native Luau runtime test program from actual assembled H1 modules.
This test cannot simulate Roblox Workspace/Studio; it executes unchanged pure Luau policy sources.
"""
from __future__ import annotations
import argparse, hashlib, pathlib

HERE=pathlib.Path(__file__).resolve()
REPO=HERE.parents[3]
SRC=REPO/"handoffs/P0D-H1-WOW-4WAY-20261113-01/dist/TRAP_RAIDERS_H1_WOW_STUDIO_ONLY/src"
MODULES={
    "Wind":("server/S1RaiderWindRules.luau","7d5706774b874759e7ab994dc0654c3ae9a46502"),
    "Trap":("server/S1TrapRules.luau","feabd705e4cfa5483d440e506277080f226343ef"),
    "Guide":("client/D18MascotGuideRules.luau","328b8a4d70261e633f163a5e166822a29d7eb1ba"),
}
def gitblob(b):
    return hashlib.sha1(b"blob "+str(len(b)).encode("ascii")+b"\0"+b).hexdigest()

PURE_HARNESS=r'''
local checked = 0
local function yes(condition, label)
    checked += 1
    assert(condition, "NATIVE_POLICY_CHECK_FAIL: " .. label)
end
local function copy(t)
    local result = {}
    for k,v in pairs(t) do result[k] = v end
    return result
end
local function wind_test(team, key, val, expected, label)
    local s = {phase="ACTIVE",team=team,role="RAIDER",alive=true,
         carrying=false,slowed=false,active=false,
         now=80,lastAt=-math.huge,x=0,y=5,z=0}
    if key then s[key]=val end
    yes(Wind.canActivate(s)==expected, "WIND_"..label)
end
for _,team in ipairs({"RED","BLUE"}) do
    wind_test(team,nil,nil,true,team.."_valid_start")
    wind_test(team,"role","GUARDIAN",false,team.."_guardian")
    wind_test(team,"carrying",true,false,team.."_egg_carrier")
    wind_test(team,"slowed",true,false,team.."_guardian_trap_slow")
    wind_test(team,"active",true,false,team.."_already_active")
    wind_test(team,"phase","LOBBY",false,team.."_out_of_round")
    wind_test(team,"alive",false,false,team.."_dead")
    wind_test(team,"now",82,true,team.."_valid_time")
    wind_test(team,"lastAt",70,false,team.."_cooldown")
    wind_test(team,"lastAt",62,true,team.."_exact_cooldown")
    wind_test(team,"x",121,false,team.."_X_bound")
    wind_test(team,"z",66,false,team.."_Z_bound")
    wind_test(team,"y",0,false,team.."_falling")
    wind_test(team,"y",13,false,team.."_sky_speed_abuse")
    wind_test(team,"x",math.huge,false,team.."_infinite_position")
    wind_test(team,"role","INVALID",false,team.."_bad_role")
end
local standard = {phase="ACTIVE",team="RED",role="GUARDIAN",
    alive=true,carrying=false,now=80,lastAt=-math.huge,
    x=-45,y=5,z=0,count=0,avoid={{x=-100,z=-20}}}
local function trap_test(key,val,expected,label)
    local s=copy(standard)
    if key then s[key]=val end
    yes(Trap.canPlace(s)==expected, "TRAP_"..label)
end
trap_test(nil,nil,true,"guardian_ground")
trap_test("team","BLUE",false,"other_side")
trap_test("role","RAIDER",false,"raider_cannot_place")
trap_test("carrying",true,false,"carrying_cannot_place")
trap_test("phase","RESULTS",false,"outside_round")
trap_test("alive",false,false,"dead")
trap_test("now",82,true,"valid_time")
trap_test("lastAt",70,false,"cooldown")
trap_test("lastAt",60,true,"exact_cooldown")
trap_test("y",12,false,"on_sky_bridge")
trap_test("y",1,false,"underground")
trap_test("x",0,false,"middle_not_owned")
trap_test("z",60,false,"outer_Z")
trap_test("count",2,false,"team_trap_cap")
trap_test("count",1.3,false,"fractional_count")
trap_test("avoid",{{x=-45,z=0}},false,"near_objective")
local contact = {phase="ACTIVE",healthy=true,trapTeam="RED",enemyTeam="BLUE",
    invulnerable=false,now=80,expiresAt=100,
    x=-45,z=0,enemyX=-45,enemyY=5,enemyZ=3}
local function trigger(key,val,expected,label)
    local s=copy(contact)
    if key then s[key]=val end
    yes(Trap.shouldTrigger(s)==expected,"TRAP_TRIGGER_"..label)
end
trigger(nil,nil,true,"opponent")
trigger("enemyTeam","RED",false,"friendly_fire")
trigger("invulnerable",true,false,"invulnerability")
trigger("enemyY",10,false,"sky_walker")
trigger("enemyZ",20,false,"distant")
trigger("now",100,false,"expired")
trigger("phase","LOBBY",false,"not_active")
yes(Trap.slowSpeed(19)==10,"TRAP_RAIDER_SLOWED_TO10")
yes(Trap.slowSpeed(15)==8,"TRAP_GUARDIAN_SLOWED_TO8")
-- A Guardian trap is a policy-level counter to Raider wind.
local s=copy(standard)
s.role="RAIDER";s.team="BLUE";s.x=0
yes(not Trap.canPlace(s),"CROSS_RAIDER_CANNOT_PLACE_GUARDIAN_TRAP")
local sprint={phase="ACTIVE",team="BLUE",role="RAIDER",alive=true,
    carrying=false,slowed=false,active=false,now=80,lastAt=-math.huge,
    x=0,y=5,z=0}
yes(Wind.canActivate(sprint),"CROSS_RAIDER_ELIGIBLE")
sprint.slowed=true
yes(not Wind.canActivate(sprint),"CROSS_TRAP_CANCELS_FUTURE_WIND")
sprint.slowed=false;sprint.carrying=true
yes(not Wind.canActivate(sprint),"CROSS_EGG_BLOCKS_FUTURE_WIND")
local function snapshot(team,egg,serial,updateId)
    return {kind="SNAPSHOT",team=team,phase="ACTIVE",
         carrying=egg,serial=serial,updateId=updateId}
end
local red=Guide.accept(snapshot("RED","",1,1),-1,-1)
yes(red~=nil and red.destinationTeam=="BLUE" and red.partName=="BLUE_EGG","GUIDE_RED_ENEMY_EGG")
local blu=Guide.accept(snapshot("BLUE","",1,1),-1,-1)
yes(blu~=nil and blu.destinationTeam=="RED" and blu.partName=="RED_EGG","GUIDE_BLUE_ENEMY_EGG")
local carrier=Guide.accept(snapshot("RED","BLUE",1,2),1,1)
yes(carrier~=nil and carrier.carrying and carrier.destinationTeam=="RED" and
    carrier.partName=="RED_SCORE_PAD","GUIDE_CARRY_REAL_OWN_PAD")
local carrier2=Guide.accept(snapshot("BLUE","RED",1,2),1,1)
yes(carrier2~=nil and carrier2.destinationTeam=="BLUE" and
    carrier2.partName=="BLUE_SCORE_PAD","GUIDE_BLUE_CARRIER")
yes(Guide.accept(snapshot("RED","",1,1),1,1)==nil,"GUIDE_REPLAY_REJECTED")
yes(Guide.accept(snapshot("RED","",0,10),1,1)==nil,"GUIDE_OLD_ROUND_REJECTED")
local x=snapshot("RED","",1,3);x.kind="BOSS_EVENT"
yes(Guide.accept(x,1,2)==nil,"GUIDE_BOSS_INJECTION_REJECTED")
x=snapshot("RED","",1,3);x.carrying={}
yes(Guide.accept(x,1,2)==nil,"GUIDE_BAD_CARRY_TYPE")
x=snapshot("RED","",1,3);x.team="NEITHER"
yes(Guide.accept(x,1,2)==nil,"GUIDE_BAD_TEAM")
x=snapshot("RED","",1,3);x.phase="CHEAT"
yes(Guide.accept(x,1,2)==nil,"GUIDE_BAD_PHASE")
x=snapshot("RED","",1,3);x.updateId=2
yes(Guide.accept(x,1,2)==nil,"GUIDE_DUPLICATE_UPDATE")
x=snapshot("RED","",1,3);x.updateId="3"
yes(Guide.accept(x,1,2)==nil,"GUIDE_BAD_UPDATE")
x=snapshot("RED","",1,3);x.serial=math.huge
yes(Guide.accept(x,1,2)==nil,"GUIDE_INF_SERIAL")
x=snapshot("RED","",1,3);x.updateId=nil
yes(Guide.accept(x,1,2)==nil,"GUIDE_DOWNGRADE_REJECTED")
x=snapshot("RED","",1,3);x.serial=2
yes(Guide.accept(x,1,2)~=nil,"GUIDE_NEW_ROUND_ALLOW")
print("P0D_H1_INDEPENDENT_GENUINE_LUAU_POLICY_RUNTIME_PASS_" .. tostring(checked))
'''

def build(output):
    chunks=[]
    for name,(path,expected) in MODULES.items():
        p=SRC/path
        b=p.read_bytes()
        actual=gitblob(b)
        assert actual==expected,(name,actual,expected)
        source=b.decode("utf-8")
        chunks.append("local "+name+" = (function()\n"+source+"\nend)()\n")
    chunks.append(PURE_HARNESS)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text("\n".join(chunks),encoding="utf-8")
    print("H1_EXACT_3_SOURCE_MODULES_NATIVE_LUAU_RUNTIME_HARNESS",output)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--write",required=True,type=pathlib.Path)
    args=parser.parse_args()
    build(args.write)
