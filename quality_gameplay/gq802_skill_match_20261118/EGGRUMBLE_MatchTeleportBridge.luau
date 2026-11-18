--!strict
-- GQ802 verified same-lobby cohort bridge. Real Roblox TeleportAsync call is here,
-- but disabled by default and NEVER auto-runs; existing Host must invoke it.
-- Cross-lobby global matchmaking (MessagingService + atomic queue) is NOT wired.
local M={}
M.VERSION="GQ802_MATCH_ROUTE_V1"
local TTL_SECONDS=180
local function validInt(v:any,low:number,high:number):boolean
 return type(v)=="number" and v==v and v%1==0 and v>=low and v<=high
end
local function verifiedPlan(plan:any):boolean
 if type(plan)~="table" or plan.status~="MATCH_READY"
    or plan.requiresAuthoritativeQueueClaim~=true or plan.teleportAuthorizedHere~=false
    or (plan.size~=8 and plan.size~=16)
    or (plan.mode~="TEAM" and plan.mode~="BR")
    or (plan.mode=="BR" and plan.teamAssignmentDisabled~=true)
    or type(plan.region)~="string" or #plan.region<1 or #plan.region>32
    or type(plan.teamA)~="table" or type(plan.teamB)~="table"
    or #plan.teamA~=plan.size/2 or #plan.teamB~=plan.size/2 then return false end
 local seen={}
 for _,group in ipairs({plan.teamA,plan.teamB}) do
  for _,id in ipairs(group) do
   if not validInt(id,1,999999999999) or seen[id] then return false end
   seen[id]=true
  end
 end
 return true
