#!/usr/bin/env python3
"""Execute the exact authored pure Luau policy under the official open-source Luau VM."""
import argparse
from pathlib import Path
HERE=Path(__file__).resolve().parent
def make(out):
    original=(HERE/"EGGRUMBLE_CarrierTellPolicy.luau").read_text(encoding="utf-8")
    anchor="\nreturn Policy\n"
    assert original.count(anchor)==1
    tests=r'''
local n=0
local function check(msg,v,w)
 n += 1
 assert(v==w, msg .. " expected="..tostring(w).." got="..tostring(v))
end
local c={alive=true,heldEggs=1}
check("1 egg alive",Policy.shouldShow("ACTIVE",nil,c,true),true)
c.heldEggs=2;check("2 eggs alive",Policy.shouldShow("ACTIVE",nil,c,true),true)
c.heldEggs=3;check("3 eggs alive",Policy.shouldShow("ACTIVE",nil,c,true),true)
check("cannot reveal lobby",Policy.shouldShow("LOBBY",nil,c,true),false)
check("cannot reveal finished",Policy.shouldShow("FINISHED",nil,c,true),false)
check("cannot reveal abandoned",Policy.shouldShow("ABANDONED",nil,c,true),false)
check("cannot reveal after winner",Policy.shouldShow("ACTIVE","RED",c,true),false)
check("cannot reveal after avatar death",Policy.shouldShow("ACTIVE",nil,c,false),false)
c.alive=false;check("castle fallen",Policy.shouldShow("ACTIVE",nil,c,true),false);c.alive=true
c.heldEggs=0;check("empty carrier",Policy.shouldShow("ACTIVE",nil,c,true),false)
c.heldEggs=4;check("invalid overlimit",Policy.shouldShow("ACTIVE",nil,c,true),false)
c.heldEggs=-1;check("invalid negative",Policy.shouldShow("ACTIVE",nil,c,true),false)
c.heldEggs=1.5;check("invalid fractional",Policy.shouldShow("ACTIVE",nil,c,true),false)
c.heldEggs=0/0;check("invalid NaN",Policy.shouldShow("ACTIVE",nil,c,true),false)
c.heldEggs=nil;check("missing count",Policy.shouldShow("ACTIVE",nil,c,true),false)
check("missing castle",Policy.shouldShow("ACTIVE",nil,nil,true),false)
check("string castle",Policy.shouldShow("ACTIVE",nil,"fake",true),false)
check("caption",Policy.caption(2),"🥚×2")
print("NATIVE_CARRIER_WORLD_TELL_POLICY_PASS checks="..tostring(n))
'''
    out.write_text(original.replace(anchor,"\n",1)+tests,encoding="utf-8")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    make(a.out)
