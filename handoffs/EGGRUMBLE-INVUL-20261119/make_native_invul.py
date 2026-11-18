#!/usr/bin/env python3
"""Source-derived, true Luau-VM policy contract + two deliberate RED mutations.
No duplicated implementation: harness inlines exact immutable policy source.
"""
from pathlib import Path
import argparse

SRC=Path(__file__).with_name("InvulnerabilityPolicy.luau")
CONTRACT=r'''
__ACTUAL_POLICY_SOURCE__
local policy=M
local roleExpected={
 WARRIOR={1.6,2,55},
 MAGE={1.4,2,60},
 NINJA={.9,3,38},
 TRAPPER={1.7,2,60},
 BUILDER={2.2,1,75},
 BEAST={1.5,2,60},
 ZOMBIE={1.5,2,65},
}
local function ctx(role,t,epoch)
 return {epoch=epoch or "MATCH001",playerId="user01",avatarEpoch="avatarA",
  phase="ACTIVE",mode="TEAM",role=role,now=t,serverCurrent=true,
  characterAlive=true,roleVerified=true,castleAlive=true,downed=false,
  eliminated=false,carryingEgg=false,shieldActive=false,
  itemOwned=true,weaponHeld=true,guardSucceeded=true}
end
local count=0
for role,spec in pairs(roleExpected) do
 local s=policy.newRound("MATCH001")
 local c=ctx(role,100)
 local active,data=policy.activate(s,c,"SKILL")
 assert(active and math.abs(data.duration-spec[1])<.00001,"RED_ROLE_TIME")
 assert(policy.damageMultiplier(s,c)==0,"RED_DAMAGE_LEAK")
 assert(policy.allowNewStatus(s,c)==false,"RED_CC_DURING_INVUL")
 assert(policy.attackMultiplier(s,c,"REGULAR")==.6,"RED_OFFENSE_COST")
 assert(policy.attackMultiplier(s,c,"SIEGE")==0,"RED_INVUL_EGG_SIEGE")
 assert(policy.allowObjectiveAction(s,c)==false,"RED_OBJECTIVE_EXPLOIT")
 local again,why=policy.activate(s,c,"SKILL")
 assert(not again and why=="ALREADY_ACTIVE","RED_STACK_OR_REFRESH")
 c.now=100+spec[1]+.001
 assert(policy.damageMultiplier(s,c)==1,"RED_PERMANENT_IMMUNITY")
 assert(policy.allowNewStatus(s,c),"RED_STATUS_PERMANENT_BLOCK")
 assert(policy.attackMultiplier(s,c,"REGULAR")==1,"RED_PERMANENT_ATTACK_PENALTY")
 assert(policy.allowObjectiveAction(s,c),"RED_PERMANENT_OBJECTIVE_LOCK")
 for i=2,spec[2] do
  c.now=100+(i-1)*(spec[3]+1)
  local ok,result=policy.activate(s,c,"SKILL")
  assert(ok,"RED_ROLE_CHARGES_NOT_USABLE_"..role)
  assert(result.used==i,"RED_ROLE_CHARGE_STATE")
 end
 c.now=100+spec[2]*(spec[3]+1)+20
 local ok,why=policy.activate(s,c,"SKILL")
 assert(not ok and why=="MATCH_CHARGE_EXHAUSTED","RED_INFINITE_ROLE_CHARGES")
 count+=1
end
assert(count==7,"RED_MISSING_ROLE")
local s=policy.newRound("MATCH001")
local c=ctx("WARRIOR",100)
c.itemOwned=false
local ok,why=policy.activate(s,c,"ITEM")
assert(not ok and why=="NO_FREE_ITEM","RED_FAKE_ITEM")
c.itemOwned=true
c.guardSucceeded=false
ok,why=policy.activate(s,c,"GUARD")
assert(not ok and why=="GUARD_NOT_PERFECT","RED_FAKE_WEAPON_GUARD")
c.guardSucceeded=true
ok=policy.activate(s,c,"SKILL")
assert(ok,"RED_INITIAL_FREE_SKILL")
c.now=119
ok,why=policy.activate(s,c,"SKILL")
assert(not ok and why=="SOURCE_COOLDOWN","RED_BYPASS_ROLE_COOLDOWN")
ok,why=policy.activate(s,c,"ITEM")
assert(ok,"RED_ITEM_NOT_ACCESSIBLE")
local dt=s.entries.user01.total
assert(math.abs(dt-2.8)<.00001,"RED_ITEM_DURATION")
c.now=140
ok,why=policy.activate(s,c,"ITEM")
assert(not ok and why=="MATCH_CHARGE_EXHAUSTED","RED_INFINITE_ITEM")
c.now=160
ok,why=policy.activate(s,c,"SKILL")
assert(ok,"RED_SECOND_ROLE_USE")
c.now=181
local success,guard=policy.activate(s,c,"GUARD")
assert(success,"RED_WEAPON_PERFECT_GUARD_NOT_USABLE")
assert(math.abs(guard.duration-.6)<.00001,"RED_TOTAL_BUDGET")
assert(math.abs(s.entries.user01.total-5.0)<.00001,"RED_TOTAL_BUDGET")
c.now=200
ok,why=policy.activate(s,c,"GUARD")
assert(not ok and why=="MATCH_CHARGE_EXHAUSTED","RED_INFINITE_GUARD")
-- One match, different avatar: old invulnerability ends but charges never refill.
local state=policy.newRound("MATCH001")
local p=ctx("NINJA",100)
assert(policy.activate(state,p,"SKILL"),"RED_NINJA_SETUP")
p.avatarEpoch="avatarB"
assert(not policy.isInvulnerable(state,p),"RED_RESPAWN_INHERITS_INVUL")
p.now=139
assert(policy.activate(state,p,"SKILL"),"RED_AVATAR_SWITCH_CANNOT_PLAY")
assert(state.entries.user01.uses.SKILL==2,"RED_RESPAWN_CHARGE_REFILL")
p.now=140
p.carryingEgg=true
assert(policy.damageMultiplier(state,p)==1,"RED_EGG_CARRIER_INVUL")
policy.cancelOnObjectivePickup(state,p)
p.carryingEgg=false
assert(policy.damageMultiplier(state,p)==1,"RED_DROP_EGG_RESTORES_INVUL")
-- Wrong round, stale actor, shield, downed, mode, dead, reversed clock.
p.now=160
p.epoch="WRONG_ROUND"
assert(policy.damageMultiplier(state,p)==1,"RED_WRONG_ROUND")
local fake=ctx("MAGE",100)
fake.serverCurrent=false
assert(not policy.activate(policy.newRound("MATCH001"),fake,"SKILL"),"RED_REMOTE_TRUST")
fake=ctx("MAGE",100);fake.downed=true
assert(not policy.activate(policy.newRound("MATCH001"),fake,"SKILL"),"RED_DOWNED_SKILL")
fake=ctx("MAGE",100);fake.shieldActive=true
assert(not policy.activate(policy.newRound("MATCH001"),fake,"SKILL"),"RED_SHIELD_STACK")
fake=ctx("MAGE",100);fake.carryingEgg=true
assert(not policy.activate(policy.newRound("MATCH001"),fake,"SKILL"),"RED_EGG_SKILL")
fake=ctx("MAGE",100);fake.mode="UNKNOWN"
assert(not policy.activate(policy.newRound("MATCH001"),fake,"SKILL"),"RED_WRONG_MODE")
fake=ctx("MAGE",100);fake.characterAlive=false
assert(not policy.activate(policy.newRound("MATCH001"),fake,"SKILL"),"RED_DEAD_SKILL")
fake=ctx("MAGE",0/0)
assert(not policy.activate(policy.newRound("MATCH001"),fake,"SKILL"),"RED_NAN_CLOCK")
local reset=policy.newRound("MATCH002")
assert(policy.activate(reset,ctx("WARRIOR",1,"MATCH002"),"SKILL"),
 "RED_NEW_MATCH_MISSING_FREE_SKILL")
print("GQ8_INVUL_SOURCE_VM_7ROLE_SKILL_ITEM_GUARD_NO_STACK_TEAM_ROLLBACK_PASS")
'''

