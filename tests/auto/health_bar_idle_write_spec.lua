-- Whole canonical server: health bar geometry is updated only when health changes.
-- Native Lua harness; no engine, renderer, networking or device evidence.
local Harness=dofile("tests/roblox_server_harness.lua")
local server=os.getenv("TWF_SERVER_FILE") or "src/ToyWarsServer.server.lua"
local passed,failed=0,0
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
local function eq(a,b,name)
    assert(a==b,name..": expected "..tostring(b)..", got "..tostring(a))
end
local function upvalue(fn,name)
    for i=1,40 do
        local key,value=debug.getupvalue(fn,i)
        if not key then break end
        if key==name then return value end
    end
    error("canonical server upvalue missing: "..name)
end
local function fixture(file)
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
    local allyBar=assert(ally.model:FindFirstChild("HealthBar"))
    local enemyBar=assert(enemy.model:FindFirstChild("HealthBar"))
    return h,state,ally,enemy,allyBar,enemyBar
end
local function observe(h,allyBar,enemyBar)
    local mt=assert(getmetatable(allyBar))
    local original=assert(mt.__newindex)
    local writes={}
    mt.__newindex=function(obj,key,value)
        if key=="Size" and (obj==allyBar or obj==enemyBar) then
            writes[#writes+1]={bar=obj,width=value.X}
        end
        return original(obj,key,value)
    end
    local ok,err=pcall(function() h.runService.Heartbeat:Fire(0.12) end)
    mt.__newindex=original
    if not ok then error(err) end
    return writes
end
check("full-health moving toys do not reassign identical health bar sizes",function()
    local h,state,ally,enemy,allyBar,enemyBar=fixture(server)
    for tick=1,3 do
        local writes=observe(h,allyBar,enemyBar)
        eq(#writes,0,"redundant bar writes on tick "..tick)
        eq(allyBar.Size.X,3.2,"ally bar stays full")
        eq(enemyBar.Size.X,3.2,"enemy bar stays full")
    end
    assert(ally.alive and enemy.alive,"fixture entities remain alive")
end)
check("one damage event changes only the damaged bar on the same step",function()
    local h,state,ally,enemy,allyBar,enemyBar=fixture(server)
    ally.x=state.x;ally.z=0;ally.cooldown=100
    enemy.x=state.x;enemy.z=3;enemy.cooldown=0
    local writes=observe(h,allyBar,enemyBar)
    eq(ally.health,34,"one enemy attack")
    eq(#writes,1,"one damaged bar write")
    eq(writes[1].bar,allyBar,"only target bar changed")
    assert(math.abs(allyBar.Size.X-3.2*34/40)<0.000001,"same-step damage width")
    eq(#observe(h,allyBar,enemyBar),0,"no repeated write while cooldown active")
    enemy.cooldown=0
    writes=observe(h,allyBar,enemyBar)
    eq(ally.health,28,"second enemy attack")
    eq(#writes,1,"second damage changes bar once")
    assert(math.abs(allyBar.Size.X-3.2*28/40)<0.000001,"second damage width")
end)
local old=os.getenv("TWF_OLD_SERVER_FILE") or ".qa/server-before/src/ToyWarsServer.server.lua"
local fh=io.open(old,"rb")
if fh then
    local contents=fh:read("*a");fh:close()
    if contents:find("bar.Size=Vector3.new(3.2*math.max",1,true) then
        check("pinned old whole server redundantly writes unchanged bar size",function()
            local h,state,ally,enemy,allyBar,enemyBar=fixture(old)
            assert(#observe(h,allyBar,enemyBar)>=2,"old server should write both full bars")
        end)
    end
end
print(string.format("AUTO_HEALTH_BAR_STABILITY_SUMMARY %d passed / %d failed; canonical whole-server Lua mock",passed,failed))
if failed>0 then os.exit(1) end
