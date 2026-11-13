--!strict
-- G9 PRIVATE Studio-only S2 egg-tag rule state. No Roblox services / paid / network / DataStores.
-- Pure deterministic server input policy; official S1 H1 Game server remains untouched.
local R={}
R.WIN_SCORE=3
R.ACTION_COOLDOWN=.45
R.CARRY_LIMIT=45
R.MAX_DISTANCE_SQUARED=144
R.TEAMS={"RED","BLUE"}
local function validTeam(s: any): boolean
 return s=="RED" or s=="BLUE"
end
local function finite(v: any): boolean
 return type(v)=="number" and v==v and math.abs(v)<1000000000
end
local function validUser(v: any): boolean
 -- Studio fake-player UserIds may be negative; 0 cannot identify a carrier.
 return finite(v) and v%1==0 and v~=0
end
local function other(team: string): string
 return if team=="RED" then "BLUE" else "RED"
end
function R.other(team: any): string?
 if not validTeam(team) then return nil end
 return other(team)
end
function R.new()
 return {home={RED=true,BLUE=true},carrier={RED=0,BLUE=0},
  since={RED=-1,BLUE=-1},scores={RED=0,BLUE=0},
  last={},winner=""}
end
local function clearEgg(state,team)
 state.home[team]=true
 state.carrier[team]=0
 state.since[team]=-1
end
-- This function is called ONLY by server after recomputing real player distance to source Part.
-- A failed action leaves state exactly unchanged.
function R.apply(state: any,action: any,team: any,userId: any,eggTeam: any,dist2: any,now: any): (boolean,string)
 if type(state)~="table" or type(state.home)~="table"
   or type(state.carrier)~="table" or type(state.scores)~="table"
   or type(state.since)~="table" or type(state.last)~="table" then
  return false,"BAD_STATE"
 end
 if not validTeam(team) or not validTeam(eggTeam) or not validUser(userId) then
  return false,"BAD_ACTOR"
 end
 if action~="STEAL" and action~="SCORE" and action~="RESCUE" then return false,"BAD_ACTION" end
 if state.winner~="" then return false,"ROUND_FINISHED" end
 if not finite(dist2) or dist2<0 or dist2>R.MAX_DISTANCE_SQUARED then return false,"TOO_FAR" end
 if not finite(now) or now<0 then return false,"INVALID_CLOCK" end
 local last=state.last[userId]
 if last~=nil and (not finite(last) or now<last or now-last<R.ACTION_COOLDOWN) then
  return false,"COOLDOWN"
 end
 local enemy=other(team)
 if action=="STEAL" then
  if eggTeam~=enemy then return false,"OWN_EGG" end
  if not state.home[eggTeam] or state.carrier[eggTeam]~=0 then return false,"ALREADY_TAKEN" end
  if state.carrier[team]~=0 then return false,"ALREADY_CARRYING" end
  state.home[eggTeam]=false
  state.carrier[eggTeam]=userId
  state.since[eggTeam]=now
  state.last[userId]=now
  return true,"STOLEN"
 elseif action=="SCORE" then
  if eggTeam~=team then return false,"WRONG_PAD" end
  if not state.home[team] then return false,"OWN_EGG_MISSING" end
  if state.carrier[enemy]~=userId then return false,"NO_ENEMY_EGG" end
  clearEgg(state,enemy)
  state.scores[team]+=1
  state.last[userId]=now
  if state.scores[team]>=R.WIN_SCORE then
   state.winner=team
   return true,"ROUND_WIN"
  end
  return true,"SCORED"
 else -- RESCUE: physically tag current enemy carrier by touching their prompt; server verifies range.
  if eggTeam~=team then return false,"WRONG_RESCUE_TEAM" end
  if state.home[team] or state.carrier[team]==0 then return false,"NOT_STOLEN" end
  if state.carrier[team]==userId then return false,"SELF_RESCUE" end
  clearEgg(state,team)
  state.last[userId]=now
  return true,"RESCUED"
 end
end
function R.release(state: any,userId: any): number
 if type(state)~="table" or type(state.carrier)~="table" or not validUser(userId) then return 0 end
 local restored=0
 for _,egg in ipairs(R.TEAMS) do
  if state.carrier[egg]==userId then
   clearEgg(state,egg)
   restored+=1
  end
 end
 return restored
end
function R.expire(state: any,now: any): number
 if type(state)~="table" or type(state.carrier)~="table" or not finite(now) or now<0 then return 0 end
 local expired=0
 for _,egg in ipairs(R.TEAMS) do
  if state.carrier[egg]~=0 and finite(state.since[egg])
     and now-state.since[egg]>=R.CARRY_LIMIT then
   clearEgg(state,egg)
   expired+=1
  end
 end
 return expired
end
return R
