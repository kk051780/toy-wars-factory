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
    for marker in (
        "local function burstForHit(serial,lastSerial,isKO)",
        'type(serial) ~= "number"',
        "serial <= lastSerial",
        'type(isKO) ~= "boolean"',
        "if isKO then 10 else 4",
    ):
        if marker not in policy:
            raise RuntimeError("ART_SPARK_SOURCE_DRIFT_"+marker)
    return policy + """
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
"""

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    args.out.write_text(extract(SRC.read_text("utf8")),encoding="utf8")

if __name__ == "__main__":
    main()
