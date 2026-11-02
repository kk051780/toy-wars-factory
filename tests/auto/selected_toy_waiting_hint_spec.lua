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
local function fixture(selectedName,initialCoins)
    local created,remoteCalls={},{}
    local function object(class,value)
        local o={ClassName=class,Value=value,_children={},Changed=signal(),Activated=signal()}
        function o:WaitForChild(name) return assert(self._children[name],"missing "..name) end
        return o
    end
    local player=object("Player")
    local stats,status,gui=object("Folder"),object("Folder"),object("PlayerGui")
    player._children={leaderstats=stats,ToyWarsStatus=status,PlayerGui=gui}
    for k,v in pairs({Coins=initialCoins or 50,Wave=1,Defeated=0}) do stats._children[k]=object("IntValue",v) end
    for k,v in pairs({BaseHP=100,FactoryLevel=1,Allies=0,Enemies=0,RoundOutcome="",SelectedToy=selectedName or "PON"}) do
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
    assert(tip and tip.Parent and tip.Parent.ClassName=="ScreenGui" and tip.Parent.Parent==gui,
        "expected existing HUD tip, not a new overlay")
    assert(guide and guide.Visible,"existing first-play guide must survive")
    eq(buttonCount,3,"toy choice count")
    return tip,stats._children.Coins,status._children.FactoryLevel,status._children.SelectedToy,remoteCalls,buttonCount,guide
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end

check("unaffordable GUARDON gives actionable wait and retains upgrade",function()
    local tip,coins,level,selected,calls,count,guide=fixture("GUARDON",0)
    assert(tip.Text:find("WAIT",1,true) and tip.Text:find("GUARDON",1,true) and tip.Text:find("28",1,true),"waiting for GUARDON must be visible")
    assert(tip.Text:find("GOLD",1,true) and tip.Text:find("65",1,true),"gold upgrade price must survive")
    eq(count,3,"three selectors");assert(guide.Visible,"QuickStart preserved");eq(#calls,0,"display cannot fire server")
end)
check("affordable GUARDON restores ordinary gold tip after coins change",function()
    local tip,coins,level,selected,calls=fixture("GUARDON",0)
    coins.Value=28;coins.Changed:Fire()
    assert(not tip.Text:find("WAIT",1,true),"affordable selected toy must not wait")
    assert(tip.Text:find("GOLD",1,true) and tip.Text:find("65",1,true),"gold tip restored")
    eq(#calls,0,"coin refresh must not send remote")
end)
check("PON GUARDON TANKURU selection uses canonical cost threshold",function()
    local tip,coins,level,selected,calls=fixture("PON",9)
    assert(tip.Text:find("WAIT",1,true) and tip.Text:find("10",1,true),"PON cost 10")
    coins.Value=10;coins.Changed:Fire()
    assert(not tip.Text:find("WAIT",1,true),"PON affordable")
    selected.Value="GUARDON";selected.Changed:Fire()
    assert(tip.Text:find("WAIT",1,true) and tip.Text:find("28",1,true),"GUARDON cost 28")
    selected.Value="TANKURU";selected.Changed:Fire()
    assert(tip.Text:find("WAIT",1,true) and tip.Text:find("48",1,true),"TANKURU cost 48")
    coins.Value=48;coins.Changed:Fire()
    assert(not tip.Text:find("WAIT",1,true),"TANKURU affordable")
    eq(#calls,0,"selection replication and refresh must not send remote")
end)
check("gold upgrade level two and MAX survive unaffordable selection",function()
    local tip,coins,level,selected,calls=fixture("TANKURU",0)
    level.Value=2;level.Changed:Fire()
    assert(tip.Text:find("WAIT",1,true) and tip.Text:find("260",1,true) and tip.Text:find("GOLD",1,true),"level2 upgrade 260")
    level.Value=B.MAX_LEVEL;level.Changed:Fire()
    assert(tip.Text:find("MAX",1,true),"MAX remains visible")
    assert(not tip.Text:find("260",1,true) and not tip.Text:find("65",1,true),"no stale upgrade cost at MAX")
    eq(#calls,0,"level refresh cannot fire server")
end)
check("unknown selected toy fails safe and keeps normal upgrade tip",function()
    local tip,coins,level,selected,calls=fixture("UNLISTED",0)
    assert(not tip.Text:find("WAIT",1,true),"unknown toy cannot claim production wait")
    assert(tip.Text:find("65",1,true),"normal upgrade price retained")
    selected.Value="JUNK";selected.Changed:Fire()
    assert(not tip.Text:find("WAIT",1,true),"enemy is not a selectable toy")
    selected.Value="";selected.Changed:Fire()
    assert(not tip.Text:find("WAIT",1,true),"empty selection is safe")
    eq(#calls,0,"malformed replication cannot send remote")
end)
print(string.format("AUTO_SELECTED_TOY_WAITING_HINT_SUMMARY %d passed / %d failed; canonical HUD native Lua mock",passed,failed))
if failed>0 then os.exit(1) end
