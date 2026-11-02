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
local function fixture()
    local balance=assert(loadfile("src/ToyWarsBalance.lua"))()
    local created,calls={},{}
    local function object(class,value)
        local o={ClassName=class,Value=value,_children={},Changed=signal(),Activated=signal()}
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
                             SelectedToy="GUARDON",RoundOutcome=""}) do
        status._children[name]=object("Value",value)
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
    local tip,guide,buttons
    buttons=0
    for _,o in ipairs(created) do
        if o.TextStrokeTransparency==0.4 then tip=o end
        if o.Name=="QuickStart" then guide=o end
        if o.ClassName=="TextButton" then buttons=buttons+1 end
    end
    assert(tip and guide and buttons==3,"existing HUD with three choices required")
    return tip,status._children.RoundOutcome,stats._children.Coins,
           status._children.Allies,guide,calls
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
    assert(guide.Visible and #calls==0,"display-only feedback")
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
print(string.format("AUTO_ROUND_OUTCOME_HUD_SUMMARY %d passed / %d failed; canonical HUD native Lua mock",passed,failed))
if failed>0 then os.exit(1) end
