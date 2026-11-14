#!/usr/bin/env python3
"""Extract *authored* server spark policy for native Luau execution.

No mock rewrite of the policy. This validates serial/KO burst semantics,
not the Roblox engine ParticleEmitter API or live packet delivery.
"""
from pathlib import Path
import argparse

SRC = Path(__file__).with_name("MinionArtSilhouette.server.luau")
START = "-- BEGIN_ACTUAL_ART_SPARK_POLICY"
END = "-- END_ACTUAL_ART_SPARK_POLICY"

def extract(raw: str) -> str:
    if raw.count(START) != 1 or raw.count(END) != 1:
        raise RuntimeError("ART_SPARK_POLICY_MISSING_OR_DUPLICATED")
    policy=raw.split(START, 1)[1].split("\n", 1)[1].split(END, 1)[0]
    evt_start="-- BEGIN_ACTUAL_ART_SERVER_EVENT"
    evt_end="-- END_ACTUAL_ART_SERVER_EVENT"
    if raw.count(evt_start)!=1 or raw.count(evt_end)!=1:
        raise RuntimeError("REAL_ART_SERVER_EVENT_MISSING")
    event=raw.split(evt_start,1)[1].split("\n",1)[1].split(evt_end,1)[0]
    for marker in ("local function onConfirmedServerHit(",
                   "pendingByCore[core]=queue",
                   "table.insert(queue,{serial=serial,isKO=isKO,round=round})",
                   "item.sparks:Emit(burst)"):
        if marker not in event:
            raise RuntimeError("REAL_ART_SERVER_EVENT_DRIFT_"+marker)
    for marker in (
        "local function burstForHit(serial,lastSerial,isKO)",
        'type(serial) ~= "number"',
        "serial <= lastSerial",
        'type(isKO) ~= "boolean"',
        "if isKO then 10 else 4",
    ):
        if marker not in policy:
            raise RuntimeError("ART_SPARK_SOURCE_DRIFT_"+marker)
    return policy + event + """
local cases=0
local function expect(input,last,ko,serial,burst)
    local gotSerial,gotBurst=burstForHit(input,last,ko)
    assert(gotSerial==serial and gotBurst==burst,
        "SPARK_CUE_MISMATCH_"..tostring(cases+1))
    cases += 1
end
expect(1,0,false,1,4)
expect(2,1,false,2,4)
expect(3,2,false,3,4) -- fast consecutive real server events
expect(4,3,true,4,10) -- KO exactly once
expect(4,4,true,nil,nil) -- replay KO is ignored
expect(3,4,false,nil,nil) -- stale hit ignored
expect(1,0,false,1,4) -- new Core on new round
expect(0,0,false,nil,nil)
expect(3,3,false,nil,nil)
expect("3",1,false,nil,nil)
expect(5,4,nil,nil,nil)
expect(2.5,1,true,nil,nil)
assert(cases==12,cases)
print("P0D_FB015_ACTUAL_MINION_SPARK_NATIVE_12_CASES_PASS")
-- Exercise the REAL authored server event handler, not recreated pseudocode.
local core={}
function core:IsA(kind) return kind=="BasePart" end
onConfirmedServerHit(core,1,false,1)
onConfirmedServerHit(core,2,false,1)
onConfirmedServerHit(core,3,true,1)
local buffered=pendingByCore[core]
assert(#buffered==3,"PREATTACH_EVENT_QUEUE_DROPPED")
local emitted={}
local state={
    lastSparkSeq=0,
    sparks={Emit=function(_,n) table.insert(emitted,n) end},
}
activeByCore[core]=state
pendingByCore[core]=nil
for _,evt in ipairs(buffered) do
    onConfirmedServerHit(core,evt.serial,evt.isKO,evt.round)
end
assert(#emitted==3 and emitted[1]==4 and emitted[2]==4 and emitted[3]==10,
       "PREATTACH_HITS_NOT_REPLAYED")
onConfirmedServerHit(core,3,true,1)
assert(#emitted==3,"DUPLICATE_KO_EMITTED")
onConfirmedServerHit(core,4,false,1)
assert(#emitted==4 and emitted[4]==4,"LIVE_HIT_NOT_EMITTED")
local slow={}
function slow:IsA(kind) return kind=="BasePart" end
for i=1,30 do onConfirmedServerHit(slow,i,false,2) end
assert(#pendingByCore[slow]==16,"PREATTACH_QUEUE_UNBOUNDED")
print("P0D_FB015_ACTUAL_SERVER_SPARK_QUEUE_NATIVE_PASS")
"""

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    args.out.write_text(extract(SRC.read_text("utf8")),encoding="utf8")

if __name__ == "__main__":
    main()
