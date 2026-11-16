--!strict
-- GQ-ZOMBIE-COMMAND: server-side, deterministic orders; no Remote/HP/reward authority.
-- Pure policy is usable in native Luau. Only the existing combat author may apply hits.
local Policy = {}

local LIMIT = 3
local LIFETIME = 14
local MELEE_RANGE = 5
local ACQUIRE_RANGE = 48
local GUARD_LEASH = 12 -- castle-defense order must not attack while outside its local perimeter
local HIT_COOLDOWN = 1.5
local SQUAD_COOLDOWN = 0.4

local VALID = { FOLLOW = true, GUARD = true, FOCUS = true }
local ENEMY = { ENEMY_PLAYER = true, ENEMY_BOT = true, NEUTRAL = true }

local function distance(a, b)
    local dx, dz = a.x - b.x, a.z - b.z
    return math.sqrt(dx * dx + dz * dz)
end

local function eligible(target, matchToken)
    return target ~= nil
        and target.active == true
        and target.matchToken == matchToken
        and target.friendly ~= true
        and ENEMY[target.kind] == true
        and type(target.id) == "string"
        and type(target.x) == "number"
        and type(target.z) == "number"
end

function Policy.new(matchToken, ownerId, startedAt)
    assert(type(matchToken) == "string" and #matchToken > 0, "match token required")
    assert(type(ownerId) == "string" and #ownerId > 0, "owner id required")
    assert(type(startedAt) == "number", "server time required")
    return {
        matchToken = matchToken,
        ownerId = ownerId,
        startedAt = startedAt,
        active = true,
        order = "FOLLOW",
        focusId = nil,
        units = {},
        count = 0,
        lastSquadHit = -math.huge,
    }
end

function Policy.enlist(state, unitId, now, position)
    if not state.active or now - state.startedAt >= LIFETIME
        or state.count >= LIMIT or state.units[unitId] ~= nil then
        return false
    end
    if type(unitId) ~= "string" or #unitId == 0 then return false end
    state.units[unitId] = {
        x = position.x, z = position.z,
        lastHit = -math.huge,
        expiresAt = math.min(state.startedAt + LIFETIME, now + LIFETIME),
    }
    state.count += 1
    return true
end

function Policy.issue(state, order, focusId)
    if not state.active or not VALID[order] then return false end
    if order == "FOCUS" and (type(focusId) ~= "string" or focusId == "") then
        return false
    end
    state.order = order
    state.focusId = if order == "FOCUS" then focusId else nil
    return true
end

function Policy.retire(state)
    state.active = false
    state.units = {}
    state.count = 0
    state.focusId = nil
end

function Policy.locate(state, unitId, position)
    local unit = state.units[unitId]
    if not unit then return false end
    unit.x, unit.z = position.x, position.z
    return true
end

local function selectTarget(state, unit, snapshot)
    local best = nil
    local guardAnchor = if state.order == "GUARD" then (snapshot.guardPoint or snapshot.ownerPosition) else nil
    local bestDistance = ACQUIRE_RANGE
    for _, candidate in ipairs(snapshot.targets or {}) do
        if eligible(candidate, state.matchToken)
            and (state.order ~= "GUARD" or (guardAnchor ~= nil and distance(candidate, guardAnchor) <= GUARD_LEASH)) then
            local d = distance(unit, candidate)
            if d <= ACQUIRE_RANGE then
                if state.order == "FOCUS" then
                    if candidate.id == state.focusId then return candidate, d end
                elseif d < bestDistance then
                    best, bestDistance = candidate, d
                end
            end
        end
    end
    return best, bestDistance
end

-- snapshot is server-trusted only. Targets must be filtered for session/team/life.
-- Returns movement requests or ATTACK permits, never directly changes HP/rewards.
function Policy.step(state, now, snapshot)
    if not state.active then return {} end
    if snapshot.matchToken ~= state.matchToken or snapshot.phase ~= "ACTIVE"
        or snapshot.ownerAlive ~= true or snapshot.ownerId ~= state.ownerId
        or now >= state.startedAt + LIFETIME then
        Policy.retire(state)
        return {}
    end
    local actions = {}
    for unitId, unit in pairs(state.units) do
        if now >= unit.expiresAt then
            state.units[unitId] = nil
            state.count -= 1
            table.insert(actions, { kind = "DESPAWN", unitId = unitId })
        else
            -- Returning defenders never stall outside their castle chasing / hitting roadside enemies.
            local guardAnchor = if state.order == "GUARD" then (snapshot.guardPoint or snapshot.ownerPosition) else nil
            if guardAnchor and distance(unit, guardAnchor) > GUARD_LEASH then
                table.insert(actions, { kind = "MOVE", unitId = unitId,
                    x = guardAnchor.x, z = guardAnchor.z })
            else
            local target, d = selectTarget(state, unit, snapshot)
            if target and d <= MELEE_RANGE then
                local canSee = snapshot.visible ~= nil
                    and snapshot.visible(unit.x, unit.z, target.x, target.z) == true
                if canSee and now - unit.lastHit >= HIT_COOLDOWN
                    and now - state.lastSquadHit >= SQUAD_COOLDOWN then
                    unit.lastHit, state.lastSquadHit = now, now
                    table.insert(actions, {
                        kind = "ATTACK", unitId = unitId, targetId = target.id,
                        matchToken = state.matchToken, damage = 6,
                    })
                end
            else
                local waypoint = nil
                if state.order == "GUARD" then waypoint = guardAnchor
                elseif target then waypoint = { x = target.x, z = target.z }
                else waypoint = snapshot.ownerPosition end
                if waypoint then
                    table.insert(actions, {
                        kind = "MOVE", unitId = unitId,
                        x = waypoint.x, z = waypoint.z,
                    })
                end
            end
            end -- guard-return fence
        end
    end
    return actions
end

Policy.MAX_UNITS = LIMIT
Policy.TTL_SECONDS = LIFETIME
Policy.HIT_COOLDOWN_SECONDS = HIT_COOLDOWN
Policy.GUARD_LEASH_STUDS = GUARD_LEASH
return Policy
