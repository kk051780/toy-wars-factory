-- Two real canonical-server fixtures sharing one atomic DataStore mock.
-- This is not real Roblox two-server execution.
local H=dofile("tests/roblox_server_harness.lua")
local path="src/ToyWarsServer.server.lua"
local oldHead="259b51e2ef3d84b02b6442dae53f56292b8bae28"
local passed,failed,serial=0,0,0
local function eq(a,b,label) assert(a==b,(label or "value")..": expected "..tostring(b)..", got "..tostring(a)) end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
local function copy(record)
    if not record then return nil end
    local out={};for k,v in pairs(record) do out[k]=v end;return out
end
local function newStore(delay)
    local store={data={["p:1"]={version=1,coins=200,wave=2,defeated=3,factoryLevel=1,revision=0}},writes=0,cancels=0}
    function store:GetAsync(key)
        local snapshot=copy(self.data[key])
        if delay then coroutine.yield(0.1) end
        return snapshot
    end
    function store:UpdateAsync(key,callback)
        self.writes=self.writes+1
        local updated=callback(copy(self.data[key]))
        if not updated then self.cancels=self.cancels+1;return nil end
        self.data[key]=updated
        return copy(updated)
    end
    return store
end
local function fixture(store,source)
    local original=loadfile
    _G.loadfile=function(file,mode,env)
        if file==path and env then
            local getService=env.game.GetService
            env.game.GetService=function(self,name)
                if name=="DataStoreService" then return {GetDataStore=function() return store end} end
                if name=="HttpService" then return {GenerateGUID=function()
                    serial=serial+1;return "claim-race-guid-"..tostring(serial)
                end} end
                return getService(self,name)
            end
            if source then return assert(load(source,"@PR94_OLD","t",env)) end
        end
        if env==nil then return original(file,mode) end
        return original(file,mode,env)
    end
    local ok,h=pcall(H.new,path);_G.loadfile=original;assert(ok,h);return h
end
local function coins(p) return assert(assert(p:FindFirstChild("leaderstats")):FindFirstChild("Coins")) end
local function oldSource()
    local pipe=assert(io.popen("git show "..oldHead..":src/ToyWarsServer.server.lua 2>/dev/null","r"))
    local source=pipe:read("*a");assert(pipe:close() and #source>27000,"pinned old head required")
    return source
end
check("concurrent GetAsync snapshots: B waits then loads A final save",function()
    local store=newStore(true)
    local a=fixture(store);local pa=a:addPlayer(a:newPlayer())
    local b=fixture(store);local pb=b:addPlayer(b:newPlayer())
    assert(not pa:FindFirstChild("leaderstats") and not pb:FindFirstChild("leaderstats"),"both reads pending")
    a:advance(0.1);b:advance(0.1)
    assert(not pb:FindFirstChild("leaderstats"),"B cannot play unsavable")
    coins(pa).Value=300;a:removePlayer(pa)
    b:advance(0.6);eq(coins(pb).Value,300,"B restores A")
    coins(pb).Value=500;b:removePlayer(pb)
    eq(store.data["p:1"].coins,500,"B save")
end)
check("unsaved A protected; B can spend coins after handoff",function()
    local store=newStore(false)
    local a=fixture(store);local pa=a:addPlayer(a:newPlayer());coins(pa).Value=300
    local b=fixture(store);local pb=b:addPlayer(b:newPlayer())
    assert(not pb:FindFirstChild("leaderstats"),"B waits")
    a:removePlayer(pa);b:advance(0.6);eq(coins(pb).Value,300,"A saved")
    coins(pb).Value=150;b:removePlayer(pb)
    eq(store.data["p:1"].coins,150,"purchases decrease coins")
end)
check("timeout refuses unsavable B; reconnect after A final save works",function()
    local store=newStore(false)
    local a=fixture(store);local pa=a:addPlayer(a:newPlayer())
    local b=fixture(store);local pb=b:addPlayer(b:newPlayer())
    b:advance(2.1)
    assert(not pb:FindFirstChild("leaderstats"),"B blocked")
    eq(b:mapCount(),0,"B plot released")
    coins(pa).Value=320;a:removePlayer(pa)
    local c=fixture(store);local pc=c:addPlayer(c:newPlayer())
    eq(coins(pc).Value,320,"later reconnect")
end)
check("negative control: pinned old head starts B with unsavable defaults",function()
    local store=newStore(true);local source=oldSource()
    local a=fixture(store,source);local pa=a:addPlayer(a:newPlayer())
    local b=fixture(store,source);local pb=b:addPlayer(b:newPlayer())
    a:advance(0.1);b:advance(0.1)
    eq(coins(pb).Value,50,"old B default")
    coins(pb).Value=500;b:removePlayer(pb)
    coins(pa).Value=300;a:removePlayer(pa)
    eq(store.data["p:1"].coins,300,"old B lost progress")
end)
print(string.format("AUTO_PROGRESS_CLAIM_RACE_SUMMARY %d passed / %d failed; canonical whole-server mock",passed,failed))
if failed>0 then os.exit(1) end
