-- Canonical whole-server regression: after a base loss, do not double the restart grace.
-- Native Lua 5.4 mock only; Roblox engine, physics, networking and mobile are NOT tested.
local Harness = dofile("tests/roblox_server_harness.lua")
local server = os.getenv("TWF_SERVER_FILE") or "src/ToyWarsServer.server.lua"
local passed, failed = 0, 0
local function check(name, fn)
    local ok, err = pcall(fn)
    if ok then passed=passed+1; print("PASS "..name)
    else failed=failed+1; print("FAIL "..name..": "..tostring(err)) end
end
local function eq(actual, expected, label)
    assert(actual==expected, label..": expected "..tostring(expected)..", got "..tostring(actual))
end
local function restartFixture(file)
    local h=Harness.new(file)
    local player=h:addPlayer(h:newPlayer())
    local coins=assert(player:FindFirstChild("leaderstats"):FindFirstChild("Coins"))
    local wave=assert(player:FindFirstChild("leaderstats"):FindFirstChild("Wave"))
    local hp=assert(h:status(player,"BaseHP"))
    local function beat()
        coins.Value=0 -- suppress allies while executing the real wave and loss logic
        h.runService.Heartbeat:Fire(0.3)
    end
    local sawWaveTwo=false
    local reset=false
    for _=1,300 do
        beat()
        if wave.Value==2 then sawWaveTwo=true end
        if sawWaveTwo and wave.Value==1 and hp.Value==100 then
            reset=true
            break
        end
    end
    assert(reset, "whole-server combat never reached base loss and reset")
    eq(h:status(player,"Enemies").Value,0,"enemies removed at loss")
    return h,player,beat
end
check("restart grace remains four seconds, not eight",function()
    local h,player,beat=restartFixture(server)
    for _=1,14 do
        beat()
        eq(h:status(player,"Enemies").Value,0,"restart grace")
    end
    beat() -- 4.5s after loss; waveBreak 4.0s and first enemyTimer 0.1s
    eq(h:status(player,"Enemies").Value,1,"first restarted JUNK")
    eq(player:FindFirstChild("leaderstats"):FindFirstChild("Wave").Value,1,"restart wave")
end)
local pinned=".qa/server-before/src/ToyWarsServer.server.lua"
local old=io.open(pinned,"rb")
if old then
    old:close()
    check("pinned pre-fix whole server reproduces doubled restart delay",function()
        local h,player,beat=restartFixture(pinned)
        for _=1,15 do beat() end
        eq(h:status(player,"Enemies").Value,0,"old server at 4.5s")
    end)
end
print(string.format("AUTO_RESTART_GRACE_SUMMARY %d passed / %d failed; whole-server Lua mock",passed,failed))
if failed>0 then os.exit(1) end
