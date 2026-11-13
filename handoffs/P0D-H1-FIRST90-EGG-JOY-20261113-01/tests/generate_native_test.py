#!/usr/bin/env python3
"""Generate native Luau execution tests from the EXACT original pure Rules file."""
from pathlib import Path
import argparse
OWN=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument("--write",required=True)
a=p.parse_args()
rules=(OWN/"client/EggJoyRules.luau").read_text(encoding="utf8")
test=String=None
test='local Rules = (function()\n'+rules+'\nend)()\n'+r'''
local count = 0
local function check(ok, message)
    if not ok then error(message) end
    count += 1
end
local function snap(serial, update, phase, team, red, blue, egg, winner)
    return {kind = "SNAPSHOT", serial = serial, updateId = update,
        phase = phase, team = team, scores = {RED = red, BLUE = blue},
        carrying = egg, winner = winner}
end
local last = nil
local function step(payload, expected, label)
    local nextState, actual = Rules.accept(last, payload)
    check(actual == expected, label .. " got=" .. tostring(actual))
    last = nextState
end
-- RED first match, no false onboarding celebration on first snapshot.
step(snap(1,1,"ACTIVE","RED",0,0,"",""),nil,"initial")
step(snap(1,1,"ACTIVE","RED",0,0,"BLUE",""),nil,"stale_id")
check(last.carrying=="","stale_not_committed")
step(snap(1,2,"ACTIVE","RED",0,0,"BLUE",""),"PICKUP","red_picks_enemy")
step(snap(1,2,"ACTIVE","RED",0,0,"BLUE",""),nil,"repeat")
step(snap(1,3,"ACTIVE","RED",1,0,"",""),"TEAM_SCORE","red_scores")
step(snap(1,4,"ACTIVE","RED",1,1,"",""),nil,"enemy_scores_no_credit")
step(snap(1,5,"RESULTS","RED",1,1,"","RED"),"VICTORY","red_win")
step(snap(1,6,"RESULTS","RED",1,1,"","RED"),nil,"results_repeat")
step(snap(2,7,"ACTIVE","RED",0,0,"",""),nil,"new_round_no_fake")
step(snap(2,8,"ACTIVE","RED",0,0,"BLUE",""),"PICKUP","second_round_new_pick")
step(snap(2,9,"ACTIVE","RED",1,0,"",""),"TEAM_SCORE","second_score")
step(snap(2,10,"COUNTDOWN","RED",1,0,"",""),nil,"round_paused")
step(snap(2,11,"ACTIVE","BLUE",1,0,"",""),nil,"team_change_rebase")
step(snap(3,12,"ACTIVE","BLUE",0,0,"",""),nil,"blue_new_game")
step(snap(3,13,"ACTIVE","BLUE",0,0,"RED",""),"PICKUP","blue_picks_red")
step(snap(3,14,"ACTIVE","BLUE",0,1,"",""),"TEAM_SCORE","blue_team")
step(snap(3,15,"RESULTS","BLUE",0,1,"","DRAW"),nil,"draw_not_win")
step(snap(4,16,"ACTIVE","RED",0,0,"",""),nil,"red_match_4")
step(snap(3,17,"ACTIVE","RED",0,0,"BLUE",""),nil,"older_serial")
check(last.serial==4,"no_old_serial_rollback")
step({kind="FAKE"},nil,"missing_fields")
step(snap(4,-1,"ACTIVE","RED",0,0,"BLUE",""),nil,"negative_update")
step(snap(4,17,"ACTIVE","RED",0,0,"RED",""),nil,"cannot_carry_own_egg")
step(snap(4,17,"ACTIVE","RED",2,0,"",""),"TEAM_SCORE","score_advance")
step(snap(4,18,"ACTIVE","RED",1,0,"",""),nil,"score_rollback_rejected")
check(last.updateId==17,"rollback_not_committed")
step(snap(4,18,"ACTIVE","RED",2,0,"",""),nil,"corrected_same_score")
step(snap(4,19,"ACTIVE","RED",2,1,"",""),nil,"enemy_score_again")
step(snap(4,20,"RESULTS","RED",2,1,"","BLUE"),nil,"lose_no_victory")
step(snap(5,21,"LOBBY","BLUE",0,0,"",""),nil,"blue_lobby")
step(snap(5,22,"ACTIVE","BLUE",0,0,"RED",""),nil,"onboard_midcarry_not_event")
step(snap(5,23,"ACTIVE","BLUE",0,0,"",""),nil,"drop_no_bonus")
step(snap(5,24,"ACTIVE","BLUE",0,0,"RED",""),"PICKUP","reacquire_new_event")
local malformed = snap(5,25,"ACTIVE","BLUE",0,0,"","")
malformed.updateId=math.huge
step(malformed,nil,"infinite_seq")
local nan = snap(5,25,"ACTIVE","BLUE",0,0,"","")
nan.scores.BLUE=0/0
step(nan,nil,"nan_score")
local nonInteger = snap(5,25.5,"ACTIVE","BLUE",0,0,"","")
step(nonInteger,nil,"fractional_update")
local wrongPhase = snap(5,25,"RUN","BLUE",0,0,"","")
step(wrongPhase,nil,"fake_phase")
local wrongKind = snap(5,25,"ACTIVE","BLUE",0,0,"","")
wrongKind.kind="HACK"
step(wrongKind,nil,"wrong_kind")
print("P0D_EGG_JOY_NATIVE_LUAU_TESTS_PASS_" .. tostring(count))
'''
out=Path(a.write);out.write_text(test,encoding="utf8")
print("PURE_MODULE_BYTES",len(rules.encode("utf8")),"NATIVE_TEST_BYTES",out.stat().st_size)
