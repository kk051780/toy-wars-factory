--!strict
-- EGGRUMBLE V3, pure server-side timeout boundary. Not production-wired.
-- Reuse the existing Rules state and RoundReplay; never create a second match.
local Deadline={}
Deadline.DEFAULT_SECONDS=900

local function timeOK(t:any):boolean
 return type(t)=="number" and t==t and t>=0 and t<math.huge
end

function Deadline.new(startedAt:number,matchId:string,seconds:number?):any
 assert(timeOK(startedAt),"invalid monotonic start")
 assert(type(matchId)=="string" and #matchId>0,"invalid match identity")
 local duration=seconds or Deadline.DEFAULT_SECONDS
 assert(timeOK(duration) and duration%1==0 and duration>=60 and duration<=3600,"invalid duration")
 return {start=startedAt,matchId=matchId,seconds=duration,consumed=false}
end

local function survivingSides(state:any):number
 if type(state.castles)~="table" then return 0 end
 local sides={}
 for id,castle in pairs(state.castles) do
  if type(castle)=="table" and castle.alive==true then
   local side=if state.mode=="TEAM" then castle.team else id
   if type(side)=="string" and #side>0 then sides[side]=true end
  end
 end
 local total=0
 for _ in pairs(sides) do total+=1 end
 return total
end

function Deadline.check(state:any,lease:any,now:number,matchId:string):(boolean,string)
 if type(state)~="table" or type(lease)~="table" then return false,"INVALID_STATE" end
 if lease.consumed==true then return false,"ALREADY_APPLIED" end
 if state.mode~="TEAM" and state.mode~="BATTLE_ROYALE" then return false,"INVALID_MODE" end
 if type(matchId)~="string" or matchId~=lease.matchId then return false,"STALE_MATCH" end
 if state.phase~="ACTIVE" or state.winner~=nil then return false,"ALREADY_FINISHED" end
 if type(state.events)~="table" or survivingSides(state)<2 then return false,"NO_CONTEST" end
 if not timeOK(now) or not timeOK(lease.start) or not timeOK(lease.seconds)
  or now<lease.start then return false,"INVALID_CLOCK" end
 if now-lease.start<lease.seconds then return false,"BEFORE_DEADLINE" end
 return true,"TIME_LIMIT"
end

-- Fallback DRAW only when neither side has legitimately won. A true
-- all-castles victory continues to be decided by the original CastleMatchRules.
-- The original ResultService/Replay sees a normal FINISHED round; no castle
-- HP, egg inventory, team deposits, individual KOs, or rewards are fabricated.
function Deadline.expire(state:any,lease:any,now:number,matchId:string):(boolean,string)
 local allowed,reason=Deadline.check(state,lease,now,matchId)
 if not allowed then return false,reason end
 lease.consumed=true
 state.winner="DRAW"
 state.phase="FINISHED"
 table.insert(state.events,{type="TIME_LIMIT_DRAW",mode=state.mode,matchId=matchId,
  elapsed=math.floor(now-lease.start)})
 return true,"TIME_LIMIT_DRAW"
end

return Deadline
