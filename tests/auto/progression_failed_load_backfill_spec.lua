-- A failed pending progress load must hand its reserved workshop to a queued player.
-- Full canonical server fixture; no real Roblox/DataStore/phone evidence.
local H=dofile("tests/roblox_server_harness.lua")
local path="src/ToyWarsServer.server.lua"
local pinned="e0db2a6a6a49f79ba0b9a900ffa84b62c30ae6e8"
local passed,failed,serial=0,0,0
local function eq(actual,expected,label)
    assert(actual==expected,(label or "value")..": expected "..tostring(expected)..", got "..tostring(actual))
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
local function newStore(mode)
    local store={data={},writes={}}
    function store:GetAsync(key)
        if key=="p:1" then
            coroutine.yield(0.2)
            if mode=="read_error" then error("injected first-player read failure") end
            if mode=="unknown_schema" then return {version=2,coins=900} end
        end
        return self.data[key]
    end
    function store:UpdateAsync(key,callback)
        self.writes[key]=(self.writes[key] or 0)+1
        local updated=callback(self.data[key])
        if updated~=nil then self.data[key]=updated end
        return updated
    end
    return store
end
local function oldSource()
    local pipe=assert(io.popen("git show "..pinned..":src/ToyWarsServer.server.lua 2>/dev/null","r"))
    local source=pipe:read("*a")
    assert(pipe:close() and #source>30000,"pinned pre-fix canonical source required")
    return source
end
local function fixture(store,source)
    local original=loadfile
    _G.loadfile=function(file,mode,env)
        if file==path and env then
            local getService=env.game.GetService
            env.game.GetService=function(self,name)
                if name=="DataStoreService" then return {GetDataStore=function() return store end} end
                if name=="HttpService" then return {GenerateGUID=function()
                    serial=serial+1;return "failed-load-backfill-"..tostring(serial)
                end} end
                return getService(self,name)
            end
            if source then return assert(load(source,"@PINNED_PRE_FIX","t",env)) end
        end
        if env==nil then return original(file,mode) end
        return original(file,mode,env)
    end
    local ok,h=pcall(H.new,path)
    _G.loadfile=original
    assert(ok,h)
    return h
end
local function scenario(mode,source)
    local store=newStore(mode)
    local h=fixture(store,source)
    local rejected=h:addPlayer(h:newPlayer())
    assert(not rejected:FindFirstChild("leaderstats"),"first read must be pending")
    for _=2,4 do
        local p=h:addPlayer(h:newPlayer())
        assert(p:FindFirstChild("leaderstats"),"other workshops must be active")
    end
    local waiting=h:addPlayer(h:newPlayer())
    eq(h:mapCount(),3,"three active plots plus one reserved loading slot")
    assert(not waiting:FindFirstChild("leaderstats"),"fifth player waits")
    h:advance(0.3)
    return h,store,rejected,waiting
end
local function assertBackfilled(mode)
    local h,store,rejected,waiting=scenario(mode)
    assert(not rejected:FindFirstChild("leaderstats"),"failed load must not create unsavable play")
    eq(store.writes["p:1"] or 0,0,"failed player must not claim or overwrite progress")
    assert(waiting:FindFirstChild("leaderstats"),"waiting player must receive freed plot")
    assert(h:workshop(waiting),"waiting player has workshop")
    eq(h:mapCount(),4,"all four plots active after backfill")
    assert(#h.warnings>0,"load failure must be logged")
end
check("read error frees reserved plot and admits waiting fifth player",function()
    assertBackfilled("read_error")
end)
check("unknown schema is preserved while waiting player receives plot",function()
    assertBackfilled("unknown_schema")
end)
check("negative control: pinned main strands fifth player after failed read",function()
    local h,store,rejected,waiting=scenario("read_error",oldSource())
    assert(not rejected:FindFirstChild("leaderstats"),"failed player blocked")
    assert(not waiting:FindFirstChild("leaderstats"),"old source never retries queued player")
    eq(h:mapCount(),3,"old source leaves an unused workshop")
    eq(store.writes["p:1"] or 0,0,"failed profile untouched")
end)
print(string.format("AUTO_FAILED_LOAD_BACKFILL_SUMMARY %d passed / %d failed; canonical whole-server mock",passed,failed))
if failed>0 then os.exit(1) end