end
function M.create(deps:any):any
 assert(type(deps)=="table","SERVER_DEPENDENCIES_REQUIRED")
 local self={deps=deps,byUser={},byMatch={},enabled=deps.enabled==true}
 function self:dispatch(plan:any, epoch:any, placeId:any):any
  -- If feature not opted-in, Studio, missing place IDs or low population:
  -- game continues with the ORIGINAL lobby and AI; never fails a match start.
  if not self.enabled or deps.isStudio or deps.inReservedServer
   then return {status="FALLBACK_NORMAL_LOBBY",reason="FEATURE_OFF_OR_STUDIO"} end
  if not verifiedPlan(plan) or not validInt(epoch,1,1000000000)
   or not validInt(placeId,1,999999999999)
   or placeId~=deps.targetPlaceId then
   return {status="FALLBACK_NORMAL_LOBBY",reason="INVALID_PLAN_OR_DESTINATION"} end
  local roster={}
  local ids={}
  for _,id in ipairs(plan.teamA) do ids[#ids+1]=id end
  for _,id in ipairs(plan.teamB) do ids[#ids+1]=id end
  for _,id in ipairs(ids) do
   if self.byUser[id] then return {status="FALLBACK_NORMAL_LOBBY",reason="ALREADY_DISPATCHING"} end
   local player=deps.players:GetPlayerByUserId(id)
   if not player or player.Parent~=deps.players or player.UserId~=id then
    return {status="FALLBACK_NORMAL_LOBBY",reason="COHORT_NOT_LOCAL"} end
   roster[#roster+1]=player
  end
  local okGuid,guid=pcall(function() return deps.http:GenerateGUID(false) end)
  if not okGuid or type(guid)~="string" or #guid<32 then
   return {status="FALLBACK_NORMAL_LOBBY",reason="GUID_FAILURE"} end
  local id=guid
  -- One shared ReservedServerId for the 8/16 players; the server-created
  -- matchId and seed are independent of client input and stable for retry.
  local seed=tonumber(string.sub(string.gsub(guid,"%-",""),1,7),16)
  if not seed then return {status="FALLBACK_NORMAL_LOBBY",reason="SEED_FAILURE"} end
  seed=1+(seed%2147483646)
  local ticket={
   version=M.VERSION,matchId=id,epoch=epoch,mode=plan.mode,region=plan.region,
   seed=seed,createdAt=deps.now(),players=ids,
   reservedServerId=id,originJobId=deps.jobId,stat="RESERVED",
  }
  local map=deps.claimMap
  local claimed
  local okClaim=pcall(function()
   claimed=map:UpdateAsync("m:"..id,function(previous:any)
    if previous~=nil then return previous end
    return ticket
   end,TTL_SECONDS)
  end)
  if not okClaim or type(claimed)~="table" or claimed.matchId~=id
    or claimed.originJobId~=deps.jobId or claimed.epoch~=epoch then
   return {status="FALLBACK_NORMAL_LOBBY",reason="CLAIM_FAILED"} end
  -- Do not instantiate a second server or teleport controller. One Roblox
  -- service call owns the entire LOCAL cohort. Results can be partial/late.
  local options=deps.optionsFactory()
  options.ReservedServerId=id
  options:SetTeleportData({
   version=M.VERSION,matchId=id,epoch=epoch,seed=seed,mode=plan.mode,
   roster=ids,
   teamA=if plan.mode=="TEAM" then plan.teamA else nil,
   teamB=if plan.mode=="TEAM" then plan.teamB else nil,
   -- On destination ALWAYS verify ticket in claimMap; teleportData alone
   -- never grants role, damage, squad, health, score or loot privileges.
   joinDataTrusted=false,
  })
  local pending={
   matchId=id,epoch=epoch,options=options,players=roster,createdAt=deps.now(),
   attempt=0,placeId=placeId,seed=seed
  }
  self.byMatch[id]=pending
  for _,player in ipairs(roster) do self.byUser[player.UserId]=pending end
  local ok,err=pcall(function()
   return deps.teleport:TeleportAsync(placeId,roster,options)
  end)
  if not ok then
   for _,player in ipairs(roster) do self.byUser[player.UserId]=nil end
   self.byMatch[id]=nil
   return {status="FALLBACK_NORMAL_LOBBY",reason="TELEPORT_THROW",detail=tostring(err)}
  end
  return {status="TELEPORT_INITIATED",matchId=id,players=#roster,
   seed=seed,requiresDestinationTicketVerification=true}
 end
 function self:teleportFailed(player:any):any
  if not player or not validInt(player.UserId,1,999999999999)
    then return {status="IGNORED"} end
  local pending=self.byUser[player.UserId]
  if not pending then return {status="IGNORED"} end
  if player.Parent~=deps.players or deps.now()-pending.createdAt>90 then
   self.byUser[player.UserId]=nil
   return {status="FALLBACK_NORMAL_LOBBY",reason="LEFT_OR_EXPIRED"} end
  if pending.attempt>=2 then
   self.byUser[player.UserId]=nil
   return {status="FALLBACK_NORMAL_LOBBY",reason="RETRIES_EXHAUSTED"} end
  pending.attempt=pending.attempt+1
  local ok=pcall(function()
   -- Same reserved server ID and same match ticket, no duplicate world.
   deps.teleport:TeleportAsync(pending.placeId,{player},pending.options)
  end)
  if not ok then
   self.byUser[player.UserId]=nil
   return {status="FALLBACK_NORMAL_LOBBY",reason="RETRY_FAILED"} end
  return {status="RETRY_INITIATED",attempt=pending.attempt,matchId=pending.matchId}
 end
 function self:playerLeft(userId:any)
  if not validInt(userId,1,999999999999) then return end
  self.byUser[userId]=nil
 end
 function self:expirePending()
  local now=deps.now()
  for matchId,pending in pairs(self.byMatch) do
   if now-pending.createdAt>=90 then
    for _,p in ipairs(pending.players) do
     if self.byUser[p.UserId]==pending then self.byUser[p.UserId]=nil end
    end
    self.byMatch[matchId]=nil
   end
  end
 end
 return self
end
function M.fromRoblox(featureEnabled:boolean, targetPlaceId:number):any
 local RunService=game:GetService("RunService")
 local Players=game:GetService("Players")
 local HttpService=game:GetService("HttpService")
 local TeleportService=game:GetService("TeleportService")
 local MemoryStoreService=game:GetService("MemoryStoreService")
 return M.create({
  enabled=featureEnabled==true,
  isStudio=RunService:IsStudio(),
  inReservedServer=game.PrivateServerId~="",
  jobId=game.JobId, targetPlaceId=targetPlaceId,
  now=os.time,players=Players,teleport=TeleportService,http=HttpService,
  claimMap=MemoryStoreService:GetHashMap("GQ802_MATCH_CLAIMS_V1"),
  optionsFactory=function()return Instance.new("TeleportOptions")end,
 })
end
return M
