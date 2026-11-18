--!strict
-- GQ8_MUSOU_FEVER_CHAIN_20261119 / OWNER #824
-- Server-owned POLICY ONLY. No new Combat, Swarm, HP, KO, score, UI Remote or Store authority.
-- Bind this module to existing verified server Combat/Swarm and reuse #801 KO finishers.
local M = {}
M.FEATURE_ID = "GQ8_MUSOU_FEVER_CHAIN_20261119"
M.FIRST_READY_SECONDS = 70
M.RECHARGE_SECONDS = 105
M.FEVER_RECHARGE_SECONDS = 90
M.BASE_SECONDS = 8
M.HARD_CAP_SECONDS = 20
M.MAX_KO_EXTENSION_SECONDS = 6
M.FEVER_BONUS_SECONDS = 6
M.COMBO_WINDOW_SECONDS = 3
M.RUSH_THRESHOLD = 3
M.FEVER_THRESHOLD = 7
M.MAX_RECEIPTS = 24
M.MAX_MATCH_RECEIPTS = 512

-- Base multipliers apply ONCE at the existing server damage/KO owner.
-- Do not multiply these with a separate permanent power fantasy awakening.
M.ROLES = {
 WARRIOR={neutral=3.8,player=1.30,boss=1.35,castle=.70,
  tell="神威・金白の天輪",sigil="DIVINE_CLEAVE",shape="GOD_RING",color="GOLD"},
 MAGE={neutral=3.6,player=1.25,boss=1.35,castle=.65,
  tell="虹彩・元素の流星",sigil="PRISM_COMET",shape="PRISM_RUNES",color="CYAN"},
 NINJA={neutral=3.5,player=1.35,boss=1.25,castle=.60,
  tell="紅影・瞬閃連斬",sigil="SHADOW_CASCADE",shape="AFTERIMAGE",color="CRIMSON"},
 TRAPPER={neutral=3.6,player=1.22,boss=1.30,castle=.65,
  tell="紫電・重力六角陣",sigil="GRAVITY_HEX",shape="FLOATING_HEX",color="VIOLET"},
 BUILDER={neutral=3.7,player=1.22,boss=1.35,castle=.70,
  tell="超機械・電磁歯車",sigil="GEAR_STORM",shape="GEAR_HALO",color="AMBER"},
 BEAST={neutral=4.0,player=1.28,boss=1.40,castle=.70,
  tell="獣王・大地の咆哮",sigil="BEAST_ROAR",shape="BEAST_CROWN",color="EMERALD"},
 ZOMBIE={neutral=3.4,player=1.20,boss=1.30,castle=.60,
  tell="冥王・呪魂の渦",sigil="CURSE_SPIRAL",shape="CURSE_CROWN",color="PURPLE"},
}
M.NEUTRAL_FEVER_BONUS=1.25

local function finite(n)
 return type(n)=="number" and n==n and n>=0 and n<math.huge
end
local function ident(v)
 if type(v)=="number" and finite(v) and v>=1 and v%1==0 then return tostring(v) end
 if type(v)=="string" and #v>=1 and #v<=64 then return v end
 return nil
end
local function baseContext(s,c)
 return type(s)=="table" and type(s.entries)=="table"
  and type(c)=="table" and s.epoch~=nil and c.epoch==s.epoch
  and finite(s.startedAt) and finite(c.now) and c.now>=s.startedAt
  and c.serverCurrent==true and c.roleVerified==true
  and (c.mode=="TEAM" or c.mode=="BATTLE_ROYALE") and c.phase=="ACTIVE"
  and ident(c.playerId)~=nil and ident(c.avatarEpoch)~=nil
  and M.ROLES[c.role]~=nil
end
local function eligible(c)
 return c.characterAlive==true and c.castleAlive==true
  and c.downed==false and c.eliminated==false
  and c.carryingEgg==false and c.invulnerable==false
  and c.shieldActive==false
