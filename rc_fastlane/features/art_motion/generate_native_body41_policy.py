#!/usr/bin/env python3
"""Run the REAL 41-part client-motion source under pinned native Luau.

This runs source-extracted watchedParts + movementFor, not a rewritten
mock algorithm; the standalone CFrame *algebra stub* is visualization math
only, and cannot claim Studio/Android render performance or real aesthetics.
"""
from __future__ import annotations
import argparse
from pathlib import Path

SOURCE=Path(__file__).with_name("NeutralMotion.client.luau")
def section(src: str, tag: str) -> str:
    start=f"-- BEGIN_NATIVE_MOTION_{tag}"
    end=f"-- END_NATIVE_MOTION_{tag}"
    if src.count(start)!=1 or src.count(end)!=1:
        raise RuntimeError("ART41_NATIVE_SECTION_NOT_UNIQUE_"+tag)
    body=src.split(start,1)[1].split("\n",1)[1].split(end,1)[0]
    return body.strip()

def generate(out: Path) -> None:
    src=SOURCE.read_text("utf8")
    names=section(src,"ALL_41_ART")
    motion=section(src,"ACTUAL_BODY_MOVEMENT")
    if not names.startswith("local watchedParts = {") or not motion.startswith("local function movementFor("):
        raise RuntimeError("ART41_NATIVE_AUTHOR_SOURCE_NOT_MATCHED")
    tests=r'''
-- A minimal transparent CFrame value algebra; asserts all 41 authored parts
-- actually invoke the true authored movement function at idle, walking, hit,
-- KO without type errors. This is native Luau behavior, NOT engine physics.
local cframeMt={}
cframeMt.__mul=function(a,b)
    return setmetatable({n=a.n+b.n},cframeMt)
end
CFrame={}
local function proxy(...)
    local total=0
    for i=1,select("#",...) do
        local x=select(i,...)
        assert(type(x)=="number" and x==x,"NONNUMERIC_MOVEMENT")
        total+=math.abs(x)
    end
    return setmetatable({n=total},cframeMt)
end
CFrame.new=proxy
CFrame.Angles=proxy
'''
    # Put proxy before the authored art and movement sections, exercise them
    # in a distinct second section without touching the authored body.
    cases=r'''
local counts={KNIGHT=10,WRAITH=10,BRUTE=11,ELITE=10}
local total=0
local changed=0
local sample={}
for kind,parts in pairs(watchedParts) do
    local count=0
    for _,name in ipairs(parts) do
        count+=1
        total+=1
        assert(name:sub(1,4)=="ART_","UNEXPECTED_41_ART_NAME")
        assert(sample[name]==nil,"DUPLICATE_ART")
        sample[name]=true
        local idle=movementFor(kind,name,0,1.31,100,100)
        local walk=movementFor(kind,name,12,1.31,100,100)
        local hit=movementFor(kind,name,12,1.31,.12,100)
        local ko=movementFor(kind,name,12,1.31,100,.3)
        assert(type(idle)=="table" and type(idle.n)=="number")
        assert(type(walk)=="table" and type(walk.n)=="number")
        assert(type(hit)=="table" and type(hit.n)=="number")
        assert(type(ko)=="table" and type(ko.n)=="number")
        assert(idle.n>=0 and walk.n>=0 and hit.n>=0 and ko.n>=0)
        if walk.n~=hit.n or walk.n~=ko.n then changed+=1 end
    end
    assert(count==counts[kind],"MISSING_FULL_ART_FOR_"..kind)
end
assert(total==41,"NO_FULL_41_ART")
-- Live scenario: 3 knights*10 + 3 wraiths*10 + 2 brutes*11 +
-- 1 elite*10 => 92 client-local mirrored parts, under maximum 104.
local activeBudget=3*counts.KNIGHT+3*counts.WRAITH+
    2*counts.BRUTE+counts.ELITE
assert(activeBudget==92 and activeBudget<=104,"FULL_ART_PART_BUDGET")
assert(changed>=20,"COMBAT_ART_MOTION_NOT_RESPONSIVE")
print("P0D_FB015_41_PART_REAL_NATIVE_MOTION_PASS",total,activeBudget,changed)
'''
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text("--!nocheck\n"+tests+"\n"+names+"\n"+motion+"\n"+cases,"utf8")
    print("P0D_FULL41_SOURCE_EXTRACTION_PASS")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    generate(p.parse_args().out)
