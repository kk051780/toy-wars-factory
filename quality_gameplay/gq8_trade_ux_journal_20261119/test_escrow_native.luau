--!strict
-- 2-account deterministic fake Store snapshots: proof of pure reducer, NOT real persistence.
local E=require("./GQ8_TradeEscrowReducer")
local plan={tradeId="eggrumble-free-trade-00001",revision=4,fromA=101,toB=202,
 itemsA={{id="weapon-01",version=3}},itemsB={{id="beast-01",version=9}},
 requiresExistingStoreAtomicJournal=true,alreadySettled=false}
local function item(id,owner,version,kind)
 return {id=id,ownerUserId=owner,version=version,
  category=kind,itemDefId="definition-"..id,originKind="FREE_EARNED",
  paidOrigin=false,tradeable=true,bound=false,equipped=false,
  escrowLocked=false,tradeIncomingLocked=false,starterProtected=false,
  visualSkin="rare-free-visual"}
end
local function player(owner,instance,ver,kind)
 return {userId=owner,revision=0,wallet={bp=713},progress={level=42},
 inventory={[instance]=item(instance,owner,ver,kind)},
 tradeState={},otherExistingStoreField="must-survive"}
end
local originalA=player(101,"weapon-01",3,"WEAPON")
local originalB=player(202,"beast-01",9,"BEAST")
local a,ra=E.prepare(originalA,plan,101)
assert(a and ra=="PREPARED" and a.inventory["weapon-01"].escrowLocked)
assert(originalA.inventory["weapon-01"].escrowLocked==false)
assert(a.wallet.bp==713 and a.progress.level==42 and a.otherExistingStoreField=="must-survive")
local b,rb=E.prepare(originalB,plan,202)
assert(b and rb=="PREPARED")
local same,status=E.prepare(a,plan,101)
assert(same and status=="ALREADY_PREPARED" and same.revision==a.revision)
local early,why=E.credit(a,plan,101,nil,nil)
assert(not early and why=="NO_DURABLE_TWO_SIDED_COMMIT")
local aEsc,es=E.escrow(a,plan,101)
assert(aEsc and es=="ESCROWED")
assert(aEsc.inventory["weapon-01"]==nil and aEsc.tradeState[plan.tradeId].outgoing["weapon-01"].id=="weapon-01")
local replay,rr=E.escrow(aEsc,plan,101)
assert(replay and rr=="ALREADY_ESCROWED" and replay.revision==aEsc.revision)
assert(a.inventory["weapon-01"]~=nil) -- no input mutation before Store confirms persistence
local proofA,pa=E.receipt(aEsc,plan,101)
assert(proofA and pa=="ESCROW_READ_ONLY")
assert(E.receipt(b,plan,202)==nil)
local bEsc=assert(E.escrow(b,plan,202))
local proofB=assert(E.receipt(bEsc,plan,202))
local coordinator={tradeId=plan.tradeId,fingerprint=proofA.fingerprint,
 bothEscrowPersisted=true,sessionLocksHeld=true,durableId="durable-global-trade-commit-01"}
local tampered={tradeId=plan.tradeId,fingerprint="wrong",owner=202,items=proofB.items}
assert(E.credit(aEsc,plan,101,tampered,coordinator)==nil)
local aCredit,ac=E.credit(aEsc,plan,101,proofB,coordinator)
assert(aCredit and ac=="CREDITED")
assert(aCredit.inventory["beast-01"].ownerUserId==101)
assert(aCredit.inventory["beast-01"].version==10)
assert(aCredit.inventory["beast-01"].tradeIncomingLocked==true)
assert(aCredit.inventory["beast-01"].visualSkin=="rare-free-visual")
assert(aCredit.wallet.bp==713 and aCredit.progress.level==42)
local again,ar=E.credit(aCredit,plan,101,proofB,coordinator)
assert(again and ar=="ALREADY_CREDITED" and again.inventory["beast-01"].version==10)
local malicious=player(101,"weapon-01",3,"WEAPON")
malicious.inventory["beast-01"]=item("beast-01",101,5,"BEAST")
local stolen=assert(E.prepare(malicious,plan,101))
local stolenEsc=assert(E.escrow(stolen,plan,101))
local no,duplicate=E.credit(stolenEsc,plan,101,proofB,coordinator)
assert(not no and duplicate=="INCOMING_ITEM_INVALID_OR_DUPLICATE")
local bCredit=assert(E.credit(bEsc,plan,202,proofA,coordinator))
assert(bCredit.inventory["weapon-01"].ownerUserId==202 and bCredit.inventory["weapon-01"].version==4)
assert(E.finalize(aCredit,plan,101,{tradeId=plan.tradeId,
 fingerprint=proofA.fingerprint,globalCommitPersisted=false,durableId=coordinator.durableId})==nil)
local commit={tradeId=plan.tradeId,fingerprint=proofA.fingerprint,
 globalCommitPersisted=true,durableId=coordinator.durableId}
local aFinal,fa=E.finalize(aCredit,plan,101,commit)
local bFinal,fb=E.finalize(bCredit,plan,202,commit)
assert(aFinal and fa=="FINALIZED" and bFinal and fb=="FINALIZED")
assert(aFinal.inventory["beast-01"].tradeIncomingLocked==false)
assert(bFinal.inventory["weapon-01"].tradeIncomingLocked==false)
assert(aFinal.inventory["weapon-01"]==nil and bFinal.inventory["beast-01"]==nil)
assert(aFinal.revision==4 and bFinal.revision==4)
local fa2,fa2r=E.finalize(aFinal,plan,101,commit)
assert(fa2 and fa2r=="ALREADY_FINALIZED" and fa2.revision==aFinal.revision)
local paid=player(101,"weapon-01",3,"WEAPON")
paid.inventory["weapon-01"].paidOrigin=true
assert(E.prepare(paid,plan,101)==nil)
paid=player(101,"weapon-01",3,"WEAPON")
paid.inventory["weapon-01"].originKind="UNKNOWN"
assert(E.prepare(paid,plan,101)==nil)
paid=player(101,"weapon-01",3,"WEAPON")
paid.inventory["weapon-01"].equipped=true
assert(E.prepare(paid,plan,101)==nil)
paid=player(101,"weapon-01",3,"WEAPON")
paid.inventory["weapon-01"].tradeIncomingLocked=true
assert(E.prepare(paid,plan,101)==nil)
paid=player(101,"weapon-01",4,"WEAPON")
assert(E.prepare(paid,plan,101)==nil) -- offer version drift
local bad={tradeId=plan.tradeId,revision=4,fromA=101,toB=202,
 itemsA={{id="weapon-01",version=3}},itemsB={{id="weapon-01",version=3}},
 requiresExistingStoreAtomicJournal=true,alreadySettled=false}
assert(E.prepare(originalA,bad,101)==nil) -- global unique instance
assert(E.prepare(originalA,plan,303)==nil) -- not a participant
print("GQ8_TRADE58_ESCROW_REDUCER_TWO_ACCOUNT_RESERVE_DEBIT_CREDIT_COMMIT_REPLAY_PAID_FAILCLOSED_PASS")
