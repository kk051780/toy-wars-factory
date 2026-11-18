--!strict
local J=require("./GQ8_TradeJournalContract")
local function sample()
 return {tradeId="eggrumble-trade-0000001",revision=4,fromA=101,toB=202,
 itemsA={{id="weapon-01",version=3}},itemsB={{id="beast-01",version=4}},
 requiresExistingStoreAtomicJournal=true,alreadySettled=false}
end
local function receipt(j,step,id,account,epoch)
 return {tradeId=j.tradeId,revision=j.revision,step=step,
 receiptId=id,accountId=account,lockEpoch=epoch,
 durable=true,storeWriterAttested=true}
end
local a,why=J.new(sample(),0)
assert(a and why=="OK")
assert(J.next(a)=="PREPARE_A" and J.canCancel(a))
local order={"PREPARE_A","PREPARE_B","ESCROW_A","ESCROW_B","CREDIT_A","CREDIT_B","COMMIT"}
local owners={101,202,101,202,101,202,0}
assert(J.record(a,receipt(a,"CREDIT_A","credit-early",101,1))==false)
assert(J.record(a,{step="PREPARE_A",tradeId=a.tradeId,revision=4,receiptId="fake-abc",
 accountId=101,lockEpoch=1,durable=false,storeWriterAttested=true})==false)
for i,name in ipairs(order) do
 local id="durable-step-"..tostring(i)
 local r=receipt(a,name,id,owners[i],11)
 local yes,nextName=J.record(a,r)
 assert(yes and (i==7 and nextName=="NONE" or i<7 and nextName==order[i+1]),name)
 local again,reason=J.record(a,r)
 assert(again and reason=="IDEMPOTENT_REPLAY")
 r.receiptId="forged-conflict"
 local bad,why=J.record(a,r)
 assert(not bad and why=="REPLAY_CONFLICT")
 if i==3 then
  assert(not J.canCancel(a))
  assert(J.cancelBeforeEscrow(a,101)==false)
  assert(J.snapshot(a).requiresRecovery)
 end
end
assert(a.complete and a.status=="COMPLETED" and J.next(a)=="NONE")
local b=assert(J.new(sample(),0))
assert(J.record(b,receipt(b,"PREPARE_A","durable-prepare-A",101,9)))
assert(J.cancelBeforeEscrow(b,202))
assert(J.record(b,receipt(b,"PREPARE_B","durable-prepare-B",202,9))==false)
local p=sample()
p.itemsB[1].id=p.itemsA[1].id
assert(J.new(p,0)==nil)
p=sample();p.alreadySettled=true;assert(J.new(p,0)==nil)
p=sample();p.itemsA={};assert(J.new(p,0)==nil)
local c=assert(J.new(sample(),0))
local wrong=receipt(c,"PREPARE_A","durable-prepare-A",202,8)
local no,reason=J.record(c,wrong)
assert(not no and reason=="UNTRUSTED_OR_MISMATCHED_RECEIPT")
local reused=assert(J.new(sample(),0))
assert(J.record(reused,receipt(reused,"PREPARE_A","durable-same-token",101,3)))
local reusedGood,reusedWhy=J.record(reused,receipt(reused,"PREPARE_B","durable-same-token",202,3))
assert(not reusedGood and reusedWhy=="RECEIPT_REUSED_ACROSS_STEPS")
local inf=sample();inf.itemsA[1].version=math.huge
assert(J.new(inf,0)==nil)
assert(J.new(sample(),math.huge)==nil)
local epoch=assert(J.new(sample(),0))
assert(J.record(epoch,receipt(epoch,"PREPARE_A","durable-epoch-inf",101,math.huge))==false)
print("GQ8_TRADE_JOURNAL_NATIVE_ORDER_REPLAY_RECOVERY_SESSION_LOCK_CONTRACT_PASS")
