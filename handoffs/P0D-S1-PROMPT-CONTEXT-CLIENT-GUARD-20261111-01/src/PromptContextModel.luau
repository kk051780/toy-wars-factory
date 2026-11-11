--!strict
-- TRAP RAIDERS S1: pure per-client prompt APPEARANCE decision. Never authorizes actions.
-- Server-side Rules.canSteal/canScore and ProximityPrompt.Enabled remain authoritative.
local PromptPolicy = {}

export type State = {
    serial: number,
    phase: string,
    team: string,
    carrying: string,
    valid: boolean,
}

local function teamIsValid(team: any): boolean
    return team == "RED" or team == "BLUE"
end

local function serialIsValid(serial: any): boolean
    return type(serial) == "number" and serial == serial and serial % 1 == 0
        and serial >= 0 and serial <= 1000000000
end

function PromptPolicy.new(): State
    return {serial = -1, phase = "UNKNOWN", team = "NONE", carrying = "", valid = false}
end

-- Return true only when a matching, non-stale, well-formed S1 snapshot was accepted.
-- Unrelated future Remote messages are deliberately ignored (not an invalidation).
function PromptPolicy.consume(state: State, packet: any): boolean
    if type(packet) ~= "table" or packet.kind ~= "SNAPSHOT" then return false end
    if serialIsValid(packet.serial) and packet.serial < state.serial then
        return false -- old match epoch must not hide/update current phase
    end
    state.valid = false -- fail closed on malformed current or newer snapshots
    if not serialIsValid(packet.serial) then return false end
    state.serial = packet.serial
    local phase = packet.phase
    if phase ~= "LOBBY" and phase ~= "COUNTDOWN" and phase ~= "ACTIVE"
        and phase ~= "RESULTS" then return false end
    local team = packet.team
    if team ~= "RED" and team ~= "BLUE" and team ~= "NONE" then return false end
    local carry = packet.carrying
    if carry ~= "" and carry ~= "RED" and carry ~= "BLUE" then return false end
    if phase == "ACTIVE" then
        if not teamIsValid(team) then return false end
        if carry ~= "" and carry == team then return false end
    end
    state.phase = phase
    state.team = team
    state.carrying = carry
    state.valid = true
    return true
end

-- Return a *visual only* permission map. The server may still reject a prompt.
-- ownEggVisible is true only when the replicated OWN egg is confirmed home.
function PromptPolicy.view(state: State, ownEggVisible: boolean): {[string]: boolean}
    local out = {RED_EGG = false, BLUE_EGG = false,
        RED_SCORE_PAD = false, BLUE_SCORE_PAD = false}
    if not state.valid or state.phase ~= "ACTIVE" or not teamIsValid(state.team) then
        return out
    end
    local enemy = if state.team == "RED" then "BLUE" else "RED"
    if state.carrying == "" then
        out[enemy .. "_EGG"] = true
    elseif state.carrying == enemy and ownEggVisible == true then
        out[state.team .. "_SCORE_PAD"] = true
    end
    return out
end

return PromptPolicy
