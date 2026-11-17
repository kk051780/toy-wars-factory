#!/usr/bin/env python3
"""Embed the exact shipped Luau policy in the native Luau test source."""
import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument("--out", required=True)
p.add_argument("--mutant", action="store_true")
args = p.parse_args()
source = (HERE / "PassiveRegenPolicy.luau").read_text(encoding="utf-8")
assert source.rstrip().endswith("return Policy"), "Unexpected policy shape; fail closed"
if args.mutant:
    original = "local QUIET_SECONDS = 7"
    assert source.count(original) == 1
    source = source.replace(original, "local QUIET_SECONDS = 0", 1)
source = source.rstrip()[: -len("return Policy")] + "local P = Policy\n"
tests = r"""
local function eq(actual, expected, message)
    assert(actual == expected, message .. " got " .. tostring(actual) .. " expected " .. tostring(expected))
end
local function close(actual, expected, message)
    assert(math.abs(actual - expected) < 0.00001, message .. " got " .. tostring(actual))
end
local wanted = {
    WARRIOR=250, MAGE=195, NINJA=185, TRAPPER=205,
    BUILDER=225, BEAST=220, ZOMBIE=230,
}
local count=0
for role, hp in pairs(wanted) do
    eq(P.maxHPForRole(role), hp, role)
    count += 1
end
eq(count,7,"all seven roles")
eq(P.maxHPForRole("UNKNOWN"),nil,"no unregistered role")
local function tick(s, t, hp, opts)
    opts=opts or {}
    return P.step(s,{
        sessionId=opts.sessionId or "roundA",
        now=t, health=hp, maxHP=opts.maxHP or 200,
        inMatch=opts.active ~= false, downed=opts.downed or false,
        hasDot=opts.dot or false,
    })
end
local s=P.new("roundA",0,100,200)
local x,r=tick(s,1,100)
eq(x,0,"no regeneration at 1 second")
x,r=tick(s,7,100)
eq(x,0,"exact seven second boundary")
x,r=tick(s,8,100)
close(x,0.7,"0.7pct/s capped at half second")
eq(r,"REGEN","regen mode")
x,r=tick(s,9,70)
eq(x,0,"hit suppresses regen")
eq(r,"REAL_DAMAGE","hit reason")
x,r=tick(s,16,70)
eq(x,0,"seven seconds after new hit")
x,r=tick(s,17,70)
close(x,0.7,"regen after new hit")
x,r=tick(s,17.1,70,{active=false})
eq(x,0,"no regen in lobby")
x,r=tick(s,18,70,{dot=true})
eq(x,0,"dot blocks regen")
x,r=tick(s,25,70)
eq(x,0,"dot resets quiet timer")
x,r=tick(s,26,70)
close(x,0.7,"regen after dot")
x,r=tick(s,27,0,{downed=true})
eq(x,0,"downed cannot regen")
x,r=tick(s,28,120,{sessionId="roundB"})
eq(r,"SESSION_RESET","old round must reset")
eq(x,0,"no cross-round regen")
x,r=P.step(s,{sessionId="roundB",now=29,health=120,maxHP=225,inMatch=true,downed=false,hasDot=false})
eq(r,"MAXHP_CHANGE","no regen on changed HP cap")
x,r=P.step(s,{sessionId="roundB",now=30,health=120,maxHP=225,inMatch=true,downed=false,hasDot=false})
eq(x,0,"new HP cap again requires delay")
x,r=P.step(s,{sessionId="roundB",now=40,health=225,maxHP=225,inMatch=true,downed=false,hasDot=false})
eq(x,0,"no heal above max")
x,r=P.step(s,{sessionId="roundB",now=39,health=225,maxHP=225,inMatch=true,downed=false,hasDot=false})
eq(r,"CLOCK_RESET","clock rollback blocked")
x,r=P.step(s,{sessionId="",now=41,health=220,maxHP=225,inMatch=true,downed=false,hasDot=false})
eq(r,"INVALID_SAMPLE","invalid session rejected")
print("GQ8_HP_REGEN_NATIVE_19_PLUS_7_ROLES_PASS")
"""
Path(args.out).write_text(source + tests, encoding="utf-8")
