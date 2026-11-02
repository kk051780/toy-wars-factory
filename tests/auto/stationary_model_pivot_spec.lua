-- Canonical whole-server regression: stationary toy models should not PivotTo each tick.
-- Lua 5.4 mock only; does not establish Roblox renderer/device frame-time gains.
local Harness=dofile("tests/roblox_server_harness.lua")
local server=os.getenv("TWF_SERVER_FILE") or "src/ToyWarsServer.server.lua"
local passed,failed=0,0
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
local function upvalue(fn,name)
    for i=1,40 do
        local key,value=debug.getupvalue(fn,i)
        if not key then break end
        if key==name then return value end
    end
    error("canonical server upvalue missing: "..name)
end
local function fixture(file,withEnemy)
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
    local enemy
    if withEnemy then
        enemy=assert(addEntity(state,"junk","enemy"))
        ally.x=state.x;ally.z=0;ally.cooldown=100
        enemy.x=state.x;enemy.z=3;enemy.cooldown=100
    end
    return h,state,ally,enemy
end
local function tick(h) h.runService.Heartbeat:Fire(0.12) end
check("stationary combat models are not pivoted on repeated Heartbeats",function()
    local h,state,ally,enemy=fixture(server,true)
    tick(h) -- First update applies the fixture's manual relocation.
    local ap,ep=ally.model._pivotCount,enemy.model._pivotCount
    assert(ap==2 and ep==2,"initial placement plus one relocation")
    for n=1,4 do
        tick(h)
        assert(ally.model._pivotCount==ap,"ally idle PivotTo at tick "..n)
        assert(enemy.model._pivotCount==ep,"enemy idle PivotTo at tick "..n)
    end
    assert(ally.alive and enemy.alive,"both units remain alive")
end)
check("a changed position pivots exactly once and keeps the new world position",function()
    local h,state,ally,enemy=fixture(server,true)
    tick(h)
    local before=ally.model._pivotCount
    local enemyBefore=enemy.model._pivotCount
    ally.x=ally.x+1
    tick(h)
    assert(ally.model._pivotCount==before+1,"moved ally must pivot once")
    assert(ally.model._lastPivot.Position.X==ally.x,"rendered position must follow movement")
    assert(enemy.model._pivotCount==enemyBefore,"stationary enemy must not pivot")
    tick(h)
    assert(ally.model._pivotCount==before+1,"same position must not pivot again")
end)
check("normal travel still updates model position",function()
    local h,state,ally=fixture(server,false)
    local before=ally.model._pivotCount
    local z=ally.z
    tick(h)
    assert(ally.z>z,"ally must advance toward the enemy portal")
    assert(ally.model._pivotCount==before+1,"moving ally must pivot")
    assert(ally.model._lastPivot.Position.Z==ally.z,"pivot must track the new Z")
end)
local old=os.getenv("TWF_OLD_SERVER_FILE") or ".qa/server-before/src/ToyWarsServer.server.lua"
local file=io.open(old,"rb")
if file then
    file:close()
    check("pinned old whole server reproduces redundant stationary PivotTo",function()
        local h,state,ally,enemy=fixture(old,true)
        tick(h)
        local before=ally.model._pivotCount
        tick(h)
        assert(ally.model._pivotCount==before+1,"old server should re-pivot idle ally")
    end)
end
print(string.format("AUTO_STATIONARY_PIVOT_SUMMARY %d passed / %d failed; canonical whole-server Lua mock",passed,failed))
if failed>0 then os.exit(1) end
