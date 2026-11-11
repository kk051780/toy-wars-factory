#!/usr/bin/env python3
"""Execute exact CURRENT S1TrapRules.luau under pinned native Luau (not Roblox Studio)."""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import tempfile

SOURCE = Path(__file__).resolve().parents[1] / "src/server/S1TrapRules.luau"
CASES = r'''
local T=(function()
__SOURCE__
end)()
local checks=0
local function check(v, id)
    checks+=1
    assert(v,id)
end
local function placement(overrides)
    local v = {
        phase="ACTIVE",team="RED",role="GUARDIAN",alive=true,carrying=false,
        now=100,lastAt=-math.huge,x=-32,y=5,z=0,count=0,
        avoid={{x=-68,z=0},{x=-98,z=-20},{x=-107,z=0},{x=-82,z=20}}
    }
    for k,value in pairs(overrides or {}) do v[k]=value end
    return T.canPlace(v)
end
check(placement(),"first_guardian_valid")
check(not placement({role="RAIDER"}),"raider_forbidden")
check(not placement({phase="LOBBY"}),"lobby_forbidden")
check(not placement({team="BLUE"}),"enemy_half_forbidden")
check(not placement({carrying=true}),"carrier_forbidden")
check(not placement({alive=false}),"dead_forbidden")
check(not placement({count=2}),"max_two")
check(not placement({now=100,lastAt=91}),"cooldown")
check(placement({now=121,lastAt=100}),"cooldown_elapsed")
check(not placement({x=-68}),"spawn_safety")
check(not placement({x=-98,z=-20}),"egg_safety")
check(not placement({x=-82,z=20}),"scorepad_safety")
check(not placement({x=-1}),"middle_band")
check(not placement({z=56}),"border")
check(not placement({y=11}),"wrong_floor")
check(not placement({x=0/0}),"nan_position")
local function trigger(o)
    local v={phase="ACTIVE",healthy=true,invulnerable=false,
        trapTeam="RED",enemyTeam="BLUE",now=102,expiresAt=125,
        x=-30,z=0,enemyX=-30,enemyY=5,enemyZ=0}
    for k,value in pairs(o or {}) do v[k]=value end
    return T.shouldTrigger(v)
end
check(trigger(),"enemy_steps_on_trap")
check(trigger({enemyX=-25}),"radius_edge_included")
check(not trigger({enemyX=-24.9}),"outside_radius")
check(not trigger({enemyY=9}),"jump_over_trap")
check(not trigger({enemyTeam="RED"}),"own_team_safe")
check(not trigger({invulnerable=true}),"spawn_invuln")
check(not trigger({healthy=false}),"dead_enemy")
check(not trigger({now=125}),"expired_trap")
check(not trigger({phase="RESULTS"}),"ended_round")
check(T.slowSpeed(19)==10,"raider_slows_to_ten")
check(T.slowSpeed(15)==8,"guardian_slows_to_eight")
check(T.slowSpeed(0)==nil,"invalid_baseline")
check(T.slowSpeed(0/0)==nil,"nan_baseline")
print("P0D_GUARDIAN_TRAP_NATIVE_PASS assertions="..tostring(checks))
'''
MUTATIONS = (
    ("role_bypass", 's.role ~= "GUARDIAN"', 's.role ~= "RAIDER"'),
    ("cooldown_bypass", 's.now - s.lastAt < TrapRules.COOLDOWN', 's.now - s.lastAt > TrapRules.COOLDOWN'),
    ("radius_inverted", 'dx * dx + dz * dz <= TrapRules.RADIUS * TrapRules.RADIUS', 'dx * dx + dz * dz >= TrapRules.RADIUS * TrapRules.RADIUS'),
)

def execute(luau: Path, src: str) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'test.luau'
        # Source is executed byte-for-byte inside a temporary local function;
        # the original production source is NEVER modified in its own tree.
        path.write_text(CASES.replace("__SOURCE__",src), encoding="utf-8")
        p=subprocess.run([str(luau),str(path)],text=True,stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,timeout=40,check=False)
        return p.returncode,p.stdout

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--luau",required=True,type=Path)
    args=parser.parse_args()
    src=SOURCE.read_text(encoding="utf-8")
    code,out=execute(args.luau,src)
    if code != 0 or "P0D_GUARDIAN_TRAP_NATIVE_PASS assertions=29" not in out:
        raise SystemExit("NATIVE_TRAP_ORIGINAL_FAIL "+out[-1400:])
    print(out.strip())
    for name,find,repl in MUTATIONS:
        assert src.count(find)==1, "UNIQUE_MUTATION_ANCHOR "+name
        code,result=execute(args.luau,src.replace(find,repl))
        if code==0:
            raise SystemExit("MUTATION_UNDETECTED "+name)
        print("P0D_GUARDIAN_TRAP_NEGATIVE_REJECTED "+name)
    print("P0D_GUARDIAN_TRAP_3_OF_3_MUTATIONS_PASS")

if __name__=="__main__":
    main()