end
local function entry(s,c,create)
 local key=ident(c.playerId)
 if not key then return nil end
 local e=s.entries[key]
 if not e and create then
  e={role=c.role,avatar=ident(c.avatarEpoch),active=false,
   startAt=0,endsAt=0,capAt=0,readyAt=s.startedAt+M.FIRST_READY_SECONDS,
   lastMutation=-1,used=0,chain=0,lastKO=-math.huge,fever=false,
   totalExtend=0,receiptCount=0,receipts={},seen={},seenCount=0}
  s.entries[key]=e
 elseif e and e.role~=c.role then
  -- Role changes must go through the existing authoritative match selection.
  return nil
 elseif e and e.avatar~=ident(c.avatarEpoch) then
  if not create then return nil end
  -- Respawns cancel the active state, but NEVER refill ready timer.
  e.active=false
  e.avatar=ident(c.avatarEpoch)
 end
 return e
end
local function activeEntry(s,c)
 if not baseContext(s,c) or not eligible(c) then return nil end
 local e=entry(s,c,false)
 if not e or not e.active or c.now<e.startAt or c.now>=e.endsAt then return nil end
 if c.now<e.lastMutation then return nil end
 return e
end
local function phaseName(e,now)
 if e.fever then return "KAKUHEN" end
 if e.chain>=M.RUSH_THRESHOLD and now-e.lastKO<=M.COMBO_WINDOW_SECONDS then return "RUSH" end
 return "MUSOU"
end
local function updateRecharge(e)
 local cd=if e.fever then M.FEVER_RECHARGE_SECONDS else M.RECHARGE_SECONDS
 e.readyAt=e.endsAt+cd
end

function M.newRound(epoch,serverStartAt)
 if epoch==nil or not finite(serverStartAt) then error("RED_ROUND_SCOPE") end
 return {epoch=epoch,startedAt=serverStartAt,entries={}}
end
function M.activate(s,c)
 if not baseContext(s,c) or not eligible(c) then return false,"SERVER_SCOPE_OR_CONFLICT" end
 local e=entry(s,c,true)
 if not e then return false,"ROLE_SWITCH_BLOCKED" end
 if c.now<e.lastMutation then return false,"TIME_REWIND" end
 if e.active and c.now<e.endsAt then return false,"ALREADY_ACTIVE" end
 if c.now<e.readyAt then return false,"RECHARGING" end
 e.active=true
 e.startAt=c.now
 e.endsAt=c.now+M.BASE_SECONDS
 e.capAt=c.now+M.HARD_CAP_SECONDS
 e.lastMutation=c.now
 e.used+=1
 e.chain=0
 e.lastKO=-math.huge
 e.fever=false
 e.totalExtend=0
 e.receiptCount=0
 e.receipts={}
 updateRecharge(e)
 return true,{phase="MUSOU",endAt=e.endsAt,readyAt=e.readyAt,
  sigil=M.ROLES[e.role].sigil,role=e.role,uses=e.used}
end

