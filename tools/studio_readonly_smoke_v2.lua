-- TOY WARS FACTORY — Roblox Studio command-bar smoke check (READ ONLY)
-- Source candidate: PR #187 head 35d4e0fc2a72a6bfc442561f4222e7497df15975
-- Run in Roblox Studio after opening twf_4toy_factory_throughput_NOT_ENGINE_VERIFIED.rbxlx.
-- First run in Edit mode to check packaged scripts, then in Play (server context)
-- to check 3D runtime world and player state. No publishing, writes, HTTP or secrets.
-- This local console output is NOT a signed hosted engine or Android QA receipt.

local RunService = game:GetService("RunService")
if not RunService:IsStudio() then
    warn("TWF_SMOKE_BLOCKED: Studio-only read-only check. No changes made.")
    return
end

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")
local StarterPlayer = game:GetService("StarterPlayer")
local Players = game:GetService("Players")
local passes, failures, skips = 0, 0, 0

local function check(name, predicate)
    local ok, detail = pcall(predicate)
    if ok and detail == true then
        passes = passes + 1
        print("TWF_SMOKE_PASS: " .. name)
    else
        failures = failures + 1
        warn("TWF_SMOKE_FAIL: " .. name .. " — " .. tostring(detail))
    end
end

local function skip(name, reason)
    skips = skips + 1
    print("TWF_SMOKE_SKIP: " .. name .. " — " .. reason)
end

local function approx(a, b)
    return type(a) == "number" and math.abs(a - b) < 0.00001
end

-- All checks below observe only the opened place. The one require() runs the
-- pinned, pure-Luau, no-Roblox-API ToyWarsBalance module.
check("ReplicatedStorage/ToyWarsBalance is ModuleScript", function()
    local v = ReplicatedStorage:FindFirstChild("ToyWarsBalance")
    return v ~= nil and v:IsA("ModuleScript")
end)
check("ToyWarsSelectUnit is RemoteEvent", function()
    local v = ReplicatedStorage:FindFirstChild("ToyWarsSelectUnit")
    return v ~= nil and v:IsA("RemoteEvent")
end)
-- Roblox intentionally does not replicate ServerScriptService contents to clients.
-- Never treat absence of a server-only Script in client Play as a defect.
if RunService:IsClient() then
    skip("Server-only source scripts", "ServerScriptService contents are not replicated to clients; inspect in Edit or server Play")
else
    check("ToyWarsServer is Script", function()
        local v = ServerScriptService:FindFirstChild("ToyWarsServer")
        return v ~= nil and v:IsA("Script")
    end)
    check("ToyWarsSmokeTest is Script", function()
        local v = ServerScriptService:FindFirstChild("ToyWarsSmokeTest")
        return v ~= nil and v:IsA("Script")
    end)
end
check("ToyWarsHUD is LocalScript", function()
    local scripts = StarterPlayer:FindFirstChild("StarterPlayerScripts")
    local v = scripts and scripts:FindFirstChild("ToyWarsHUD")
    return v ~= nil and v:IsA("LocalScript")
end)

local B
local mod = ReplicatedStorage:FindFirstChild("ToyWarsBalance")
if mod and mod:IsA("ModuleScript") then
    local success, value = pcall(require, mod)
    if success and type(value) == "table" then
        B = value
    else
        failures = failures + 1
        warn("TWF_SMOKE_FAIL: ToyWarsBalance require — " .. tostring(value))
    end
end
if B then
    check("Four playable allies are registered", function()
        local names = {"pon", "guardon", "tankuru", "curebo"}
        if #B.PLAYABLE_IDS ~= #names then return false end
        for i, id in ipairs(names) do
            if B.PLAYABLE_IDS[i] ~= id or not B.isUnit(id) then return false end
        end
        return not B.isUnit("junk")
    end)
    check("Factory Lv1..6 produces every 3.0..1.5 sec", function()
        for level = 1, 6 do
            if not approx(B.productionInterval(level), 3.0 - 0.3 * (level - 1)) then
                return false
            end
        end
        return B.productionInterval(0) == nil and B.productionInterval(7) == nil
    end)
    check("JUNK escalates at wave11 and wave50", function()
        local first = B.junkThreat(1)
        local eleven = B.junkThreat(11)
        local fifty = B.junkThreat(50)
        return first.hp == 38 and first.damage == 6
            and eleven.hp == 46 and eleven.damage == 7
            and fifty.hp == 102 and fifty.damage == 14
    end)
    check("Final JUNK CAPTAIN stats and every-10th rule", function()
        local captain = B.junkBoss(50)
        if not (captain and captain.hp == 306 and captain.damage == 18 and captain.reward == 140) then
            return false
        end
        for wave = 1, 50 do
            local result = B.junkBoss(wave)
            if (result ~= nil) ~= (wave % 10 == 0) then return false end
        end
        return true
    end)
    check("Invalid coin or field-cap purchase is refused", function()
        local permitted = B.canBuy("pon", 100, 20)
        local invalid = B.buy("junk", 100, 0)
        return permitted == false and invalid == nil
    end)
