-- Refresh/final-save interleaving against the real canonical server script.
-- This is not real Roblox two-server execution.
local H=dofile("tests/roblox_server_harness.lua")
local path="src/ToyWarsServer.server.lua"
local oldHead="9399dee1ee5d8e70085fadef66d48cf5a75ddea1"
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
    local store={data={["p:1"]={version=1,coins=200,wave=2,defeated=3,factoryLevel=1,revision=0}},writes=0,cancels=0,failRefresh=false}
    function store:GetAsync(key)
        local snapshot=copy(self.data[key])
        if delay then coroutine.yield(0.1) end
        return snapshot
    end
    function store:UpdateAsync(key,callback)
        self.writes=self.writes+1
        if self.failRefresh and self.writes==2 then
            self.failRefresh=false
            error("injected transient refresh failure")
        end
        local updated=callback(copy(self.data[key]))
        if not updated then self.cancels=self.cancels+1;return nil end
        self.data[key]=updated
        return copy(updated)
    end
    return store
end
local function fixture(store,source,clock)
    local original=loadfile
    _G.loadfile=function(file,mode,env)
        if file==path and env then
            if clock then env.os.time=function() return clock.value end end
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

-- UpdateAsync transforms never yield. Only simulated service response latency
-- is injected here, with a per-call ordinal captured before suspension.
local function runRace(refreshDelay,finalDelay,refreshCommitsBeforeResponse,source,foreign)
    local store=newStore(false)
    local original=store.UpdateAsync
    local calls=0
    function store:UpdateAsync(key,callback)
        calls=calls+1
        local request=calls
        if request==2 then
            if refreshCommitsBeforeResponse then
                local result=original(self,key,callback)
                coroutine.yield(refreshDelay)
                return result
            end
            coroutine.yield(refreshDelay)
        elseif request==3 then
            coroutine.yield(finalDelay)
        end
        return original(self,key,callback)
    end
    local clock={value=1000}
    local h=fixture(store,source,clock)
    local p=h:addPlayer(h:newPlayer())
    coins(p).Value=350
    clock.value=1050
    h.runService.Heartbeat:Fire(0.2)
    eq(calls,2,"refresh request started")
    h:removePlayer(p)
    eq(calls,3,"final save request started")
    if foreign then
        store.data["p:1"].sessionOwner="foreign-session"
        store.data["p:1"].revision=9
    end
    h:advance(math.max(refreshDelay,finalDelay)+0.02)
    return store,h
end
local function noFalseLoss(h)
    for _,warning in ipairs(h.warnings) do
        assert(warning[1]~="TWF: progress lease ownership lost for",
            "own final save must not report foreign takeover")
    end
end
check("pending refresh cannot invalidate final earned progress",function()
    local store,h=runRace(0.1,0.2,false,nil,false)
    eq(store.data["p:1"].coins,350,"earned coins")
    eq(store.data["p:1"].sessionOwner,nil,"owner released")
    eq(store.data["p:1"].revision,1,"one final revision")
    noFalseLoss(h)
end)
check("refresh commit with delayed response permits same-owner final save",function()
    local store,h=runRace(0.2,0.1,true,nil,false)
    eq(store.data["p:1"].coins,350,"earned coins")
    eq(store.data["p:1"].sessionOwner,nil,"owner released")
    eq(store.data["p:1"].revision,1,"one final revision")
    noFalseLoss(h)
end)
check("final save completing first ignores late refresh response",function()
    local store,h=runRace(0.2,0.1,false,nil,false)
    eq(store.data["p:1"].coins,350,"earned coins")
    eq(store.data["p:1"].sessionOwner,nil,"owner released")
    noFalseLoss(h)
end)
check("foreign owner and revision still reject final save",function()
    local store=runRace(0.1,0.2,false,nil,true)
    eq(store.data["p:1"].coins,200,"foreign progress protected")
    eq(store.data["p:1"].sessionOwner,"foreign-session","foreign owner protected")
    eq(store.data["p:1"].revision,9,"foreign revision protected")
end)
check("negative control pinned9399 loses final save after refresh",function()
    local store=runRace(0.1,0.2,false,oldSource(),false)
    eq(store.data["p:1"].coins,200,"old source loses earned coins")
    assert(store.data["p:1"].sessionOwner~=nil,"old source leaves lease")
end)
check("negative control pinned9399 rejects same-owner refreshed lease",function()
    local store=runRace(0.2,0.1,true,oldSource(),false)
    eq(store.data["p:1"].coins,200,"old source rejects own lease extension")
end)
print(string.format("AUTO_PROGRESS_REFRESH_SAVE_RACE_SUMMARY %d passed / %d failed; canonical whole-server mock",passed,failed))
if failed>0 then os.exit(1) end
