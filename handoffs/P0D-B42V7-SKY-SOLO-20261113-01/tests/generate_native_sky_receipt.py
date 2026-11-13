#!/usr/bin/env python3
"""Extract exactly the ACTUAL diagnostic's pure Luau predicates, test in pinned native VM.
This verifies logic but NOT Roblox Studio, physics, a real walk, or human FUN.
"""
import argparse
import itertools
import json
from pathlib import Path

START="-- SOURCE_QA_NATIVE_BEGIN"
END="-- SOURCE_QA_NATIVE_END"
p=argparse.ArgumentParser()
p.add_argument("--source",type=Path,required=True)
p.add_argument("--write",type=Path,required=True)
args=p.parse_args()
text=args.source.read_text("utf-8")
assert text.count(START)==text.count(END)==1,"NATIVE_EXTRACT_SOURCE_DRIFT"
body=text.split(START,1)[1].split(END,1)[0]
assert body.count("local function qualifiesSkyScore(")==1
assert body.count("local function invalidatesSkyRoute(")==1
assert 'previousCarry==skyEgg' in body and 'population==1' in body
assert 'currentCarry~=skyEgg' in body and 'phase~="ACTIVE"' in body
assert "if not RunService:IsStudio() then return end" in text
q=lambda v:"true" if v is True else "false" if v is False else json.dumps(v)
lines=["--!strict","-- Exact real production H1 client helper source under native Luau.",""]
lines.extend(body.strip().splitlines())
lines.append("local passed=0")
count=0
for vals in itertools.product((False,True),("","BLUE","RED"),
                              ("","BLUE","RED"),("","BLUE","RED"),
                              (0,1,2),(False,True),(False,True)):
    score,now,prev,egg,pop,char,roundOK=vals
    expected=score and now=="" and prev==egg and egg!="" and pop==1 and char and roundOK
    expr="qualifiesSkyScore("+",".join(map(q,vals))+")"
    lines.append(f'assert({expr}=={q(expected)}, "QUALIFY_{count}")')
    lines.append("passed+=1")
    count+=1
for vals in itertools.product((False,True),(False,True),
                              ("","BLUE","RED"),("","BLUE","RED"),
                              (False,True),("ACTIVE","RESULTS")):
    visited,complete,now,egg,char,phase=vals
    expected=visited and not complete and (now!=egg or not char or phase!="ACTIVE")
    expr="invalidatesSkyRoute("+",".join(map(q,vals))+")"
    lines.append(f'assert({expr}=={q(expected)}, "INVALIDATE_{count}")')
    lines.append("passed+=1")
    count+=1
assert count==792, count
lines.append('assert(passed==792)')
lines.append('print("P0D_SKY_RECEIPT_NATIVE_792_ASSERTIONS_PASS")')
args.write.write_text("\n".join(lines)+"\n","utf-8")
print("P0D_EXACT_DIAGNOSTIC_LUAU_PREDICATE_GENERATED",count)
