-- P0D-LOBBY-TRAINING-001 / V4 focus-cap scheduler
-- Pure, server-side policy. NO XP write, Remote, DataStore, receipt or purchase handling.
-- Caller MUST supply authoritative server Unix seconds, verified same-server friend count,
-- training active boolean, and a server-authorized premium flag (disabled at MVP).
local Scheduler = {}

Scheduler.DISCIPLINES = { "BEAST", "MAGIC", "WEAPON", "ZOMBIE", "VEHICLE", "BUILDING" }
Scheduler.FREE_FOCUS_SECONDS = 30 * 60
Scheduler.RANDOM_SLOT_SECONDS = 10 * 60
Scheduler.MAX_SETTLE_SECONDS = 120
Scheduler.BASE_XP_PER_SECOND = 10 -- balancing reference only; NOT credited by this module
Scheduler.MAX_FRIENDS = 4
Scheduler.FRIEND_BONUS_PERCENT = 25

local SEC_PER_DAY = 86400
local JST_OFFSET = 9 * 3600
local MODULUS = 2147483647
local MAX_USER_ID = 999999999999 -- avoid large multiplications in deterministic PRNG

local function int(value, default)
    if type(value) ~= "number" or value ~= value or value == math.huge or value == -math.huge then
        return default
    end
    return math.floor(value)
end

local function dayIndex(unixSeconds)
    return math.floor((unixSeconds + JST_OFFSET) / SEC_PER_DAY)
end

local function nextJstMidnight(unixSeconds)
    return (dayIndex(unixSeconds) + 1) * SEC_PER_DAY - JST_OFFSET
end

local function clamp(value, low, high)
    return math.min(high, math.max(low, value))
end

local function isSkill(candidate)
    for _, skill in ipairs(Scheduler.DISCIPLINES) do
        if candidate == skill then
            return true
        end
    end
    return false
end

local function plainShuffle(userId, cycle)
    -- Stable per-user/cycle shuffle bag (not crypto/security, not paid random reward).
    local seed = (((userId % 100000000) + 1) * 16807 + (cycle % 1000000) * 101390) % MODULUS
    if seed == 0 then seed = 1 end
    local bag = table.clone(Scheduler.DISCIPLINES)
    for i = #bag, 2, -1 do
        seed = (seed * 48271) % MODULUS
        local index = (seed % i) + 1
        bag[i], bag[index] = bag[index], bag[i]
    end
    return bag
end

local function selectedRandomSkill(userId, cycle, position)
    local bag = plainShuffle(userId, cycle)
    if cycle > 0 then
        local previous = plainShuffle(userId, cycle - 1)
        -- Avoid adjacent duplicate across shuffle-bag boundaries.
        -- A swap among 1,2 leaves bag[6] unchanged for subsequent cycles.
        if bag[1] == previous[6] then
            bag[1], bag[2] = bag[2], bag[1]
        end
    end
    return bag[position]
end

local function copyState(source)
    local result = {}
    for key, value in pairs(source) do
        result[key] = value
    end
    return result
end

function Scheduler.newState(userId, now, persisted)
    assert(type(userId) == "number" and userId >= 1 and userId <= MAX_USER_ID and userId == math.floor(userId), "userId")
    now = int(now, nil)
    assert(now ~= nil, "server time")
    persisted = type(persisted) == "table" and persisted or {}
    local day = dayIndex(now)
    local previousDay = int(persisted.dayIndex, day)
    local state = {
        userId = userId,
        dayIndex = day,
        focusedSeconds = previousDay == day and clamp(int(persisted.focusedSeconds, 0), 0, Scheduler.FREE_FOCUS_SECONDS) or 0,
        selectedSkill = isSkill(persisted.selectedSkill) and persisted.selectedSkill or nil,
        randomCycle = clamp(int(persisted.randomCycle, 0), 0, 1000000),
        randomPosition = clamp(int(persisted.randomPosition, 1), 1, 6),
        randomRemaining = clamp(int(persisted.randomRemaining, Scheduler.RANDOM_SLOT_SECONDS), 1, Scheduler.RANDOM_SLOT_SECONDS),
        lastTick = now, -- important: never accrue offline time on rejoin
    }
    return state
end

function Scheduler.selectSkill(state, selectedSkill)
    assert(isSkill(selectedSkill), "invalid selectedSkill")
    local new = copyState(state)
    new.selectedSkill = selectedSkill
    return new
end

function Scheduler.clearSelection(state)
    local new = copyState(state)
    new.selectedSkill = nil
    return new
