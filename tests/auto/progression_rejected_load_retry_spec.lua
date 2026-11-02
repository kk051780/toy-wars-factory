-- Reviewer regression: two failed loads must never re-enter the workshop queue.
-- Executes the canonical full server with delayed Kick disconnect, not real Roblox.
local H=dofile("tests/roblox_server_harness.lua")
local path="src/ToyWarsServer.server.lua"
local pinned="ae1e80f5b2e05e983497f33b675a52bf33a7acfd"
local passed,failed=0,0
local function eq(actual,expected,label)
    assert(actual==expected,(label or "value")..": expected "..tostring(expected)..", got "..tostring(actual))
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
local function oldSource()
    local pipe=assert(io.popen("git show "..pinned..":"..path.." 2>/dev/null","r"))
    local source=pipe:read("*a")
    assert(pipe:close() and #source>33000,"pinned PR99 source required")
    return source
end
local function fixture(source)
    local store={data={},reads={},writes={}}
    function store:GetAsync(key)
        self.reads[key]=(self.reads[key] or 0)+1
        if key=="p:1" then
            coroutine.yield(0.2)
            error("injected failed read for A")
        end
        if key=="p:2" then
            coroutine.yield(0.3)
            return {version=2,coins=999}
        end
        return self.data[key]
    end
    function store:UpdateAsync(key,callback)
        self.writes[key]=(self.writes[key] or 0)+1
        local updated=callback(self.data[key])
        if updated~=nil then self.data[key]=updated end
        return updated
    end
    local original=loadfile
    _G.loadfile=function(file,mode,env)
        if file==path and env then
            local getService=env.game.GetService
            env.game.GetService=function(self,name)
                if name=="DataStoreService" then return {GetDataStore=function() return store end} end
                return getService(self,name)
            end
            if source then return assert(load(source,"@PINNED_PR99","t",env)) end
        end
        if env==nil then return original(file,mode) end
        return original(file,mode,env)
    end
    local ok,h=pcall(H.new,path)
    _G.loadfile=original
    assert(ok,h)
    local a=h:newPlayer()
    local b=h:newPlayer()
    a.Kick=function(self) self.kicks=(self.kicks or 0)+1 end
    b.Kick=function(self) self.kicks=(self.kicks or 0)+1 end
    h:addPlayer(a)
    h:addPlayer(b)
    local c=h:addPlayer(h:newPlayer())
    local d=h:addPlayer(h:newPlayer())
    local e=h:addPlayer(h:newPlayer())
    assert(not e:FindFirstChild("leaderstats"),"E must wait for a reserved plot")
    h:advance(1.2)
    return h,store,a,b,c,d,e
end
check("two delayed disconnects cannot requeue rejected loads",function()
    local h,store,a,b,c,d,e=fixture()
    eq(store.reads["p:1"],1,"A read count")
    eq(store.reads["p:2"],1,"B read count")
    eq(store.writes["p:1"] or 0,0,"A writes")
    eq(store.writes["p:2"] or 0,0,"B writes")
    eq(a.kicks,1,"A kicked once")
    eq(b.kicks,1,"B kicked once")
    assert(a.Parent==h.players and b.Parent==h.players,"Kick disconnect must remain delayed")
    assert(not a:FindFirstChild("leaderstats") and not b:FindFirstChild("leaderstats"),"rejected play blocked")
    assert(e:FindFirstChild("leaderstats") and h:workshop(e),"healthy E receives a workshop")
    eq(h:mapCount(),3,"three healthy workshops")
    local f=h:addPlayer(h:newPlayer())
    local g=h:addPlayer(h:newPlayer())
    assert(f:FindFirstChild("leaderstats") and not g:FindFirstChild("leaderstats"),"G waits at capacity")
    h:removePlayer(c)
    assert(g:FindFirstChild("leaderstats") and h:workshop(g),"departure backfill skips rejected A/B")
    eq(store.reads["p:1"],1,"A never retried by departure")
    eq(store.reads["p:2"],1,"B never retried by departure")
end)
check("PlayerRemoving clears rejection for a genuine later join",function()
    local h,store,a,b=fixture()
    h:removePlayer(a)
    h:addPlayer(a)
    h:advance(0.3)
    eq(store.reads["p:1"],2,"new join may retry after real removal")
    eq(store.writes["p:1"] or 0,0,"failed player cannot write")
    assert(not a:FindFirstChild("leaderstats"),"failed rejoin remains blocked")
end)
check("negative control: PR99 retries a rejected player still in Players",function()
    local h,store,a,b,c,d,e=fixture(oldSource())
    assert((store.reads["p:1"] or 0)>1 or (store.reads["p:2"] or 0)>1,
        "pinned PR99 must reproduce the rejected-player retry storm")
    assert(e:FindFirstChild("leaderstats"),"first freed plot still admits healthy E")
    eq(store.writes["p:1"] or 0,0,"old A never writes")
    eq(store.writes["p:2"] or 0,0,"old B never writes")
end)
print(string.format("AUTO_REJECTED_LOAD_RETRY_SUMMARY %d passed / %d failed; canonical whole-server mock",passed,failed))
if failed>0 then os.exit(1) end
