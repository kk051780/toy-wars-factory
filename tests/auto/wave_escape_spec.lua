-- Exercise canonical server wave spawning, escapes, and wave-clear rewards.
-- Whole-server Lua harness only; no Roblox physics, clients, or rendering.
local Harness = dofile("tests/roblox_server_harness.lua")
local B = dofile("src/ToyWarsBalance.lua")
local server = os.getenv("TWF_SERVER_FILE") or "src/ToyWarsServer.server.lua"
local passed, failed = 0, 0

local function eq(actual, expected, name)
    assert(actual == expected, (name or "value") .. ": expected " ..
        tostring(expected) .. ", got " .. tostring(actual))
end

local function check(name, fn)
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

local function tickWithoutPurchases(h, coins)
    -- Isolate enemy-wave behavior: a zero balance before each tick keeps
    -- automatic production from creating allies that kill incoming JUNK.
    coins.Value = 0
    h.runService.Heartbeat:Fire(0.3)
end

check("first wave respects grace period before spawning JUNK", function()
    local h, player, coins = fixture()
    for _ = 1, 14 do tickWithoutPurchases(h, coins) end
    eq(h:status(player, "Enemies").Value, 0, "grace-period enemies")
    eq(h:status(player, "Wave").Value, 1, "initial wave")
    tickWithoutPurchases(h, coins)
    eq(h:status(player, "Enemies").Value, 1, "first JUNK spawned")
    eq(h:status(player, "BaseHP").Value, 100, "base before escape")
end)

check("five unopposed JUNK escapes damage base and advance wave", function()
    local h, player, coins = fixture()
    local completedAt
    for i = 1, 100 do
        tickWithoutPurchases(h, coins)
        if h:status(player, "Wave").Value == 2 then
            completedAt = i
            break
        end
    end
    assert(completedAt, "wave 1 did not finish within 30 simulated seconds")
    eq(B.waveSize(1), 5, "canonical first-wave size")
    eq(h:status(player, "BaseHP").Value, 40, "five escapes at 12 damage")
    eq(h:status(player, "Enemies").Value, 0, "cleared enemy status")
    eq(h:status(player, "Allies").Value, 0, "no purchased allies")
    eq(player:FindFirstChild("leaderstats"):FindFirstChild("Defeated").Value, 0, "no ally kills")
    local reward = assert(B.waveReward(1))
    assert(coins.Value >= reward and coins.Value <= reward + 2,
        "wave-clear reward missing: expected " .. reward .. " plus at most 2 income, got " .. coins.Value)
end)

print(string.format("AUTO_WAVE_SUMMARY %d passed / %d failed; whole-server Lua mock, not Roblox engine", passed, failed))
if failed > 0 then os.exit(1) end
