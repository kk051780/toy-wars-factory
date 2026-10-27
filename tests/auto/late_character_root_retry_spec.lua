-- Whole canonical server: late character root must not strand a player in the lobby.
-- Native Lua scheduler mock only; no Roblox engine/streaming evidence.
local Harness=dofile("tests/roblox_server_harness.lua")
local server=os.getenv("TWF_SERVER_FILE") or "src/ToyWarsServer.server.lua"
local passed,failed=0,0
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
local function fixture(file)
    local h=Harness.new(file)
    return h,h:addPlayer(h:newPlayer())
end
local function lateRoot(file)
    local h,player=fixture(file)
    local character=h:character(nil,false)
    h:respawn(player,character)
    h:advance(8.1)
    assert(character._pivotCount==0,"cannot teleport without root")
    h:addRoot(character,{X=0,Y=0,Z=0})
    h:advance(8.1)
    return character._pivotCount
end
check("late root after first timeout still teleports to allocated workshop",function()
    assert(lateRoot(server)==1,"slow root must teleport exactly once")
end)
check("ready root uses original fast path",function()
    local h,player=fixture(server)
    local character=h:character()
    h:respawn(player,character)
    h:advance(0.11)
    assert(character._pivotCount==1,"normal spawn must teleport once")
end)
check("replaced character cannot be teleported by stale retry",function()
    local h,player=fixture(server)
    local stale=h:character(nil,false)
    h:respawn(player,stale)
    h:advance(8.1)
    local fresh=h:character()
    h:respawn(player,fresh)
    h:advance(0.11)
    h:addRoot(stale,{X=0,Y=0,Z=0})
    h:advance(8.1)
    assert(stale._pivotCount==0,"stale character moved")
    assert(fresh._pivotCount==1,"new character not moved")
end)
check("disconnected player cannot be teleported by retry",function()
    local h,player=fixture(server)
    local character=h:character(nil,false)
    h:respawn(player,character)
    h:advance(8.1)
    h:removePlayer(player)
    h:addRoot(character,{X=0,Y=0,Z=0})
    h:advance(8.1)
    assert(character._pivotCount==0,"removed player moved")
end)
check("missing root exits after bounded retries",function()
    local h,player=fixture(server)
    local character=h:character(nil,false)
    h:respawn(player,character)
    h:advance(25)
    assert(character._pivotCount==0,"missing root moved")
    assert(#h.queue==0,"retry coroutine should terminate")
end)
local old=".qa/server-before/src/ToyWarsServer.server.lua"
local f=io.open(old,"rb")
if f then
    local source=f:read("*a");f:close()
    if source:find('WaitForChild("HumanoidRootPart",8)',1,true) then
        check("pinned old whole server fails late-root teleport",function()
            assert(lateRoot(old)==0,"old source unexpectedly teleported")
        end)
    else print("SKIP pinned fixture lacks original eight-second wait") end
else print("SKIP pinned old-server negative control unavailable") end
print(string.format("AUTO_LATE_ROOT_SUMMARY %d passed / %d failed; whole-server Lua mock",passed,failed))
if failed>0 then os.exit(1) end
