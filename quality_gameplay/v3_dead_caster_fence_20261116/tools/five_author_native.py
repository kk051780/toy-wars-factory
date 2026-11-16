#!/usr/bin/env python3
"""Run real source-derived seven-role execute() 84-state Luau negative test
on the five-author combined script. The deliberate dead-caster mutant MUST fail.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from compose_five_author import apply_to_combined, ENTRY, REPLACEMENT, sha256, ORIGINAL_529_FOUR_SHA256

# Identical 84-case runtime harness as original-author GQ530 test.
from make_native_cast_fence_harness import PREAMBLE, CASES

def make(source: str, mutant: bool) -> str:
    if source.count(REPLACEMENT)!=1:
        raise ValueError("RED_FIVE_AUTHOR_PATCH_NOT_UNIQUE")
    if mutant:
        source=source.replace(REPLACEMENT,ENTRY,1)
        if sha256(source)!=ORIGINAL_529_FOUR_SHA256:
            raise ValueError("RED_FOUR_AUTHOR_ROLLBACK_DIFF")
    else:
        if apply_to_combined(source.replace(REPLACEMENT,ENTRY,1))!=source:
            raise ValueError("RED_FIVE_AUTHOR_ROUNDTRIP")
    first="local function execute(session:any,p:Player,role:string,slot:string)"
    last="\nfunction HeroCombat.roleOrder()"
    if source.count(first)!=1 or source.count(last)!=1:
        raise ValueError("RED_EXECUTE_UNIQUE_ANCHOR")
    body=source[source.index(first):source.index(last)]
    for marker in ('elseif role=="MAGE"', 'elseif role=="TRAPPER"',
                   'elseif role=="BEAST"', 'elseif role=="ZOMBIE"',
                   "StatusTickFence.canTick(", "humanCombatTargetable("):
        # Markers in the complete single-source composition, not necessarily execute body.
        if marker not in source:
            raise ValueError("RED_MISSING_ORIGINAL_FOUR_AUTHOR_PATCH: "+marker)
    return PREAMBLE+"\n"+body+"\n"+CASES

def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--combined",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--mutant",action="store_true")
    a=p.parse_args()
    s=make(a.combined.read_text(encoding="utf-8"),a.mutant)
    a.out.write_text(s,encoding="utf-8")
    print("FIVE_AUTHOR_NATIVE84_SOURCE_READY", "OLD_MUTANT_SHOULD_FAIL" if a.mutant else "FIXED_SHOULD_PASS")

if __name__=="__main__":
    main()
