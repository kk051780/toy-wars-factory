#!/usr/bin/env python3
"""Real optional LSS source-derived Luau VM: trap ownership fairness, fail-closed."""
from pathlib import Path
import argparse

SOURCE=Path(__file__).with_name("EGGRUMBLE_LandSeaSkyTraversal.server.luau")
BEGIN=" -- GQ8_LSS_TRAP_OWNER_FAIRNESS_20261118_BEGIN\n"
END=" -- GQ8_LSS_TRAP_OWNER_FAIRNESS_20261118_END\n"
ANCHOR="if previousOwner==ownerId then return false end"

def extract(source: str) -> str:
    if source.count(BEGIN)!=1 or source.count(END)!=1:
        raise ValueError("RED_TRAP_OWNER_MARKER_DRIFT")
    selected=source.split(BEGIN,1)[1].split(END,1)[0]
    if selected.count(ANCHOR)!=1 or selected.count("return live<MAX_LIVE_TRAPS")!=1:
        raise ValueError("RED_TRAP_OWNER_POLICY_DRIFT")
    if "traps[t]=owner.UserId" not in source or "canReserveTrapSlot(owner.UserId)" not in source:
        raise ValueError("RED_TRAP_OWNER_NOT_SELECTED")
    return selected

CASES="""local a={Parent=true}
local b={Parent=true}
local expired={Parent=nil}
assert(canReserveTrapSlot(101), "RED_INITIAL_SLOT_BLOCKED")
traps[a]=101
assert(not canReserveTrapSlot(101), "RED_SAME_OWNER_TWO_TRAPS")
assert(canReserveTrapSlot(202), "RED_SECOND_PLAYER_BLOCKED")
traps[b]=202
assert(not canReserveTrapSlot(303), "RED_GLOBAL_THIRD_TRAP_ACCEPTED")
assert(not canReserveTrapSlot(101), "RED_OWNER_FIRST_TRAP_BYPASS")
b.Parent=nil
assert(canReserveTrapSlot(202), "RED_DESTROYED_TRAP_NOT_RELEASED")
assert(canReserveTrapSlot(303), "RED_DESTROYED_GLOBAL_SLOT_NOT_RELEASED")
assert(not canReserveTrapSlot(101), "RED_OTHER_OWNER_TRAP_CHANGED")
traps[expired]=404
assert(canReserveTrapSlot(404), "RED_EXPIRED_SLOT_STILL_ACTIVE")
a.Parent=nil
assert(canReserveTrapSlot(101), "RED_OLD_OWNER_COOLDOWN_STUCK")
assert(canReserveTrapSlot(202), "RED_BOTH_SLOTS_NOT_FREED")
print("GQ8_LSS_TRAP_OWNER_LUAU_11_CASES_PASS")
"""

def build(source: str, mutant: bool=False) -> str:
    fn=extract(source)
    if mutant:
        fn=fn.replace(ANCHOR,"if previousOwner==-1 then return false end",1)
    return "local MAX_LIVE_TRAPS=2\nlocal traps={}\n"+fn+"\n"+CASES

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--mutant",type=Path,required=True)
    args=p.parse_args()
    src=SOURCE.read_text(encoding="utf-8")
    if args.out==args.mutant or args.out.exists() or args.mutant.exists():
        raise ValueError("RED_HARNESS_OUTPUT_COLLISION")
    args.out.write_text(build(src),encoding="utf-8")
    args.mutant.write_text(build(src,mutant=True),encoding="utf-8")
    print("GQ8_LSS_TRAP_OWNER_VM_GOOD_AND_MUTANT_CREATED")

if __name__=="__main__":
    main()
