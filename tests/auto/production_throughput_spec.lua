-- Real canonical four-toy/Boss PvE production path, deterministic Lua mocks only.
-- No Roblox Studio, network, mobile or player-play balancing is implied.
local H=dofile('tests/roblox_server_harness.lua')
local B=dofile('src/ToyWarsBalance.lua')
local passed,failed=0,0
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print('PASS '..name)
    else failed=failed+1;print('FAIL '..name..': '..tostring(err)) end
end
local function near(actual,expected)
    assert(math.abs(actual-expected)<0.000001,tostring(actual)..' != '..tostring(expected))
end
local function up(fn,name)
    for i=1,80 do
        local k,v=debug.getupvalue(fn,i)
        if not k then break end
        if k==name then return v end
    end
    error('missing real server upvalue '..name)
end
local function fixture()
    local h=H.new()
    local player=h:addPlayer(h:newPlayer(h:character()))
    h:advance(.11)
    local heartbeat=assert(h.runService.Heartbeat.listeners[1]).fn
    local state=assert(up(heartbeat,'sessions')[player])
    return h,player,state
end
local function beats(h,n)
    for i=1,n do h.runService.Heartbeat:Fire(0.3) end
end
local function printerText(h,p)
    local machine=assert(h:workshop(p):FindFirstChild('ToyPrinter'))
    local bb=assert(machine:FindFirstChild('Caption'))
    return assert(bb:FindFirstChild('TextLabel')).Text
end
local function upgrade(h,p)
    local prompt,pad=h:prompt(p,'UpgradeStation')
    p.Character:FindFirstChild('HumanoidRootPart').Position=h.vector(pad.Position.X,pad.Position.Y,pad.Position.Z)
    prompt.Triggered:Fire(p)
end
check('levels1..6 have deterministic 3.0..1.5-second intervals',function()
    for i=1,6 do
        local interval,status=B.productionInterval(i)
        assert(status=='ok')
        near(interval,3.0-.3*(i-1))
        if i>1 then assert(interval < B.productionInterval(i-1)) end
    end
    near(B.productionInterval(1),3.0)
    near(B.productionInterval(6),1.5)
end)
check('invalid levels are rejected, not promoted to faster or zero production',function()
    for _,bad in ipairs({0,-1,7,1.5,math.huge,-math.huge,'6',true}) do
        local interval,reason=B.productionInterval(bad)
        assert(interval==nil and reason=='invalid_level')
    end
    assert(B.productionInterval(0/0)==nil)
end)
check('original level1 machine shows accurate 3.0s production label',function()
    local h,p,s=fixture()
    assert(s.level.Value==1)
    assert(printerText(h,p)=='TOY PRINTER\n3.0s / toy')
end)
check('real proximity upgrade Lv1->Lv2 changes printer label immediately',function()
    local h,p,s=fixture()
    s.coins.Value=1000
    upgrade(h,p)
    assert(s.level.Value==2 and s.coins.Value==935)
    assert(printerText(h,p)=='TOY PRINTER\n2.7s / toy')
    assert(s.productionTimer==1.2,'upgrade must not print free toy immediately')
end)
check('out-of-range upgrade cannot spend money or accelerate printer',function()
    local h,p,s=fixture()
    s.coins.Value=1000
    local prompt,pad=h:prompt(p,'UpgradeStation')
    p.Character:FindFirstChild('HumanoidRootPart').Position=h.vector(pad.Position.X+100,pad.Position.Y,pad.Position.Z)
    prompt.Triggered:Fire(p)
    assert(s.level.Value==1 and s.coins.Value==1000)
    assert(printerText(h,p)=='TOY PRINTER\n3.0s / toy')
end)
check('level6 machine reaches the 1.5s floor with upgrade label matching',function()
    local h,p,s=fixture()
    s.coins.Value=50000
    for _=1,5 do upgrade(h,p) end
    assert(s.level.Value==6)
    assert(printerText(h,p)=='TOY PRINTER\n1.5s / toy')
    near(B.productionInterval(s.level.Value),1.5)
end)
check('upgrading alters subsequent authoritative production cadence',function()
    local h,p,s=fixture()
    s.coins.Value=1000
    s.productionTimer=.1
    s.waveBreak=30
    beats(h,1)
    assert(#s.entities==1 and s.entities[1].id=='pon')
    near(s.productionTimer,2.8)
    upgrade(h,p)
    assert(s.level.Value==2)
    beats(h,10)
    assert(#s.entities==2,'first post-upgrade toy produced')
    near(s.productionTimer,2.5)
    beats(h,9)
    assert(#s.entities==3,'new interval 2.7 seconds, not old 3.0')
    near(s.productionTimer,2.5)
end)
check('fast factory still buys every ally; no free printing on insufficient coins',function()
    local h,p,s=fixture()
    s.level.Value=6
    s.selected='guardon'
    s.coins.Value=0
    s.incomeCarry=0
    s.productionTimer=.1
    beats(h,1)
    assert(#s.entities==0 and s.coins.Value>=0)
    near(s.productionTimer,1.3)
end)
check('level6 repeated prints respect cost and can fill at most 20 allies',function()
    local h,p,s=fixture()
    s.level.Value=6
    s.coins.Value=9999
    s.productionTimer=.1
    s.waveBreak=100
    beats(h,115)
    assert(#s.entities<=B.MAX_FIELD_UNITS,'must never exceed field cap')
    assert(s.coins.Value>=0 and s.coins.Value<=B.MAX_CASH)
end)
check('only one toy per Heartbeat even when dt overshoots interval',function()
    local h,p,s=fixture()
    s.level.Value=6
    s.coins.Value=1000
    s.productionTimer=-5
    s.waveBreak=100
    beats(h,1)
    assert(#s.entities==1)
    assert(s.productionTimer<0,'one beat does not mint backlogged toys')
end)
check('CUREBO and boss remain unchanged while printer throughput increases',function()
    local h,p,s=fixture()
    s.level.Value=6
    s.selected='curebo'
    s.coins.Value=500
    s.productionTimer=.1
    s.waveBreak=100
    beats(h,1)
    assert(#s.entities==1 and s.entities[1].id=='curebo')
    assert(s.entities[1].maxHealth==56 and B.UNITS.curebo.repairAmount==8)
    local captain=B.junkBoss(50)
    assert(captain.hp==306 and captain.damage==18 and captain.reward==140)
end)
print(string.format('AUTO_FACTORY_THROUGHPUT_SUMMARY %d passed / %d failed; whole-server Lua mocks, NOT Studio',passed,failed))
if failed>0 then os.exit(1) end
