#!/usr/bin/env python3
"""Run the exact pure view-model Luau source in native CLI; deliberate matrix mutant must fail."""
from pathlib import Path
import argparse

HERE=Path(__file__).resolve().parent
SOURCE=HERE/"AffinityGuidePolicy.luau"
GOOD=r"""
local matrix={
 FIRE={"ICE","WATER"},WATER={"FIRE","LIGHTNING"},LIGHTNING={"WATER","EARTH"},
 WIND={"EARTH","ICE"},EARTH={"LIGHTNING","WIND"},ICE={"WIND","FIRE"},
 DIVINE={"CURSE","CURSE"},CURSE={"DIVINE","DIVINE"},
}
local count=0
for element,expected in pairs(matrix) do
 local desc=Policy.describe(element)
 assert(desc and desc.advantage==expected[1] and desc.disadvantage==expected[2],"RED_MATRIX_"..element)
 assert(type(desc.shortLabel)=="string" and type(desc.matchup)=="string")
 assert(desc.name~="" and desc.glyph~="")
 count+=1
end
assert(count==8,"RED_ELEMENT_COUNT")
assert(Policy.describe("INVALID")==nil)
assert(Policy.describe(1)==nil)
for _,sample in ipairs({
 {"MAGE:A:1","MAGE","ICE",1},{"MAGE:B:2","MAGE","FIRE",2},
 {"MAGE:C:3","MAGE","LIGHTNING",3},{"WARRIOR:C:4","WARRIOR","DIVINE",4},
 {"ZOMBIE:C:5","ZOMBIE","CURSE",5},
}) do
 local d,n=Policy.fromVerifiedServerCast(sample[1],sample[2])
 assert(d and d.element==sample[3] and n==sample[4],"RED_VERIFIED_CAST")
end
for _,sample in ipairs({
 {"MAGE:A:1","WARRIOR"},{"MAGE:D:2","MAGE"},{"NINJA:A:3","NINJA"},
 {"MAGE:A:0","MAGE"},{"MAGE:A:-1","MAGE"},{"MAGE:A:2147483648","MAGE"},
 {"MAGE:A:999999999999","MAGE"},{"MAGE:A:1;MAGE:B:2","MAGE"},
 {"","MAGE"},
}) do
 assert(Policy.fromVerifiedServerCast(sample[1],sample[2])==nil,"RED_UNVERIFIED_CAST")
end
assert(Policy.help():find("神と悪",1,true),"RED_TUTORIAL")
print("GQ8_AFFINITY_HUD_NATIVE_MATRIX_CAST_AND_SPOOF_PASS")
"""
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--out",required=True)
 args=p.parse_args()
 code=SOURCE.read_text(encoding="utf-8")
 assert code.rstrip().endswith("return Policy"),"RED_POLICY_TAIL"
 assert code.splitlines().count("return Policy")==1,"RED_POLICY_DUP_RETURN"
 for forbidden in ("RemoteEvent","TakeDamage","DataStoreService","GetAsync","SetAsync"):
  assert forbidden not in code,"RED_AUTHORITY_INTRUSION_"+forbidden
 body=code.rsplit("return Policy",1)[0]
 out=Path(args.out)
 out.mkdir(parents=True,exist_ok=True)
 (out/"good.luau").write_text(body+GOOD,encoding="utf-8")
 needle='FIRE={name="火",glyph="炎",strong="ICE",weak="WATER"}'
 assert needle in body,"RED_MUTANT_SOURCE_DRIFT"
 mutated=body.replace(needle,'FIRE={name="火",glyph="炎",strong="WATER",weak="ICE"}',1)
 (out/"mutant.luau").write_text(mutated+GOOD,encoding="utf-8")
 print("GQ8_AFFINITY_HUD_NATIVE_HARNESSES_READY")
if __name__=="__main__":
 main()
