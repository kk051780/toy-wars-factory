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
local function fixture(file,queued)
    file=file or hud
    local created,calls={},{}
    local queueSeen=false
    local player,stats,status,gui
    local balance=assert(loadfile("src/ToyWarsBalance.lua"))()
    local function object(class,value)
        local o={ClassName=class,Value=value,_children={},Changed=signal(),Activated=signal()}
        function o:WaitForChild(name)
            if self==player and name=="leaderstats" and queued then
                local notice,earlyGuide
                for _,item in ipairs(created) do
                    if item.Name=="WorkshopQueueNotice" then notice=item end
                    if item.Name=="QuickStart" then earlyGuide=item end
                end
                assert(notice and notice.Parent and notice.Parent.Parent==gui and notice.Visible~=false,
                    "queue notice must be visible before leaderstats wait")
                assert(earlyGuide==nil,"guide must not cover waiting notice")
                queueSeen=true
                self._children.leaderstats=stats
                queued=false
            end
            return assert(self._children[name],"fixture missing "..name)
        end
        return o
    end
    player,stats,status,gui=object("Player"),object("Folder"),object("Folder"),object("PlayerGui")
    player._children={ToyWarsStatus=status,PlayerGui=gui}
    if not queued then player._children.leaderstats=stats end
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
    assert(loadfile(file,"t",env))()
    local found,selection={},0
    for _,o in ipairs(created) do
        if o.Name then found[o.Name]=o end
        if o.ClassName=="TextButton" then selection=selection+1 end
    end
    return found,selection,calls,stats,status,queueSeen
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
check("waiting player sees queue before guide; guide appears only after assignment",function()
    local f,count,calls,stats,status,queueSeen=fixture(nil,true)
    eq(queueSeen,true,"queue observed before assignment")
    eq(f.WorkshopQueueNotice.Visible,false,"notice clears after assignment")
    eq(f.QuickStart.Visible,true,"guide appears after assignment")
    eq(count,3,"selectors retained")
    eq(#calls,0,"no guide gameplay command")
end)
check("guide NEXT and PLAY never send gameplay commands",function()
    local f,count,calls=fixture()
    f.GuideNext.Activated:Fire()
    f.GuideNext.Activated:Fire()
    f.GuideNext.Activated:Fire()
    eq(#calls,0,"no command on guide navigation")
    eq(f.QuickStart.Visible,false,"PLAY dismisses")
    eq(count,3,"selectors unchanged")
end)

-- Deterministic UDim2 bounds from the canonical HUD; not actual mobile rendering.
local function bounds(node,width,height)
    local px,py,pw,ph=0,0,width,height
    if node.Parent and node.Parent.ClassName~="ScreenGui" then
        px,py,pw,ph=bounds(node.Parent,width,height)
    end
    local pos,size=node.Position,node.Size
    assert(type(pos)=="table" and type(size)=="table","GuiObject requires UDim2")
    return px+pw*pos[1]+pos[2],py+ph*pos[3]+pos[4],pw*size[1]+size[2],ph*size[3]+size[4]
end
local function overlaps(a,b)
    return a[1]<b[1]+b[3] and b[1]<a[1]+a[3]
       and a[2]<b[2]+b[4] and b[2]<a[2]+a[4]
end
check("guide SKIP/NEXT do not overlap toy selectors on compact landscape screens",function()
    local f,count,calls=fixture()
    eq(count,3,"three selectors preserved")
    for _,v in ipairs({{640,320},{640,360},{844,390},{960,540}}) do
        local w,h=v[1],v[2]
        for _,action in ipairs({f.GuideSkip,f.GuideNext}) do
            local a={bounds(action,w,h)}
            assert(a[1]>=0 and a[2]>=0 and a[1]+a[3]<=w and a[2]+a[4]<=h,
                string.format("%s outside %dx%d",action.Name,w,h))
            for _,selector in ipairs({f.pon,f.guardon,f.tankuru}) do
                assert(not overlaps(a,{bounds(selector,w,h)}),
                    string.format("%s overlaps %s at %dx%d",action.Name,selector.Name,w,h))
            end
        end
    end
    eq(#calls,0,"geometry test sends no gameplay command")
end)
check("rejected PR67 a57961e4 old guide position reproduces mobile overlap",function()
    local f=fixture()
    -- Old rejected head placed the guide at 0.34 screen height; other dimensions unchanged.
    local saved=f.QuickStart.Position
    f.QuickStart.Position={0.11,0,0.34,0}
    for _,v in ipairs({{640,320},{640,360}}) do
        local w,h=v[1],v[2]
        local collision=false
        for _,action in ipairs({f.GuideSkip,f.GuideNext}) do
            for _,selector in ipairs({f.pon,f.guardon,f.tankuru}) do
                if overlaps({bounds(action,w,h)},{bounds(selector,w,h)}) then collision=true end
            end
        end
        assert(collision,string.format("old guide must collide at %dx%d",w,h))
    end
    f.QuickStart.Position=saved
end)
local old=".qa/server-before/src/ToyWarsHUD.client.lua"
local fh=io.open(old,"rb")
if fh then
    fh:close()
    check("pinned pre-guide HUD negative control",function()
        local f=fixture(old,false)
        assert(f.QuickStart==nil and f.GuideNext==nil,"old HUD unexpectedly has onboarding")
    end)
end
print(string.format("AUTO_HUD_QUICKSTART_SUMMARY %d passed / %d failed; canonical HUD Lua mock, not Roblox UI",passed,failed))
if failed>0 then os.exit(1) end
