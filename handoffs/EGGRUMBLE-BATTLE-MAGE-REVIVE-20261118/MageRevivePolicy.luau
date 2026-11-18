--!strict
-- #765 lane8 BATTLE-MAGE-REVIVE: server-only policy, not a second HP/Combat authority.
-- The existing Host/Combat must authenticate and supply every context field. Do not call from a Remote directly.
-- This source cannot change a Humanoid, Remote, match, XP, score, or DataStore.
local M = {}
M.FEATURE_ID = "BATTLE-MAGE-REVIVE"
M.HEAL_COOLDOWN = 18
M.HEAL_MAX_FRACTION = 0.30
M.REVIVE_COOLDOWN = 40
M.CHANNEL_SECONDS = 3
M.CHANNEL_GRACE_SECONDS = 2
M.DOWNED_WINDOW_SECONDS = 60
M.REVIVE_HP_FRACTION = 0.35

local function finite(v: any): boolean
 return type(v) == "number" and v == v and v ~= math.huge and v ~= -math.huge
end

local function id(v: any): boolean
 return type(v) == "string" and #v > 0 and #v <= 96
end

-- All booleans must be server-computed: current human/AI membership, session,
-- both *current* character identities, team, line of sight, caster ability.
local function common(c: any): string?
 if type(c) ~= "table" then return "BAD_CONTEXT" end
 if not finite(c.now) or c.now < 0 or not finite(c.maxHP) or c.maxHP <= 0 then return "BAD_NUMBER" end
 if not id(c.sessionId) or not id(c.roundId) or not id(c.casterId)
   or not id(c.targetId) or not id(c.casterAvatarId) or not id(c.targetAvatarId) then
  return "BAD_ID"
 end
 if c.casterId == c.targetId then return "SELF" end
 if c.active ~= true or c.currentCaster ~= true or c.currentTarget ~= true then return "STALE_MATCH" end
 if c.sameTeam ~= true or c.teamMode ~= "TEAM" then return "NOT_TEAMMATE" end
 if c.casterIsMage ~= true or c.casterAlive ~= true then return "NOT_LIVING_MAGE" end
 if c.inRange ~= true or c.lineClear ~= true then return "OUT_OF_REACH" end
 if c.casterInterrupted == true then return "INTERRUPTED" end
 return nil
end

-- Immediate, in-combat MAGE healing. Existing real MAGE/AI +25 heal is retained;
-- this defines a new candidate 30%-of-target-MaxHP, CD18s server rule.
function M.healDelta(c: any): (number, string)
 local bad = common(c)
 if bad then return 0, bad end
 if c.targetAlive ~= true or c.targetDowned == true then return 0, "TARGET_DOWNED" end
 if not finite(c.targetHP) or c.targetHP <= 0 or c.targetHP >= c.maxHP then return 0, "NO_MISSING_HP" end
 if not finite(c.lastHealAt) or c.lastHealAt > c.now then return 0, "BAD_CLOCK" end
 if c.now - c.lastHealAt < M.HEAL_COOLDOWN then return 0, "HEAL_COOLDOWN" end
 local amount = math.min(c.maxHP - c.targetHP, c.maxHP * M.HEAL_MAX_FRACTION)
 return amount, "HEAL_READY"
end

-- Begin a server-owned, non-yielding channel token. Host must store at most ONE
-- active attempt for a caster, deny a second start, and never expose token to clients.
function M.beginRevive(c: any): (any?, string)
 local bad = common(c)
 if bad then return nil, bad end
 if c.alreadyChanneling == true then return nil, "CHANNEL_BUSY" end
 if c.targetDowned ~= true or c.targetAlive == true or c.targetEliminated == true then
  return nil, "TARGET_NOT_DOWNED"
 end
 if not finite(c.downedAt) or c.downedAt > c.now or c.now - c.downedAt > M.DOWNED_WINDOW_SECONDS then
  return nil, "DOWNED_EXPIRED"
 end
 if not finite(c.lastReviveAt) or c.lastReviveAt > c.now then return nil, "BAD_CLOCK" end
 if c.now - c.lastReviveAt < M.REVIVE_COOLDOWN then return nil, "REVIVE_COOLDOWN" end
 return {
  sessionId=c.sessionId, roundId=c.roundId, casterId=c.casterId, targetId=c.targetId,
  casterAvatarId=c.casterAvatarId, targetAvatarId=c.targetAvatarId,
  startedAt=c.now, downedAt=c.downedAt, consumed=false
 }, "CHANNEL_STARTED"
end

-- Call after 3 seconds of continuous channel. Atomic consumption is done BEFORE
-- returning the HP amount; replay/cancel/race cannot yield a second revive.
-- Caller must apply damage/HP through its existing authoritative server Host.
function M.finishRevive(attempt: any, c: any): (number, string)
 if type(attempt) ~= "table" or attempt.consumed ~= false then return 0, "TOKEN_USED" end
 local bad = common(c)
 if bad then return 0, bad end
 if attempt.sessionId ~= c.sessionId or attempt.roundId ~= c.roundId
  or attempt.casterId ~= c.casterId or attempt.targetId ~= c.targetId
  or attempt.casterAvatarId ~= c.casterAvatarId or attempt.targetAvatarId ~= c.targetAvatarId then
  return 0, "TOKEN_STALE"
 end
 if not finite(attempt.startedAt) or attempt.startedAt > c.now then return 0, "TOKEN_CLOCK" end
 if c.now - attempt.startedAt < M.CHANNEL_SECONDS then return 0, "CHANNEL_EARLY" end
 if c.now - attempt.startedAt > M.CHANNEL_SECONDS + M.CHANNEL_GRACE_SECONDS then
  return 0, "CHANNEL_EXPIRED"
 end
 if not finite(c.downedAt) or attempt.downedAt ~= c.downedAt
  or c.now - c.downedAt > M.DOWNED_WINDOW_SECONDS then
  return 0, "DOWNED_EXPIRED"
 end
 if c.targetDowned ~= true or c.targetAlive == true or c.targetEliminated == true then
  return 0, "TARGET_NOT_DOWNED"
 end
 if not finite(c.lastReviveAt) or c.lastReviveAt > c.now
  or c.now - c.lastReviveAt < M.REVIVE_COOLDOWN then
  return 0, "REVIVE_COOLDOWN"
 end
 if c.casterHitSinceStart == true or c.casterInterrupted == true then return 0, "INTERRUPTED" end
 attempt.consumed = true
 return math.max(1, math.floor(c.maxHP * M.REVIVE_HP_FRACTION + 0.5)), "REVIVE_READY"
end

function M.cancelRevive(attempt: any): boolean
 if type(attempt) ~= "table" or attempt.consumed ~= false then return false end
 attempt.consumed = true
 return true
end

return M
