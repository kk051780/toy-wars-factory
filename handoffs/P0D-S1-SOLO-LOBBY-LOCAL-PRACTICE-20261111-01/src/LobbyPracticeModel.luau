--!strict
-- LOCAL ONLY. S1 server remains sole match/combat/score/egg authority.
local Practice = {}
local COOLDOWN_SECONDS = 0.45
local MAX_HITS = 99
local MAX_RANGE_STUDS = 12
local MIN_FACE_DOT = 0.12

local function finite(n: any): boolean
    return type(n) == "number" and n == n and n > -math.huge and n < math.huge
end

local function count(n: any): boolean
    return finite(n) and n % 1 == 0 and n >= 0 and n <= 100
end

function Practice.new()
    return {serial = -1, eligible = false, hits = 0, lastHitAt = -math.huge}
end

function Practice.consume(state, packet: any): boolean
    if type(packet) ~= "table" or packet.kind ~= "SNAPSHOT" then return false end
    -- Ignore a delayed prior-round packet; do not reopen the lobby in a new round.
    local serial = packet.serial
    if not finite(serial) or serial < 0 or serial > 1000000000 or serial % 1 ~= 0 then
        state.eligible = false
        return false
    end
    if serial < state.serial then return false end
    if packet.phase ~= "LOBBY" and packet.phase ~= "COUNTDOWN"
        and packet.phase ~= "ACTIVE" and packet.phase ~= "RESULTS" then
        state.eligible = false
        return false
    end
    if not count(packet.redPlayers) or not count(packet.bluePlayers) then
        state.eligible = false
        return false
    end
    local team = packet.team
    if team ~= "RED" and team ~= "BLUE" then
        state.eligible = false
        return false
    end
    local online = packet.redPlayers + packet.bluePlayers
    local own = if team == "RED" then packet.redPlayers else packet.bluePlayers
    local enable = packet.phase == "LOBBY" and online == 1 and own == 1
    local was = state.eligible
    if serial ~= state.serial or (enable and not was) then
        state.hits = 0
        state.lastHitAt = -math.huge
    end
    state.serial = serial
    state.eligible = enable
    return true
end

function Practice.hit(state, now: any, distance: any, faceDot: any): boolean
    if not state.eligible then return false end
    if not finite(now) or not finite(distance) or not finite(faceDot) then return false end
    if distance < 0 or distance > MAX_RANGE_STUDS then return false end
    if faceDot < MIN_FACE_DOT or faceDot > 1.0001 then return false end
    if state.hits >= MAX_HITS or now < state.lastHitAt then return false end
    if now - state.lastHitAt < COOLDOWN_SECONDS then return false end
    state.lastHitAt = now
    state.hits += 1
    return true
end

function Practice.status(state): string
    if not state.eligible then return "" end
    return string.format("れんしゅう %d/%d　※スコア・ほうしゅうなし", state.hits, MAX_HITS)
end

return Practice
