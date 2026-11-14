#!/usr/bin/env python3
"""Run exact P0D #388 Luau hit/replay source in pinned native interpreter.

The extracts are taken from the authored client LocalScript, not hand-copied
policy pseudocode; missing/duplicate region anchors are fatal.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
SOURCE=HERE/"NeutralMotion.client.luau"

def extract(text: str, label: str) -> str:
    start=f"-- BEGIN_NATIVE_MOTION_{label}"
    end=f"-- END_NATIVE_MOTION_{label}"
    if text.count(start)!=1 or text.count(end)!=1:
        raise RuntimeError("P0D_MOTION_POLICY_ANCHORS_MISSING_OR_DUPLICATED_"+label)
    block=text.split(start,1)[1].split("\n",1)[1].split(end,1)[0]
    if "local function " not in block:
        raise RuntimeError("P0D_MOTION_POLICY_FUNCTION_MISSING_"+label)
    return block

def write(out: Path) -> None:
    text=SOURCE.read_text("utf8")
    replay=extract(text,"PENDING_REPLAY")
    policy=extract(text,"CONFIRMED_HIT")
    tests=r'''
local active={}
local function lookup(id) return active[id] end
-- A server-confirmed hit can arrive before #374 art exists.
assert(applyConfirmedHit(3,false,1,1,10,lookup)==true)
assert(pendingHits[3] ~= nil and pendingHits[3].at == 10)
assert(lastHitSerial[3] == 1)
-- Repeated notification must not duplicate or age-reset a single hit.
assert(applyConfirmedHit(3,false,1,1,10.01,lookup)==false)
assert(pendingHits[3].at == 10)
local e3={hitAt=-100,koAt=-100}
active[3]=e3
assert(replayPendingHit(e3,3,10.1)==true)
assert(e3.hitAt==10 and e3.koAt==-100)
assert(pendingHits[3]==nil)
-- New serial during a still-active popup updates the real hit timestamp.
assert(applyConfirmedHit(3,false,2,1,10.12,lookup)==true)
assert(e3.hitAt==10.12)
assert(applyConfirmedHit(3,true,3,1,10.15,lookup)==true)
assert(e3.koAt==10.15)
assert(applyConfirmedHit(3,false,2,1,10.16,lookup)==false)
-- A KO queued before art replication is replayed with original timestamp.
assert(applyConfirmedHit(9,true,1,1,10.2,lookup)==true)
local e9={hitAt=-100,koAt=-100}
active[9]=e9
assert(replayPendingHit(e9,9,10.3)==true)
assert(e9.hitAt==10.2 and e9.koAt==10.2)
-- Old queued cues are not falsely "new" after streaming delay.
assert(applyConfirmedHit(8,true,1,1,10.4,lookup)==true)
local e8={hitAt=-100,koAt=-100}
assert(replayPendingHit(e8,8,11.2)==false)
assert(e8.hitAt==-100 and e8.koAt==-100)
-- Higher round clears old serial and pending signals.
assert(applyConfirmedHit(7,true,2,1,11.3,lookup)==true)
assert(pendingHits[7]~=nil)
assert(applyConfirmedHit(4,false,1,2,11.35,lookup)==true)
assert(pendingHits[7]==nil)
assert(applyConfirmedHit(4,false,99,1,11.4,lookup)==false)
-- Invalid or unsupported IDs/rounds must never be turned into damage claims.
assert(applyConfirmedHit(0,false,1,2,11.4,lookup)==false)
assert(applyConfirmedHit(10,false,1,2,11.4,lookup)==false)
assert(applyConfirmedHit(4,false,1.1,2,11.4,lookup)==false)
assert(applyConfirmedHit(4,"KO",2,2,11.4,lookup)==false)
assert(applyConfirmedHit(4,false,2,2.5,11.4,lookup)==false)
assert(applyConfirmedHit(4,false,2,2,11.4,lookup)==true)
assert(lastHitSerial[4]==2)
print("P0D_FB015_ACTUAL_MOTION_NATIVE_POLICY_PASS")
'''
    qa='''--!nocheck
-- Authored exact Luau function body extraction, NOT rewritten test policy.
local lastRound=nil
local lastHitSerial={}
local pendingHits={}
'''+replay+"\n"+policy+"\n"+tests
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(qa,"utf8")
    print("P0D_MOTION_NATIVE_EXACT_FUNCTIONS_EXTRACTED",len(re.findall(r"\bassert\(",tests)))

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    write(parser.parse_args().out)