end

function Scheduler.getStatus(state, unlimitedFocus)
    local canFocus = state.selectedSkill ~= nil and (unlimitedFocus == true or state.focusedSeconds < Scheduler.FREE_FOCUS_SECONDS)
    return {
        mode = canFocus and "FOCUS" or "RANDOM",
        skill = canFocus and state.selectedSkill or selectedRandomSkill(state.userId, state.randomCycle, state.randomPosition),
        freeRemaining = math.max(0, Scheduler.FREE_FOCUS_SECONDS - state.focusedSeconds),
        untilRandomSwitch = state.randomRemaining,
        nextFreeReset = (state.dayIndex + 1) * SEC_PER_DAY - JST_OFFSET,
    }
end

local function mergeSegment(segments, skill, seconds, bonusBps, mode)
    if seconds <= 0 then return end
    local last = segments[#segments]
    if last and last.skill == skill and last.bonusBps == bonusBps and last.mode == mode then
        last.seconds = last.seconds + seconds
    else
        table.insert(segments, {skill = skill, seconds = seconds, bonusBps = bonusBps, mode = mode})
    end
end

function Scheduler.settle(state, now, isTraining, verifiedFriends, unlimitedFocus)
    now = int(now, nil)
    assert(now ~= nil, "server time")
    local nextState = copyState(state)
    local currentDay = dayIndex(now)
    local last = int(state.lastTick, now)
    -- Protection against clock rollback and duplicate settlement on same timestamp.
    if now <= last then return nextState, {} end
    -- Cap long server ticks, never grant earnings for an offline / stalled interval.
    local start = math.max(last, now - Scheduler.MAX_SETTLE_SECONDS)
    nextState.lastTick = now
    -- Day rollover even when not training.
    if nextState.dayIndex ~= currentDay and not isTraining then
        nextState.dayIndex = currentDay
        nextState.focusedSeconds = 0
    end
    if not isTraining then return nextState, {} end

    verifiedFriends = clamp(int(verifiedFriends, 0), 0, Scheduler.MAX_FRIENDS)
    local bonusBps = 10000 + verifiedFriends * Scheduler.FRIEND_BONUS_PERCENT * 100
    local segments = {}
    local cursor = start
    local iterations = 0
    while cursor < now do
        iterations = iterations + 1
        assert(iterations <= 50, "unexpected segment loop")
        local bucket = dayIndex(cursor)
        if nextState.dayIndex ~= bucket then
            nextState.dayIndex = bucket
            nextState.focusedSeconds = 0
        end
        local available = math.min(now - cursor, nextJstMidnight(cursor) - cursor)
        local focusAvailable = Scheduler.FREE_FOCUS_SECONDS - nextState.focusedSeconds
        local doFocus = nextState.selectedSkill ~= nil and (unlimitedFocus == true or focusAvailable > 0)
        if doFocus then
            local runSeconds = unlimitedFocus == true and available or math.min(available, focusAvailable)
            mergeSegment(segments, nextState.selectedSkill, runSeconds, bonusBps, "FOCUS")
            if unlimitedFocus ~= true then
                nextState.focusedSeconds = nextState.focusedSeconds + runSeconds
            end
            cursor = cursor + runSeconds
        else
            local runSeconds = math.min(available, nextState.randomRemaining)
            mergeSegment(segments, selectedRandomSkill(nextState.userId, nextState.randomCycle, nextState.randomPosition), runSeconds, bonusBps, "RANDOM")
            nextState.randomRemaining = nextState.randomRemaining - runSeconds
            cursor = cursor + runSeconds
            if nextState.randomRemaining == 0 then
                nextState.randomPosition = nextState.randomPosition + 1
                if nextState.randomPosition > 6 then
                    nextState.randomPosition = 1
                    nextState.randomCycle = nextState.randomCycle + 1
                end
                nextState.randomRemaining = Scheduler.RANDOM_SLOT_SECONDS
            end
        end
    end
    if nextState.dayIndex ~= currentDay then
        nextState.dayIndex = currentDay
        nextState.focusedSeconds = 0
    end
    return nextState, segments
end

function Scheduler.snapshot(state)
    -- Persist only via the existing single-authority user profile, never independently.
    return {
        version = 1,
        dayIndex = state.dayIndex,
        focusedSeconds = state.focusedSeconds,
        selectedSkill = state.selectedSkill,
        randomCycle = state.randomCycle,
        randomPosition = state.randomPosition,
        randomRemaining = state.randomRemaining,
    }
end

return Scheduler
