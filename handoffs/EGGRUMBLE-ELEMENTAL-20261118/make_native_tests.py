#!/usr/bin/env python3
"""Generate authentic Luau VM tests directly from the source policy text."""
from pathlib import Path
import argparse

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/"ElementalAffinityPolicy.luau"
HIT="if dominates[attack]==defense then return 1.25 end"

CONTRACT=r'''
__SOURCE__
local m=M
local elements=m.ORDER
assert(#elements==8, "RED_8_ELEMENTS")
for _,a in ipairs(elements) do
 for _,d in ipairs(elements) do
  local result=m.resolve(a,d,"LAND","CLEAR")
  assert(result.total>=.65 and result.total<=1.35,"RED_DAMAGE_CAP")
  assert(type(m.visibleTell(a,result.classification))=="string", "RED_LABEL")
  assert(m.matchup(a,d)>0,"RED_VALID_MATCHUP")
  if a==d then assert(m.matchup(a,d)==1,"RED_SAME_ELEMENT") end
 end
end
local circle={"FIRE","ICE","WIND","EARTH","LIGHTNING","WATER"}
for i=1,#circle do
 local a=circle[i];local d=circle[(i%#circle)+1]
 assert(m.matchup(a,d)==1.25,"RED_COUNTER_RING")
 assert(m.matchup(d,a)==.80,"RED_COUNTER_REVERSAL")
end
assert(m.matchup("DIVINE","CURSE")==1.25,"RED_GOD_COUNTER")
assert(m.matchup("CURSE","DIVINE")==1.25,"RED_CURSE_COUNTER")
for _,other in ipairs(circle) do
 assert(m.matchup("DIVINE",other)==1,"RED_GOD_PAY_TO_WIN")
 assert(m.matchup("CURSE",other)==1,"RED_CURSE_PAY_TO_WIN")
end
assert(m.resolve("FIRE","FIRE","SUBSEA","CLEAR").total==.15,
 "RED_FIRE_SUBSEA_SUPPRESSION")
assert(m.resolve("LIGHTNING","LIGHTNING","SUBSEA","CLEAR").total==1.25,
 "RED_LIGHTNING_SUBSEA")
assert(m.resolve("WIND","WIND","SKY","CLEAR").total>1,"RED_SKY_WIND")
assert(m.resolve("FIRE","WATER","LAND","RAIN").total<1,"RED_RAIN_FIRE")
assert(m.resolve("DIVINE","CURSE","LAND","HOLY_AURA").total<=1.35,
 "RED_GOD_UPPER_BOUND")
assert(m.resolve("CURSE","DIVINE","LAND","CURSE_FOG").total<=1.35,
 "RED_EVIL_UPPER_BOUND")
assert(m.matchup("BOGUS","FIRE")==1,"RED_INVALID_UNTRUSTED_INPUT")
assert(m.visibleTell("FIRE","ADVANTAGE")=="炎・有利","RED_TEXT_ADVANTAGE")
print("GQ8_ELEMENT_AFFINITY_NATIVE_64_MATRIX_AND_ENVIRONMENT_PASS")
'''

def generate(out:Path):
 src=SOURCE.read_text(encoding="utf-8")
 if src.count(HIT)!=1:
  raise RuntimeError("RED_EXPECTED_ONE_COUNTER_POLICY")
 out.mkdir(parents=True,exist_ok=True)
 if not src.rstrip().endswith("return M"):
  raise RuntimeError("RED_MODULE_RETURN_EXPECTATION")
 head=src.rstrip()[:-len("return M")]
 (out/"good.luau").write_text(CONTRACT.replace("__SOURCE__",head),encoding="utf-8")
 (out/"mutant.luau").write_text(CONTRACT.replace("__SOURCE__",head.replace(HIT,"if dominates[attack]==defense then return .80 end")),encoding="utf-8")
 print("GQ8_ELEMENT_SOURCE_DERIVED_NATIVE_READY")

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args()
 generate(a.out)
