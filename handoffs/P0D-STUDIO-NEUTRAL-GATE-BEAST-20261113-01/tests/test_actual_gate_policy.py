#!/usr/bin/env python3
"""Genuinely execute the original new neutral beast pure policy in pinned Luau CLI.

No Roblox physics, no human Studio proof; also reject eight adversarial mutants.
"""
from __future__ import annotations
import argparse, hashlib, pathlib, re, subprocess, sys, tempfile
SOURCE=pathlib.Path(__file__).resolve().parents[1]/"src/server/H2GateBeastPolicy.luau"
EXPECTED_SHA="0aee2fc29b376cb9be5362f5230245fdf634ddff"
TEST=r'''
local P=(function()
__REAL_ORIGINAL_POLICY__
end)()
local n=0
local function eq(actual,want,name)
  n+=1
  if actual~=want then
    error("GATE_ASSERT_"..name.." actual="..tostring(actual).." expected="..tostring(want),0)
  end
end
eq(P.nearBeast(0,2,0,"RED",true),true,"red_wakes")
eq(P.nearBeast(0,2,0,"BLUE",true),true,"blue_wakes_same")
eq(P.nearBeast(28,2,0,"BLUE",true),true,"radius_exact")
eq(P.nearBeast(28.1,2,0,"RED",true),false,"past_radius")
eq(P.nearBeast(0,2,29,"RED",true),false,"past_z_radius")
eq(P.nearBeast(0,2,0,"NONE",true),false,"no_team_no_wake")
eq(P.nearBeast(0,2,0,"HACK",true),false,"invalid_team_no_wake")
eq(P.nearBeast(0,2,0,"RED",false),false,"dead_no_wake")
eq(P.nearBeast(0,18,0,"BLUE",true),false,"too_high_no_wake")
eq(P.nearBeast(0,-3,0,"RED",true),false,"out_of_floor_no_wake")
eq(P.nearBeast(0/0,2,0,"RED",true),false,"nan_player_no_wake")
eq(P.nearBeast(math.huge,2,0,"RED",true),false,"infinite_player_no_wake")
eq(P.insideGate(0,2,0),true,"centre_player_protected")
eq(P.insideGate(4.9,2,0),true,"x_wide_enough_for_humanoid")
eq(P.insideGate(5,2,0),false,"x_edge")
eq(P.insideGate(0,2,13.9),true,"z_approach_buffer")
eq(P.insideGate(0,2,14),false,"z_edge")
eq(P.insideGate(0,16,0),true,"head_clearance")
eq(P.insideGate(0,17,0),false,"overhead_not_in_gate")
eq(P.insideGate(0,-3,0),false,"underground_outside")
eq(P.insideGate(math.huge,2,0),false,"invalid_infinite_is_not_in_gate")
eq(P.insideGate(0/0,2,0),false,"invalid_nan_is_not_in_gate")
eq(P.solid(nil),false,"nil_not_solid")
local idle=P.initial()
eq(idle.phase,P.IDLE,"initial_idle")
eq(P.solid(idle),false,"initial_not_solid")
eq(P.advance(idle,100,false,true),idle,"no_players_stays_idle")
local warn=P.advance(idle,100,true,true)
eq(warn.phase,P.WARN,"either_team_wakes_guardian")
eq(warn.untilAt,102,"visible_warning_is_2_seconds")
eq(P.solid(warn),false,"telegraph_never_collides")
eq(P.advance(warn,101,false,true),warn,"cannot_block_early")
local occupied=P.advance(warn,102,false,false)
eq(occupied.phase,P.WARN,"occupied_lane_will_not_crush_player")
eq(P.solid(occupied),false,"occupied_lane_no_collision")
eq(P.advance(warn,104,false,false).phase,P.WARN,"occupied_wait_max_5")
local skip=P.advance(warn,105,false,false)
eq(skip.phase,P.COOLDOWN,"occupied_too_long_skips_block")
eq(skip.untilAt,113,"unsafe_lane_skip_has_cooldown")
local closed=P.advance(warn,102,false,true)
eq(closed.phase,P.BLOCK,"empty_lane_allows_short_gate")
eq(closed.untilAt,107,"short_5_second_block")
eq(P.solid(closed),true,"real_server_collision_active")
eq(P.advance(closed,106,true,false),closed,"open_not_early")
local cool=P.advance(closed,107,true,false)
eq(cool.phase,P.COOLDOWN,"block_goes_to_cooldown")
eq(P.solid(cool),false,"collision_off_at_end_of_block")
eq(cool.untilAt,115,"cooldown_eight_seconds")
eq(P.advance(cool,114,true,true),cool,"cooldown_blocks_reactivation")
local fresh=P.advance(cool,115,true,true)
eq(fresh.phase,P.IDLE,"cooldown_returns_to_idle")
eq(P.advance(fresh,116,true,true).phase,P.WARN,"next_player_can_wake_again")
eq(P.advance(idle,-1,true,true),nil,"bad_negative_time_denied")
eq(P.advance(idle,0/0,true,true),nil,"nan_time_denied")
eq(P.advance(idle,math.huge,true,true),nil,"infinite_time_denied")
eq(P.advance(idle,100,"true",true),nil,"fake_nearby_type_denied")
eq(P.advance(idle,100,true,"false"),nil,"fake_clear_type_denied")
eq(P.advance({phase="CHEAT",untilAt=0,startedAt=0},100,true,true),nil,"illegal_phase_denied")
eq(P.advance({phase=P.WARN,untilAt=0/0,startedAt=0},100,true,true),nil,"corrupt_future_denied")
eq(P.advance({phase=P.WARN,untilAt=102,startedAt=103},102,true,true),nil,"rewound_clock_denied")
eq(P.advance(nil,100,true,true),nil,"nil_old_denied")
eq(P.WARNING_SECONDS,2,"warning_seconds_contract")
eq(P.BLOCK_SECONDS,5,"block_seconds_contract")
eq(P.COOLDOWN_SECONDS,8,"cooldown_seconds_contract")
eq(P.MAX_WARNING_SECONDS,5,"no_trapping_max_wait")
if n<55 then error("GATE_TOO_FEW_CASES_"..tostring(n),0) end
print("P0D_NEUTRAL_BEAST_NATIVE_POLICY_PASS_"..tostring(n))
'''
MUTANTS=[
  ("no_occupied_gate_guard",'if laneClear then','if true then'),
  ("suppress_telegraph",'P.WARNING_SECONDS = 2','P.WARNING_SECONDS = 0'),
  ("overlong_block",'P.BLOCK_SECONDS = 5','P.BLOCK_SECONDS = 25'),
  ("bypass_cooldown",'P.COOLDOWN_SECONDS = 8','P.COOLDOWN_SECONDS = 0'),
  ("wake_without_team",'if team ~= "RED" and team ~= "BLUE" then return false end','if false then return false end'),
  ("oversized_wake_radius",'P.WAKE_RADIUS = 28','P.WAKE_RADIUS = 200'),
  ("insufficient_player_collision_buffer",'math.abs(x) < 5','math.abs(x) < 0.2'),
  ("make_warning_collision",'s.phase==P.BLOCK','s.phase==P.WARN'),
]
def gitblob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def run(luau:pathlib.Path,policy:str):
    script=TEST.replace("__REAL_ORIGINAL_POLICY__",policy)
    with tempfile.TemporaryDirectory(prefix="p0d_gate_native_") as temp:
        path=pathlib.Path(temp)/"actual_beast_test.luau"
        path.write_text(script,encoding="utf-8")
        p=subprocess.run([str(luau),str(path)],capture_output=True,text=True,timeout=30)
        return p.returncode,p.stdout+p.stderr
