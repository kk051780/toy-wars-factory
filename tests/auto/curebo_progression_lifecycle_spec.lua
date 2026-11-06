-- Run the canonical combined server. Offline services do not verify Roblox.
local H=dofile("tests/roblox_server_harness.lua")
local server="src/ToyWarsServer.server.lua"
local passed,failed=0,0
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
local function up(fn,name)
    for i=1,60 do local k,v=debug.getupvalue(fn,i);if not k then break end;if k==name then return v end end
    error("missing canonical upvalue "..name)
end
local function copy(value)
    if not value then return nil end
    local out={};for k,v in pairs(value) do out[k]=v end;return out
end
local function scenario(mode,source)
    local clock={value=1000}
    local store={value={version=1,coins=200,wave=2,defeated=3,factoryLevel=1,revision=0},calls=0}
    function store:GetAsync() return copy(self.value) end
    function store:UpdateAsync(_,transform)
        self.calls=self.calls+1
        if self.calls==2 and mode=="delayed" then coroutine.yield(0.3) end
        if self.calls==2 and mode=="foreign" then
            self.value.sessionOwner="foreign";self.value.revision=self.value.revision+1
        end
        local updated=transform(copy(self.value))
        if updated then self.value=copy(updated) end
        return copy(updated)
    end
    local original=loadfile
    _G.loadfile=function(path,kind,env)
        if path==server and env then
            env.os.time=function() return clock.value end
            local get=env.game.GetService
            env.game.GetService=function(self,name)
                if name=="DataStoreService" then return {GetDataStore=function() return store end} end
                if name=="HttpService" then return {GenerateGUID=function() return "curebo-lifecycle" end} end
                return get(self,name)
            end
            if source then return assert(load(source,"@LIFECYCLE_MUTANT","t",env)) end
        end
        if env==nil then return original(path,kind) end
        return original(path,kind,env)
    end
    local ok,h=pcall(H.new,server);_G.loadfile=original;assert(ok,h)
    local p=h:addPlayer(h:newPlayer());local kicked=0
    p.Kick=function() kicked=kicked+1 end
    local heartbeat=h.runService.Heartbeat.listeners[1].fn
    local state=up(heartbeat,"sessions")[p]
    local add=up(up(heartbeat,"simulate"),"addEntity")
    state.productionTimer=100;state.waveBreak=100
    local target=assert(add(state,"guardon","ally"));target.health=50;target.x=state.x;target.z=0
    local healer=assert(add(state,"curebo","ally"));healer.x=state.x;healer.z=0
    clock.value=1050;h.runService.Heartbeat:Fire(0.12)
    assert(store.calls==2,"claim and refresh must execute")
    if mode=="delayed" then h:removePlayer(p);h:advance(0.31) end
    return {state=state,target=target,healer=healer,store=store,kicked=kicked}
end
local function noStaleRepair(r)
    assert(r.target.health==50,"stale session repaired a toy")
    assert((r.state.combatTime or 0)==0,"stale session advanced repair clock")
    assert(r.healer.repairCooldown==nil,"stale session advanced repair cooldown")
end
check("valid progress lease permits CUREBO repair",function()
    local r=scenario("valid")
    assert(r.target.health==58 and r.state.combatTime==0.12)
    assert(r.store.value.sessionOwner=="curebo-lifecycle")
end)
check("foreign progress owner blocks repair and its clock in the same Heartbeat",function()
    local r=scenario("foreign");noStaleRepair(r)
    assert(r.kicked==1 and r.store.value.sessionOwner=="foreign")
end)
check("departure during lease refresh cannot resume repair",function()
    local r=scenario("delayed");noStaleRepair(r)
    assert(r.store.value.sessionOwner==nil and r.store.value.coins==200)
end)
check("negative control detects removal of the post-refresh lifecycle fence",function()
    local f=assert(io.open(server,"rb"));local src=f:read("*a");f:close()
    local fence='    if not state.active or sessions[state.player] ~= state or state.player.Parent ~= Players then return end\n'
    local start=assert(src:find(fence,1,true));assert(not src:find(fence,start+1,true))
    local mutant=src:sub(1,start-1)..src:sub(start+#fence)
    local r=scenario("foreign",mutant)
    assert(r.target.health==58,"unfenced source must reproduce stale repair")
    assert(not pcall(noStaleRepair,r),"same positive assertion accepted unfenced repair")
end)
print(string.format("AUTO_CUREBO_PROGRESS_LIFECYCLE_SUMMARY %d passed / %d failed; offline only",passed,failed))
if failed>0 then os.exit(1) end
