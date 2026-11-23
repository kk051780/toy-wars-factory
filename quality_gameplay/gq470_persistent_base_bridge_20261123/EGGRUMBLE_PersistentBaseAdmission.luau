--!strict
-- Unattached, server-only read preparation. The authoritative Host supplies
-- genuine-Studio/current-Player eligibility and ACTIVE round membership.
-- These trusted callbacks MUST be synchronous and non-yielding.
-- This module never obtains a DataStore, writes, retries, starts tasks or joins
-- the current runtime. Only read() may yield, through the unchanged donor load.
local Store = require(script.Parent:WaitForChild("PersistentHatchStore"))
local Admission = {}
local MAX_USER_ID = 999999999999999
local MAX_REVISION = 9007199254740991

local function integer(value: any, maximum: number): boolean
    return type(value) == "number" and value == value and value >= 0
        and value <= maximum and value == math.floor(value)
end

local function snapshot(raw: any, profile: any, uid: number)
    if type(raw) ~= "table" or type(profile) ~= "table"
        or not integer(raw.revision, MAX_REVISION)
        or not integer(profile.level, 50) or profile.level < 1
        or not integer(profile.xp, MAX_REVISION)
        or type(raw.equipped) ~= "string" or type(profile.mastery) ~= "table" then
        return nil
    end
    local mastery = {}
    for item, value in pairs(profile.mastery) do
        if type(item) ~= "string" or type(value) ~= "table"
            or not integer(value.level, 10) or value.level < 1
            or not integer(value.xp, MAX_REVISION) then return nil end
        mastery[item] = table.freeze({level = value.level, xp = value.xp})
    end
    return table.freeze({userId = uid, revision = raw.revision,
        level = profile.level, xp = profile.xp, equipped = raw.equipped,
        mastery = table.freeze(mastery)})
end

local function copySnapshot(value: any)
    local mastery = {}
    for item, row in pairs(value.mastery) do
        mastery[item] = table.freeze({level = row.level, xp = row.xp})
    end
    return table.freeze({userId = value.userId, revision = value.revision,
        level = value.level, xp = value.xp, equipped = value.equipped,
        mastery = table.freeze(mastery)})
end

local function equalSnapshot(a: any, b: any): boolean
    if a.userId ~= b.userId or a.revision ~= b.revision or a.level ~= b.level
        or a.xp ~= b.xp or a.equipped ~= b.equipped then return false end
    for item, row in pairs(a.mastery) do
        local other = b.mastery[item]
        if other == nil or other.level ~= row.level or other.xp ~= row.xp then return false end
    end
    for item in pairs(b.mastery) do
        if a.mastery[item] == nil then return false end
    end
    return true
end

