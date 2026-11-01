-- Canonical full-server failure-path regressions. Offline mocks only, not Roblox engine.
-- Pinned PR94 old head is a negative control for both unsafe behaviors.
local H=dofile("tests/roblox_server_harness.lua")
local path="src/ToyWarsServer.server.lua"
local oldHead="09abf3753bdfc9753a45004048b95a17afb311f4"
local passed,failed,serial=0,0,0
local function eq(a,b,label)
    assert(a==b,(label or "value")..": expected "..tostring(b)..", got "..tostring(a))
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
local function profile(coins)
    return {version=1,coins=coins,wave=2,defeated=3,factoryLevel=1,revision=0}
end
local function storeFixture()
    local store={data={["p:1"]=profile(200)},writes=0,finalAttempts=0,
        failRead=false,failFinalOnce=false,failFinalAlways=false,ids={123},meta={keep="yes"}}
    function store:GetAsync(key)
        if self.failRead then error("injected read failure") end
        return self.data[key]
    end
    function store:UpdateAsync(key,callback)
        self.writes=self.writes+1
        if self.writes>=2 then
            self.finalAttempts=self.finalAttempts+1
            if self.failFinalAlways or (self.failFinalOnce and self.finalAttempts==1) then
                error("injected transient final save failure")
            end
        end
        local current=self.data[key]
        local info=current and {
            GetUserIds=function() return self.ids end,
            GetMetadata=function() return self.meta end
        } or nil
        local updated,ids,meta=callback(current,info)
        if updated==nil then return nil end
        self.data[key]=updated
        if ids then self.ids=ids end
        if meta then self.meta=meta end
        return updated
    end
    return store
end
local function oldSource()
    local pipe=assert(io.popen("git show "..oldHead..":src/ToyWarsServer.server.lua 2>/dev/null","r"))
    local source=pipe:read("*a")
    assert(pipe:close() and #source>30000,"pinned current-head negative control required")
    return source
end
local function fixture(store,source)
    local original=loadfile
    _G.loadfile=function(file,mode,env)
        if file==path and env then
            local getService=env.game.GetService
            env.game.GetService=function(self,name)
                if name=="DataStoreService" then
                    return {GetDataStore=function() return store end}
                end
                if name=="HttpService" then
                    return {GenerateGUID=function()
                        serial=serial+1;return "failure-path-guid-"..tostring(serial)
                    end}
                end
                return getService(self,name)
            end
            if source then return assert(load(source,"@PR94_FAILURE_NEGATIVE","t",env)) end
        end
        if env==nil then return original(file,mode) end
        return original(file,mode,env)
    end
    local ok,h=pcall(H.new,path)
    _G.loadfile=original
    assert(ok,h)
    return h
end
local function coins(p)
    return assert(assert(p:FindFirstChild("leaderstats")):FindFirstChild("Coins"))
end
check("read failure refuses gameplay and releases workshop",function()
    local store=storeFixture();store.failRead=true;store.data["p:1"]=profile(500)
    local h=fixture(store);local p=h:addPlayer(h:newPlayer())
    assert(not p:FindFirstChild("leaderstats"),"no unsavable session")
    eq(h:mapCount(),0,"workshop released")
    eq(store.writes,0,"read error must not claim")
    eq(store.data["p:1"].coins,500,"previous save intact")
    assert(#h.warnings>0,"failure must be observable")
end)
check("unknown schema refuses gameplay without overwriting",function()
    local store=storeFixture();store.data["p:1"]={version=2,coins=900}
    local h=fixture(store);local p=h:addPlayer(h:newPlayer())
    assert(not p:FindFirstChild("leaderstats"),"unknown schema must not start")
    eq(h:mapCount(),0,"workshop released")
    eq(store.writes,0,"no claim")
    eq(store.data["p:1"].version,2,"schema preserved")
end)
check("transient final save retries and releases session owner",function()
    local store=storeFixture();store.failFinalOnce=true
    local h=fixture(store);local p=h:addPlayer(h:newPlayer())
    coins(p).Value=350
    h:removePlayer(p)
    eq(store.data["p:1"].coins,200,"first final attempt failed")
    h:advance(0.3)
    eq(store.finalAttempts,2,"bounded second attempt")
    eq(store.data["p:1"].coins,350,"earned coins saved")
    eq(store.data["p:1"].revision,1,"revision incremented exactly once")
    eq(store.data["p:1"].sessionOwner,nil,"owner released")
    eq(store.ids[1],123,"user IDs retained")
    eq(store.meta.keep,"yes","metadata retained")
    assert(#h.warnings>=1,"transient failure logged")
end)
check("exhausted final save retries are bounded and observable",function()
    local store=storeFixture();store.failFinalAlways=true
    local h=fixture(store);local p=h:addPlayer(h:newPlayer())
    coins(p).Value=350;h:removePlayer(p);h:advance(0.6)
    eq(store.finalAttempts,3,"bounded attempts")
    eq(store.data["p:1"].coins,200,"no false save")
    assert(store.data["p:1"].sessionOwner~=nil,"lease retained until recovery")
    assert(#h.warnings>=4,"attempts and terminal failure logged")
end)
check("negative control: old PR94 head permits unsavable read-failure play",function()
    local store=storeFixture();store.failRead=true;store.data["p:1"]=profile(500)
    local h=fixture(store,oldSource());local p=h:addPlayer(h:newPlayer())
    eq(coins(p).Value,50,"old source default despite saved coins")
    h:removePlayer(p)
    eq(store.data["p:1"].coins,500,"old source never saves earned coins")
end)
check("negative control: old PR94 head loses once-failed final save",function()
    local store=storeFixture();store.failFinalOnce=true
    local h=fixture(store,oldSource());local p=h:addPlayer(h:newPlayer())
    coins(p).Value=350;h:removePlayer(p);h:advance(0.6)
    eq(store.finalAttempts,1,"old source never retries")
    eq(store.data["p:1"].coins,200,"old source loses earned coins")
end)
print(string.format("AUTO_PROGRESS_FAILURE_PATHS_SUMMARY %d passed / %d failed; canonical whole-server mock",passed,failed))
if failed>0 then os.exit(1) end
