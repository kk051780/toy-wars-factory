-- Canonical full-server lease expiry regression; offline mock, not Roblox engine.
local H=dofile("tests/roblox_server_harness.lua")
local path="src/ToyWarsServer.server.lua"
local oldHead="9deab2acbdba8406b02f653ae84b355d92dd499a"
local passed,failed,serial=0,0,0
local function eq(a,b,n) assert(a==b,(n or "value")..": expected "..tostring(b)..", got "..tostring(a)) end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
local function copy(v)
    if not v then return nil end
    local out={};for k,x in pairs(v) do out[k]=x end;return out
end
local function newStore()
    local s={data={["p:1"]={version=1,coins=200,wave=2,defeated=3,
        factoryLevel=1,revision=0}},calls=0,failRefresh=false,delayRefresh=false,
        ids={123},metadata={keep="yes"}}
    function s:GetAsync(key) return copy(self.data[key]) end
    function s:UpdateAsync(key,callback)
        self.calls=self.calls+1
        if self.failRefresh and self.calls==2 then
            if self.delayRefresh then coroutine.yield(0.3) end
            error("injected lease refresh transport failure")
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
    return s
end
local function oldSource()
    local p=assert(io.popen("git show "..oldHead..":src/ToyWarsServer.server.lua 2>/dev/null","r"))
    local source=p:read("*a")
    assert(p:close() and #source>33000,"pinned old-main source required")
    return source
end
local function fixture(store,clock,source)
    local original=loadfile
    _G.loadfile=function(file,mode,env)
        if file==path and env then
            env.os.time=function() return clock.value end
            local get=env.game.GetService
            env.game.GetService=function(self,name)
                if name=="DataStoreService" then return {GetDataStore=function() return store end} end
                if name=="HttpService" then return {GenerateGUID=function()
                    serial=serial+1;return "lease-expiry-"..tostring(serial)
                end} end
                return get(self,name)
            end
            env.game.BindToClose=function(_,callback) clock.onClose=callback end
            if source then return assert(load(source,"@PINNED_9DEAB2AC","t",env)) end
        end
        if env==nil then return original(file,mode) end
        return original(file,mode,env)
    end
    local ok,h=pcall(H.new,path);_G.loadfile=original;assert(ok,h);return h
end
local function coins(p) return assert(assert(p:FindFirstChild("leaderstats")):FindFirstChild("Coins")) end
local function expiredScenario(source)
    local store=newStore();local clock={value=0}
    local a=fixture(store,clock,source);local pa=a:addPlayer(a:newPlayer())
    local money=coins(pa);money.Value=350
    local kicked=0;pa.Kick=function() kicked=kicked+1 end
    eq(store.data["p:1"].sessionLeaseUntil,180,"initial lease")
    store.failRefresh=true;clock.value=181
    a.runService.Heartbeat:Fire(0.2)
    store.failRefresh=false
    local b=fixture(store,clock);local pb=b:addPlayer(b:newPlayer())
    eq(coins(pb).Value,200,"B restores persisted progress")
    local newOwner=store.data["p:1"].sessionOwner
    assert(newOwner~=nil and newOwner~="lease-expiry-1","B claims expired lease")
    a.runService.Heartbeat:Fire(0.2)
    a:removePlayer(pa)
    eq(store.data["p:1"].sessionOwner,newOwner,"A cannot steal B ownership")
    coins(pb).Value=270;b:removePlayer(pb)
    eq(store.data["p:1"].coins,270,"B final save")
    eq(store.metadata.keep,"yes","metadata retained")
    eq(store.ids[1],123,"UserIds retained")
    return {money=money,kicked=kicked,store=store}
end
check("expired lease stops income when refresh fails and B claims",function()
    local r=expiredScenario()
    eq(r.money.Value,350,"no unsavable income")
    eq(r.kicked,1,"rejoin instruction")
end)
check("unexpired transient refresh failure can retry without kick",function()
    local store=newStore();local clock={value=0}
    local h=fixture(store,clock);local p=h:addPlayer(h:newPlayer())
    local kicked=0;p.Kick=function() kicked=kicked+1 end
    local money=coins(p);money.Value=350
    store.failRefresh=true;clock.value=45;h.runService.Heartbeat:Fire(0.2)
    eq(money.Value,351,"live session continues")
    eq(kicked,0,"transient does not kick")
    store.failRefresh=false;clock.value=50;h.runService.Heartbeat:Fire(0.2)
    eq(store.data["p:1"].sessionLeaseUntil,230,"lease renewed")
    eq(kicked,0,"retry remains active")
    h:removePlayer(p)
    eq(store.data["p:1"].coins,money.Value,"earned progress saved")
    eq(store.data["p:1"].sessionOwner,nil,"owner released")
end)
local function delayedScenario(source)
    local store=newStore();local clock={value=0}
    local h=fixture(store,clock,source);local p=h:addPlayer(h:newPlayer())
    local money=coins(p);money.Value=350
    local kicked=0;p.Kick=function() kicked=kicked+1 end
    store.failRefresh=true;store.delayRefresh=true;clock.value=179
    h.runService.Heartbeat:Fire(0.2)
    eq(store.calls,2,"refresh started")
    eq(money.Value,350,"inflight does not pay")
    clock.value=181;h:advance(0.31)
    return {store=store,h=h,p=p,money=money,kicked=kicked}
end
check("delayed failed refresh past expiry cannot resume income",function()
    local r=delayedScenario()
    eq(r.money.Value,350,"no post-expiry income")
    eq(r.kicked,1,"expired rejoin instruction")
    r.h:removePlayer(r.p)
    eq(r.store.data["p:1"].coins,350,"CAS saves earlier earnings if still owner")
end)
check("pinned old main continues unsavable income after expired failure",function()
    local r=expiredScenario(oldSource())
    assert(r.money.Value>350,"old main must continue income")
    eq(r.kicked,0,"old main has no expiry kick")
end)
check("pinned old main resumes after delayed failed refresh past expiry",function()
    local r=delayedScenario(oldSource())
    assert(r.money.Value>350,"old main resumes unsavable income")
    eq(r.kicked,0,"old main does not fail closed")
end)
-- The exact reviewed PR100 head is a negative control for the shutdown-before-removal race.
local function reviewedHeadSource()
    local p=assert(io.popen("git show 06ef9e558743b7eec1582cf7d6e358c9766132ea:src/ToyWarsServer.server.lua 2>/dev/null","r"))
    local source=p:read("*a")
    assert(p:close() and #source>34000,"pinned reviewed PR head required")
    return source
end
local function shutdownBeforeRemoval(source,foreign)
    local store=newStore();local clock={value=0}
    local h=fixture(store,clock,source);local p=h:addPlayer(h:newPlayer())
    local owner=assert(store.data["p:1"].sessionOwner)
    local money=coins(p);money.Value=350
    local kicked=0;p.Kick=function() kicked=kicked+1 end
    clock.value=181
    h.runService.Heartbeat:Fire(0.2)
    eq(kicked,1,"lease expiry kicks but does not remove immediately")
    eq(money.Value,350,"no post-expiry income")
    if foreign then
        local record=store.data["p:1"]
        record.sessionOwner="new-server-owner"
        record.sessionLeaseUntil=361
        record.revision=1
        record.coins=275
    end
    assert(type(clock.onClose)=="function","real server BindToClose callback must be registered")
    clock.onClose() -- before PlayerRemoving: the old server still has a session
    return {store=store,owner=owner,player=p,h=h,money=money}
end
check("expired but CAS-owned session saves on shutdown before PlayerRemoving",function()
    local r=shutdownBeforeRemoval()
    local saved=r.store.data["p:1"]
    eq(saved.coins,350,"pre-expiry earnings committed")
    eq(saved.wave,2,"wave preserved")
    eq(saved.defeated,3,"kills preserved")
    eq(saved.revision,1,"revision advanced exactly once")
    eq(saved.sessionOwner,nil,"owner released after successful save")
    eq(saved.sessionLeaseUntil,nil,"lease released after successful save")
    eq(r.store.metadata.keep,"yes","metadata retained")
    eq(r.store.ids[1],123,"UserIds retained")
    r.h:removePlayer(r.player)
    eq(r.store.data["p:1"].revision,1,"PlayerRemoving cannot duplicate committed save")
end)
check("expired shutdown cannot overwrite a foreign owner",function()
    local r=shutdownBeforeRemoval(nil,true)
    local saved=r.store.data["p:1"]
    eq(saved.coins,275,"foreign progress unchanged")
    eq(saved.revision,1,"foreign revision unchanged")
    eq(saved.sessionOwner,"new-server-owner","foreign lease owner unchanged")
    eq(saved.sessionLeaseUntil,361,"foreign lease remains")
    eq(r.store.metadata.keep,"yes","metadata retained")
    eq(r.store.ids[1],123,"UserIds retained")
end)
check("pinned reviewed PR100 head skips expired session during shutdown",function()
    local r=shutdownBeforeRemoval(reviewedHeadSource())
    local saved=r.store.data["p:1"]
    eq(saved.coins,200,"reviewed old head loses unsaved earnings")
    eq(saved.sessionOwner,r.owner,"reviewed old head leaves lease owned")
end)
print(string.format("AUTO_EXPIRED_LEASE_SUMMARY %d passed / %d failed",passed,failed))
if failed>0 then os.exit(1) end
