-- Canonical complete-server UpdateAsync interleaving regression, not live Roblox DataStore.
-- Negative controls execute the immutable PR94 pre-review server source from Git history.
local H = dofile("tests/roblox_server_harness.lua")
local server = "src/ToyWarsServer.server.lua"
local oldHead = "aeb60a50aa9ca4eaf64cb636e113ab562d05b6bb"
local passed, failed = 0, 0
local guidSerial = 0
local function eq(actual, expected, label)
    assert(actual == expected, (label or "value")..": expected "..tostring(expected)..", got "..tostring(actual))
end
local function check(name, fn)
    local ok, err = pcall(fn)
    if ok then passed = passed + 1; print("PASS "..name)
    else failed = failed + 1; print("FAIL "..name..": "..tostring(err)) end
end
local function profile(coins, revision)
    return {version=1,coins=coins,wave=2,defeated=3,factoryLevel=1,revision=revision}
end
local function storeFixture()
    local store={data={},writes=0,commits=0,cancels=0,ids={},metadata={},retry=nil}
    function store:GetAsync(key) return self.data[key] end
    function store:UpdateAsync(key, callback)
        self.writes=self.writes+1
        local function info()
            if self.data[key]==nil then return nil end
            return {
                GetUserIds=function() return self.ids[key] end,
                GetMetadata=function() return self.metadata[key] end,
            }
        end
        local updated, ids, metadata = callback(self.data[key], info())
        if self.retry then
            self.retry(self,key)
            updated, ids, metadata = callback(self.data[key], info())
        end
        if updated==nil then self.cancels=self.cancels+1;return nil end
        self.data[key]=updated
        if ids~=nil then self.ids[key]=ids end
        if metadata~=nil then self.metadata[key]=metadata end
        self.commits=self.commits+1
        return updated
    end
    return store
end
local function fixture(store, oldSource)
    local original=loadfile
    _G.loadfile=function(path,mode,env)
        if path==server and env then
            local getService=env.game.GetService
            env.game.GetService=function(self,name)
                if name=="DataStoreService" then
                    return {GetDataStore=function(_,storeName)
                        eq(storeName,"ToyWarsProgressV1","store")
                        return store
                    end}
                end
            if name=="HttpService" then
                return {GenerateGUID=function()
                    guidSerial=guidSerial+1
                    return "offline-session-guid-"..tostring(guidSerial)
                end}
            end
                return getService(self,name)
            end
            if oldSource then return assert(load(oldSource,"@PR94_HEAD","t",env)) end
        end
        if env==nil then return original(path,mode) end
        return original(path,mode,env)
    end
    local ok,h=pcall(H.new,server)
    _G.loadfile=original
    assert(ok,h)
    return h
end
local function setCoins(player, coins)
    assert(player:FindFirstChild("leaderstats"):FindFirstChild("Coins")).Value=coins
