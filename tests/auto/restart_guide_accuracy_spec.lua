-- Canonical HUD wording and server loss-reset regression; native Lua mocks only.
local hud=os.getenv("TWF_HUD_FILE") or "src/ToyWarsHUD.client.lua"
local server=os.getenv("TWF_SERVER_FILE") or "src/ToyWarsServer.server.lua"
local Harness=dofile("tests/roblox_server_harness.lua")
local B=assert(loadfile("src/ToyWarsBalance.lua"))()
local passed,failed=0,0
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
local function signal()
    local s={listeners={}}
    function s:Connect(fn) self.listeners[#self.listeners+1]=fn end
    function s:Fire(...) for _,fn in ipairs(self.listeners) do fn(...) end end
    return s
end
local function fixture(file)
    local created,calls={},{}
    local function obj(class,value)
        local o={ClassName=class,Value=value,_children={},Changed=signal(),Activated=signal()}
        function o:WaitForChild(name) return assert(self._children[name],"missing "..name) end
        return o
    end
    local p,stats,status,gui=obj("Player"),obj("Folder"),obj("Folder"),obj("PlayerGui")
    p._children={leaderstats=stats,ToyWarsStatus=status,PlayerGui=gui}
    for k,v in pairs({Coins=50,Wave=1,Defeated=0}) do stats._children[k]=obj("IntValue",v) end
    for k,v in pairs({BaseHP=100,FactoryLevel=1,Allies=0,Enemies=0,RoundOutcome="",SelectedToy="PON"}) do
        status._children[k]=obj("Value",v)
    end
    local module=obj("ModuleScript")
    local storage=obj("ReplicatedStorage")
    storage._children={ToyWarsBalance=module,ToyWarsSelectUnit={
        FireServer=function(_,id) calls[#calls+1]=id end}}
    local services={Players={LocalPlayer=p},ReplicatedStorage=storage}
    local function tuple(...) return {...} end
    local env=setmetatable({
        game={GetService=function(_,name) return assert(services[name]) end},
        Instance={new=function(class) local o=obj(class);created[#created+1]=o;return o end},
        Color3={fromRGB=tuple},UDim={new=tuple},UDim2={new=tuple,fromScale=tuple},
        Enum={Font={GothamBold="GothamBold"}},
        require=function(value) assert(value==module);return B end,print=function() end,
    },{__index=_G})
    assert(loadfile(file,"t",env))()
    local found={}
    for _,o in ipairs(created) do if o.Name then found[o.Name]=o end end
    return found,calls
end
check("third guide page states automatic restart, PLAY closes without commands",function()
    local f,calls=fixture(hud)
    assert(f.QuickStart.Visible==true,"guide missing")
    f.GuideNext.Activated:Fire();f.GuideNext.Activated:Fire()
    local text=assert(f.GuideStepText).Text
    assert(text:find("Loss automatically restarts wave 1.",1,true),"wrong restart instruction")
    assert(not text:find("retry after a loss",1,true),"obsolete retry instruction")
    assert(f.GuideNextCaption.Text=="PLAY","PLAY missing")
    f.GuideNext.Activated:Fire()
    assert(f.QuickStart.Visible==false and #calls==0,"guide did not dismiss safely")
end)
check("whole canonical server resets wave 1 automatically after base loss",function()
    local h=Harness.new(server)
    local p=h:addPlayer(h:newPlayer())
    local stats=assert(p:FindFirstChild("leaderstats"))
    local coins=assert(stats:FindFirstChild("Coins"))
    local wave=assert(stats:FindFirstChild("Wave"))
    local hp=assert(h:status(p,"BaseHP"))
    local sawWaveTwo=false
    for _=1,220 do
        coins.Value=0
        h.runService.Heartbeat:Fire(0.3)
        if wave.Value==2 then sawWaveTwo=true end
        if sawWaveTwo and wave.Value==1 and hp.Value==100 then
            assert(h:status(p,"Enemies").Value==0,"restart left enemies")
            return
        end
    end
    error("no automatic wave-one restart")
end)
local pinned=".qa/server-before/src/ToyWarsHUD.client.lua"
local old=io.open(pinned,"rb")
if old then
    old:close()
    check("pinned old HUD lacks corrected restart instruction",function()
        local f=fixture(pinned)
        if f.GuideNext then f.GuideNext.Activated:Fire();f.GuideNext.Activated:Fire() end
        local text=f.GuideStepText and f.GuideStepText.Text or ""
        assert(not text:find("Loss automatically restarts wave 1.",1,true),"old source unexpectedly corrected")
    end)
end
print(string.format("AUTO_RESTART_GUIDE_SUMMARY %d passed / %d failed; canonical Lua mocks",passed,failed))
if failed>0 then os.exit(1) end
