-- JUNK CAPTAIN at every tenth wave: 3D model + server-only combat/reward checks.
-- Execute actual canonical server in Lua mocks; NOT Roblox Studio/Play/mobile.
local H=dofile("tests/roblox_server_harness.lua")
local B=dofile("src/ToyWarsBalance.lua")
local passed,failed=0,0
local function up(fn,name)
    for i=1,70 do
        local key,value=debug.getupvalue(fn,i)
        if not key then break end
        if key==name then return value end
    end
    error("missing canonical upvalue "..name)
end
local function fixture()
    local h=H.new()
    local p=h:addPlayer(h:newPlayer())
    local heart=h.runService.Heartbeat.listeners[1].fn
    local sessions=up(heart,"sessions")
    local simulate=up(heart,"simulate")
    local spawn=up(simulate,"addEntity")
    local update=up(simulate,"updateEntity")
    local kill=up(update,"killEntity")
    return h,assert(sessions[p]),spawn,update,kill
end
local function finalEnemy(state,spawn,wave)
    state.wave.Value=wave
    state.enemyTarget=B.waveSize(wave)
    state.enemiesMade=state.enemyTarget-1
    return assert(spawn(state,"junk","enemy"))
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
check("boss-wave stat calculation spans all five 10-wave milestones",function()
    for _,wave in ipairs({10,20,30,40,50}) do
        local stat,why=B.junkBoss(wave)
        local base=B.junkThreat(wave)
        assert(why=="ok" and stat.hp==base.hp*3)
        assert(stat.damage==base.damage+4 and stat.reward==40+wave*2)
    end
end)
check("ordinary waves cannot manufacture a captain through stat API",function()
    for _,wave in ipairs({1,9,11,15,19,21,29,31,49}) do
        local result,why=B.junkBoss(wave)
        assert(result==nil and why=="not_boss_wave")
    end
end)
check("invalid wave inputs never produce boss stats",function()
    for _,wave in ipairs({0,-1,51,10.5,math.huge,-math.huge,"10",true}) do
        local result,why=B.junkBoss(wave)
        assert(result==nil and why=="invalid_wave")
    end
end)
check("the penultimate enemy on boss wave is still ordinary JUNK",function()
    local _,state,spawn=fixture()
    state.wave.Value=10
    state.enemyTarget=B.waveSize(10)
    state.enemiesMade=state.enemyTarget-2
    local enemy=assert(spawn(state,"junk","enemy"))
    assert(not enemy.boss and enemy.maxHealth==38 and enemy.damage==6)
    assert(enemy.reward==8 and enemy.model.Name=="JUNK")
    assert(not enemy.model:FindFirstChild("BossCrown"))
end)
check("the final enemy on wave10 has distinct 3D crown and beacon",function()
    local _,state,spawn=fixture()
    local captain=finalEnemy(state,spawn,10)
    assert(captain.boss and captain.maxHealth==114 and captain.damage==10)
    assert(captain.reward==60 and captain.model.Name=="JUNK_CAPTAIN")
    local crown=assert(captain.model:FindFirstChild("BossCrown"))
    local beacon=assert(captain.model:FindFirstChild("BossBeacon"))
    assert(crown.Material=="Material.Neon" and beacon.Material=="Material.Neon")
    assert(crown:FindFirstChild("Caption") and captain.model:FindFirstChild("HealthBar"))
    assert(captain.model.Parent)
end)
check("the final enemy on wave50 gets the late-game boss stats",function()
    local _,state,spawn=fixture()
    local boss=finalEnemy(state,spawn,50)
    assert(boss.boss and boss.health==306 and boss.maxHealth==306)
    assert(boss.damage==18 and boss.reward==140)
    assert(B.UNITS.junk.hp==38 and B.UNITS.junk.damage==6)
end)
check("an actual server Heartbeat spawns precisely one captain at last slot",function()
    local h,state=fixture()
    state.wave.Value=20
    state.enemyTarget=B.waveSize(20)
    state.enemiesMade=state.enemyTarget-1
    state.waveBreak=0
    state.enemyTimer=0
    state.productionTimer=100
    h.runService.Heartbeat:Fire(0.3)
    assert(state.enemiesMade==state.enemyTarget)
    local bosses=0
    for _,enemy in ipairs(state.entities) do
        if enemy.boss then
            bosses=bosses+1
            assert(enemy.maxHealth==162 and enemy.reward==80)
        end
    end
    assert(bosses==1)
    h.runService.Heartbeat:Fire(0.3)
    local remaining=0
    for _,e in ipairs(state.entities) do if e.boss then remaining=remaining+1 end end
    assert(remaining==1,"no duplicate captain can spawn in a wave")
end)
check("boss damage is used in actual canonical enemy attack",function()
    local _,state,spawn,update=fixture()
    local ally=assert(spawn(state,"guardon","ally"))
    local boss=finalEnemy(state,spawn,50)
    boss.x=ally.x;boss.z=ally.z
    update(state,boss,0.3)
    assert(ally.health==90,"108 guardon HP minus 18 captain attack")
end)
check("defeating a captain pays its bonus only to allied attacker",function()
    local _,state,spawn,_,kill=fixture()
    local boss=finalEnemy(state,spawn,50)
    state.coins.Value=100
    local before=state.kills.Value
    kill(state,boss,{side="ally"})
    assert(not boss.alive and not boss.model.Parent)
    assert(state.coins.Value==240 and state.kills.Value==before+1)
end)
check("captain killed without an ally grants no extra coins",function()
    local _,state,spawn,_,kill=fixture()
    local boss=finalEnemy(state,spawn,30)
    state.coins.Value=100
    kill(state,boss,{side="enemy"})
    assert(state.coins.Value==100 and not boss.model.Parent)
end)
check("captain breaches vault for 28 but ordinary JUNK only for 12",function()
    local _,state,spawn,update=fixture()
    local boss=finalEnemy(state,spawn,10)
    boss.z=-41
    update(state,boss,0.3)
    assert(state.baseHP.Value==72 and not boss.alive and not boss.model.Parent)
    state.wave.Value=1;state.enemiesMade=0;state.enemyTarget=B.waveSize(1)
    local normal=assert(spawn(state,"junk","enemy"))
    normal.z=-41
    update(state,normal,0.3)
    assert(state.baseHP.Value==60 and not normal.alive)
end)
check("a boss cannot arise from ally side, other player's wave, or nonboss wave",function()
    local _,state,spawn=fixture()
    local allyJunk=assert(spawn(state,"junk","ally"))
    assert(not allyJunk.boss)
    local normal=finalEnemy(state,spawn,49)
    assert(not normal.boss and normal.reward==8)
    local big=finalEnemy(state,spawn,50)
    assert(big.boss)
    local low=finalEnemy(state,spawn,1)
    assert(not low.boss and low.maxHealth==38)
    assert(big.maxHealth==306,"existing per-entity boss stays unchanged after wave update")
end)
check("wave50 victory starts wave1 without leftover boss or 3D crown",function()
    local h,state,spawn,_,kill=fixture()
    local boss=finalEnemy(state,spawn,50)
    state.enemiesMade=state.enemyTarget
    state.waveBreak=0
    state.productionTimer=100
    state.enemyTimer=100
    kill(state,boss,{side="ally"})
    h.runService.Heartbeat:Fire(0.3)
    assert(state.roundOutcome.Value=="VICTORY" and state.wave.Value==1)
    assert(not boss.model.Parent)
    local fresh=assert(spawn(state,"junk","enemy"))
    assert(not fresh.boss and fresh.maxHealth==38 and fresh.model.Name=="JUNK")
end)
assert(failed==0,("JUNK_CAPTAIN_BOSS %d passed / %d failed"):format(passed,failed))
print(("AUTO_JUNK_CAPTAIN_BOSS_SUMMARY %d passed / %d failed; whole server Lua mocks, NOT Studio"):format(passed,failed))
