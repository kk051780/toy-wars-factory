#!/usr/bin/env python3
"""Execute actual authored StudioSoloGateRules.luau with pinned native Luau CLI."""
from pathlib import Path
import argparse
ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/"src/StudioSoloGateRules.luau").read_text("utf-8")
TESTS=r'''
local count=0
local function eq(a,b)
    assert(a==b,"SOLO_POLICY_NATIVE_MISMATCH "..tostring(a).." vs "..tostring(b))
    count+=1
end
-- solo practice: only exactly one authenticated member in a Studio process.
eq(Solo.isPractice(true,1,1,0),true)
eq(Solo.isPractice(true,1,0,1),true)
eq(Solo.isPractice(false,1,1,0),false)
eq(Solo.isPractice(false,1,0,1),false)
eq(Solo.isPractice(true,1,0,0),false)
eq(Solo.isPractice(true,2,1,1),false)
eq(Solo.isPractice(true,1,1,1),false)
eq(Solo.isPractice(true,1,2,0),false)
eq(Solo.isPractice(true,0,0,0),false)
eq(Solo.isPractice(true,1.5,1,0),false)
eq(Solo.isPractice(true,1,0/0,0),false)
eq(Solo.isPractice(true,1,1,math.huge),false)
eq(Solo.isPractice("true",1,1,0),false)
-- real 2-team matches use original Config.MinPlayers unchanged.
eq(Solo.canStart(false,2,2,1,1),true)
eq(Solo.canStart(true,2,2,1,1),true)
eq(Solo.canStart(false,3,2,2,1),true)
eq(Solo.canStart(false,1,2,1,0),false)
eq(Solo.canStart(true,1,2,1,0),true)
eq(Solo.canStart(true,1,2,0,1),true)
eq(Solo.canStart(true,2,2,2,0),false)
eq(Solo.canStart(false,2,2,2,0),false)
eq(Solo.canStart(true,0,2,0,0),false)
eq(Solo.canStart(true,2,2,0,2),false)
eq(Solo.canStart(true,2,2,1,0),false)
eq(Solo.canStart(true,1,2,0,0),false)
eq(Solo.canStart(true,0/0,2,1,0),false)
eq(Solo.canStart(true,1,math.huge,1,0),false)
eq(Solo.canStart(true,-1,2,1,0),false)
-- when owner plays solo, the absent RED/BLUE does not instantly end match.
eq(Solo.allowTeamEmptyResult(true,1,1,0),false)
eq(Solo.allowTeamEmptyResult(true,1,0,1),false)
eq(Solo.allowTeamEmptyResult(false,1,1,0),true)
eq(Solo.allowTeamEmptyResult(true,2,1,1),true)
eq(Solo.allowTeamEmptyResult(true,2,2,0),true)
eq(Solo.allowTeamEmptyResult(true,0,0,0),true)
assert(count==34,"EXPECTED_34_ASSERTIONS got "..tostring(count))
print("P0D_S2_STUDIO_SOLO_34_NATIVE_ASSERTIONS_PASS")
'''
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--write",required=True,type=Path)
    args=p.parse_args()
    text="local Solo=(function()\n"+SOURCE+"\nend)()\n"+TESTS
    args.write.write_text(text,encoding="utf-8")
    print("SOLO_NATIVE_SOURCE_REAL_MODULE_GENERATED")
if __name__=="__main__":main()
