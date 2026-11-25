--!strict
-- Pure in-memory journal PROTOCOL for a future SINGLE existing Store writer.
-- Never call from a Remote handler with client-supplied "durable" receipts.
-- This module does not save data or transfer an item: storage receipts must be
-- constructed by the trusted Store AFTER its own durable, session-locked writes.
local Journal={}
local ORDER={"PREPARE_A","PREPARE_B","ESCROW_A","ESCROW_B","CREDIT_A","CREDIT_B","COMMIT"}
local BY_STEP={}
for i,name in ipairs(ORDER) do BY_STEP[name]=i end
local function sideOwner(j,step)
    if step=="PREPARE_A" or step=="ESCROW_A" or step=="CREDIT_A" then return j.a end
    if step=="PREPARE_B" or step=="ESCROW_B" or step=="CREDIT_B" then return j.b end
    return 0
end
local function copyItems(xs)
    if type(xs)~="table" or #xs<1 or #xs>8 then return nil end
    local result={}
    for _,item in ipairs(xs) do
        if type(item)~="table" or type(item.id)~="string" or #item.id<3 or #item.id>120
           or type(item.version)~="number" or item.version<0 or item.version~=item.version
           or item.version==math.huge or item.version~=math.floor(item.version) then
           return nil
        end
        result[#result+1]={id=item.id,version=item.version}
    end
    return result
end
function Journal.new(plan,now)
    if type(plan)~="table" or plan.requiresExistingStoreAtomicJournal~=true
       or plan.alreadySettled~=false or type(plan.tradeId)~="string"
       or #plan.tradeId<8 or #plan.tradeId>100 or type(plan.revision)~="number"
       or plan.revision<0 or plan.revision~=math.floor(plan.revision)
       or type(plan.fromA)~="number" or type(plan.toB)~="number"
       or plan.fromA<1 or plan.toB<1 or plan.fromA==plan.toB
       or type(now)~="number" or now<0 or now~=now or now==math.huge then
        return nil,"BAD_SETTLEMENT_PLAN"
    end
    local a=copyItems(plan.itemsA);local b=copyItems(plan.itemsB)
    if not a or not b then return nil,"BAD_ITEMS" end
    local seen={}
    for _,side in ipairs({a,b}) do
        for _,item in ipairs(side) do
            if seen[item.id] then return nil,"DUPLICATE_INSTANCE" end
            seen[item.id]=true
        end
    end
    return {tradeId=plan.tradeId,revision=plan.revision,a=plan.fromA,b=plan.toB,
       aItems=a,bItems=b,step=0,status="PREPARED",
       receipts={},createdAt=now,lastAt=now,complete=false},"OK"
end
function Journal.next(j)
    if j.status=="ABORTED" then return "NONE" end
    if j.step==#ORDER then return "NONE" end
    return ORDER[j.step+1]
end
function Journal.canCancel(j)
    return not j.complete and j.status~="ABORTED" and j.step<3
end
function Journal.cancelBeforeEscrow(j,requester)
    if requester~=j.a and requester~=j.b then return false,"NOT_PARTICIPANT" end
    if not Journal.canCancel(j) then return false,"ESCROW_RECOVERY_REQUIRED" end
    j.status="ABORTED"
    return true,"ABORTED"
end
-- Receipt is a VERIFIED EXISTING-STORE INTERNAL callback, never a client request.
-- Actual Store MUST atomically journal each step with each account's session lock.
-- At any crash after ESCROW_A, items stay unavailable until an idempotent recovery
-- agent verifies durable receipt and resumes, never a unilateral refund/credit.
function Journal.record(j,receipt)
    if type(receipt)~="table" or j.status=="ABORTED" then return false,"CLOSED" end
    if type(receipt.step)~="string" or not BY_STEP[receipt.step] then return false,"UNKNOWN_STEP" end
    local index=BY_STEP[receipt.step]
    if receipt.tradeId~=j.tradeId or receipt.revision~=j.revision or receipt.durable~=true
       or receipt.storeWriterAttested~=true or type(receipt.receiptId)~="string"
       or #receipt.receiptId<8 or #receipt.receiptId>140
       or type(receipt.lockEpoch)~="number" or receipt.lockEpoch<1
       or receipt.lockEpoch~=math.floor(receipt.lockEpoch) or receipt.lockEpoch==math.huge
       or receipt.accountId~=sideOwner(j,receipt.step)
       then return false,"UNTRUSTED_OR_MISMATCHED_RECEIPT" end
    if index<=j.step then
        local old=j.receipts[receipt.step]
        if old and old.id==receipt.receiptId and old.epoch==receipt.lockEpoch then
            return true,"IDEMPOTENT_REPLAY"
        end
        return false,"REPLAY_CONFLICT"
    end
    if index~=j.step+1 then return false,"STEP_OUT_OF_ORDER" end
    for _,previous in pairs(j.receipts) do
        if previous.id==receipt.receiptId then return false,"RECEIPT_REUSED_ACROSS_STEPS" end
    end
    if j.complete then return false,"ALREADY_COMPLETED" end
    j.receipts[receipt.step]={id=receipt.receiptId,epoch=receipt.lockEpoch,accountId=receipt.accountId}
    j.step=index
    if receipt.step=="COMMIT" then j.complete=true;j.status="COMPLETED"
    elseif index>=3 then j.status="RECOVERY_REQUIRED_IF_INTERRUPTED"
    else j.status="PREPARING" end
    return true,Journal.next(j)
end
function Journal.snapshot(j)
    return {tradeId=j.tradeId,revision=j.revision,phase=j.status,step=j.step,
        nextStep=Journal.next(j),canCancel=Journal.canCancel(j),
        requiresRecovery=(j.step>=3 and not j.complete),complete=j.complete}
end
return Journal
