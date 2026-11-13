--!strict
-- P0D FTUE Egg Joy: PURE read-only view transition policy.
-- Server remains the sole egg, score, role, round and winner authority.
-- Never credit the player for a teammate's score; never celebrate from initial sync.
local Rules = {}

local function int(n: any): boolean
    return type(n) == "number" and n == n and n ~= math.huge
        and n ~= -math.huge and n % 1 == 0 and n >= 0 and n <= 2000000000
end

local function team(t: any): boolean
    return t == "RED" or t == "BLUE"
end

local function phase(p: any): boolean
    return p == "LOBBY" or p == "COUNTDOWN"
        or p == "ACTIVE" or p == "RESULTS"
end

function Rules.accept(previous: any, snap: any): (any, string?)
    if type(snap) ~= "table" or snap.kind ~= "SNAPSHOT"
        or not int(snap.serial) or not int(snap.updateId)
        or not phase(snap.phase) or not team(snap.team)
        or type(snap.scores) ~= "table"
        or not int(snap.scores.RED) or not int(snap.scores.BLUE)
        or type(snap.carrying) ~= "string"
        or (snap.carrying ~= "" and not team(snap.carrying))
        or type(snap.winner) ~= "string"
        or (snap.winner ~= "" and not team(snap.winner)
            and snap.winner ~= "DRAW") then
        return previous, nil
    end
    -- Game snapshots always carry only the *enemy* egg.
    if snap.carrying ~= "" and snap.carrying == snap.team then
        return previous, nil
    end
    if type(previous) == "table" then
        if snap.serial < previous.serial
            or snap.updateId <= previous.updateId then
            return previous, nil
        end
    end
    local current = {
        serial = snap.serial, updateId = snap.updateId,
        phase = snap.phase, team = snap.team,
        carrying = snap.carrying,
        scores = {RED = snap.scores.RED, BLUE = snap.scores.BLUE},
        winner = snap.winner,
    }
    -- Initial sync, new match, team reassignment, and non-ACTIVE history:
    -- never invent an exciting moment that the player did not observe.
    if type(previous) ~= "table" or previous.serial ~= current.serial
        or previous.team ~= current.team or previous.phase ~= "ACTIVE" then
        return current, nil
    end
    -- Scores are monotonic within one valid server round. A malformed
    -- rollback must not create a false "score" on the next packet.
    if current.scores.RED < previous.scores.RED
        or current.scores.BLUE < previous.scores.BLUE then
        return previous, nil
    end
    if current.phase == "RESULTS" then
        if current.winner == current.team then
            return current, "VICTORY"
        end
        return current, nil
    end
    if current.phase ~= "ACTIVE" then
        return current, nil
    end
    -- Team score: say TEAM, not "YOU scored".
    if current.scores[current.team] > previous.scores[current.team] then
        return current, "TEAM_SCORE"
    end
    -- Highlight a genuine first observed empty->enemy-egg transition.
    if previous.carrying == "" and current.carrying ~= ""
        and current.carrying ~= current.team then
        return current, "PICKUP"
    end
    return current, nil
end

return Rules
