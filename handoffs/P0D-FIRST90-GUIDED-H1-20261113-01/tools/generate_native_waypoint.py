#!/usr/bin/env python3
"""Run the actual pure server-directed first90 waypoint selector in native Luau."""
from pathlib import Path
import argparse,hashlib
root=Path(__file__).resolve().parents[1]
raw=(root/"inputs/First90WaypointRules.luau").read_bytes()
sha=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
assert sha=="69c81d82eac5189d34eed801099ab52b559f2b52",(sha,"WaypointRules source drift")
TEST=r"""
local n=0
local function ck(v,name) n+=1;assert(v,"WAYPOINT_FAIL "..name) end
local nav=P
local at={x=-105,y=3,z=0}
local padR={x=-105,y=3,z=10}
local padB={x=105,y=3,z=10}
local eggs={
 {id="R1",owner="RED",x=-100,y=2,z=0,available=true},
 {id="B1",owner="BLUE",x=100,y=2,z=0,available=true},
 {id="N1",owner="NEUTRAL",x=0,y=3,z=0,available=true},
 {id="B2",owner="BLUE",x=102,y=2,z=22,available=false},
}
local function test(phase,elapsed,team,mode,step,origin,pad,items)
 return nav.select(phase,elapsed,team,mode,step,origin,pad,items)
end
local function g(mode,step,items)
 return test("ACTIVE",20,"RED",mode,step,at,padR,items or eggs)
end
ck(g("CLASSIC","PICKUP").x==100,"classic_enemy_egg_only")
ck(g("CLASSIC","PICKUP").kind=="EGG","classic_kind")
ck(g("SCORE_5","PICKUP").x==0,"five_neutral_nearest")
ck(g("SCORE_5","PICKUP").kind=="EGG","five_kind")
ck(g("CLASSIC","RETURN").x==-105,"classic_home")
ck(g("SCORE_5","RETURN").kind=="HOME","five_home")
ck(g("SCORE_5","RETURN").z==10,"five_pad_home")
ck(g("CLASSIC","SCORE")==nil,"never_score_without_carried_egg")
ck(g("CLASSIC","DODGE")==nil,"boss_preempts_waypoint")
ck(g("CLASSIC","BREAK")==nil,"bound_preempts_waypoint")
ck(g("CLASSIC","RESCUE")==nil,"rescue_preempts_waypoint")
ck(test("LOBBY",0,"RED","CLASSIC","PICKUP",at,padR,eggs)==nil,"no_lobby")
ck(test("RESULTS",10,"RED","CLASSIC","PICKUP",at,padR,eggs)==nil,"no_results")
ck(test("ACTIVE",89.9,"RED","CLASSIC","PICKUP",at,padR,eggs)~=nil,"before_90")
ck(test("ACTIVE",90,"RED","CLASSIC","PICKUP",at,padR,eggs)==nil,"strict90")
ck(test("ACTIVE",91,"RED","CLASSIC","PICKUP",at,padR,eggs)==nil,"after90")
ck(test("ACTIVE",-1,"RED","CLASSIC","PICKUP",at,padR,eggs)==nil,"negative_time")
ck(test("ACTIVE",0,"NONE","CLASSIC","PICKUP",at,padR,eggs)==nil,"no_unassigned_team")
ck(test("ACTIVE",0,"GREEN","CLASSIC","PICKUP",at,padR,eggs)==nil,"no_unknown_team")
ck(test("ACTIVE",0,"RED","UNKNOWN","PICKUP",at,padR,eggs)==nil,"unknown_mode")
ck(test("ACTIVE",0,"RED","CLASSIC","PICKUP",nil,padR,eggs)==nil,"missing_origin")
ck(test("ACTIVE",0,"RED","CLASSIC","PICKUP",{x=999,y=2,z=0},padR,eggs)==nil,"off_map_origin")
ck(test("ACTIVE",0,"RED","CLASSIC","RETURN",at,nil,eggs)==nil,"missing_pad")
ck(test("ACTIVE",0,"RED","CLASSIC","RETURN",at,{x=999,y=3,z=0},eggs)==nil,"invalid_pad")
ck(test("ACTIVE",0,"RED","CLASSIC","PICKUP",at,padR,nil)==nil,"missing_eggs")
ck(test("ACTIVE",0,"RED","CLASSIC","PICKUP",at,padR,{})==nil,"no_eggs")
ck(g("CLASSIC","PICKUP",{{id="B1",owner="BLUE",x=100,y=2,z=0,available=false}})==nil,"stolen_enemy_no_ghost_target")
ck(g("CLASSIC","PICKUP",{{id="N1",owner="NEUTRAL",x=0,y=3,z=0,available=true}})==nil,"classic_not_neutral")
ck(g("SCORE_5","PICKUP",{{id="R1",owner="RED",x=-100,y=3,z=0,available=true}})==nil,"five_never_own_egg")
ck(g("SCORE_5","PICKUP",{{id="N1",owner="NEUTRAL",x=0,y=3,z=0,available=true}}).x==0,"neutral_permitted")
ck(g("SCORE_5","PICKUP",{{id="B1",owner="BLUE",x=100,y=3,z=0,available=true}}).x==100,"opponent_permitted")
ck(g("SCORE_5","PICKUP",{{id="EvilLongName",owner="BLUE",x=100,y=3,z=0,available=true}})==nil,"invalid_long_id")
ck(g("SCORE_5","PICKUP",{{id="N1",owner="NEUTRAL",x=0/0,y=3,z=0,available=true}})==nil,"reject_nan_goal")
ck(g("SCORE_5","PICKUP",{{id="N1",owner="NEUTRAL",x=500,y=3,z=0,available=true}})==nil,"off_map_goal")
local equal={
 {id="B2",owner="BLUE",x=100,y=2,z=0,available=true},
 {id="B1",owner="BLUE",x=100,y=2,z=0,available=true},
}
ck(g("CLASSIC","PICKUP",equal).x==100,"equal_nearest_deterministic")
local behind=nav.select("ACTIVE",1,"BLUE","CLASSIC","PICKUP",
 {x=106,y=3,z=0},padB,eggs)
ck(behind and behind.x==-100,"blue_targets_red")
ck(nav.select("ACTIVE",89,"BLUE","SCORE_5","RETURN",
 {x=106,y=3,z=0},padB,eggs).x==105,"blue_home")
local tooMany={
 {id="R1",owner="RED",x=-100,y=2,z=0,available=false},
 {id="R2",owner="RED",x=-98,y=2,z=0,available=false},
 {id="B1",owner="BLUE",x=100,y=2,z=0,available=false},
 {id="B2",owner="BLUE",x=100,y=2,z=20,available=false},
 {id="N1",owner="NEUTRAL",x=0,y=2,z=0,available=false},
 {id="B3",owner="BLUE",x=20,y=2,z=0,available=true},
}
ck(g("SCORE_5","PICKUP",tooMany)==nil,"no_sixth_egg_injection")
ck(nav.WINDOW==90,"window_constant")
print("P0D_FIRST90_WAYPOINT_NATIVE_"..tostring(n).."_ASSERTIONS_PASS")
"""
code="local P=(function()\n"+raw.decode("utf8")+"\nend)()\n"+TEST
if __name__=="__main__":
 arg=argparse.ArgumentParser();arg.add_argument("--write",required=True)
 p=arg.parse_args()
 Path(p.write).write_text(code,"utf8")
 print("P0D_FIRST90_WAYPOINT_NATIVE_DRIVER_READY")
