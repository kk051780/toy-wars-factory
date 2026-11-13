#!/usr/bin/env python3
"""Execute the actual new multi-egg server reference rules using native Luau.

Original 5-egg score rules run (not Python copies), plus 10 unsafe actual-source
mutants must fail. This is pure logic, NOT a Roblox-engine or Game.server test.
"""
from __future__ import annotations
import argparse, hashlib, pathlib, re, subprocess, sys, tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
FILE=ROOT/"src/MultiEggScoreRules.luau"
ORIGINAL_GITBLOB="ab35825cfcbf14315eecfae954318b4d92e0a592"
LUAU=r'''
local M=(function()
__ORIGINAL_MULTI_EGG_LUAU_SOURCE__
end)()
local n=0
local function eq(got,want,id)
    n+=1
    if got~=want then
        error("MULTI_ASSERT_"..id.." got="..tostring(got).." want="..tostring(want),0)
    end
end
local function score(s,team) return s.scores[team] end
eq(M.new(0),nil,"bad_zero_epoch")
eq(M.new(0/0),nil,"bad_nan_epoch")
local st=M.new(1)
eq(st.phase,"ACTIVE","initial_active")
eq(st.now,0,"initial_at_zero")
eq(st.eggs.RED_1.owner,"RED","owner_red1")
eq(st.eggs.BLUE_2.owner,"BLUE","owner_blue2")
eq(st.eggs.CENTRE_1.owner,"NEUTRAL","owner_center")
eq(st.eggs.CENTRE_1.place,"NEST","center_starts_nest")
local count=0
for _ in pairs(st.eggs) do count+=1 end
eq(count,5,"five_real_egg_records")
eq(M.addPlayer(st,"r","RED",1),true,"red_join")
eq(M.addPlayer(st,"b","BLUE",1),true,"blue_join")
eq(M.addPlayer(st,"b","RED",1),false,"existing_player_cannot_reteam")
eq(M.addPlayer(st,"evil","INVALID",1),false,"team_spoof_join")
eq(M.addPlayer(st,"x","RED",888),false,"wrong_epoch_join")
eq(M.advance(st,1,20),true,"advance20")
eq(score(st,"RED"),2,"red_two_home_vault_passive20")
eq(score(st,"BLUE"),2,"blue_two_home_vault_passive20")
eq(M.event(st,1,"b",1,"PICK","RED_1",false),false,"remote_pick_no_near_rejected")
eq(M.event(st,1,"b",1,"PICK","RED_1",true),false,"replay_of_failed_seq_rejected")
eq(M.event(st,1,"b",2,"PICK","RED_1",true),true,"enemy_egg_stolen")
eq(st.eggs.RED_1.place,"CARRIED","one_location_carried")
eq(st.eggs.RED_1.holder,"b","enemy_holder")
eq(st.eggs.RED_1.everEnemy,true,"real_enemy_control_logged")
eq(M.event(st,1,"b",3,"PICK","RED_2",true),false,"no_double_carry")
eq(M.event(st,1,"r",1,"PICK","RED_1",true),false,"no_simultaneous_pick")
eq(M.event(st,1,"b",2,"DROP","RED_1",true),false,"stale_action_seq_denied")
eq(M.advance(st,1,30),true,"advance30")
eq(score(st,"BLUE"),3,"enemy_carrier_gets_one_10sec")
eq(score(st,"RED"),2,"red_home_other_egg_not_yet_tick")
eq(M.event(st,1,"b",4,"DEPOSIT","RED_1",true),true,"genuine_enemy_capture")
eq(score(st,"BLUE"),15,"genuine_capture_plus12")
eq(st.eggs.RED_1.vault,"BLUE","actual_foreign_vault")
eq(M.advance(st,1,40),true,"advance40")
eq(score(st,"BLUE"),20,"captured_vault_plus3_per10sec")
eq(score(st,"RED"),3,"owned_red_second_egg_plus1_at40")
eq(M.event(st,1,"b",5,"PICK","RED_1",true),true,"repick_same_captured_egg")
eq(M.event(st,1,"b",6,"DEPOSIT","RED_1",true),true,"legit_redelivery_without_bonus")
eq(score(st,"BLUE"),20,"no_repeat_12pt_capture_farming")
eq(M.event(st,1,"r",2,"PICK","RED_1",true),true,"recover_stolen_red_egg")
eq(M.event(st,1,"r",3,"DEPOSIT","RED_1",true),true,"recover_to_own_vault")
eq(score(st,"RED"),5,"actual_2pt_recapture_bonus")
eq(M.event(st,1,"r",4,"PICK","RED_1",true),true,"repick_own_after_recovery")
eq(M.event(st,1,"r",5,"DEPOSIT","RED_1",true),true,"own_redeposit_legal")
eq(score(st,"RED"),5,"cannot_farm_own_recapture_bonus")
eq(M.event(st,1,"r",6,"PICK","RED_2",true),true,"carry_own_egg_defensively")
eq(M.event(st,1,"r",7,"PICK","BLUE_1",true),false,"own_egg_carrier_cannot_steal_more")
eq(M.event(st,1,"r",6,"DROP","RED_2",true),false,"old_seq_no_replay")
eq(M.advance(st,1,70),true,"advance_30_more_seconds")
eq(score(st,"RED"),7,"own_egg_carry_awards_one_per30")
eq(M.removePlayer(st,888,"r"),false,"wrong_epoch_cannot_drop")
eq(M.removePlayer(st,1,"r"),true,"disconnect_drops_owned_egg")
eq(st.eggs.RED_2.place,"DROPPED","egg_not_deleted_on_disconnect")
eq(st.eggs.RED_2.holder,nil,"no_ghost_owner_after_disconnect")
eq(M.event(st,1,"r",8,"PICK","RED_2",true),false,"dead_player_cannot_pick")
eq(M.respawnPlayer(st,1,"r"),true,"allow_server_respawn")
eq(M.event(st,1,"b",7,"PICK","RED_2",true),true,"other_team_can_claim_dropped_egg")
eq(M.event(st,1,"r",8,"PICK","RED_2",true),false,"cannot_duplicate_one_egg")
eq(M.event(st,1,"b",8,"DROP","RED_2",false),true,"carrier_may_drop_without_vault")
eq(M.event(st,1,"r",9,"PICK","RED_2",true),true,"owner_can_recapture_dropped")
eq(M.event(st,1,"r",10,"DEPOSIT","RED_2",true),true,"red2_recovery")
eq(score(st,"RED"),9,"red2_genuine_recapture_bonus_once")
eq(M.event(st,1,"r",11,"PICK","RED_2",true),true,"red2_repicked")
eq(M.event(st,1,"r",12,"DEPOSIT","RED_2",true),true,"red2_redeposited")
eq(score(st,"RED"),9,"red2_recovery_not_repeat_paid")
local neutral=M.new(5)
eq(M.addPlayer(neutral,"r","RED",5),true,"neutral_r_join")
eq(M.event(neutral,5,"r",1,"PICK","CENTRE_1",true),true,"neutral_pick")
eq(M.advance(neutral,5,10),true,"neutral_carry10")
eq(score(neutral,"RED"),1,"neutral_carrier_one_per10")
eq(M.event(neutral,5,"r",2,"DEPOSIT","CENTRE_1",true),true,"first_neutral_vault")
eq(score(neutral,"RED"),11,"neutral_first_capture_plus10")
eq(M.advance(neutral,5,20),true,"neutral_vault10")
eq(score(neutral,"RED"),15,"two_home_owned_eggs_plus1_each_and_neutral_vault_plus2")
eq(M.event(neutral,5,"r",3,"PICK","CENTRE_1",true),true,"neutral_repick")
eq(M.event(neutral,5,"r",4,"DEPOSIT","CENTRE_1",false),false,"fake_near_vault_denied")
eq(M.event(neutral,5,"r",5,"DEPOSIT","CENTRE_1",true),true,"second_neutral_delivery")
eq(score(neutral,"RED"),15,"neutral_capture_once_no_farm")
local enemy=M.new(6)
eq(M.addPlayer(enemy,"r","RED",6),true,"enemy_r_join")
eq(M.event(enemy,6,"r",1,"PICK","BLUE_1",true),true,"enemy_pick")
eq(M.advance(enemy,6,10),true,"enemy_ten_seconds")
eq(score(enemy,"RED"),1,"enemy_hold_one_per10")
eq(M.event(enemy,6,"r",2,"DEPOSIT","BLUE_1",true),true,"enemy_deposit")
eq(score(enemy,"RED"),13,"enemy_capture_twelve_bonus")
eq(M.advance(enemy,6,20),true,"enemy_vault_20")
eq(score(enemy,"RED"),18,"two_own_at20_plus_foreign_vault3")
eq(M.event(enemy,6,"r",3,"DEPOSIT","BLUE_1",true),false,"deposit_without_carry_denied")
eq(score(enemy,"RED"),18,"no_post_deposit_double_score")
local overtime=M.new(2)
eq(M.addPlayer(overtime,"r","RED",2),true,"ot_red_join")
eq(M.addPlayer(overtime,"b","BLUE",2),true,"ot_blue_join")
eq(M.advance(overtime,2,240),true,"four_minute_regulation")
eq(score(overtime,"RED"),24,"home_scores_equal24")
eq(score(overtime,"BLUE"),24,"home_scores_symmetric")
eq(overtime.phase,"OVERTIME","tie_enters_overtime")
eq(overtime.eggs.CENTRE_1.place,"NEST","central_egg_reset_for_golden")
eq(M.event(overtime,2,"r",1,"PICK","RED_1",true),false,"overtime_home_egg_not_pickable")
eq(M.event(overtime,2,"r",2,"PICK","CENTRE_1",true),true,"new_overtime_neutral_acquisition")
eq(M.event(overtime,2,"r",3,"DEPOSIT","CENTRE_1",true),true,"golden_center_decides_winner")
eq(overtime.phase,"FINISHED","golden_time_ended")
eq(overtime.winner,"RED","red_won_golden")
eq(overtime.finishReason,"GOLDEN_CENTRE","golden_reason")
eq(M.advance(overtime,2,241),false,"never_score_after_win")
eq(M.event(overtime,2,"r",4,"PICK","CENTRE_1",true),false,"no_post_game_replay")
local draw=M.new(3)
eq(M.advance(draw,3,270),true,"draw_overtime_270")
eq(draw.phase,"FINISHED","overtime_draw_finished")
eq(draw.winner,"DRAW","true_draw_not_fake_winner")
eq(draw.finishReason,"OVERTIME_DRAW","true_draw_reason")
eq(M.advance(draw,3,271),false,"no_overtime_second_win")
local winner=M.new(4)
eq(M.addPlayer(winner,"r","RED",4),true,"winner_r_join")
eq(M.addPlayer(winner,"b","BLUE",4),true,"winner_b_join")
eq(M.event(winner,4,"r",1,"PICK","BLUE_1",true),true,"winner_enemy_pick")
eq(M.event(winner,4,"r",2,"DEPOSIT","BLUE_1",true),true,"winner_early_capture")
eq(M.advance(winner,4,240),true,"winner_regulation_finish")
eq(winner.phase,"FINISHED","not_overtime_if_scores_differ")
eq(winner.winner,"RED","red_regulation_winner")
eq(winner.finishReason,"REGULATION","regular_win_reason")
eq(M.advance(winner,4,250),false,"cannot_add_passive_after_end")
eq(M.event(winner,4,"r",3,"PICK","BLUE_2",true),false,"finished_game_no_new_pick")
eq(M.event(winner,5,"r",4,"PICK","BLUE_2",true),false,"old_epoch_refuses_wrong_game")
eq(M.advance(winner,5,250),false,"cross_epoch_time_spoof_rejected")
eq(M.advance(M.new(8),8,0/0),false,"nan_clock_refused")
eq(M.advance(M.new(8),8,-1),false,"negative_clock_refused")
eq(M.event(st,1,"r",13,"PICK","FOREVER_FAKE_EGG",true),false,"fake_egg_id_refused")
eq(M.event(st,1,"r",14,"PICK","RED_1","true"),false,"fake_near_type_refused")
eq(M.event(st,1,"r",15,"PICK","RED_1",true),true,"valid_seq_after_bad_action")
eq(M.event(st,1,"r",15,"DROP","RED_1",true),false,"stale_valid_seq_does_not_repeat")
if n<92 then error("MULTI_NATIVE_TOO_FEW_ASSERTIONS_"..tostring(n),0) end
print("P0D_MULTI_EGG_REAL_LUAU_POLICY_PASS_"..tostring(n))
'''
MUTANTS=[
 ("epoch_cross_match",'state.epoch == epoch','state.epoch ~= epoch'),
 ("replay_nonmonotonic",'seq<=player.seq','false'),
 ("remote_pickup_without_distance",'if trustedNear~=true or player.carrying~=nil then','if false or player.carrying~=nil then'),
 ("double_carry",'player.carrying~=nil then return false end','false then return false end'),
 ("capture_farm",'egg.capturePaid[team]~=true','true'),
 ("enemy_vault_inflated",'return team,10,3','return team,10,30'),
 ("own_carry_inflated",'return carrier.team,30,1','return carrier.team,10,1'),
 ("post_game_advance",'if state.phase=="FINISHED" then return false end','if false then return false end'),
 ("stale_overtime_center",'changeEgg(egg,"NEST",nil,nil)','changeEgg(egg,"DROPPED",nil,nil)'),
 ("disconnect_no_drop",'if egg and egg.holder==id then','if false then'),
]
def gitblob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def run(luau:pathlib.Path,source:str):
    with tempfile.TemporaryDirectory(prefix="p0d_real_multi_egg_native_") as tmp:
        f=pathlib.Path(tmp)/"genuine_multi_egg_luau_run.luau"
        f.write_text(LUAU.replace("__ORIGINAL_MULTI_EGG_LUAU_SOURCE__",source),encoding="utf-8")
        p=subprocess.run([str(luau),str(f)],capture_output=True,text=True,timeout=35)
        return p.returncode,p.stdout+p.stderr
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--luau",required=True,type=pathlib.Path)
    parser.add_argument("--build-test",type=pathlib.Path)
    args=parser.parse_args()
    raw=FILE.read_bytes()
    if gitblob(raw)!=ORIGINAL_GITBLOB:
        raise RuntimeError("ORIGINAL_MULTI_EGG_SOURCE_CHANGED")
    source=raw.decode("utf-8")
    if args.build_test:
        args.build_test.write_text(LUAU.replace("__ORIGINAL_MULTI_EGG_LUAU_SOURCE__",source),encoding="utf-8")
    code,out=run(args.luau,source)
    match=re.search(r"P0D_MULTI_EGG_REAL_LUAU_POLICY_PASS_(\d+)",out)
    if code or not match or int(match.group(1))<92:
        raise RuntimeError("GENUINE_MULTI_EGG_NATIVE_LUAU_REJECTED "+out[-2000:])
    print(match.group(0))
    count=0
    for title,old,new in MUTANTS:
        if source.count(old)!=1:
            raise RuntimeError("AMBIGUOUS_MUTANT_"+title+"_"+str(source.count(old)))
        code,log=run(args.luau,source.replace(old,new,1))
        if code==0 or "MULTI_ASSERT_" not in log:
            raise RuntimeError("UNSAFE_SOURCE_MUTATION_SURVIVED_"+title+" "+log[-1000:])
        count+=1
        print("P0D_MULTI_EGG_UNSAFE_MUTANT_REJECTED "+title)
    print("P0D_MULTI_EGG_NATIVE_MUTANTS_PASS_"+str(count))
    print("P0D_MULTI_EGG_ACTUAL_S1_GAME_INTEGRATION_STUDIO_2CLIENT_MOBILE_FUN_NOT_TESTED")
if __name__=="__main__":
    try:main()
    except (OSError,RuntimeError,AssertionError,subprocess.TimeoutExpired) as exc:
        print("P0D_MULTI_EGG_NATIVE_BLOCKED "+str(exc),file=sys.stderr)
        sys.exit(1)
