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
    required = ("local function acceptVisualCue(", "serial<=(lastByMob[id] or 0)",
                "lastByMob[id]=serial", "return true")
    for text in required:
        if text not in fragment:
            raise RuntimeError("POLICY_RUNTIME_CONTRACT_DRIFT: " + text)
    return '''local lastRound=nil
local lastByMob={}
''' + fragment + '''
local accepted = 0
local rejected = 0
local function check(ok, expected)
    if ok == expected then
        if ok then accepted += 1 else rejected += 1 end
    else
        error("ACTUAL_CUE_POLICY_WRONG_RESULT")
    end
end
-- Single mob hits with identical damage text still change sequence.
check(acceptVisualCue(1,1,1),true)
check(acceptVisualCue(1,2,1),true)
check(acceptVisualCue(1,3,1),true)
check(acceptVisualCue(1,3,1),false)
check(acceptVisualCue(1,2,1),false)
-- Different mobs can each start at serial 1.
check(acceptVisualCue(2,1,1),true)
check(acceptVisualCue(9,1,1),true)
-- Fresh round restarts per-mob serial and old round cannot replay.
check(acceptVisualCue(1,1,2),true)
check(acceptVisualCue(1,4,1),false)
check(acceptVisualCue(1,1,2),false)
-- Corrupted/malformed payload rejected before any effects.
check(acceptVisualCue(0,3,2),false)
check(acceptVisualCue(10,3,2),false)
check(acceptVisualCue(1,0,2),false)
check(acceptVisualCue(1,2,1.3),false)
assert(accepted==6 and rejected==8,accepted,rejected)
print("P0D_FB015_REAL_CLIENT_CUE_NATIVE_14_CASES_PASS")
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.write_text(compose(SRC.read_text("utf8")), encoding="utf8")

if __name__ == "__main__":
    main()
