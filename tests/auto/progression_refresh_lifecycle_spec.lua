-- Canonical whole-server lifecycle regression: a yielding lease refresh must not
-- resume gameplay after departure or a foreign-owner kick. No Roblox engine.
local H=dofile("tests/roblox_server_harness.lua")
local path="src/ToyWarsServer.server.lua"
local pinned="c7227654cd89d665bf8c4d84dbcb966f4881e2f4"
local passed,failed,serial=0,0,0
local function eq(actual,expected,name)
    assert(actual==expected,(name or "value")..": expected "..tostring(expected)..", got "..tostring(actual))
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
local function copy(value)
    if not value then return nil end
    local result={};for k,v in pairs(value) do result[k]=v end
    return result
end
local function newStore(mode)
    local store={data={["p:1"]={version=1,coins=200,wave=2,defeated=3,factoryLevel=1,revision=0}},calls=0}
    function store:GetAsync(key) return copy(self.data[key]) end
    function store:UpdateAsync(key,callback)
        self.calls=self.calls+1
        local ordinal=self.calls
        -- Simulated network latency is OUTSIDE the non-yielding CAS transform.
        if ordinal==2 and mode=="delayed" then coroutine.yield(0.3) end
        if ordinal==2 and mode=="foreign" then
            local other=copy(self.data[key])
            other.sessionOwner="foreign"
            other.revision=other.revision+1
            self.data[key]=other
        end
        local updated=callback(copy(self.data[key]))
        if not updated then return nil end
        self.data[key]=copy(updated)
        return copy(updated)
    end
    return store
end
local function fixture(store,source,clock)
    local original=loadfile
    _G.loadfile=function(file,mode,env)
        if file==path and env then
            env.os.time=function() return clock.value end
            local get=env.game.GetService
            env.game.GetService=function(self,name)
                if name=="DataStoreService" then return {GetDataStore=function() return store end} end
                if name=="HttpService" then return {GenerateGUID=function()
                    serial=serial+1;return "post-refresh-"..tostring(serial)
                end} end
                return get(self,name)
            end
            if source then return assert(load(source,"@PINNED_C7227654","t",env)) end
        end
        if env==nil then return original(file,mode) end
        return original(file,mode,env)
    end
    local ok,h=pcall(H.new,path)
    _G.loadfile=original
    assert(ok,h)
    return h
end
local function models(h)
    local n=0
    local world=assert(h.workspace:FindFirstChild("ToyWarsWorld"))
    for _,child in ipairs(world:GetChildren()) do
        if child.ClassName=="Model" then n=n+1 end
    end
    return n
end
local function coins(p)
    return assert(assert(p:FindFirstChild("leaderstats")):FindFirstChild("Coins"))
end
local function oldSource()
    local p=assert(io.popen("git show "..pinned..":src/ToyWarsServer.server.lua 2>/dev/null","r"))
    local source=p:read("*a")
    assert(p:close() and #source>30000,"pinned c7227654 source required")
    return source
end
local function scenario(mode,source)
    local store=newStore(mode)
    local clock={value=1000}
    local h=fixture(store,source,clock)
    local p=h:addPlayer(h:newPlayer())
    local kicked=0
    p.Kick=function() kicked=kicked+1 end
    local money=coins(p)
    -- Production is almost due, but no toy has been created yet.
    for _=1,3 do h.runService.Heartbeat:Fire(0.3) end
    money.Value=350
    eq(models(h),0,"no pre-existing toy")
    clock.value=1050
    h.runService.Heartbeat:Fire(0.3)
    eq(store.calls,2,"claim and refresh")
    if mode=="delayed" then
        h:removePlayer(p)
        eq(store.calls,3,"final save after departure")
        eq(store.data["p:1"].coins,350,"final save committed")
        h:advance(0.31)
    else
        eq(kicked,1,"foreign ownership kick")
    end
    return {store=store,h=h,money=money,kicked=kicked}
end
check("delayed refresh cannot resume production or income after PlayerRemoving",function()
    local r=scenario("delayed")
    eq(models(r.h),0,"no post-departure model")
    eq(r.money.Value,350,"no post-departure coin mutation")
    eq(r.store.data["p:1"].coins,350,"saved balance")
    eq(r.store.data["p:1"].sessionOwner,nil,"owner released")
end)
check("foreign-owner Kick cannot continue same Heartbeat gameplay",function()
    local r=scenario("foreign")
    eq(models(r.h),0,"no post-kick model")
    eq(r.money.Value,350,"no post-kick coin mutation")
    eq(r.store.data["p:1"].sessionOwner,"foreign","foreign owner protected")
    eq(r.store.data["p:1"].revision,1,"foreign revision protected")
end)
check("pinned c7227654 reproduces post-departure model and coin mutation",function()
    local r=scenario("delayed",oldSource())
    assert(models(r.h)>0,"old server must create a toy after cleanup")
    assert(r.money.Value~=350,"old server must mutate departed coins")
    eq(r.store.data["p:1"].coins,350,"old final save preceded stale simulation")
end)
check("pinned c7227654 reproduces post-kick model and coin mutation",function()
    local r=scenario("foreign",oldSource())
    assert(models(r.h)>0,"old server must create a toy after ownership loss")
    assert(r.money.Value~=350,"old server must mutate kicked coins")
    eq(r.store.data["p:1"].sessionOwner,"foreign","foreign record remains protected")
end)
print(string.format("AUTO_PROGRESS_REFRESH_LIFECYCLE_SUMMARY %d passed / %d failed",passed,failed))
if failed>0 then os.exit(1) end