end
local function getOldSource()
    local command="git show "..oldHead..":src/ToyWarsServer.server.lua 2>/dev/null"
    local pipe=assert(io.popen(command,"r"))
    local source=pipe:read("*a")
    local ok=pipe:close()
    assert(ok and #source>20000,"pinned PR94 head is required for negative controls")
    return source
end
check("schema changed after GetAsync cannot be overwritten",function()
    local store=storeFixture();store.data["p:1"]=profile(200)
    local h=fixture(store);local p=h:addPlayer(h:newPlayer())
    store.data["p:1"]={version=2,coins=900,wave=7,defeated=10,factoryLevel=3}
    setCoins(p,100);h:removePlayer(p)
    eq(store.data["p:1"].version,2,"new schema")
    eq(store.data["p:1"].coins,900,"new coins")
    eq(store.cancels,1,"canceled write")
    assert(#h.warnings>=1,"conflict warning")
end)
check("older server cannot roll back newer session",function()
    local store=storeFixture();store.data["p:1"]=profile(200)
    local older=fixture(store);local a=older:addPlayer(older:newPlayer())
    local newer=fixture(store);local b=newer:addPlayer(newer:newPlayer())
    setCoins(b,500);newer:removePlayer(b)
    eq(store.data["p:1"].revision,1,"newer revision")
    setCoins(a,199);older:removePlayer(a)
    eq(store.data["p:1"].coins,500,"newer coins retained")
    eq(store.cancels,1,"stale canceled")
end)
check("revision rejects same-value competing write",function()
    local store=storeFixture();store.data["p:1"]=profile(200)
    local older=fixture(store);local a=older:addPlayer(older:newPlayer())
    local newer=fixture(store);local b=newer:addPlayer(newer:newPlayer())
    newer:removePlayer(b)
    eq(store.data["p:1"].coins,200,"same value")
    eq(store.data["p:1"].revision,1,"revision set")
    setCoins(a,111);older:removePlayer(a)
    eq(store.data["p:1"].coins,200,"stale same-value writer blocked")
end)
check("successful rejoin advances revision and retains metadata",function()
    local store=storeFixture();store.data["p:1"]=profile(300,4)
    store.data["p:1"].customField="retain"
    store.ids["p:1"]={123,456};store.metadata["p:1"]={label="keep"}
    local h=fixture(store);local p=h:addPlayer(h:newPlayer())
    setCoins(p,320);h:removePlayer(p)
    eq(store.data["p:1"].revision,5,"first revision")
    eq(store.data["p:1"].customField,"retain","record extra field")
    eq(store.ids["p:1"][2],456,"userIds")
    eq(store.metadata["p:1"].label,"keep","metadata")
    local h2=fixture(store);local again=h2:addPlayer(h2:newPlayer())
    eq(again:FindFirstChild("leaderstats"):FindFirstChild("Coins").Value,320,"rejoined coins")
    setCoins(again,350);h2:removePlayer(again)
    eq(store.data["p:1"].revision,6,"second revision")
    eq(store.data["p:1"].coins,350,"second save")
end)
check("UpdateAsync retry rechecks concurrent schema replacement",function()
    local store=storeFixture();store.data["p:1"]=profile(220)
    local h=fixture(store);local p=h:addPlayer(h:newPlayer())
    store.retry=function(self,key)
        self.data[key]={version=2,coins=888,wave=8,defeated=8,factoryLevel=3}
        self.retry=nil
    end
    setCoins(p,450);h:removePlayer(p)
    eq(store.data["p:1"].version,2,"retry schema")
    eq(store.data["p:1"].coins,888,"retry coins")
    eq(store.cancels,1,"retry canceled")
end)
check("negative control: PR94 old head overwrites changed schema",function()
    local store=storeFixture();store.data["p:1"]=profile(200)
    local h=fixture(store,getOldSource());local p=h:addPlayer(h:newPlayer())
    store.data["p:1"]={version=2,coins=900,wave=7,defeated=10,factoryLevel=3}
    setCoins(p,100);h:removePlayer(p)
    eq(store.data["p:1"].version,1,"old source reproduced overwrite")
    eq(store.data["p:1"].coins,100,"old source reproduced rollback")
end)
check("negative control: PR94 old head rolls back newer session",function()
    local store=storeFixture();store.data["p:1"]=profile(200)
    local oldSource=getOldSource()
    local older=fixture(store,oldSource);local a=older:addPlayer(older:newPlayer())
    local newer=fixture(store,oldSource);local b=newer:addPlayer(newer:newPlayer())
    setCoins(b,500);newer:removePlayer(b)
    setCoins(a,199);older:removePlayer(a)
    eq(store.data["p:1"].coins,199,"old stale session overwrite reproduced")
end)
print(string.format("AUTO_PROGRESS_CONFLICT_SUMMARY %d passed / %d failed; canonical whole-server Lua mock",passed,failed))
if failed>0 then os.exit(1) end
