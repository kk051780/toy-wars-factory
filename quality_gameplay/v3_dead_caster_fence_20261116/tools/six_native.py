#!/usr/bin/env python3
"""Real 7-role execute extracted from one 6-author Combat (84 states).
Only the #530 guard is mutated; #535 member helper is original author source.
"""
import argparse
import importlib.util
from pathlib import Path
from compose_six_author import MEMBER, import_author, MEMBER_BLOB, REPLACEMENT, ENTRY

from make_native_cast_fence_harness import PREAMBLE, CASES

def generated(source:str,negative_mutant:bool):
    g535=import_author(MEMBER,"six_member_author_535",MEMBER_BLOB)
    if source.count(g535.HELPER)!=1:
        raise ValueError("RED_535_HELPER_MISSING")
    if source.count(REPLACEMENT)!=1:
        raise ValueError("RED_530_GUARD_MISSING")
    if negative_mutant:
        source=source.replace(REPLACEMENT,ENTRY,1)
    left="local function execute(session:any,p:Player,role:string,slot:string)"
    right="\nfunction HeroCombat.roleOrder()"
    if source.count(left)!=1 or source.count(right)!=1:
        raise ValueError("RED_SIX_EXECUTE_NOT_UNIQUE")
    chunk=source[source.index(left):source.index(right)]
    if "currentHumanMember(session,p)" not in chunk:
        raise ValueError("RED_535_CASTER_MEMBER_CHECK_MISSING")
    # The original 84-state harness simulates current roster membership to isolate
    # the dead/downed guard. Real callback uses original #531 Host in separate test.
    cases=CASES.replace(
        "   called=0;lastByPlayer={};currentChar=char;currentHum=h",
        "   session.isCurrentHuman=function(_p) return true end\n"
        "   called=0;lastByPlayer={};currentChar=char;currentHum=h",
        1
    )
    if "session.isCurrentHuman=function(_p) return true end" not in cases:
        raise ValueError("RED_84_MEMBERSHIP_SETUP")
    return PREAMBLE+"\n"+g535.HELPER+"\n"+chunk+"\n"+cases

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--combat",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--mutant",action="store_true")
    a=p.parse_args()
    a.out.write_text(generated(a.combat.read_text(encoding="utf-8"),a.mutant),encoding="utf-8")
    print("GQ530_535_ACTUAL_SIX_AUTHOR_NATIVE_84_READY",a.mutant)

if __name__=="__main__":main()
