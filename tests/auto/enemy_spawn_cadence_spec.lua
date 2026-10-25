-- Canonical whole-server enemy cadence regression (Lua mock, not Roblox engine).
local H = dofile("tests/roblox_server_harness.lua")
local server = os.getenv("TWF_SERVER_FILE") or "src/ToyWarsServer.server.lua"
local passed, failed = 0, 0
local function check(name, fn)
    local ok, err = pcall(fn)
    if ok then passed=passed+1; print("PASS "..name)
    else failed=failed+1; print("FAIL "..name..": "..tostring(err)) end
end
local function eq(got, expected, label)
    assert(got==expected, label..": expected "..expected..", got "..got)
end
local function fixture()
    local h=H.new(server)
    local player=h:addPlayer(h:newPlayer())
    local coins=assert(player:FindFirstChild("leaderstats"):FindFirstChild("Coins"))
    return h,player,coins
end
local function ticks(h,coins,dt,n)
    for _=1,n do
        coins.Value=0 -- no ally purchases or combat to distort wave count
        h.runService.Heartbeat:Fire(dt)
    end
end
check("grace period and first JUNK remain unchanged", function()
    local h,p,c=fixture()
    ticks(h,c,0.3,14)
    eq(h:status(p,"Enemies").Value,0,"grace enemies")
    ticks(h,c,0.3,1)
    eq(h:status(p,"Enemies").Value,1,"first spawn")
end)
check("0.30s steps retain five JUNK before first escape", function()
    local h,p,c=fixture()
    ticks(h,c,0.3,45)
    eq(h:status(p,"Enemies").Value,5,"enemies")
    eq(h:status(p,"Allies").Value,0,"allies")
    eq(h:status(p,"BaseHP").Value,100,"base")
end)
check("0.26s steps retain five JUNK before first escape", function()
    local h,p,c=fixture()
    ticks(h,c,0.26,52)
    eq(h:status(p,"Enemies").Value,5,"enemies")
    eq(h:status(p,"Allies").Value,0,"allies")
    eq(h:status(p,"BaseHP").Value,100,"base")
end)
print(string.format("AUTO_ENEMY_CADENCE_SUMMARY %d passed / %d failed; whole-server Lua mock",passed,failed))
if failed>0 then os.exit(1) end
