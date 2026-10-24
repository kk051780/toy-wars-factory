-- Verify canonical server base-loss reset after unopposed enemy escapes.
-- Whole-server Lua mock only: not Roblox physics, networking, or Studio.
local Harness = dofile("tests/roblox_server_harness.lua")
local server = os.getenv("TWF_SERVER_FILE") or "src/ToyWarsServer.server.lua"
local h = Harness.new(server)
local player = h:addPlayer(h:newPlayer())
local coins = assert(player:FindFirstChild("leaderstats"):FindFirstChild("Coins"))

local function status(name)
    return assert(h:status(player, name), "missing status: " .. name).Value
end

local function eq(actual, expected, context)
    assert(actual == expected, context .. ": expected " ..
        tostring(expected) .. ", got " .. tostring(actual))
end

local function noPurchaseBeat()
    -- Prevent allied production so the real Heartbeat wave logic reaches loss.
    coins.Value = 0
    h.runService.Heartbeat:Fire(0.3)
end

local reachedWaveTwo, sawDamage, resetTick = false, false, nil
for tick = 1, 220 do
    noPurchaseBeat()
    local wave, hp = status("Wave"), status("BaseHP")
    if wave == 2 then
        reachedWaveTwo = true
        if hp < 40 then sawDamage = true end
    elseif reachedWaveTwo and wave == 1 and hp == 100 then
        resetTick = tick
        break
    end
end
assert(reachedWaveTwo, "first wave never completed")
assert(sawDamage, "second-wave enemies never damaged the base")
assert(resetTick, "base loss did not reset within 66 simulated seconds")
eq(status("Wave"), 1, "wave reset")
eq(status("BaseHP"), 100, "base HP reset")
eq(coins.Value, 40, "minimum restart wallet")
eq(status("Enemies"), 0, "all enemy entities removed")
eq(status("Allies"), 0, "no phantom allies")
eq(player:FindFirstChild("leaderstats"):FindFirstChild("Defeated").Value, 0, "no phantom kills")

local junkModels = 0
local world = assert(h.workspace:FindFirstChild("ToyWarsWorld"))
for _, child in ipairs(world:GetChildren()) do
    if child.ClassName == "Model" and child.Name == "JUNK" then
        junkModels = junkModels + 1
    end
end
eq(junkModels, 0, "enemy models removed after loss")

-- Reset must restore a grace period, not immediately spawn a new JUNK.
for _ = 1, 13 do
    noPurchaseBeat()
    eq(status("Enemies"), 0, "restart grace period")
end
eq(status("Wave"), 1, "restart wave remains one")
eq(status("BaseHP"), 100, "restart HP remains full")
print("PASS base loss resets wave, HP, wallet, enemies and restart grace; whole-server Lua mock, not Roblox engine")