def main():
    a=argparse.ArgumentParser()
    a.add_argument("--luau",type=pathlib.Path,required=True)
    args=a.parse_args()
    raw=SOURCE.read_bytes()
    assert gitblob(raw)==EXPECTED_SHA,("ACTUAL_POLICY_GIT_BLOB_CHANGED",gitblob(raw))
    policy=raw.decode("utf-8")
    code,output=run(args.luau,policy)
    found=re.search(r"P0D_NEUTRAL_BEAST_NATIVE_POLICY_PASS_(\d+)",output)
    if code or not found or int(found.group(1))<55:
        raise RuntimeError("ACTUAL_NATIVE_LUAU_BEAST_POLICY_FAILED "+output[-1400:])
    print(found.group(0))
    rejected=0
    for label,old,new in MUTANTS:
        if policy.count(old)!=1:
            raise RuntimeError("AMBIGUOUS_MUTANT_"+label+"_"+str(policy.count(old)))
        broken=policy.replace(old,new,1)
        status,text=run(args.luau,broken)
        if status==0 or "GATE_ASSERT_" not in text:
            raise RuntimeError("HARMFUL_MUTANT_SURVIVED_"+label+" "+text[-800:])
        rejected+=1
        print("P0D_NEUTRAL_BEAST_MUTATION_REJECTED "+label)
    assert rejected==len(MUTANTS)
    print("P0D_NEUTRAL_BEAST_NATIVE_MUTANTS_PASS_"+str(rejected))
    print("P0D_H2_BEAST_OWNER_REAL_ROBLOX_STUDIO_PHYSICS_MOBILE_NOT_TESTED")
if __name__=="__main__":
    try:main()
    except (RuntimeError,OSError,AssertionError,subprocess.TimeoutExpired) as exc:
        print("P0D_NEUTRAL_BEAST_NATIVE_BLOCKED "+str(exc),file=sys.stderr)
        sys.exit(1)
