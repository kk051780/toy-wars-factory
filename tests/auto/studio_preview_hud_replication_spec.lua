-- Entire canonical HUD Lua mock: replicating ProgressMode after Folder is safe.
-- Not a Roblox rendering or network/engine test.
local path="src/ToyWarsHUD.client.lua"
local passed,failed=0,0
local function signal()
    local s={listeners={},active=0}
    function s:Connect(fn)
        local connection={connected=true}
        self.active=self.active+1
        function connection:Disconnect()
            if self.connected then s.active=s.active-1;self.connected=false end
        end
        self.listeners[#self.listeners+1]=function(...)
            if connection.connected then fn(...) end
        end
        return connection
    end
    function s:Fire(...) for _,fn in ipairs(self.listeners) do fn(...) end end
    return s
end
local function instance(class,value)
    local o={ClassName=class,Value=value,_children={},_extraChildren={},
             Changed=signal(),ChildAdded=signal(),ChildRemoved=signal(),Activated=signal()}
    function o:WaitForChild(name) return assert(self._children[name],"missing "..name) end
    function o:FindFirstChild(name) return self._children[name] end
    o._properties={}
    function o:GetPropertyChangedSignal(name)
        self._properties[name]=self._properties[name] or signal()
        return self._properties[name]
    end
    function o:GetChildren()
        local result={}
        for _,v in pairs(self._children) do result[#result+1]=v end
        for _,v in ipairs(self._extraChildren) do result[#result+1]=v end
        return result
    end
    return o
end
local function tuple(...) return {...} end
local function setup(initialMode)
    local balance=assert(loadfile("src/ToyWarsBalance.lua"))()
    local created={}
    local player,stats,status,gui=instance("Player"),instance("Folder"),
       instance("Folder"),instance("PlayerGui")
    player._children={leaderstats=stats,ToyWarsStatus=status,PlayerGui=gui}
    for name,value in pairs({Coins=50,Wave=1,Defeated=0}) do
        stats._children[name]=instance("IntValue",value)
    end
    for name,value in pairs({BaseHP=100,FactoryLevel=1,Allies=0,Enemies=0,SelectedToy="PON"}) do
        status._children[name]=instance("Value",value)
    end
    if initialMode then
        local m=instance("StringValue",initialMode)
        m.Name="ProgressMode"
        m.Parent=status
        status._children.ProgressMode=m
    end
    local mod=instance("ModuleScript")
    local remote=instance("RemoteEvent")
    remote.FireServer=function() end
    local rep=instance("ReplicatedStorage")
    rep._children={ToyWarsBalance=mod,ToyWarsSelectUnit=remote}
    local services={Players={LocalPlayer=player},ReplicatedStorage=rep}
    local env=setmetatable({
        game={GetService=function(_,name) return assert(services[name]) end},
        Instance={new=function(class) local o=instance(class);created[#created+1]=o;return o end},
        Color3={fromRGB=tuple},UDim={new=tuple},UDim2={new=tuple},
        Enum={Font={GothamBold="GothamBold"}},
        require=function(value) assert(value==mod);return balance end,
        print=function() end
    },{__index=_G})
    assert(loadfile(path,"t",env))()
    local notice
    for _,o in ipairs(created) do
        if o.Name=="StudioPreviewNotice" then notice=o end
    end
    assert(notice and notice.ClassName=="TextLabel","missing warning banner")
    local function arrive(mode)
        local m=instance("StringValue",mode)
        m.Name="ProgressMode"
        m.Parent=status
        status._children.ProgressMode=m
        status.ChildAdded:Fire(m)
        return m
    end
    local function removeMode(mode)
        local removed=false
        if status._children.ProgressMode==mode then
            status._children.ProgressMode=nil
            removed=true
        end
        for i,v in ipairs(status._extraChildren) do
            if v==mode then
                table.remove(status._extraChildren,i)
                removed=true
                break
            end
        end
        assert(removed,"missing mode to remove")
        mode.Parent=nil
        status.ChildRemoved:Fire(mode)
    end
    local function duplicate(mode)
        local m=instance("StringValue",mode)
        m.Name="ProgressMode"
        m.Parent=status
        status._extraChildren[#status._extraChildren+1]=m
        status.ChildAdded:Fire(m)
        return m
    end
    return notice,arrive,status,removeMode,duplicate
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
check("missing mode initially shows pending save warning",function()
    local n=setup()
    assert(n.Visible and n.Text=="PROGRESS STATUS PENDING - SAVE UNVERIFIED")
end)
check("late STUDIO_PREVIEW_UNSAVED turns on explicit warning",function()
    local n,arrive=setup()
    arrive("STUDIO_PREVIEW_UNSAVED")
    assert(n.Visible and n.Text=="STUDIO PREVIEW - PROGRESS NOT SAVED")
end)
check("late SAVED hides pending warning",function()
    local n,arrive=setup()
    arrive("SAVED")
    assert(n.Visible==false)
end)
check("already replicated preview shows unsaved warning",function()
    local n=setup("STUDIO_PREVIEW_UNSAVED")
    assert(n.Visible and n.Text=="STUDIO PREVIEW - PROGRESS NOT SAVED")
end)
check("already replicated SAVED hides banner",function()
    local n=setup("SAVED")
    assert(n.Visible==false)
end)
check("unrecognized mode cannot falsely look saved",function()
    local n,arrive=setup()
    arrive("MALFORMED")
    assert(n.Visible and n.Text=="PROGRESS STATUS UNVERIFIED - DO NOT EXPECT SAVE")
end)
check("mode value change refreshes visible warning",function()
    local n,arrive=setup()
    local m=arrive("SAVED")
    assert(n.Visible==false)
    m.Value="STUDIO_PREVIEW_UNSAVED"
    m.Changed:Fire(m.Value)
    assert(n.Visible and n.Text=="STUDIO PREVIEW - PROGRESS NOT SAVED")
end)

check("removed SAVED immediately restores pending warning",function()
    local n,_,status,removeMode=setup("SAVED")
    assert(n.Visible==false)
    removeMode(status._children.ProgressMode)
    assert(n.Visible and n.Text=="PROGRESS STATUS PENDING - SAVE UNVERIFIED")
end)
check("removed SAVED followed by replacement UNSAVED stays warning",function()
    local n,arrive,status,removeMode=setup("SAVED")
    removeMode(status._children.ProgressMode)
    arrive("STUDIO_PREVIEW_UNSAVED")
    assert(n.Visible and n.Text=="STUDIO PREVIEW - PROGRESS NOT SAVED")
end)
check("stale Changed on removed SAVED never hides replacement UNSAVED",function()
    local n,arrive,status,removeMode=setup("SAVED")
    local old=status._children.ProgressMode
    removeMode(old)
    arrive("STUDIO_PREVIEW_UNSAVED")
    old.Value="SAVED"
    old.Changed:Fire(old.Value)
    assert(n.Visible and n.Text=="STUDIO PREVIEW - PROGRESS NOT SAVED")
end)
check("duplicate SAVED modes show unverified until one is removed",function()
    local n,_,_,removeMode,duplicate=setup("SAVED")
    local second=duplicate("SAVED")
    assert(n.Visible and n.Text=="PROGRESS STATUS UNVERIFIED - DO NOT EXPECT SAVE")
    removeMode(second)
    assert(n.Visible==false)
end)
check("duplicate UNSAVED with SAVED cannot silently hide save warning",function()
    local n,_,status,removeMode,duplicate=setup("SAVED")
    local extra=duplicate("STUDIO_PREVIEW_UNSAVED")
    assert(n.Visible and n.Text=="PROGRESS STATUS UNVERIFIED - DO NOT EXPECT SAVE")
    removeMode(status._children.ProgressMode)
    assert(n.Visible and n.Text=="STUDIO PREVIEW - PROGRESS NOT SAVED")
    removeMode(extra)
    assert(n.Visible and n.Text=="PROGRESS STATUS PENDING - SAVE UNVERIFIED")
end)

check("selected rename and restore without child events rescans",function()
    local n,_,status=setup("SAVED")
    local m=status._children.ProgressMode
    for i=1,20 do
        m.Name="FormerMode";m:GetPropertyChangedSignal("Name"):Fire()
        assert(n.Visible,"rename must show warning")
        m.Name="ProgressMode";m:GetPropertyChangedSignal("Name"):Fire()
        assert(not n.Visible,"restored unique SAVED")
    end
    assert(m.Changed.active==1,"only one active value subscription")
    assert(m:GetPropertyChangedSignal("Name").active==1,"only one name subscription")
    m.Changed:Fire("SAVED")
    assert(not n.Visible)
end)
check("renamed-in duplicate and rename-out restore unique mode",function()
    local n,_,status,_,duplicate=setup("SAVED")
    local other=duplicate("SAVED")
    other.Name="Other";other:GetPropertyChangedSignal("Name"):Fire()
    assert(not n.Visible)
    other.Name="ProgressMode";other:GetPropertyChangedSignal("Name"):Fire()
    assert(n.Visible and n.Text=="PROGRESS STATUS UNVERIFIED - DO NOT EXPECT SAVE")
end)
check("queued Changed before ChildRemoved cannot trust detached SAVED",function()
    local n,_,status=setup("SAVED")
    local old=status._children.ProgressMode
    status._children.ProgressMode=nil;old.Parent=nil
    old.Changed:Fire("SAVED")
    assert(n.Visible and n.Text=="PROGRESS STATUS PENDING - SAVE UNVERIFIED")
end)
check("queued Changed before rename signal cannot trust renamed SAVED",function()
    local n,_,status=setup("SAVED")
    local old=status._children.ProgressMode
    old.Name="Other";old.Changed:Fire("SAVED")
    assert(n.Visible)
end)
check("reparent before removal signal and replacement remains unsaved",function()
    local n,arrive,status=setup("SAVED")
    local old=status._children.ProgressMode
    status._children.ProgressMode=nil;old.Parent=instance("Folder")
    old:GetPropertyChangedSignal("Parent"):Fire()
    assert(n.Visible)
    arrive("STUDIO_PREVIEW_UNSAVED")
    old.Changed:Fire("SAVED");status.ChildRemoved:Fire(old)
    assert(n.Visible and n.Text=="STUDIO PREVIEW - PROGRESS NOT SAVED")
    assert(old.Changed.active==0)
    assert(old:GetPropertyChangedSignal("Name").active==0)
    assert(old:GetPropertyChangedSignal("Parent").active==0)
end)

print(string.format("STUDIO_PREVIEW_HUD_REPLICATION_SUMMARY %d passed / %d failed; Lua mocks not Roblox engine",passed,failed))
if failed>0 then os.exit(1) end
