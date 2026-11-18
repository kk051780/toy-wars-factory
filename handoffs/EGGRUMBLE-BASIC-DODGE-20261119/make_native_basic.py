#!/usr/bin/env python3
"""Native Luau pure role-action policy tests and adversarial changes, source-derived."""
from pathlib import Path
import argparse
P=Path(__file__).resolve().parent
SOURCE=(P/"EGGRUMBLE_BasicMobilityPolicy.luau").read_text(encoding="utf8")
TEST=r'''
local policy=Policy
assert(policy.validate()==7,"RED_NOT_SEVEN_ROLES")
local roles={"WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE"}
local function ctx()
 return {
  serverVerified=true,roleVerified=true,ownsTool=true,
  phase="ACTIVE",mode="TEAM",alive=true,castleAlive=true,
  downed=false,eliminated=false,carryingEgg=false,seated=false,
  onGround=true,realm="LAND",matchEpoch="real59-test-round-1",
 }
end
for _,role in ipairs(roles) do
 local ledger={}
 local c=ctx()
 local ok,key,spec=policy.take(ledger,role,"BASIC",100,c)
 assert(ok and type(key)=="string" and spec.damage>=8 and spec.damage<=13,"RED_BASIC_NOT_APPROVED_"..role)
 local repeatOk=policy.take(ledger,role,"BASIC",100.1,c)
 assert(not repeatOk,"RED_BASIC_SPAM_"..role)
 assert(policy.take(ledger,role,"BASIC",101,c),"RED_BASIC_RECOVERY_"..role)
 ok,key,spec=policy.authorize(ledger,role,"DODGE",111,c)
 assert(ok and spec.distance<=10,"RED_VALID_GROUNDED_DODGE_"..role)
 assert(policy.take(ledger,role,"DODGE",111,c),"RED_DODGE_COMMIT_"..role)
 assert(not policy.take(ledger,role,"DODGE",111.1,c),"RED_DODGE_SPAM_"..role)
 c.carryingEgg=true
 assert(not policy.take(ledger,role,"DODGE",121,c),"RED_EGG_DODGE_CHEAT_"..role)
 assert(policy.take(ledger,role,"BASIC",121,c),"RED_EGG_DEFENSE_BLOCKED_"..role)
 c.carryingEgg=false
 c.onGround=false
 assert(not policy.take(ledger,role,"DODGE",130,c),"RED_AIR_DODGE_"..role)
 c.onGround=true;c.seated=true
 assert(not policy.take(ledger,role,"DODGE",130,c),"RED_SEAT_DODGE_"..role)
 c.seated=false;c.realm="SEA"
 assert(not policy.take(ledger,role,"DODGE",130,c),"RED_SEA_TELEPORT_"..role)
 c.realm="LAND";c.ownsTool=false
 assert(not policy.take(ledger,role,"BASIC",130,c),"RED_CLIENT_MINTED_TOOL_"..role)
 c.ownsTool=true;c.phase="LOBBY"
 assert(not policy.take(ledger,role,"BASIC",130,c),"RED_LOBBY_ATTACK_"..role)
 c.phase="ACTIVE";c.roleVerified=false
 assert(not policy.take(ledger,role,"BASIC",130,c),"RED_ROLE_SPOOF_"..role)
 c.roleVerified=true;c.serverVerified=false
 assert(not policy.take(ledger,role,"BASIC",130,c),"RED_CLIENT_FAKE_OWNER_"..role)
 c.serverVerified=true;c.eliminated=true
 assert(not policy.take(ledger,role,"BASIC",130,c),"RED_ELIMINATED_ATTACK_"..role)
 c.eliminated=false;c.matchEpoch=""
 assert(not policy.take(ledger,role,"BASIC",130,c),"RED_MISSING_MATCH_EPOCH_"..role)
 c.matchEpoch="real59-test-round-2"
 assert(policy.take(ledger,role,"BASIC",130,c),"RED_NEW_MATCH_STALE_CD_"..role)
end
assert(not policy.take({},"INVALID","BASIC",100,ctx()),"RED_UNKNOWN_ROLE")
assert(not policy.take({},"WARRIOR","PURCHASE",100,ctx()),"RED_UNKNOWN_ACTION_PURCHASE")
-- In production both TEAM rounds name their world TEAM_Arena. A world-name
-- cooldown key incorrectly carries 3-4s cooldown into the next game.
local firstSession={world={Name="TEAM_Arena"}}
local nextSession={world={Name="TEAM_Arena"}}
assert(firstSession.world.Name==nextSession.world.Name)
local firstCtx=ctx();firstCtx.matchEpoch=tostring(firstSession)
local nextCtx=ctx();nextCtx.matchEpoch=tostring(nextSession)
assert(firstCtx.matchEpoch~=nextCtx.matchEpoch,"RED_SESSION_EPOCH_NOT_UNIQUE")
local roundLedger={}
assert(policy.take(roundLedger,"WARRIOR","DODGE",200,firstCtx),"RED_ROUND1_DODGE")
assert(policy.take(roundLedger,"WARRIOR","DODGE",200,nextCtx),"RED_ROUND2_DODGE_BLEED")
assert(not policy.take(roundLedger,"WARRIOR","DODGE",200.1,nextCtx),"RED_ROUND2_SPAM")
assert(not policy.take({},"WARRIOR","BASIC",math.huge,ctx()),"RED_INFINITY")
assert(not policy.take({},"WARRIOR","BASIC",0/0,ctx()),"RED_NAN")
print("GQ828_REAL60_BASIC_DODGE_NATIVE_SEVEN_ROLE_COOLDOWN_ANTICHEAT_PASS")
'''
def compose(policy):
 return "local Policy=(function()\n"+policy+"\nend)()\n"+TEST
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args()
 a.out.mkdir(parents=True,exist_ok=False)
 (a.out/"positive.luau").write_text(compose(SOURCE),encoding="utf8")
 changes={
 "unowned":("ctx.ownsTool~=true","ctx.ownsTool==true"),
 "egg":("ctx.carryingEgg==true","ctx.carryingEgg~=true"),
 "cooldown":("now-last<spec.cooldown","now-last>spec.cooldown"),
 }
 for name,(before,after) in changes.items():
  assert SOURCE.count(before)==1,(name,"RED_MUTANT_ANCHOR_CHANGED")
  (a.out/(name+"_mutant.luau")).write_text(compose(SOURCE.replace(before,after)),encoding="utf8")
 print("GQ828_REAL60_NATIVE_ACTUAL_SOURCE_3_MUTANTS_GENERATED")
if __name__=="__main__":
 main()