else
    skip("Balance runtime rules", "ModuleScript did not load; investigate error above")
end

if RunService:IsRunning() then
    check("3D ToyWarsWorld exists in Play", function()
        local world = workspace:FindFirstChild("ToyWarsWorld")
        return world ~= nil and world:IsA("Folder")
    end)
    check("3D lobby spawn exists in Play", function()
        local world = workspace:FindFirstChild("ToyWarsWorld")
        local spawn = world and world:FindFirstChild("ToyWarsLobbySpawn")
        return spawn ~= nil and spawn:IsA("SpawnLocation")
    end)
    -- In the client console, the local player's replicated objects are the
    -- only authoritative UI target; GetPlayers()[1] could be another user.
    local player = RunService:IsClient() and Players.LocalPlayer or Players:GetPlayers()[1]
    if player then
        check("Player owns server-authoritative factory status", function()
            local status = player:FindFirstChild("ToyWarsStatus")
            if not status then return false end
            local needed = {"FactoryLevel", "BaseHP", "Allies", "Enemies", "SelectedToy", "RoundOutcome"}
            for _, name in ipairs(needed) do
                if not status:FindFirstChild(name) then return false end
            end
            return true
        end)
        check("3D workshop printer displays the server's current speed", function()
            local world = workspace:FindFirstChild("ToyWarsWorld")
            local workshop = world and world:FindFirstChild("Workshop_" .. tostring(player.UserId))
            local printer = workshop and workshop:FindFirstChild("ToyPrinter")
            local caption = printer and printer:FindFirstChild("Caption")
            local text = caption and caption:FindFirstChild("TextLabel")
            local status = player:FindFirstChild("ToyWarsStatus")
            local level = status and status:FindFirstChild("FactoryLevel")
            if not (printer and printer:IsA("BasePart") and text and level and B) then return false end
            local interval = B.productionInterval(level.Value)
            return interval ~= nil and text.Text:find(string.format("%.1fs / toy", interval), 1, true) ~= nil
        end)
        check("Server leaderstats tracks Coins/Wave/Defeated", function()
            local stats = player:FindFirstChild("leaderstats")
            return stats ~= nil and stats:FindFirstChild("Coins") ~= nil
                and stats:FindFirstChild("Wave") ~= nil
                and stats:FindFirstChild("Defeated") ~= nil
        end)
        if RunService:IsClient() then
            check("Local player has responsive HUD instance", function()
                local gui = player:FindFirstChild("PlayerGui")
                local hud = gui and gui:FindFirstChild("ToyWarsHUD")
                return hud ~= nil and hud:FindFirstChild("StatusPanel") ~= nil
                    and hud:FindFirstChild("SelectToy") ~= nil
            end)
        else
            skip("Local HUD", "Run the smoke in client context as well")
        end
    else
        skip("Player status/HUD", "No player loaded yet; run again once Play has a player")
    end
else
    skip("3D Play world and player state", "Currently in Edit mode: press Play and rerun to observe runtime")
end

print(string.format("TWF_STUDIO_SMOKE_RESULT passes=%d failures=%d skips=%d mode=%s source=PR187_35d4e0fc",
    passes, failures, skips, RunService:IsRunning() and "PLAY" or "EDIT"))
-- A PASS must not mask checks which have never executed. Edit-mode, server-
-- only Play and not-yet-spawned player observations are necessarily PARTIAL.
-- Client Play also skips private server source checks by design; completing
-- separate mode runs does not create a signed, combined QA receipt.
-- Even a complete local smoke is not a provider-authenticated engine result.
if failures ~= 0 then
    warn("TWF_STUDIO_SMOKE_INCOMPLETE: investigate failures; do not claim engine PASS")
elseif skips ~= 0 then
    print("TWF_STUDIO_SMOKE_PARTIAL: some checks skipped; no complete local PASS or signed engine proof")
else
    print("TWF_STUDIO_SMOKE_LOCAL_CHECKS_PASS: all checks ran locally; Android/two-client and signed engine evidence UNVERIFIED")
end
