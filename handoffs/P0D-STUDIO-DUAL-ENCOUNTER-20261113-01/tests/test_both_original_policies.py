#!/usr/bin/env python3
"""Execute TWO genuine original Luau policies in the SAME native Luau state machine.

Original #267 Star and #268 Beast are byte-pinned; the scenario only mocks
player positions/times (NOT an actual Roblox physics or multi-client run).
Eight deliberate hazardous mutations must be detected by REAL Luau assertions.
"""
from __future__ import annotations
import argparse, hashlib, pathlib, re, subprocess, sys, tempfile

REPO=pathlib.Path(__file__).resolve().parents[3]
OWN=pathlib.Path(__file__).resolve().parents[1]
STAR=OWN/"inputs/H2StarLaunchPolicy.luau"
BEAST=REPO/"handoffs/P0D-STUDIO-NEUTRAL-GATE-BEAST-20261113-01/src/server/H2GateBeastPolicy.luau"
STAR_BLOB="2879b6fc8b1547a4d13db19a616da756c04180d7"
BEAST_BLOB="0aee2fc29b376cb9be5362f5230245fdf634ddff"
LUACODE=StringRaw= r'''
local Star=(function()
__EXACT_STAR_POLICY_LUAU__
end)()
local Beast=(function()
__EXACT_BEAST_POLICY_LUAU__
end)()
local n=0
local function eq(got,want,id)
    n+=1
    if got~=want then
        error("DUAL_ASSERT_"..id.." got="..tostring(got).." want="..tostring(want),0)
    end
end
local function pad(team,padName,x,now,lastAt,extras)
    local s={team=team,pad=padName,healthy=true,grounded=true,seated=false,
        now=now or 100,lastAt=lastAt or -math.huge,x=x,y=1,z=-20}
    for key,v in pairs(extras or {}) do s[key]=v end
    return Star.canLaunch(s)
end
eq(Star.COOLDOWN,12,"one_tap_12sec")
eq(Star.MAX_DISTANCE,10,"one_tap_radius")
eq(pad("RED","RED",-66),true,"red_can_launch")
eq(pad("BLUE","RED",-66),true,"enemy_can_chase_red_pad")
eq(pad("BLUE","BLUE",66),true,"blue_can_launch")
eq(pad("RED","BLUE",66),true,"red_can_chase_blue_pad")
eq(pad("RED","BLUE",-66),false,"forged_remote_pad")
eq(pad("BLUE","RED",66),false,"forged_other_side_pad")
eq(pad("RED","RED",-55),false,"remote_launch_denied")
eq(pad("RED","RED",-56),true,"radius_boundary_allowed")
eq(pad("RED","RED",-66,100,99),false,"launch_cooldown_enforced")
eq(pad("RED","RED",-66,112,100),true,"launch_after_cooldown")
eq(pad("RED","RED",-66,100,0/0),false,"clock_nan_rejected")
eq(pad("RED","RED",-66,100,0,{grounded=false}),false,"airborne_no_repeat")
eq(pad("RED","RED",-66,100,0,{healthy=false}),false,"dead_no_jump")
eq(pad("NONE","RED",-66),false,"spectator_no_jump")
local vr=Star.velocityFor("RED")
local vb=Star.velocityFor("BLUE")
eq(vr.x,62,"red_launch_to_centre")
eq(vb.x,-62,"blue_launch_to_centre")
eq(vr.y,72,"equal_vertical_power_red")
eq(vb.y,72,"equal_vertical_power_blue")
eq(vr.z,vb.z,"equal_tactical_drift")
eq(Star.velocityFor("INVALID"),nil,"invalid_no_impulse")
eq(Beast.WARNING_SECONDS,2,"telegraph_2sec")
eq(Beast.BLOCK_SECONDS,5,"gate_block_5sec")
eq(Beast.COOLDOWN_SECONDS,8,"gate_cooldown_8sec")
eq(Beast.nearBeast(-66,1,-20,"RED",true),false,"pad_is_outside_beast_wake")
eq(Beast.nearBeast(66,1,-20,"BLUE",true),false,"blue_pad_outside_beast")
eq(Beast.nearBeast(0,2,0,"RED",true),true,"red_awakens_beast")
eq(Beast.nearBeast(0,2,0,"BLUE",true),true,"blue_awakens_beast")
eq(Beast.nearBeast(0,2,0,"NONE",true),false,"unassigned_cannot_trigger_beast")
eq(Beast.nearBeast(0,2,0,"RED",false),false,"dead_cannot_trigger_beast")
-- Source velocity and documented default gravity form a numeric-only
-- illustrative trajectory at t=.7s. NOT Roblox engine physics verification.
local gravityAssumption=196.2
local t=0.7
local ax=-66+vr.x*t
local ay=1+vr.y*t-0.5*gravityAssumption*t*t
local az=-20+vr.z*t
eq(Beast.nearBeast(ax,ay,az,"RED",true),true,"red_pads_to_guardian_wake_range")
eq(Beast.insideGate(ax,ay,az),false,"red_illustrative_jump_does_not_start_inside_gate")
local bx=66+vb.x*t
local by=1+vb.y*t-0.5*gravityAssumption*t*t
local bz=-20+vb.z*t
eq(Beast.nearBeast(bx,by,bz,"BLUE",true),true,"blue_pads_to_guardian_wake_range")
eq(Beast.insideGate(bx,by,bz),false,"blue_illustrative_jump_not_inside_gate")
eq(math.abs(ax+bx)<0.001,true,"two_team_horizontally_symmetric")
local idle=Beast.initial()
eq(idle.phase,Beast.IDLE,"start_unblocked")
eq(Beast.solid(idle),false,"initial_center_route_open")
local warn=Beast.advance(idle,100,true,true)
eq(warn.phase,Beast.WARN,"guardian_wakes_after_approach")
eq(warn.untilAt,102,"guardian_warn_until102")
eq(Beast.solid(warn),false,"warning_never_physically_blocks")
eq(Beast.advance(warn,101,true,true).phase,Beast.WARN,"warning_must_last2sec")
local occupied=Beast.advance(warn,102,true,false)
eq(occupied.phase,Beast.WARN,"safe_skip_occupied_gate")
eq(Beast.solid(occupied),false,"occupied_never_crushed")
eq(Beast.insideGate(0,3,0),true,"model_body_safety_buffer")
eq(Beast.insideGate(4.5,2,11),true,"wide_humanoid_buffer")
eq(Beast.advance(warn,105,true,false).phase,Beast.COOLDOWN,"timeout_skip_instead_of_grief")
local closed=Beast.advance(warn,102,true,true)
eq(closed.phase,Beast.BLOCK,"clear_gate_engages")
eq(Beast.solid(closed),true,"center_ground_physically_blocked")
eq(closed.untilAt,107,"only_five_seconds")
eq(Beast.advance(closed,106,true,true),closed,"gate_does_not_expire_early")
local cool=Beast.advance(closed,107,true,true)
eq(cool.phase,Beast.COOLDOWN,"gate_releases")
eq(Beast.solid(cool),false,"route_reopens_after5")
eq(Beast.advance(cool,114,true,true).phase,Beast.COOLDOWN,"cooldown_not_early")
eq(Beast.advance(cool,115,true,true).phase,Beast.IDLE,"cooldown_recovered")
eq(Beast.advance(Beast.initial(),100,"true",true),nil,"failclosed_fake_wake_input")
eq(Beast.advance(Beast.initial(),100,true,"true"),nil,"failclosed_fake_clear_input")
eq(Beast.advance(Beast.initial(),0/0,true,true),nil,"failclosed_nan_clock")
eq(Beast.nearBeast(0/0,1,0,"RED",true),false,"failclosed_nan_position")
if n<55 then error("DUAL_REAL_POLICY_TOO_FEW_CHECKS_"..tostring(n),0) end
print("P0D_DUAL_ORIGINAL_BOTH_NATIVE_POLICY_PASS_"..tostring(n))
'''
MUTANTS=[
    ("remote_star_pad",'dx*dx + dy*dy + dz*dz <= P.MAX_DISTANCE*P.MAX_DISTANCE','true'),
    ("star_cooldown_bypass",'s.now - s.lastAt < P.COOLDOWN','false'),
    ("star_unbalanced",'x=-P.SPEED_X','x=P.SPEED_X'),
    ("star_airborne_retrigger",'s.grounded ~= true','false'),
    ("beast_missing_warning",'P.WARNING_SECONDS = 2','P.WARNING_SECONDS = 0'),
    ("beast_unsafe_gate_occupied",'if laneClear then','if true then'),
    ("beast_too_long_block",'P.BLOCK_SECONDS = 5','P.BLOCK_SECONDS = 25'),
    ("beast_no_cooldown",'P.COOLDOWN_SECONDS = 8','P.COOLDOWN_SECONDS = 0'),
    ("beast_wake_without_team",'if team ~= "RED" and team ~= "BLUE" then return false end','if false then return false end'),
]
def blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def load(path:pathlib.Path,expected:str)->str:
    raw=path.read_bytes()
    if blob(raw)!=expected:raise RuntimeError("ORIGINAL_POLICY_BYTE_CHANGED "+str(path))
    return raw.decode("utf-8")
