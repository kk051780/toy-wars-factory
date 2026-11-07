-- Exact canonical server under deterministic Lua service mocks.
-- TANKURU focuses only a living in-range captain; no Roblox engine proof.
local H=dofile("tests/roblox_server_harness.lua")
local B=dofile("src/ToyWarsBalance.lua")
local passed,failed=0,0
local function up(fn,name)
    for i=1,80 do
        local k,v=debug.getupvalue(fn,i)
        if not k then break end
        if k==name then return v end
    end
    error("missing canonical upvalue: "..name)
end
local function fixture()
    local h=H.new(os.getenv("TWF_SERVER_FILE") or "src/ToyWarsServer.server.lua")
    local player=h:addPlayer(h:newPlayer())
    local heart=assert(h.runService.Heartbeat.listeners[1]).fn
    local simulate=up(heart,"simulate")
    local sessions=up(heart,"sessions")
    local s=assert(sessions[player])
    s.productionTimer=100
    s.waveBreak=100
    local add=up(simulate,"addEntity")
    local update=up(simulate,"updateEntity")
    local function entity(id,side,x,z)
        local e=assert(add(s,id,side))
        e.x=s.x+(x or 0)
        e.z=z or 0
        e.cooldown=0
        return e
    end
    local function captain(x,z)
        s.wave.Value=10
        s.enemyTarget=B.waveSize(10)
        s.enemiesMade=s.enemyTarget-1
        local e=entity("junk","enemy",x,z)
        assert(e.boss and e.damage==10)
        return e
    end
    return s,entity,captain,update
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
check("tankuru targets captain within 17 studs over nearby junk",function()
    local s,entity,captain,update=fixture()
    local artillery=entity("tankuru","ally",0,0)
    local minion=entity("junk","enemy",0,0)
    local boss=captain(0,12)
    update(s,artillery,0.3)
    assert(boss.health==boss.maxHealth-19 and minion.health==38)
    assert(artillery.cooldown>0)
end)
check("out-of-range boss never distracts ranged toy from nearby junk",function()
    local s,entity,captain,update=fixture()
    local artillery=entity("tankuru","ally",0,0)
    local minion=entity("junk","enemy",0,0)
    local boss=captain(0,18)
    update(s,artillery,0.3)
    assert(boss.health==boss.maxHealth and minion.health==19)
end)
check("dead boss is not a target",function()
    local s,entity,captain,update=fixture()
    local artillery=entity("tankuru","ally",0,0)
    local minion=entity("junk","enemy",0,0)
    local boss=captain(0,9)
    boss.alive=false
    boss.health=0
    update(s,artillery,0.3)
    assert(minion.health==19)
end)
check("a PON remains nearest-opponent focused",function()
    local s,entity,captain,update=fixture()
    local pon=entity("pon","ally",0,0)
    local minion=entity("junk","enemy",0,0)
    local boss=captain(0,4)
    update(s,pon,0.3)
    assert(minion.health==29 and boss.health==boss.maxHealth)
end)
check("boss just at artillery range can be hit",function()
    local s,entity,captain,update=fixture()
    local artillery=entity("tankuru","ally",0,0)
    local minion=entity("junk","enemy",0,0)
    local boss=captain(17,0)
    update(s,artillery,0.3)
    assert(boss.health==boss.maxHealth-19 and minion.health==38)
end)
check("closest of two in-range captains receives the shot",function()
    local s,entity,captain,update=fixture()
    local artillery=entity("tankuru","ally",0,0)
    local farther=captain(0,14)
    local nearer=captain(0,8)
    update(s,artillery,0.3)
    assert(nearer.health==nearer.maxHealth-19 and farther.health==farther.maxHealth)
end)
check("captain elimination pays the authentic server-side reward",function()
    local s,entity,captain,update=fixture()
    local artillery=entity("tankuru","ally",0,0)
    local minion=entity("junk","enemy",0,0)
    local boss=captain(0,5)
    boss.health=9
    local coins=s.coins.Value
    local kills=s.kills.Value
    update(s,artillery,0.3)
    assert(not boss.alive and minion.alive and minion.health==38)
    assert(s.coins.Value==math.min(B.MAX_CASH,coins+boss.reward))
    assert(s.kills.Value==kills+1)
end)
check("JUNK retains ordinary target selection and GUARDON shielding",function()
    local s,entity,captain,update=fixture()
    local pon=entity("pon","ally",0,0)
    local shield=entity("guardon","ally",2,0)
    local boss=captain(0,0)
    update(s,boss,0.3)
    assert(pon.health==40 and shield.health==98)
end)
print(string.format("TANKURU_CAPTAIN_TARGET_SUMMARY %d passed / %d failed; canonical-server Lua mocks only",passed,failed))
if failed>0 then os.exit(1) end
