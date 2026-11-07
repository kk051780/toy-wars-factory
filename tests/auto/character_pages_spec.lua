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
-- Legacy cases use an explicit four-unit fixture, never a frozen live roster.
local function fixture(roster,waitingOn)
    local rules=dofile("src/ToyWarsBalance.lua")
    rules.PLAYABLE_IDS=roster or {"pon","guardon","tankuru","curebo"}
    for _,id in ipairs(rules.PLAYABLE_IDS) do
        if not rules.UNITS[id] then rules.UNITS[id]={name=string.upper(id),cost=41} end
    end
    local made,calls={},{}
    local function object(class,value)
        local o={ClassName=class,Value=value,_children={},Changed=signal(),Activated=signal()}
        function o:WaitForChild(name)
            if name==waitingOn then
                local notice
                for _,v in ipairs(made) do if v.Name=="WorkshopQueueNotice" then notice=v end end
                assert(notice and notice.Text:find(name=="leaderstats" and "Waiting" or "Preparing",1,true),"queue/preparing feedback before yield")
                coroutine.yield(0.2)
            end
            return assert(self._children[name],name)
        end
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
        Enum={Font={GothamBold="GothamBold"}},require=function(v) assert(v==module);return rules end,print=function() end}, {__index=_G})
    local chunk=assert(loadfile(hud,"t",env))
    local thread=coroutine.create(chunk)
    local ok,err=coroutine.resume(thread);assert(ok,err)
    local function find(name) for _,o in ipairs(made) do if o.Name==name then return o end end end
    local function resume() local success,e=coroutine.resume(thread);assert(success,e) end
    return find,calls,made,status,resume,stats
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
check("first-play guide explains PON courier without breaking exact button prices",function()
    local find=fixture()
    local reward=assert(B.deliveryReward("pon"))
    local guide=assert(find("GuideStepText"))
    assert(guide.Text:find("COURIER +"..reward,1,true))
    for _,id in ipairs({"pon","guardon","tankuru"}) do
        local button=assert(find(id))
        assert(button.Text==string.upper(id).." | "..B.UNITS[id].cost,
               "button must retain canonical one-line unit name and exact price")
    end
end)
check("boss forecast appears only on imminent and milestone waves",function()
    local find,calls,_,_,_,stats=fixture()
    local banner=assert(find("BossWaveWarning"))
    local wave=assert(stats._children.Wave)
    local cases={
        {1,""},{7,""},{8,"CAPTAIN IN 2 WAVES"},{9,"CAPTAIN NEXT WAVE"},
        {10,"JUNK CAPTAIN\nWAVE 10"},{11,""},{18,"CAPTAIN IN 2 WAVES"},
        {19,"CAPTAIN NEXT WAVE"},{20,"JUNK CAPTAIN\nWAVE 20"},
        {21,""},{38,"CAPTAIN IN 2 WAVES"},{39,"CAPTAIN NEXT WAVE"},
        {40,"JUNK CAPTAIN\nWAVE 40"},{47,""},
        {49,"CAPTAIN NEXT WAVE"},{50,"JUNK CAPTAIN\nWAVE 50"},
    }
    for _,case in ipairs(cases) do
        wave.Value=case[1];wave.Changed:Fire()
        assert(banner.Text==case[2],"wrong boss hint on wave "..case[1]..
            ": "..tostring(banner.Text))
        assert(banner.Visible==(case[2]~=""),"wrong visibility on wave "..case[1])
    end
    assert(#calls==0,"warning must not send gameplay commands")
end)
check("captain warning is noninteractive and does not replace price selectors",function()
    local find,calls,made=fixture()
    local warning=assert(find("BossWaveWarning"))
    assert(warning.ClassName=="TextLabel")
    assert(warning.Position[1]==0.63 and warning.Size[1]==0.34)
    assert(warning.Text=="" and warning.Visible==false)
    local count=0
    for _,obj in ipairs(made) do if obj.ClassName=="TextButton" then count=count+1 end end
    assert(count==3 and find("pon") and find("guardon") and find("tankuru"))
    assert(#calls==0)
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
local function roster(count)
    local ids={"pon","guardon","tankuru","curebo","kururin","future_six","future_seven"}
    local selected={};for i=1,count do selected[i]=ids[i] end
    return selected
end
for _,count in ipairs({5,7}) do
    check(tostring(count).." units page through every slot, empty tail and both wrap directions",function()
        local ids=roster(count)
        local find,calls,made,status=fixture(ids)
        assert(#calls==0 and find("ToyPageNavigation").Visible==false)
        find("GuideSkip").Activated:Fire()
        local pages=math.ceil(count/3)
        for page=1,pages do
            assert(find("ToyPageCaption").Text==string.format("TOYS %d / %d",page,pages))
            for slot=1,3 do
                local id=ids[(page-1)*3+slot]
                local before=#calls
                if id then
                    local button=assert(find(id));assert(button.Visible)
                    status._children.SelectedToy.Value=string.upper(id);status._children.SelectedToy.Changed:Fire()
                    assert(button.BorderSizePixel==3)
                    button.Activated:Fire();assert(calls[#calls]==id and #calls==before+1)
                else
                    local empty=assert(find("EmptyToySlot"..slot));assert(empty.Visible==false)
                    empty.Activated:Fire();assert(#calls==before)
                end
            end
            local before=#calls;find("ToyPageNext").Activated:Fire();assert(#calls==before)
        end
        assert(find("ToyPageCaption").Text=="TOYS 1 / "..pages)
        local before=#calls;find("ToyPagePrevious").Activated:Fire();assert(#calls==before)
        assert(find("ToyPageCaption").Text=="TOYS "..pages.." / "..pages)
        find("ToyPageNext").Activated:Fire()
        for _,id in ipairs({"pon","guardon","tankuru"}) do find(id).Activated:Fire();assert(calls[#calls]==id) end
    end)
end
check("single page roster stays without navigation after guide",function()
    local find,calls=fixture(roster(3));find("GuideSkip").Activated:Fire()
    assert(find("ToyPageNavigation").Visible==false and #calls==0)
end)
for _,missing in ipairs({"leaderstats","ToyWarsBalance"}) do
    check("waiting state survives delayed "..missing.." before guide and pager",function()
        local find,calls,made,status,resume=fixture(roster(7),missing)
        assert(find("WorkshopQueueNotice") and #calls==0)
        assert(not find("QuickStart") and not find("ToyPageNavigation"))
        resume()
        assert(find("WorkshopQueueNotice").Visible==false and find("QuickStart").Visible==true)
        find("GuideNext").Activated:Fire();find("GuideNext").Activated:Fire();find("GuideNext").Activated:Fire()
        assert(find("ToyPageNavigation").Visible==true and #calls==0)
    end)
end
print(string.format("AUTO_CHARACTER_PAGES_SUMMARY %d passed / %d failed; HUD mock, not phone hardware",passed,failed))
if failed>0 then os.exit(1) end

