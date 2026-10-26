-- Execute the canonical HUD against deterministic UI mocks: no rendering/Roblox runtime.
local hud = os.getenv("TWF_HUD_FILE") or "src/ToyWarsHUD.client.lua"
local passed,failed=0,0
local function eq(a,b,label)
    assert(a==b,(label or "value")..": expected "..tostring(b)..", got "..tostring(a))
end
local function signal()
    local s={listeners={}}
    function s:Connect(fn) self.listeners[#self.listeners+1]=fn end
    function s:Fire(...) for _,fn in ipairs(self.listeners) do fn(...) end end
    return s
end
local function fixture()
    local created,calls={},{}
    local balance=assert(loadfile("src/ToyWarsBalance.lua"))()
    local function object(class,value)
        local o={ClassName=class,Value=value,_children={},Changed=signal(),Activated=signal()}
        function o:WaitForChild(name) return assert(self._children[name],"fixture missing "..name) end
        return o
    end
    local player,stats,status,gui=object("Player"),object("Folder"),object("Folder"),object("PlayerGui")
    player._children={leaderstats=stats,ToyWarsStatus=status,PlayerGui=gui}
    for id,v in pairs({Coins=50,Wave=1,Defeated=0}) do stats._children[id]=object("IntValue",v) end
    for id,v in pairs({BaseHP=100,FactoryLevel=1,Allies=0,Enemies=0,SelectedToy="PON"}) do
        status._children[id]=object("Value",v)
    end
    local module={}
    local remote={FireServer=function(_,value) calls[#calls+1]=value end}
    local storage=object("ReplicatedStorage")
    storage._children={ToyWarsBalance=module,ToyWarsSelectUnit=remote}
    local services={Players={LocalPlayer=player},ReplicatedStorage=storage}
    local function tuple(...) return {...} end
    local env=setmetatable({
        game={GetService=function(_,name) return assert(services[name],"unsupported service") end},
        Instance={new=function(class) local o=object(class);created[#created+1]=o;return o end},
        Color3={fromRGB=tuple},UDim={new=tuple},UDim2={new=tuple,fromScale=tuple},
        Enum={Font={GothamBold="GothamBold"}},
        require=function(value) eq(value,module,"balance module");return balance end,
        print=function() end,
    },{__index=_G})
    assert(loadfile(hud,"t",env))()
    local found,selection={},0
    for _,o in ipairs(created) do
        if o.Name then found[o.Name]=o end
        if o.ClassName=="TextButton" then selection=selection+1 end
    end
    return found,selection,calls,stats,status
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
check("starts with a visible first-play guide without changing three toy buttons",function()
    local f,count=fixture()
    eq(count,3,"purchasable button count")
    eq(f.QuickStart.Visible,true,"guide initially visible")
    assert(f.QuickStart.ClassName=="Frame","quick start frame")
    assert(f.GuideNext.ClassName=="ImageButton" and f.GuideSkip.ClassName=="ImageButton","touch actions")
    assert(f.StatusPanel.ZIndex==nil or f.QuickStart.ZIndex>f.StatusPanel.ZIndex,"guide foreground")
end)
check("next moves through all three lessons and PLAY dismisses the guide",function()
    local f=fixture()
    local guide,go=f.QuickStart,f.GuideNext
    local message=f.GuideStepText
    assert(message.Text:match("^1/3"),"initial page 1")
    go.Activated:Fire()
    assert(message.Text:match("^2/3"),"shows page 2 instructions")
    eq(guide.Visible,true,"page two visible")
    go.Activated:Fire()
    assert(message.Text:match("^3/3"),"shows page 3 instructions")
    eq(f.GuideNextCaption.Text,"PLAY","final button label")
    eq(guide.Visible,true,"page three visible")
    go.Activated:Fire()
    eq(guide.Visible,false,"guide closed")
    go.Activated:Fire()
    eq(guide.Visible,false,"dismissed guide stays closed")
end)
check("SKIP dismisses guide without gameplay requests",function()
    local f,count,calls=fixture()
    f.GuideSkip.Activated:Fire()
    eq(f.QuickStart.Visible,false,"dismissed")
    eq(#calls,0,"no remote calls")
    eq(count,3,"three buttons retained")
    f.pon.Activated:Fire()
    eq(calls[1],"pon","gameplay selection still works")
end)
check("tutorial buttons are isolated from server authority and stats changes",function()
    local f,count,calls,stats,status=fixture()
    f.GuideNext.Activated:Fire()
    f.GuideSkip.Activated:Fire()
    eq(#calls,0,"no gameplay event from tutorial")
    stats._children.Coins.Value=88
    stats._children.Coins.Changed:Fire()
    -- A HUD state refresh must not make the guide reappear.
    eq(f.QuickStart.Visible,false,"stays dismissed after value change")
    eq(count,3,"original choices retained")
end)
print(string.format("AUTO_HUD_QUICKSTART_SUMMARY %d passed / %d failed; canonical HUD Lua mock, not Roblox UI",passed,failed))
if failed>0 then os.exit(1) end
