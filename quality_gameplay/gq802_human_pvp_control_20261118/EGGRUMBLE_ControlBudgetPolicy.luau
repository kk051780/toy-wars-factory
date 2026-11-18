--!strict
-- GQ802: Pure SERVER-SIDE per-avatar hard-CC budget with hit-id de-dup.
-- An authoritative Combat owner must call this using verified hit receipts.
-- NO HP/damage, Humanoid, Store, RemoteEvent, physics or visual object writer.
local Cue=require("./EGGRUMBLE_PvPControlCuePolicy")
local M={}
local WINDOW=8
local MAX_SEEN=72
local function validNumber(v:any):boolean
 return type(v)=="number" and v==v and v>=0 and v<1e10
end
local function validKey(v:any):boolean
 return type(v)=="string" and #v>=1 and #v<=96
end
function M.new(epoch:any):any
 if not validKey(epoch) then return nil end
 return {epoch=epoch,targets={}}
end
function M.resetRound(state:any,epoch:any):boolean
 if type(state)~="table" or not validKey(epoch) then return false end
 state.epoch=epoch
 state.targets={}
 return true
end
function M.clearTarget(state:any,avatarKey:any):boolean
 if type(state)~="table" or type(state.targets)~="table"
  or not validKey(avatarKey) then return false end
 state.targets[avatarKey]=nil
 return true
end
function M.consume(state:any,receipt:any):any
 if type(state)~="table" or not validKey(state.epoch)
  or type(state.targets)~="table" or type(receipt)~="table"
  or receipt.epoch~=state.epoch or not validKey(receipt.targetAvatarKey)
  or not validKey(receipt.uniqueHitId)
  or not validNumber(receipt.serverTimeSeconds)
  or receipt.serverConfirmedHit~=true or receipt.epochCurrent~=true
  or receipt.matchActive~=true then return nil end
 local now=receipt.serverTimeSeconds
 local victim=receipt.targetAvatarKey
 local s=state.targets[victim]
 if not s then s={seen={},recent={},immuneUntil=0,lastNow=0} end
 if now<s.lastNow then return nil end -- stale callbacks cannot rewind a window
 -- A consumed receipt is keyed to the same target avatar and round.
 if s.seen[receipt.uniqueHitId] then return nil end
 local recent={}
 local count,total=0,0
 for _,x in ipairs(s.recent) do
  if now-x.time<WINDOW then
   recent[#recent+1]=x
   count=count+1
   total=total+x.duration
  end
 end
 -- Any caller-provided historical counters are ignored, never trusted.
 local own=table.clone(receipt)
 own.targetHardCCCount8s=count
 own.targetHardCCSeconds8s=math.min(8,total)
 own.targetControlImmunityUntil=s.immuneUntil
 local result=Cue.select(own)
 if not result then return nil end
 s.recent=recent
 s.lastNow=now
 -- Seen events are expired each hit, memory remains bounded after long fights.
 for key,stamp in pairs(s.seen) do
  if now-stamp>=WINDOW then s.seen[key]=nil end
 end
 local seenCount=0
 for _ in pairs(s.seen) do seenCount=seenCount+1 end
 if seenCount>=MAX_SEEN then return nil end
 s.seen[receipt.uniqueHitId]=now
 if result.hardControl then
  s.recent[#s.recent+1]={time=now,duration=result.durationSeconds}
  if #s.recent>=2 or total+result.durationSeconds>=1.8 then
   s.immuneUntil=math.max(s.immuneUntil,now+2)
  end
 end
 state.targets[victim]=s
 return result
end
M.WINDOW_SECONDS=WINDOW
M.MAX_SEEN_RECEIPTS_PER_AVATAR=MAX_SEEN
return M
