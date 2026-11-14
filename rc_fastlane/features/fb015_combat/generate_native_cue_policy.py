#!/usr/bin/env python3
"""Extract and execute the REAL client hit dedupe policy under native Luau.

CI must compile and run the extracted exact source, not a Python re-creation.
This still does not simulate Roblox networking, Studio scene or visual rendering.
"""
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "ArtCombatSlash.client.luau"
START = "-- BEGIN_ACTUAL_CUE_DEDUPE_POLICY"
END = "-- END_ACTUAL_CUE_DEDUPE_POLICY"

def compose(raw: str) -> str:
    if raw.count(START) != 1 or raw.count(END) != 1:
        raise RuntimeError("POLICY_SOURCE_BOUNDARY_MISSING_OR_DUPLICATED")
    fragment = raw.split(START, 1)[1].split("\n", 1)[1].split(END, 1)[0]
    required = ("local function acceptVisualCue(", "state.seen[serial]",
                "state.max=math.max(state.max,serial)",
                "serial<=state.max-16", "table.clear(lastByMob)",
                "if lastRound==nil then")
    for text in required:
        if text not in fragment:
            raise RuntimeError("POLICY_RUNTIME_CONTRACT_DRIFT: " + text)
    start_pending="-- BEGIN_ACTUAL_PENDING_EPOCH_POLICY"
    end_pending="-- END_ACTUAL_PENDING_EPOCH_POLICY"
    if raw.count(start_pending)!=1 or raw.count(end_pending)!=1:
        raise RuntimeError("REAL_PENDING_EPOCH_POLICY_NOT_UNIQUE")
    pending_fragment=raw.split(start_pending,1)[1].split("\n",1)[1].split(end_pending,1)[0]
    for marker in ("local function admitPacketEpoch(", "highestPacketEpoch=epoch",
                   "if pending[i][7]<epoch then table.remove(pending,i) end"):
        if marker not in pending_fragment:
            raise RuntimeError("PENDING_EPOCH_SOURCE_DRIFT_"+marker)
    return '''local lastRound=nil
local lastEpoch=nil
local lastByMob={}
''' + fragment + '''
local highestPacketEpoch=nil
local pending={}
''' + pending_fragment + '''
local yes,no=0,0
local function check(actual, expected)
    assert(actual==expected,"EPOCH_AND_OUT_OF_ORDER_POLICY_FAIL")
    if actual then yes+=1 else no+=1 end
end
check(acceptVisualCue(1,1,1,1),true)
check(acceptVisualCue(1,2,1,1),true)
check(acceptVisualCue(1,3,1,1),true)
check(acceptVisualCue(1,3,1,1),false)
check(acceptVisualCue(1,2,1,1),false)
check(acceptVisualCue(2,1,1,1),true)
check(acceptVisualCue(9,1,1,1),true)
-- Earlier unseen snapshot hits must survive when newer live hits overtake.
check(acceptVisualCue(1,6,1,1),true)
check(acceptVisualCue(1,5,1,1),true)
check(acceptVisualCue(1,4,1,1),true)
check(acceptVisualCue(1,5,1,1),false)
-- New epochs accept reused or LOWER round ids.
check(acceptVisualCue(1,1,2,2),true)
check(acceptVisualCue(1,4,1,1),false)
check(acceptVisualCue(1,1,2,2),false)
check(acceptVisualCue(1,1,1,3),true)
check(acceptVisualCue(1,1,1,3),false)
check(acceptVisualCue(1,1,1,4),true)
check(acceptVisualCue(1,4,1,3),false)
check(acceptVisualCue(1,1,2,4),false)
-- Epoch arrived first in replicated Attribute with no hit yet.
lastEpoch=5
lastRound=nil
table.clear(lastByMob)
check(acceptVisualCue(1,1,8,5),true)
check(acceptVisualCue(1,1,8,4),false)
check(acceptVisualCue(1,1,8,5),false)
check(acceptVisualCue(1,3,8,5),true)
check(acceptVisualCue(1,2,8,5),true)
-- Source derives 16-item budget with safe expiry of very old serials.
check(acceptVisualCue(1,23,8,5),true)
check(acceptVisualCue(1,4,8,5),false)
-- Bad payload and attempted cross-round bleed must not change state.
check(acceptVisualCue(0,3,8,5),false)
check(acceptVisualCue(10,3,8,5),false)
check(acceptVisualCue(1,0,8,5),false)
check(acceptVisualCue(1,2,1.3,5),false)
check(acceptVisualCue(1,2,8,0),false)
check(acceptVisualCue(1,2,8,5.5),false)
check(acceptVisualCue(1,2,8,"5"),false)
check(acceptVisualCue(1,2,7,5),false)
-- Arrival-order eviction bug regression: max=100 delivered FIRST; then
-- backfill 85..99. When 101 arrives, only 85 is expired, not serial100.
lastEpoch=6
lastRound=nil
table.clear(lastByMob)
check(acceptVisualCue(1,100,1,6),true)
for serial=85,99 do
    check(acceptVisualCue(1,serial,1,6),true)
end
check(acceptVisualCue(1,101,1,6),true)
check(acceptVisualCue(1,100,1,6),false)
check(acceptVisualCue(1,85,1,6),false)
assert(yes==32 and no==21,yes,no)
print("P0D_FB015_REAL_CLIENT_CUE_NATIVE_53_ORDERED_EPOCH_CASES_PASS")
-- Replicated epoch Attribute can lag the reliable hit RemoteEvent.
-- A newer server hit MUST be delivered; a genuinely old packet is rejected.
assert(not isEpochStale(3,4),"FUTURE_CONFIRMED_HIT_WAS_DROPPED")
assert(not isEpochStale(nil,4),"MISSING_EPOCH_ATTRIBUTE_DROPPED_HIT")
assert(not isEpochStale(3,3),"EQUAL_EPOCH_MISTAKENLY_STALE")
assert(isEpochStale(4,3),"OLDER_HIT_NOT_REJECTED")
print("P0D_FB015_REAL_CLIENT_EPOCH_LAG_NATIVE_PASS")
-- Actual authored pending-epoch policy: do not lose current-match events.
assert(admitPacketEpoch(10),"FIRST_NEW_MATCH")
table.insert(pending,{1,1,1,false,1,1,10,0})
table.insert(pending,{1,1,1,false,2,1,10,0})
assert(admitPacketEpoch(10) and #pending==2,"SAME_EPOCH_DROPPED")
assert(not admitPacketEpoch(9) and #pending==2,"OLD_CUE_ADMITTED")
assert(admitPacketEpoch(11) and #pending==0,"OLD_MATCH_PENDING_NOT_CLEARED")
table.insert(pending,{1,1,1,false,1,1,11,0})
assert(admitPacketEpoch(11) and #pending==1,"CURRENT_EPOCH_QUEUE_LOST")
assert(not admitPacketEpoch("11"),"BAD_EPOCH_ADMITTED")
print("P0D_FB015_REAL_PENDING_EPOCH_NATIVE_PASS")
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.write_text(compose(SRC.read_text("utf8")), encoding="utf8")

if __name__ == "__main__":
    main()
