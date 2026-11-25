#!/usr/bin/env python3
"""Native Luau tests generated from the LSS script's REAL collision filter helper.

This is not a pasted replica: changes to the actual helper change the native
test implementation. The negative mutant keeps syntax valid but drops pilot.
"""
from pathlib import Path
import argparse

HERE=Path(__file__).parent
SOURCE=HERE/"EGGRUMBLE_LandSeaSkyTraversal.server.luau"
START="local function vehicleSweepExclusions(craft,water,offshoreWater,pilotCharacter)\n"
END="\nend\n\n-- GQ8_LSS_FULL_CRAFT_SWEEP_20261118:"

PRELUDE="""-- Native self/other collision filter regression.
local craft={Name="Craft"}
local water={Name="Coast"}
local offshoreWater={Name="Offshore"}
local pilot={Name="ActualServerOccupiedPlayerCharacter"}
local otherPlayer={Name="OtherPlayerRemainSolid"}
local castle={Name="CastleWallRemainSolid"}
"""

TAIL="""
local excluded=vehicleSweepExclusions(craft,water,offshoreWater,pilot)
assert(#excluded==4,"RED_PILOT_NOT_EXCLUDED")
assert(excluded[1]==craft and excluded[2]==water and excluded[3]==offshoreWater,
 "RED_ORIGINAL_SWEEP_FILTER_CHANGED")
assert(excluded[4]==pilot,"RED_SIT_OCCUPANT_MUST_BE_EXCLUDED")
assert(table.find(excluded,otherPlayer)==nil,"RED_OPPONENT_MUST_REMAIN_BLOCKING")
assert(table.find(excluded,castle)==nil,"RED_CASTLE_MUST_REMAIN_BLOCKING")
local noPilot=vehicleSweepExclusions(craft,water,offshoreWater,nil)
assert(#noPilot==3,"RED_MISSING_PILOT_SHOULD_NOT_EXCLUDE_OTHERS")
assert(table.find(noPilot,pilot)==nil)
print("GQ8_LSS_PILOT_OWN_BODY_BLOCKCAST_EXCLUSION_REAL_LUAU_PASS")
"""

def extract(src: str) -> str:
    if src.count(START)!=1 or src.count(END)!=1:
        raise ValueError("RED_REAL_SOURCE_SWEEP_FILTER_DRIFT")
    body=START+src.split(START,1)[1].split(END,1)[0]+"\nend"
    if body.count("table.insert(ignore,pilotCharacter)") != 1:
        raise ValueError("RED_SERVER_SEATED_PILOT_FILTER_MISSING")
    if "local exclude=vehicleSweepExclusions(\n      craft,water,offshoreWater,hum.Parent)" not in src:
        raise ValueError("RED_FILTER_NOT_WIRED_TO_ACTUAL_SEATED_HUMANOID")
    if "elseif hum and driver==v.owner then" not in src:
        raise ValueError("RED_SERVER_PILOT_OWNERSHIP_AUTHORITY_DRIFT")
    if "params.RespectCanCollide=true" not in src or "Workspace:Blockcast" not in src:
        raise ValueError("RED_SOLID_COLLISION_AUTHORITY_REMOVED")
    return body

def generate(out:Path,mutant:Path)->None:
    body=extract(SOURCE.read_text())
    out.write_text(PRELUDE+body+TAIL)
    mutant.write_text(PRELUDE+
       body.replace("table.insert(ignore,pilotCharacter)","local dropped=pilotCharacter",1)
       +TAIL)
    print("GQ8_LSS_NATIVE_REAL_HELPER_AND_MUTANT_GENERATED")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--mutant",type=Path,required=True)
    args=ap.parse_args()
    generate(args.out,args.mutant)

if __name__=="__main__":
    main()
