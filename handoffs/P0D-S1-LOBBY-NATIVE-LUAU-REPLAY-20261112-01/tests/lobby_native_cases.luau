--!strict
-- Test body is appended after wrapping original source in a local function by
-- tools/run_native_lobby_replay.py. This is *actual* Luau execution, not an oracle.
local cases = 0
local failures = 0
local function check(condition, tag)
    cases += 1
    if not condition then
        error("LOBBY_NATIVE_FAIL " .. tag)
    end
end
local function clone(roster)
    local out = {}
    for i, v in ipairs(roster) do
        out[i] = { userId = v.userId, team = v.team }
    end
    return out
end
local function sameMoves(a, b)
    if type(a) ~= "table" or type(b) ~= "table" or #a ~= #b then return false end
    for i = 1, #a do
        if a[i].userId ~= b[i].userId or a[i].from ~= b[i].from or a[i].to ~= b[i].to then
            return false
        end
    end
    return true
end
local function verifyValid(roster, tag)
    local original = clone(roster)
    local red, blue, teamById = 0, 0, {}
    for _, player in ipairs(roster) do
        teamById[player.userId] = player.team
        if player.team == "RED" then red += 1 else blue += 1 end
    end
    local moves = LobbyTeamRecovery.plan(roster)
    check(type(moves) == "table", tag .. ":returned_table")
    local expected = math.floor(math.abs(red-blue)/2)
    check(#moves == expected, tag .. ":minimal_move_count")
    local visited = {}
    local totalRed, totalBlue = red, blue
    local largestFrom = nil
    for i, move in ipairs(moves) do
        check(visited[move.userId] == nil, tag .. ":unique_move_"..i)
        visited[move.userId] = true
        check(teamById[move.userId] == move.from, tag .. ":correct_original_side_"..i)
        check((move.from == "RED" and move.to == "BLUE") or (move.from == "BLUE" and move.to == "RED"), tag .. ":correct_target_"..i)
        if move.from == "RED" then totalRed -= 1; totalBlue += 1
        else totalBlue -= 1; totalRed += 1 end
        if largestFrom ~= nil then check(largestFrom > move.userId, tag .. ":stable_desc_order_"..i) end
        largestFrom = move.userId
    end
    check(math.abs(totalRed - totalBlue) <= 1, tag .. ":balanced_after_moves")
    for i, originalPlayer in ipairs(original) do
        check(roster[i].userId == originalPlayer.userId and roster[i].team == originalPlayer.team, tag .. ":input_not_mutated_"..i)
    end
    local reverse = {}
    for i = #original, 1, -1 do table.insert(reverse, original[i]) end
    local reversedMoves = LobbyTeamRecovery.plan(reverse)
    check(sameMoves(moves, reversedMoves), tag .. ":permutation_invariant")
end

-- Exhaustively cover 0..8 player RED/BLUE masks (511 cases), with reverse-roster check.
local exhaustive = 0
for n = 0, 8 do
    for mask = 0, 2 ^ n - 1 do
        local roster = {}
        for i = 1, n do
            local team = if bit32.band(mask, bit32.lshift(1, i - 1)) ~= 0 then "RED" else "BLUE"
            roster[i] = { userId = 1000 + i, team = team }
        end
        verifyValid(roster, "exhaustive-"..n.."-"..mask)
        exhaustive += 1
    end
end
check(exhaustive == 511, "exhaustive_count_511")

-- Deterministic seeded larger masks, including the 64-player defensive upper limit.
math.randomseed(20261112)
local fuzz = 0
for n = 1, 64 do
    for rep = 1, 8 do
        local roster = {}
        for i = 1, n do
            roster[i] = {userId = i * 3 - 800, team = if math.random(0,1) == 0 then "RED" else "BLUE"}
        end
        verifyValid(roster, "fuzz-"..n.."-"..rep)
        fuzz += 1
    end
end
check(fuzz == 512, "fuzz_count_512")

local function invalid(roster, tag)
    local ok, value = pcall(function() return LobbyTeamRecovery.plan(roster) end)
    check(ok and value == nil, "invalid_fail_closed_"..tag)
end
invalid(nil, "nil")
invalid(false, "false")
invalid(3, "numeric")
invalid("bad", "string")
invalid({{userId = 1, team = "RED"}, {userId = 1, team = "BLUE"}}, "duplicate_id")
invalid({{userId = "1", team = "RED"}}, "id_string")
invalid({{userId = 1.5, team = "RED"}}, "fraction")
invalid({{userId = 9007199254740992, team = "RED"}}, "unsafe_precision")
invalid({{userId = math.huge, team = "RED"}}, "infinity")
invalid({{userId = 0/0, team = "RED"}}, "nan")
invalid({{userId = 1, team = "NONE"}}, "bad_team")
invalid({{userId = 1, team = "RED", extra = 1}}, "member_extra")
invalid({[2] = {userId = 1, team = "RED"}}, "sparse_missing_first")
invalid({[1] = {userId = 1, team = "RED"}, [3] = {userId = 2, team = "BLUE"}}, "sparse_missing_middle")
invalid({[1] = {userId = 1, team = "RED"}, diagnostic = true}, "extra_roster_key")
local large = {}
for i = 1, 65 do large[i] = {userId = i, team = "RED"} end
invalid(large, "too_many_65")

verifyValid({{userId=-1, team="RED"}, {userId=-2,team="RED"}, {userId=-3,team="RED"}, {userId=-4,team="RED"}}, "negative_studio_ids")
verifyValid({{userId=9007199254740991,team="RED"}, {userId=0,team="RED"}}, "max_safe_positive")
print("P0D_LOBBY_NATIVE_SEMANTIC_PASS", "exhaustive="..exhaustive, "seeded_fuzz="..fuzz, "assertions="..cases, "invalid_inputs=16", "source_sha256=35c546f33e0454ceaf7fa26cf5ee44763673c6764906cc249ef282bb096ea404")