def emit(out:Path):
 src=SRC.read_text(encoding="utf-8")
 end="return M"
 if not src.rstrip().endswith(end):raise ValueError("RED_SOURCE_MUST_RETURN_MODULE")
 body=src.rstrip()[:-len(end)]
 if body.count("M.MAX_MATCH_SECONDS=5.0")!=1 or body.count("return 0")<1:
  raise ValueError("RED_EXPECTED_POLICY_SIGNATURE")
 out.mkdir(parents=True,exist_ok=True)
 good=CONTRACT.replace("__ACTUAL_POLICY_SOURCE__",body)
 (out/"good.luau").write_text(good,encoding="utf-8")
 mutant1=body.replace("M.MAX_MATCH_SECONDS=5.0","M.MAX_MATCH_SECONDS=50.0")
 (out/"budget_mutant.luau").write_text(CONTRACT.replace("__ACTUAL_POLICY_SOURCE__",mutant1))
 mutant2=body.replace("if M.isInvulnerable(s,c) then return 0 end",
                     "if M.isInvulnerable(s,c) then return 1 end")
 if mutant2==body:raise ValueError("RED_MUTANT_LEAK_FAILED")
 (out/"damage_mutant.luau").write_text(CONTRACT.replace("__ACTUAL_POLICY_SOURCE__",mutant2))
 print("GQ8_INVUL_REAL_POLICY_SOURCE_TESTS_GENERATED")

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--out",required=True,type=Path)
 a=p.parse_args()
 emit(a.out)
