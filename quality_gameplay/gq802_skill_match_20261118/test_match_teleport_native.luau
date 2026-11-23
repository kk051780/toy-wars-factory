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


-- GQ807_CLAIM_WAIT_OWNERSHIP_REGRESSION_20261123
-- Preserve all author tests above. Six bounded sequences below exercise the
-- public adapter with yielding service dependencies; no source phase string is
-- used as an oracle. These are Native models, not live Roblox teleports.
do
 local function eightPlan(ids:any):any
  local a,b={},{}
  for i=1,4 do a[i]=ids[i];b[i]=ids[i+4] end
  return {status="MATCH_READY",mode="TEAM",region="JP",size=8,
   requiresAuthoritativeQueueClaim=true,teleportAuthorizedHere=false,
   teamA=a,teamB=b}
 end
 local primary=eightPlan({1,2,3,4,5,6,7,8})
 local function fixture():any
  local f={now=1000,epoch=5,guidCount=0,claimModes={},teleportModes={},
   claimCalls={},commits={},records={},teleports={},playersById={}}
  local ps={}
  for id=1,16 do f.playersById[id]={UserId=id,Parent=ps} end
  function ps:GetPlayerByUserId(id:any):any return f.playersById[id] end
  f.players=ps
  local hs={}
  function hs:GenerateGUID(_dash:any):string
   f.guidCount+=1
   return string.format("%08x-1234-1234-1234-123456789abc",f.guidCount)
  end
  local ms={}
  function ms:UpdateAsync(key:any,transform:any,ttl:any):any
   assert(ttl==180,"RED_CLAIM_TTL_DRIFT")
   local index=#f.claimCalls+1
   f.claimCalls[index]={key=key,ttl=ttl}
   local action=f.claimModes[index] or "OK"
   if action=="WAIT" then
    -- The service request yields before the atomic transform. The callback
    -- itself never yields and retains the original per-key semantics.
    action=coroutine.yield({kind="CLAIM_WAIT",index=index,key=key})
   end
   if action=="THROW" then error("MODEL_CLAIM_NETWORK_FAILURE") end
   if action=="INVALID" then return {matchId="WRONG_CLAIM",originJobId="native-origin",epoch=f.epoch} end
   assert(action=="OK","HARNESS_UNKNOWN_CLAIM_ACTION")
   local value=transform(f.records[key])
   if value~=nil then f.records[key]=value end
   f.commits[#f.commits+1]={key=key,value=value}
   return value
  end
  function ms:GetAsync(key:any):any return f.records[key] end
  local ts={}
  function ts:TeleportAsync(placeId:any,players:any,options:any):any
   assert(placeId==102030 and #players>=1 and #players<=16,"RED_TRANSPORT_INPUT_DRIFT")
   assert(options.data.joinDataTrusted==false and options.data.matchId==options.ReservedServerId,
    "RED_TRANSPORT_TRUST_OR_DESTINATION_DRIFT")
   local refs,ids={},{}
   for i,player in ipairs(players) do refs[i]=player;ids[i]=player.UserId end
   local index=#f.teleports+1
   local call={id=options.ReservedServerId,players=refs,ids=ids,succeeded=false}
   f.teleports[index]=call
   local action=f.teleportModes[index] or "OK"
   if action=="WAIT" then action=coroutine.yield({kind="TELEPORT_WAIT",index=index}) end
   if action=="THROW" then error("MODEL_TELEPORT_NETWORK_FAILURE") end
   assert(action=="OK","HARNESS_UNKNOWN_TELEPORT_ACTION")
   call.succeeded=true
   return {PrivateServerId=options.ReservedServerId}
  end
  f.deps={enabled=true,isStudio=false,inReservedServer=false,targetPlaceId=102030,
   jobId="native-origin",players=ps,teleport=ts,http=hs,claimMap=ms,
   now=function()return f.now end,
   isEpochCurrent=function(epoch:any)return epoch==f.epoch end,
   optionsFactory=function()return {SetTeleportData=function(self:any,data:any)self.data=data end} end}
  f.bridge=M.create(f.deps)
  return f
 end
 local function launch(f:any,plan:any):any
  local run={}
  run.thread=coroutine.create(function()return f.bridge:dispatch(plan,f.epoch,102030)end)
  local okay,value=coroutine.resume(run.thread)
  assert(okay,value)
  if coroutine.status(run.thread)=="dead" then run.result=value else run.waiting=value end
  return run
 end
 local function finish(run:any,response:string):any
  assert(coroutine.status(run.thread)=="suspended","HARNESS_NOT_WAITING")
  local okay,value=coroutine.resume(run.thread,response)
  assert(okay,value)
  assert(coroutine.status(run.thread)=="dead","HARNESS_UNEXPECTED_SECOND_WAIT")
  run.result=value;run.waiting=nil
  return value
 end
 local function expectWait(run:any,kind:string)
  assert(run.waiting and run.waiting.kind==kind,"HARNESS_MISSING_SERVICE_WAIT")
 end
 local function expectRoster(call:any,ids:any)
  assert(#call.ids==#ids,"RED_ROSTER_SIZE_CHANGED")
  for i,id in ipairs(ids) do assert(call.ids[i]==id,"RED_ROSTER_ID_CHANGED") end
 end

 -- Sequence1: same-cohort overlap during the claim; a failure notification
 -- while only claiming cannot teleport early or consume the later retry budget.
 do
  local f=fixture();f.claimModes={"WAIT","WAIT"}
  local a=launch(f,primary);expectWait(a,"CLAIM_WAIT")
  assert(f.bridge:teleportFailed(f.playersById[1]).status=="IGNORED","RED_CLAIMING_RETRY_ACCEPTED")
  assert(#f.teleports==0,"RED_CLAIMING_RETRY_TELEPORTED")
  local b=launch(f,primary)
  finish(a,"OK")
  -- A legacy source can also suspend B: release it so the same behavioral
  -- oracle observes both requests instead of failing on a fixture assumption.
  if b.waiting then finish(b,"OK") end
  assert(#f.claimCalls==1 and #f.teleports==1,
   "RED_GQ802_SAME_COHORT_RESERVED_TWICE_DURING_UPDATEASYNC_YIELD")
  assert(a.result.status=="TELEPORT_INITIATED" and b.result.reason=="ALREADY_DISPATCHING")
  assert(f.guidCount==1,"RED_DUPLICATE_COHORT_MINTED_SECOND_GUID")
  expectRoster(f.teleports[1],{1,2,3,4,5,6,7,8})
  local retry=f.bridge:teleportFailed(f.playersById[1])
  assert(retry.status=="RETRY_INITIATED" and retry.attempt==1,"RED_CLAIM_NOTIFICATION_SPENT_RETRY")
  assert(#f.teleports==2 and f.teleports[2].id==f.teleports[1].id)
  print("GQ807_SEQUENCE1_SAME_COHORT_AND_CLAIM_RETRY_PASS")
 end

 -- Sequence2: two failed claims followed by a genuine retry. Both thrown and
 -- invalid claim responses must release all eight local slots, without travel.
 do
  local f=fixture();f.claimModes={"WAIT","WAIT"}
  local first=launch(f,primary);expectWait(first,"CLAIM_WAIT")
  assert(finish(first,"THROW").reason=="CLAIM_FAILED")
  assert(#f.teleports==0,"RED_THROWN_CLAIM_TELEPORTED")
  local second=launch(f,primary);expectWait(second,"CLAIM_WAIT")
  assert(finish(second,"INVALID").reason=="CLAIM_FAILED")
  assert(#f.teleports==0,"RED_INVALID_CLAIM_TELEPORTED")
  local accepted=f.bridge:dispatch(primary,f.epoch,102030)
  assert(accepted.status=="TELEPORT_INITIATED","RED_FAILED_CLAIM_LEFT_ROSTER_RESERVED")
  assert(#f.claimCalls==3 and #f.commits==1 and #f.teleports==1)
  print("GQ807_SEQUENCE2_CLAIM_FAILURE_RELEASE_RETRY_PASS")
 end

 -- Sequence3: a real Host epoch changes during the yielding claim. The old
 -- request cannot teleport, and the current epoch can use the same cohort.
 do
  local f=fixture();f.claimModes={"WAIT"}
  local old=launch(f,primary);expectWait(old,"CLAIM_WAIT")
  f.epoch=6
  assert(finish(old,"OK").reason=="EPOCH_CHANGED_DURING_CLAIM")
  assert(#f.teleports==0,"RED_RETIRED_EPOCH_TELEPORTED")
  assert(f.bridge:dispatch(primary,6,102030).status=="TELEPORT_INITIATED",
   "RED_RETIRED_EPOCH_LEFT_ROSTER_RESERVED")
  assert(#f.teleports==1)
  print("GQ807_SEQUENCE3_EPOCH_RELEASE_PASS")
 end

 -- Sequence4: a participant leaves during claim and the same UserId obtains
 -- a new Player instance and a different cohort. Retired cleanup must not
 -- remove that newer owner; the other seven old slots must become usable.
 do
  local f=fixture();f.claimModes={"WAIT"}
  local old=launch(f,primary);expectWait(old,"CLAIM_WAIT")
  local retired=f.playersById[1]
  retired.Parent=nil;f.bridge:playerLeft(1)
  local replacement={UserId=1,Parent=f.players}
  f.playersById[1]=replacement
  local successor=eightPlan({1,9,10,11,12,13,14,15})
  local accepted=f.bridge:dispatch(successor,f.epoch,102030)
  assert(accepted.status=="TELEPORT_INITIATED")
  assert(finish(old,"OK").reason=="COHORT_CHANGED_DURING_CLAIM")
  assert(#f.teleports==1,"RED_RETIRED_PLAYER_COHORT_TELEPORTED")
  assert(f.teleports[1].players[1]==replacement and f.teleports[1].players[1]~=retired)
  expectRoster(f.teleports[1],{1,9,10,11,12,13,14,15})
  assert(f.bridge:dispatch(successor,f.epoch,102030).reason=="ALREADY_DISPATCHING",
   "RED_OLD_CLAIM_CLEARED_NEW_PLAYER_OWNER")
  local retry=f.bridge:teleportFailed(replacement)
  assert(retry.status=="RETRY_INITIATED" and retry.matchId==accepted.matchId)
  local released=eightPlan({2,3,4,5,6,7,8,16})
  assert(f.bridge:dispatch(released,f.epoch,102030).status=="TELEPORT_INITIATED",
   "RED_RETIRED_COHORT_LEFT_OTHER_PLAYERS_RESERVED")
  print("GQ807_SEQUENCE4_REJOIN_AND_NEW_OWNER_PASS")
 end

 -- Sequence5: the existing 90-second expiry clears a waiting claim. A fresh
 -- same-cohort reservation survives the old successful claim response.
 do
  local f=fixture();f.claimModes={"WAIT"}
  local old=launch(f,primary);expectWait(old,"CLAIM_WAIT")
  f.now+=90;f.bridge:expirePending()
  local accepted=f.bridge:dispatch(primary,f.epoch,102030)
  assert(accepted.status=="TELEPORT_INITIATED","RED_CLAIM_EXPIRY_BLOCKED_RETRY")
  assert(finish(old,"OK").reason=="CLAIM_EXPIRED")
  assert(#f.teleports==1,"RED_EXPIRED_CLAIM_TELEPORTED")
  assert(f.bridge:dispatch(primary,f.epoch,102030).reason=="ALREADY_DISPATCHING",
   "RED_EXPIRED_CLAIM_CLEARED_NEW_OWNER")
  local retry=f.bridge:teleportFailed(f.playersById[1])
  assert(retry.status=="RETRY_INITIATED" and retry.matchId==accepted.matchId)
  print("GQ807_SEQUENCE5_EXPIRED_CLAIM_NEW_OWNER_PASS")
 end

 -- Sequence6: TeleportAsync itself yields and then throws after its pending
 -- expired. Its old cleanup cannot erase the newer cohort's successful owner.
 do
  local f=fixture();f.teleportModes={"WAIT"}
  local old=launch(f,primary);expectWait(old,"TELEPORT_WAIT")
  f.now+=90;f.bridge:expirePending()
  local accepted=f.bridge:dispatch(primary,f.epoch,102030)
  assert(accepted.status=="TELEPORT_INITIATED")
  assert(finish(old,"THROW").reason=="TELEPORT_THROW")
  assert(#f.teleports==2 and not f.teleports[1].succeeded and f.teleports[2].succeeded)
  assert(f.bridge:dispatch(primary,f.epoch,102030).reason=="ALREADY_DISPATCHING",
   "RED_OLD_TELEPORT_THROW_CLEARED_NEW_OWNER")
  local retry=f.bridge:teleportFailed(f.playersById[1])
  assert(retry.status=="RETRY_INITIATED" and retry.matchId==accepted.matchId)
  assert(f.teleports[3].id==accepted.matchId)
  print("GQ807_SEQUENCE6_OLD_TELEPORT_THROW_NEW_OWNER_PASS")
 end
 print("GQ807_CLAIM_WAIT_OWNERSHIP_SIX_SEQUENCES_NATIVE_PASS")
end
