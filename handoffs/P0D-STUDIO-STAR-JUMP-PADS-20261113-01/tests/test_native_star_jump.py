#!/usr/bin/env python3
"""Execute exact new original H2 pure Luau gameplay policy and hostile mutants."""
from __future__ import annotations
import argparse, pathlib, subprocess, sys, tempfile, re, hashlib
SOURCE=pathlib.Path(__file__).resolve().parents[1]/"src/server/H2StarLaunchPolicy.luau"
EXPECTED_SHA="2879b6fc8b1547a4d13db19a616da756c04180d7"
LUAU= r'''
local P=(function()
__ORIGINAL_SOURCE_BYTES__
end)()
local n=0
local function eq(a,b,why)
 n+=1
 if a~=b then error("STAR_ASSERT_"..why.." got="..tostring(a).." want="..tostring(b),0) end
end
local function scenario(patch)
 local s={team="RED",pad="RED",healthy=true,grounded=true,seated=false,
  x=-66,y=1,z=-20,now=100,lastAt=-math.huge}
 for key,v in pairs(patch or {}) do s[key]=v end
 return P.canLaunch(s)
end
eq(scenario({}),true,"both_team_free_valid_red")
eq(scenario({team="BLUE"}),true,"enemy_can_also_use_red_pad")
eq(scenario({team="BLUE",pad="BLUE",x=66}),true,"mirror_blue_valid")
eq(scenario({team="RED",pad="BLUE",x=66}),true,"red_can_chase_blue_side")
eq(scenario({team="NONE"}),false,"not_joined_s1_team")
eq(scenario({team="HACKER"}),false,"invalid_team")
eq(scenario({pad="VOID"}),false,"invalid_pad")
eq(scenario({pad="BLUE"}),false,"cannot_activate_remote_pad")
eq(scenario({x=-55}),false,"far_11_studs")
eq(scenario({x=-56}),true,"at_10_stud_radius")
eq(scenario({y=12}),false,"too_far_in_vertical_distance")
eq(scenario({y=-1}),false,"cannot_launch_from_below_arena")
eq(scenario({grounded=false}),false,"airborne_retrigger_forbidden")
eq(scenario({healthy=false}),false,"dead_forbidden")
eq(scenario({seated=true}),false,"seated_forbidden")
eq(scenario({now=100,lastAt=90}),false,"cooldown_10_of_12")
eq(scenario({now=102,lastAt=90}),true,"cooldown_exact_12_allowed")
eq(scenario({now=102,lastAt=91}),false,"cooldown_11_denied")
eq(scenario({x=0/0}),false,"nan_x_fails_closed")
eq(scenario({z=0/0}),false,"nan_z_fails_closed")
eq(scenario({now=0/0}),false,"nan_clock_fails_closed")
eq(scenario({lastAt=0/0}),false,"nan_prior_clock_fails_closed")
eq(scenario({x=math.huge}),false,"inf_x_fails_closed")
eq(scenario({now=math.huge}),false,"inf_clock_fails_closed")
eq(P.canLaunch(nil),false,"missing_record")
eq(P.canLaunch({}),false,"empty_record")
local red=P.velocityFor("RED")
local blue=P.velocityFor("BLUE")
eq(red.x,62,"red_launch_towards_centre")
eq(blue.x,-62,"blue_launch_towards_centre")
eq(red.y,72,"upward_impulse")
eq(blue.y,72,"symmetric_upward_impulse")
eq(red.z,16,"red_angled_escape")
eq(blue.z,16,"blue_angled_escape")
eq(P.velocityFor("VOID"),nil,"invalid_pad_has_no_velocity")
eq(P.COOLDOWN,12,"cooldown_declared")
eq(P.MAX_DISTANCE,10,"distance_declared")
print("H2_STAR_JUMP_NATIVE_ACTUAL_POLICY_PASS_"..tostring(n))
'''
MUTANTS=[
 ("no_nearby_check",'dx*dx + dy*dy + dz*dz <= P.MAX_DISTANCE*P.MAX_DISTANCE',
  'true',"STAR_ASSERT_cannot_activate_remote_pad"),
 ("no_cooldown",'s.now - s.lastAt < P.COOLDOWN',
  'false',"STAR_ASSERT_cooldown_10_of_12"),
 ("no_enemy_access",'s.team ~= "RED" and s.team ~= "BLUE"',
  's.team ~= "RED"',"STAR_ASSERT_enemy_can_also_use_red_pad"),
 ("no_grounded_gate",'s.grounded ~= true',
  'false',"STAR_ASSERT_airborne_retrigger_forbidden"),
 ("unbalanced_launch",'x=-P.SPEED_X','x=P.SPEED_X',
  "STAR_ASSERT_blue_launch_towards_centre"),
 ("no_healthy_gate",'s.healthy ~= true','false',"STAR_ASSERT_dead_forbidden"),
]
def blob(b):
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def run(luau,src):
    code=LUAU.replace("__ORIGINAL_SOURCE_BYTES__",src)
    with tempfile.TemporaryDirectory(prefix="h2_star_") as td:
        f=pathlib.Path(td)/"test_star_policy.luau"
        f.write_text(code,encoding="utf-8")
        r=subprocess.run([str(luau),str(f)],capture_output=True,text=True,timeout=30)
        return r.returncode,r.stdout+r.stderr
def main():
    p=argparse.ArgumentParser();p.add_argument("--luau",required=True,type=pathlib.Path)
    a=p.parse_args();raw=SOURCE.read_bytes()
    assert blob(raw)==EXPECTED_SHA,("ORIGINAL_SOURCE_BLOB_CHANGED",blob(raw))
    src=raw.decode("utf-8")
    status,out=run(a.luau,src)
    if status or "H2_STAR_JUMP_NATIVE_ACTUAL_POLICY_PASS_35" not in out:
        raise RuntimeError("GENUINE_H2_LUAU_POLICY_FAILED "+out[-1300:])
    print(out.strip())
    for key,anchor,new,expected in MUTANTS:
        if src.count(anchor)!=1:raise RuntimeError("UNIQUE_MUTATION_ANCHOR_FAILED_"+key)
        code,log=run(a.luau,src.replace(anchor,new,1))
        if code==0 or expected not in log:
            raise RuntimeError("MUTANT_NOT_REJECTED_"+key+" "+log[-900:])
        print("H2_STAR_JUMP_POLICY_MUTATION_REJECTED "+key)
    print("H2_STAR_JUMP_NATIVE_NEGATIVE_MUTANTS_PASS_6")
    print("H2_STAR_JUMP_OWNER_REAL_STUDIO_2CLIENT_MOBILE_NOT_TESTED")
if __name__=="__main__":
    try:main()
    except (OSError,RuntimeError,AssertionError,subprocess.TimeoutExpired) as x:
        print("H2_NATIVE_POLICY_BLOCKED "+str(x),file=sys.stderr);sys.exit(1)
