--!strict
-- #765 lane8: server-owned Mage rescue decision helper, NOT a second HP writer.
-- Caller must supply verified server session/character/team/LOS/health facts;
-- the existing Host/Combat alone writes Humanoid.Health and owns downed lifecycle.
local P = {}
P.HEAL_FRACTION = 0.30
P.HEAL_COOLDOWN_SECONDS = 18
P.REVIVE_FRACTION = 0.35
P.REVIVE_COOLDOWN_SECONDS = 40
P.REVIVE_CHANNEL_SECONDS = 3
P.DOWNED_WINDOW_SECONDS = 60
P.RANGE_STUDS = 22

local function finite(n: any): boolean
 return type(n) == "number" and n == n and n > -math.huge and n < math.huge
end

local function nonempty(s: any): boolean
 return (type(s) == "string" and #s > 0) or (type(s) == "number" and finite(s) and s > 0)
end

function P.newState(epoch: string): any
 assert(type(epoch) == "string" and #epoch > 0, "RED_INVALID_SESSION_EPOCH")
 return {epoch = epoch, pending = {}, busyCasters = {}, healingCooldown = {}, reviveCooldown = {}, nextTicket = 0}
end

local function common(state: any, ctx: any): (boolean, string)
 if type(state) ~= "table" or type(ctx) ~= "table" then return false, "BAD_CONTEXT" end
 if type(ctx.epoch) ~= "string" or ctx.epoch ~= state.epoch then return false, "STALE_SESSION" end
 if ctx.mode ~= "TEAM" and ctx.mode ~= "BR" then return false, "BAD_MODE" end
 if not finite(ctx.now) or ctx.now < 0 or not finite(ctx.distance)
   or ctx.distance < 0 or ctx.distance > P.RANGE_STUDS then
  return false, "INVALID_RANGE_TIME"
 end
 if ctx.casterRole ~= "MAGE" or ctx.casterActive ~= true or ctx.targetActive ~= true
   or ctx.casterAlive ~= true or ctx.casterCastleAlive ~= true or ctx.targetCastleAlive ~= true then
  return false, "INACTIVE_OR_WRONG_ROLE"
 end
 if not nonempty(ctx.casterId) or not nonempty(ctx.targetId)
   or not nonempty(ctx.casterCharacterKey) or not nonempty(ctx.targetCharacterKey) then
  return false, "BAD_IDENTITY"
 end
 if ctx.lineClear ~= true then return false, "BLOCKED_WALL" end
 if not finite(ctx.targetHP) or not finite(ctx.targetMaxHP) or ctx.targetMaxHP <= 0
   or ctx.targetHP < 0 or ctx.targetHP > ctx.targetMaxHP then
  return false, "BAD_HP"
 end
 if ctx.mode == "TEAM" then
  if not nonempty(ctx.casterTeam) or ctx.casterTeam ~= ctx.targetTeam then
   return false, "ENEMY_TEAM"
  end
 elseif ctx.casterId ~= ctx.targetId then
  return false, "BR_SELF_ONLY"
 end
 return true, "OK"
end

function P.heal(state: any, ctx: any): (number, string)
 local ok, why = common(state, ctx)
 if not ok then return 0, why end
 if ctx.targetDowned == true or ctx.targetHP <= 0 then return 0, "DOWNED_OR_DEAD" end
 if ctx.targetHP == ctx.targetMaxHP then return 0, "NO_WASTED_HEAL" end
 local caster = tostring(ctx.casterId)
 if ctx.now < (state.healingCooldown[caster] or 0) then return 0, "HEAL_COOLDOWN" end
 local amount = math.min(ctx.targetMaxHP - ctx.targetHP, ctx.targetMaxHP * P.HEAL_FRACTION)
 if amount <= 0 then return 0, "NO_WASTED_HEAL" end
 state.healingCooldown[caster] = ctx.now + P.HEAL_COOLDOWN_SECONDS
 return amount, "HEAL"
end

function P.beginRevive(state: any, ctx: any): (number?, string)
 local ok, why = common(state, ctx)
 if not ok then return nil, why end
 if ctx.mode ~= "TEAM" or ctx.casterId == ctx.targetId then return nil, "NO_SELF_REVIVE" end
 if ctx.targetDowned ~= true or ctx.targetHP <= 0 then return nil, "NOT_PROTECTED_DOWNED" end
 if not finite(ctx.downedAt) or ctx.downedAt > ctx.now
   or ctx.now - ctx.downedAt >= P.DOWNED_WINDOW_SECONDS then
  return nil, "DOWNED_WINDOW_EXPIRED"
 end
 local caster, target = tostring(ctx.casterId), tostring(ctx.targetId)
 if ctx.now < (state.reviveCooldown[caster] or 0) then return nil, "REVIVE_COOLDOWN" end
 if state.pending[target] ~= nil then return nil, "TARGET_ALREADY_RESERVED" end
 if state.busyCasters[caster] ~= nil then return nil, "CASTER_ALREADY_CHANNELING" end
 state.nextTicket += 1
 local ticket = state.nextTicket
 state.pending[target] = {
  ticket = ticket, epoch = ctx.epoch, caster = caster,
  casterCharacterKey = ctx.casterCharacterKey,
  targetCharacterKey = ctx.targetCharacterKey,
  startedAt = ctx.now, downedAt = ctx.downedAt,
 }
 state.busyCasters[caster] = ticket
 return ticket, "CHANNEL_STARTED"
end

function P.completeRevive(state: any, ctx: any, ticket: any): (number, string)
 local ok, why = common(state, ctx)
 if not ok then return 0, why end
 local target, caster = tostring(ctx.targetId), tostring(ctx.casterId)
 local record = state.pending[target]
 if type(record) ~= "table" or record.ticket ~= ticket then return 0, "NO_MATCHING_TICKET" end
 if record.epoch ~= ctx.epoch or record.caster ~= caster
   or record.casterCharacterKey ~= ctx.casterCharacterKey
   or record.targetCharacterKey ~= ctx.targetCharacterKey then
  return 0, "STALE_AVATAR_OR_CASTER"
 end
 if ctx.mode ~= "TEAM" or ctx.casterId == ctx.targetId
   or ctx.targetDowned ~= true or ctx.targetHP <= 0 then
  return 0, "NOT_PROTECTED_DOWNED"
 end
 if not finite(ctx.downedAt) or record.downedAt ~= ctx.downedAt
   or ctx.now - ctx.downedAt >= P.DOWNED_WINDOW_SECONDS then
  return 0, "DOWNED_WINDOW_EXPIRED"
 end
 if ctx.now < record.startedAt or ctx.now - record.startedAt < P.REVIVE_CHANNEL_SECONDS then
  return 0, "CHANNEL_INCOMPLETE"
 end
 if ctx.now < (state.reviveCooldown[caster] or 0) then
  return 0, "REVIVE_COOLDOWN"
 end
 -- A protected 1-HP downed Humanoid stays alive until the existing Host applies
 -- this target HP. At a real Humanoid.Health=0, resurrection is deliberately denied.
 local finalHP = math.min(ctx.targetMaxHP, math.max(1, ctx.targetMaxHP * P.REVIVE_FRACTION))
 state.pending[target] = nil
 state.busyCasters[caster] = nil
 state.reviveCooldown[caster] = ctx.now + P.REVIVE_COOLDOWN_SECONDS
 return finalHP, "REVIVE"
end

function P.cancelRevive(state: any, targetId: any, ticket: any): boolean
 if type(state) ~= "table" or not nonempty(targetId) then return false end
 local target = tostring(targetId)
 local record = state.pending[target]
 if not record or record.ticket ~= ticket then return false end
 state.pending[target] = nil
 if state.busyCasters[record.caster] == ticket then
  state.busyCasters[record.caster] = nil
 end
 return true
end

return P
