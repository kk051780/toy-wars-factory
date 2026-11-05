-- Whole canonical server: skip idle HealthBar searches; not an engine/device test.
local Harness=dofile("tests/roblox_server_harness.lua")
local server=os.getenv("TWF_SERVER_FILE") or "src/ToyWarsServer.server.lua"
local passed,failed=0,0
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
local function upvalue(fn,name)
    for i=1,50 do
        local key,value=debug.getupvalue(fn,i)
        if not key then break end
        if key==name then return value end
    end
    error("missing canonical upvalue: "..name)
end
local function fixture(file,withEnemy)
    local h=Harness.new(file)
    local player=h:addPlayer(h:newPlayer())
    local heartbeat=assert(h.runService.Heartbeat.listeners[1]).fn
    local simulate=upvalue(heartbeat,"simulate")
    local state=assert(upvalue(heartbeat,"sessions")[player])
    local addEntity=upvalue(simulate,"addEntity")
    state.productionTimer=100;state.waveBreak=100
    local ally=assert(addEntity(state,"pon","ally"))
    local enemy
    if withEnemy then
        enemy=assert(addEntity(state,"junk","enemy"))
        ally.x=state.x;ally.z=0;ally.cooldown=100
        enemy.x=state.x;enemy.z=3;enemy.cooldown=100
    end
    return h,ally,enemy
end
local function observe(h,ally,enemy)
    local mt=assert(getmetatable(ally.model))
    local original=assert(mt.__index)
    local reads={ally=0,enemy=0}
    mt.__index=function(obj,key)
        local member=original(obj,key)
        if key~="FindFirstChild" then return member end
        return function(self,name)
            if name=="HealthBar" then
                if self==ally.model then reads.ally=reads.ally+1 end
                if enemy and self==enemy.model then reads.enemy=reads.enemy+1 end
            end
            return member(self,name)
        end
    end
    local ok,err=pcall(function() h.runService.Heartbeat:Fire(0.12) end)
    mt.__index=original
    if not ok then error(err) end
    return reads
end
check("two healthy stationary combatants avoid repeated HealthBar searches",function()
    local h,ally,enemy=fixture(server,true)
    for tick=1,4 do
        local reads=observe(h,ally,enemy)
        assert(reads.ally==0 and reads.enemy==0,"idle search tick "..tick)
    end
    assert(ally.health==40 and enemy.health==38,"no attacks during cooldown")
end)
check("one damage hit updates victim HealthBar in same tick only",function()
    local h,ally,enemy=fixture(server,true)
    enemy.cooldown=0
    local bar=assert(ally.model:FindFirstChild("HealthBar"))
    local reads=observe(h,ally,enemy)
    assert(ally.health==34,"JUNK should deal six damage")
    assert(reads.ally==1 and reads.enemy==0,"only victim bar should be searched")
    assert(math.abs(bar.Size.X-3.2*34/40)<0.000001,"bar must update immediately")
    reads=observe(h,ally,enemy)
    assert(reads.ally==0 and reads.enemy==0,"cooldown step should not search")
end)
check("moving healthy ally avoids HealthBar search",function()
    local h,ally=fixture(server,false)
    local before=ally.z
    local reads=observe(h,ally,nil)
    assert(ally.z>before,"canonical travel must continue")
    assert(reads.ally==0,"movement should not search HealthBar")
end)
local old=os.getenv("TWF_OLD_SERVER_FILE") or ".qa/server-before/src/ToyWarsServer.server.lua"
local f=io.open(old,"rb")
if f then
    local contents=f:read("*a");f:close()
    if contents:find("refreshHealthBar(e)",1,true) then
        check("compatible pinned old server reproduces idle searches",function()
            local h,ally,enemy=fixture(old,true)
            local reads=observe(h,ally,enemy)
            assert(reads.ally>=1 and reads.enemy>=1,"old source should search both bars")
        end)
    end
end
print(string.format("AUTO_HEALTH_BAR_LOOKUP_SUMMARY %d passed / %d failed; canonical whole-server mock",passed,failed))
if failed>0 then os.exit(1) end
