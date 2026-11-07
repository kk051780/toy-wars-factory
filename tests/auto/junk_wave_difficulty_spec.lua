-- Execute the REAL source-pinned 4-toy server with deterministic Lua service mocks.
-- This is not a Roblox Studio engine test, rendering test or balance playtest.
local H=dofile('tests/roblox_server_harness.lua')
local B=dofile('src/ToyWarsBalance.lua')
local passed,failed=0,0
local function up(fn,name)
    for i=1,70 do
        local k,v=debug.getupvalue(fn,i)
        if not k then break end
        if k==name then return v end
    end
    error('missing canonical upvalue '..name)
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print('PASS '..name)
    else failed=failed+1;print('FAIL '..name..' '..tostring(err)) end
end
local function fixture()
    local h=H.new()
    local player=h:addPlayer(h:newPlayer())
    local heartbeat=h.runService.Heartbeat.listeners[1].fn
    local simulate=up(heartbeat,'simulate')
    local sessions=up(heartbeat,'sessions')
    return h,assert(sessions[player]),up(simulate,'addEntity'),up(simulate,'updateEntity')
end
check('wave1-10 keep base JUNK and wave count cap unchanged',function()
    assert(B.waveSize(10)==B.MAX_FIELD_UNITS)
    for wave=1,10 do
        local stat,why=B.junkThreat(wave)
        assert(why=='ok' and stat.hp==38 and stat.damage==6 and stat.tier==0)
    end
end)
check('tier boundaries are discrete and predictable',function()
    for wave,tier in pairs({[11]=1,[15]=1,[16]=2,[20]=2,[21]=3,[49]=8,[50]=8}) do
        local stat=B.junkThreat(wave)
        assert(stat.tier==tier and stat.hp==38+8*tier and stat.damage==6+tier)
    end
end)
check('invalid wave values reject without fallback to unlimited damage',function()
    for _,wave in ipairs({0,-1,51,1.5,math.huge,-math.huge,'20',true}) do
        local stat,why=B.junkThreat(wave)
        assert(stat==nil and why=='invalid_wave')
    end
end)
check('unit definitions stay unmodified for every wave',function()
    local origHP,origDamage=B.UNITS.junk.hp,B.UNITS.junk.damage
    for wave=1,B.MAX_WAVE do B.junkThreat(wave) end
    assert(B.UNITS.junk.hp==origHP and B.UNITS.junk.damage==origDamage)
end)
check('enemy spawn on wave50 sets HP and damage on REAL 3D model-backed entity',function()
    local h,state,spawn=fixture()
    state.wave.Value=50
    local junk=assert(spawn(state,'junk','enemy'))
    assert(junk.id=='junk' and junk.alive and junk.model.Parent)
    assert(junk.health==102 and junk.maxHealth==102 and junk.damage==14)
    assert(B.UNITS.junk.hp==38 and B.UNITS.junk.damage==6)
end)
check('server-side enemy damage actually uses the stronger per-entity value',function()
    local h,state,spawn,update=fixture()
    state.wave.Value=50
    local ally=assert(spawn(state,'guardon','ally'))
    local enemy=assert(spawn(state,'junk','enemy'))
    enemy.x=ally.x;enemy.z=ally.z
    local before=ally.health
    update(state,enemy,0.3)
    assert(before==108 and ally.health==94,'wave50 damage must be 14, not base 6')
    assert(enemy.cooldown>0)
end)
check('low-wave server attack retains existing six damage',function()
    local h,state,spawn,update=fixture()
    state.wave.Value=1
    local ally=assert(spawn(state,'guardon','ally'))
    local enemy=assert(spawn(state,'junk','enemy'))
    enemy.x=ally.x;enemy.z=ally.z
    update(state,enemy,0.3)
    assert(ally.health==102,'wave1 damage regression')
end)
check('stronger JUNK is isolated per player workshop and per wave',function()
    local h,state,spawn=fixture()
    state.wave.Value=50
    local big=assert(spawn(state,'junk','enemy'))
    state.wave.Value=1
    local small=assert(spawn(state,'junk','enemy'))
    assert(big.maxHealth==102 and big.damage==14)
    assert(small.maxHealth==38 and small.damage==6)
    assert(big.model~=small.model and big.model.Parent and small.model.Parent)
end)
check('at wave50 completion, next run reverts to wave1 threat',function()
    local h,state,spawn=fixture()
    state.wave.Value=50
    state.enemyTarget=B.waveSize(50)
    state.enemiesMade=state.enemyTarget
    state.waveBreak=0
    state.productionTimer=50
    state.enemyTimer=50
    h.runService.Heartbeat:Fire(0.3)
    assert(state.roundOutcome.Value=='VICTORY' and state.wave.Value==1)
    local first=assert(spawn(state,'junk','enemy'))
    assert(first.health==38 and first.damage==6)
end)
check('CUREBO ally repair contract remains unchanged by JUNK scaling',function()
    local h,state,spawn=fixture()
    state.wave.Value=50
    local ally=assert(spawn(state,'curebo','ally'))
    assert(ally.health==B.UNITS.curebo.hp and ally.damage==B.UNITS.curebo.damage)
    assert(ally.model.Parent and B.UNITS.curebo.repairAmount==8)
end)
assert(failed==0,string.format('JUNK_WAVE_DIFFICULTY %d passed %d failed',passed,failed))
print('AUTO_JUNK_WAVE_DIFFICULTY_SUMMARY '..passed..' passed / '..failed..' failed; actual server Lua mocked, NOT Roblox Studio')
