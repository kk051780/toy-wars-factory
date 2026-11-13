#!/usr/bin/env python3
"""Generate a standalone REAL native Luau Store+XP+Evolution transaction test.
Uses the exact generated source bodies; mocks UpdateAsync retry, never Roblox production.
"""
from pathlib import Path
import argparse,hashlib
root=Path(__file__).resolve().parents[1]
dist=root/"dist/EGG_RAID_RUMBLE_EARNED_EVOLUTION_FULL_H1_PRIVATE_STUDIO_ONLY/src/server"
def text(name):
 p=dist/name
 assert p.is_file(),p
 return p.read_text("utf8")
pro=text("ProgressionRules.luau")
evo=text("EvolutionRules.luau")
store=text("PersistentHatchStore.luau")
def blob(s):
 b=s.encode("utf8")
 return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
assert blob(evo)=="0efca67b41e34917038fdc883c8ad34f3eb3c2e2"
assert blob(pro)=="a72830b039a46ca02d02f6aab7d6a4805bec8860"
assert 'local Progression=require(script.Parent:WaitForChild("ProgressionRules"))' in store
assert 'local Evolution=require(script.Parent:WaitForChild("EvolutionRules"))' in store
store=store.replace('local Progression=require(script.Parent:WaitForChild("ProgressionRules"))',
                    'local Progression=__P')
store=store.replace('local Evolution=require(script.Parent:WaitForChild("EvolutionRules"))',
                    'local Evolution=__E')
