#!/usr/bin/env python3
"""Generate actual Luau native combat fairness tests from the exact source module."""
from pathlib import Path
import argparse
ROOT=Path(__file__).resolve().parents[1]
policy=(ROOT/"inputs/MusouCombatRules.luau").read_text("utf-8")
assert policy.count("return R")==1
payload=r'''
local R=(function()
__POLICY__
end)()
local checks={
 {"acquire_near",R.canAcquire(1,0),true},
 {"acquire_range",R.canAcquire(26,0),true},
 {"acquire_too_far",R.canAcquire(27,0),false},
 {"acquire_height_six",R.canAcquire(12,6),true},
 {"acquire_high_floor",R.canAcquire(12,6.1),false},
 {"acquire_low_floor",R.canAcquire(12,-7),false},
 {"acquire_negative",R.canAcquire(-1,0),false},
 {"acquire_infinite",R.canAcquire(math.huge,0),false},
 {"sweep_normal",R.canSweep(5,0,.9,true),true},
 {"sweep_edge",R.canSweep(13,0,.9,true),true},
 {"sweep_outside",R.canSweep(13.1,0,.9,true),false},
 {"sweep_behind",R.canSweep(3,0,-.3,true),false},
 {"sweep_side",R.canSweep(3,0,.05,true),false},
 {"sweep_height_five",R.canSweep(4,5,.8,true),true},
 {"sweep_upper_level",R.canSweep(4,5.1,.8,true),false},
 {"sweep_wall",R.canSweep(4,0,.8,false),false},
 {"sweep_invalid_type",R.canSweep("4",0,.8,true),false},
 {"minion_hit",R.canMobStrike(4,0,true,false),true},
 {"minion_edge",R.canMobStrike(5,0,true,false),true},
 {"minion_far",R.canMobStrike(5.1,0,true,false),false},
 {"elite_hit",R.canMobStrike(9,0,true,true),true},
 {"elite_far",R.canMobStrike(9.1,0,true,true),false},
 {"elite_height_four",R.canMobStrike(6,4,true,true),true},
 {"elite_upstairs",R.canMobStrike(6,5,true,true),false},
 {"elite_wall",R.canMobStrike(6,0,false,true),false},
 {"negative_range",R.canMobStrike(-1,0,true,true),false},
}
assert(#checks == 26)
for _,case in ipairs(checks) do
    assert(case[2]==case[3], "MUSOU_COMBAT_FAIL_"..case[1])
end
print("MUSOU_COMBAT_NATIVE_26_ASSERTIONS_PASS")
'''
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--write",required=True)
    args=p.parse_args()
    target=Path(args.write)
    target.write_text(payload.replace("__POLICY__",policy),encoding="utf-8")
    print("MUSOU_COMBAT_NATIVE_TEST_GENERATED",target)
