-- Full canonical-server regression for a departed player's already-committed claim.
-- Offline coroutine DataStore mock only; no live Roblox/DataStore execution.
local H=dofile("tests/roblox_server_harness.lua")
local path="src/ToyWarsServer.server.lua"
local oldMain="5d4774843179227956f68d92c0ff6f89c77cb28d"
local passed,failed=0,0
local function eq(a,b,name)
    assert(a==b,(name or "value")..": expected "..tostring(b)..", got "..tostring(a))
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
local function copy(t)
    if not t then return nil end
    local out={};for k,v in pairs(t) do out[k]=v end;return out
end
local function oldSource()
    local p=assert(io.popen("git show "..oldMain..":"..path.." 2>/dev/null","r"))
    local s=p:read("*a")
    assert(p:close() and #s>39000,"pinned old main required")
    return s
end
local function fixture(mode,source)
    local store={data={["p:1"]={version=1,coins=275,wave=2,defeated=4,
        factoryLevel=1,revision=0}},calls=0,ids={123},meta={tag="keep"}}
    function store:GetAsync(key) return copy(self.data[key]) end
    function store:UpdateAsync(key,callback)
        self.calls=self.calls+1
        if self.calls>=2 and (mode=="always" or self.calls==2 and mode~="none") then
            error("injected cleanup transport error")
        end
        local info={GetUserIds=function() return self.ids end,
            GetMetadata=function() return self.meta end}
        local updated,ids,meta=callback(copy(self.data[key]),info)
        if updated~=nil then
            self.data[key]=copy(updated)
            if ids then self.ids=ids end
            if meta then self.meta=meta end
        end
        if self.calls==1 then
            coroutine.yield(0.2) -- claim committed, response not yet delivered
        end
        return copy(updated)
    end
    local original=loadfile
    _G.loadfile=function(file,modeArg,env)
        if file==path and env then
            local get=env.game.GetService
            env.game.GetService=function(self,name)
                if name=="DataStoreService" then
                    return {GetDataStore=function() return store end}
                end
                return get(self,name)
            end
            if source then return assert(load(source,"@OLD_MAIN_CLAIM","t",env)) end
        end
        if env==nil then return original(file,modeArg) end
        return original(file,modeArg,env)
    end
    local ok,h=pcall(H.new,path)
    _G.loadfile=original
    assert(ok,h)
    local p=h:addPlayer(h:newPlayer())
    eq(store.calls,1,"claim started")
    assert(store.data["p:1"].sessionOwner,"claim committed before disconnect")
    assert(not p:FindFirstChild("leaderstats"),"claim response still pending")
    h:removePlayer(p)
    eq(h:mapCount(),0,"departed player has no workshop")
    return h,p,store
end
check("transient cleanup failure retries and releases only departed token",function()
    local h,p,s=fixture("once")
    h:advance(0.21)
    eq(s.calls,2,"first cleanup failed")
    assert(s.data["p:1"].sessionOwner,"owner still held during retry")
    h:advance(0.3)
    eq(s.calls,3,"one bounded retry")
    eq(s.data["p:1"].sessionOwner,nil,"claim owner released")
    eq(s.data["p:1"].sessionLeaseUntil,nil,"lease released")
    eq(s.data["p:1"].coins,275,"saved coins unchanged")
    eq(s.data["p:1"].revision,0,"no fake progress revision")
    eq(s.ids[1],123,"user IDs retained")
    eq(s.meta.tag,"keep","metadata retained")
    assert(not p:FindFirstChild("leaderstats"),"no departed admission")
end)
check("foreign owner appearing during retry is never overwritten",function()
    local h,p,s=fixture("once")
    h:advance(0.21)
    s.data["p:1"].sessionOwner="other-session"
    s.data["p:1"].sessionLeaseUntil=9999
    s.data["p:1"].coins=420
    h:advance(0.3)
    eq(s.calls,3,"retry checked current record")
    eq(s.data["p:1"].sessionOwner,"other-session","foreign owner preserved")
    eq(s.data["p:1"].sessionLeaseUntil,9999,"foreign lease preserved")
    eq(s.data["p:1"].coins,420,"foreign progress preserved")
end)
check("permanent transport errors stop after three cleanup attempts",function()
    local h,p,s=fixture("always")
    h:advance(0.9)
    eq(s.calls,4,"claim plus three bounded cleanup attempts")
    assert(s.data["p:1"].sessionOwner,"unavailable cleanup retains lease")
    assert(#h.warnings>=1,"terminal cleanup failure visible")
    assert(not p:FindFirstChild("leaderstats"),"never starts unsavable play")
end)
check("old main strands departed token after one transient cleanup error",function()
    local h,p,s=fixture("once",oldSource())
    h:advance(0.9)
    eq(s.calls,2,"old cleanup never retries")
    assert(s.data["p:1"].sessionOwner,"old claim remains held until lease expiry")
    assert(not p:FindFirstChild("leaderstats"),"old player still departed")
end)
print(string.format("AUTO_DEPARTED_CLAIM_CLEANUP_SUMMARY %d passed / %d failed; offline whole-server mock",passed,failed))
if failed>0 then os.exit(1) end