def run(luau:pathlib.Path,star:str,beast:str):
    script=LUACODE.replace("__EXACT_STAR_POLICY_LUAU__",star)
    script=script.replace("__EXACT_BEAST_POLICY_LUAU__",beast)
    with tempfile.TemporaryDirectory(prefix="p0d_dual_actual_native_") as tmp:
        path=pathlib.Path(tmp)/"actual_two_original_policies.luau"
        path.write_text(script,encoding="utf-8")
        p=subprocess.run([str(luau),str(path)],capture_output=True,text=True,timeout=30)
        return p.returncode,p.stdout+p.stderr
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--luau",required=True,type=pathlib.Path)
    args=parser.parse_args()
    star=load(STAR,STAR_BLOB)
    beast=load(BEAST,BEAST_BLOB)
    code,output=run(args.luau,star,beast)
    result=re.search(r"P0D_DUAL_ORIGINAL_BOTH_NATIVE_POLICY_PASS_(\d+)",output)
    if code or not result or int(result.group(1))<55:
        raise RuntimeError("ORIGINAL_TWO_POLICIES_FAILED "+output[-1500:])
    print(result.group(0))
    for name,old,new in MUTANTS:
        target=star if name.startswith("star_") or name=="remote_star_pad" else beast
        if target.count(old)!=1:
            raise RuntimeError("MUTATION_UNIQUE_ANCHOR_"+name+"_"+str(target.count(old)))
        broken=target.replace(old,new,1)
        c,log=run(args.luau,broken if target==star else star,broken if target==beast else beast)
        if c==0 or "DUAL_ASSERT_" not in log:
            raise RuntimeError("UNDETECTED_COMBINED_HAZARD_"+name+" "+log[-700:])
        print("P0D_DUAL_ACTUAL_POLICY_HAZARD_REJECTED "+name)
    print("P0D_DUAL_REAL_NATIVE_HAZARDOUS_MUTANTS_PASS_"+str(len(MUTANTS)))
    print("P0D_DUAL_ACTUAL_ENGINE_2CLIENT_PHONE_FUN_NOT_TESTED")
if __name__=="__main__":
    try:main()
    except (OSError,RuntimeError,AssertionError,subprocess.TimeoutExpired) as e:
        print("P0D_DUAL_REAL_NATIVE_BLOCKED "+str(e),file=sys.stderr)
        sys.exit(1)
