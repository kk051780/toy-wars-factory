-- Real canonical server's server-owned outcome announcement; native Lua mocks only.
-- These are deterministic state/logic tests, NOT Roblox Studio or network proof.
local Harness = dofile("tests/roblox_server_harness.lua")
local B = dofile("src/ToyWarsBalance.lua")
local source = os.getenv("TWF_SERVER_FILE") or "src/ToyWarsServer.server.lua"
local passed, failed = 0, 0
local function eq(actual, expected, name)
    assert(actual == expected, (name or "value")..": expected "..tostring(expected)..", got "..tostring(actual))
end
local function check(name, fn)
    local ok, err = pcall(fn)
    if ok then passed = passed+1; print("PASS "..name)
    else failed=failed+1; print("FAIL "..name..": "..tostring(err)) end
end
local function fixture()
    local h=Harness.new(source)
    local p=h:addPlayer(h:newPlayer())
    local stats=assert(p:FindFirstChild("leaderstats"))
    local c=assert(stats:FindFirstChild("Coins"))
    local w=assert(stats:FindFirstChild("Wave"))
    local hp=assert(h:status(p,"BaseHP"))
    local result=h:status(p,"RoundOutcome")
    return h,p,c,w,hp,result
end
local function beat(h,coins)
    coins.Value=0 -- force unopposed JUNK; no client commands or purchased allies
    h.runService.Heartbeat:Fire(0.3)
end
local function stateFor(h,p)
    local listener=assert(h.runService.Heartbeat.listeners[1]).fn
    for i=1,48 do
        local key,value=debug.getupvalue(listener,i)
        if not key then break end
        if key=="sessions" then return assert(value[p],"session not found") end
    end
    error("canonical server session upvalue not found")
end

check("new session has a neutral replicated RoundOutcome StringValue",function()
    local h,p,coins,wave,hp,result=fixture()
    assert(result and result.ClassName=="StringValue","missing server-owned outcome")
    eq(result.Value,"","no result at first join")
    eq(wave.Value,1,"new run wave")
end)

check("ordinary wave advance is not misclassified as loss or final victory",function()
    local h,p,coins,wave,hp,result=fixture()
    assert(result,"result status missing")
    local advanced=false
    for _=1,105 do
        beat(h,coins)
        if wave.Value==2 then advanced=true; break end
    end
    assert(advanced,"canonical wave one did not complete")
    eq(result.Value,"","intermediate wave has no outcome")
end)

check("authentic base damage reset emits LOSS and clears after four-second grace",function()
    local h,p,coins,wave,hp,result=fixture()
    assert(result,"result status missing")
    local sawSecond,reset=false,false
    for _=1,220 do
        beat(h,coins)
        if wave.Value==2 then sawSecond=true end
        if sawSecond and wave.Value==1 and hp.Value==100 then reset=true;break end
    end
    assert(sawSecond and reset,"whole-server base loss was not reached")
    eq(result.Value,"LOSS","loss from authoritative server branch")
    for _=1,12 do
        beat(h,coins)
        eq(result.Value,"LOSS","outcome remains visible during grace")
    end
    for _=1,5 do beat(h,coins) end
    eq(result.Value,"","outcome clears after restart grace")
end)

check("final-wave server clear announces VICTORY instead of LOSS",function()
    local h,p,coins,wave,hp,result=fixture()
    assert(result,"result status missing")
    local s=stateFor(h,p)
    -- Arrange the canonical server's after-final-enemy state directly.
    -- The tested code is the real Heartbeat; this is not a full 50-wave playthrough.
    s.wave.Value=B.MAX_WAVE
    s.enemyTarget=B.waveSize(B.MAX_WAVE)
    s.enemiesMade=s.enemyTarget
    s.entities={}
    s.waveBreak=0
    s.baseHP.Value=100
    h.runService.Heartbeat:Fire(0.3)
    eq(wave.Value,1,"post-final-wave starts new run")
    eq(result.Value,"VICTORY","server recognizes MAX_WAVE complete")
    eq(hp.Value,100,"victory preserves vault")
    for _=1,15 do h.runService.Heartbeat:Fire(0.3) end
    eq(result.Value,"VICTORY","five-second victory notice")
    for _=1,3 do h.runService.Heartbeat:Fire(0.3) end
    eq(result.Value,"","victory notice expires")
end)

