-- Whole-server upgrade economy regression; native mocks, not Roblox Studio.
local Harness = dofile("tests/roblox_server_harness.lua")
local B = assert(loadfile("src/ToyWarsBalance.lua"))()
local server = os.getenv("TWF_SERVER_FILE") or "src/ToyWarsServer.server.lua"
local passed, failed = 0, 0
local function eq(a, b, msg)
    assert(a == b, (msg or "value") .. ": expected " .. tostring(b) .. ", got " .. tostring(a))
end
local function test(name, fn)
    local ok, err = pcall(fn)
    if ok then passed = passed + 1; print("PASS " .. name)
    else failed = failed + 1; print("FAIL " .. name .. ": " .. tostring(err)) end
end
local function fixture()
    local h = Harness.new(server)
    local p = h:addPlayer(h:newPlayer(h:character()))
    h:advance(0.11) -- finish deferred teleport before positioning at station
    local prompt, pad = h:prompt(p, "UpgradeStation")
    p.Character:FindFirstChild("HumanoidRootPart").Position = pad.Position
    local coins = p:FindFirstChild("leaderstats"):FindFirstChild("Coins")
    return h, p, prompt, coins, h:status(p, "FactoryLevel")
end
test("insufficient coins cannot purchase an upgrade", function()
    local _, p, prompt, coins, level = fixture()
    eq(B.upgradePrice(1), 65, "canonical level-one price")
    coins.Value = 64
    prompt.Triggered:Fire(p)
    eq(level.Value, 1, "level"); eq(coins.Value, 64, "coins")
end)
test("exact upgrade price leaves zero coins and increases level once", function()
    local _, p, prompt, coins, level = fixture()
    coins.Value = B.upgradePrice(1)
    prompt.Triggered:Fire(p)
    eq(level.Value, 2, "level"); eq(coins.Value, 0, "coins")
end)
test("all upgrades stop at MAX_LEVEL even on forged disabled trigger", function()
    local _, p, prompt, coins, level = fixture()
    for current = 1, B.MAX_LEVEL - 1 do
        eq(level.Value, current, "before upgrade")
        coins.Value = B.upgradePrice(current)
        prompt.Triggered:Fire(p)
        eq(level.Value, current + 1, "after upgrade")
        eq(coins.Value, 0, "exact-price balance")
    end
    eq(prompt.Enabled, false, "prompt disabled at maximum")
    coins.Value = B.MAX_CASH
    prompt.Triggered:Fire(p) -- harness intentionally bypasses client-side Enabled
    eq(level.Value, B.MAX_LEVEL, "maximum level")
    eq(coins.Value, B.MAX_CASH, "maximum-level funds retained")
end)
test("real Heartbeat increases income after upgrading before production", function()
    local h, p, prompt, coins, level = fixture()
    coins.Value = B.upgradePrice(1)
    prompt.Triggered:Fire(p)
    eq(level.Value, 2, "upgraded level")
    for _ = 1, 5 do h.runService.Heartbeat:Fire(0.12) end
    eq(coins.Value, math.floor(B.incomePerSecond(2) * 0.6), "upgraded income")
    eq(h:status(p, "Allies").Value, 0, "no production before 1.2 seconds")
    local normal, _, _, normalCoins = fixture()
    normalCoins.Value = 0
    for _ = 1, 5 do normal.runService.Heartbeat:Fire(0.12) end
    eq(normalCoins.Value, math.floor(B.incomePerSecond(1) * 0.6), "baseline income")
    assert(coins.Value > normalCoins.Value, "upgrade must increase real server income")
end)
print(string.format("AUTO_UPGRADE_ECONOMY_SUMMARY %d passed / %d failed; offline Lua mocks", passed, failed))
if failed > 0 then os.exit(1) end