function Admission.new(input: any)
    if type(input) ~= "table" or input.store == nil or input.store == false
        or type(input.eligible) ~= "function" or type(input.member) ~= "function" then
        return nil, "INVALID_ARGUMENT"
    end
    local store, options = input.store, input.readOptions
    local eligible, member = input.eligible, input.member
    local byAccount, byPlayer = {}, {}
    local api = {}

    local function current(record: any): boolean
        -- Capture only the clearable record, never a separate Player reference.
        local ok, yes = pcall(function()
            return record.player ~= nil and typeof(record.player) == "Instance"
                and record.player:IsA("Player") and record.player.UserId == record.uid
                and eligible(record.player, record.uid) == true
        end)
        return ok and yes == true
    end

    local function account(token: any, checkEligibility: boolean)
        if type(token) ~= "table" then return nil, "INVALID_ARGUMENT" end
        local record = byAccount[token]
        if record == nil then return nil, "STALE_ACCOUNT" end
        if checkEligibility and not current(record) then return nil, "INELIGIBLE" end
        return record, "OK"
    end

    local function membership(record: any, round: any): boolean
        local ok, yes = pcall(member, record.player, round)
        return ok and yes == true
    end

    function api:bind(player: any)
        local ok, uid = pcall(function()
            if typeof(player) ~= "Instance" or not player:IsA("Player") then return nil end
            return player.UserId
        end)
        if not ok or not integer(uid, MAX_USER_ID) or uid < 1 then
            return nil, "INVALID_ARGUMENT"
        end
        local present = byPlayer[player]
        if present ~= nil then
            if present.uid ~= uid or not current(present) then return nil, "INELIGIBLE" end
            return present.token, "OK"
        end
        local record = {player = player, uid = uid, inFlight = 0, state = "NOT_LOADED"}
        if not current(record) then return nil, "INELIGIBLE" end
        local token = table.freeze({})
        record.token = token
        byPlayer[player], byAccount[token] = record, record
        return token, "OK"
    end

    function api:read(token: any)
        local record, code = account(token, true)
        if record == nil then return nil, code end
        if record.inFlight >= 2 then return nil, "READ_BUSY" end
        local ticket = {}
        local uid = record.uid
        record.inFlight += 1
        record.generation, record.state = ticket, "READ_PENDING"
        -- No Player or old profile is held separately across this yield.
        -- pcall success and the donor's load success are distinct booleans.
        local called, loaded, raw, loadCode = pcall(Store.load, store, uid, options)
        -- Exactly one return to THIS account's accounting, even after remove.
        -- Never resolve the current account by UserId or reset this cell on remove.
        record.inFlight -= 1
        if byAccount[token] ~= record or record.generation ~= ticket then
            return nil, "STALE_READ"
        end
        if not current(record) then
            record.state = "INELIGIBLE"
            return nil, record.state
        end
        if not called then
            record.state = "DONOR_ERROR"
            return nil, record.state
        end
        if loaded ~= true then
            local known = loadCode == "INVALID_STORE_OR_PLAYER" or loadCode == "READ_FAILED"
                or loadCode == "CORRUPT_RECORD"
            record.state = if known then loadCode else "DONOR_ERROR"
            return nil, record.state
        end
        local projected, value = pcall(function()
            return snapshot(raw, Store.toProgressProfile(raw, uid), uid)
        end)
        if not projected then
            record.state = "DONOR_ERROR"
            return nil, record.state
        end
        if value == nil then
            record.state = "INVALID_PROFILE"
            return nil, record.state
        end
        local previous = record.confirmed
        if previous ~= nil and value.revision < previous.revision then
            record.state = "REVISION_REGRESSION"
            return nil, record.state
        end
        if previous ~= nil and value.revision == previous.revision
            and not equalSnapshot(value, previous) then
            record.state = "REVISION_CONFLICT"
            return nil, record.state
        end
        record.confirmed, record.state = value, "OK"
        return value, "OK"
    end

    function api:peek(token: any)
        local record, code = account(token, true)
        if record == nil then return nil, code end
        if record.state ~= "OK" then return nil, record.state end
        return record.confirmed, "OK"
    end

    function api:admit(token: any, round: any, admission: any)
        local record, code = account(token, true)
        if record == nil then return nil, code end
        if type(round) ~= "table" or type(admission) ~= "table" then return nil, "INVALID_ARGUMENT" end
        if not membership(record, round) then return nil, "STALE_ADMISSION" end
        local active = record.admission
        if active ~= nil then
            if active.round == round and active.token == admission then return active.snapshot, "OK" end
            return nil, "ADMISSION_CONFLICT"
        end
        if record.state ~= "OK" then return nil, record.state end
        local value = copySnapshot(record.confirmed)
        record.admission = {round = round, token = admission, snapshot = value}
        return value, "OK"
    end

    function api:get(token: any, round: any, admission: any)
        local record, code = account(token, true)
        if record == nil then return nil, code end
        if type(round) ~= "table" or type(admission) ~= "table" then return nil, "INVALID_ARGUMENT" end
        local active = record.admission
        if active == nil or active.round ~= round or active.token ~= admission
            or not membership(record, round) then return nil, "STALE_ADMISSION" end
        return active.snapshot, "OK"
    end

    function api:endAdmission(token: any, round: any, admission: any)
        local record, code = account(token, false)
        if record == nil then return false, code end
        if type(round) ~= "table" or type(admission) ~= "table" then return false, "INVALID_ARGUMENT" end
        local active = record.admission
        if active == nil or active.round ~= round or active.token ~= admission then
            return false, "STALE_ADMISSION"
        end
        record.admission = nil
        return true, "OK"
    end

    function api:remove(token: any)
        local record, code = account(token, false)
        if record == nil then return false, code end
        byPlayer[record.player], byAccount[token] = nil, nil
        -- In-flight reads retain only this scrubbed account and their own UID/ticket.
        record.player, record.uid, record.token = nil, nil, nil
        record.confirmed, record.admission, record.generation = nil, nil, nil
        record.state = "STALE_ACCOUNT"
        return true, "OK"
    end

    return table.freeze(api), "OK"
end

return table.freeze(Admission)
