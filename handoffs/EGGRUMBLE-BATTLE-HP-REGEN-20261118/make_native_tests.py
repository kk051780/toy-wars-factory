#!/usr/bin/env python3
"""Source-derived native Luau good/mutant cases: no fake Python damage simulation."""
import argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/"PassiveRegenPolicy.luau"
NEEDLE='if now - lastDamageAt < M.REGEN_DELAY then'
CONTRACT=r'''
__SOURCE__
local policy=M
local hp={WARRIOR=250,MAGE=195,NINJA=185,TRAPPER=205,BUILDER=225,BEAST=220,ZOMBIE=230}
local count=0
for role,maximum in pairs(hp) do
 assert(policy.initialMaxHP(role)==maximum,"RED_ROLE_HP_"..role)
 local value,why=policy.regenDelta(maximum/2,maximum,107,100,.25,true,true,false,false)
 assert(why=="REGEN" and math.abs(value-maximum*.007*.25)<.00001,"RED_HP_RATE_"..role)
 count+=1
end
assert(count==7,"RED_ROLE_COUNT")
assert(policy.initialMaxHP("FAKE")==nil,"RED_UNKNOWN_ROLE")
assert(policy.initialMaxHP(42)==nil,"RED_UNTRUSTED_ROLE")
local d,why=policy.regenDelta(100,200,106.999,100,.25,true,true,false,false)
assert(d==0 and why=="RECENT_DAMAGE","RED_7S_DELAY")
d,why=policy.regenDelta(100,200,107,100,.25,true,true,false,false)
assert(math.abs(d-.35)<.000001 and why=="REGEN","RED_7S_EXACT")
d=policy.regenDelta(100,200,108,100,50,true,true,false,false)
assert(math.abs(d-.35)<.000001,"RED_LAG_SPIKE_CATCHUP")
d=policy.regenDelta(199.95,200,107,100,.25,true,true,false,false)
assert(math.abs(d-.05)<.000001,"RED_OVERHEAL")
local deny={
 {100,200,107,100,.25,false,true,false,false,"NOT_CURRENT_MATCH"},
 {100,200,107,100,.25,true,false,false,false,"NOT_CURRENT_MATCH"},
 {100,200,107,100,.25,true,true,true,false,"DOT_ACTIVE"},
 {100,200,107,100,.25,true,true,false,true,"DEAD_OR_DOWNED"},
 {0,200,107,100,.25,true,true,false,false,"DEAD_OR_DOWNED"},
 {100,200,107,100,0,true,true,false,false,"NO_STEP"},
 {200,200,107,100,.25,true,true,false,false,"FULL"},
 {100,200,99,100,.25,true,true,false,false,"BAD_STATE"},
 {100,200,107,100,-.1,true,true,false,false,"NO_STEP"},
 {100,0,107,100,.25,true,true,false,false,"BAD_STATE"},
}
for i,case in ipairs(deny) do
 local amount,reason=policy.regenDelta(table.unpack(case,1,9))
 assert(amount==0 and reason==case[10],"RED_DENIAL_"..i.."_"..reason)
end
local nan=0/0
d,why=policy.regenDelta(100,nan,107,100,.25,true,true,false,false)
assert(d==0 and why=="BAD_NUMBER","RED_NAN")
local inf=math.huge
d,why=policy.regenDelta(100,200,inf,100,.25,true,true,false,false)
assert(d==0 and why=="BAD_NUMBER","RED_INF")
local last,hit=policy.observeHealth(200,180,100,92)
assert(last==100 and hit==true,"RED_REAL_HIT")
last,hit=policy.observeHealth(180,190,101,last)
assert(last==100 and hit==false,"RED_HEAL_EVENT_NOT_DAMAGE")
last,hit=policy.observeHealth(180,180,102,last)
assert(last==100 and hit==false,"RED_BLOCKED_HIT_NOT_DAMAGE")
last,hit=policy.observeHealth(180,175,103,last)
assert(last==103 and hit==true,"RED_DOT_TICK_DAMAGE")
last,hit=policy.observeHealth(180,nan,104,last)
assert(last==103 and hit==false,"RED_NAN_DAMAGE")
print("GQ8_HP_REGEN_7_ROLE_REAL_LUAU_PASS")
'''

def emit(out:Path)->None:
 source=SOURCE.read_text(encoding="utf-8")
 assert source.count(NEEDLE)==1,"RED_SOURCE_DELAY_MARKER"
 assert source.rstrip().endswith("return M"),"RED_SOURCE_RETURN"
 body=source.rstrip()[:-len("return M")]
 out.mkdir(parents=True,exist_ok=True)
 (out/"good.luau").write_text(CONTRACT.replace("__SOURCE__",body),encoding="utf-8")
 bad=body.replace(NEEDLE,"if now - lastDamageAt < 0 then")
 (out/"mutant.luau").write_text(CONTRACT.replace("__SOURCE__",bad),encoding="utf-8")
 print("GQ8_REGEN_SOURCE_DERIVED_NATIVE_READY")

if __name__=="__main__":
 parser=argparse.ArgumentParser()
 parser.add_argument("--out",required=True,type=Path)
 emit(parser.parse_args().out)
