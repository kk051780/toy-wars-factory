#!/usr/bin/env python3
"""Extract the REAL current optional32 server's KO+combo milestone predicate.

Build one Luau executable and a syntax-valid negative mutant (dedup removed).
The native code being exercised comes from the actual shipping-candidate source,
never a hand-copied alternative helper.
"""
from __future__ import annotations
import argparse
from pathlib import Path

DIR=Path(__file__).resolve().parent
SOURCE=DIR/"EGGRUMBLE_LandSeaSkyTraversal.server.luau"
START=" local function musouConfirmedMilestone(ko,combo,koAt,comboAt,shown,now)\n"
END="\n end\n local lastNeutralCount={}"

TESTS=r'''
local cases=0
local function check(name,value,expected)
 cases+=1
 assert(value==expected, "MUSOU_ATTR_ORDER_FAIL_"..name)
end
-- Two legitimate server update orders on a real twelfth neutral KO.
check("ko_then_combo",musouConfirmedMilestone(12,12,10,10.1,nil,10.1),true)
check("combo_then_ko",musouConfirmedMilestone(12,12,10.1,10,nil,10.1),true)
-- Both original attributes MUST have actually advanced.
check("ko_only",musouConfirmedMilestone(12,12,10,nil,nil,10),false)
check("combo_only",musouConfirmedMilestone(12,12,nil,10,nil,10),false)
check("stale_ko",musouConfirmedMilestone(12,12,7,10,nil,10),false)
check("stale_combo",musouConfirmedMilestone(12,12,10,7,nil,10),false)
check("old_event",musouConfirmedMilestone(12,12,3,3,nil,4),false)
-- A second attribute signal for one milestone MUST NOT duplicate a wave.
check("repeat_same_combo",musouConfirmedMilestone(12,12,10,10.1,12,10.2),false)
-- Genuine later streaks can trigger, including another 12 after round reset.
check("later_24",musouConfirmedMilestone(24,24,14,14.2,12,14.2),true)
check("reset_12",musouConfirmedMilestone(24,12,14,14.2,nil,14.2),true)
check("bad_11",musouConfirmedMilestone(12,11,10,10.1,nil,10.1),false)
check("bad_13",musouConfirmedMilestone(13,13,10,10.1,nil,10.1),false)
check("combo_exceeds_KO",musouConfirmedMilestone(11,12,10,10.1,nil,10.1),false)
check("no_combo",musouConfirmedMilestone(12,0,10,10.1,nil,10.1),false)
check("non_number_KO",musouConfirmedMilestone("12",12,10,10.1,nil,10.1),false)
check("non_number_combo",musouConfirmedMilestone(12,"12",10,10.1,nil,10.1),false)
check("negative_KO",musouConfirmedMilestone(-1,12,10,10.1,nil,10.1),false)
print("GQ8_LSS_ACTUAL_SERVER_MUSOU_17_NATIVE_CASES_PASS")
'''

def make(out:Path,mutant:Path)->None:
    source=SOURCE.read_text(encoding="utf-8")
    if source.count(START)!=1 or source.count(END)!=1:
        raise ValueError("RED_ACTUAL_MUSOU_PREDICATE_NOT_UNIQUE")
    helper=START+source.split(START,1)[1].split(END,1)[0]+"\n end"
    if helper.count("or shown==combo")!=1:
        raise ValueError("RED_REAL_MUSOU_DEDUP_MISSING")
    if source.count('player:GetAttributeChangedSignal("EGGRUMBLE_Combo")')!=1:
        raise ValueError("RED_MISSING_COMBO_WATCHER")
    if source.count('player:GetAttributeChangedSignal("EGGRUMBLE_NeutralKOs")')!=1:
        raise ValueError("RED_MISSING_REAL_KO_WATCHER")
    if "lastKOAdvanceAt[userId]=now" not in source or "lastComboAdvanceAt[userId]=now" not in source:
        raise ValueError("RED_MISSING_ACTUAL_SERVER_ADVANCE_EVIDENCE")
    prelude="local MUSOU_COMBO_STEP=12\nlocal MUSOU_ATTRIBUTE_SYNC_SECONDS=0.75\n"
    full=prelude+helper+TESTS
    out.parent.mkdir(parents=True,exist_ok=True)
    mutant.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(full,encoding="utf-8")
    mutant.write_text(prelude+helper.replace("or shown==combo","or false",1)+TESTS,
                      encoding="utf-8")
    print("GQ8_LSS_EXTRACTED_MUSOU_LUAU_NATIVE_AND_MUTANT_READY")

def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--mutant",required=True,type=Path)
    a=p.parse_args()
    make(a.out,a.mutant)

if __name__=="__main__":
    main()
