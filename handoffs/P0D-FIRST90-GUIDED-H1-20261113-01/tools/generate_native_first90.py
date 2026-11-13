#!/usr/bin/env python3
"""Pure original Luau FIRST90 policy execution; no engine and no fake user test."""
from pathlib import Path
import argparse,hashlib
root=Path(__file__).resolve().parents[1]
body=(root/"inputs/First90GuideRules.luau").read_text("utf8")
b=body.encode("utf8")
assert hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()=="644073946930d63e6b06c20ca249739b9ecfa5ad"
assert body.rstrip().endswith("return Guide")
TEST=r"""
local n=0
local function ok(condition,name)
 n+=1
 assert(condition,"FIRST90_FAIL: "..name)
end
local Guide=P
local state=Guide.newRound(7)
local def={mode="CLASSIC",eliteWarning=0,carrying=false,
 bound=false,rescueNearby=false,scoutReady=true}
ok(Guide.newRound(0)==nil,"no_zero_epoch")
ok(Guide.newRound(7.5)==nil,"no_fraction_epoch")
ok(Guide.newRound("7")==nil,"no_text_epoch")
ok(state~=nil and state.hit==false and state.pickup==false,"valid_new")
local function v(t,s,d) return Guide.view("ACTIVE",t,s or state,d or def) end
ok(Guide.view("LOBBY",0,state,def).visible==false,"no_lobby_guide")
ok(Guide.view("RESULTS",0,state,def).visible==false,"no_result_guide")
ok(Guide.view("ACTIVE",-1,state,def).visible==false,"no_negative_seconds")
ok(Guide.view("ACTIVE",0,nil,def).visible==false,"no_fake_missing_state")
ok(v(0).step=="ATTACK","begin_with_satisfying_attack")
ok(v(23).step=="ATTACK","attack_23")
ok(v(24).step=="PICKUP","attack_fallback_24")
ok(v(59).step=="PICKUP","pickup_before_60")
ok(v(60).step=="SCOUT","scout_after60_not_stuck")
ok(v(89).step=="FREE","last_second")
ok(v(90).visible==false,"zero_after_90")
ok(v(91).visible==false,"never_reappear")
ok(v(12).seconds==78,"correct_counter")
ok(Guide.mark(state,7,"HIT",false)==false,"client_hit_cannot_certify")
ok(Guide.mark(state,8,"HIT",true)==false,"old_round_not_applied")
ok(Guide.mark(state,7,"KILL",true)==false,"mob_kill_not_reward")
ok(state.hit==false,"spoofs_cannot_progress")
ok(Guide.mark(state,7,"HIT",true)==true,"server_real_hit")
ok(Guide.mark(state,7,"HIT",true)==false,"hit_dedup")
ok(v(10).step=="PICKUP","hit_progresses_to_egg")
local carried={mode="CLASSIC",carrying=true,eliteWarning=0,bound=false,
 rescueNearby=false,scoutReady=true}
ok(v(11,nil,carried).step=="RETURN","carry_overrides_attack")
ok(string.find(v(11,nil,carried).text,"自陣",1,true)~=nil,"real_team_return")
local five={mode="SCORE_5",carrying=true,eliteWarning=0,bound=false,
 rescueNearby=false,scoutReady=true}
ok(v(11,nil,five).step=="RETURN","five_egg_return")
ok(string.find(v(11,nil,five).text,"金庫",1,true)~=nil,"five_egg_correct_deposit")
local danger={mode="CLASSIC",carrying=true,eliteWarning=1.5,bound=false,
 rescueNearby=false,scoutReady=true}
ok(v(11,nil,danger).step=="DODGE","elite_danger_preempts_carry")
danger.eliteWarning=0.01
ok(v(11,nil,danger).step=="DODGE","subsecond_boss_danger")
danger.eliteWarning=100
ok(v(11,nil,danger).step=="RETURN","invalid_warning_cannot_spoof")
local trapped={mode="CLASSIC",carrying=false,eliteWarning=0,bound=true,
 rescueNearby=true,scoutReady=true}
ok(v(30,nil,trapped).step=="BREAK","break_preempts_rescue")
trapped.bound=false
ok(v(30,nil,trapped).step=="RESCUE","help_preempts_egg")
ok(Guide.mark(state,7,"PICKUP",true)==true,"actual_server_pickup")
ok(Guide.mark(state,7,"PICKUP",true)==false,"pickup_replay")
ok(v(35).step=="SCORE","after_pickup_remind_delivery")
ok(Guide.mark(state,7,"DEPOSIT",true)==true,"actual_server_deposit")
ok(v(40).step=="SCOUT","summon_after_delivering")
ok(Guide.mark(state,7,"SCOUT",true)==true,"real_scout_active")
ok(v(50).step=="FREE","after_scout_free_choice")
ok(Guide.mark(state,8,"DEPOSIT",true)==false,"future_round_spoof")
ok(Guide.mark(state,7,"EQUIP_USE",true)==false,"different_not_milestone")
local empty={mode="CLASSIC",carrying=false,eliteWarning=0,bound=false,
 rescueNearby=false,scoutReady=false}
local state2=Guide.newRound(8)
ok(Guide.view("ACTIVE",60,state2,empty).step=="FREE","unavailable_scout_not_stuck")
ok(Guide.view("ACTIVE",20,state2,{mode="WRONG"}).visible==false,"reject_unknown_mode")
ok(Guide.view("ACTIVE",20,state2,def).seconds==70,"new_round_counter")
ok(Guide.view("ACTIVE",90,state2,def).step=="HIDDEN","strict_90_exit")
ok(Guide.mark(state2,7,"HIT",true)==false,"cross_epoch")
print("P0D_FIRST90_NATIVE_"..tostring(n).."_ASSERTIONS_PASS")
"""
content="local P=(function()\n"+body+"\nend)()\n"+TEST
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--write",required=True);args=a.parse_args()
 Path(args.write).write_text(content,"utf8")
 print("FIRST90_POLICY_NATIVE_DRIVER_READY")
