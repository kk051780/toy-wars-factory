#!/usr/bin/env python3
"""Adapt the immutable PR296 extracted-Game native tests to safe default-OFF.
Changes ONLY the generated test stubs; never rewrites extracted gameplay logic.
"""
from pathlib import Path
import argparse
p=argparse.ArgumentParser()
p.add_argument("--input",required=True,type=Path)
p.add_argument("--output",required=True,type=Path)
a=p.parse_args()
s=a.input.read_text("utf8")
expect=[
    ('    serverFlag=nil\n    workspace.blocked=false',
     '    serverFlag={Value=true,IsA=function(_,name) return name=="BoolValue" end}\n    workspace.blocked=false'),
    ('runCase("not Studio cannot pass",function(p) isStudio=false end,false)',
     'runCase("missing Studio BoolValue must remain OFF",function(p) serverFlag=nil end,false)\n'
     'runCase("not Studio cannot pass",function(p) isStudio=false end,false)'),
    ('P0D_EGG_RELAY_ACTUAL_GAME_NATIVE_30_CASES_PASS',
     'P0D_WCS_JOBS_RELAY_REAL_GAME_NATIVE_31_CASES_PASS'),
    ('assert(caseCount==30,"EXPECTED_30_CASES: "',
     'assert(caseCount==31,"EXPECTED_31_CASES: "')
]
for old,new in expect:
    assert s.count(old)==1,("HARNESS_FORMAT_DRIFT",old[:80],s.count(old))
    s=s.replace(old,new,1)
assert s.count("local function applyClassicEggRelay(player: Player, data)")==1
assert s.count("local function classicRelayEnabled(): boolean")==1
assert 'return flag ~= nil and (flag:IsA("BoolValue") and flag.Value == true)' in s
assert s.count('match.eggOwners[egg]=target')==1
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(s,"utf8")
print("P0D_ACTUAL_GAME_NATIVE_HARNESS_SAFE_OPTIN_GENERATED_PASS")