check("final-wave victory clears surviving toys and restores vault for a fresh run",function()
    local h,p,coins,wave,hp,result=fixture()
    local s=stateFor(h,p)
    s.productionTimer=0.1
    h.runService.Heartbeat:Fire(0.3)
    local ally
    for _,e in ipairs(s.entities) do if e.side=="ally" then ally=e;break end end
    assert(ally and ally.alive and ally.model.Parent,"actual PON must spawn for this test")
    local model=ally.model
    s.wave.Value=B.MAX_WAVE
    s.enemyTarget=B.waveSize(B.MAX_WAVE)
    s.enemiesMade=s.enemyTarget
    s.enemyTimer=20
    s.waveBreak=0
    s.productionTimer=20
    s.incomeCarry=0
    s.baseHP.Value=49
    s.coins.Value=150
    local previousLevel=s.level.Value
    local previousKills=s.kills.Value
    h.runService.Heartbeat:Fire(0.3)
    eq(result.Value,"VICTORY","server announces the actual completed final wave")
    eq(wave.Value,1,"new cycle starts at wave one")
    eq(hp.Value,100,"victory starts the new run with full vault HP")
    eq(#s.entities,0,"victory removes previous run field units")
    assert(model.Parent==nil and not ally.alive,"old 3D ally model must be destroyed")
    eq(s.enemyTarget,B.waveSize(1),"new run uses first-wave enemy size")
    eq(s.waveBreak,5,"new run retains result announcement grace")
    eq(s.productionTimer,1,"new cycle starts normal production cadence")
    eq(s.level.Value,previousLevel,"factory upgrade is retained")
    eq(s.kills.Value,previousKills,"defeated counter is retained")
    assert(s.coins.Value>=150+B.waveReward(B.MAX_WAVE),"wave victory rewards coins")
end)

check("ordinary wave 49 to 50 keeps surviving toys and earned vault HP",function()
    local h,p,coins,wave,hp,result=fixture()
    local s=stateFor(h,p)
    s.productionTimer=0.1
    h.runService.Heartbeat:Fire(0.3)
    local ally
    for _,e in ipairs(s.entities) do if e.side=="ally" then ally=e;break end end
    assert(ally and ally.model.Parent,"ordinary wave has a living toy")
    s.wave.Value=B.MAX_WAVE-1
    s.enemyTarget=B.waveSize(B.MAX_WAVE-1)
    s.enemiesMade=s.enemyTarget
    s.enemyTimer=20
    s.waveBreak=0
    s.productionTimer=20
    s.baseHP.Value=49
    h.runService.Heartbeat:Fire(0.3)
    eq(wave.Value,B.MAX_WAVE,"wave 49 should advance to wave 50")
    eq(result.Value,"","only full completion signals victory")
    eq(hp.Value,67,"ordinary wave only grants the existing 18 HP recovery")
    assert(ally.alive and ally.model.Parent and #s.entities>0,
           "ordinary wave keeps surviving allies for the next battle")
end)

check("outcome belongs only to the affected player",function()
    local h=Harness.new(source)
    local a=h:addPlayer(h:newPlayer())
    local b=h:addPlayer(h:newPlayer())
    local resultA=assert(h:status(a,"RoundOutcome"))
    local resultB=assert(h:status(b,"RoundOutcome"))
    local s=stateFor(h,a)
    s.baseHP.Value=0
    h.runService.Heartbeat:Fire(0.3)
    eq(resultA.Value,"LOSS","affected player")
    eq(resultB.Value,"","unaffected other workshop")
end)

check("temporary outcome never enters persisted progress schema",function()
    local h,p,coins,wave,hp,result=fixture()
    assert(result,"outcome status missing")
    local s=stateFor(h,p)
    s.baseHP.Value=0
    h.runService.Heartbeat:Fire(0.3)
    eq(result.Value,"LOSS","live server signal")
    h:removePlayer(p)
    local store=h.services.DataStoreService:GetDataStore("ToyWarsProgressV1")
    local saved=assert(store:GetAsync("p:"..tostring(p.UserId)))
    eq(saved.RoundOutcome,nil,"not stored with persistent progress")
    eq(saved.wave,1,"progress resets to wave one")
end)

print(string.format("AUTO_ROUND_OUTCOME_SERVER_SUMMARY %d passed / %d failed; canonical whole-server Lua mock, NOT Studio",passed,failed))
if failed>0 then os.exit(1) end
