--!strict
local M=require("./EGGRUMBLE_MatchTeleportBridge")
local roster={}
local playerService={}
for id=1,16 do roster[id]={UserId=id,Parent=playerService} end
function playerService:GetPlayerByUserId(id:number):any return roster[id] end
local requests={}
local failTeleport=false
local teleport={}
function teleport:TeleportAsync(placeId:any,players:any,options:any):any
 if failTeleport then error("NETWORK_TRANSIENT") end
 assert(placeId==102030)
 assert(type(options.ReservedServerId)=="string" and #options.ReservedServerId>=32)
 assert(options.data.joinDataTrusted==false)
 assert(options.data.matchId==options.ReservedServerId)
 if options.data.mode=="BR" then
  assert(options.data.teamA==nil and options.data.teamB==nil)
 end
 assert(#players>=1 and #players<=16)
 requests[#requests+1]={id=options.ReservedServerId,count=#players,seed=options.data.seed}
 return {PrivateServerId=options.ReservedServerId}
end
local http={counter=0}
function http:GenerateGUID(_dash:any):string
 self.counter=self.counter+1
 return string.format("%08x-1234-1234-1234-123456789abc",self.counter)
end
local map={saved={}}
function map:GetAsync(key:any):any return self.saved[key] end
function map:UpdateAsync(key:any,fn:any,ttl:any):any
 assert(ttl>=180)
 local nextValue=fn(self.saved[key])
 self.saved[key]=nextValue
 return nextValue
end
local now=1000
local epochEnabled=true
local deps={
 enabled=true,isStudio=false,inReservedServer=false,
 targetPlaceId=102030,jobId="origin-job",
 players=playerService,teleport=teleport,http=http,claimMap=map,
 now=function()return now end,
 isEpochCurrent=function(epoch:number):boolean return epochEnabled and epoch>=1 and epoch<=9 end,
 optionsFactory=function()return {
  SetTeleportData=function(self:any,data:any)self.data=data end
 } end
}
local p={status="MATCH_READY",mode="TEAM",region="JP",size=8,
 requiresAuthoritativeQueueClaim=true,teleportAuthorizedHere=false,
 teamA={1,2,3,4},teamB={5,6,7,8}}
local off=M.create({enabled=false,isStudio=false})
assert(off:dispatch(p,5,102030).status=="FALLBACK_NORMAL_LOBBY")
local bridge=M.create(deps)
local started=bridge:dispatch(p,5,102030)
assert(started.status=="TELEPORT_INITIATED" and started.players==8)
assert(started.seed>0 and #requests==1)
assert(map.saved["m:"..started.matchId].reservedServerId==started.matchId)
assert(bridge:dispatch(p,5,102030).reason=="ALREADY_DISPATCHING")
local validData={version=M.VERSION,matchId=started.matchId,epoch=5,
 seed=started.seed,mode="TEAM",joinDataTrusted=false}
local checked=M.verifyArrival(validData,1,map,started.matchId,1001)
assert(checked.accepted and checked.source=="SERVER_MEMORYSTORE_ONLY")
assert(checked.teamA[1]==1 and checked.teamB[1]==5)
assert(M.verifyArrival(validData,16,map,started.matchId,1001).reason=="NOT_IN_SERVER_ROSTER")
assert(M.verifyArrival(validData,1,map,"ANOTHER_SERVER",1001).reason=="INVALID_OR_WRONG_RESERVED_SERVER")
assert(M.verifyArrival(validData,1,map,started.matchId,1181).reason=="MISSING_OR_EXPIRED_SERVER_TICKET")
epochEnabled=false
assert(bridge:teleportFailed(roster[5]).reason=="OLD_ROUND_EPOCH")
assert(bridge:dispatch(p,6,102030).reason=="OLD_ROUND_EPOCH")
epochEnabled=true
validData.seed=12
assert(not M.verifyArrival(validData,1,map,started.matchId,1001).accepted)
validData.seed=started.seed
local source=map.saved["m:"..started.matchId]
source.players[2]=source.players[1]
assert(M.verifyArrival(validData,1,map,started.matchId,1001).reason=="INVALID_SERVER_ROSTER")
source.players[2]=2
source.stat="EXPIRED"
assert(not M.verifyArrival(validData,1,map,started.matchId,1001).accepted)
source.stat="RESERVED"
local retry=bridge:teleportFailed(roster[1])
assert(retry.status=="RETRY_INITIATED" and retry.attempt==1)
assert(requests[2].id==requests[1].id and requests[2].seed==requests[1].seed)
retry=bridge:teleportFailed(roster[1])
assert(retry.attempt==2)
assert(bridge:teleportFailed(roster[1]).reason=="RETRIES_EXHAUSTED")
bridge:playerLeft(2)
roster[2].Parent=nil
assert(bridge:dispatch(p,6,102030).reason=="COHORT_NOT_LOCAL")
roster[2].Parent=playerService
now=1100
bridge:expirePending()
assert(bridge:dispatch(p,6,102030).status=="TELEPORT_INITIATED")
bridge:expirePending()
now=1192
bridge:expirePending()
assert(next(bridge.byMatch)==nil)
local tampered={status="MATCH_READY",mode="TEAM",region="JP",size=8,
 requiresAuthoritativeQueueClaim=true,teleportAuthorizedHere=true,
 teamA={1,2,3,4},teamB={5,6,7,8}}
assert(bridge:dispatch(tampered,7,102030).reason=="INVALID_PLAN_OR_DESTINATION")
tampered.teleportAuthorizedHere=false
tampered.teamB={5,6,7,7}
assert(bridge:dispatch(tampered,7,102030).reason=="INVALID_PLAN_OR_DESTINATION")
assert(bridge:dispatch(p,7,123).reason=="INVALID_PLAN_OR_DESTINATION")
local studio=M.create({enabled=true,isStudio=true})
assert(studio:dispatch(p,7,102030).status=="FALLBACK_NORMAL_LOBBY")
local reserved=M.create({enabled=true,inReservedServer=true})
assert(reserved:dispatch(p,7,102030).status=="FALLBACK_NORMAL_LOBBY")
local second=M.create(deps)
failTeleport=true
assert(second:dispatch(p,8,102030).reason=="TELEPORT_THROW")
failTeleport=false
assert(second:teleportFailed(roster[1]).status=="IGNORED")
local brPlan={status="MATCH_READY",mode="BR",region="JP",size=8,
 requiresAuthoritativeQueueClaim=true,teleportAuthorizedHere=false,
 teamAssignmentDisabled=true,teamA={1,2,3,4},teamB={5,6,7,8}}
local startedBR=second:dispatch(brPlan,9,102030)
assert(startedBR.status=="TELEPORT_INITIATED")
local brData={version=M.VERSION,matchId=startedBR.matchId,epoch=9,
 seed=startedBR.seed,mode="BR",joinDataTrusted=false}
local validBR=M.verifyArrival(brData,1,map,startedBR.matchId,1192)
assert(validBR.accepted and validBR.freeForAll)
assert(validBR.teamA==nil and validBR.teamB==nil)
brPlan.teamAssignmentDisabled=nil
assert(second:dispatch(brPlan,10,102030).reason=="INVALID_PLAN_OR_DESTINATION")
-- A real MemoryStore UpdateAsync yields; if the match expires during the
-- network call it must be rejected before TeleportAsync starts.
local transient={}
for k,v in pairs(deps) do transient[k]=v end
transient.claimMap={
 UpdateAsync=function(_self:any,_key:any,callback:any,_ttl:any):any
  epochEnabled=false
  return callback(nil)
 end
}
epochEnabled=true
local before=#requests
local delayed=M.create(transient)
assert(delayed:dispatch(p,9,102030).reason=="EPOCH_CHANGED_DURING_CLAIM")
assert(#requests==before)
epochEnabled=true
print("GQ802_MATCH_ROUTE_NATIVE_LIVE_SERVICE_BOUNDARY_GUID_CLAIM_RETRY_FAILSAFE_PASS")
