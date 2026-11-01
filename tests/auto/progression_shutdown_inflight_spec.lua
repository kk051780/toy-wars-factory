-- Canonical full-server shutdown interleaving; offline coroutine mock only.
local H=dofile("tests/roblox_server_harness.lua")
local path="src/ToyWarsServer.server.lua"
local pinned="1ed8445528eb6c48597888f0be395859df0d44bd"
local passed,failed,serial=0,0,0
local function eq(a,b,n) assert(a==b,(n or "value")..": expected "..tostring(b)..", got "..tostring(a)) end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
local function copy(v)
    if not v then return nil end
    local t={};for k,x in pairs(v) do t[k]=x end;return t
end
local function oldSource()
    local p=assert(io.popen("git show "..pinned..":src/ToyWarsServer.server.lua 2>/dev/null","r"))
    local source=p:read("*a")
    assert(p:close() and #source==35117,"pinned main source required")
    return source
end
local function fixture(source,delay)
    local store={data={["p:1"]={version=1,coins=200,wave=2,defeated=3,
        factoryLevel=1,revision=0}},calls=0,pending=false,ids={123},metadata={keep="yes"}}
    function store:GetAsync(key) return copy(self.data[key]) end
    function store:UpdateAsync(key,callback)
        self.calls=self.calls+1
        if self.calls==2 and delay and delay>0 then
            self.pending=true
            coroutine.yield(delay) -- outside the atomic transform
            self.pending=false
        end
        local current=copy(self.data[key])
        local info=current and {
            GetUserIds=function() return self.ids end,
            GetMetadata=function() return self.metadata end
        } or nil
        local updated,ids,metadata=callback(current,info)
        if updated==nil then return nil end
        self.data[key]=copy(updated)
        if ids~=nil then self.ids=ids end
        if metadata~=nil then self.metadata=metadata end
        return copy(updated)
    end
    local original=loadfile
    local clock={}
    _G.loadfile=function(file,mode,env)
        if file==path and env then
            local get=env.game.GetService
            env.game.GetService=function(self,name)
                if name=="DataStoreService" then return {GetDataStore=function() return store end} end
                if name=="HttpService" then return {GenerateGUID=function()
                    serial=serial+1;return "shutdown-inflight-"..tostring(serial)
                end} end
                return get(self,name)
            end
            env.game.BindToClose=function(_,callback) clock.onClose=callback end
            if source then return assert(load(source,"@PINNED_MAIN_1ED84455","t",env)) end
        end
        if env==nil then return original(file,mode) end
        return original(file,mode,env)
    end
    local ok,h=pcall(H.new,path);_G.loadfile=original;assert(ok,h)
    assert(type(clock.onClose)=="function","actual BindToClose callback registered")
    local p=h:addPlayer(h:newPlayer())
    local money=assert(assert(p:FindFirstChild("leaderstats")):FindFirstChild("Coins"))
    money.Value=350
    eq(store.calls,1,"initial claim")
    return {store=store,h=h,p=p,close=clock.onClose}
end
local function driveClose(f,maxSteps)
    local thread=coroutine.create(f.close)
    local steps=0
    while coroutine.status(thread)~="dead" and steps<(maxSteps or 300) do
        local ok,delay=coroutine.resume(thread);assert(ok,delay)
        steps=steps+1
        if coroutine.status(thread)~="dead" then
            assert(type(delay)=="number" and delay>0,"shutdown must yield")
            f.h:advance(delay)
        end
    end
    eq(coroutine.status(thread),"dead","shutdown completed")
    return steps
end
check("shutdown waits for in-flight PlayerRemoving final save",function()
    local f=fixture(nil,3)
    f.h:removePlayer(f.p)
    eq(f.store.pending,true,"final UpdateAsync yielded")
    eq(f.store.data["p:1"].coins,200,"not yet committed")
    assert(driveClose(f,60)>1,"shutdown cannot return before save")
    eq(f.store.pending,false,"save finished")
    eq(f.store.data["p:1"].coins,350,"earnings committed")
    eq(f.store.data["p:1"].revision,1,"single revision")
    eq(f.store.data["p:1"].sessionOwner,nil,"owner released")
    eq(f.store.metadata.keep,"yes","metadata preserved")
    eq(f.store.ids[1],123,"UserIds preserved")
    eq(f.store.calls,2,"claim plus one final save")
end)
check("pending final save cannot overwrite foreign owner",function()
    local f=fixture(nil,3)
    f.h:removePlayer(f.p)
    local record=f.store.data["p:1"]
    record.sessionOwner="foreign-owner";record.sessionLeaseUntil=999
    record.revision=9;record.coins=275
    assert(driveClose(f,60)>1,"shutdown waits for CAS conflict")
    eq(record.coins,275,"foreign coins")
    eq(record.revision,9,"foreign revision")
    eq(record.sessionOwner,"foreign-owner","foreign owner")
    eq(record.sessionLeaseUntil,999,"foreign lease")
    eq(f.store.calls,2,"no duplicate save")
end)
check("PlayerRemoving cannot duplicate shutdown final save",function()
    local f=fixture(nil,3)
    local thread=coroutine.create(f.close)
    local ok,delay=coroutine.resume(thread);assert(ok,delay)
    eq(delay,3,"shutdown final save yielded")
    eq(f.store.pending,true,"shutdown finalizing")
    f.h:removePlayer(f.p)
    eq(f.store.calls,2,"no second CAS")
    f.h:advance(3.1)
    local resumed,err=coroutine.resume(thread);assert(resumed,err)
    eq(coroutine.status(thread),"dead","shutdown completed")
    eq(f.store.data["p:1"].coins,350,"saved coins")
    eq(f.store.data["p:1"].revision,1,"no double revision")
    eq(f.store.data["p:1"].sessionOwner,nil,"owner released")
    eq(f.store.calls,2,"one final CAS")
end)
check("shutdown wait ends by deadline if DataStore stalls",function()
    local f=fixture(nil,100)
    f.h:removePlayer(f.p)
    local steps=driveClose(f,300)
    assert(steps>=200 and steps<=260,"bounded wait iterations")
    assert(f.h.now>=24 and f.h.now<=26,"about 25 seconds")
    eq(f.store.pending,true,"still pending")
    eq(f.store.data["p:1"].coins,200,"no false save claim")
    f.h:advance(100)
    eq(f.store.data["p:1"].coins,350,"eventual CAS still allowed")
end)
check("pinned main exits shutdown while departing save is pending",function()
    local f=fixture(oldSource(),3)
    f.h:removePlayer(f.p)
    eq(f.store.pending,true,"old save pending")
    eq(driveClose(f,2),1,"old shutdown returns immediately")
    eq(f.store.data["p:1"].coins,200,"old save not finished")
    assert(f.store.data["p:1"].sessionOwner~=nil,"old owner still held")
    f.h:advance(3.1)
    eq(f.store.data["p:1"].coins,350,"later completion is not shutdown wait")
end)
print(string.format("AUTO_PROGRESS_SHUTDOWN_INFLIGHT_SUMMARY %d passed / %d failed",passed,failed))
if failed>0 then os.exit(1) end
