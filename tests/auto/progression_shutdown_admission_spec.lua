-- Canonical server shutdown admission fence: offline Lua mock, not Roblox engine.
local H=dofile("tests/roblox_server_harness.lua")
local path="src/ToyWarsServer.server.lua"
local pinned="c3189d75d4b9bc49d79204c9bab17265e57813f4"
local passed,failed=0,0
local function eq(a,b,n) assert(a==b,(n or "value")..": expected "..tostring(b)..", got "..tostring(a)) end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
local function oldSource()
    local p=assert(io.popen("git show "..pinned..":src/ToyWarsServer.server.lua 2>/dev/null","r"))
    local source=p:read("*a")
    assert(p:close() and #source==36613,"pinned main source required")
    return source
end
local function fixture(source,count,delayMode)
    local f={delayedClaim=false}
    local original=loadfile
    _G.loadfile=function(file,mode,env)
        if file==path and env then
            local get=env.game.GetService
            local store=get(env.game,"DataStoreService"):GetDataStore("ToyWarsProgressV1")
            local proxy={}
            function proxy:GetAsync(key)
                if delayMode=="read" and key=="p:2" then coroutine.yield(2) end
                return store:GetAsync(key)
            end
            function proxy:UpdateAsync(key,transform)
                local current=store:GetAsync(key)
                if delayMode=="claim" and key=="p:2" and not f.delayedClaim then
                    f.delayedClaim=true
                    local result=store:UpdateAsync(key,transform)
                    coroutine.yield(2)
                    return result
                end
                if current and current.sessionOwner then coroutine.yield(3) end
                return store:UpdateAsync(key,transform)
            end
            env.game.GetService=function(self,name)
                if name=="DataStoreService" then return {GetDataStore=function() return proxy end} end
                return get(self,name)
            end
            env.game.BindToClose=function(_,cb) f.close=cb end
            if source then return assert(load(source,"@PINNED_C3189D75","t",env)) end
        end
        if env==nil then return original(file,mode) end
        return original(file,mode,env)
    end
    local ok,h=pcall(H.new,path,count)
    _G.loadfile=original
    assert(ok,h)
    assert(type(f.close)=="function","real server close callback required")
    f.h=h;f.store=h.services.DataStoreService:GetDataStore("ToyWarsProgressV1")
    f.players={table.unpack(h.playerList)}
    return f
end
local function startClose(f)
    local thread=coroutine.create(f.close)
    local ok,delay=coroutine.resume(thread)
    assert(ok,delay)
    eq(delay,3,"shutdown final save delay")
    eq(coroutine.status(thread),"suspended","shutdown in progress")
    return thread
end
local function finishClose(f,thread,advance)
    f.h:advance(advance or 3.1)
    local ok,err=coroutine.resume(thread)
    assert(ok,err)
    eq(coroutine.status(thread),"dead","shutdown finished")
end
local function notAdmitted(f,p)
    eq(f.h:workshop(p),nil,"no late workshop")
    eq(p:FindFirstChild("leaderstats"),nil,"no late stats")
    eq(f.store:GetAsync("p:"..p.UserId),nil,"no late claim")
end
check("pre-shutdown queue backfill remains functional",function()
    local f=fixture(nil,4)
    local waiting=f.h:addPlayer(f.h:newPlayer())
    notAdmitted(f,waiting)
    f.h:removePlayer(f.players[1])
    assert(f.h:workshop(waiting),"fifth player should receive freed plot")
    assert(waiting:FindFirstChild("leaderstats"),"waiting player must load")
end)
check("PlayerRemoving during shutdown cannot backfill fifth player",function()
    local f=fixture(nil,4)
    local waiting=f.h:addPlayer(f.h:newPlayer())
    local thread=startClose(f)
    f.h:removePlayer(f.players[1])
    notAdmitted(f,waiting)
    finishClose(f,thread)
    notAdmitted(f,waiting)
    for i=1,4 do
        local saved=assert(f.store:GetAsync("p:"..i),"existing progress")
        eq(saved.sessionOwner,nil,"existing final save owner")
    end
end)
check("new join after shutdown cannot claim freed slot",function()
    local f=fixture(nil,1)
    local thread=startClose(f)
    f.h:removePlayer(f.players[1])
    local newcomer=f.h:addPlayer(f.h:newPlayer())
    notAdmitted(f,newcomer)
    finishClose(f,thread)
end)
check("pre-shutdown pending read completes but is frozen and finalized",function()
    local f=fixture(nil,1,"read")
    local pending=f.h:addPlayer(f.h:newPlayer())
    local thread=startClose(f)
    f.h:advance(2.1)
    assert(f.h:workshop(pending),"accepted pending queue admission")
    local coins=assert(assert(pending:FindFirstChild("leaderstats")):FindFirstChild("Coins"))
    local before=coins.Value
    f.h.runService.Heartbeat:Fire(0.3)
    eq(coins.Value,before,"no late gameplay income")
    finishClose(f,thread,3.1)
    local record=assert(f.store:GetAsync("p:2"),"late progress")
    eq(record.sessionOwner,nil,"late session lease released")
end)
check("already-committed pending claim is finalized without gameplay",function()
    local f=fixture(nil,1,"claim")
    local pending=f.h:addPlayer(f.h:newPlayer())
    assert(f.delayedClaim,"claim must commit before response")
    assert(assert(f.store:GetAsync("p:2")).sessionOwner,"pending owner held")
    local thread=startClose(f)
    f.h:advance(5.2)
    assert(f.h:workshop(pending),"pending admission preserved")
    local record=assert(f.store:GetAsync("p:2"),"record retained")
    eq(record.sessionOwner,nil,"pending claim owner released")
    eq(record.sessionLeaseUntil,nil,"pending claim lease released")
    local coins=assert(assert(pending:FindFirstChild("leaderstats")):FindFirstChild("Coins"))
    local before=coins.Value
    f.h.runService.Heartbeat:Fire(0.3)
    eq(coins.Value,before,"no unsavable gameplay")
    finishClose(f,thread,0)
end)
check("pinned old main admits fifth player during shutdown",function()
    local f=fixture(oldSource(),4)
    local waiting=f.h:addPlayer(f.h:newPlayer())
    local thread=startClose(f)
    f.h:removePlayer(f.players[1])
    assert(f.h:workshop(waiting),"old main must reproduce late backfill")
    finishClose(f,thread)
end)
check("pinned old main admits pending read after shutdown",function()
    local f=fixture(oldSource(),1,"read")
    local pending=f.h:addPlayer(f.h:newPlayer())
    local thread=startClose(f)
    f.h:advance(2.1)
    assert(f.h:workshop(pending),"old main must reproduce late read")
    assert(assert(f.store:GetAsync("p:2")).sessionOwner,"old main leaves late session lease held")
    finishClose(f,thread,1)
end)
print(string.format("AUTO_SHUTDOWN_ADMISSION_SUMMARY %d passed / %d failed",passed,failed))
if failed>0 then os.exit(1) end
