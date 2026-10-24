-- Execute the canonical server file, not extracted/reimplemented callback snippets.
-- Deterministic Lua 5.4 mocks only; this is not Roblox engine or exploit evidence.
local Harness=dofile("tests/roblox_server_harness.lua")
local server=os.getenv("TWF_SERVER_FILE") or "src/ToyWarsServer.server.lua"
local passed,failed=0,0
local function eq(actual,expected,message) assert(actual==expected,(message or "value")..": expected "..tostring(expected)..", got "..tostring(actual)) end
local function test(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
local function fixture()
    local h=Harness.new(server)
    local p=h:newPlayer(h:character())
    h:addPlayer(p)
    h:advance(0.11)
    return h,p
end
local function positionAt(h,p,pad,distance)
    p.Character:FindFirstChild("HumanoidRootPart").Position=h.vector(pad.Position.X+distance,pad.Position.Y,pad.Position.Z)
end

test("startup admits existing players exactly once",function()
    local h=Harness.new(server,2)
    eq(h:mapCount(),2)
    h.players.PlayerAdded:Fire(h.playerList[1])
    eq(h:mapCount(),2)
    eq(#h.playerList[1]:GetChildren(),2)
end)
test("capacity remains four while extra players wait",function()
    local h=Harness.new(server)
    for _=1,6 do h:addPlayer(h:newPlayer()) end
    eq(h:mapCount(),4)
    eq(h.playerList[5]:FindFirstChild("leaderstats"),nil)
    eq(h.playerList[6]:FindFirstChild("ToyWarsStatus"),nil)
end)
test("a free plot admits one waiting player and preserves other workshops",function()
    local h=Harness.new(server)
    local players={}
    for i=1,6 do players[i]=h:addPlayer(h:newPlayer()) end
    local old=h:workshop(players[1]);local retained=h:workshop(players[2])
    h:removePlayer(players[1])
    eq(old.Parent,nil);eq(h:mapCount(),4)
    assert(h:workshop(players[5]));eq(h:workshop(players[6]),nil)
    eq(h:workshop(players[2]),retained)
end)
test("disconnected waiting player is skipped",function()
    local h=Harness.new(server);local players={}
    for i=1,6 do players[i]=h:addPlayer(h:newPlayer()) end
    h:removePlayer(players[5]);h:removePlayer(players[1])
    eq(h:workshop(players[5]),nil);assert(h:workshop(players[6]));eq(h:mapCount(),4)
end)
test("multiple departures admit remaining waiters without exceeding capacity",function()
    local h=Harness.new(server);local players={}
    for i=1,7 do players[i]=h:addPlayer(h:newPlayer()) end
    for i=1,3 do h:removePlayer(players[i]);eq(h:mapCount(),4) end
    for i=5,7 do assert(h:workshop(players[i])) end
end)
test("late join event for a disconnected player does not allocate",function()
    local h=Harness.new(server);local p=h:newPlayer()
    h.players.PlayerAdded:Fire(p)
    eq(h:mapCount(),0);eq(p:FindFirstChild("leaderstats"),nil)
end)

for _,distance in ipairs({0,12,13,13.0001,1000,math.huge}) do
    test("selector distance "..tostring(distance),function()
        local h,p=fixture();local prompt,pad=h:prompt(p,"tankuruSelector")
        positionAt(h,p,pad,distance);prompt.Triggered:Fire(p)
        eq(h:status(p,"SelectedToy").Value,distance<=13 and "TANKURU" or "PON")
    end)
end
test("selector rejects a different player",function()
    local h,p=fixture();local other=h:addPlayer(h:newPlayer(h:character()))
    local prompt,pad=h:prompt(p,"tankuruSelector");positionAt(h,other,pad,0)
    prompt.Triggered:Fire(other);eq(h:status(p,"SelectedToy").Value,"PON")
end)
test("selector rejects a missing character root",function()
    local h,p=fixture();p.Character=h:character(nil,false)
    local prompt=h:prompt(p,"tankuruSelector");prompt.Triggered:Fire(p)
    eq(h:status(p,"SelectedToy").Value,"PON")
end)
test("selector rejects NaN distance",function()
    local h,p=fixture();local prompt,pad=h:prompt(p,"tankuruSelector")
    positionAt(h,p,pad,0/0);prompt.Triggered:Fire(p)
    eq(h:status(p,"SelectedToy").Value,"PON")
end)
for _,distance in ipairs({13,13.0001,math.huge}) do
    test("upgrade distance "..tostring(distance),function()
        local h,p=fixture();local prompt,pad=h:prompt(p,"UpgradeStation")
        local coins=p:FindFirstChild("leaderstats"):FindFirstChild("Coins");coins.Value=1000
        positionAt(h,p,pad,distance);prompt.Triggered:Fire(p)
        eq(h:status(p,"FactoryLevel").Value,distance<=13 and 2 or 1)
        eq(coins.Value,distance<=13 and 935 or 1000)
    end)
end
test("upgrade rejects NaN without spending coins",function()
    local h,p=fixture();local prompt,pad=h:prompt(p,"UpgradeStation")
    local coins=p:FindFirstChild("leaderstats"):FindFirstChild("Coins");coins.Value=1000
    positionAt(h,p,pad,0/0);prompt.Triggered:Fire(p)
    eq(h:status(p,"FactoryLevel").Value,1);eq(coins.Value,1000)
end)
test("remote selection validates unit and rate limit",function()
    local h,p=fixture()
    for _,bad in ipairs({"junk","unknown",{},42}) do h.remote.OnServerEvent:Fire(p,bad);eq(h:status(p,"SelectedToy").Value,"PON") end
    h.remote.OnServerEvent:Fire(p,"guardon");eq(h:status(p,"SelectedToy").Value,"GUARDON")
    h.remote.OnServerEvent:Fire(p,"tankuru");eq(h:status(p,"SelectedToy").Value,"GUARDON")
    h:advance(0.121);h.remote.OnServerEvent:Fire(p,"tankuru");eq(h:status(p,"SelectedToy").Value,"TANKURU")
end)
test("remote selection ignores an actor with no workshop",function()
    local h,p=fixture();local outsider=h:newPlayer()
    h.remote.OnServerEvent:Fire(outsider,"tankuru");eq(h:status(p,"SelectedToy").Value,"PON")
end)

test("normal character teleports once after the deferred wait",function()
    local h=Harness.new(server);local character=h:character();local p=h:addPlayer(h:newPlayer(character))
    h:advance(0.099);eq(character._pivotCount,0)
    h:advance(0.002);eq(character._pivotCount,1)
    local floor=h:workshop(p):FindFirstChild("FeltBattlefield")
    eq(character._lastPivot.Position.X,floor.Position.X+17)
    eq(character._lastPivot.Position.Y,6);eq(character._lastPivot.Position.Z,-37)
end)
test("departure during deferred wait prevents teleport",function()
    local h=Harness.new(server);local character=h:character();local p=h:addPlayer(h:newPlayer(character))
    h:advance(0.05);h:removePlayer(p);h:advance(0.2)
    eq(character._pivotCount,0)
end)
test("replacement during deferred wait only teleports the current character",function()
    local h=Harness.new(server);local old=h:character();local p=h:addPlayer(h:newPlayer(old))
    h:advance(0.05);local current=h:character();h:respawn(p,current);h:advance(0.2)
    eq(old._pivotCount,0);eq(current._pivotCount,1)
end)
test("detached player membership prevents deferred teleport",function()
    local h=Harness.new(server);local character=h:character();local p=h:addPlayer(h:newPlayer(character))
    p.Parent=nil;h:advance(0.2);eq(character._pivotCount,0)
end)
test("missing root times out without teleport",function()
    local h=Harness.new(server);local character=h:character(nil,false)
    h:addPlayer(h:newPlayer(character));h:advance(9);eq(character._pivotCount,0)
end)
test("root arriving after departure does not revive a stale callback",function()
    local h=Harness.new(server);local character=h:character(nil,false);local p=h:addPlayer(h:newPlayer(character))
    h:removePlayer(p);h:addRoot(character,h.vector(0,0,0));h:advance(9);eq(character._pivotCount,0)
end)

print(string.format("SERVER_EVENT_SUMMARY %d passed / %d failed; Lua mocks, not Roblox engine",passed,failed))
if failed>0 then os.exit(1) end
