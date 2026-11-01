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
    for k,v in pairs({BaseHP=100,FactoryLevel=1,Allies=0,Enemies=0,SelectedToy=selectedName or "PON"}) do
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
    return tip,stats._children.Coins,status._children.FactoryLevel,status._children.SelectedToy,remoteCalls,buttonCount,guide,status._children.Allies
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end


local function has(t,s) return t.Text:find(s,1,true)~=nil end
check("full affordable displays capacity and gold",function()
 local tip,coins,lv,sel,calls,n,guide,allies=fixture("GUARDON",28)
 allies.Value=B.MAX_FIELD_UNITS;allies.Changed:Fire()
 assert(has(tip,"FIELD FULL 20/20") and has(tip,"GOLD") and has(tip,"65"))
 eq(n,3);assert(guide.Visible);eq(#calls,0)
end)
check("full overrides money wait",function()
 local tip,coins,lv,sel,calls,n,guide,allies=fixture("GUARDON",0)
 allies.Value=B.MAX_FIELD_UNITS;allies.Changed:Fire()
 assert(has(tip,"FIELD FULL 20/20") and not has(tip,"WAIT") and has(tip,"GOLD") and has(tip,"65"))
 eq(#calls,0)
end)
check("19 unaffordable keeps old WAIT",function()
 local tip,coins,lv,sel,calls,n,guide,allies=fixture("GUARDON",0)
 allies.Value=B.MAX_FIELD_UNITS-1;allies.Changed:Fire()
 assert(has(tip,"WAIT GUARDON 28 COINS") and has(tip,"GOLD") and has(tip,"65") and not has(tip,"FIELD FULL"))
 eq(#calls,0)
end)
check("19 affordable keeps ordinary gold",function()
 local tip,coins,lv,sel,calls,n,guide,allies=fixture("GUARDON",28)
 allies.Value=B.MAX_FIELD_UNITS-1;allies.Changed:Fire()
 assert(not has(tip,"WAIT") and not has(tip,"FIELD FULL") and has(tip,"GOLD") and has(tip,"65"))
 eq(#calls,0)
end)
check("allies Changed refresh and coins Changed restore",function()
 local tip,coins,lv,sel,calls,n,guide,allies=fixture("GUARDON",0)
 allies.Value=B.MAX_FIELD_UNITS;allies.Changed:Fire();assert(has(tip,"FIELD FULL"))
 allies.Value=B.MAX_FIELD_UNITS-1;allies.Changed:Fire();assert(has(tip,"WAIT GUARDON 28"))
 coins.Value=28;coins.Changed:Fire();assert(not has(tip,"WAIT") and has(tip,"GOLD"))
 allies.Value=B.MAX_FIELD_UNITS;allies.Changed:Fire();assert(has(tip,"FIELD FULL"))
 eq(#calls,0)
end)
check("level2 GOLD260 and MAX survive",function()
 local tip,coins,lv,sel,calls,n,guide,allies=fixture("TANKURU",0)
 allies.Value=B.MAX_FIELD_UNITS;allies.Changed:Fire()
 lv.Value=2;lv.Changed:Fire();assert(has(tip,"FIELD FULL") and has(tip,"GOLD") and has(tip,"260"))
 lv.Value=B.MAX_LEVEL;lv.Changed:Fire();assert(has(tip,"FIELD FULL") and has(tip,"MAX LEVEL") and not has(tip,"260"))
 eq(#calls,0)
end)
check("unknown selected toy and three selectors remain safe",function()
 local tip,coins,lv,sel,calls,n,guide,allies=fixture("UNLISTED",0)
 allies.Value=B.MAX_FIELD_UNITS;allies.Changed:Fire();assert(has(tip,"FIELD FULL"))
 sel.Value="JUNK";sel.Changed:Fire();assert(not has(tip,"WAIT"))
 sel.Value="";sel.Changed:Fire();assert(has(tip,"FIELD FULL"))
 eq(n,3);assert(guide.Visible);eq(#calls,0)
end)
print(string.format("AUTO_FIELD_CAPACITY_HUD_SUMMARY %d passed / %d failed; canonical HUD native Lua mock",passed,failed))
if failed>0 then os.exit(1) end
