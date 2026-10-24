-- Real whole-server Heartbeat regression through the existing Lua 5.4 harness.
-- Not a Roblox engine, networking, rendering, or multiplayer test.
local Harness = dofile("tests/roblox_server_harness.lua")
local B = dofile("src/ToyWarsBalance.lua")
local server = os.getenv("TWF_SERVER_FILE") or "src/ToyWarsServer.server.lua"
local passed, failed = 0, 0

local function eq(actual, expected, context)
    assert(actual == expected, (context or "value") .. ": expected " ..
        tostring(expected) .. ", got " .. tostring(actual))
end

local function test(name, fn)
    local ok, err = pcall(fn)
    if ok then
        passed = passed + 1
        print("PASS " .. name)
    else
        failed = failed + 1
        print("FAIL " .. name .. ": " .. tostring(err))
    end
end

local function fixture()
    local h = Harness.new(server)
    local player = h:addPlayer(h:newPlayer())
    local coins = assert(player:FindFirstChild("leaderstats"):FindFirstChild("Coins"))
    return h, player, coins
end

local function beats(h, count)
    for _ = 1, count do h.runService.Heartbeat:Fire(0.3) end
end

local function models(h, name)
    local n = 0
    for _, child in ipairs(h.workspace:FindFirstChild("ToyWarsWorld"):GetChildren()) do
        if child.ClassName == "Model" and child.Name == name then n = n + 1 end
    end
    return n
end

test("sufficient coins: Heartbeat buys one PON only after production timer", function()
    local h, player, coins = fixture()
    eq(coins.Value, 50, "initial coins")
    eq(B.buy("pon", coins.Value, 0), 40, "canonical B.buy")
    beats(h, 3)
    eq(h:status(player, "Allies").Value, 0, "before production")
    eq(models(h, "PON"), 0, "before model creation")
    eq(coins.Value, 55, "income before production")
    beats(h, 1)
    eq(coins.Value, 47, "income minus PON cost")
    eq(h:status(player, "Allies").Value, 1, "produced ally")
    eq(models(h, "PON"), 1, "produced PON model")
end)

test("insufficient coins: Heartbeat must not produce or overspend", function()
    local h, player, coins = fixture()
    coins.Value = 0
    h.remote.OnServerEvent:Fire(player, "guardon")
    eq(h:status(player, "SelectedToy").Value, "GUARDON", "selected unit")
    beats(h, 4)
    eq(coins.Value, 7, "income remains when purchase denied")
    local remaining, reason = B.buy("guardon", coins.Value, 0)
    eq(remaining, nil, "canonical B.buy rejects shortage")
    eq(reason, "not_enough_coins", "purchase failure reason")
    eq(h:status(player, "Allies").Value, 0, "no free ally")
    eq(models(h, "GUARDON"), 0, "no free model")
end)

test("recovered balance: next production interval buys selected GUARDON", function()
    local h, player, coins = fixture()
    coins.Value = 0
    h.remote.OnServerEvent:Fire(player, "guardon")
    beats(h, 4)
    eq(h:status(player, "Allies").Value, 0, "first attempt rejected")
    coins.Value = 100
    beats(h, 10)
    eq(coins.Value, 90, "3 seconds of income minus GUARDON cost")
    eq(h:status(player, "Allies").Value, 1, "one ally after recovery")
    eq(models(h, "GUARDON"), 1, "GUARDON produced")
end)

print(string.format("AUTO_PRODUCTION_SUMMARY %d passed / %d failed; whole-server Lua mock, not Roblox engine", passed, failed))
if failed > 0 then os.exit(1) end