TEST=r"""
local n=0
local function check(x,m) n+=1;assert(x,m) end
local validRound=function(id)
 return {id=id,mode="CLASSIC",outcome="WIN",duration=120,
  itemId="starter_scout",events={{id=id..":A",kind="PICKUP"},{id=id..":B",kind="DEPOSIT"}}}
end
local id1="Sabcdefghijklm:1"
local id2="Sabcdefghijklm:2"
local raw=Store.blank()
check(Store.validate(raw),"old schema profile valid")
check(raw.evolution==nil and raw.progress==nil,"legacy no evo")
local saved,status=Store.settleProgressTransition(raw,101,validRound(id1))
check(saved~=nil and status=="SETTLED","single atomic settlement")
check(Store.validate(saved),"profile validation")
check(raw.evolution==nil and raw.progress==nil,"no input mutation")
check(saved.evolution.fragments==2,"two certified objectives -> two shards")
check(saved.evolution.roundCount==1,"one round credited")
check(saved.progress.settledCount==1,"same atomic XP round")
local again,why=Store.settleProgressTransition(saved,101,validRound(id1))
check(again~=nil and why=="ALREADY_SETTLED","XP replay idempotent")
check(again.evolution.fragments==2 and again.revision==saved.revision,
 "shards + revision replay exactly idempotent")
local bad=validRound(id2)
bad.events={{id="same",kind="PICKUP"},{id="same",kind="DEPOSIT"}}
local rejected=Store.settleProgressTransition(saved,101,bad)
check(rejected==nil,"duplicate canonical action rejected")
local notOwned,invalid=Store.evolveTransition(saved,101,"E123456789abcdef","NONE")
check(notOwned==nil,"level 1 cannot evolve")
local ready=Store.toEvolutionProfile(saved,101)
check(ready and ready.fragments==2,"same-store view")
check(Store.toEvolutionProfile(saved,102)==nil,"foreign user cannot inspect")
local prep=Store.settleProgressTransition(saved,101,validRound(id2))
check(prep~=nil and prep.evolution.fragments==4,"second round earned")
local originalRevision=prep.revision
-- Simulated trusted high-level stored record only for test fast-forward.
prep.progress.level=10;prep.progress.xp=0
prep.progress.mastery.starter_scout={level=3,xp=0}
check(Store.validate(prep),"saved level10/mastery3 profile remains valid")
local first,info=Store.evolveTransition(prep,101,"E123456789abcdef","NONE")
check(first~=nil and info=="EVOLVED","actual equipped item stage1")
check(first.evolution.forms.starter_scout.stage==1,"stage1 persisted same profile")
check(first.evolution.fragments==2,"material deducted only once")
check(first.progress.level==10 and first.owned.starter_scout==1,"no XP/inventory wipe")
check(prep.evolution.forms.starter_scout==nil,"input evo unmodified")
local rerun,s=Store.evolveTransition(first,101,"E123456789abcdef","NONE")
check(rerun and s=="ALREADY_EVOLVED" and rerun.revision==first.revision,
 "retry does not increase revision")
check(rerun.evolution.fragments==first.evolution.fragments,"retry no double spend")
local mismatched=Store.evolveTransition(first,101,"E123456789abcdef","ASSAULT")
check(mismatched==nil,"receipt choice conflict rejected")
local second=Store.evolveTransition(first,101,"E123456789abcdef2","NONE")
check(second==nil,"cannot jump to stage2 without branch/certified level")
first.progress.level=25;first.progress.xp=0
first.progress.mastery.starter_scout={level=6,xp=0}
first.evolution.fragments=8
local branch,reason=Store.evolveTransition(first,101,"E123456789abcdef2","ASSAULT")
check(branch and reason=="EVOLVED","server-owned branch stage2")
check(branch.evolution.forms.starter_scout.stage==2 and
 branch.evolution.forms.starter_scout.branch=="ASSAULT","persisted choice")
check(branch.evolution.fragments==3,"stage2 consumes 5 earned shards")
check(E.form(branch.evolution,"starter_scout",branch.owned).additionalPvpStatMultiplier==0,
 "evolution does not duplicate power multiplier")
local forged=Store.blank()
forged.evolution=E.newProfile(102)
forged.evolution.forms.starter_scout={stage=3,branch="NONE"}
check(not Store.validate(forged),"malformed mythic form rejected")
local grant=Store.grantTransition(branch,"Sabcdefghijklm:3","forest_scout")
check(grant and Store.validate(grant),"existing free hatch preserved")
check(grant.evolution.forms.starter_scout.stage==2,"evo preserved on item grant")
local equipped=Store.equipTransition(grant,"forest_scout")
check(equipped and Store.validate(equipped),"existing equip preserved")
check(equipped.evolution.forms.starter_scout.stage==2,"evo preserved when equipping")
local newStart=Store.toEvolutionProfile(Store.blank(),101)
check(newStart and newStart.fragments==0,"old record migrates no free shards")
local fake={record=Store.blank(),calls=0}
function fake:UpdateAsync(key,fn)
 check(key=="U_101","one real ID key")
 local old=self.record
 local once=fn(old)
 local twice=fn(old) -- concurrent UpdateAsync optimistic retry, no side effects
 check(once~=nil and twice~=nil,"callbacks return complete records")
 check(once.revision==twice.revision,"callback pure replay revision")
 self.record=twice
 self.calls+=1
 return twice
end
local ok,updated,receipt=Store.settleProgress(fake,101,validRound("Sabcdefghijklm:4"))
check(ok and updated~=nil and receipt=="PROGRESS_PERSISTED_OR_ALREADY_SETTLED",
 "real mocked single-key settlement succeeds")
check(fake.calls==1 and fake.record.evolution.fragments==2,
 "one atomic update writes shards+XP")
local ok2=Store.settleProgress(fake,101,validRound("Sabcdefghijklm:4"))
check(ok2 and fake.record.evolution.fragments==2,
 "same-round repeated network retry cannot mint shards")
print("P0D_ATOMIC_EVOLUTION_NATIVE_"..tostring(n).."_ASSERTIONS_PASS")
"""
source="local __P=(function()\n"+pro+"\nend)()\n"+
       "local __E=(function()\n"+evo+"\nend)()\n"+
       "local E=__E\nlocal Store=(function()\n"+store+"\nend)()\n"+TEST
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--write",required=True);args=p.parse_args()
 Path(args.write).write_text(source,"utf8")
 print("P0D_NATIVE_EVOLUTION_TRANSACTION_DRIVER_CREATED")
