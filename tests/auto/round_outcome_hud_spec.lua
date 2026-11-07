-- Execute the entire canonical HUD with deterministic UI signals.
-- Client rendering, replication timing and mobile screens are NOT tested.
local hud=os.getenv("TWF_HUD_FILE") or "src/ToyWarsHUD.client.lua"
local passed,failed=0,0
local function signal()
    local s={listeners={}}
    function s:Connect(fn) self.listeners[#self.listeners+1]=fn end
    function s:Fire(...) for _,fn in ipairs(self.listeners) do fn(...) end end
    return s
end
local function fixture(lateOutcome,duringSubscription)
    local balance=assert(loadfile("src/ToyWarsBalance.lua"))()
    local created,calls={},{}
    local function object(class,value)
        local o={ClassName=class,Value=value,_children={},Changed=signal(),Activated=signal(),ChildAdded=signal()}
        function o:FindFirstChild(name) return self._children[name] end
        function o:WaitForChild(name)
            return assert(self._children[name],"fixture missing "..name)
        end
        return o
    end
    local player=object("Player")
    local stats,status,gui=object("Folder"),object("Folder"),object("PlayerGui")
    player._children={leaderstats=stats,ToyWarsStatus=status,PlayerGui=gui}
    for name,value in pairs({Coins=0,Wave=1,Defeated=0}) do
        stats._children[name]=object("IntValue",value)
    end
    for name,value in pairs({BaseHP=100,FactoryLevel=1,Allies=0,Enemies=0,
                             SelectedToy="GUARDON"}) do
        status._children[name]=object("Value",value)
    end
    if not lateOutcome then status._children.RoundOutcome=object("StringValue","") end
    if duringSubscription then
        assert(lateOutcome,"subscription race requires initially absent result")
        local oldConnect=status.ChildAdded.Connect
        function status.ChildAdded:Connect(fn)
            -- Replication occurs after FindFirstChild, before this handler attaches.
            local child=object("StringValue","VICTORY")
            child.Name="RoundOutcome"
            status._children.RoundOutcome=child
            self:Fire(child) -- Nobody is listening yet: the notification is lost.
            return oldConnect(self,fn)
        end
    end
    local model=object("ModuleScript")
    local storage=object("ReplicatedStorage")
    storage._children={ToyWarsBalance=model,ToyWarsSelectUnit={FireServer=function(_,id) calls[#calls+1]=id end}}
    local services={Players={LocalPlayer=player},ReplicatedStorage=storage}
    local function tuple(...) return {...} end
    local env=setmetatable({
        game={GetService=function(_,name) return assert(services[name]) end},
        Instance={new=function(class) local o=object(class);created[#created+1]=o;return o end},
        Color3={fromRGB=tuple},UDim={new=tuple},UDim2={new=tuple},
        Enum={Font={GothamBold="GothamBold"}},
        require=function(v) assert(v==model);return balance end,
        print=function() end,
    },{__index=_G})
    assert(loadfile(hud,"t",env))()
    local tip,guide,buttons,banner
    buttons=0
    for _,o in ipairs(created) do
        if o.TextStrokeTransparency==0.4 then tip=o end
        if o.Name=="QuickStart" then guide=o end
        if o.Name=="RoundResultBanner" then banner=o end
        if o.ClassName=="TextButton" then buttons=buttons+1 end
    end
    assert(tip and guide and buttons==3,"existing HUD with three choices required")
    return tip,status._children.RoundOutcome,stats._children.Coins,
           status._children.Allies,guide,calls,function(value)
               local child=object("StringValue",value)
               child.Name="RoundOutcome"
               status._children.RoundOutcome=child
               status.ChildAdded:Fire(child)
               return child
           end,banner
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
local function has(t,s) return t.Text:find(s,1,true)~=nil end

check("neutral result retains waiting production and gold guidance",function()
    local tip,result=fixture()
    assert(result.Value=="")
    assert(has(tip,"WAIT GUARDON 28 COINS") and has(tip,"GOLD"),"neutral instructions")
end)
check("LOSS server value overrides unaffordable and full-capacity hints",function()
    local tip,result,coins,allies,guide,calls=fixture()
    allies.Value=20;allies.Changed:Fire()
    assert(has(tip,"FIELD FULL"),"ordinary capacity cue")
    result.Value="LOSS";result.Changed:Fire()
    assert(has(tip,"BASE LOST") and not has(tip,"FIELD FULL"),"authoritative defeat cue")
    coins.Value=0;coins.Changed:Fire()
    assert(has(tip,"BASE LOST"),"coin changes do not obscure defeat")
    assert(not guide.Visible and #calls==0,"outcome-only feedback dismisses onboarding")
end)
check("VICTORY is distinct from loss when wave loops back to one",function()
    local tip,result,coins,allies,guide,calls=fixture()
    result.Value="VICTORY";result.Changed:Fire()
    assert(has(tip,"WAVE 50") and not has(tip,"BASE LOST"),"explicit last-wave celebration")
    assert(#calls==0,"client never sends a result command")
end)
check("clearing result restores the original canonical money wait tip",function()
    local tip,result=fixture()
    result.Value="LOSS";result.Changed:Fire()
    result.Value="";result.Changed:Fire()
    assert(has(tip,"WAIT GUARDON 28 COINS") and has(tip,"GOLD"),"original hint resumed")
end)
check("unknown or forged replicated result is treated as neutral",function()
    local tip,result,coins,allies,guide,calls=fixture()
    result.Value="UNEXPECTED";result.Changed:Fire()
    assert(has(tip,"WAIT GUARDON") and not has(tip,"BASE LOST"),"unknown state ignored")
    assert(#calls==0,"no client action")
end)
check("late server result arrives without blocking original HUD",function()
    local tip,result,coins,allies,guide,calls,inject=fixture(true)
    assert(result==nil and has(tip,"WAIT GUARDON"),"original HUD must load while result is absent")
    local late=inject("VICTORY")
    assert(has(tip,"WAVE 50") and not has(tip,"BASE LOST"),"late result refreshes HUD")
    late.Value=""
    late.Changed:Fire()
    assert(has(tip,"WAIT GUARDON") and #calls==0,"restored guidance without client gameplay event")
end)

check("outcome arriving inside ChildAdded subscription is reconciled",function()
    local tip,result,coins,allies,guide,calls=fixture(true,true)
    assert(result and result.Value=="VICTORY","race injection created authoritative result")
    assert(has(tip,"WAVE 50") and not guide.Visible,
           "result already present after subscription must be displayed")
    result.Value="";result.Changed:Fire()
    assert(has(tip,"WAIT GUARDON") and #calls==0,"cleared result restores original guidance")
end)

for _,recognized in ipairs({"LOSS","VICTORY"}) do
    check("recognized "..recognized.." exposes result even when onboarding is visible",function()
        local tip,result,coins,allies,guide,calls=fixture()
        assert(guide.Visible,"new player sees first-play guide")
        result.Value=recognized
        result.Changed:Fire()
        assert(guide.Visible==false,"outcome must dismiss onboarding overlay")
        assert(recognized=="LOSS" and has(tip,"BASE LOST") or
               recognized=="VICTORY" and has(tip,"WAVE 50"),"server-owned result still displayed")
        result.Value=""
        result.Changed:Fire()
        assert(guide.Visible==false,"result clear must not reopen first-play guide")
        assert(#calls==0,"client only displays outcome, no gameplay command")
    end)
end

check("result banner shows each server result and restores unobstructed guidance",function()
    local tip,result,coins,allies,guide,calls,inject,banner=fixture()
    assert(banner and banner.Visible==false and tip.Visible==true,
           "a neutral game session should keep the result banner hidden")
    result.Value="LOSS";result.Changed:Fire()
    assert(banner.Visible==true and banner.Text:find("BASE LOST",1,true)
           and banner.Text:find("RESTARTING WAVE 1",1,true),
           "loss must appear in the prominent result banner")
    assert(banner.Text:find("\n",1,true), "loss must render an actual second line")
    assert(tip.Visible==false and guide.Visible==false,
           "normal hint and onboarding cannot compete with an outcome")
    result.Value="VICTORY";result.Changed:Fire()
    assert(banner.Visible==true and banner.Text:find("WAVE 50 CLEARED",1,true)
           and banner.Text:find("NEW FACTORY RUN",1,true),
           "victory must be distinguishable from loss")
    assert(banner.Text:find("\n",1,true), "victory must render an actual second line")
    result.Value="";result.Changed:Fire()
    assert(banner.Visible==false and tip.Visible==true
           and tip.Text:find("WAIT GUARDON",1,true),
           "banner must leave gameplay readable after the grace period")
    assert(#calls==0,"UI-only outcome presentation must not send gameplay commands")
end)

print(string.format("AUTO_ROUND_OUTCOME_HUD_SUMMARY %d passed / %d failed; canonical HUD native Lua mock",passed,failed))
if failed>0 then os.exit(1) end
