#!/usr/bin/env python3
"""Execute selected RoundReplay's real cleanup body in native Luau, with mutant."""
import argparse,json
from pathlib import Path
from select_shield import MODULE, AFTER, mapping

MARKER_BEGIN=" -- GQ8_MULTI_SHIELD_REPLAY_CLEANUP_BEGIN"
MARKER_END=" -- GQ8_MULTI_SHIELD_REPLAY_CLEANUP_END"
HEADER=r'''
local function cleanup(ch)
'''
TRAILER=r'''
end
local function makeEffect(name, class)
 local obj={Name=name, class=class, destroyed=false, destroyCount=0}
 function obj:IsA(want) return self.class==want end
 function obj:Destroy()
  self.destroyed=true
  self.destroyCount+=1
 end
 return obj
end
local function run(caseName, parts, expected)
 local ch={parts=parts}
 function ch:GetChildren() return self.parts end
 cleanup(ch)
 for i,obj in ipairs(parts) do
  assert(obj.destroyed==expected[i], "GQ8_SHIELD_MUTANT_RED_"..caseName.."_"..tostring(i))
  if expected[i] then assert(obj.destroyCount==1,"GQ8_DOUBLE_DESTROY_RED") end
 end
end
cleanup(nil)
run("no_shields",{}, {})
run("single",{makeEffect("EGGRUMBLE_ItemShield","ForceField")},{true})
run("three",{makeEffect("EGGRUMBLE_ItemShield","ForceField"),makeEffect("EGGRUMBLE_ItemShield","ForceField"),makeEffect("EGGRUMBLE_ItemShield","ForceField")},{true,true,true})
run("preserve_foreign",{makeEffect("OtherGameShield","ForceField"),makeEffect("EGGRUMBLE_ItemShield","ForceField"),makeEffect("HealthVisual","Part")},{false,true,false})
run("name_spoof",{makeEffect("EGGRUMBLE_ItemShield","Part"),makeEffect("EGGRUMBLE_ItemShield","ForceField")},{false,true})
run("mixed",{makeEffect("EGGRUMBLE_ItemShield","ForceField"),makeEffect("Other","ForceField"),makeEffect("EGGRUMBLE_ItemShield","ForceField"),makeEffect("Other","Part")},{true,false,true,false})
print("GQ8_REAL_ROUNDREPLAY_MULTI_SHIELD_NATIVE_6_CASES_PASS")
'''
def main():
    a=argparse.ArgumentParser()
    a.add_argument("--project",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    a.add_argument("--mutant",type=Path,required=True)
    args=a.parse_args()
    _,sources,key=mapping(args.project)
    src=sources[key].read_text(encoding="utf-8")
    if key[-1]!=MODULE or src.count(AFTER)!=1:
        raise ValueError("RED_REAL_SELECTED_ROUND_REPLAY_SOURCE_NOT_FOUND")
    block=src.split(MARKER_BEGIN,1)[1].split(MARKER_END,1)[0]
    if block.count('effect:Destroy()')!=1 or block.count('ipairs(ch:GetChildren())')!=1:
        raise ValueError("RED_BAD_SOURCE_EXTRACTION")
    native=HEADER+block+TRAILER
    mutant=HEADER+block.replace('effect:Destroy()', '-- mutant omitted cleanup')+TRAILER
    args.out.write_text(native,encoding="utf-8")
    args.mutant.write_text(mutant,encoding="utf-8")
    print("GQ8_REAL_ROUNDREPLAY_NATIVE_AND_MUTANT_HARNESSES_GENERATED")

if __name__=="__main__":main()
