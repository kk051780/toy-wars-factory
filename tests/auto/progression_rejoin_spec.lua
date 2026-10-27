-- Execute the complete canonical server with an injected versioned DataStore service.
-- Offline Lua only: no actual Roblox DataStore, engine, or network is exercised.
local H = dofile("tests/roblox_server_harness.lua")
local server = os.getenv("TWF_SERVER_FILE") or "src/ToyWarsServer.server.lua"
local passed, failed = 0, 0
local guidSerial = 0
local function eq(a,b,label)
    assert(a==b,(label or "value")..": expected "..tostring(b)..", got "..tostring(a))
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
local function newStore()
    local store={data={},reads=0,writes=0,failRead=false,failWrite=false,delayRead=0}
    function store:GetAsync(key)
        self.reads=self.reads+1
        if self.delayRead>0 then coroutine.yield(self.delayRead) end
        if self.failRead then error("injected read failure") end
        return self.data[key]
    end
    function store:UpdateAsync(key,callback)
        self.writes=self.writes+1
        if self.failWrite then error("injected write failure") end
        local value=callback(self.data[key])
        self.data[key]=value
        return value
    end
    return store
end
local function fixture(store)
    local original=loadfile
    local callbacks={}
    _G.loadfile=function(path,mode,env)
        if path==server and env then
            local originalGetService=env.game.GetService
            env.game.GetService=function(self,name)
                if name=="DataStoreService" then
                    return {GetDataStore=function(_,storeName)
                        eq(storeName,"ToyWarsProgressV1","versioned store")
                        return store
                    end}
                end
            if name=="HttpService" then
                return {GenerateGUID=function()
                    guidSerial=guidSerial+1
                    return "offline-session-guid-"..tostring(guidSerial)
                end}
            end
                return originalGetService(self,name)
            end
            env.game.BindToClose=function(_,fn) callbacks[#callbacks+1]=fn end
        end
        if env==nil then return original(path,mode) end
        return original(path,mode,env)
    end
    local ok,h=pcall(H.new,server)
    _G.loadfile=original
    assert(ok,h)
    return h,callbacks
end
local function value(p,folder,key)
    return assert(assert(p:FindFirstChild(folder)):FindFirstChild(key)).Value
end
check("new profile starts with canonical defaults and writes version one",function()
    local store=newStore()
    local h=fixture(store)
    local p=h:addPlayer(h:newPlayer())
    eq(value(p,"leaderstats","Coins"),50,"new coins")
    eq(value(p,"leaderstats","Wave"),1,"new wave")
    h:removePlayer(p)
    eq(store.writes,2,"atomic session claim plus final save")
    eq(store.data["p:1"].version,1,"version")
    eq(store.data["p:1"].factoryLevel,1,"level")
end)
check("earned progress survives leave and rejoin",function()
    local store=newStore()
    local h=fixture(store)
    local p=h:addPlayer(h:newPlayer())
    p:FindFirstChild("leaderstats"):FindFirstChild("Coins").Value=137
    p:FindFirstChild("leaderstats"):FindFirstChild("Wave").Value=4
    p:FindFirstChild("leaderstats"):FindFirstChild("Defeated").Value=9
    h:status(p,"FactoryLevel").Value=3
    h:removePlayer(p)
    local h2=fixture(store)
    local again=h2:addPlayer(h2:newPlayer())
    eq(value(again,"leaderstats","Coins"),137,"rejoined coins")
    eq(value(again,"leaderstats","Wave"),4,"rejoined wave")
    eq(value(again,"leaderstats","Defeated"),9,"rejoined kills")
    eq(h2:status(again,"FactoryLevel").Value,3,"rejoined factory")
end)
check("unrecognized version is not silently overwritten by defaults",function()
    local store=newStore()
    store.data["p:1"]={version=2,coins=500,wave=3,defeated=4,factoryLevel=2}
    local h=fixture(store)
    local p=h:addPlayer(h:newPlayer())
    eq(value(p,"leaderstats","Coins"),50,"safe fallback")
    h:removePlayer(p)
    eq(store.writes,0,"invalid record not overwritten")
    eq(store.data["p:1"].version,2,"existing version retained")
end)
check("read failure allows play but never overwrites prior save",function()
    local store=newStore()
    store.data["p:1"]={version=1,coins=500,wave=3,defeated=4,factoryLevel=2}
    store.failRead=true
    local h=fixture(store)
    local p=h:addPlayer(h:newPlayer())
    eq(value(p,"leaderstats","Coins"),50,"fallback")
    h:removePlayer(p)
    eq(store.writes,0,"failed read not saved")
    eq(store.data["p:1"].coins,500,"prior coins preserved")
end)
check("disconnect while read yields frees slot without a ghost plot",function()
    local store=newStore();store.delayRead=0.2
    local h=fixture(store)
    local p=h:addPlayer(h:newPlayer())
    assert(not p:FindFirstChild("leaderstats"),"load must still be pending")
    h:removePlayer(p)
    h:advance(0.3)
    eq(h:mapCount(),0,"no orphan plot")
    assert(not p:FindFirstChild("leaderstats"),"disconnected player must not initialize")
    eq(store.writes,0,"pending load not saved")
end)
check("write failure leaves slot free and emits warning",function()
    local store=newStore();store.failWrite=true
    local h=fixture(store)
    local p=h:addPlayer(h:newPlayer())
    h:removePlayer(p)
    eq(h:mapCount(),0,"plot released")
    assert(#h.warnings>=1,"write failure must be observable")
end)
check("server close saves active player with current values",function()
    local store=newStore()
    local h,callbacks=fixture(store)
    local p=h:addPlayer(h:newPlayer())
    eq(#callbacks,1,"shutdown hook")
    p:FindFirstChild("leaderstats"):FindFirstChild("Coins").Value=271
    callbacks[1]()
    eq(store.data["p:1"].coins,271,"shutdown snapshot")
end)
print(string.format("AUTO_PROGRESS_REJOIN_SUMMARY %d passed / %d failed; whole-server Lua mock",passed,failed))
if failed>0 then os.exit(1) end
