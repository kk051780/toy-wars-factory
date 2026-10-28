-- Canonical whole-server proximity authority regression; native Lua mock only.
-- ProximityPrompt MaxActivationDistance is 12; forged Triggered at 12.5 must not act.
local H=dofile("tests/roblox_server_harness.lua")
local server="src/ToyWarsServer.server.lua"
local pinned="8a0f8816870fa4854b71c23d223728589303070a"
local passed,failed=0,0
local function eq(actual,expected,label)
    assert(actual==expected,(label or "value")..": expected "..tostring(expected)..", got "..tostring(actual))
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
local function oldSource()
    local p=assert(io.popen("git show "..pinned..":"..server.." 2>/dev/null","r"))
    local s=p:read("*a")
    assert(p:close() and #s==39993,"pinned current-main source required")
    return s
end
local function fixture(source)
    local original=loadfile
    if source then
        _G.loadfile=function(path,mode,env)
            if path==server and env then return assert(load(source,"@PINNED_PROMPT_RANGE","t",env)) end
            if env==nil then return original(path,mode) end
            return original(path,mode,env)
        end
    end
    local ok,h=pcall(H.new,server)
    _G.loadfile=original
    assert(ok,h)
    local p=h:addPlayer(h:newPlayer(h:character()))
    h:advance(0.11) -- finish deferred character teleport before setting position
    return h,p
end
local function scenario(kind,distance,source)
    local h,p=fixture(source)
    local prompt,pad=h:prompt(p,kind=="upgrade" and "UpgradeStation" or "guardonSelector")
    eq(prompt.MaxActivationDistance,12,"configured activation range")
    local root=p.Character:FindFirstChild("HumanoidRootPart")
    root.Position=h.vector(pad.Position.X+distance,pad.Position.Y,pad.Position.Z)
    local coins=assert(p:FindFirstChild("leaderstats"):FindFirstChild("Coins"))
    if kind=="upgrade" then coins.Value=65 end
    prompt.Triggered:Fire(p) -- bypass client range gate; test server authorization
    local result={coins=coins.Value,level=h:status(p,"FactoryLevel").Value,
        selected=h:status(p,"SelectedToy").Value}
    h:removePlayer(p)
    return result
end
check("selector rejects forged activation beyond configured range",function()
    local r=scenario("selector",12.5)
    eq(r.selected,"PON","out-of-range selection")
end)
check("upgrade rejects forged activation beyond configured range",function()
    local r=scenario("upgrade",12.5)
    eq(r.level,1,"out-of-range level");eq(r.coins,65,"out-of-range coins")
end)
check("both prompts still accept activation at configured 12-stud boundary",function()
    local s=scenario("selector",12)
    eq(s.selected,"GUARDON","boundary selection")
    local u=scenario("upgrade",12)
    eq(u.level,2,"boundary level");eq(u.coins,0,"boundary coins")
end)
check("pinned main accepted both out-of-range forged triggers (negative control)",function()
    local source=oldSource()
    local s=scenario("selector",12.5,source)
    eq(s.selected,"GUARDON","old selection")
    local u=scenario("upgrade",12.5,source)
    eq(u.level,2,"old level");eq(u.coins,0,"old coins")
end)
print(string.format("AUTO_PROMPT_DISTANCE_SUMMARY %d passed / %d failed; whole-server Lua mock",passed,failed))
if failed>0 then os.exit(1) end
