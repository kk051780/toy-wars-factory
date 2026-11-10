-- TRAP RAIDERS v39-H1: PURE server-side, session-only reference module.
-- TRUST BOUNDARY: caller MUST be a privileged server MatchCoordinator.
-- Data fields and the "SERVER_FINALIZED_ROUND" tag DO NOT authenticate an event.
-- Never require this module from a LocalScript or feed it RemoteEvent payloads.
local Stamp = {}

local MAX_FINALIZED_ROUNDS = 512
local JOBS = {
    WARRIOR = true, NINJA = true, TRAPPER = true,
    ZOMBIE_MASTER = true, BEAST_TAMER = true, MAGE = true, BUILDER = true,
}
local STAGES = { S1 = true, S2 = true, S3 = true, S4 = true }

local function finiteNumber(value)
    return type(value) == "number" and value == value
        and value ~= math.huge and value ~= -math.huge
end

local function integer(value, low, high)
    return finiteNumber(value) and value % 1 == 0
        and value >= low and value <= high
end

local function validMatchId(value)
    -- Opaque server-generated identifiers. This is format validation, NOT authentication.
    return type(value) == "string" and #value >= 4 and #value <= 128
        and not string.find(value, "^%s") and not string.find(value, "%s$")
end

local function copyLedger(ledger)
    local nextLedger = {}
    for matchId, award in pairs(ledger) do
        nextLedger[matchId] = award
    end
    return nextLedger
end

local function validState(state)
    if type(state) ~= "table"
        or not integer(state.ownerUserId, 1, 9007199254740991)
        or not integer(state.stamps, 0, 1024)
        or not integer(state.finalizedCount, 0, MAX_FINALIZED_ROUNDS)
        or type(state.ledger) ~= "table"
        or state.sessionOnly ~= true then
        return false
    end
    -- Only consider the exact server-owned state object from newState/apply.
    -- A client-provided table MUST NOT be used as state.
    local count = 0
    local total = 0
    for matchId, award in pairs(state.ledger) do
        if not validMatchId(matchId) or not integer(award, 0, 2) then
            return false
        end
        count += 1
        total += award
        if count > MAX_FINALIZED_ROUNDS then return false end
    end
    return count == state.finalizedCount and total == state.stamps
end

local function validEvidence(ev, ownerUserId)
    if type(ev) ~= "table" or ev.kind ~= "SERVER_FINALIZED_ROUND"
        or not validMatchId(ev.matchId)
        or ev.userId ~= ownerUserId
        or not STAGES[ev.stageId]
        or not JOBS[ev.jobId]
        or ev.completed ~= true
        or type(ev.won) ~= "boolean"
        or type(ev.contributed) ~= "boolean"
        or not finiteNumber(ev.roundSeconds)
        or not finiteNumber(ev.activeSeconds)
        or ev.roundSeconds < 1 or ev.roundSeconds > 7200
        or ev.activeSeconds < 0 or ev.activeSeconds > ev.roundSeconds
        or not integer(ev.meaningfulServerActions, 0, 2048) then
        return false
    end
    return true
end

local function newUnlocks(beforeCount, afterCount)
    local unlocked = {}
    if beforeCount < 3 and afterCount >= 3 then
        table.insert(unlocked, "FREE_EGG_BANNER")
    end
    if beforeCount < 6 and afterCount >= 6 then
        table.insert(unlocked, "FREE_TRAP_TRAIL")
    end
    return unlocked
end

function Stamp.newState(ownerUserId)
    if not integer(ownerUserId, 1, 9007199254740991) then
        return nil, "INVALID_OWNER"
    end
    return {
        ownerUserId = ownerUserId,
        stamps = 0,
        finalizedCount = 0,
        ledger = {},
        sessionOnly = true,
    }
end

function Stamp.apply(state, evidence)
    if not validState(state) then
        return state, { status = "INVALID_STATE", awarded = 0, unlocks = {} }
    end
    if not validEvidence(evidence, state.ownerUserId) then
        return state, { status = "INVALID_EVIDENCE", awarded = 0, unlocks = {} }
    end
    if state.ledger[evidence.matchId] ~= nil then
        return state, { status = "DUPLICATE_FINALIZATION", awarded = 0, unlocks = {} }
    end
    if state.finalizedCount >= MAX_FINALIZED_ROUNDS then
        return state, { status = "LEDGER_FULL", awarded = 0, unlocks = {} }
    end
    local requiredActive = math.min(15, math.max(1, evidence.roundSeconds * 0.3))
    local eligible = evidence.activeSeconds >= requiredActive
        and evidence.meaningfulServerActions > 0
    local awarded = 0
    if eligible then
        awarded = 1
        if evidence.won or evidence.contributed then
            awarded += 1
        end
    end
    if state.stamps + awarded > 1024 then
        return state, { status = "STAMP_CAP_REACHED", awarded = 0, unlocks = {} }
    end
    local nextLedger = copyLedger(state.ledger)
    -- Mark both rewarded and legitimately zero-award rounds as finalized.
    nextLedger[evidence.matchId] = awarded
    local nextState = {
        ownerUserId = state.ownerUserId,
        stamps = state.stamps + awarded,
        finalizedCount = state.finalizedCount + 1,
        ledger = nextLedger,
        sessionOnly = true,
    }
    return nextState, {
        status = eligible and "AWARDED_SESSION_ONLY" or "INELIGIBLE_FINALIZED",
        awarded = awarded,
        unlocks = newUnlocks(state.stamps, nextState.stamps),
    }
end

function Stamp.view(state)
    if not validState(state) then return nil, "INVALID_STATE" end
    local nextAt = nil
    if state.stamps < 3 then nextAt = 3
    elseif state.stamps < 6 then nextAt = 6 end
    local unlocked = {}
    if state.stamps >= 3 then table.insert(unlocked, "FREE_EGG_BANNER") end
    if state.stamps >= 6 then table.insert(unlocked, "FREE_TRAP_TRAIL") end
    return {
        stamps = state.stamps,
        nextRewardAt = nextAt,
        toNextReward = nextAt and nextAt - state.stamps or 0,
        unlockedCosmetics = unlocked,
        sessionOnly = true,
        saved = false,
    }
end

return Stamp
