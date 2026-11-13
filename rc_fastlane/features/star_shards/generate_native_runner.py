#!/usr/bin/env python3
"""Extract the ACTUAL assembled source's pure per-user six-shard policy for native Luau tests.

No reimplementation: the marker section is copied byte-for-byte from Game source.
"""
from __future__ import annotations
import argparse
from pathlib import Path

BEGIN="-- BEGIN_P0D_STAR_SHARDS_POLICY"
END="-- END_P0D_STAR_SHARDS_POLICY"
SUFFIX=r'''
local count=0
local function check(map,id,accepted,total,complete)
    local got,n,done=awardShard(map,id)
    assert(got==accepted, "accepted case "..tostring(count+1))
    assert(n==total, "count case "..tostring(count+1)..": "..tostring(n).." expected "..tostring(total))
    assert(done==complete, "complete case "..tostring(count+1))
    count+=1
end
local p={}
check(p,0,false,0,false)
check(p,-1,false,0,false)
check(p,7,false,0,false)
check(p,1.5,false,0,false)
check(p,"1",false,0,false)
check(p,nil,false,0,false)
check(p,math.huge,false,0,false)
check(p,1,true,1,false)
check(p,1,false,1,false)
check(p,2,true,2,false)
check(p,3,true,3,false)
check(p,4,true,4,false)
check(p,5,true,5,false)
check(p,6,true,6,true)
check(p,6,false,6,true)
check(p,7,false,6,true)
check(nil,3,false,0,false)
local other={}
check(other,6,true,1,false)
check(other,6,false,1,false)
local junk={foo=true}
check(junk,1,true,1,false)
local randomOrder={}
check(randomOrder,4,true,1,false)
check(randomOrder,4,false,1,false)
assert(count==22)
print("P0D_STAR_SHARDS_REAL_SOURCE_NATIVE_22_POLICY_CASES_PASS")
'''

def make(script:Path,out:Path):
    txt=script.read_text("utf8")
    assert txt.count(BEGIN)==1 and txt.count(END)==1,"SHARDS_POLICY_MARKERS_NOT_SINGLE"
    assert txt.index(BEGIN)<txt.index(END)
    pure=txt.split(BEGIN,1)[1].split(END,1)[0]
    assert "local function awardShard(oldMap, id)" in pure
    assert pure.count("local TOTAL=6")==1
    assert 'player:SetAttribute("P0D_StarShardCount",count)' in txt
    assert "GetAttribute(\"P0D_RC_ENABLE_STAR_SHARDS_V1\")~=true" in txt
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text("-- THIS POLICY IS SOURCE EXTRACTED FROM COMBINED GAME\n"+pure+"\n"+SUFFIX,"utf8")
    print("P0D_STAR_SHARDS_REAL_SOURCE_POLICY_EXTRACTED_PASS")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--script",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    make(a.script,a.out)
