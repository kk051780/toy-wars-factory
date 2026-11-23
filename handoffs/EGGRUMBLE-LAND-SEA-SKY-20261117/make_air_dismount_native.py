#!/usr/bin/env python3
"""Run the actual LSS airplane/beast dismount predicate in pinned native Luau."""
from __future__ import annotations
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "EGGRUMBLE_LandSeaSkyTraversal.server.luau"
BEGIN = "-- GQ8_LSS_AIR_DISMOUNT_GROUNDED_RESCUE_20261118_BEGIN"
END = "-- GQ8_LSS_AIR_DISMOUNT_GROUNDED_RESCUE_20261118_END"
GROUND_FENCE = "and highCraft and highAvatar and not solidBelow"
HEARTBEAT = "if flightDismountNeedsRescue(v.flying,"
RESCUE = "and safeMove(v.owner,landDock.Position+Vector3.new(0,4,0),mode,world) then"


def extract(source: str | None = None) -> str:
    s = source if source is not None else SOURCE.read_text(encoding="utf-8")
    if s.count(BEGIN) != 1 or s.count(END) != 1:
        raise ValueError("RED_AIR_DISMOUNT_SOURCE_MARKERS")
    block = s.split(BEGIN, 1)[1].split(END, 1)[0]
    if block.count("local function flightDismountNeedsRescue(") != 1 or GROUND_FENCE not in block:
        raise ValueError("RED_AIR_DISMOUNT_ACTUAL_GROUND_POLICY_DRIFT")
    if s.count(HEARTBEAT) != 1 or s.count(RESCUE) != 1:
        raise ValueError("RED_AIR_DISMOUNT_CALLBACK_UNWIRED")
    if "groundParams.FilterDescendantsInstances={ch,craft}" not in s or "groundParams.RespectCanCollide=true" not in s:
        raise ValueError("RED_AIR_DISMOUNT_UNTRUSTWORTHY_GROUND_CHECK")
    if "Workspace:Raycast(root.Position,Vector3.new(0,-12,0)" not in s:
        raise ValueError("RED_AIR_DISMOUNT_MISSING_SOLID_SUPPORT_CHECK")
    if "v.owner.Character==ch and departed.Parent==ch and departed.Health>0" not in s:
        raise ValueError("RED_AIR_DISMOUNT_STALE_AVATAR")
    return block


HARNESS = r"""
__ACTUAL_LUAU__
local function check(a,b,c,d,e,f,g,label)
 assert(flightDismountNeedsRescue(a,b,c,d,e,f,g)==(label=="RESCUE"),label)
end
check(true,true,true,true,true,true,false,"RESCUE")
check(true,true,true,true,true,true,true,"SOLID_PLATFORM")
check(false,true,true,true,true,true,false,"BOAT_NOT_AIR")
check(true,false,true,true,true,true,false,"NO_CURRENT_MATCH")
check(true,true,false,true,true,true,false,"STALE_AVATAR")
check(true,true,true,false,true,true,false,"DISTANT_OTHER_PLAYER")
check(true,true,true,true,false,true,false,"GROUND_LEVEL_CRAFT")
check(true,true,true,true,true,false,false,"GROUNDED_AVATAR")
check(true,true,true,true,true,true,false,"RESCUE")
print("GQ8_LSS_AIR_DISMOUNT_REAL_SOURCE_NATIVE_9_CASES_PASS")
"""


def generate(good: Path, mutant: Path) -> None:
    block = extract()
    good.write_text(HARNESS.replace("__ACTUAL_LUAU__", block), encoding="utf-8")
    altered = block.replace(GROUND_FENCE, "and highCraft and highAvatar and true")
    assert altered != block, "RED_AIR_DISMOUNT_MUTANT_NOT_CREATED"
    mutant.write_text(HARNESS.replace("__ACTUAL_LUAU__", altered), encoding="utf-8")


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--out", type=Path, required=True)
    a.add_argument("--mutant", type=Path, required=True)
    opts = a.parse_args()
    generate(opts.out, opts.mutant)
