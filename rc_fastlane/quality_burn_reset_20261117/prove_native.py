#!/usr/bin/env python3
"""Run the current selected RoundReplay.resetHuman movement/status block in native Luau.
This is an isolated source-derived behavioral test, not a Studio engine test.
"""
import argparse
from pathlib import Path
from patch_burn_reset import PATCH, MODULE, mapping

PRE = "\n if hum then\n"
POST = "\n end\n if hum and hum.Health>0 and root then"
TESTS = r'''
end
local function humanoid(burn,walk,mark,slow,foreign)
 local h = {WalkSpeed=walk, attrs={
  EGGRUMBLE_BurnUntil=burn,
  EGGRUMBLE_MarkedUntil=mark,
  EGGRUMBLE_SlowExpiry=slow,
  OtherGameStatus=foreign
 }}
 function h:GetAttribute(k) return self.attrs[k] end
 function h:SetAttribute(k,v) self.attrs[k]=v end
 return h
end
local function case(name,h,base)
 reset(h,base)
 assert(h.attrs.EGGRUMBLE_BurnUntil==nil,"GQ8_BURN_RESET_MUTANT_RED_"..name)
 assert(h.attrs.EGGRUMBLE_MarkedUntil==nil,"GQ8_MARK_NOT_RESET_"..name)
 assert(h.attrs.EGGRUMBLE_SlowExpiry==nil,"GQ8_SLOW_NOT_RESET_"..name)
 assert(h.attrs.OtherGameStatus=="EXTERNAL","GQ8_FOREIGN_STATUS_CHANGED_"..name)
end
reset(nil,nil)
case("old_burning",humanoid(999999,8,999,999,"EXTERNAL"),16)
case("expired_burn",humanoid(-1,18,999,999,"EXTERNAL"),18)
case("future_burn",humanoid(1e12,22,999,999,"EXTERNAL"),18)
case("no_burn",humanoid(nil,14,999,999,"EXTERNAL"),16)
local h=humanoid(999999,6,9,9,"EXTERNAL")
case("invalid_speed",h,1000)
assert(h.WalkSpeed==16,"GQ8_INVALID_SPEED_RESET")
local keep=humanoid(nil,14,nil,nil,"EXTERNAL")
reset(keep,20)
assert(keep.WalkSpeed==20,"GQ8_VALID_SPEED_RESET")
print("GQ8_BURN_REPLAY_REAL_SELECTED_NATIVE_6_CASES_PASS")
'''

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--mutant",type=Path,required=True)
    a=p.parse_args()
    _, files, key = mapping(a.project)
    if key[-1] != MODULE:
        raise ValueError("RED_ROUNDREPLAY_MISSING")
    src=files[key].read_text(encoding="utf-8")
    if src.count(PATCH) != 1 or src.count(PRE) != 1 or src.count(POST) != 1:
        raise ValueError("RED_CURRENT_SELECTED_ROUNDREPLAY_SOURCE_CHANGED")
    body=src.split(PRE,1)[1].split(POST,1)[0]
    if body.count('hum:SetAttribute("EGGRUMBLE_BurnUntil",nil)') != 1:
        raise ValueError("RED_BURN_RESET_EXTRACT")
    source="local function reset(hum,baseWalkSpeed)\n if hum then\n"+body+"\n end\n"+TESTS
    changed=body.replace('hum:SetAttribute("EGGRUMBLE_BurnUntil",nil)',
                         'hum:SetAttribute("EGGRUMBLE_BurnUntil",999999)')
    mutated="local function reset(hum,baseWalkSpeed)\n if hum then\n"+changed+"\n end\n"+TESTS
    a.out.write_text(source,encoding="utf-8")
    a.mutant.write_text(mutated,encoding="utf-8")
    print("GQ8_BURN_REAL_SELECTED_NATIVE_AND_MUTANT_READY")

if __name__=="__main__":main()
