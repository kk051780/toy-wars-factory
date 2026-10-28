-- Execute the complete real HUD; preserve three large selectors while paging.
local B=dofile("src/ToyWarsBalance.lua")
local hud=os.getenv("TWF_HUD_FILE") or "src/ToyWarsHUD.client.lua"
local passed,failed=0,0
local function signal()
    local s={listeners={}}
    function s:Connect(fn) self.listeners[#self.listeners+1]=fn end
    function s:Fire(...) for _,fn in ipairs(self.listeners) do fn(...) end end
    return s
end
local function fixture()
    local made,calls={},{}
    local function object(class,value)
        local o={ClassName=class,Value=value,_children={},Changed=signal(),Activated=signal()}
        function o:WaitForChild(name) return assert(self._children[name],name) end
        return o
    end
    local p,stats,status=object("Player"),object("Folder"),object("Folder")
    p._children={leaderstats=stats,ToyWarsStatus=status,PlayerGui=object("PlayerGui")}
    for n,v in pairs({Coins=50,Wave=1,Defeated=0}) do stats._children[n]=object("IntValue",v) end
    for n,v in pairs({BaseHP=100,FactoryLevel=1,Allies=0,Enemies=0,SelectedToy="PON"}) do status._children[n]=object("Value",v) end
    local module=object("ModuleScript");local storage=object("ReplicatedStorage")
    storage._children={ToyWarsBalance=module,ToyWarsSelectUnit={FireServer=function(_,id) calls[#calls+1]=id end}}
    local services={Players={LocalPlayer=p},ReplicatedStorage=storage}
    local function tuple(...) return {...} end
    local env=setmetatable({game={GetService=function(_,n) return services[n] end},
        Instance={new=function(class) local o=object(class);made[#made+1]=o;return o end},
        Color3={fromRGB=tuple},UDim={new=tuple},UDim2={new=tuple,fromScale=tuple},
        Enum={Font={GothamBold="GothamBold"}},require=function(v) assert(v==module);return B end,print=function() end}, {__index=_G})
    assert(loadfile(hud,"t",env))()
    local function find(name) for _,o in ipairs(made) do if o.Name==name then return o end end end
    return find,calls,made,status
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name) else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
check("first page preserves exactly the three original toy buttons",function()
    local find,calls,made=fixture();local n=0
    for _,o in ipairs(made) do if o.ClassName=="TextButton" then n=n+1 end end
    assert(n==3 and find("pon") and find("guardon") and find("tankuru"))
    assert(find("ToyPageNavigation").Visible==false and #calls==0)
end)
check("page navigation never sends a gameplay request",function()
    local find,calls=fixture();find("GuideSkip").Activated:Fire()
    assert(find("ToyPageNavigation").Visible)
    find("ToyPageNext").Activated:Fire()
    assert(#calls==0 and find("ToyPageCaption").Text=="TOYS 2 / 2")
    local b=assert(find("curebo"));assert(b.Visible and b.Text:find("32",1,true))
    assert(b.Text:find("REPAIR ALLIES",1,true))
    b.Activated:Fire();assert(#calls==1 and calls[1]=="curebo")
end)
check("hidden empty slots cannot replay an old character request",function()
    local find,calls=fixture();find("GuideSkip").Activated:Fire();find("ToyPageNext").Activated:Fire()
    local b=assert(find("EmptyToySlot2"));assert(b.Visible==false);b.Activated:Fire()
    assert(#calls==0)
end)
check("previous wraps and original selection still works after paging",function()
    local find,calls=fixture();find("GuideSkip").Activated:Fire();find("ToyPagePrevious").Activated:Fire()
    assert(find("curebo"));find("ToyPageNext").Activated:Fire()
    find("pon").Activated:Fire();find("guardon").Activated:Fire();find("tankuru").Activated:Fire()
    assert(table.concat(calls,",")=="pon,guardon,tankuru")
end)
check("selection highlighting follows server state on the visible page",function()
    local find,calls,made,status=fixture();find("GuideSkip").Activated:Fire();find("ToyPageNext").Activated:Fire()
    status._children.SelectedToy.Value="CUREBO";status._children.SelectedToy.Changed:Fire()
    assert(find("curebo").BorderSizePixel==3)
end)
check("pager touch height and selector separation are explicit",function()
    local find=fixture();local nav=find("ToyPageNavigation");local pane=find("SelectToy")
    assert(nav.Size[4]==42 and nav.Position[4]+nav.Size[4]<pane.Position[4])
    find("GuideNext").Activated:Fire();find("GuideNext").Activated:Fire();find("GuideNext").Activated:Fire()
    assert(find("QuickStart").Visible==false and nav.Visible==true)
end)
print(string.format("AUTO_CHARACTER_PAGES_SUMMARY %d passed / %d failed; HUD mock, not phone hardware",passed,failed))
if failed>0 then os.exit(1) end