-- Call ONLY after the existing authoritative KO + score ledger confirms this
-- death event exactly once. The server sends a unique receipt ID, not a client hit.
function M.onConfirmedKO(s,c,ko)
 local e=activeEntry(s,c)
 if not e then return false,"NOT_ACTIVE" end
 if type(ko)~="table" or ko.serverConfirmed~=true
   or ko.enemyConfirmed~=true or ko.creditVerified~=true
   or ko.scoreEligible~=true or ko.creditedPlayerId~=c.playerId
   or ko.isSummoned~=false or ko.isConverted~=false
   or ident(ko.victimId)==nil or ident(ko.receiptId)==nil
   or ident(ko.victimId)==ident(c.playerId) then
  return false,"UNVERIFIED_KO"
 end
 local kind=ko.targetKind
 if kind~="NEUTRAL" and kind~="HUMAN" and kind~="BOSS" then
  return false,"INVALID_TARGET"
 end
 if e.seen[ident(ko.receiptId)] then return false,"REPLAYED_KO" end
 if e.seenCount>=M.MAX_MATCH_RECEIPTS then return false,"MATCH_KO_BUDGET" end
 if e.receiptCount>=M.MAX_RECEIPTS then return false,"KO_BUDGET" end
 local w=if kind=="NEUTRAL" then 1 else 2
 if c.now-e.lastKO>M.COMBO_WINDOW_SECONDS then e.chain=0 end
 e.chain+=w
 e.lastKO=c.now
 e.lastMutation=c.now
 e.receiptCount+=1
 e.receipts[ident(ko.receiptId)]=true
 e.seen[ident(ko.receiptId)]=true
 e.seenCount+=1
 local seconds=if kind=="NEUTRAL" then .5 else 1.0
 local room=M.MAX_KO_EXTENSION_SECONDS-e.totalExtend
 local add=math.min(room,seconds)
 if add>0 then
  e.endsAt=math.min(e.capAt,e.endsAt+add)
  e.totalExtend+=add
 end
 if not e.fever and e.chain>=M.FEVER_THRESHOLD then
  e.fever=true
  e.endsAt=math.min(e.capAt,e.endsAt+M.FEVER_BONUS_SECONDS)
 end
 updateRecharge(e)
 return true,{phase=phaseName(e,c.now),chain=e.chain,fever=e.fever,
  endAt=e.endsAt,remaining=e.endsAt-c.now,readyAt=e.readyAt,
  sigil=M.ROLES[e.role].sigil}
end

-- Existing Combat invokes this once before DAMAGE, never in addition to another multiplier.
-- For PvP and bosses, KAKUHEN intentionally adds NO extra multiplier.
function M.attackMultiplier(s,c,targetKind)
 local e=activeEntry(s,c)
 if not e then return 1 end
 local role=M.ROLES[e.role]
 if targetKind=="NEUTRAL" then
  return role.neutral * (if e.fever then M.NEUTRAL_FEVER_BONUS else 1)
 elseif targetKind=="HUMAN" then return role.player
 elseif targetKind=="BOSS" then return role.boss
 elseif targetKind=="CASTLE" then return role.castle
 end
 return 1
end
function M.allowEggObjective(s,c)
 if not baseContext(s,c) then return false end
 local e=entry(s,c,false)
 -- Fail closed even after egg pickup revokes effective attack power:
 -- the actual item owner must cancel this mode before accepting objective actions.
 return not (e and e.active and c.now>=e.startAt and c.now<e.endsAt)
end
-- Only the existing match / character owner calls cancel, including
-- pickup, death, invul activation, shield activation and match transitions.
function M.cancel(s,c)
 if type(s)~="table" or type(s.entries)~="table"
  or type(c)~="table" or c.epoch~=s.epoch then return false end
 local e=s.entries[ident(c.playerId)]
 if not e or e.avatar~=ident(c.avatarEpoch) then return false end
 e.active=false
 return true
end
function M.snapshot(s,c)
 if not baseContext(s,c) then return {active=false,phase="OFF",remaining=0,readyIn=-1} end
 local e=entry(s,c,false)
 if not e then
  return {active=false,phase="CHARGING",remaining=0,
   readyIn=math.max(0,s.startedAt+M.FIRST_READY_SECONDS-c.now),role=c.role}
 end
 local live=activeEntry(s,c)
 if not live then
  return {active=false,phase="CHARGING",remaining=0,
   readyIn=math.max(0,e.readyAt-c.now),role=e.role,uses=e.used}
 end
 local rule=M.ROLES[e.role]
 return {active=true,phase=phaseName(e,c.now),remaining=e.endsAt-c.now,
  readyIn=math.max(0,e.readyAt-c.now),role=e.role,
  chain=e.chain,fever=e.fever,uses=e.used,
  tell=rule.tell,sigil=rule.sigil,shape=rule.shape,color=rule.color,
  -- Source owner may replicate these read-only cues via its EXISTING channels.
  visibleToEnemies=true,androidLod="1_HIGHLIGHT_1_BILLBOARD_1_EMITTER"}
end
return M
