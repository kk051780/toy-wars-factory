--!strict
local R=require("./EGGRUMBLE_MatchPointPolicy")
local S=require("./EGGRUMBLE_ShopTransactionPolicy")
local function gameResult()
 return {serverVerified=true,phase="FINISHED",matchId="TEAM:24:epoch",userId="17",
  isHuman=true,playerEligible=true,wasAFK=false,playedSeconds=420,won=true,
  neutralKOs=99,eggsDeposited=99,castleContributions=99}
end
local original=gameResult()
local receipt=R.quote(original)
assert(receipt and receipt.battlePoints==230 and receipt.receiptKey=="TEAM:24:epoch:17")
assert(receipt.mustApplyOnce and receipt.requiresPersistentWallet)
original.won=false;assert(R.quote(original).battlePoints==170)
local rejects={{"serverVerified",false},{"phase","ACTIVE"},{"wasAFK",true},{"isHuman",false},
 {"playedSeconds",119},{"neutralKOs",-1},{"eggsDeposited",math.huge},{"castleContributions",0/0},
 {"playerEligible",false},{"matchId",""}}
for _,r in ipairs(rejects) do
 local x=gameResult();x[r[1]]=r[2]
 assert(R.quote(x)==nil,r[1])
end
local state={serverAuthorized=true,phase="LOBBY",profileLoaded=true,accountEligible=true,
 walletAvailable=true,userId="17",role="WARRIOR",level=10,points=500,owned={}}
local request={userId="17",itemId="GUARD_WAR_BANNER",currency="BP",uniqueOrderId="TEAM-17-0001"}
local permit=S.request(state,request)
assert(permit and permit.pointsToSubtract==420 and permit.proposedBalance==80)
assert(permit.requiresAtomicStore and permit.requiresIdempotentOrder)
state.phase="ACTIVE";assert(S.request(state,request)==nil)
state.phase="LOBBY";state.points=419;assert(S.request(state,request)==nil)
state.points=500;state.owned.GUARD_WAR_BANNER=true;assert(S.request(state,request)==nil)
state.owned.GUARD_WAR_BANNER=nil
request.currency="ROBUX";local pending=S.request(state,request)
assert(pending and pending.kind=="ROBUX_NOT_CONFIGURED" and pending.serverGrantsNothing)
request.currency="BP"
request.itemId="GUARD_SHADOW_SCOUT";assert(S.request(state,request)==nil)
request.itemId="GUARD_WAR_BANNER";request.userId="18";assert(S.request(state,request)==nil)
request.userId="17";state.profileLoaded=false;assert(S.request(state,request)==nil)
print("GQ805_REWARDS_CHECKOUT_NATIVE_SERVER_ONLY_DUAL_PRICE_PASS")
