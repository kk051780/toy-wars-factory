--!strict
-- P0D S1 - purely presentational route selection for existing server SNAPSHOT.
-- Does not own positions, objectives, egg state, scores, rounds or remotes.
local Route = {}

export type Target = {
    serial: number,
    phase: string,
    team: string,
    kind: string,
    folderName: string?,
    partName: string?,
    label: string,
}

local VALID_PHASES = {LOBBY = true, COUNTDOWN = true, ACTIVE = true, RESULTS = true}
local VALID_TEAMS = {RED = true, BLUE = true, NONE = true}
local VALID_CARRIED = {RED = true, BLUE = true, [""] = true}

local function validSerial(value: any): boolean
    return type(value) == "number" and value == value
        and value % 1 == 0 and value >= 0 and value <= 1000000000
end

local function empty(serial: number, phase: string, team: string): Target
    return {serial = serial, phase = phase, team = team, kind = "NONE", label = ""}
end

-- Returns nil on malformed/stale packet; returns NONE on valid non-active phase.
-- This function never grants authorization or modifies the authoritative state.
function Route.resolve(snapshot: any, lastSerial: number): Target?
    if type(snapshot) ~= "table" or snapshot.kind ~= "SNAPSHOT" then return nil end
    if not validSerial(snapshot.serial) or snapshot.serial < lastSerial then return nil end
    if not VALID_PHASES[snapshot.phase] or not VALID_TEAMS[snapshot.team] then return nil end
    if type(snapshot.carrying) ~= "string" or not VALID_CARRIED[snapshot.carrying] then return nil end

    local serial: number = snapshot.serial
    local phase: string = snapshot.phase
    local team: string = snapshot.team
    if phase ~= "ACTIVE" then
        return empty(serial, phase, team)
    end
    if team ~= "RED" and team ~= "BLUE" then return nil end

    local enemy: string = if team == "RED" then "BLUE" else "RED"
    if snapshot.carrying == enemy then
        return {
            serial = serial, phase = phase, team = team,
            kind = "HOME_PAD", folderName = team .. "_CASTLE",
            partName = team .. "_SCORE_PAD", label = "自分の納品台へ！",
        }
    end
    if snapshot.carrying == "" then
        return {
            serial = serial, phase = phase, team = team,
            kind = "ENEMY_EGG", folderName = enemy .. "_CASTLE",
            partName = enemy .. "_EGG", label = "敵の卵を取ろう！",
        }
    end
    -- An impossible client observation (carrying one's own egg) is not a route.
    return nil
end

return Route
