-- TRAP RAIDERS D16: independent no-key reference, not the original AES sealed ZIP.
-- Pure server-only cosmetic event state. This ModuleScript never writes Roblox Instances.
-- Call begin() ONLY from an audited server-owned D08 canonical event callback.
local Core = {}

local MAX_SEEN_ROUNDS = 128
local TTL_MS = 8000
local SCALES = { GIANT_ONE = 1.6, MINI_ALL = 0.7 }

local function finiteNumber(v)
    return type(v) == "number" and v == v and v ~= math.huge and v ~= -math.huge
end

local function validId(v)
    return type(v) == "string" and #v >= 1 and #v <= 96 and not string.find(v, "[%c]")
end

local function validEpoch(v)
    return finiteNumber(v) and v >= 1 and v <= 2147483647 and v % 1 == 0
end

local function validUserId(v)
    return finiteNumber(v) and v >= 1 and v <= 9007199254740991 and v % 1 == 0
end

local function normalizeRoster(roster)
    if type(roster) ~= "table" then return nil end
    local count = #roster
    if count < 1 or count > 24 then return nil end
    local found = {}
    local users = {}
    for i = 1, count do
        local id = roster[i]
        if not validUserId(id) or found[id] then return nil end
        found[id] = true
        users[i] = id
    end
    for k in pairs(roster) do
        if type(k) ~= "number" or k % 1 ~= 0 or k < 1 or k > count then
            return nil
        end
    end
    table.sort(users)
    return users, found
end

function Core.new()
    return { active = nil, seen = {}, seenCount = 0, newestEpoch = 0, lastNowMs = nil }
end

function Core.begin(state, args)
    if type(state) ~= "table" or type(state.seen) ~= "table" or type(args) ~= "table" then
        return false, "INVALID_INPUT"
    end
    if not validId(args.matchId) or not validId(args.eventId) or not validEpoch(args.epoch) then
        return false, "INVALID_ID"
    end
    if not finiteNumber(args.nowMs) or args.nowMs < 0 or args.nowMs > 100000000000000 then
        return false, "INVALID_CLOCK"
    end
    local effect = args.effect
    local scale = SCALES[effect]
    if scale == nil then return false, "INVALID_EFFECT" end
    local users, present = normalizeRoster(args.serverRoster)
    if not users then return false, "INVALID_ROSTER" end
    if effect == "GIANT_ONE" and not validUserId(args.targetUserId) then
        return false, "INVALID_TARGET"
    end
    if effect == "GIANT_ONE" and not present[args.targetUserId] then
        return false, "TARGET_NOT_IN_ROSTER"
    end
    if effect == "MINI_ALL" and args.targetUserId ~= nil then
        return false, "UNEXPECTED_TARGET"
    end
    if args.epoch < state.newestEpoch then return false, "STALE_EPOCH" end
    if state.lastNowMs ~= nil and args.nowMs < state.lastNowMs then
        return false, "CLOCK_BACKWARDS"
    end
    local roundKey = args.matchId .. ":" .. tostring(args.epoch)
    if state.seen[roundKey] or state.active ~= nil then
        return false, "DUPLICATE_OR_ACTIVE"
    end
    if state.seenCount >= MAX_SEEN_ROUNDS then
        return false, "ANTI_REPLAY_CAPACITY"
    end
    local selected = {}
    if effect == "GIANT_ONE" then
        selected[1] = args.targetUserId
    else
        selected = users
    end
    state.seen[roundKey] = true
    state.seenCount = state.seenCount + 1
    state.newestEpoch = math.max(state.newestEpoch, args.epoch)
    state.lastNowMs = args.nowMs
    state.active = {
        matchId = args.matchId, epoch = args.epoch, eventId = args.eventId,
        effect = effect, scale = scale, startedAtMs = args.nowMs,
        expiresAtMs = args.nowMs + TTL_MS, users = selected,
    }
    return true, "STARTED"
end

local function copySnapshot(active)
    local users = {}
    for i, id in ipairs(active.users) do users[i] = id end
    return {
        matchId = active.matchId, epoch = active.epoch,
        eventId = active.eventId, effect = active.effect, visualScale = active.scale,
        startedAtMs = active.startedAtMs, expiresAtMs = active.expiresAtMs,
        userIds = users,
    }
end

function Core.snapshot(state, nowMs, matchId, epoch)
    if type(state) ~= "table" or not finiteNumber(nowMs) or nowMs < 0 then
        return nil, "INVALID_CLOCK_OR_STATE"
    end
    if state.lastNowMs ~= nil and nowMs < state.lastNowMs then
        return nil, "CLOCK_BACKWARDS"
    end
    state.lastNowMs = nowMs
    local a = state.active
    if a == nil then return nil, "INACTIVE" end
    if matchId ~= a.matchId or epoch ~= a.epoch or nowMs >= a.expiresAtMs then
        state.active = nil
        return nil, "CLOSED_OR_EXPIRED"
    end
    return copySnapshot(a), "ACTIVE"
end

function Core.close(state, matchId, epoch, nowMs)
    if type(state) ~= "table" or not finiteNumber(nowMs) or nowMs < 0 then
        return false, "INVALID_CLOCK_OR_STATE"
    end
    if state.lastNowMs ~= nil and nowMs < state.lastNowMs then
        return false, "CLOCK_BACKWARDS"
    end
    state.lastNowMs = nowMs
    local a = state.active
    if a == nil or matchId ~= a.matchId or epoch ~= a.epoch then
        return false, "NOT_ACTIVE_MATCH"
    end
    state.active = nil
    return true, "CLOSED"
end

return Core
