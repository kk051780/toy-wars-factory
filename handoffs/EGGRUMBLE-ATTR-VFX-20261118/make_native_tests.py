#!/usr/bin/env python3
"""Source-derived Luau CLI gate. No Roblox fake services or simulator success claim."""
import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "ElementVisuals.luau"
APPEND = r'''
local elements={"FIRE","WATER","LIGHTNING","WIND","EARTH","ICE","DIVINE","CURSE"}
local kinds={"WEAPON","ATTACK","SHIELD"}
local outcomes={"NORMAL","ADVANTAGE","RESIST","IMMUNE"}
local seen={}
for _,element in ipairs(elements) do
 local sample=Visual.describe(element,"ATTACK","NORMAL",false)
 assert(sample and sample.color and sample.silhouette)
 local serial=""
 for _,pt in ipairs(sample.silhouette) do
  serial=serial..tostring(pt[1])..":"..tostring(pt[2])..";"
 end
 assert(not seen[serial],"RED_SILHOUETTE_DUPLICATE_"..element)
 seen[serial]=true
 for _,kind in ipairs(kinds) do
  for _,outcome in ipairs(outcomes) do
   local full=Visual.describe(element,kind,outcome,false)
   local lite=Visual.describe(element,kind,outcome,true)
   assert(full.beamCount>=1 and full.beamCount<=8,"RED_FULL_BEAM_BUDGET")
   assert(lite.beamCount>=1 and lite.beamCount<=4,"RED_MOBILE_BEAM_BUDGET")
   assert(full.duration>0 and full.duration<=.9,"RED_VISUAL_LIFETIME")
   assert(full.width>0 and full.width<=.18,"RED_THICKNESS")
   assert(full.pulse==(outcome=="ADVANTAGE" and 2 or 1),"RED_ADVANTAGE_SIGNAL")
   assert(full.drawSlash==(outcome=="IMMUNE"),"RED_IMMUNE_SIGNAL")
  end
 end
end
assert(Visual.describe("INVALID","ATTACK","NORMAL",false)==nil,"RED_INVALID_ELEMENT")
assert(Visual.describe("FIRE","INVALID","NORMAL",false)==nil,"RED_INVALID_KIND")
assert(Visual.describe("FIRE","ATTACK","INVALID",false)==nil,"RED_INVALID_RESULT")
local known={{"MAGE:A:1","MAGE","ICE"},{"MAGE:B:2","MAGE","FIRE"},{"MAGE:C:3","MAGE","LIGHTNING"},{"WARRIOR:C:4","WARRIOR","DIVINE"},{"ZOMBIE:C:5","ZOMBIE","CURSE"}}
for _,case in ipairs(known) do
 local element,seq=Visual.elementForServerCast(case[1],case[2])
 assert(element==case[3] and seq>0,"RED_VERIFIED_CAST_MAP")
end
local noCast={"NINJA:B:6","MAGE:D:7","WARRIOR:A:8","MAGE:A:-1","MAGE:A:0","MAGE:A:999999999999"}
for _,sig in ipairs(noCast) do
 local element=Visual.elementForServerCast(sig,"MAGE")
 assert(element==nil,"RED_INVENTED_ELEMENT")
end
local spoof=Visual.elementForServerCast("MAGE:A:9","WARRIOR")
assert(spoof==nil,"RED_ROLE_MISMATCH")
local cap,beams=Visual.capacity()
assert(cap==8 and beams==8,"RED_BUDGET")
print("GQ8_ATTR_VFX_NATIVE_SHAPES_BUDGET_CONTRACT_PASS")
'''
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    args=p.parse_args()
    out=Path(args.out)
    out.mkdir(parents=True,exist_ok=True)
    original=SOURCE.read_text(encoding="utf-8")
    assert original.rstrip().endswith("return Visual"), "RED_SOURCE_TAIL_CHANGED"
    assert original.count("return Visual")==1, "RED_SOURCE_TERM_AMBIGUOUS"
    code_lines = "\n".join(line for line in original.splitlines() if not line.lstrip().startswith("--"))
    assert not any(word in code_lines for word in ["TakeDamage(", "RemoteEvent.new(", "DataStoreService", ".Health=", "GetAsync(", "SetAsync("]), "RED_DAMAGE_AUTHORITY_INTRUSION"
    body=original.rsplit("return Visual",1)[0]
    (out/"good.luau").write_text(body+APPEND,encoding="utf-8")
    assert "local MAX_ACTIVE=8" in body
    (out/"mutant.luau").write_text(body.replace("local MAX_ACTIVE=8","local MAX_ACTIVE=88",1)+APPEND,encoding="utf-8")
    print("SOURCE_DERIVED_TRUE_LUAU_HARNESS_CREATED")
if __name__=="__main__":
    main()
