-- Canonical whole-server input lease fence; offline mock, not Roblox or live DataStore.
local H=dofile("tests/roblox_server_harness.lua")
local server="src/ToyWarsServer.server.lua"
local pinned="e6d41268a4fc0efcb8f8d72dd674826c6dcbe092"
local passed,failed=0,0
local function eq(a,b,label)
    assert(a==b,(label or "value")..": expected "..tostring(b)..", got "..tostring(a))
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
local function oldSource()
    local p=assert(io.popen("git show "..pinned..":"..server.." 2>/dev/null","r"))
    local s=p:read("*a")
    assert(p:close() and #s==39816,"pinned current main required")
    return s
end
local function fixture(source)
    local original=loadfile
    if source then
        _G.loadfile=function(path,mode,env)
            if path==server and env then return assert(load(source,"@PINNED_E6D41268","t",env)) end
            return original(path,mode,env)
        end
    end
    local ok,h=pcall(H.new,server)
    _G.loadfile=original
    assert(ok,h)
    local p=h:addPlayer(h:newPlayer(h:character()))
    h:advance(0.11)
    local kicked=0
    p.Kick=function() kicked=kicked+1 end
    return h,p,function() return kicked end
end
local function coins(p)
    return assert(assert(p:FindFirstChild("leaderstats")):FindFirstChild("Coins"))
end
local function scenario(action,source,elapsed)
    local h,p,kicks=fixture(source)
    local prompt,pad
    if action=="upgrade" then
        prompt,pad=h:prompt(p,"UpgradeStation")
        coins(p).Value=65
    elseif action=="pad" then
        prompt,pad=h:prompt(p,"guardonSelector")
    end
    if pad then p.Character:FindFirstChild("HumanoidRootPart").Position=pad.Position end
    h:advance(elapsed or 180)
    if prompt then prompt.Triggered:Fire(p)
    else h.remote.OnServerEvent:Fire(p,"guardon") end
    local result={money=coins(p).Value,level=h:status(p,"FactoryLevel").Value,
        selected=h:status(p,"SelectedToy").Value,kicks=kicks()}
    h:removePlayer(p)
    return result
end
check("expired upgrade prompt cannot spend or level up before Heartbeat",function()
    local r=scenario("upgrade")
    eq(r.money,65,"money");eq(r.level,1,"level");eq(r.kicks,1,"rejoin kick")
end)
check("expired proximity selector cannot change toy before Heartbeat",function()
    local r=scenario("pad")
    eq(r.selected,"PON","toy");eq(r.kicks,1,"rejoin kick")
end)
check("expired remote selector cannot change toy before Heartbeat",function()
    local r=scenario("remote")
    eq(r.selected,"PON","toy");eq(r.kicks,1,"rejoin kick")
end)
check("unexpired lease still permits all three inputs",function()
    local u=scenario("upgrade",nil,179)
    eq(u.money,0,"upgrade money");eq(u.level,2,"upgrade level");eq(u.kicks,0,"upgrade kick")
    local p=scenario("pad",nil,179)
    eq(p.selected,"GUARDON","pad");eq(p.kicks,0,"pad kick")
    local r=scenario("remote",nil,179)
    eq(r.selected,"GUARDON","remote");eq(r.kicks,0,"remote kick")
end)
check("pinned main accepts all three expired inputs (negative control)",function()
    local source=oldSource()
    local u=scenario("upgrade",source)
    eq(u.money,0,"old money");eq(u.level,2,"old level");eq(u.kicks,0,"old kick")
    local p=scenario("pad",source)
    eq(p.selected,"GUARDON","old pad");eq(p.kicks,0,"old pad kick")
    local r=scenario("remote",source)
    eq(r.selected,"GUARDON","old remote");eq(r.kicks,0,"old remote kick")
end)
print(string.format("AUTO_EXPIRED_INPUT_FENCE_SUMMARY %d passed / %d failed",passed,failed))
if failed>0 then os.exit(1) end
