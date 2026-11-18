#!/usr/bin/env python3
"""Produce source-derived genuine native Luau positive/negative cases and a replay mutant."""
import argparse
from pathlib import Path

SOURCE = Path(__file__).with_name("MageRevivePolicy.luau")
MUTATE = 'if type(attempt) ~= "table" or attempt.consumed ~= false then return 0, "TOKEN_USED" end'
TEST = r'''
__SOURCE__
local policy = M
local function context()
 return {
  now=100,maxHP=195,sessionId="TEAM-701",roundId="roundA",
  casterId="human-mage",targetId="ally-2",
  casterAvatarId="m1",targetAvatarId="t1",
  active=true,currentCaster=true,currentTarget=true,
  sameTeam=true,teamMode="TEAM",casterIsMage=true,casterAlive=true,
  inRange=true,lineClear=true,casterInterrupted=false,
  lastHealAt=80,targetHP=80,targetAlive=true,targetDowned=false,
  targetEliminated=false,downedAt=96,lastReviveAt=0,
  alreadyChanneling=false,casterHitSinceStart=false,
 }
end
local function denied(fn, expected, c, attempt)
 local val, why
 if attempt then val,why=fn(attempt,c) else val,why=fn(c) end
 assert(val==0 or val==nil, "RED_UNEXPECTED_POSITIVE_"..expected)
 assert(why==expected,"RED_DENIAL_"..expected.."_"..tostring(why))
end
local c=context()
local amount, why=policy.healDelta(c)
assert(why=="HEAL_READY" and math.abs(amount-58.5)<.00001,"RED_HEAL_30_PERCENT")
c.lastHealAt=82.001
denied(policy.healDelta,"HEAL_COOLDOWN",c)
c.lastHealAt=82
assert(select(2,policy.healDelta(c))=="HEAL_READY","RED_18S_EDGE")
c.targetHP=190
assert(math.abs(select(1,policy.healDelta(c))-5)<.0001,"RED_NO_OVERHEAL")
c.targetHP=80
c.targetDowned=true
c.targetAlive=false
denied(policy.healDelta,"TARGET_DOWNED",c)
local token, msg=policy.beginRevive(c)
assert(token~=nil and msg=="CHANNEL_STARTED","RED_START")
c.now=102.999
denied(policy.finishRevive,"CHANNEL_EARLY",c,token)
c.now=103
amount,why=policy.finishRevive(token,c)
assert(why=="REVIVE_READY" and amount==68,"RED_35_PERCENT_REVIVE")
amount,why=policy.finishRevive(token,c)
assert(amount==0 and why=="TOKEN_USED","RED_REPLAY")
assert(not policy.cancelRevive(token),"RED_CANCEL_REPLAY")
local cancelC=context()
cancelC.targetDowned=true
cancelC.targetAlive=false
local t=select(1,policy.beginRevive(cancelC))
assert(policy.cancelRevive(t)==true,"RED_CANCEL")
cancelC.now=103
denied(policy.finishRevive,"TOKEN_USED",cancelC,t)
local function tryDenial(field,value,expected)
 local x=context()
 x.targetDowned=true;x.targetAlive=false
 local attempt=select(1,policy.beginRevive(x))
 assert(attempt,"RED_FIXTURE_"..field)
 x.now=103
 x[field]=value
 denied(policy.finishRevive,expected,x,attempt)
end
tryDenial("active",false,"STALE_MATCH")
tryDenial("currentCaster",false,"STALE_MATCH")
tryDenial("currentTarget",false,"STALE_MATCH")
tryDenial("roundId","roundB","TOKEN_STALE")
tryDenial("sessionId","TEAM-702","TOKEN_STALE")
tryDenial("casterAvatarId","m2","TOKEN_STALE")
tryDenial("targetAvatarId","t2","TOKEN_STALE")
tryDenial("sameTeam",false,"NOT_TEAMMATE")
tryDenial("teamMode","BR","NOT_TEAMMATE")
tryDenial("casterIsMage",false,"NOT_LIVING_MAGE")
tryDenial("casterAlive",false,"NOT_LIVING_MAGE")
tryDenial("lineClear",false,"OUT_OF_REACH")
tryDenial("inRange",false,"OUT_OF_REACH")
tryDenial("casterHitSinceStart",true,"INTERRUPTED")
tryDenial("casterInterrupted",true,"INTERRUPTED")
tryDenial("targetEliminated",true,"TARGET_NOT_DOWNED")
tryDenial("targetDowned",false,"TARGET_NOT_DOWNED")
tryDenial("downedAt",95,"DOWNED_EXPIRED")
tryDenial("lastReviveAt",80,"REVIVE_COOLDOWN")
local expired=context()
expired.now=100;expired.downedAt=39
expired.targetAlive=false;expired.targetDowned=true
denied(policy.beginRevive,"DOWNED_EXPIRED",expired)
local overlap=context()
overlap.targetAlive=false;overlap.targetDowned=true;overlap.alreadyChanneling=true
denied(policy.beginRevive,"CHANNEL_BUSY",overlap)
local br=context()
br.targetAlive=false;br.targetDowned=true;br.teamMode="BR"
denied(policy.beginRevive,"NOT_TEAMMATE",br)
local clock=context()
clock.targetAlive=false;clock.targetDowned=true
local old=select(1,policy.beginRevive(clock))
clock.now=105.001
denied(policy.finishRevive,"CHANNEL_EXPIRED",clock,old)
local bad=context();bad.now=0/0
denied(policy.healDelta,"BAD_NUMBER",bad)
local roleHP={WARRIOR=250,MAGE=195,NINJA=185,TRAPPER=205,BUILDER=225,BEAST=220,ZOMBIE=230}
local count=0
for _,hp in pairs(roleHP) do
 local tctx=context();tctx.maxHP=hp;tctx.targetDowned=true;tctx.targetAlive=false
 local tkn=select(1,policy.beginRevive(tctx));tctx.now=103
 local recovered,reason=policy.finishRevive(tkn,tctx)
 assert(reason=="REVIVE_READY" and recovered==math.max(1,math.floor(hp*.35+.5)),"RED_ROLE_REVIVE_RATIO")
 count+=1
end
assert(count==7,"RED_ROLE_COUNT")
print("GQ8_MAGE_REVIVE_NATIVE_7_ROLE_GOOD")
'''
def main(out):
 src=SOURCE.read_text(encoding="utf-8")
 assert src.count(MUTATE)==1,"RED_MUTANT_ANCHOR"
 assert src.rstrip().endswith("return M"),"RED_MODULE_END"
 prefix=src.rstrip()[:-len("return M")]
 mutant=prefix.replace(MUTATE,'if type(attempt) ~= "table" then return 0, "TOKEN_USED" end',1)
 out.mkdir(parents=True,exist_ok=True)
 (out/"good.luau").write_text(TEST.replace("__SOURCE__",prefix),encoding="utf-8")
 (out/"mutant.luau").write_text(TEST.replace("__SOURCE__",mutant),encoding="utf-8")
 print("GQ8_MAGE_REVIVE_NATIVE_FIXTURES_SOURCE_DERIVED")
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--out",type=Path,required=True)
 main(p.parse_args().out)
