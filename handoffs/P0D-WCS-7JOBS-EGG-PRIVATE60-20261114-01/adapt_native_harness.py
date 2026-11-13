#!/usr/bin/env python3
"""Adjust AUTHOR's native30 test fixture for stricter Studio opt-in behavior.

Never changes the actual Game policy or author script. The same actual Game
function is extracted by the original pinned author harness generator.
Adds a real missing-flag negative after the preserved 30 cases.
"""
from __future__ import annotations
import argparse
from pathlib import Path

def adapt(src: Path) -> None:
    source=src.read_text("utf8")
    old='    serverFlag=nil\n    workspace.blocked=false'
    replacement='    serverFlag={IsA=function(_,kind) return kind=="BoolValue" end,Value=true}\n    workspace.blocked=false'
    assert source.count(old)==1,"AUTHOR_FIXTURE_RESET_ANCHOR_DRIFT"
    assert 'return flag ~= nil and flag:IsA("BoolValue") and flag.Value == true' in source,"SOURCE_MUST_EXPLICITLY_OPT_IN"
    assert 'P0D_EGG_RELAY_ACTUAL_GAME_NATIVE_30_CASES_PASS' in source
    source=source.replace(old,replacement,1)
    # Preserve the exact 30 original source-based test functions, and add an
    # explicit missing-flag DENY case *after* their original 30-case assertion.
    marker='assert(caseCount==30,"EXPECTED_30_CASES: "..tostring(caseCount))'
    assert source.count(marker)==1,"AUTHOR_EXPECTED_30_CASE_ANCHOR_DRIFT"
    additional=(
        marker+"\n"
        "reset()\n"
        "serverFlag=nil -- absence must not grant relay privilege\n"
        "local prior = broadcasts\n"
        "applyClassicEggRelay(actor,request())\n"
        "assert(broadcasts==prior and match.eggOwners.BLUE==actor and carry[actor]==\"BLUE\","
        "\"MISSING_STUDIO_FLAG_MUST_DISABLE_RELAY\")\n"
        "print(\"P0D_EGG_CLASSIC_MISSING_FLAG_FAIL_CLOSED_NATIVE_PASS\")"
    )
    source=source.replace(marker,additional,1)
    src.write_text(source,"utf8")
    print("P0D_ACTUAL_GAME_NATIVE_30_PRESERVED_PLUS_MISSING_FLAG_NEGATIVE_GENERATED")

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--fixture",required=True,type=Path)
    adapt(a.parse_args().fixture)
