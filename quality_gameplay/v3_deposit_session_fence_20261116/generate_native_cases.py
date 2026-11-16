#!/usr/bin/env python3
"""Native Luau differential generated from the actual selected original Host callback predicate."""
from pathlib import Path
from argparse import ArgumentParser
from select_deposit import BLOCK, REPLACEMENT

def make(source: bytes) -> str:
    if source.count(REPLACEMENT)!=1 or source.count(BLOCK)!=0:
        raise ValueError("RED: selected original Host guard missing")
    current=REPLACEMENT.decode("utf-8").splitlines()[1].strip().replace(" then return end"," then return false end")
    old=BLOCK.decode("utf-8").splitlines()[1].strip().replace(" then return end"," then return false end")
    return """-- Generated from exact original/current Host Luau predicate.
local joined={[101]="TEAM"}
local entry={id="101"}
local session={mode="TEAM",rules={phase="ACTIVE"}}
local sessions={TEAM=session}
local p={UserId=101}
local function current()
  """+current+"""
  return true
end
local function original()
  """+old+"""
  return true
end
assert(current()==true,"valid owner allowed")
joined[101]="BATTLE_ROYALE"
assert(original()==true and current()==false,"old mode allowed by original; fixed denies")
joined[101]="TEAM"
sessions.TEAM={mode="TEAM",rules={phase="ACTIVE"}}
assert(original()==true and current()==false,"old session allowed by original; fixed denies")
sessions.TEAM=session
entry.id="202"
assert(current()==false,"foreign castle owner denied")
entry.id="101"
session.rules=nil
assert(current()==false,"missing rules denied")
session.rules={phase="ACTIVE"}
assert(current()==true,"legitimate return allowed")
joined[101]=nil
assert(current()==false,"departed player denied")
print("GQ_DEPOSIT_CURRENT_SESSION_NATIVE_7_CASES_PASS")
"""

if __name__=="__main__":
    ap=ArgumentParser()
    ap.add_argument("--selected",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(make(args.selected.read_bytes()),encoding="utf-8")
