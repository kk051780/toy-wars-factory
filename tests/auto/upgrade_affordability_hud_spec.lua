-- Whole canonical HUD fixture: upgrade tip must follow authoritative balance, not local hard-coded prices.
-- Native Lua mocks only; no Roblox rendering/device assertions.
local hud=os.getenv("TWF_HUD_FILE") or "src/ToyWarsHUD.client.lua"
local B=assert(loadfile("src/ToyWarsBalance.lua"))()
local passed,failed=0,0
local function eq(actual,expected,label)
    assert(actual==expected,(label or "value")..": expected "..tostring(expected)..", got "..tostring(actual))
end
local function signal()
    local s={listeners={}}
    function s:Connect(fn) self.listeners[#self.listeners+1]=fn end
    function s:Fire(...) for _,fn in ipairs(self.listeners) do fn(...) end end
    return s
end
local function fixture()
    local created,remoteCalls={},{}
    local function object(class,value)
        local o={ClassName=class,Value=value,_children={},Changed=signal(),Activated=signal()}
        function o:WaitForChild(name) return assert(self._children[name],"missing "..name) end
        return o
    end
    local player=object("Player")
    local stats,status,gui=object("Folder"),object("Folder"),object("PlayerGui")
    player._children={leaderstats=stats,ToyWarsStatus=status,PlayerGui=gui}
    for k,v in pairs({Coins=50,Wave=1,Defeated=0}) do stats._children[k]=object("IntValue",v) end
    for k,v in pairs({BaseHP=100,FactoryLevel=1,Allies=0,Enemies=0,SelectedToy="PON"}) do
        status._children[k]=object("Value",v)
    end
    local module=object("ModuleScript")
    local remote={FireServer=function(_,id) remoteCalls[#remoteCalls+1]=id end}
    local storage=object("ReplicatedStorage")
    storage._children={ToyWarsBalance=module,ToyWarsSelectUnit=remote}
    local services={Players={LocalPlayer=player},ReplicatedStorage=storage}
    local function tuple(...) return {...} end
    local env=setmetatable({
        game={GetService=function(_,name) return assert(services[name]) end},
        Instance={new=function(class) local o=object(class);created[#created+1]=o;return o end},
        Color3={fromRGB=tuple},UDim={new=tuple},UDim2={new=tuple},
        Enum={Font={GothamBold="GothamBold"}},
        require=function(x) eq(x,module,"balance");return B end,
        print=function() end,
    },{__index=_G})
    assert(loadfile(hud,"t",env))()
    local tip,guide,buttonCount
    buttonCount=0
    for _,o in ipairs(created) do
        if o.TextStrokeTransparency==0.4 then tip=o end
        if o.Name=="QuickStart" then guide=o end
        if o.ClassName=="TextButton" then buttonCount=buttonCount+1 end
    end
    assert(tip and tip.Parent==gui,"expected existing HUD tip, not a new overlay")
    assert(guide and guide.Visible,"existing first-play guide must survive")
    eq(buttonCount,3,"toy choice count")
    return tip,stats._children.Coins,status._children.FactoryLevel,remoteCalls
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
check("level one tip shows canonical 65-coin gold upgrade",function()
    local tip,coins,level,calls=fixture()
    eq(level.Value,1)
    local price=B.upgradePrice(level.Value)
    eq(price,65)
    assert(tip.Text:find(tostring(price),1,true) and tip.Text:find("GOLD",1,true),
        "tip must show current gold upgrade price")
    eq(#calls,0,"no remote commands on HUD load")
end)
check("level change updates next price and coins change never sends gameplay command",function()
    local tip,coins,level,calls=fixture()
    level.Value=2;level.Changed:Fire()
    eq(B.upgradePrice(level.Value),260)
    assert(tip.Text:find("260",1,true) and tip.Text:find("GOLD",1,true),
        "tip must show new canonical upgrade price")
    coins.Value=500;coins.Changed:Fire()
    assert(tip.Text:find("260",1,true),"coin refresh must retain current price")
    eq(#calls,0,"no remote commands from display refresh")
end)
check("maximum level displays MAX without a stale upgrade price",function()
    local tip,coins,level,calls=fixture()
    level.Value=B.MAX_LEVEL;level.Changed:Fire()
    eq(B.upgradePrice(level.Value),nil,"no upgrade at max")
    assert(tip.Text:find("MAX",1,true),"tip must show max level")
    assert(not tip.Text:find("65",1,true) and not tip.Text:find("260",1,true),
        "max tip must not show a stale upgrade price")
    eq(#calls,0,"no remote commands at max level")
end)
print(string.format("AUTO_UPGRADE_AFFORDABILITY_HUD_SUMMARY %d passed / %d failed; canonical HUD native Lua mock",passed,failed))
if failed>0 then os.exit(1) end
