#!/usr/bin/env python3
"""Actual source-derived Luau VM proof for OWNER #822 reactive awakening V2.
No duplicate policy in the harness; two malicious mutations must fail.
"""
from pathlib import Path
import argparse
SRC=Path(__file__).with_name("InvulnerabilityPolicy.luau")
HARNESS=r'''
__SOURCE__
local policy=M
local expected={
 WARRIOR={7,2,75,"DIVINE_SINGLE_COUNTER"},
 MAGE={9,2,85,"ARCANE_NULL_DOMAIN"},
 NINJA={6,3,60,"SHADOW_SINGLE_EXECUTION"},
 TRAPPER={7.5,2,80,"PSYCHIC_REFLECTION"},
 BUILDER={9,2,90,"AEGIS_LAB"},
 BEAST={7.5,2,80,"BEAST_REPRISAL"},
 ZOMBIE={8,2,85,"CURSE_SEAL_REVERSAL"},
}
local function ctx(role,t,epoch)
 return {epoch=epoch or "M1",playerId="p1",avatarEpoch="a1",role=role,now=t,
  phase="ACTIVE",mode="TEAM",serverCurrent=true,characterAlive=true,
  roleVerified=true,castleAlive=true,downed=false,eliminated=false,
  carryingEgg=false,shieldActive=false,itemOwned=true,
  weaponHeld=true,guardSucceeded=true}
end
local function hit(n,attacker,kind)
 return {serverVerified=true,hostile=true,damage=23,attackId="hit"..n,
  attackerId=attacker or "enemyA",kind=kind or "PLAYER"}
end
local roleCount=0
for role,spec in pairs(expected) do
 local s=policy.newRound("M1")
 local c=ctx(role,100)
 local ok,armed=policy.arm(s,c,"SKILL")
 assert(ok and armed.phase=="ARMED" and not armed.consumed,"RED_ARM_NOT_PREP")
 assert(policy.damageMultiplier(s,c)==1,"RED_PREHIT_FREE_INVUL")
 assert(policy.allowNewStatus(s,c),"RED_PREHIT_CC_INVUL")
 local hostile=hit("zero")
 hostile.hostile=false
 local invalid=policy.onIncomingDamage(s,c,hostile)
 assert(not invalid.blocked,"RED_UNVERIFIED_HIT_TRIGGER")
 local env=hit("weather","weather","ENVIRONMENT")
 assert(not policy.onIncomingDamage(s,c,env).blocked,"RED_ENVIRONMENT_TRIGGER")
 c.now=101
 local first=policy.onIncomingDamage(s,c,hit("one","enemyA"))
 assert(first.blocked and first.multiplier==0 and first.awakened,"RED_FIRST_HIT_NOT_ZERO")
 assert(math.abs(first.duration-spec[1])<.00001,"RED_ROLE_AWAKENING_TOO_SHORT")
 assert(first.kind==spec[4],"RED_MISSING_ROLE_SPECIAL")
 assert(policy.damageMultiplier(s,c)==0,"RED_DAMAGE_LEAK")
 assert(not policy.allowNewStatus(s,c),"RED_CC_LEAK")
 assert(policy.attackMultiplier(s,c,"NORMAL")==.80,"RED_AWAKENING_ATTACK_COST")
 assert(policy.attackMultiplier(s,c,"AUTHORIZED_COUNTER")==1,"RED_COUNTER_ATTACK_LOCKED")
 assert(policy.attackMultiplier(s,c,"SIEGE")==0,"RED_INVUL_SIEGE_ABUSE")
 assert(not policy.allowObjectiveAction(s,c),"RED_INVUL_EGG_PICKUP")
 local again,why=policy.arm(s,c,"SKILL")
 assert(not again and why=="ALREADY_AWAKENED","RED_STACKED_AWAKEN")
 for n=2, spec[4]=="ARCANE_NULL_DOMAIN" and 3 or policy.ROLES[role].hits do
  c.now+=.1
  local block=policy.onIncomingDamage(s,c,hit("many"..n,"enemy"..n))
  assert(block.blocked and block.multiplier==0,"RED_MULTI_HIT_LEAK")
 end
 assert(policy.snapshot(s,c).blockedHits>=policy.ROLES[role].hits,"RED_HIT_COUNT")
 local target={serverVerified=true,alive=true,inRange=true,lineOfSight=true,
  id="enemyA",class="MINION",hpFraction=.8}
 local command,reason=policy.claimCounter(s,c,target)
 assert(command and command.kind==spec[4] and not command.damageDirectlyApplied,
  "RED_ROLE_COUNTER_MISSING_"..tostring(reason))
 if role=="WARRIOR" or role=="NINJA" then
  assert(command.effect=="INSTANT_SINGLE_NEUTRAL_KO","RED_SINGLE_KO")
 elseif role=="MAGE" then
  assert(command.effect=="MULTI_SOURCE_NULL_BURST","RED_MAGE_MULTI_NULL")
 elseif role=="TRAPPER" then
  assert(command.reflectCapPerTarget==.18,"RED_TRAPPER_REFLECT_CAP")
 elseif role=="BUILDER" then
  assert(command.allyDuration==3,"RED_SCIENTIST_TEAM_BARRIER")
 elseif role=="BEAST" then
  assert(command.effect=="BEAST_COUNTER_CHARGE","RED_BEAST_CHARGE")
 elseif role=="ZOMBIE" then
  assert(command.maxConverted==1,"RED_CURSE_INFINITE_CONVERT")
 end
 assert(policy.claimCounter(s,c,target)==nil,"RED_INFINITE_COUNTER")
 local got,extra=policy.rewardConfirmedCounter(s,c,{
  serverVerified=true,hitConfirmed=true,kind="NEUTRAL"})
 assert(got and extra.bonus==1.5,"RED_NEUTRAL_CHAIN_BONUS")
 assert(not policy.rewardConfirmedCounter(s,c,{serverVerified=true,hitConfirmed=true,kind="NEUTRAL"}),
  "RED_CHAIN_INFINITE_EXTENSION")
 c.now=101+spec[1]+1.501
 assert(policy.damageMultiplier(s,c)==1,"RED_PERMANENT_INVUL")
 assert(policy.allowNewStatus(s,c),"RED_PERMANENT_CC_BLOCK")
 assert(policy.attackMultiplier(s,c,"SIEGE")==1,"RED_PERMANENT_OFFENSE_LOCK")
 for k=2,spec[2] do
  c.now=100+(k-1)*(spec[3]+5)
  assert(policy.arm(s,c,"SKILL"),"RED_SKILL_CHARGE_BLOCKED")
  c.now+=1
  local nextHit=policy.onIncomingDamage(s,c,hit("new"..k))
  assert(nextHit.awakened,"RED_NEXT_AWAKENING_MISSING")
 end
 c.now=100+spec[2]*(spec[3]+5)+10
 local more,reason=policy.arm(s,c,"SKILL")
 assert(not more and reason=="MATCH_CHARGE_EXHAUSTED","RED_INFINITE_SKILL")
 roleCount+=1
end
assert(roleCount==7,"RED_NOT_SEVEN_ROLES")
local s=policy.newRound("M1")
local c=ctx("WARRIOR",100)
c.itemOwned=false
assert(not policy.arm(s,c,"ITEM"),"RED_FAKE_ITEM")
c.itemOwned=true
c.guardSucceeded=false
assert(not policy.arm(s,c,"GUARD"),"RED_FAKE_GUARD")
c.guardSucceeded=true
assert(policy.arm(s,c,"SKILL"),"RED_FREE_INITIAL_SKILL")
c.now=104
assert(policy.damageMultiplier(s,c)==1,"RED_MISSED_ARM_GIVES_INVUL")
assert(s.entries.p1.used.SKILL==0,"RED_MISS_CONSUMED_CHARGE")
local miss,why=policy.arm(s,c,"SKILL")
assert(not miss and why=="EMPTY_RETRY","RED_MISSED_GUARD_SPAM")
c.now=113
assert(policy.arm(s,c,"SKILL"),"RED_CAN_RETRY_MISSED_GUARD")
c.now=114
assert(policy.onIncomingDamage(s,c,hit("newattack")).blocked,"RED_RETRY_INCOMING_NOT_ZERO")
c.now=155
assert(policy.arm(s,c,"ITEM"),"RED_ITEM_ARM")
c.now=156
local item=policy.onIncomingDamage(s,c,hit("itemhit"))
assert(item.awakened and item.duration==3.5,"RED_ITEM_NOT_3_5S")
c.now=197
local dup,why=policy.arm(s,c,"ITEM")
assert(not dup and why=="MATCH_CHARGE_EXHAUSTED","RED_ITEM_DUPLICATION")
assert(policy.arm(s,c,"GUARD"),"RED_GUARD_ARM")
c.now=197.2
local guard=policy.onIncomingDamage(s,c,hit("perfect"))
assert(guard.awakened and guard.duration==2.2,"RED_PERFECT_GUARD_TIME")
assert(s.entries.p1.total==12.7,"RED_MIXED_SOURCE_TOTAL")
c.now=240
local dupGuard,why=policy.arm(s,c,"GUARD")
assert(not dupGuard and why=="MATCH_CHARGE_EXHAUSTED","RED_GUARD_DUPLICATION")
-- cap at 24 seconds even when role+item+guard are used across sources.
local cap=policy.newRound("M1")
local cp=ctx("BUILDER",100)
assert(policy.arm(cap,cp,"SKILL"),"RED_CAP_SETUP")
cp.now=101
assert(policy.onIncomingDamage(cap,cp,hit("first")).blocked,"RED_CAP_FIRST_HIT")
cap.entries.p1.total=23.75
cp.now=200
assert(policy.arm(cap,cp,"ITEM"),"RED_CAP_ITEM_ARM")
cp.now=201
local capped=policy.onIncomingDamage(cap,cp,hit("cap"))
assert(capped.duration==.25 and cap.entries.p1.total==24,"RED_24S_MATCH_BUDGET")
-- revive/respawn and egg pickup cannot mint unlimited invulnerability.
local life=policy.newRound("M1")
local lp=ctx("NINJA",100)
assert(policy.arm(life,lp,"SKILL"),"RED_NINJA_ARM")
lp.now=101
assert(policy.onIncomingDamage(life,lp,hit("life")).blocked,"RED_LIFE_HIT")
lp.avatarEpoch="a2"
assert(policy.damageMultiplier(life,lp)==1,"RED_OLD_AVATAR_IMMUNE")
assert(life.entries.p1.used.SKILL==1,"RED_RESPAWN_CHARGE_REFILL")
lp.now=200
assert(policy.arm(life,lp,"SKILL"),"RED_NEW_AVATAR_USE")
lp.now=201
assert(policy.onIncomingDamage(life,lp,hit("afterrespawn")).blocked,"RED_NEW_AVATAR_HIT")
lp.carryingEgg=true
assert(policy.damageMultiplier(life,lp)==1,"RED_EGG_CARRIER_IMMUNE")
policy.cancelOnObjectivePickup(life,lp)
lp.carryingEgg=false
assert(policy.damageMultiplier(life,lp)==1,"RED_EGG_DROP_RESTORES")
lp.now=202;lp.epoch="OTHER"
assert(policy.damageMultiplier(life,lp)==1,"RED_CROSS_MATCH")
local zombie=policy.newRound("M2")
local zp=ctx("ZOMBIE",100,"M2")
zp.mode="BATTLE_ROYALE"
assert(policy.arm(zombie,zp,"SKILL"),"RED_BR_UNFAIRLY_DISABLED")
zp.now=101
assert(policy.onIncomingDamage(zombie,zp,hit("zombie","enemyB","PLAYER")).blocked,
 "RED_BR_COUNTER_NOT_TRIGGERED")
zp.now=101.1
assert(policy.onIncomingDamage(zombie,zp,hit("environment","weather","ENVIRONMENT")).blocked,
 "RED_AWAKENING_WEATHER_DAMAGE_LEAK")
local fail=ctx("MAGE",0/0)
assert(not policy.arm(policy.newRound("M1"),fail,"SKILL"),"RED_CLIENT_NAN_CLOCK")
fail=ctx("MAGE",100);fail.downed=true
assert(not policy.arm(policy.newRound("M1"),fail,"SKILL"),"RED_DOWNED_INVUL")
fail=ctx("MAGE",100);fail.shieldActive=true
assert(not policy.arm(policy.newRound("M1"),fail,"SKILL"),"RED_SHIELD_STACK")
fail=ctx("MAGE",100);fail.carryingEgg=true
assert(not policy.arm(policy.newRound("M1"),fail,"SKILL"),"RED_EGG_IMMUNE")
fail=ctx("MAGE",100);fail.serverCurrent=false
assert(not policy.arm(policy.newRound("M1"),fail,"SKILL"),"RED_CLIENT_SPOOF")
print("GQ8_INVUL_REACTIVE_V2_NATIVE7ROLE_MULTISOURCE_COUNTER_PVP_GUARDS_PASS")
'''
def emit(out:Path):
 src=SRC.read_text(encoding="utf-8")
 end="return M"
 if not src.rstrip().endswith(end):raise ValueError("RED_INVALID_MODULE_RETURN")
 body=src.rstrip()[:-len(end)]
 patterns=["M.MAX_MATCH_SECONDS=24.0","M.ARM_SECONDS=3.0",
           "return if M.isInvulnerable(s,c) then 0 else 1",
           "e.used[e.source]+=1"]
 for p in patterns:
  if body.count(p)!=1:raise ValueError("RED_SOURCE_SIGNATURE_"+p)
 out.mkdir(parents=True,exist_ok=True)
 good=HARNESS.replace("__SOURCE__",body)
 (out/"good.luau").write_text(good,encoding="utf-8")
 mutant1=body.replace("M.MAX_MATCH_SECONDS=24.0","M.MAX_MATCH_SECONDS=240.0")
 mutant2=body.replace("return if M.isInvulnerable(s,c) then 0 else 1",
                      "return if M.isInvulnerable(s,c) then 1 else 1")
 mutant3=body.replace("e.used[e.source]+=1","e.used[e.source]+=0")
 for name,content in [("budget_mutant",mutant1),("damage_mutant",mutant2),
                      ("charge_mutant",mutant3)]:
  if content==body:raise ValueError("RED_MUTATION_FAILED_"+name)
  (out/(name+".luau")).write_text(HARNESS.replace("__SOURCE__",content),encoding="utf-8")
 print("GQ8_INVUL_REACTIVE_V2_ORIGINAL_SOURCE_NATIVE_HARNESS_READY")
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--out",type=Path,required=True)
 emit(p.parse_args().out)
