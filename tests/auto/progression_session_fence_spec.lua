-- Whole canonical-server two-session ownership regressions, including pinned prior-head negative control.
-- No Roblox engine or live DataStore execution; each fixture loads the real server script.
local H = dofile("tests/roblox_server_harness.lua")
local server = "src/ToyWarsServer.server.lua"
local previous = "5bba9a7fffa3b494b485341b51372452f196fad1"
local passed, failed, guidSerial = 0, 0, 0
local function eq(actual, expected, label)
    assert(actual==expected,(label or "value")..": expected "..tostring(expected)..", got "..tostring(actual))
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
local function profile(coins)
    return {version=1,coins=coins,wave=2,defeated=3,factoryLevel=1,revision=0}
end
local function newStore()
    local store={data={},writes=0,cancels=0,ids={},metadata={},failClaim=false}
    function store:GetAsync(key) return self.data[key] end
    function store:UpdateAsync(key,callback)
        self.writes=self.writes+1
        if self.failClaim then error("injected claim failure") end
        local current=self.data[key]
        local info=current and {
            GetUserIds=function() return self.ids[key] end,
            GetMetadata=function() return self.metadata[key] end,
        } or nil
        local updated,ids,metadata=callback(current,info)
        if updated==nil then self.cancels=self.cancels+1;return nil end
        self.data[key]=updated
        if ids~=nil then self.ids[key]=ids end
        if metadata~=nil then self.metadata[key]=metadata end
        return updated
    end
    return store
end
local function oldSource()
    local pipe=assert(io.popen("git show "..previous..":src/ToyWarsServer.server.lua 2>/dev/null","r"))
    local source=pipe:read("*a")
    assert(pipe:close() and #source>24000,"pinned previous head required")
    return source
end
local function fixture(store,source)
    local original=loadfile
    _G.loadfile=function(path,mode,env)
        if path==server and env then
            local getService=env.game.GetService
            env.game.GetService=function(self,name)
                if name=="DataStoreService" then
                    return {GetDataStore=function(_,storeName)
                        eq(storeName,"ToyWarsProgressV1","store name")
                        return store
                    end}
                end
                if name=="HttpService" then
                    return {GenerateGUID=function()
                        guidSerial=guidSerial+1
                        return "offline-session-guid-"..tostring(guidSerial)
                    end}
                end
                return getService(self,name)
            end
            if source then return assert(load(source,"@PREVIOUS_PR94","t",env)) end
        end
        if env==nil then return original(path,mode) end
        return original(path,mode,env)
    end
    local ok,h=pcall(H.new,server)
    _G.loadfile=original
    assert(ok,h)
    return h
end
local function coins(p) return assert(assert(p:FindFirstChild("leaderstats")):FindFirstChild("Coins")) end
check("second session waits for first final save before loading progress",function()
    local store=newStore();store.data["p:1"]=profile(200)
    local a=fixture(store);local pa=a:addPlayer(a:newPlayer())
    local b=fixture(store);local pb=b:addPlayer(b:newPlayer())
    assert(not pb:FindFirstChild("leaderstats"),"B must wait for A")
    coins(pa).Value=300;a:removePlayer(pa)
    eq(store.data["p:1"].coins,300,"A saved before B claim")
    b:advance(0.6)
    eq(coins(pb).Value,300,"B restores A final progress")
    coins(pb).Value=500;b:removePlayer(pb)
    eq(store.data["p:1"].coins,500,"B saved")
    eq(store.data["p:1"].revision,2,"both saves")
end)
check("busy session times out without unsavable gameplay",function()
    local store=newStore();store.data["p:1"]=profile(200)
    local a=fixture(store);local pa=a:addPlayer(a:newPlayer())
    local b=fixture(store);local pb=b:addPlayer(b:newPlayer())
    b:advance(2)
    assert(not pb:FindFirstChild("leaderstats"),"busy B must not play")
    eq(b:mapCount(),0,"failed join releases plot")
    coins(pa).Value=300;a:removePlayer(pa)
    local c=fixture(store);local pc=c:addPlayer(c:newPlayer())
    eq(coins(pc).Value,300,"later reconnect loads saved progress")
    coins(pc).Value=250;c:removePlayer(pc)
    eq(store.data["p:1"].coins,250,"purchase decreases coins")
end)
check("rejoin claims new owner and preserves user IDs and metadata",function()
    local store=newStore();store.data["p:1"]=profile(200)
    store.ids["p:1"]={123,456};store.metadata["p:1"]={tag="keep"}
    local a=fixture(store);local pa=a:addPlayer(a:newPlayer())
    local first=store.data["p:1"].sessionOwner
    assert(type(first)=="string" and #first>8,"claim token missing")
    coins(pa).Value=300;a:removePlayer(pa)
    local b=fixture(store);local pb=b:addPlayer(b:newPlayer())
    assert(store.data["p:1"].sessionOwner~=first,"rejoin must rotate owner")
    eq(coins(pb).Value,300,"loaded latest progress")
    coins(pb).Value=400;b:removePlayer(pb)
    eq(store.data["p:1"].coins,400,"new progress")
    eq(store.ids["p:1"][2],456,"user IDs")
    eq(store.metadata["p:1"].tag,"keep","metadata")
end)
check("unknown schema never receives a session claim",function()
    local store=newStore();store.data["p:1"]={version=2,coins=900}
    local h=fixture(store);local p=h:addPlayer(h:newPlayer())
    eq(store.writes,0,"no writes on unknown schema")
    h:removePlayer(p)
    eq(store.data["p:1"].version,2,"schema untouched")
end)
check("failed claim blocks gameplay without overwriting progress",function()
    local store=newStore();store.data["p:1"]=profile(200);store.failClaim=true
    local h=fixture(store);local p=h:addPlayer(h:newPlayer())
    assert(not p:FindFirstChild("leaderstats"),"no unsavable game")
    h:removePlayer(p)
    eq(store.data["p:1"].coins,200,"saved data intact")
    eq(store.writes,1,"claim attempted once")
    assert(#h.warnings>=1,"failure surfaced")
end)
check("negative control: previous PR head loses later session's progress",function()
    local store=newStore();store.data["p:1"]=profile(200)
    local source=oldSource()
    local a=fixture(store,source);local pa=a:addPlayer(a:newPlayer())
    local b=fixture(store,source);local pb=b:addPlayer(b:newPlayer())
    coins(pa).Value=300;coins(pb).Value=500
    a:removePlayer(pa);b:removePlayer(pb)
    eq(store.data["p:1"].coins,300,"old source loses later progress")
    eq(store.cancels,1,"old later save conflicts")
end)
print(string.format("AUTO_PROGRESS_SESSION_FENCE_SUMMARY %d passed / %d failed; canonical whole-server Lua mock",passed,failed))
if failed>0 then os.exit(1) end
