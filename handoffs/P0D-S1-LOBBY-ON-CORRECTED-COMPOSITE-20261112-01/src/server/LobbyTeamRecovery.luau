--!strict
-- Standalone deterministic lobby-only TEAM ASSIGNMENT PLANNER.
-- This planner neither assigns sides nor mutates source data, remotes or rounds.
-- Only the sole Game.server.luau integrator may use this with phase == LOBBY.
local LobbyTeamRecovery = {}

type Move = {userId: number, from: string, to: string}

local function exactInteger(v: any): boolean
    return type(v) == "number" and v == v and math.abs(v) <= 9007199254740991
        and v % 1 == 0
end

-- Includes negative Studio test userIds. Nil means unsafe roster, not "no moves".
function LobbyTeamRecovery.plan(roster: any): {Move}?
    if type(roster) ~= "table" or #roster > 64 then return nil end
    local seen: {[number]: boolean} = {}
    local red: {number} = {}
    local blue: {number} = {}
    for i, member in ipairs(roster) do
        if type(member) ~= "table" or not exactInteger(member.userId)
            or seen[member.userId] or (member.team ~= "RED" and member.team ~= "BLUE") then
            return nil
        end
        for key, _ in pairs(member) do
            if key ~= "userId" and key ~= "team" then return nil end
        end
        seen[member.userId] = true
        if member.team == "RED" then
            table.insert(red, member.userId)
        else
            table.insert(blue, member.userId)
        end
        if i > 64 then return nil end
    end
    -- Reject sparse tables and extra non-array fields; ipairs otherwise silently skips holes.
    local arrayCount = #red + #blue
    if arrayCount ~= #roster then return nil end
    for key, _ in pairs(roster) do
        if not exactInteger(key) or key < 1 or key > arrayCount then return nil end
    end
    local source: {number} = red
    local from = "RED"
    local to = "BLUE"
    if #red <= #blue then
        source = blue
        from = "BLUE"
        to = "RED"
    end
    local diff = math.abs(#red - #blue)
    local moves: {Move} = {}
    if diff <= 1 then return moves end
    -- Stable selection independent of input roster ordering.
    table.sort(source, function(a, b) return a > b end)
    for i = 1, math.floor(diff / 2) do
        table.insert(moves, {userId = source[i], from = from, to = to})
    end
    return moves
end

return LobbyTeamRecovery
