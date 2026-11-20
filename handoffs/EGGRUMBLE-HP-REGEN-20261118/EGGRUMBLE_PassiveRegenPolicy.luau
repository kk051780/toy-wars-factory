--!strict
-- BATTLE-HP-REGEN / #765 lane 7. Pure policy: NO Humanoid writes, remotes, loops or authority.
-- Only the existing server Combat/Host/Game health owner may consume this policy.
local M = {}
M.FEATURE_ID = "BATTLE-HP-REGEN"
M.ROLE_MAX_HP = {
 WARRIOR = 250, MAGE = 195, NINJA = 185, TRAPPER = 205,
 BUILDER = 225, BEAST = 220, ZOMBIE = 230,
}
M.REGEN_DELAY = 7
M.REGEN_FRACTION_PER_SECOND = 0.007
M.MAX_STEP_SECONDS = 0.25

local function finite(v: any): boolean
 return type(v) == "number" and v == v and v < math.huge and v > -math.huge
end

-- Unknown/untrusted role input must never produce a fallback elite health pool.
function M.initialMaxHP(role: any): number?
 if type(role) ~= "string" then return nil end
 return M.ROLE_MAX_HP[role]
end

-- Call from an existing SERVER Humanoid.HealthChanged observer with the same character.
-- Timestamp only real HP loss. A heal or failed/absorbed attack cannot delay regeneration.
-- A DOT tick is real loss and therefore resets the timer.
function M.observeHealth(previousHP: any, nextHP: any, now: any, lastDamageAt: any): (number?, boolean)
 if not finite(now) or now < 0 or not finite(previousHP) or not finite(nextHP)
  or not finite(lastDamageAt) then
  return lastDamageAt, false
 end
 if previousHP > nextHP and previousHP > 0 and nextHP >= 0 then
  return now, true
 end
 return lastDamageAt, false
end

-- Caller supplies truth from the existing authoritative current-session/character checks.
-- This is only the permitted positive HP DELTA; the caller alone applies it on the server.
-- No catch-up after a lag spike and never resurrect a downed/dead player.
function M.regenDelta(health: any, maxHP: any, now: any, lastDamageAt: any,
 deltaSeconds: any, matchActive: any, currentSessionAvatar: any,
 dotActive: any, downed: any): (number, string)
 if not finite(health) or not finite(maxHP) or not finite(now)
  or not finite(lastDamageAt) or not finite(deltaSeconds) then
  return 0, "BAD_NUMBER"
 end
 if maxHP <= 0 or health < 0 or now < 0 or lastDamageAt < 0 or now < lastDamageAt then
  return 0, "BAD_STATE"
 end
 if matchActive ~= true or currentSessionAvatar ~= true then
  return 0, "NOT_CURRENT_MATCH"
 end
 if downed == true or health <= 0 then
  return 0, "DEAD_OR_DOWNED"
 end
 if dotActive == true then
  return 0, "DOT_ACTIVE"
 end
 if now - lastDamageAt < M.REGEN_DELAY then
  return 0, "RECENT_DAMAGE"
 end
 if deltaSeconds <= 0 then
  return 0, "NO_STEP"
 end
 if health >= maxHP then
  return 0, "FULL"
 end
 local safeStep = math.min(deltaSeconds, M.MAX_STEP_SECONDS)
 local delta = math.min(maxHP - health, maxHP * M.REGEN_FRACTION_PER_SECOND * safeStep)
 return delta, "REGEN"
end

return M
