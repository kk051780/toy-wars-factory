--!strict
-- GQ805 server-side receipt proposal only. Authoritative match Host + persistent wallet owner apply once.
local M={}
local function safe(v:any):number
 if type(v)~="number" or v~=v or v==math.huge or v==-math.huge or v<0 then return -1 end
 return math.floor(v)
end
function M.quote(r:any):any
 if type(r)~="table" or r.serverVerified~=true or r.phase~="FINISHED" then return nil end
 if type(r.matchId)~="string" or #r.matchId<4 then return nil end
 if type(r.userId)~="string" or r.userId=="" then return nil end
 if r.isHuman~=true or r.wasAFK==true or r.wasBanned==true or r.playerEligible~=true then return nil end
 if safe(r.playedSeconds)<120 then return nil end
 if type(r.won)~="boolean" then return nil end
 local ko,eggs,castle=safe(r.neutralKOs),safe(r.eggsDeposited),safe(r.castleContributions)
 if ko<0 or eggs<0 or castle<0 then return nil end
 local base=if r.won then 120 else 60
 local earned=base+math.min(40,ko*2)+math.min(45,eggs*15)+math.min(25,castle*25)
 return {kind="BP_AWARD_PERMIT",receiptKey=r.matchId..":"..r.userId,
  battlePoints=earned,basePoints=base,win=r.won,
  mustApplyOnce=true,requiresPersistentWallet=true,source="ORIGINAL_MATCH_HOST"}
end
M.MAX_MATCH_BP=230
return M
