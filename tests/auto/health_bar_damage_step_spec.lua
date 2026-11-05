-- Whole canonical server regression: target health bar must update on the damage step.
-- Deterministic Lua 5.4 mock, not Roblox rendering, physics or mobile evidence.
local Harness=dofile("tests/roblox_server_harness.lua")
local server=os.getenv("TWF_SERVER_FILE") or "src/ToyWarsServer.server.lua"
local passed,failed=0,0
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1; print("PASS "..name)
    else failed=failed+1; print("FAIL "..name..": "..tostring(err)) end
end
local function upvalue(fn,name)
    for i=1,40 do
        local key,value=debug.getupvalue(fn,i)
        if not key then break end
        if key==name then return value end
    end
    error("canonical server upvalue missing: "..name)
end
local function fixture(file,enemyCooldown)
    local h=Harness.new(file)
    local player=h:addPlayer(h:newPlayer())
    local heartbeat=assert(h.runService.Heartbeat.listeners[1]).fn
    local sessions=upvalue(heartbeat,"sessions")
    local simulate=upvalue(heartbeat,"simulate")
    local addEntity=upvalue(simulate,"addEntity")
    local state=assert(sessions[player])
    state.productionTimer=100
    state.waveBreak=100
    local ally=assert(addEntity(state,"pon","ally"))
    local enemy=assert(addEntity(state,"junk","enemy"))
    ally.x=state.x; ally.z=0; ally.cooldown=100
    enemy.x=state.x; enemy.z=3; enemy.cooldown=enemyCooldown
    local bar=assert(ally.model:FindFirstChild("HealthBar"))
    assert(bar.Size.X==3.2,"fixture starts with full PON bar")
    h.runService.Heartbeat:Fire(0.12)
    return ally,bar
end
local function near(a,b,label)
    assert(math.abs(a-b)<0.000001,label..": expected "..tostring(b)..", got "..tostring(a))
end
check("JUNK damage immediately updates earlier-processed PON health bar",function()
    local ally,bar=fixture(server,0)
    assert(ally.health==34,"one JUNK attack should reduce PON HP from 40 to 34")
    near(bar.Size.X,3.2*34/40,"same-step health bar width")
end)
check("no attack leaves PON health bar unchanged",function()
    local ally,bar=fixture(server,1)
    assert(ally.health==40,"cooling-down JUNK must not damage PON")
    near(bar.Size.X,3.2,"undamaged health bar width")
end)
local pinned=".qa/server-before/src/ToyWarsServer.server.lua"
local file=io.open(pinned,"rb")
if file then
    file:close()
    check("pinned old canonical server reproduces one-tick stale health bar",function()
        local ally,bar=fixture(pinned,0)
        assert(ally.health==34,"old source must still apply combat damage")
        near(bar.Size.X,3.2,"old source stale width")
    end)
end
print(string.format("AUTO_HEALTH_BAR_SUMMARY %d passed / %d failed; canonical whole-server mock",passed,failed))
if failed>0 then os.exit(1) end
