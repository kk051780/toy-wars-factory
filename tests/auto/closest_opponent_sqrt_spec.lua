-- Whole canonical server: nearest opponent is unchanged, sqrt only for the winner.
-- Offline Lua 5.4 mock; no Roblox engine or device frame-time measurement.
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
    error("canonical server upvalue missing: "..name)
end
local function fixture(file)
    local h=Harness.new(file)
    local player=h:addPlayer(h:newPlayer())
    local heartbeat=assert(h.runService.Heartbeat.listeners[1]).fn
    local state=assert(upvalue(heartbeat,"sessions")[player])
    local simulate=upvalue(heartbeat,"simulate")
    local addEntity=upvalue(simulate,"addEntity")
    local updateEntity=upvalue(simulate,"updateEntity")
    local closest=upvalue(updateEntity,"closestOpponent")
    local ally=assert(addEntity(state,"pon","ally"))
    ally.x=state.x;ally.z=0
    local enemies={}
    for i,distance in ipairs({12,8,5,2,7,9}) do
        local enemy=assert(addEntity(state,"junk","enemy"))
        enemy.x=state.x+distance;enemy.z=0
        enemies[i]=enemy
    end
    return state,ally,enemies,closest
end
local function observed(closest,state,ally)
    local original=math.sqrt
    local count=0
    math.sqrt=function(x) count=count+1;return original(x) end
    local ok,target,distance=pcall(closest,state,ally)
    math.sqrt=original
    if not ok then error(target) end
    return target,distance,count
end
check("six enemies select nearest with one square root",function()
    local state,ally,enemies,closest=fixture(server)
    local target,distance,count=observed(closest,state,ally)
    assert(target==enemies[4] and distance==2,"nearest enemy or distance changed")
    assert(count==1,"sqrt count must be one, got "..count)
end)
check("dead and friendly targets are ignored without changing distances",function()
    local state,ally,enemies,closest=fixture(server)
    enemies[4].alive=false
    enemies[3].side="ally"
    local target,distance,count=observed(closest,state,ally)
    assert(target==enemies[5] and distance==7,"wrong eligible nearest enemy")
    assert(count==1,"one sqrt for remaining opponents")
end)
check("no living opponent returns nil and infinity without sqrt",function()
    local state,ally,enemies,closest=fixture(server)
    for _,enemy in ipairs(enemies) do enemy.alive=false end
    local target,distance,count=observed(closest,state,ally)
    assert(target==nil and distance==math.huge,"empty target contract changed")
    assert(count==0,"empty target should not call sqrt")
end)
local old=os.getenv("TWF_OLD_SERVER_FILE") or ".qa/server-before/src/ToyWarsServer.server.lua"
local fh=io.open(old,"rb")
if fh then
    local contents=fh:read("*a");fh:close()
    if contents:find("local d=math.sqrt(dx*dx+dz*dz)",1,true) then
        check("pinned old whole server repeats sqrt for each opponent",function()
            local state,ally,enemies,closest=fixture(old)
            local target,distance,count=observed(closest,state,ally)
            assert(target==enemies[4] and distance==2,"old nearest target changed")
            assert(count==6,"old server should call sqrt six times, got "..count)
        end)
    end
end
print(string.format("AUTO_CLOSEST_OPPONENT_SQRT_SUMMARY %d passed / %d failed; canonical whole-server Lua mock",passed,failed))
if failed>0 then os.exit(1) end
