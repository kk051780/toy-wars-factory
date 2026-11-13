#!/usr/bin/env python3
"""Execute pinned ACTUAL 3-source V4 Luau pipeline in a native Luau CLI.
The generated tests call Scheduler -> Gate -> Projection, not a Python reimplementation.
This is NOT Roblox Studio and does not touch canonical UserData Store or premium APIs.
"""
from pathlib import Path
import hashlib
import argparse

ROOT=Path(__file__).resolve().parents[1]
BLOBS={
    "FocusTrainingScheduler.luau":"a00caf954aacfca03c92a75b0165c1bafd4de8fd",
    "TrainingIntegrationGate.luau":"45c6c3a51ca0fc6a0167d50b217f05c1323e52b3",
    "SixSkillCreditProjection.luau":"bf7c2632736658939b2a4294c37b67142bb83cae",
}
def git_blob(data:bytes)->str:
    return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()

def source(name, symbol):
    data=(ROOT/"src"/name).read_bytes()
    assert git_blob(data)==BLOBS[name],f"frozen source mismatch: {name}"
    text=data.decode("utf8").rstrip()
    assert text.endswith(f"return {symbol}"),name
    return f"local {symbol} = (function()\n"+text+"\nend)()\n"

def build():
    lua=source("FocusTrainingScheduler.luau","Scheduler")
    lua+=source("TrainingIntegrationGate.luau","Gate")
    lua+=source("SixSkillCreditProjection.luau","Projection")
    lua+=r"""
local n=0
local function check(value,label)
    n+=1
    if not value then error("V4_PIPELINE_ASSERT_"..tostring(n).." "..label) end
end
local caps={
    skills={BEAST=true,MAGIC=true,WEAPON=true,ZOMBIE=true,VEHICLE=true,BUILDING=true},
    singleXPAuthority=true,persistentProfile=true,atomicSessionLock=true,
    friendModel="COUNT_25_CAP4",acceptsMicroXP=true,serverAuthoritativeTime=true,
    pvpNormalized=true,maxSegmentSeconds=120,
}
local function copy(a)
    local r={}
    for k,v in pairs(a) do r[k]=v end
    return r
end
local T=1700000000
local state=Scheduler.selectSkill(Scheduler.newState(42,T,{}),"BEAST")
local newState,segments=Scheduler.settle(state,T+60,true,0,false)
check(#segments==1 and segments[1].skill=="BEAST" and segments[1].seconds==60,"real scheduler segment")
local quote=Gate.quote(caps,segments,10000,"server-uuid-0001")
check(quote.ok and quote.applied==false,"actual gate quote is passive")
check(quote.totalSeconds==60 and quote.totalMicroXP==600000000,"actual 10XP/s quote")
local empty=Projection.blank()
check(Projection.checkTotals(empty),"six initial ledgers")
local result=Projection.prepare(empty,0,quote)
check(result.ok and result.applied==false,"proposal not applied")
check(result.expectedRevision==0 and result.proposedRevision==1,"no Store revision claimed")
check(result.totals.BEAST==600000000,"BEAST credited in projection")
check(result.levels.BEAST.level==3,"600XP leads Lv3")
check(result.levels.MAGIC.level==1 and result.totals.MAGIC==0,"other skill untouched")
check(empty.BEAST==0,"pure no source mutation")
check(Projection.viewLevel(0).level==1,"level 1 zero XP")
check(Projection.viewLevel(99999999).level==1,"99.999999XP remains Lv1")
check(Projection.viewLevel(100000000).level==2,"100XP levels to 2")
check(Projection.viewLevel(499999999).level==2,"499.999999 XP remains Lv2")
check(Projection.viewLevel(500000000).level==3,"500 XP reaches Lv3")
check(Projection.viewLevel(855500000000).level==30,"quadratic curve max Lv30")
check(Projection.viewLevel(855500000000).maxLevel,"max flagged")
local legacy={BEAST=10,WEAPON=20}
local denied=Projection.prepare(legacy,0,quote)
check(not denied.ok and denied.problem=="MISSING_OR_INVALID_MAGIC","legacy 2 skill MUST NOT pass as six")
check(not Projection.checkTotals({}),"empty must fail closed")
local extra=Projection.blank()
extra.CHEAT=999
local good,reason=Projection.checkTotals(extra)
check(not good and reason=="UNKNOWN_SKILL_PROFILE","unrecognized old/new skill blocked")
local invalid=Projection.blank()
invalid.ZOMBIE=0/0
check(not Projection.checkTotals(invalid),"NaN rejected")
local tooBig=Projection.blank()
tooBig.WEAPON=9000000000001
check(not Projection.checkTotals(tooBig),"upper cap enforced")
local withFriend=Scheduler.selectSkill(newState,"MAGIC")
local nextState,friendSegments=Scheduler.settle(withFriend,T+120,true,2,false)
check(#friendSegments==1 and friendSegments[1].bonusBps==15000,"2 friends XP multiplier")
local q2=Gate.quote(caps,friendSegments,10000,"server-uuid-0002")
check(q2.ok and q2.totalMicroXP==900000000,"friend XP earned 900 points")
local r2=Projection.prepare(result.totals,1,q2)
check(r2.ok and r2.totals.BEAST==600000000,"beast retained")
check(r2.totals.MAGIC==900000000 and r2.levels.MAGIC.level==3,"magic XP added")
check(r2.expectedRevision==1 and r2.proposedRevision==2,"only candidate revision")
local spoofed=copy(q2)
spoofed.totalMicroXP=900000001
check(Projection.prepare(result.totals,1,spoofed).problem=="QUOTE_CHECKSUM_MISMATCH","check sum mismatch blocked")
local manipulated=copy(q2)
manipulated.applied=true
check(Projection.prepare(result.totals,1,manipulated).problem=="INVALID_QUOTE","already-applied grant blocked")
local negative=copy(q2)
negative.grants={{skill="BEAST",seconds=60,microXP=-1,bonusBps=15000,mode="FOCUS"}}
negative.grantCount=1
negative.totalMicroXP=1
check(Projection.prepare(result.totals,1,negative).problem=="INVALID_GRANT","negative grant blocked")
local wrongCaps=copy(caps)
wrongCaps.skills={BEAST=true,WEAPON=true}
local refused=Gate.quote(wrongCaps,friendSegments,10000,"server-uuid-0003")
check(not refused.ok and #refused.grants==0,"legacy 2-pad cannot claim ready")
local oldProfile=Projection.blank()
oldProfile.MAGIC=Projection.MAX_TOTAL_MICROXP
local saturation=Gate.quote(caps,{{skill="MAGIC",seconds=1,bonusBps=10000,mode="FOCUS"}},1,"server-uuid-0004")
check(saturation.ok,"valid tiny quote")
check(Projection.prepare(oldProfile,100,saturation).problem=="TOTAL_XP_CAP","overflow fail closed")
local tiny=Gate.quote(caps,{{skill="VEHICLE",seconds=1,bonusBps=12500,mode="FOCUS"}},1,"server-uuid-0005")
local tinyProfile=Projection.prepare(Projection.blank(),4,tiny)
check(tiny.ok and tinyProfile.ok and tinyProfile.totals.VEHICLE==1250,"0.001XP base 25pct friend exact")
check(tinyProfile.levels.VEHICLE.level==1,"tiny XP no false level up")
local projectionReplay=Projection.prepare(empty,0,quote)
check(projectionReplay.ok and projectionReplay.totals.BEAST==result.totals.BEAST,"pure projection repeat deterministic")
check(projectionReplay.applied==false,"replay needs Store dedupe: never claim applied")
local a=Scheduler.selectSkill(Scheduler.newState(42,T,{}),"WEAPON")
for i=1,30 do
    a=Scheduler.settle(a,T+60*i,true,0,false)
end
check(a.focusedSeconds==1800,"free focus 30min exhausted")
local afterCap,randomSeg=Scheduler.settle(a,T+1860,true,0,false)
check(#randomSeg==1 and randomSeg[1].mode=="RANDOM","free remains productive")
local randomQuote=Gate.quote(caps,randomSeg,10000,"server-uuid-0006")
check(randomQuote.ok,"random V4 goes through full gate")
local randomProjection=Projection.prepare(Projection.blank(),0,randomQuote)
check(randomProjection.ok,"random into six-skill profile")
check(randomProjection.totals[randomSeg[1].skill]==600000000,"random XP does not disappear")
local projectedChanged=0
for _,skill in ipairs(Projection.SKILLS) do
    if randomProjection.totals[skill]>0 then projectedChanged+=1 end
end
check(projectedChanged==1,"only selected skill affected by random")
print("P0D_V4_3SOURCE_PIPELINE_NATIVE_"..tostring(n).."_ASSERTIONS_PASS")
"""
    return lua

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--write",required=True)
    args=ap.parse_args()
    Path(args.write).write_text(build(),encoding="utf8")
    print("V4_NATIVE_THREE_SOURCE_PINNED",",".join(BLOBS.values()))
