-- Combined PR98 CUREBO + PR179 server outcome, native Lua mock.
-- Purpose: prove the actual 4-toy HUD remains usable during and after results.
-- Not Roblox Studio/mobile device rendering or network proof.
local B=dofile("src/ToyWarsBalance.lua")
local source=os.getenv("TWF_HUD_FILE") or "src/ToyWarsHUD.client.lua"
local pass,fail=0,0
local function signal()
    local v={listeners={}}
    function v:Connect(fn) self.listeners[#self.listeners+1]=fn end
    function v:Fire(...) for _,fn in ipairs(self.listeners) do fn(...) end end
    return v
end
local function object(class,value)
    local o={ClassName=class,Value=value,_children={},Changed=signal(),Activated=signal(),ChildAdded=signal()}
    function o:FindFirstChild(name) return self._children[name] end
    function o:WaitForChild(name) return assert(self._children[name],name) end
    return o
end
local function fixture(late,race)
    local made,calls={},{}
    local player=object("Player")
    local stats,status,gui=object("Folder"),object("Folder"),object("PlayerGui")
    player._children={leaderstats=stats,ToyWarsStatus=status,PlayerGui=gui}
    for name,value in pairs({Coins=50,Wave=1,Defeated=0}) do stats._children[name]=object("IntValue",value) end
    for name,value in pairs({BaseHP=100,FactoryLevel=1,Allies=0,Enemies=0,SelectedToy="PON"}) do
        status._children[name]=object("Value",value)
    end
    if not late then status._children.RoundOutcome=object("StringValue","") end
    if race then
        assert(late)
        local connect=status.ChildAdded.Connect
        function status.ChildAdded:Connect(fn)
            local child=object("StringValue","VICTORY")
            child.Name="RoundOutcome"
            status._children.RoundOutcome=child
            self:Fire(child) -- race: event occurs before listener subscribes
            return connect(self,fn)
        end
    end
    local module=object("ModuleScript")
    local storage=object("ReplicatedStorage")
    storage._children={ToyWarsBalance=module,ToyWarsSelectUnit={
        FireServer=function(_,id) calls[#calls+1]=id end
    }}
    local services={Players={LocalPlayer=player},ReplicatedStorage=storage}
    local function tuple(...) return {...} end
    local environment=setmetatable({
        game={GetService=function(_,name) return assert(services[name]) end},
        Instance={new=function(class) local v=object(class);made[#made+1]=v;return v end},
        Color3={fromRGB=tuple},UDim={new=tuple},UDim2={new=tuple},
        Enum={Font={GothamBold="GothamBold"}},
        require=function(x) assert(x==module);return B end,
        print=function()end,
    },{__index=_G})
    assert(loadfile(source,"t",environment))()
    local f={status=status,calls=calls}
    function f:find(name)
        for _,v in ipairs(made) do if v.Name==name then return v end end
    end
    function f:result(value)
        local child=status._children.RoundOutcome
        if not child then
            child=object("StringValue","")
            child.Name="RoundOutcome"
            status._children.RoundOutcome=child
            status.ChildAdded:Fire(child)
        end
        child.Value=value
        child.Changed:Fire()
    end
    return f
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then pass=pass+1;print("PASS "..name)
    else fail=fail+1;print("FAIL "..name..": "..tostring(err)) end
end
check("four real playable toys and CUREBO repair data survive the combination",function()
    assert(#B.PLAYABLE_IDS==4)
    assert(B.UNITS.curebo.cost==32 and B.UNITS.curebo.repairAmount==8)
    for _,id in ipairs(B.PLAYABLE_IDS) do assert(B.isUnit(id)) end
end)
check("LOSS dismisses guide, reveals page two and allows CUREBO selection",function()
    local f=fixture()
    assert(f:find("QuickStart").Visible and not f:find("ToyPageNavigation").Visible)
    f:result("LOSS")
    assert(not f:find("QuickStart").Visible and f:find("ToyPageNavigation").Visible)
    local banner=assert(f:find("RoundResultBanner"))
    assert(banner.Visible and banner.Text:find("BASE LOST",1,true))
    f:find("ToyPageNext").Activated:Fire()
    local curebo=assert(f:find("curebo"))
    assert(curebo.Visible and curebo.Text:find("REPAIR ALLIES",1,true))
    curebo.Activated:Fire()
    assert(#f.calls==1 and f.calls[1]=="curebo")
end)
check("VICTORY and return to neutral preserve the page navigation",function()
    local f=fixture()
    f:result("VICTORY")
    local banner=assert(f:find("RoundResultBanner"))
    assert(banner.Visible and banner.Text:find("WAVE 50 CLEARED",1,true))
    assert(f:find("ToyPageNavigation").Visible)
    f:result("")
    assert(not banner.Visible and f:find("ToyPageNavigation").Visible)
    f:find("ToyPageNext").Activated:Fire()
    assert(f:find("curebo").Visible)
end)
check("late RoundOutcome replicates without blocking four-toy HUD",function()
    local f=fixture(true)
    assert(not f.status._children.RoundOutcome)
    assert(not f:find("ToyPageNavigation").Visible)
    f:result("VICTORY")
    assert(f:find("RoundResultBanner").Visible and f:find("ToyPageNavigation").Visible)
end)
check("find-then-subscribe race still reveals outcome and fourth toy",function()
    local f=fixture(true,true)
    local banner=assert(f:find("RoundResultBanner"))
    assert(banner.Visible and banner.Text:find("WAVE 50 CLEARED",1,true))
    assert(f:find("ToyPageNavigation").Visible)
end)
print(string.format("AUTO_CUREBO_ROUND_RESULT_INTEGRATION_SUMMARY %d passed / %d failed; whole HUD Lua mock, NOT Roblox Studio",pass,fail))
if fail>0 then os.exit(1) end
