--!strict
-- Executes in pinned Luau.Repl.CLI, not a mock of the trading-policy implementation.
local P=require("./GQ8_TradePolicy")
local function item(id,owner,category,version)
    return {id=id,ownerUserId=owner,category=category,version=version,
        tradeable=true,bound=false,equipped=false,escrowLocked=false,starterProtected=false}
end
local a={["warrior-blade-01"]=item("warrior-blade-01",101,"WEAPON",1)}
local b={["beast-wolf-01"]=item("beast-wolf-01",202,"BEAST",5)}
local trade=P.new("EGGRUMBLE-REALTRADE-001",101,202,0)
local ok,rev=P.setOffer(trade,101,{"warrior-blade-01"},a,1)
assert(ok and rev==1)
ok,rev=P.setOffer(trade,202,{"beast-wolf-01"},b,2)
assert(ok and rev==2)
assert(P.lock(trade,303,rev,3)==false)
assert(P.lock(trade,101,rev-1,3)==false)
assert(P.lock(trade,101,rev,3)==true)
local yes,ready=P.lock(trade,202,rev,4)
assert(yes and ready==9)
assert(P.confirm(trade,101,rev,8)==false)
local success,mutual=P.confirm(trade,101,rev,9)
assert(success and mutual==false)
success,mutual=P.confirm(trade,202,rev,9)
assert(success and mutual==true)
local good,plan=P.proposeSettlement(trade,a,b)
assert(good and plan.tradeId=="EGGRUMBLE-REALTRADE-001")
assert(plan.requiresExistingStoreAtomicJournal and #plan.itemsA==1 and #plan.itemsB==1)
assert(a["warrior-blade-01"].ownerUserId==101 and b["beast-wolf-01"].ownerUserId==202)
-- Version drift during two-party proposal must never create a transfer plan.
b["beast-wolf-01"].version=6
assert(P.proposeSettlement(trade,a,b)==false)
b["beast-wolf-01"].version=5
assert(P.markSettledAfterStoreReceipt(trade,"DURABLE-RECEIPT-0001"))
assert(P.proposeSettlement(trade,a,b)==false)
assert(P.cancel(trade,101)==false)
-- A revised offer invalidates BOTH previous lock/confirm states and requires a new countdown.
local t=P.new("EGGRUMBLE-REALTRADE-002",101,202,0)
assert(P.setOffer(t,101,{"warrior-blade-01"},a,1))
assert(P.setOffer(t,202,{"beast-wolf-01"},b,2))
assert(P.lock(t,101,t.revision,3))
assert(P.lock(t,202,t.revision,4))
assert(P.setOffer(t,101,{"warrior-blade-01"},a,5))
assert(t.readyAt==0 and not t.aLocked and not t.bLocked)
assert(P.confirm(t,101,t.revision,20)==false)
assert(P.lock(t,101,t.revision,6))
assert(P.lock(t,202,t.revision,7))
assert(P.confirm(t,101,t.revision,11)==false)
assert(P.confirm(t,101,t.revision,12))
assert(P.confirm(t,202,t.revision,12))
local d=P.new("EGGRUMBLE-REALTRADE-003",101,202,0)
assert(P.setOffer(d,101,{"warrior-blade-01","warrior-blade-01"},a,1)==false)
a["warrior-blade-01"].paidOrigin=true
assert(P.setOffer(d,101,{"warrior-blade-01"},a,2)==false)
a["warrior-blade-01"].paidOrigin=false
a["warrior-blade-01"].starterProtected=true
assert(P.setOffer(d,101,{"warrior-blade-01"},a,3)==false)
a["warrior-blade-01"].starterProtected=false
a["warrior-blade-01"].equipped=true
assert(P.setOffer(d,101,{"warrior-blade-01"},a,4)==false)
a["warrior-blade-01"].equipped=false
assert(P.setOffer(d,303,{"warrior-blade-01"},a,4)==false)
assert(P.setOffer(d,101,{"warrior-blade-01"},a,5)==true)
-- Cross-owner duplicated item instance ID cannot settle, even if both snapshots are internally valid.
local left={sameid=item("sameid",101,"ITEM",1)}
local right={sameid=item("sameid",202,"ITEM",1)}
local x=P.new("EGGRUMBLE-REALTRADE-004",101,202,0)
assert(P.setOffer(x,101,{"sameid"},left,1))
assert(P.setOffer(x,202,{"sameid"},right,2))
assert(P.lock(x,101,x.revision,3));assert(P.lock(x,202,x.revision,4))
assert(P.confirm(x,101,x.revision,9));assert(P.confirm(x,202,x.revision,9))
local unique,reason=P.proposeSettlement(x,left,right)
assert(unique==false and reason=="DUPLICATE_GLOBAL_INSTANCE")
-- Explicitly tradeable *earned* egg can appear in a future policy, paid-origin cannot.
local eggs={["egg-free-01"]=item("egg-free-01",101,"EGG",1)}
assert(P.setOffer(P.new("EGGRUMBLE-REALTRADE-005",101,202,0),101,{"egg-free-01"},eggs,1))
print("GQ8_TRADE_POLICY_NATIVE_DOUBLE_CONFIRM_OWNERSHIP_PAID_REPLAY_DUPLICATE_PASS")
