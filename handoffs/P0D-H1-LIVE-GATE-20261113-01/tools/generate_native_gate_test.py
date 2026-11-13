#!/usr/bin/env python3
"""Genuine Luau native runtime matrix: default production deny, Studio allow, exact-ID simulate.
The enabled module variant is in a /tmp TEST HARNESS ONLY and cannot be shipped by the 29-game build.
"""
from pathlib import Path
import argparse,hashlib

HERE=Path(__file__).resolve()
OWN=HERE.parents[1]
SOURCE=OWN/"inputs/H1ReleaseGate.luau"
BLOB="59eb9aa6e3f41b52b6bfb5e23147ae42dc451b57"

def blob(b):
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def make(out):
    b=SOURCE.read_bytes()
    assert blob(b)==BLOB,(blob(b),BLOB)
    original=b.decode("utf-8")
    assert original.count("local LIVE_ENABLE = false")==1
    assert original.count("local APPROVED_GAME_ID = 0")==1
    assert original.count("local APPROVED_PLACE_ID = 0")==1
    approved=original.replace("local LIVE_ENABLE = false","local LIVE_ENABLE = true")
    approved=approved.replace("local APPROVED_GAME_ID = 0","local APPROVED_GAME_ID = 140102")
    approved=approved.replace("local APPROVED_PLACE_ID = 0","local APPROVED_PLACE_ID = 703914")
    denied=original.replace("local LIVE_ENABLE = false","local LIVE_ENABLE = true")
    assert "local APPROVED_GAME_ID = 0" in denied
    harness=r'''
local count=0
local function check(got,expected,label)
    count+=1
    assert(got==expected,"H1_LIVE_RELEASE_GATE_TEST_FAIL:"..label..
                        " expected="..tostring(expected).." got="..tostring(got))
end
for _,a in ipairs({{1,2},{0,0},{nil,nil},{-1,-1},{math.huge,math.huge}}) do
    check(Disabled.canRun(true,a[1],a[2]),true,"STUDIO_ALWAYS_WORKS")
    check(Disabled.canRun(false,a[1],a[2]),false,"PROD_DEFAULT_DENIED")
    check(MissingIds.canRun(false,a[1],a[2]),false,"APPROVAL_WITHOUT_IDS_DENIED")
end
for _,a in ipairs({{false,140102,703914,true,"MATCH"},
 {false,140102,703915,false,"WRONG_PLACE"},
 {false,140103,703914,false,"WRONG_UNIVERSE"},
 {false,0,703914,false,"ZERO_GAME"},
 {false,140102,0,false,"ZERO_PLACE"},
 {false,-10,703914,false,"NEG_GAME"},
 {false,140102,-1,false,"NEG_PLACE"},
 {false,140102.5,703914,false,"FRACTION_GAME"},
 {false,140102,703914.1,false,"FRACTION_PLACE"},
 {false,math.huge,703914,false,"INFINITE_GAME"},
 {false,140102,math.huge,false,"INFINITE_PLACE"},
 {false,"140102",703914,false,"STRING_GAME"},
 {false,140102,"703914",false,"STRING_PLACE"},
 {false,nil,703914,false,"NIL_GAME"},
 {false,140102,nil,false,"NIL_PLACE"},
 {nil,140102,703914,false,"NIL_STUDIO"},
 {"true",140102,703914,false,"STRING_STUDIO"},
 {1,140102,703914,false,"NUMBER_STUDIO"},
 {true,nil,nil,true,"STUDIO_WITHOUT_GAME_ID"}}) do
    check(Approved.canRun(a[1],a[2],a[3]),a[4],a[5])
end
check(Disabled.canRun(false,140102,703914),false,"LIVE_OFF_EVEN_MATCHING_IDS")
check(Approved.canRun(false,703914,140102),false,"REVERSED_IDS_DENIED")
check(Approved.canRun(false,1/0,703914),false,"NUMERIC_OVERFLOW_DENIED")
check(Approved.canRun(false,140102,703914.0001),false,"EXACT_MATCH_ONLY")
print("P0D_H1_RELEASE_GATE_REAL_NATIVE_LUAU_PASS_"..tostring(count))
'''
    output="local Disabled=(function()\n"+original+"\nend)()\n"
    output+="local MissingIds=(function()\n"+denied+"\nend)()\n"
    output+="local Approved=(function()\n"+approved+"\nend)()\n"
    output+=harness
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(output,encoding="utf-8")
    print("TEST_ONLY_LUAU_APPROVED_ID_VARIANT_NOT_MOUNTED_TO_GAME",str(out))
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--write",type=Path,required=True)
    a=p.parse_args()
    make(a.write)
