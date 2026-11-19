--!strict
-- EGGRUMBLE neutral-horde SPAWN BUDGET only. No character/AI/score authority.
-- Intended for existing #482 SwarmCombat author to wire, never a second horde.
local Pacing = {}
Pacing.MAX_ALIVE = 110
Pacing.MAX_BATCH = 8
Pacing.NOMINAL_RATE = 40 -- upper throughput 36,000 per 15m if all are killed
Pacing.BUSY_RATE = 26
Pacing.OVERLOADED_RATE = 16
Pacing.MAX_CREDIT = 8

local function finite(v: any): boolean
    return type(v) == "number" and v == v and v ~= math.huge and v ~= -math.huge
end

function Pacing.new(matchId: string): any
    assert(type(matchId) == "string" and #matchId > 0, "match ID required")
    return { matchId = matchId, credit = 0, totalIssued = 0, ticks = 0 }
end

-- Input is server-only, never derived from client Remote or a scoreboard.
-- dt: elapsed wall seconds since last planner tick (no processing of backlog).
-- tickMs: measured server task/heartbeat pressure; NOT Android fps evidence.
-- We deliberately return zero on invalid/transient state to preserve the match.
function Pacing.step(state: any, input: any): (number, string)
    if type(state) ~= "table" or type(input) ~= "table" then return 0, "INVALID" end
    if input.matchId ~= state.matchId or input.phase ~= "ACTIVE" then
        state.credit = 0
        return 0, "INACTIVE"
    end
    local heroes = input.activeHeroes
    local live = input.live
    local dt = input.dt
    local tickMs = input.tickMs
    if not finite(heroes) or not finite(live) or not finite(dt) or not finite(tickMs)
        or heroes % 1 ~= 0 or heroes < 0 or heroes > 16
        or live % 1 ~= 0 or live < 0 or live > Pacing.MAX_ALIVE
        or dt <= 0 or dt > 1 or tickMs < 0 then
        state.credit = 0
        return 0, "INVALID"
    end
    if heroes == 0 then
        state.credit = 0 -- do not bank a huge spawn burst during empty maps
        return 0, "NO_TARGET"
    end
    local room = Pacing.MAX_ALIVE - live
    if room == 0 then
        state.credit = 0 -- no hidden spawn debt when 110 actors already alive
        return 0, "CAP"
    end
    local rate = Pacing.NOMINAL_RATE
    if tickMs >= 65 then
        rate = Pacing.OVERLOADED_RATE
    elseif tickMs >= 45 then
        rate = Pacing.BUSY_RATE
    end
    -- Bounded catch-up: no latency-induced mega wave and no client-driven rate.
    state.credit = math.min(Pacing.MAX_CREDIT, (state.credit or 0) + dt * rate)
    local count = math.min(math.floor(state.credit + 1e-9), room, Pacing.MAX_BATCH)
    state.credit -= count
    state.totalIssued = (state.totalIssued or 0) + count
    state.ticks = (state.ticks or 0) + 1
    return count, "READY"
end

return Pacing
