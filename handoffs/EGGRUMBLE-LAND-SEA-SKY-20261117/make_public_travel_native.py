#!/usr/bin/env python3
"""Real-source Luau cases for optional LSS voluntary public travel pacing.
Extract actual helper; mutate only its cooldown predicate for expected RED.
"""
from __future__ import annotations
import argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/"EGGRUMBLE_LandSeaSkyTraversal.server.luau"
BEGIN=" -- GQ8_LSS_PUBLIC_TRAVEL_PACING_20261118_BEGIN\n"
END=" -- GQ8_LSS_PUBLIC_TRAVEL_PACING_20261118_END"
PRED="  if prev and now-prev<PUBLIC_TRAVEL_COOLDOWN then return false end"

def helper():
    source=SOURCE.read_text(encoding="utf-8")
    if source.count(BEGIN)!=1 or source.count(END)!=1:
        raise ValueError("RED_GQ8_PUBLIC_TRAVEL_MARKER_MISSING")
    chunk=source.split(BEGIN,1)[1].split(END,1)[0]
    if chunk.count(PRED)!=1 or chunk.count("if not safeMove(player,at,mode,world) then return false end")!=1:
        raise ValueError("RED_GQ8_PUBLIC_TRAVEL_HELPER_DRIFT")
    for fragment in [
        "publicTravel(p,offshorePads[-1].Position",
        "publicTravel(p,landDock.Position",
        "publicTravel(p,Vector3.new(sx,cloudY+5,skyZ))",
        "publicTravel(p,groundLift.Position",
        "safeMove(v.owner,landDock.Position", 
        "table.clear(publicTravelAt)",
    ]:
        if fragment not in source:
            raise ValueError("RED_GQ8_PUBLIC_TRAVEL_ROUTE_OR_RESCUE_"+fragment)
    return chunk

HARNESS=r"""
local now=100
local permitted=true
local active=true
local PUBLIC_TRAVEL_COOLDOWN=2.5
local os={clock=function()return now end}
local mode="TEAM"
local world={}
local moved={}
local function safeMove(player,at,checkMode,checkWorld)
 assert(checkMode==mode and checkWorld==world)
 if not permitted then return false end
 table.insert(moved,{uid=player.UserId,place=at})
 return true
end
__HELPER__
local a={UserId=101}
local b={UserId=202}
assert(publicTravel(a,"dock"),"RED_GQ8_FIRST_TRAVEL")
assert(not publicTravel(a,"cloud"),"RED_GQ8_PUBLIC_TRAVEL_DOUBLE_HOP")
assert(publicTravel(b,"cloud"),"RED_GQ8_CROSS_PLAYER_COOLDOWN_LEAK")
now=102.49
assert(not publicTravel(a,"dock"),"RED_GQ8_BEFORE_BOUNDARY")
now=102.5
assert(publicTravel(a,"dock"),"RED_GQ8_AT_BOUNDARY")
now=105
permitted=false
assert(not publicTravel(a,"bad"),"RED_GQ8_BAD_MOVE_APPROVED")
permitted=true
assert(publicTravel(a,"good"),"RED_GQ8_FAILED_MOVE_CONSUMED_COOLDOWN")
active=false
now=120
assert(not publicTravel(a,"inactive"),"RED_GQ8_INACTIVE_TRAVEL")
assert(#moved==4,"RED_GQ8_MOVE_COUNT")
print("GQ8_LSS_PUBLIC_TRAVEL_LUAU_8_CASES_PASS")
"""

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--mutant",type=Path,required=True)
    a=p.parse_args()
    actual=helper()
    a.out.write_text(HARNESS.replace("__HELPER__",actual),encoding="utf-8")
    invalid=actual.replace(PRED,"  -- MUTANT: public travel cooldown was bypassed")
    a.mutant.write_text(HARNESS.replace("__HELPER__",invalid),encoding="utf-8")
    print("GQ8_LSS_PUBLIC_TRAVEL_REAL_SOURCE_NATIVE_AND_MUTANT_GENERATED")

if __name__=="__main__":
    main()
