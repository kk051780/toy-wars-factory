#!/usr/bin/env python3
"""Generate Luau VM tests from the exact LSS idle-lease helper, not a reimplementation."""
from __future__ import annotations
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "EGGRUMBLE_LandSeaSkyTraversal.server.luau"
BEGIN = "-- GQ8_LSS_IDLE_CRAFT_LEASE_20261118_BEGIN"
END = "-- GQ8_LSS_IDLE_CRAFT_LEASE_20261118_END"
PREDICATE = "now-emptySince>=EMPTY_CRAFT_GRACE_SECONDS"

def actual_helper(source: str | None = None) -> str:
    s = source if source is not None else SOURCE.read_text(encoding="utf-8")
    if s.count(BEGIN) != 1 or s.count(END) != 1:
        raise ValueError("RED_IDLE_CRAFT_SOURCE_MARKER_DRIFT")
    selected = s.split(BEGIN, 1)[1].split(END, 1)[0]
    if selected.count("local function emptyCraftLease(") != 1 or selected.count(PREDICATE) != 1:
        raise ValueError("RED_IDLE_CRAFT_HELPER_CHANGED")
    if s.count("emptyCraftLease(activePilot,v.emptySince,os.clock())") != 1:
        raise ValueError("RED_IDLE_CRAFT_REAL_HEARTBEAT_NOT_CONNECTED")
    if "if idleExpired then" not in s or "v.lastPilot=nil\n     craft:Destroy()" not in s:
        raise ValueError("RED_IDLE_CRAFT_RETIRE_UNWIRED")
    return selected

HARNESS = r"""
local EMPTY_CRAFT_GRACE_SECONDS=25
__ACTUAL_HELPER__
local expired,stamp
expired,stamp=emptyCraftLease(false,nil,100)
assert(expired==false and stamp==100,"NEW_EMPTY_START")
expired,stamp=emptyCraftLease(false,stamp,124.999)
assert(expired==false and stamp==100,"REBOARDING_GRACE")
expired,stamp=emptyCraftLease(false,stamp,125)
assert(expired==true and stamp==100,"EXACT_EXPIRY")
expired,stamp=emptyCraftLease(true,100,125)
assert(expired==false and stamp==nil,"OWNER_REBOARDED_RESET")
expired,stamp=emptyCraftLease(false,stamp,200)
assert(expired==false and stamp==200,"SECOND_IDLE_EPOCH")
expired,stamp=emptyCraftLease(false,stamp,212)
assert(expired==false and stamp==200,"SECOND_GRACE")
expired,stamp=emptyCraftLease(true,stamp,212)
assert(expired==false and stamp==nil,"INTERMITTENT_REBOARD")
expired,stamp=emptyCraftLease(false,stamp,220)
assert(expired==false and stamp==220,"AFTER_REBOARD_START")
expired,stamp=emptyCraftLease(false,stamp,245)
assert(expired==true,"AFTER_REBOARD_EXPIRY")
expired,stamp=emptyCraftLease(false,nil,10000)
assert(expired==false and stamp==10000,"NEW_CRAFT_NO_EARLY_RETIRE")
print("GQ8_LSS_IDLE_CRAFT_REAL_SOURCE_LUAU_10_CASES_PASS")
"""

def generate(out: Path, mutant: Path):
    helper = actual_helper()
    out.parent.mkdir(parents=True, exist_ok=True)
    mutant.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(HARNESS.replace("__ACTUAL_HELPER__",helper),encoding="utf-8")
    broken=helper.replace(PREDICATE,"now-emptySince<EMPTY_CRAFT_GRACE_SECONDS")
    mutant.write_text(HARNESS.replace("__ACTUAL_HELPER__",broken),encoding="utf-8")

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--out",type=Path,required=True)
    a.add_argument("--mutant",type=Path,required=True)
    args=a.parse_args()
    generate(args.out,args.mutant)
