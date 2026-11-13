-- EGG RAID RUMBLE optional read-only UX cue policy.
-- Never awards points, XP, items or changes gameplay authority.
local M = {}
local CUES = {
 SCOUT_ASSIST = {title="みつけた！", detail="なかまと たまごを おいかけよう", icon="👀"},
 SEA_ESCORT = {title="うみルート！", detail="なかまと たまごを はこぼう", icon="⛵"},
 TRAP_GUARD = {title="ナイスガード！", detail="なかまを まもった！", icon="🛡"},
 CASTLE_RECAPTURE = {title="とりかえした！", detail="おしろを まもった！", icon="🏰"},
}
local function finite(n)
 return type(n)=="number" and n==n and n~=math.huge and n~=-math.huge
end
local function validId(s)
 return type(s)=="string" and #s>=1 and #s<=64 and s:match("^[%w_%-]+$")~=nil
end
local function validSeq(n)
 return finite(n) and n%1==0 and n>=1 and n<=1000000000
end
function M.new()
 return {roundId=nil, roundSerial=0, lastSeq=0, nextAllowed=0}
end
-- packet must be derived by the sole #220 integrator from an authenticated
-- server->client status event. This module is NOT an authentication boundary.
-- packet={roundId,roundSerial,seq,kind,team,expiresAt}
function M.accept(state,packet,now,localTeam)
 if type(state)~="table" or type(packet)~="table" or not finite(now) then return nil end
 if localTeam~="RED" and localTeam~="BLUE" then return nil end
 if packet.team~=localTeam or not validId(packet.roundId) or not validSeq(packet.roundSerial) or not validSeq(packet.seq) then return nil end
 local cue=CUES[packet.kind]
 if not cue or not finite(packet.expiresAt) then return nil end
 if packet.expiresAt<now or packet.expiresAt>now+4 then return nil end
 local currentSerial=state.roundSerial or 0
 if not finite(currentSerial) or currentSerial%1~=0 or currentSerial<0 then return nil end
 if packet.roundSerial<currentSerial then return nil end
 if packet.roundSerial==currentSerial and state.roundId~=packet.roundId then return nil end
 if packet.roundSerial>currentSerial then
  state.roundId=packet.roundId; state.roundSerial=packet.roundSerial
  state.lastSeq=0; state.nextAllowed=0
 end
 if packet.seq<=state.lastSeq then return nil end
 state.lastSeq=packet.seq
 if now<state.nextAllowed then return nil end
 state.nextAllowed=now+2.2
 return {title=cue.title,detail=cue.detail,icon=cue.icon,duration=1.55,kind=packet.kind}
end
return M
