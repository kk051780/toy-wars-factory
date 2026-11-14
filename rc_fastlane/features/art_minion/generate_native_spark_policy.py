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
        "local function parseSparkCue(raw, lastSerial)",
        'raw:match("^(%d+)|([HK])$")',
        "if not seq or seq <= lastSerial",
        'if kind == "K" then 10 else 4',
    ):
        if marker not in policy:
            raise RuntimeError("ART_SPARK_SOURCE_DRIFT_"+marker)
    return policy + """
local cases=0
local function expect(input,last,serial,burst)
    local gotSerial,gotBurst=parseSparkCue(input,last)
    assert(gotSerial==serial and gotBurst==burst,
        "SPARK_CUE_MISMATCH_"..tostring(cases+1))
    cases += 1
end
expect("1|H",0,1,4)
expect("2|H",1,2,4)
expect("3|H",2,3,4) -- identical damage/continuous color
expect("4|K",3,4,10) -- KO exactly once
expect("4|K",4,nil,nil) -- duplicate KO is ignored
expect("3|H",4,nil,nil) -- stale hit ignored
expect("1|H",0,1,4) -- NPC spawned in a new round
expect("1|X",0,nil,nil)
expect("0|H",0,nil,nil)
expect("5|K",5,nil,nil)
expect("",0,nil,nil)
expect(nil,0,nil,nil)
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
