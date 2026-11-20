#!/usr/bin/env python3
"""Run 21 combat profile assertions in the ACTUAL open-source Luau VM.

This concatenation works only for a pure exported table (no Roblox service calls);
3D skill damage, VFX and client latency still require real Roblox Studio/Android.
"""
from pathlib import Path
import argparse
BASE=Path(__file__).resolve().parents[1]
SOURCE=BASE/"EGGRUMBLE_CombatBalance.luau"
def main(destination:Path):
    code=SOURCE.read_text(encoding="utf-8").rstrip()
    assert code.endswith("\nreturn Balance"),"source purity/return contract changed"
    checks='''\n
local n=Balance.validate()
assert(n==21,"expected 7 x 3")
local names={"WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE"}
local distinct={}
for _,role in ipairs(names) do
 local a=Balance.skill(role,"A")
 local b=Balance.skill(role,"B")
 local c=Balance.skill(role,"C")
 assert(a.damage>0 and b.damage>0 and c.damage>0)
 assert(a.cooldown<c.cooldown)
 local signature=string.format("%s:%d:%d:%d",role,a.damage,a.reach,a.radius)
 assert(not distinct[signature],"duplicate role signature")
 distinct[signature]=true
end
assert(Balance.skill("WARRIOR","A").damage/Balance.skill("WARRIOR","A").cooldown*Balance.KAMI_DUEL_MULTIPLIER >
 Balance.skill("NINJA","A").damage/Balance.skill("NINJA","A").cooldown, "武神 should lead 1v1")
assert(Balance.skill("MAGE","B").radius>=20,"mage needs high-value crowd AOE")
assert(Balance.skill("BUILDER","A").reach>Balance.skill("WARRIOR","A").reach)
assert(Balance.skill("BEAST","C").effect=="THREE_SPLITS")
assert(Balance.skill("TRAPPER","B").effect=="SLOW_3S")
assert(Balance.skill("ZOMBIE","B").effect=="SLOW_3S")
assert(not pcall(function() Balance.skill("FAKE","A") end))
assert(not pcall(function() Balance.skill("MAGE","X") end))
print("[EGGRUMBLE NATIVE COMBAT BALANCE] PASS",n,"role skill profiles plus fairness invariants")
'''
    destination.write_text(code[:-len("\nreturn Balance")]+checks,encoding="utf-8")
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    main(args.out)
