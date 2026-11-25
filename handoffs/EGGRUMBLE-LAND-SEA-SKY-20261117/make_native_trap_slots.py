#!/usr/bin/env python3
"""Extract the ACTUAL optional32 Luau slot allocator, run positive and mutant cases."""
from __future__ import annotations
import argparse
from pathlib import Path

SOURCE=Path(__file__).resolve().with_name("EGGRUMBLE_LandSeaSkyTraversal.server.luau")
BEGIN="-- GQ8_LSS_TRAP_SPATIAL_SLOTS_20261118_BEGIN"
END="-- GQ8_LSS_TRAP_SPATIAL_SLOTS_20261118_END"

def extract(src: str) -> str:
    if src.count(BEGIN)!=1 or src.count(END)!=1:
        raise ValueError("RED_TRAP_SLOT_MARKER")
    fn=src.split(BEGIN,1)[1].split(END,1)[0]
    required=(
       "local function chooseUnoccupiedTrapSlot()",
       'local slot=part:GetAttribute("LSS_TrapSlot")',
       "if slot==1 or slot==2 then occupied[slot]=true end",
       "if not occupied[1] then return 1 end",
       "if not occupied[2] then return 2 end",
       "return nil",
    )
    if any(piece not in fn for piece in required):
        raise ValueError("RED_TRAP_SLOT_AUTHORITY")
    if src.count('t:SetAttribute("LSS_TrapSlot",slot)')!=1 or src.count("local slot=chooseUnoccupiedTrapSlot()")!=1 or src.count("x+48+(slot-1)*30")!=1:
        raise ValueError("RED_TRAP_SLOT_WIRING")
    if src.index("local slot=chooseUnoccupiedTrapSlot()")>src.index('t:SetAttribute("LSS_TrapSlot",slot)'):
        raise ValueError("RED_TRAP_SLOT_ORDER")
    return fn

def build(src: str, mutant: bool=False) -> str:
    fn=extract(src)
    if mutant:
        fn=fn.replace("if not occupied[2] then return 2 end",
                      "if not occupied[2] then return 1 end",1)
    header="""
local traps={}
"""
    cases="""
local function mockPart(slot)
 local p={Parent=true,slot=slot}
 function p:GetAttribute(key)
  assert(key=="LSS_TrapSlot")
  return self.slot
 end
 return p
end
assert(chooseUnoccupiedTrapSlot()==1,"RED_EMPTY_MUST_CHOOSE_ONE")
local first=mockPart(1)
traps[first]=101
assert(chooseUnoccupiedTrapSlot()==2,"RED_SECOND_OWNER_MUST_HAVE_DISTINCT_SLOT")
local second=mockPart(2)
traps[second]=202
assert(chooseUnoccupiedTrapSlot()==nil,"RED_FULL_TWO_SLOT_CAP")
first.Parent=nil
assert(chooseUnoccupiedTrapSlot()==1,"RED_DESTROYED_FIRST_SLOT_NOT_RECLAIMED")
first.Parent=true
second.Parent=nil
assert(chooseUnoccupiedTrapSlot()==2,"RED_DESTROYED_SECOND_SLOT_NOT_RECLAIMED")
traps[first]=nil
assert(chooseUnoccupiedTrapSlot()==1,"RED_DELETED_FIRST_SLOT_NOT_RECLAIMED")
print("GQ8_LSS_TRAP_SPATIAL_6_NATIVE_CASES_PASS")
"""
    return header+fn+"\n"+cases

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--mutant",type=Path,required=True)
    args=ap.parse_args()
    src=SOURCE.read_text(encoding="utf-8")
    args.out.write_text(build(src),encoding="utf-8")
    args.mutant.write_text(build(src,mutant=True),encoding="utf-8")

if __name__=="__main__":
    main()
