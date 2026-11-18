--!strict
-- EGGRUMBLE GQ8_VIRAL_MOMENTS_CAPTURE_20261119
-- Read-only client view policy over the existing server-authored S1 SNAPSHOT.
-- Never invent a personal KO, damage, reward, egg delivery, or final victory.
local Moment = {}

export type Cue = {kind: string, title: string, recordSeconds: number, tint: string}
export type State = {
    serial: number,
    prev: any?,
    lastAt: number,
    cueCount: number,
    castleDanger: boolean,
    dangerEmitted: boolean,
    finished: boolean,
}

local PHASES = {LOBBY = true, COUNTDOWN = true, ACTIVE = true, RESULTS = true}
local TEAMS = {RED = true, BLUE = true, NONE = true}
local function whole(v: any): boolean
    return type(v) == "number" and v == v and v % 1 == 0 and v >= 0 and v <= 100000000
end

local function valid(packet: any, now: number): boolean
    if type(packet) ~= "table" or packet.kind ~= "SNAPSHOT" then return false end
    if not whole(packet.serial) or not PHASES[packet.phase] or not TEAMS[packet.team] then return false end
    if packet.winner ~= "" and packet.winner ~= "RED" and packet.winner ~= "BLUE"
        and packet.winner ~= "DRAW" then return false end
    if type(packet.carrying) ~= "string" or (packet.carrying ~= ""
        and packet.carrying ~= "RED" and packet.carrying ~= "BLUE") then return false end
    if type(packet.scores) ~= "table" or type(packet.hp) ~= "table"
        or not whole(packet.scores.RED) or not whole(packet.scores.BLUE)
        or not whole(packet.hp.RED) or not whole(packet.hp.BLUE) then return false end
    if not whole(packet.maxHp) or packet.maxHp <= 0
        or packet.hp.RED > packet.maxHp or packet.hp.BLUE > packet.maxHp then return false end
    return type(now) == "number" and now == now and now >= 0 and now <= 1000000000
end

local function compact(packet: any)
    return {
        serial = packet.serial, phase = packet.phase, team = packet.team,
        carrying = packet.carrying, winner = packet.winner,
        redScore = packet.scores.RED, blueScore = packet.scores.BLUE,
        redHp = packet.hp.RED, blueHp = packet.hp.BLUE,
        maxHp = packet.maxHp,
    }
end

function Moment.new(): State
    return {
        serial = -1, prev = nil, lastAt = -10000000, cueCount = 0,
        castleDanger = false, dangerEmitted = false, finished = false,
    }
end

-- Returns only a presentational cue. Server remains sole gameplay authority.
function Moment.consume(state: State, packet: any, now: number): Cue?
    if not valid(packet, now) or packet.serial < state.serial then return nil end
    if packet.serial > state.serial then
        state.serial = packet.serial
        state.prev = nil
        state.lastAt = -10000000
        state.cueCount = 0
        state.castleDanger = false
        state.dangerEmitted = false
        state.finished = false
    end
    local prev = state.prev
    local curr = compact(packet)
    state.prev = curr
    if prev == nil or prev.team ~= curr.team or curr.team == "NONE" then return nil end
    if state.finished then return nil end
    local own = curr.team
    local ownScore = if own == "RED" then curr.redScore else curr.blueScore
    local oldScore = if own == "RED" then prev.redScore else prev.blueScore
    local ownHp = if own == "RED" then curr.redHp else curr.blueHp
    local oldHp = if own == "RED" then prev.redHp else prev.blueHp
    -- A duplicate/out-of-order same-epoch snapshot never earns a new cue.
    if curr.redScore < prev.redScore or curr.blueScore < prev.blueScore then return nil end
    local cue: Cue? = nil
    if prev.phase == "ACTIVE" and curr.phase == "RESULTS" then
        state.finished = true
        if curr.winner == own then
            if state.castleDanger then
                cue = {kind = "COMEBACK", title = "大逆転！お城を守りきった", recordSeconds = 12, tint = "GOLD"}
            else
                cue = {kind = "VICTORY", title = "チーム勝利！", recordSeconds = 10, tint = "GOLD"}
            end
        end
    elseif prev.phase == "ACTIVE" and curr.phase == "ACTIVE" then
        if oldHp > prev.maxHp * 0.22 and ownHp <= curr.maxHp * 0.22 then
            state.castleDanger = true
        end
        if prev.carrying == "" and curr.carrying ~= "" and curr.carrying ~= own then
            cue = {kind = "EGG_STEAL", title = "卵を奪った！逃げ切れ！", recordSeconds = 15, tint = "CYAN"}
        elseif ownScore > oldScore then
            cue = {kind = "TEAM_SCORE", title = "仲間と卵を運んで得点！", recordSeconds = 10, tint = "CYAN"}
        elseif state.castleDanger and not state.dangerEmitted then
            state.dangerEmitted = true
            cue = {kind = "LAST_STAND", title = "お城がピンチ！守り抜け！", recordSeconds = 15, tint = "VIOLET"}
        end
    end
    if cue == nil then return nil end
    local terminal = cue.kind == "VICTORY" or cue.kind == "COMEBACK"
    if not terminal and (state.cueCount >= 4 or now - state.lastAt < 3) then return nil end
    state.lastAt = now
    state.cueCount += 1
    return cue
end

return Moment
