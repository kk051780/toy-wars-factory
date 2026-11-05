-- Regress discarded Heartbeat time using the canonical full server and Lua harness.
-- Native mock only; this is not a Roblox engine or device timing measurement.
local Harness = dofile("tests/roblox_server_harness.lua")
local server = os.getenv("TWF_SERVER_FILE") or "src/ToyWarsServer.server.lua"
local passed, failed = 0, 0
local function eq(actual, expected, context)
    assert(actual == expected, (context or "value") .. ": expected " ..
        tostring(expected) .. ", got " .. tostring(actual))
end
local function test(name, fn)
    local ok, err = pcall(fn)
    if ok then passed = passed + 1; print("PASS " .. name)
    else failed = failed + 1; print("FAIL " .. name .. ": " .. tostring(err)) end
end
local function fixture()
    local h = Harness.new(server)
    local player = h:addPlayer(h:newPlayer())
    local coins = assert(player:FindFirstChild("leaderstats"):FindFirstChild("Coins"))
    return h, player, coins
end
local function lagged(h)
    h.runService.Heartbeat:Fire(0.6) -- server must cap each step without discarding 0.3s
    for _ = 1, 3 do h.runService.Heartbeat:Fire(0.12) end
end
test("lagged Heartbeat retains elapsed income without early production", function()
    local h, player, coins = fixture()
    lagged(h) -- total 0.96s, 6 coins/s, floor(5.76) = 5
    eq(coins.Value, 55, "coins after 0.96 elapsed seconds")
    eq(h:status(player, "Allies").Value, 0, "no production before 1.2 seconds")
end)
test("lagged and regular Heartbeats reach the same first production", function()
    local h, player, coins = fixture()
    lagged(h)
    h.runService.Heartbeat:Fire(0.3) -- 1.26s total: 7 earned, 10 spent
    eq(coins.Value, 47, "lagged production balance")
    eq(h:status(player, "Allies").Value, 1, "lagged first toy")
    local regular, regularPlayer, regularCoins = fixture()
    for _ = 1, 8 do regular.runService.Heartbeat:Fire(0.12) end
    regular.runService.Heartbeat:Fire(0.3)
    eq(regularCoins.Value, coins.Value, "lagged vs regular balance")
    eq(regular:status(regularPlayer, "Allies").Value, 1, "regular first toy")
end)
print(string.format("AUTO_HEARTBEAT_LAG_SUMMARY %d passed / %d failed; whole-server Lua mock", passed, failed))
if failed > 0 then os.exit(1) end
