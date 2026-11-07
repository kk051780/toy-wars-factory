-- PON's first actual game role: server-owned courier reward when crossing the enemy line.
-- The full canonical server runs in the Lua 5.4 mock; not Roblox physics.
local H=dofile("tests/roblox_server_harness.lua")
local B=dofile("src/ToyWarsBalance.lua")
local server=os.getenv("TWF_SERVER_FILE") or "src/ToyWarsServer.server.lua"
local passed,failed=0,0
local function up(fn,name)
    for i=1,80 do
        local k,v=debug.getupvalue(fn,i)
        if not k then break end
        if k==name then return v end
    end
    error("missing canonical server upvalue "..name)
end
local function fixture(path)
    local h=H.new(path or server)
    local player=h:addPlayer(h:newPlayer())
    local heartbeat=assert(h.runService.Heartbeat.listeners[1]).fn
    local simulate=up(heartbeat,"simulate")
    local sessions=up(heartbeat,"sessions")
    local state=assert(sessions[player])
    state.productionTimer=100
    state.waveBreak=100
    return h,player,state,up(simulate,"addEntity"),up(simulate,"updateEntity"),sessions
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
local function exitToy(state,add,update,id,dt,start)
    local e=assert(add(state,id,"ally"))
    e.x=state.x
    e.z=start or 38.8
    update(state,e,dt or 0.3)
    return e
end
check("PON courier reward is twelve and other four toys keep four",function()
    assert(B.deliveryReward("pon")==12)
    for _,id in ipairs({"guardon","tankuru","curebo"}) do
        local amount,reason=B.deliveryReward(id)
        assert(amount==4 and reason=="ok")
    end
end)
check("invalid and enemy identities never receive courier reward",function()
    for _,id in ipairs({"junk","forged","PON",0,true,{},1/0,0/0}) do
        local amount,reason=B.deliveryReward(id)
        assert(amount==nil and reason=="invalid_unit")
    end
    assert(B.deliveryReward(nil)==nil)
end)
check("real PON reaches enemy boundary, earns twelve once and despawns",function()
    local _,_,s,add,update=fixture()
    s.coins.Value=50
    local e=exitToy(s,add,update,"pon")
    assert(s.coins.Value==62 and not e.alive)
    assert(e.model.Parent==nil)
    update(s,e,0.3)
    assert(s.coins.Value==62,"dead courier must not mint coins twice")
end)
check("GUARDON TANKURU CUREBO each retain their original four coins",function()
    for _,id in ipairs({"guardon","tankuru","curebo"}) do
        local _,_,s,add,update=fixture()
        s.coins.Value=50
        local e=exitToy(s,add,update,id)
        assert(s.coins.Value==54 and not e.alive,"wrong reward for "..id)
    end
end)
check("scout that has not crossed the boundary receives no coin bonus",function()
    local _,_,s,add,update=fixture()
    s.coins.Value=50
    local e=exitToy(s,add,update,"pon",0.05,37.0)
    assert(e.alive and e.z<39 and s.coins.Value==50)
end)
check("hostile enemy reaching vault damages base but does not mint courier coins",function()
    local _,_,s,add,update=fixture()
    s.coins.Value=50
    local enemy=assert(add(s,"junk","enemy"))
    enemy.x=s.x
    enemy.z=-39
    update(s,enemy,0.4)
    assert(not enemy.alive and s.baseHP.Value==88 and s.coins.Value==50)
end)
check("courier reward saturates at MAX_CASH without overflowing",function()
    local _,_,s,add,update=fixture()
    s.coins.Value=B.MAX_CASH-3
    local e=exitToy(s,add,update,"pon")
    assert(not e.alive and s.coins.Value==B.MAX_CASH)
end)
check("one workshop's courier cannot credit the other workshop",function()
    local h,_,s,add,update,sessions=fixture()
    local other=h:addPlayer(h:newPlayer())
    local foreign=assert(sessions[other])
    s.coins.Value=40;foreign.coins.Value=200
    local e=exitToy(s,add,update,"pon")
    assert(not e.alive and s.coins.Value==52)
    assert(foreign.coins.Value==200)
end)
check("negative control: restoring universal four-coin delivery fails positive PON fixture",function()
    local f=assert(io.open(server,"rb"))
    local original=f:read("*a");f:close()
    local broken,count=original:gsub("B%.deliveryReward%(e%.id%)","4")
    assert(count==1,"expected one server-owned courier reward call")
    local tmp=os.tmpname()
    local out=assert(io.open(tmp,"wb"));out:write(broken);out:close()
    local ok,err=pcall(function()
        local _,_,s,add,update=fixture(tmp)
        s.coins.Value=50
        local e=exitToy(s,add,update,"pon")
        assert(not e.alive and s.coins.Value==54,"old four-coin behavior required for negative control")
        local accepted=pcall(function() assert(s.coins.Value==62) end)
        assert(not accepted,"positive PON payout assertion accepted the old behavior")
    end)
    os.remove(tmp)
    assert(ok,err)
end)
print(string.format("AUTO_PON_COURIER_SUMMARY %d passed / %d failed; canonical Lua mocks, NOT Roblox engine",passed,failed))
if failed>0 then os.exit(1) end
