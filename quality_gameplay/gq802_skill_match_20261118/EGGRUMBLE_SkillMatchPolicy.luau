--!strict
-- GQ802: SERVER-VERIFIED queue cohort + party-safe team proposal only.
-- Existing lobby alone owns MemoryStore, matchmaking queue, reserves and teleports.
local M={}
M.MIN_PLAYERS=8
M.MAX_PLAYERS=16
local function finite(v:any):boolean
 return type(v)=="number" and v==v and v>-math.huge and v<math.huge
end
local function integer(v:any,lo:number,hi:number):boolean
 return finite(v) and v>=lo and v<=hi and v%1==0
end
local function ok(ticket:any,now:number,mode:string,region:string):boolean
 return type(ticket)=="table" and ticket.serverVerified==true
  and ticket.roundEligible==true and ticket.mode==mode and ticket.region==region
  and integer(ticket.userId,1,999999999999) and integer(ticket.level,1,300)
  and integer(ticket.games,0,100000) and integer(ticket.rating,300,2500)
  and finite(ticket.queuedAtSeconds) and ticket.queuedAtSeconds>=0
  and ticket.queuedAtSeconds<=now and now-ticket.queuedAtSeconds<=180
  and (ticket.partyKey==nil or (type(ticket.partyKey)=="string" and #ticket.partyKey>=1 and #ticket.partyKey<=64))
  and type(ticket.sessionId)=="string" and #ticket.sessionId>0
end
local function strength(t:any):number
 -- Level is only a mild input, so new players aren't crushed by older accounts.
 return t.rating+math.min(t.level,120)*2+math.min(t.games,200)*0.4
end
local function makeGroups(tickets:any,now:number,mode:string,region:string):{any}
 local byKey={}
 local keys={}
 local seenIds={}
 for _,t in ipairs(tickets) do
  if ok(t,now,mode,region) and not seenIds[t.userId] then
   seenIds[t.userId]=true
   local key=if t.partyKey then "party:"..t.partyKey else "solo:"..tostring(t.userId)
   if not byKey[key] then
    byKey[key]={key=key,members={},ratingMin=2500,ratingMax=300,
      newestTime=0,firstTime=now,novice=nil,totalStrength=0}
    keys[#keys+1]=key
   end
   local g=byKey[key]
   g.members[#g.members+1]=t.userId
   g.totalStrength=g.totalStrength+strength(t)
   g.ratingMin=math.min(g.ratingMin,t.rating)
   g.ratingMax=math.max(g.ratingMax,t.rating)
   g.firstTime=math.min(g.firstTime,t.queuedAtSeconds)
   g.newestTime=math.max(g.newestTime,t.queuedAtSeconds)
   local newcomer=t.games<=5 and t.level<=12
   if g.novice==nil then g.novice=newcomer
   elseif g.novice~=newcomer then g.mixedBand=true end
  end
 end
 local groups={}
 for _,key in ipairs(keys) do
  local g=byKey[key]
  if #g.members<=4 and not g.mixedBand then groups[#groups+1]=g end
 end
 table.sort(groups,function(a,b)
  if a.firstTime==b.firstTime then return a.key<b.key end
  return a.firstTime<b.firstTime
 end)
 return groups
end
local function splitBalanced(groups:{any},players:number,age:number):any
 local half=players/2
 local bestGap=math.huge
 local bestA,bestB
 local function rec(i:number,countA:number,countB:number,sumA:number,sumB:number,a:any,b:any)
  if countA>half or countB>half then return end
  if i>#groups then
   if countA==half and countB==half then
    local gap=math.abs(sumA-sumB)/math.max(1,(sumA+sumB)/2)
    if gap<bestGap then
     bestGap=gap
     bestA=table.clone(a);bestB=table.clone(b)
    end
   end
   return
  end
  local g=groups[i]
  if countA+#g.members<=half then
   a[#a+1]=g
   rec(i+1,countA+#g.members,countB,sumA+g.totalStrength,sumB,a,b)
   a[#a]=nil
  end
  if countB+#g.members<=half then
   b[#b+1]=g
   rec(i+1,countA,countB+#g.members,sumA,sumB+g.totalStrength,a,b)
   b[#b]=nil
  end
 end
 rec(1,0,0,0,0,{}, {})
 local allowed=if age>=45 then 0.16 else 0.10
 if not bestA or not bestB or bestGap>allowed then return nil end
 local teamA,teamB={},{}
 for _,g in ipairs(bestA) do for _,id in ipairs(g.members) do teamA[#teamA+1]=id end end
 for _,g in ipairs(bestB) do for _,id in ipairs(g.members) do teamB[#teamB+1]=id end end
 return {teamA=teamA,teamB=teamB,gapRatio=bestGap}
end
function M.propose(tickets:any,now:any,mode:any,region:any):any
 if type(tickets)~="table" or #tickets>128 or not finite(now) or now<0
  or (mode~="TEAM" and mode~="BR") or type(region)~="string" or #region<1
  or #region>32 then return {status="REJECT_INVALID_INPUT"} end
 local groups=makeGroups(tickets,now,mode,region)
 local eligible=0
 for _,g in ipairs(groups) do eligible=eligible+#g.members end
 if eligible<M.MIN_PLAYERS then
  return {status="FALLBACK_NORMAL_LOBBY",reason="LOW_POPULATION",playersEligible=eligible}
 end
 for _,target in ipairs({16,8}) do
  if eligible>=target then
   for anchor=1,#groups do
    local g0=groups[anchor]
    local maxAge=math.max(0,now-g0.firstTime)
    local maxBand=240+math.min(maxAge,90)*2
    local set={}
    local n,minRating,maxRating=0,2500,300
    for j=anchor,#groups do
     local g=groups[j]
     local lo=math.min(minRating,g.ratingMin)
     local hi=math.max(maxRating,g.ratingMax)
     if g.novice==g0.novice and n+#g.members<=target and hi-lo<=maxBand then
      set[#set+1]=g
      n=n+#g.members;minRating=lo;maxRating=hi
      if n==target then break end
     end
    end
    if n==target then
     local balanced=splitBalanced(set,target,maxAge)
     if balanced then
      return {status="MATCH_READY",mode=mode,region=region,
       size=target,teamA=balanced.teamA,teamB=balanced.teamB,
       ratingMin=minRating,ratingMax=maxRating,noviceBand=g0.novice,
       teamGapRatio=balanced.gapRatio,
       -- BR participants are separately allocated players, NEVER a team alliance.
       teamAssignmentDisabled=mode=="BR",freeForAll=mode=="BR",
       -- Existing lobby MUST atomically claim tickets and reserve server.
       requiresAuthoritativeQueueClaim=true,
       teleportAuthorizedHere=false,randomStageAssignedHere=false}
     end
    end
   end
  end
 end
 return {status="WAIT_OR_NORMAL_LOBBY",reason="NO_FAIR_WHOLE_PARTY_COHORT",playersEligible=eligible}
end
return M
