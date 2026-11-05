-- Run the full canonical HUD and verify first-choice role hints against actual balance.
-- Lua mock only: no Roblox rendering, touch hardware or mobile readability proof.
local hud=os.getenv("TWF_HUD_FILE") or "src/ToyWarsHUD.client.lua"
local B=assert(loadfile("src/ToyWarsBalance.lua"))()
local passed,failed=0,0
local function signal()
    local s={listeners={}}
    function s:Connect(fn) self.listeners[#self.listeners+1]=fn end
    function s:Fire(...) for _,fn in ipairs(self.listeners) do fn(...) end end
    return s
end
local function fixture(file)
    local created,calls={},{}
    local function object(class,value)
        local o={ClassName=class,Value=value,_children={},Changed=signal(),Activated=signal()}
        function o:WaitForChild(name)
            return assert(self._children[name],"missing "..name)
        end
        return o
    end
    local player,stats,status,gui=object("Player"),object("Folder"),object("Folder"),object("PlayerGui")
    player._children={leaderstats=stats,ToyWarsStatus=status,PlayerGui=gui}
    for id,value in pairs({Coins=50,Wave=1,Defeated=0}) do
        stats._children[id]=object("IntValue",value)
    end
    for id,value in pairs({BaseHP=100,FactoryLevel=1,Allies=0,Enemies=0,SelectedToy="PON"}) do
        status._children[id]=object("Value",value)
    end
    local module=object("ModuleScript")
    local remote={FireServer=function(_,id) calls[#calls+1]=id end}
    local storage=object("ReplicatedStorage")
    storage._children={ToyWarsBalance=module,ToyWarsSelectUnit=remote}
    local services={Players={LocalPlayer=player},ReplicatedStorage=storage}
    local function tuple(...) return {...} end
    local env=setmetatable({
        game={GetService=function(_,name) return assert(services[name]) end},
        Instance={new=function(class) local o=object(class);created[#created+1]=o;return o end},
        Color3={fromRGB=tuple},UDim={new=tuple},UDim2={new=tuple,fromScale=tuple},
        Enum={Font={GothamBold="GothamBold"}},
        require=function(value) assert(value==module);return B end,
        print=function() end,
    },{__index=_G})
    assert(loadfile(file,"t",env))()
    local found,count={},0
    for _,o in ipairs(created) do
        if o.Name then found[o.Name]=o end
        if o.ClassName=="TextButton" then count=count+1 end
    end
    return found,count,calls
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
check("role hints describe the actual three unit strengths",function()
    assert(B.UNITS.pon.speed>B.UNITS.guardon.speed and
           B.UNITS.pon.speed>B.UNITS.tankuru.speed,"PON speed assumption changed")
    assert(B.UNITS.guardon.hp>B.UNITS.pon.hp and
           B.UNITS.guardon.hp>B.UNITS.tankuru.hp,"GUARDON durability assumption changed")
    assert(B.UNITS.tankuru.range>B.UNITS.pon.range and
           B.UNITS.tankuru.range>B.UNITS.guardon.range,"TANKURU range assumption changed")
    local f,count=fixture(hud)
    assert(count==3,"three selectors must remain available")
    local text=assert(f.GuideStepText,"first-play text missing").Text
    for _,hint in ipairs({"PON fast","GUARDON tough","TANKURU ranged"}) do
        assert(text:find(hint,1,true),"missing truthful role hint: "..hint)
    end
    assert(f.WorkshopQueueNotice.Visible==false,"queue notice remains after assignment")
end)
check("guide navigation remains independent of toy selection",function()
    local f,count,calls=fixture(hud)
    f.GuideNext.Activated:Fire()
    f.GuideNext.Activated:Fire()
    f.GuideNext.Activated:Fire()
    assert(f.QuickStart.Visible==false,"PLAY did not dismiss")
    assert(#calls==0,"guide sent gameplay commands")
    assert(count==3,"toy selector count changed")
    f.pon.Activated:Fire()
    assert(calls[1]=="pon","real selector command broken")
end)
local pinned=".qa/server-before/src/ToyWarsHUD.client.lua"
local old=io.open(pinned,"rb")
if old then
    old:close()
    check("pre-guide baseline does not provide role onboarding",function()
        local f=fixture(pinned)
        assert(f.GuideStepText==nil,"old baseline unexpectedly has guide hints")
    end)
end
print(string.format("AUTO_ROLE_HINTS_SUMMARY %d passed / %d failed; canonical HUD Lua mock",passed,failed))
if failed>0 then os.exit(1) end
