-- Whole canonical server regression: production timer must preserve sub-step overshoot.
-- Native Lua 5.4 mock only; no Roblox engine, physics, networking or mobile evidence.
local Harness = dofile("tests/roblox_server_harness.lua")
local server = os.getenv("TWF_SERVER_FILE") or "src/ToyWarsServer.server.lua"
local passed, failed = 0, 0
local function eq(actual, expected, context)
    assert(actual == expected, context .. ": expected " .. tostring(expected) ..
        ", got " .. tostring(actual))
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
local function beats(h, count)
    for _ = 1, count do h.runService.Heartbeat:Fire(0.26) end
end
test("no production before the first 1.2-second interval", function()
    local h, player, coins = fixture()
    beats(h, 4) -- 1.04 seconds
    eq(h:status(player, "Allies").Value, 0, "early ally count")
    eq(coins.Value, 56, "income without purchase")
    beats(h, 1) -- 1.30 seconds, first purchase
    eq(h:status(player, "Allies").Value, 1, "first PON")
    eq(coins.Value, 47, "first purchase and income")
end)
test("overshoot does not accumulate into a lost production cycle", function()
    local h, player, coins = fixture()
    beats(h, 28) -- 7.28 seconds: 1.2, 4.2, 7.2 are due
    eq(h:status(player, "Allies").Value, 3, "three PONs produced")
    eq(coins.Value, 63, "income minus three purchases")
    -- Old server resets to 3.0, loses overshoot, and produces only two PONs (73 coins).
end)
print(string.format("AUTO_PRODUCTION_CADENCE_SUMMARY %d passed / %d failed; native whole-server mock", passed, failed))
if failed > 0 then os.exit(1) end
