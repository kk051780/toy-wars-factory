-- Whole canonical server: a queued player's slow DataStore read must not delay
-- the departing workshop owner's final save. Offline scheduler, not Roblox engine.
local H=dofile("tests/roblox_server_harness.lua")
local path="src/ToyWarsServer.server.lua"
local pinned="6ac3f11a0fa88154652b9c68c60a6838a4e5eb60"
local passed,failed,serial=0,0,0
local function eq(actual,expected,label)
    assert(actual==expected,(label or "value")..": expected "..tostring(expected)..", got "..tostring(actual))
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
local function newStore()
    local store={data={["p:1"]={version=1,coins=200,wave=2,defeated=3,factoryLevel=1,revision=0}},
        writes={},slowReads=0}
    function store:GetAsync(key)
        if key=="p:5" then
            self.slowReads=self.slowReads+1
            -- Network latency occurs outside any UpdateAsync transform.
            coroutine.yield(5)
        end
        return copy(self.data[key])
    end
    function store:UpdateAsync(key,callback)
        self.writes[#self.writes+1]=key
        local updated=callback(copy(self.data[key]))
        if updated==nil then return nil end
        self.data[key]=copy(updated)
        return copy(updated)
    end
    return store
end
local function oldSource()
    local pipe=assert(io.popen("git show "..pinned..":src/ToyWarsServer.server.lua 2>/dev/null","r"))
    local source=pipe:read("*a")
    assert(pipe:close() and #source>30000,"pinned 6ac3f11a source required")
    return source
end
local function fixture(store,source)
    local original=loadfile
    local callbacks={}
    _G.loadfile=function(file,mode,env)
        if file==path and env then
            local getService=env.game.GetService
            env.game.GetService=function(self,name)
                if name=="DataStoreService" then return {GetDataStore=function() return store end} end
                if name=="HttpService" then return {GenerateGUID=function()
                    serial=serial+1;return "backfill-save-"..tostring(serial)
                end} end
                return getService(self,name)
            end
            env.game.BindToClose=function(_,fn) callbacks[#callbacks+1]=fn end
            if source then return assert(load(source,"@PINNED_6AC3F11A","t",env)) end
        end
        if env==nil then return original(file,mode) end
        return original(file,mode,env)
    end
    local ok,h=pcall(H.new,path)
    _G.loadfile=original
    assert(ok,h)
    return h,callbacks
end
local function countWrites(store,key)
    local n=0
    for _,written in ipairs(store.writes) do if written==key then n=n+1 end end
    return n
end
local function scenario(source)
    local store=newStore()
    local h,shutdown=fixture(store,source)
    local players={}
    for i=1,4 do
        players[i]=h:addPlayer(h:newPlayer())
        assert(players[i]:FindFirstChild("leaderstats"),"four initial sessions must start")
    end
    local waiting=h:addPlayer(h:newPlayer())
    eq(h:mapCount(),4,"all four workshops occupied")
    assert(not waiting:FindFirstChild("leaderstats"),"fifth player must wait")
    local money=assert(assert(players[1]:FindFirstChild("leaderstats")):FindFirstChild("Coins"))
    money.Value=350
    h:removePlayer(players[1])
    eq(store.slowReads,1,"backfill must enter slow fifth-player GetAsync")
    eq(h:mapCount(),3,"backfill is still loading")
    eq(#shutdown,1,"shutdown callback registered")
    -- Shutdown cannot rescue a departed player because sessions[departing] is gone.
    shutdown[1]()
    return {store=store,h=h,waiting=waiting}
end
check("departing save precedes slow backfill read and survives shutdown",function()
    local r=scenario()
    eq(countWrites(r.store,"p:1"),2,"claim plus final save before fifth-player read resumes")
    eq(r.store.data["p:1"].coins,350,"departing earned progress persisted")
    eq(r.store.data["p:1"].sessionOwner,nil,"departing owner released")
    eq(r.store.data["p:1"].revision,1,"single final revision")
end)
check("waiting player still receives the freed workshop after delayed read",function()
    local r=scenario()
    r.h:advance(5.1)
    assert(r.waiting:FindFirstChild("leaderstats"),"waiting player admitted")
    assert(r.h:workshop(r.waiting),"waiting player gets a workshop")
    eq(r.h:mapCount(),4,"four workshops restored")
    eq(r.store.data["p:1"].coins,350,"departing save remains committed")
end)
check("pinned 6ac3f11a delays final save until slow read completes",function()
    local r=scenario(oldSource())
    eq(countWrites(r.store,"p:1"),1,"old source only claimed before read")
    eq(r.store.data["p:1"].coins,200,"old source loses earned coins at shutdown")
    assert(r.store.data["p:1"].sessionOwner~=nil,"old lease not released")
    r.h:advance(5.1)
    eq(r.store.data["p:1"].coins,350,"old save happens only after delayed read")
end)
print(string.format("AUTO_PROGRESS_BACKFILL_SAVE_ORDER_SUMMARY %d passed / %d failed",passed,failed))
if failed>0 then os.exit(1) end
