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
local lastEpoch=nil
local lastByMob={}
''' + fragment + '''
local accepted = 0
local rejected = 0
local function check(ok, expected)
    if ok == expected then
        if ok then accepted += 1 else rejected += 1 end
    else
        error("ACTUAL_CUE_EPOCH_POLICY_WRONG_RESULT")
    end
end
-- Real live packets retain identical-damage serials and reject duplicates.
check(acceptVisualCue(1,1,1,1),true)
check(acceptVisualCue(1,2,1,1),true)
check(acceptVisualCue(1,3,1,1),true)
check(acceptVisualCue(1,3,1,1),false)
check(acceptVisualCue(1,2,1,1),false)
check(acceptVisualCue(2,1,1,1),true)
check(acceptVisualCue(9,1,1,1),true)
-- New Horde epoch resets per-id seq; older epoch replay is rejected.
check(acceptVisualCue(1,1,2,2),true)
check(acceptVisualCue(1,4,1,1),false)
check(acceptVisualCue(1,1,2,2),false)
-- Same or LOWER round is valid only if new epoch is larger.
check(acceptVisualCue(1,1,1,3),true)
check(acceptVisualCue(1,1,1,3),false)
check(acceptVisualCue(1,1,1,4),true)
check(acceptVisualCue(1,4,1,3),false)
check(acceptVisualCue(1,1,2,4),false)
-- Malformed event cannot change dedupe state.
check(acceptVisualCue(0,3,2,4),false)
check(acceptVisualCue(10,3,2,4),false)
check(acceptVisualCue(1,0,2,4),false)
check(acceptVisualCue(1,2,1.3,4),false)
check(acceptVisualCue(1,2,2,0),false)
check(acceptVisualCue(1,2,2,4.5),false)
check(acceptVisualCue(1,2,2,"4"),false)
assert(accepted==8 and rejected==14,accepted,rejected)
print("P0D_FB015_REAL_CLIENT_CUE_NATIVE_22_EPOCH_CASES_PASS")
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.write_text(compose(SRC.read_text("utf8")), encoding="utf8")

if __name__ == "__main__":
    main()
