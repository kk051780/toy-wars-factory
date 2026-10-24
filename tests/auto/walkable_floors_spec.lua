-- Exercise the canonical full server through the Lua 5.4 harness; not Roblox physics.
local Harness = dofile("tests/roblox_server_harness.lua")
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

local floorNames = {"FeltBattlefield", "FactoryFloor"}
local function checkWorkshopFloors(map, expected)
    for _, name in ipairs(floorNames) do
        local floor = assert(map:FindFirstChild(name), "missing floor: " .. name)
        eq(floor.CanCollide, expected, name .. " collision")
        eq(floor.Anchored, true, name .. " anchoring")
    end
end

test("both workshop floors collide in every allocated plot", function()
    local h = Harness.new(server)
    for _ = 1, 2 do
        local player = h:addPlayer(h:newPlayer())
        checkWorkshopFloors(assert(h:workshop(player)), true)
    end
end)

test("lobby ground collides while remaining anchored", function()
    local h = Harness.new(server)
    local world = assert(h.workspace:FindFirstChild("ToyWarsWorld"))
    local lobby = assert(world:FindFirstChild("LobbyGround"))
    eq(lobby.CanCollide, true, "LobbyGround collision")
    eq(lobby.Anchored, true, "LobbyGround anchoring")
end)

test("workshop decoration and selectors stay non-collidable", function()
    local h = Harness.new(server)
    local player = h:addPlayer(h:newPlayer())
    local map = assert(h:workshop(player))
    local expected = {
        BattleStripe = true, Conveyor = true, BeltStripe = true,
        ToyPrinter = true, JunkPortal = true, BlueprintVault = true,
        ponSelector = true, guardonSelector = true, tankuruSelector = true,
        UpgradeStation = true,
    }
    local seen = {}
    for _, child in ipairs(map:GetChildren()) do
        if expected[child.Name] then
            eq(child.CanCollide, false, child.Name .. " decoration collision")
            seen[child.Name] = true
        end
    end
    for name in pairs(expected) do
        assert(seen[name], "missing decoration: " .. name)
    end
end)

test("produced PON body parts remain non-collidable", function()
    local h = Harness.new(server)
    h:addPlayer(h:newPlayer())
    for _ = 1, 4 do h.runService.Heartbeat:Fire(0.3) end
    local world = assert(h.workspace:FindFirstChild("ToyWarsWorld"))
    local toy
    for _, child in ipairs(world:GetChildren()) do
        if child.ClassName == "Model" and child.Name == "PON" then
            toy = child
            break
        end
    end
    assert(toy, "PON should be produced by real Heartbeat callback")
    local parts = 0
    for _, child in ipairs(toy:GetChildren()) do
        if child:IsA("BasePart") then
            eq(child.CanCollide, false, "PON " .. child.Name .. " collision")
            parts = parts + 1
        end
    end
    assert(parts >= 4, "expected complete PON body")
end)

-- CI pins a pre-fix server in .qa/server-before. The old server must fail
-- the new floor assertions; this guards against a test that always passes.
local before = ".qa/server-before/src/ToyWarsServer.server.lua"
local oldFile = io.open(before, "r")
if oldFile then
    oldFile:close()
    test("pinned old server is a negative control for all three floors", function()
        local h = Harness.new(before)
        local player = h:addPlayer(h:newPlayer())
        checkWorkshopFloors(assert(h:workshop(player)), false)
        local world = assert(h.workspace:FindFirstChild("ToyWarsWorld"))
        eq(assert(world:FindFirstChild("LobbyGround")).CanCollide, false,
            "old LobbyGround collision")
    end)
else
    print("SKIP pinned negative control (CI fixture not present)")
end

print(string.format("AUTO_WALKABLE_FLOORS_SUMMARY %d passed / %d failed; native mocks, not Roblox physics", passed, failed))
if failed > 0 then os.exit(1) end
