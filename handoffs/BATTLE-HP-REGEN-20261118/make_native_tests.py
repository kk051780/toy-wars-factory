#!/usr/bin/env python3
"""Generate true-source Luau positive/negative native tests for health recovery."""
from pathlib import Path
import argparse
ROOT=Path(__file__).resolve().parent
SRC=ROOT/"HealthRegenPolicy.luau"
ANCHOR="M.OUT_OF_COMBAT_DELAY=7"
SPEC=r'''
__SOURCE__
local m=M
assert(m.OUT_OF_COMBAT_DELAY==7,"RED_DELAY")
assert(m.MAX_HP_PER_SECOND==0.007,"RED_RATE")
local expected={WARRIOR=250,MAGE=195,NINJA=185,TRAPPER=205,BUILDER=225,BEAST=220,ZOMBIE=230}
local count=0
for k,v in pairs(expected) do
 assert(m.baseHP(k)==v,"RED_ROLE_HP_"..k)
 count+=1
end
assert(count==7 and m.baseHP("UNKNOWN")==nil and m.baseHP(5)==nil,"RED_ROLE_SET")
local good={active=true,currentSession=true,currentAvatar=true,alive=true,
 downed=false,eliminated=false,hasDamageOverTime=false,inCombat=false}
local function step(h,mx,hit,now,dt,ctx)
 return m.step(h,mx,hit,now,dt,ctx or good)
end
local h,g,why=step(200,250,0,6.9,0.2)
assert(h==200 and g==0 and why=="WAIT","RED_REGEN_EARLY")
h,g,why=step(200,250,0,7,1)
assert(h==200 and g==0,"RED_DELAY_EDGE")
h,g,why=step(200,250,0,7.25,1)
assert(math.abs(h-200.4375)<0.000001 and why=="RECOVERING","RED_DELAY_CROSSING")
h,g,why=step(200,250,0,8,1)
assert(math.abs(h-201.75)<0.000001,"RED_REGEN_RATE")
h,g,why=step(249.4,250,0,10,1)
assert(h==250 and math.abs(g-.6)<.000001,"RED_MAX_HP_CLAMP")
h,g,why=step(200,250,0,20,50)
assert(math.abs(g-1.75)<.000001,"RED_LAG_CATCHUP_CAP")
h,g,why=step(0,250,0,20,1)
assert(g==0 and h==0 and why=="DOWN","RED_NO_PASSIVE_REVIVE")
h,g,why=step(250,250,0,20,1)
assert(g==0 and why=="FULL","RED_FULL")
local blockers={"active","currentSession","currentAvatar","alive"}
for _,k in ipairs(blockers) do
 local c={active=true,currentSession=true,currentAvatar=true,alive=true}
 c[k]=false
 local new,delta,reason=step(200,250,0,20,1,c)
 assert(new==200 and delta==0 and reason=="BLOCKED","RED_MEMBERSHIP_"..k)
end
local negatives={"downed","eliminated","hasDamageOverTime","inCombat"}
for _,k in ipairs(negatives) do
 local c={active=true,currentSession=true,currentAvatar=true,alive=true}
 c[k]=true
 local new,delta,reason=step(200,250,0,20,1,c)
 assert(new==200 and delta==0 and reason=="BLOCKED","RED_BLOCK_"..k)
end
h,g,why=step(200,250,21,20,1)
assert(g==0 and why=="INVALID","RED_FUTURE_DAMAGE_TIME")
h,g,why=step(200,250,0,10,-1)
assert(g==0 and why=="INVALID","RED_NEGATIVE_TICK")
h,g,why=step(200,250,nil,10,1)
assert(g==0 and why=="INVALID","RED_UNKNOWN_DAMAGE_CLOCK")
local stamp,changed=m.recordRealDamage(250,230,4.25,1)
assert(stamp==4.25 and changed==true,"RED_ACTUAL_HIT_TIMESTAMP")
stamp,changed=m.recordRealDamage(230,240,5,4.25)
assert(stamp==4.25 and changed==false,"RED_HEAL_IS_NOT_HIT")
stamp,changed=m.recordRealDamage(230,230,5,4.25)
assert(stamp==4.25 and changed==false,"RED_NO_FAKE_HIT")
stamp,changed=m.recordRealDamage(230,210,6,4.25)
assert(stamp==6 and changed==true,"RED_DOT_RESETS_CLOCK")
print("GQ8_BATTLE_HP_REGEN_NATIVE_7ROLES_26CASES_PASS")
'''
def generate(out:Path):
 text=SRC.read_text(encoding="utf-8")
 if text.count(ANCHOR)!=1 or not text.rstrip().endswith("return M"):
  raise RuntimeError("RED_SOURCE_ANCHOR")
 head=text.rstrip()[:-len("return M")]
 out.mkdir(parents=True,exist_ok=True)
 (out/"good.luau").write_text(SPEC.replace("__SOURCE__",head),encoding="utf-8")
 bad=head.replace(ANCHOR,"M.OUT_OF_COMBAT_DELAY=6")
 (out/"mutant.luau").write_text(SPEC.replace("__SOURCE__",bad),encoding="utf-8")
 print("GQ8_BATTLE_HP_REGEN_REAL_SOURCE_TESTS_GENERATED")
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--out",type=Path,required=True)
 args=p.parse_args()
 generate(args.out)
