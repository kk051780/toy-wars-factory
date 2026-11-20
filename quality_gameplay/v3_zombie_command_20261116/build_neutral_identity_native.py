#!/usr/bin/env python3
"""Extract the ACTUAL original-author ZOMBIE neutral ID closure into native Luau.
Fails closed if the composer drifts or a name/index-based identity returns.
Tests source code under a real Luau binary, not copied production policy.
"""
from __future__ import annotations
import argparse
import importlib.util
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--composer",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    spec=importlib.util.spec_from_file_location("zombie_author",a.composer)
    module=importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    source=module.NEW_ZOMBIE
    start="   local neutralIds=setmetatable({}, {__mode=\"k\"})"
    end="   local function commanderSnapshot"
    assert source.count(start)==1 and source.count(end)==1
    s=source[source.index(start):source.index(end)]
    assert s.count("local function neutralTargetId(enemy:Model):string")==1
    assert "neutralIds[enemy]" in s
    assert "nextNeutralId+=1" in s
    assert 'id=neutralTargetId(enemy),kind="NEUTRAL"' in source
    assert 'id="N:"..tostring(enemy)' not in source
    assert 'id="N:"..tostring(n)' not in source
    assert 'session.isCurrentHuman(other)==true' in source
    assert "theirHum.Health>0" in source
    harness = (
        '--!strict\nlocal p={UserId=731}\n'
        +s
        +'''
local a=setmetatable({}, {__tostring=function() return "NeutralRaider" end})
local b=setmetatable({}, {__tostring=function() return "NeutralRaider" end})
local c=setmetatable({}, {__tostring=function() return "NeutralRaider" end})
assert(tostring(a)==tostring(b) and tostring(b)==tostring(c))
local ai=neutralTargetId(a)
local bi=neutralTargetId(b)
assert(ai~=(bi) and ai=="N:731:1" and bi=="N:731:2")
assert(neutralTargetId(a)==ai and neutralTargetId(b)==bi)
local reorder={b,a}
assert(neutralTargetId(reorder[1])==bi)
assert(neutralTargetId(reorder[2])==ai)
local ci=neutralTargetId(c)
assert(ci~=(ai) and ci~=(bi) and ci=="N:731:3")
-- Reclaimed/reordered enemy cannot impersonate another via a reused index/name.
assert(neutralTargetId(c)==ci and neutralTargetId(a)==ai)
assert(neutralTargetId(b)==bi)
print("GQ582_ACTUAL_NEUTRAL_INSTANCE_ID_NATIVE_PASS checks=12")
''')
    if a.out.exists():
        raise ValueError("RED_NATIVE_OUTPUT_EXISTS")
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(harness,encoding="utf8")
    print("GQ582_ACTUAL_NEUTRAL_ID_CLOSURE_EXTRACTED_PASS")

if __name__=="__main__":
    main()
