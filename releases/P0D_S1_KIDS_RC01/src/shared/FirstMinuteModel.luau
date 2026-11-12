--!strict
-- TRAP RAIDERS S1: client-only first-minute coach. Never sends gameplay intent.
-- No persistence, reward, analytics, timers, RNG, RemoteEvent creation or authority.
local Coach = {}

export type State = {
    serial: number,
    lastUpdateId: number,
    activeAt: number?,
    initialScore: number,
    scored: boolean,
    carried: boolean,
    dismissed: boolean,
    manualHelp: boolean,
    latest: {[string]: any}?,
}

local VALID_PHASES = {LOBBY = true, COUNTDOWN = true, ACTIVE = true, RESULTS = true}
local VALID_TEAMS = {RED = true, BLUE = true, NONE = true}
local function wholeNumber(value: any): boolean
    return type(value) == "number" and value == value
        and value >= 0 and value <= 1000000000 and value % 1 == 0
end

function Coach.new(): State
    return {
        serial = -1, lastUpdateId = -1, activeAt = nil, initialScore = 0,
        scored = false, carried = false, dismissed = false,
        manualHelp = false, latest = nil,
    }
end

function Coach.setHidden(state: State, hidden: boolean)
    state.dismissed = hidden
    state.manualHelp = not hidden
end

-- False means stale/bad packet. This is ONLY a view-model gate, not a security boundary.
function Coach.consume(state: State, packet: any, localNow: number): boolean
    if type(packet) ~= "table" or packet.kind ~= "SNAPSHOT" then return false end
    if not wholeNumber(packet.serial) or packet.serial < state.serial then return false end
    if not VALID_PHASES[packet.phase] or not VALID_TEAMS[packet.team] then return false end
    if type(packet.time) ~= "number" or packet.time ~= packet.time
        or packet.time < 0 or packet.time > 1000000000 then return false end
    if type(packet.scores) ~= "table" or not wholeNumber(packet.scores.RED)
        or not wholeNumber(packet.scores.BLUE) then return false end
    if type(packet.carrying) ~= "string" or #packet.carrying > 16 then return false end
    if packet.carrying ~= "" and packet.carrying ~= "RED" and packet.carrying ~= "BLUE" then return false end
    if type(packet.role) ~= "string" or (packet.role ~= "RAIDER" and packet.role ~= "GUARDIAN") then return false end
    if type(localNow) ~= "number" or localNow ~= localNow or math.abs(localNow) > 1000000000 then return false end
    -- A server-monotonic SNAPSHOT ordinal protects same-round GUI ordering.
    -- Legacy unversioned snapshots are accepted only until a versioned one.
    local id = packet.updateId
    if id ~= nil then
        if not wholeNumber(id) or id <= state.lastUpdateId then return false end
    elseif state.lastUpdateId >= 0 then
        return false
    end

    if packet.serial > state.serial then
        state.serial = packet.serial
        state.activeAt = nil
        state.initialScore = 0
        state.scored = false
        state.carried = false
    end
    if packet.phase == "ACTIVE" then
        local own = if packet.team == "BLUE" then packet.scores.BLUE else packet.scores.RED
        if state.activeAt == nil then
            state.activeAt = localNow
            state.initialScore = own
        end
        if own > state.initialScore then state.scored = true end
        if packet.carrying ~= "" then state.carried = true end
    end
    state.latest = packet
    if id ~= nil then state.lastUpdateId = id end
    return true
end

export type View = {title: string, detail: string, visible: boolean, tone: string}
function Coach.view(state: State, localNow: number): View?
    local s = state.latest
    if not s then return nil end
    if state.dismissed then return {title = "", detail = "", visible = false, tone = "normal"} end
    if s.phase == "LOBBY" then
        return {title = "まず役職をえらぼう", detail = "速攻は足が速い／守護は体力が多く、罠を置ける！2人でスタート！", visible = true, tone = "normal"}
    end
    if s.phase == "COUNTDOWN" then
        return {title = "もうすぐ対戦！", detail = "敵のお城で卵を取り、自分のお城の納品台へ運ぼう。", visible = true, tone = "normal"}
    end
    if s.phase == "RESULTS" then
        return {title = "つぎの対戦も挑戦しよう！", detail = "数秒後に自動で再戦。もう一度卵を運んでみよう！", visible = true, tone = "success"}
    end
    if s.phase ~= "ACTIVE" then return nil end
    if s.carrying ~= "" then
        return {title = "卵をゲット！", detail = "自分の色のお城へ！ 光る納品台に近づいてタップ。", visible = true, tone = "success"}
    end
    if state.scored then
        return {title = "得点できたね！", detail = "2個先に運ぶと勝利！ 仲間と協力してもう一度！", visible = true, tone = "success"}
    end
    local elapsed = if state.activeAt == nil then 0 else math.max(0, localNow - state.activeAt)
    if elapsed > 60 and not state.manualHelp then
        return {title = "", detail = "", visible = false, tone = "normal"}
    end
    if elapsed < 12 then
        if s.role == "GUARDIAN" then
            return {title = "守護：卵を守ろう！", detail = "自分の卵を守ろう！右下の罠ボタンで足止め。敵が踏むと足が遅くなるよ！", visible = true, tone = "normal"}
        end
        return {title = "敵のお城の卵をねらおう！", detail = "移動して敵の卵に近づこう。出たボタンをタップして取れるよ。", visible = true, tone = "normal"}
    end
    if elapsed < 32 then
        if s.role == "GUARDIAN" then
            return {title = "守護：罠を置こう！", detail = "自分の陣地でTキーか右下の罠ボタンを押そう。敵を足止めできるよ！", visible = true, tone = "normal"}
        end
        return {title = "卵を取ると得点チャンス！", detail = "敵の卵 → 自分の城の納品台。取られたら追いかけよう。", visible = true, tone = "normal"}
    end
    if s.role == "GUARDIAN" then
        return {title = "守護：仲間を守ろう！", detail = "罠は自分の陣地で置こう。20秒たてば次の罠！敵の卵も奪えるよ。", visible = true, tone = "normal"}
    end
    return {title = "城を攻める作戦もあるよ", detail = "敵のお城のコアは右下の攻撃で壊せる。まずは卵を探そう！", visible = true, tone = "normal"}
end

return Coach