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
