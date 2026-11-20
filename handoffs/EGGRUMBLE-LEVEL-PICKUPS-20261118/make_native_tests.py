#!/usr/bin/env python3
"""Generate genuine source-derived Luau behavior and a deliberate expiry mutant."""
from pathlib import Path
import argparse
P=Path(__file__).resolve().parent
MARK='if grant.expiresAt <= ctx.now then'
CASES=r"""
__SOURCE__
local P=M
local roles={WARRIOR="FIRE",MAGE="ICE",NINJA="WIND",TRAPPER="LIGHTNING",
 BUILDER="EARTH",BEAST="WATER",ZOMBIE="EARTH"}
local count=0
for role,element in pairs(roles) do
 local c={serverOwned=true,activeMatch=true,currentAvatar=true,sessionId="MATCH-A",role=role,now=100,level=1}
 assert(P.starter(role)==element,"RED_STARTER_"..role)
 local okay,route=P.authorizeAndConsume(c,element,{})
 assert(okay and route=="LEVEL","RED_LV1_FREE_"..role)
 count+=1
end
assert(count==7,"RED_MISSING_CLASS")
assert(P.unlockLevel("WARRIOR","DIVINE")==25,"RED_DIVINE_PROGRESS")
assert(P.unlockLevel("ZOMBIE","CURSE")==20,"RED_CURSE_PROGRESS")
assert(P.unlockLevel("MAGE","LIGHTNING")==12,"RED_MAGE_PROGRESS")
assert(P.starter("BOSS")==nil,"RED_FAKE_ROLE")
assert(P.pickupSpec("DIVINE").charges==1,"RED_UPPER_LIMIT")
assert(P.pickupSpec("CURSE").duration==10,"RED_UPPER_EXPIRY")
assert(P.pickupSpec("UNKNOWN")==nil,"RED_FAKE_ELEMENT")
local ctx={serverOwned=true,activeMatch=true,currentAvatar=true,sessionId="MATCH-A",role="MAGE",now=100,level=1}
local registry={pickupA={available=true,element="FIRE",sessionId="MATCH-A"}}
local grants={}
local ok,msg=P.issuePickup(ctx,"pickupA","FIRE",registry,grants)
assert(ok and msg=="PICKUP_GRANTED" and registry.pickupA.available==false,"RED_ISSUE")
ok,msg=P.issuePickup(ctx,"pickupA","FIRE",registry,grants)
assert(not ok and msg=="UNVERIFIED_OR_TAKEN_PICKUP","RED_DUPLICATE_PICKUP")
ok,msg=P.authorizeAndConsume(ctx,"FIRE",grants)
assert(ok and msg=="PICKUP" and grants.FIRE.charges==1,"RED_FIRST_FREE_CAST")
ok,msg=P.authorizeAndConsume(ctx,"FIRE",grants)
assert(ok and msg=="PICKUP" and grants.FIRE==nil,"RED_EXACTLY_TWO_CASTS")
ok,msg=P.authorizeAndConsume(ctx,"FIRE",grants)
assert(not ok,"RED_THIRD_FREE_CAST")
local fresh={pickupB={available=true,element="WIND",sessionId="MATCH-A"}}
local grants2={}
ok,msg=P.issuePickup(ctx,"pickupB","WIND",fresh,grants2)
assert(ok,"RED_SECOND_PICKUP")
ctx.now=124
ok,msg=P.authorizeAndConsume(ctx,"WIND",grants2)
assert(not ok and msg=="PICKUP_EXPIRED","RED_EXACT_EXPIRY")
ctx.now=101
ok,msg=P.authorizeAndConsume(ctx,"WIND",grants2)
assert(ok,"RED_PRE_EXPIRY")
local evil={serverOwned=false,activeMatch=true,currentAvatar=true,sessionId="MATCH-A",role="MAGE",now=100,level=1}
ok,msg=P.authorizeAndConsume(evil,"ICE",{})
assert(not ok and msg=="INVALID_SERVER_CONTEXT","RED_CLIENT_SPOOF")
ctx.sessionId="MATCH-B"
ok,msg=P.authorizeAndConsume(ctx,"WIND",grants2)
assert(not ok,"RED_CROSS_ROUND")
ctx.sessionId="MATCH-A"
ctx.currentAvatar=false
ok,msg=P.authorizeAndConsume(ctx,"ICE",{})
assert(not ok,"RED_STALE_AVATAR")
ctx.currentAvatar=true
ctx.activeMatch=false
ok,msg=P.authorizeAndConsume(ctx,"ICE",{})
assert(not ok,"RED_AFTER_ROUND")
ctx.activeMatch=true
ctx.role="WARRIOR"
ok,msg=P.authorizeAndConsume(ctx,"CURSE",{})
assert(not ok,"RED_UNEARNED_UPPER")
ctx.level=25
ok,msg=P.authorizeAndConsume(ctx,"DIVINE",{})
assert(ok and msg=="LEVEL","RED_FINAL_LEVEL_FREE")
ctx.role="ZOMBIE";ctx.level=20
ok,msg=P.authorizeAndConsume(ctx,"CURSE",{})
assert(ok and msg=="LEVEL","RED_CURSE_UNLOCK")
ctx.level=1;ctx.now=102
local special={pickupC={available=true,element="DIVINE",sessionId="MATCH-A"}}
local sg={}
ok,msg=P.issuePickup(ctx,"pickupC","DIVINE",special,sg)
assert(ok and sg.DIVINE.charges==1 and sg.DIVINE.expiresAt==112,"RED_DIVINE_PICKUP_BOUND")
ok,msg=P.authorizeAndConsume(ctx,"DIVINE",sg)
assert(ok and sg.DIVINE==nil,"RED_DIVINE_SINGLE_USE")
local invalid={pickupD={available=true,element="WATER",sessionId="OLD-ROUND"}}
ok,msg=P.issuePickup(ctx,"pickupD","WATER",invalid,{})
assert(not ok and invalid.pickupD.available==true,"RED_OLD_PICKUP")
print("GQ8_LEVEL_PICKUP_7ROLE_SOURCE_NATIVE_PASS")
"""
def main(out):
    source=(P/"ElementAccessPolicy.luau").read_text()
    assert source.count(MARK)==1,"RED_MUTATION_MARKER"
    assert source.rstrip().endswith("return M"),"RED_SOURCE_RETURN"
    prefix=source.rstrip()[:-len("return M")]
    out.mkdir(parents=True,exist_ok=True)
    (out/"good.luau").write_text(CASES.replace("__SOURCE__",prefix))
    (out/"mutant.luau").write_text(CASES.replace("__SOURCE__",prefix.replace(MARK,'if grant.expiresAt < ctx.now then')))
    print("GQ8_LEVEL_PICKUP_SOURCE_CASES_READY")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True)
    main(p.parse_args().out)
