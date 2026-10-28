-- Complete canonical server, deterministic service-latency interleaving (not Roblox).
local H=dofile("tests/roblox_server_harness.lua")
local path="src/ToyWarsServer.server.lua"
local pinned="f6bf432901e66ce025c490373fbf5a17f176d431"
local passed,failed,serial=0,0,0
local function eq(a,b,n) assert(a==b,(n or "value")..": expected "..tostring(b)..", got "..tostring(a)) end
local function check(n,f)
    local ok,err=pcall(f)
    if ok then passed=passed+1;print("PASS "..n)
    else failed=failed+1;print("FAIL "..n..": "..tostring(err)) end
end
local function copy(v)
    if not v then return nil end
    local out={};for k,x in pairs(v) do out[k]=x end;return out
end
local function store()
    local s={data={["p:1"]={version=1,coins=200,wave=2,defeated=3,factoryLevel=1,revision=0}},calls=0}
    function s:GetAsync(key) return copy(self.data[key]) end
    function s:UpdateAsync(key,callback)
        self.calls=self.calls+1
        local updated=callback(copy(self.data[key]))
        if updated==nil then return nil end
        self.data[key]=copy(updated)
        if self.calls==2 then coroutine.yield(0.3) end -- first refresh commits, response delayed
        return copy(updated)
    end
    return s
end
local function fixture(s,source,clock)
    local original=loadfile
    _G.loadfile=function(file,mode,env)
        if file==path and env then
            env.os.time=function() return clock.value end
            local get=env.game.GetService
            env.game.GetService=function(self,name)
                if name=="DataStoreService" then return {GetDataStore=function() return s end} end
                if name=="HttpService" then return {GenerateGUID=function()
                    serial=serial+1;return "refresh-overlap-"..tostring(serial)
                end} end
                return get(self,name)
            end
            if source then return assert(load(source,"@PINNED_F6BF4329","t",env)) end
        end
        if env==nil then return original(file,mode) end
        return original(file,mode,env)
    end
    local ok,h=pcall(H.new,path);_G.loadfile=original;assert(ok,h);return h
end
local function oldSource()
    local p=assert(io.popen("git show "..pinned..":src/ToyWarsServer.server.lua 2>/dev/null","r"))
    local s=p:read("*a");assert(p:close() and #s>30000,"pinned prior head required")
    return s
end
local function lost(h)
    for _,v in ipairs(h.warnings) do
        if v[1]=="TWF: progress lease ownership lost for" then return true end
    end
    return false
end
local function race(source,foreign)
    local s=store();local clock={value=1000};local h=fixture(s,source,clock)
    local p=h:addPlayer(h:newPlayer())
    assert(assert(p:FindFirstChild("leaderstats")):FindFirstChild("Coins")).Value=350
    eq(s.calls,1,"claim")
    clock.value=1050;h.runService.Heartbeat:Fire(0.2)
    eq(s.calls,2,"first refresh started")
    clock.value=1095;h.runService.Heartbeat:Fire(0.2)
    local callsBeforeRemove=s.calls
    if foreign then s.data["p:1"].sessionOwner="foreign";s.data["p:1"].revision=9 end
    h:removePlayer(p);h:advance(0.35)
    return s,h,callsBeforeRemove
end
check("second Heartbeat cannot launch an overlapping self-refresh",function()
    local s,h,n=race(nil,false)
    eq(n,2,"one in-flight refresh")
    eq(s.calls,3,"claim, refresh, final save")
    eq(s.data["p:1"].coins,350,"earned coins persisted")
    eq(s.data["p:1"].revision,1,"one final revision")
    eq(s.data["p:1"].sessionOwner,nil,"owner released")
    eq(s.data["p:1"].sessionLeaseUntil,nil,"lease released")
    assert(not lost(h),"false ownership loss")
end)
check("foreign owner and revision still block final save",function()
    local s,h,n=race(nil,true)
    eq(n,2,"in-flight guard")
    eq(s.data["p:1"].coins,200,"foreign progress protected")
    eq(s.data["p:1"].sessionOwner,"foreign","foreign owner protected")
    eq(s.data["p:1"].revision,9,"foreign revision protected")
    assert(not lost(h),"late response ignored during finalization")
end)
check("pinned f6bf4329 reproduces duplicate refresh and unsaved coins",function()
    local s,h,n=race(oldSource(),false)
    eq(n,3,"old head duplicate refresh")
    eq(s.data["p:1"].coins,200,"old head loses earned coins")
    assert(s.data["p:1"].sessionOwner~=nil,"old head retains lease")
    assert(lost(h),"old head reports false ownership loss")
end)
print(string.format("AUTO_PROGRESS_REFRESH_OVERLAP_SUMMARY %d passed / %d failed",passed,failed))
if failed>0 then os.exit(1) end
