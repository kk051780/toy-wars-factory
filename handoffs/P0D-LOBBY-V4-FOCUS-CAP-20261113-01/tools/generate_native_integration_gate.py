#!/usr/bin/env python3
"""A genuine Luau native runtime QA using exact fixed Git blob source for V4 gate."""
from pathlib import Path
import hashlib
import argparse
ROOT=Path(__file__).resolve().parents[1]
SOURCE_BLOB="45c6c3a51ca0fc6a0167d50b217f05c1323e52b3"
def git_blob(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()
def build() -> str:
    content=(ROOT/"src/TrainingIntegrationGate.luau").read_bytes()
    assert git_blob(content)==SOURCE_BLOB, "V4 gate source drift"
    source=content.decode("utf8").rstrip()
    assert source.endswith("return Gate")
    return source[:-len("return Gate")]+r"""
local assertions=0
local function check(test,label)
    assertions+=1
    if not test then error("assert "..tostring(assertions).." "..label) end
end
local six={BEAST=true,MAGIC=true,WEAPON=true,ZOMBIE=true,VEHICLE=true,BUILDING=true}
local caps={
    skills=six,
    singleXPAuthority=true,
    persistentProfile=true,
    atomicSessionLock=true,
    friendModel="COUNT_25_CAP4",
    acceptsMicroXP=true,
    serverAuthoritativeTime=true,
    pvpNormalized=true,
    maxSegmentSeconds=120,
}
local function clone(base)
    local value={}
    for k,v in pairs(base) do value[k]=v end
    return value
end
local ok,blocked=Gate.checkCapabilities(caps)
check(ok and #blocked==0,"complete caps ready")
local legacy=clone(caps)
legacy.skills={BEAST=true,WEAPON=true}
legacy.persistentProfile=false
legacy.friendModel="BOOLEAN_1_5"
legacy.maxSegmentSeconds=1.5
ok,blocked=Gate.checkCapabilities(legacy)
check(not ok and #blocked>=6,"legacy 2-skill dojo must be blocked")
local codes={}
for _,p in ipairs(blocked) do codes[p]=true end
check(codes.MISSING_SKILL_MAGIC,"missing magic")
check(codes.MISSING_SKILL_ZOMBIE,"missing zombie")
check(codes.MISSING_SKILL_VEHICLE,"missing vehicle")
check(codes.MISSING_SKILL_BUILDING,"missing building")
check(codes.NO_PERSISTENT_PROFILE,"legacy no save")
check(codes.WRONG_FRIEND_BONUS_MODEL,"legacy boolean friend")
check(codes.SEGMENT_DURATION_UNSUPPORTED,"legacy tiny delta")
local legacyNoGrant=Gate.quote(legacy,{{skill="BEAST",seconds=60,bonusBps=10000,mode="FOCUS"}},10000,"srv-tick-0001")
check(not legacyNoGrant.ok and #legacyNoGrant.grants==0,"not credited if legacy")
local s1={{skill="BEAST",seconds=60,bonusBps=10000,mode="FOCUS"}}
local quote=Gate.quote(caps,s1,10000,"server-step-00000001")
check(quote.ok and quote.applied==false,"quote is not applied")
check(quote.grantCount==1 and quote.grants[1].skill=="BEAST","one skill")
check(quote.totalSeconds==60 and quote.totalMicroXP==600000000,"base XP quote 600")
check(quote.grants[1].bonusBps==10000,"0 friends")
local twoFriends=Gate.quote(caps,{{skill="WEAPON",seconds=60,bonusBps=15000,mode="FOCUS"}},10000,"server-step-00000002")
check(twoFriends.ok and twoFriends.totalMicroXP==900000000,"2 friends x1.5")
local fourFriends=Gate.quote(caps,{{skill="MAGIC",seconds=60,bonusBps=20000,mode="RANDOM"}},10000,"server-step-00000003")
check(fourFriends.ok and fourFriends.totalMicroXP==1200000000,"4 friends x2")
local all={}
local idx=0
for _,skill in ipairs(Gate.EXPECTED_SKILLS) do
    idx+=1
    table.insert(all,{skill=skill,seconds=10,bonusBps=10000,mode="RANDOM"})
end
local multi=Gate.quote(caps,all,10000,"server-multiskill-00004")
check(multi.ok and multi.grantCount==6,"six skill support")
check(multi.totalSeconds==60 and multi.totalMicroXP==600000000,"no time lost in six")
local missingCaps=Gate.quote(nil,s1,10000,"server-step-00000001")
check(not missingCaps.ok and missingCaps.problem=="INTEGRATION_BLOCKED","missing caps fail closed")
local noSave=clone(caps)
noSave.persistentProfile=false
check(not Gate.quote(noSave,s1,10000,"server-step-00000001").ok,"no saved profile no quote")
local noLock=clone(caps)
noLock.atomicSessionLock=false
check(not Gate.quote(noLock,s1,10000,"server-step-00000001").ok,"no lock no quote")
local pvp=clone(caps)
pvp.pvpNormalized=false
check(not Gate.quote(pvp,s1,10000,"server-step-00000001").ok,"PVP normalize required")
local clock=clone(caps)
clock.serverAuthoritativeTime=false
check(not Gate.quote(clock,s1,10000,"server-step-00000001").ok,"no client clock")
check(Gate.quote(caps,s1,10000,"client").problem=="BAD_SERVER_NONCE","short nonce")
check(Gate.quote(caps,s1,0,"server-step-00000001").problem=="BAD_XP_RATE","zero rate")
check(Gate.quote(caps,{},10000,"server-step-00000001").problem=="BAD_SEGMENTS","empty segments")
check(Gate.quote(caps,{{skill="UNKNOWN",seconds=60,bonusBps=10000,mode="FOCUS"}},10000,"server-step-00000001").problem=="INVALID_SEGMENT","skill unsupported")
check(Gate.quote(caps,{{skill="BEAST",seconds=60,bonusBps=22500,mode="FOCUS"}},10000,"server-step-00000001").problem=="INVALID_SEGMENT","friend cap overflow")
check(Gate.quote(caps,{{skill="BEAST",seconds=60,bonusBps=12345,mode="FOCUS"}},10000,"server-step-00000001").problem=="INVALID_SEGMENT","bonus tampering")
check(Gate.quote(caps,{{skill="BEAST",seconds=0,bonusBps=10000,mode="FOCUS"}},10000,"server-step-00000001").problem=="INVALID_SEGMENT","zero seconds")
check(Gate.quote(caps,{{skill="BEAST",seconds=121,bonusBps=10000,mode="FOCUS"}},10000,"server-step-00000001").problem=="INVALID_SEGMENT","segment too big")
check(Gate.quote(caps,{{skill="BEAST",seconds=100,bonusBps=10000,mode="FOCUS"},{skill="WEAPON",seconds=21,bonusBps=12500,mode="RANDOM"}},10000,"server-step-00000001").problem=="EXCESS_SESSION_SECONDS","total too large")
check(Gate.quote(caps,{{skill="BEAST",seconds=1,bonusBps=10000,mode="IDLE"}},10000,"server-step-00000001").problem=="INVALID_SEGMENT","cannot idle grant")
check(Gate.quote(caps,{{skill="BEAST",seconds=1,bonusBps=10000,mode="FOCUS"}},1,"server-step-00000001").totalMicroXP==1000,"micro precise 0.001XP")
check(Gate.quote(caps,{{skill="BEAST",seconds=1,bonusBps=12500,mode="FOCUS"}},1,"server-step-00000001").totalMicroXP==1250,"micro precise +25pct")
check(not Gate.quote(caps,s1,10000,{}).ok,"nonce not string")
check(not Gate.quote(caps,s1,math.huge,"server-step-00000001").ok,"infinity rate rejected")
print("P0D_V4_INTEGRATION_GATE_NATIVE_"..tostring(assertions).."_ASSERTIONS_PASS")
"""
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--write",required=True)
    args=ap.parse_args()
    Path(args.write).write_text(build(),encoding="utf8")
    print("PINNED_GATE_SOURCE_BLOB",SOURCE_BLOB)
