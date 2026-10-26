-- Whole-server combat regression: fractional Heartbeat overshoot must not slow attacks.
-- Native Lua mock only; not Roblox physics, rendering, multiplayer or device evidence.
local Harness=dofile("tests/roblox_server_harness.lua")
local server=os.getenv("TWF_SERVER_FILE") or "src/ToyWarsServer.server.lua"
local passed,failed=0,0
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1; print("PASS "..name)
    else failed=failed+1; print("FAIL "..name..": "..tostring(err)) end
end
local function eq(actual,expected,label)
    assert(actual==expected,label..": expected "..tostring(expected)..", got "..tostring(actual))
end
local function firstThreeHits(file)
    local h=Harness.new(file)
    local player=h:addPlayer(h:newPlayer())
    local coins=assert(player:FindFirstChild("leaderstats"):FindFirstChild("Coins"))
    h.remote.OnServerEvent:Fire(player,"pon")
    local world=assert(h.workspace:FindFirstChild("ToyWarsWorld"))
    local firstJunk=nil
    local previousWidth=3.2
    local hitTicks={}
    for tick=1,110 do
        -- Buy one PON on the first production tick; suppress all later purchases.
        coins.Value=tick<=5 and 10 or 0
        h.runService.Heartbeat:Fire(0.26)
        if not firstJunk then
            for _,model in ipairs(world:GetChildren()) do
                if model.Name=="JUNK" then firstJunk=model; break end
            end
        end
        if firstJunk and firstJunk.Parent then
            local bar=assert(firstJunk:FindFirstChild("HealthBar"))
            local width=bar.Size.X
            if width<previousWidth-0.01 then
                hitTicks[#hitTicks+1]=tick
                previousWidth=width
                if #hitTicks==3 then return hitTicks end
            end
        end
    end
    error("canonical server did not produce three PON hits on first JUNK")
end
check("0.26-second frames retain PON cooldown remainder without banking idle time",function()
    local ticks=firstThreeHits(server)
    eq(ticks[2]-ticks[1],4,"first attack interval")
    eq(ticks[3]-ticks[1],7,"third attack with preserved fractional remainder")
end)
local pinned=".qa/server-before/src/ToyWarsServer.server.lua"
local old=io.open(pinned,"rb")
if old then
    old:close()
    check("pinned old whole server reproduces one extra tick of cooldown drift",function()
        local ticks=firstThreeHits(pinned)
        eq(ticks[2]-ticks[1],4,"old first attack interval")
        eq(ticks[3]-ticks[1],8,"old third attack drift")
    end)
end
print(string.format("AUTO_COMBAT_CADENCE_SUMMARY %d passed / %d failed; whole-server Lua mock",passed,failed))
if failed>0 then os.exit(1) end
