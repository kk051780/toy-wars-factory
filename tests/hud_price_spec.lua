-- Execute the entire canonical HUD with small UI/value substitutes in Lua 5.4.
-- No rendering, input device, replication, or Roblox engine is exercised.
local hud=os.getenv("TWF_HUD_FILE") or "src/ToyWarsHUD.client.lua"
local passed,failed=0,0
local function eq(actual,expected,message)
    assert(actual==expected,(message or "value")..": expected "..tostring(expected)..", got "..tostring(actual))
end
local function signal()
    local s={listeners={}}
    function s:Connect(fn) self.listeners[#self.listeners+1]=fn end
    function s:Fire(...) for _,fn in ipairs(self.listeners) do fn(...) end end
    return s
end
local function fixture(costs)
    -- A fresh real balance module per fixture; only this in-memory copy is varied.
    local balance=assert(loadfile("src/ToyWarsBalance.lua"))()
    for id,cost in pairs(costs) do balance.UNITS[id].cost=cost end
    local created,calls={},{}
    local function object(class,value)
        local o={ClassName=class,Value=value,_children={},Changed=signal(),Activated=signal()}
        function o:WaitForChild(name) return assert(self._children[name],"fixture missing "..name) end
        return o
    end
    local player=object("Player")
    local stats,status,gui=object("Folder"),object("Folder"),object("PlayerGui")
    player._children={leaderstats=stats,ToyWarsStatus=status,PlayerGui=gui}
    for key,value in pairs({Coins=100,Wave=1,Defeated=0}) do stats._children[key]=object("IntValue",value) end
    for key,value in pairs({BaseHP=100,FactoryLevel=1,Allies=0,Enemies=0,SelectedToy="PON"}) do
        status._children[key]=object("Value",value)
    end
    local module={}
    local remote={FireServer=function(_,...) calls[#calls+1]={...} end}
    local storage=object("ReplicatedStorage")
    storage._children={ToyWarsBalance=module,ToyWarsSelectUnit=remote}
    local services={Players={LocalPlayer=player},ReplicatedStorage=storage}
    local function tuple(...) return {...} end
    local env=setmetatable({
        game={GetService=function(_,name) return assert(services[name],"unsupported service") end},
        Instance={new=function(class) local o=object(class);created[#created+1]=o;return o end},
        Color3={fromRGB=tuple},UDim={new=tuple},UDim2={new=tuple},
        Enum={Font={GothamBold="GothamBold"}},
        require=function(value) eq(value,module,"shared balance module");return balance end,
        print=function() end,
    },{__index=_G})
    assert(loadfile(hud,"t",env))()
    local buttons={}
    for _,o in ipairs(created) do if o.ClassName=="TextButton" then buttons[#buttons+1]=o end end
    return balance,buttons,calls
end
local cases={
    {"canonical prices",{}},
    {"changed PON price",{pon=17}},
    {"changed GUARDON price",{guardon=35}},
    {"changed TANKURU price",{tankuru=61}},
    {"zero prices",{pon=0,guardon=0,tankuru=0}},
    {"maximum wallet prices",{pon=999999,guardon=999999,tankuru=999999}},
}
for _,case in ipairs(cases) do
    local ok,err=pcall(function()
        local balance,buttons,calls=fixture(case[2])
        local ids={"pon","guardon","tankuru"}
        eq(#buttons,#ids,"selectable toy count")
        for i,id in ipairs(ids) do
            local button=buttons[i]
            eq(button.Name,id,"button identity")
            local label,price=button.Text:match("^([A-Z]+) | (%d+)$")
            eq(label,balance.UNITS[id].name,"label identity")
            local advertised=assert(tonumber(price),"missing displayed price")
            local remaining,reason=balance.buy(id,advertised,0)
            eq(reason,"ok","buy at displayed price")
            eq(remaining,0,"displayed price equals real purchase deduction")
            if advertised>0 then
                remaining,reason=balance.buy(id,advertised-1,0)
                eq(remaining,nil,"cannot buy below displayed price")
                eq(reason,"not_enough_coins","purchase threshold")
            end
            button.Activated:Fire()
            eq(#calls[i],1,"selection payload has no client-supplied price")
            eq(calls[i][1],id,"selection payload identity")
        end
        eq(#calls,3,"one selection event per activation")
    end)
    if ok then passed=passed+1;print("PASS "..case[1])
    else failed=failed+1;print("FAIL "..case[1]..": "..tostring(err)) end
end
print(string.format("HUD_PRICE_SUMMARY %d passed / %d failed; Lua mocks, not Roblox UI",passed,failed))
if failed>0 then os.exit(1) end
