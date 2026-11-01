-- Four-player shutdown save concurrency on the complete canonical server.
-- Deterministic coroutine DataStore mock; NOT Roblox engine or real network timing.
local H=dofile("tests/roblox_server_harness.lua")
local path="src/ToyWarsServer.server.lua"
local pinned="d56cf4239f50eaaeb31233cc7f2a277dc855e4f9"
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
    assert(p:close() and #source==35960,"pinned main source required")
    return source
end
local function fixture(source,opts)
    opts=opts or {}
    local store={data={},calls=0,savesStarted=0,delay=opts.delay or 0,
        fail=opts.fail or false,ids={},metadata={}}
    for i=1,4 do
        local key="p:"..i
        store.data[key]={version=1,coins=50,wave=1,defeated=0,factoryLevel=1,revision=0}
        store.ids[key]={100+i};store.metadata[key]={source="keep-"..i}
    end
    function store:GetAsync(key) return copy(self.data[key]) end
    function store:UpdateAsync(key,callback)
        self.calls=self.calls+1
        if self.data[key] and self.data[key].sessionOwner then
            self.savesStarted=self.savesStarted+1
            if self.delay>0 then coroutine.yield(self.delay) end
            if self.fail then error("injected final-save transport failure") end
        end
        local current=copy(self.data[key])
        local info=current and {
            GetUserIds=function() return self.ids[key] end,
            GetMetadata=function() return self.metadata[key] end
        } or nil
        local updated,ids,metadata=callback(current,info)
        if updated==nil then return nil end
        self.data[key]=copy(updated)
        if ids~=nil then self.ids[key]=ids end
        if metadata~=nil then self.metadata[key]=metadata end
        return copy(updated)
    end
    local original=loadfile
    local callbacks={}
    _G.loadfile=function(file,mode,env)
        if file==path and env then
            local get=env.game.GetService
            env.game.GetService=function(self,name)
                if name=="DataStoreService" then return {GetDataStore=function() return store end} end
                if name=="HttpService" then return {GenerateGUID=function()
                    serial=serial+1;return "shutdown-parallel-"..serial
                end} end
                return get(self,name)
            end
            env.game.BindToClose=function(_,cb) callbacks.close=cb end
            if source then return assert(load(source,"@PINNED_D56CF423","t",env)) end
        end
        if env==nil then return original(file,mode) end
        return original(file,mode,env)
    end
    local ok,h=pcall(H.new,path);_G.loadfile=original;assert(ok,h)
    assert(type(callbacks.close)=="function","actual BindToClose registered")
    local players={}
    for i=1,4 do
        local p=h:addPlayer(h:newPlayer())
        local stats=assert(p:FindFirstChild("leaderstats"))
        assert(stats:FindFirstChild("Coins")).Value=350
        assert(stats:FindFirstChild("Wave")).Value=2
        assert(stats:FindFirstChild("Defeated")).Value=i
        assert(h:status(p,"FactoryLevel")).Value=2
        players[i]=p
    end
    eq(store.calls,4,"four atomic initial claims")
    return {h=h,store=store,players=players,close=callbacks.close}
end
local function savedCount(f)
    local count=0
    for i=1,4 do
        local record=f.store.data["p:"..i]
        if record.coins==350 and record.sessionOwner==nil then count=count+1 end
    end
    return count
end
local function assertSaved(f)
    eq(savedCount(f),4,"all progress saved")
    for i=1,4 do
        local key="p:"..i
        local r=f.store.data[key]
        eq(r.revision,1,"revision "..i)
        eq(r.wave,2,"wave "..i)
        eq(r.defeated,i,"kills "..i)
        eq(r.factoryLevel,2,"level "..i)
        eq(r.sessionOwner,nil,"released owner "..i)
        eq(r.sessionLeaseUntil,nil,"released lease "..i)
        eq(f.store.ids[key][1],100+i,"UserIds "..i)
        eq(f.store.metadata[key].source,"keep-"..i,"metadata "..i)
    end
end
local function startClose(f)
    local thread=coroutine.create(f.close)
    local ok,delay=coroutine.resume(thread);assert(ok,delay)
    assert(coroutine.status(thread)~="dead","expected delayed close")
    assert(type(delay)=="number" and delay>0,"positive coroutine wait")
    return thread,delay
end
local function finishClose(f,thread,delay)
    local steps=0
    while coroutine.status(thread)~="dead" and steps<400 do
        f.h:advance(delay)
        local ok,nextDelay=coroutine.resume(thread);assert(ok,nextDelay)
        steps=steps+1
        if coroutine.status(thread)~="dead" then
            assert(type(nextDelay)=="number" and nextDelay>0,"positive shutdown wait")
            delay=nextDelay
        end
    end
    eq(coroutine.status(thread),"dead","shutdown completed")
    return steps
end
check("four eight-second saves finish in parallel within thirty seconds",function()
    local f=fixture(nil,{delay=8})
    local thread,delay=startClose(f)
    eq(f.store.savesStarted,4,"all four final UpdateAsync calls started")
    eq(delay,8,"one synchronous save retains old single-player semantics")
    finishClose(f,thread,delay)
    assert(f.h.now<=8.2,"parallel saves must not sum to thirty-two seconds")
    assertSaved(f)
    eq(f.store.calls,8,"one claim and one save per player")
end)
check("shutdown freezes all admitted sessions before any slow save",function()
    local f=fixture(nil,{delay=8})
    local thread,delay=startClose(f)
    for _,p in ipairs(f.players) do
        local before=assert(assert(p:FindFirstChild("leaderstats")):FindFirstChild("Coins")).Value
        f.h.runService.Heartbeat:Fire(0.3)
        eq(assert(assert(p:FindFirstChild("leaderstats")):FindFirstChild("Coins")).Value,
            before,"no unsavable shutdown income")
    end
    finishClose(f,thread,delay)
    assertSaved(f)
end)
check("PlayerRemoving during parallel shutdown cannot double-save",function()
    local f=fixture(nil,{delay=8})
    local thread,delay=startClose(f)
    f.h:removePlayer(f.players[2])
    eq(f.store.savesStarted,4,"no second final save for departing player")
    finishClose(f,thread,delay)
    assertSaved(f)
    eq(f.store.calls,8,"no duplicate revision writes")
end)
check("four failed final saves exhaust bounded retries without false success",function()
    local f=fixture(nil,{fail=true})
    local thread=coroutine.create(f.close)
    local steps=0
    while coroutine.status(thread)~="dead" and steps<100 do
        local ok,delay=coroutine.resume(thread);assert(ok,delay)
        if coroutine.status(thread)~="dead" then
            assert(type(delay)=="number" and delay>0,"bounded retry wait")
            f.h:advance(delay)
        end
        steps=steps+1
    end
    eq(coroutine.status(thread),"dead","all-fail close bounded")
    eq(f.store.savesStarted,12,"three bounded attempts for four users")
    eq(savedCount(f),0,"no false save success")
    assert(f.h.now<25,"bounded within shutdown wait budget")
    assert(#f.h.warnings>=4,"exhausted saves visible")
end)
check("pinned main sequentially leaves fourth save unsaved at thirty seconds",function()
    local f=fixture(oldSource(),{delay=8})
    local thread,delay=startClose(f)
    eq(f.store.savesStarted,1,"old main starts only one save")
    for i=1,3 do
        eq(delay,8,"old sequential wait")
        f.h:advance(delay)
        local ok,nextDelay=coroutine.resume(thread);assert(ok,nextDelay)
        eq(nextDelay,8,"next sequential save")
        delay=nextDelay
    end
    eq(f.h.now,24,"three completed at twenty-four seconds")
    eq(savedCount(f),3,"only three of four saved")
    eq(f.store.savesStarted,4,"fourth save only starts at twenty-four")
    f.h:advance(6)
    eq(savedCount(f),3,"fourth still unsaved at thirty-second cutoff")
end)
print(string.format("AUTO_SHUTDOWN_PARALLEL_SUMMARY %d passed / %d failed",passed,failed))
if failed>0 then os.exit(1) end
