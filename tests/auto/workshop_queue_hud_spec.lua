-- Run the canonical HUD, including its initial WaitForChild flow, with Lua mocks.
-- A fifth player waits for a free plot; no Roblox rendering or network is claimed.
local hud=os.getenv("TWF_HUD_FILE") or "src/ToyWarsHUD.client.lua"
local passed,failed=0,0
local function signal()
    local s={listeners={}}
    function s:Connect(fn) self.listeners[#self.listeners+1]=fn end
    function s:Fire(...) for _,fn in ipairs(self.listeners) do fn(...) end end
    return s
end
local function fixture(file,queued)
    local created,queueSeen={},false
    local player,stats,status,playerGui
    local function object(class,value)
        local o={ClassName=class,Value=value,_children={},Changed=signal(),Activated=signal()}
        function o:WaitForChild(name)
            if self==player and name=="leaderstats" and queued then
                local notice
                for _,item in ipairs(created) do
                    if item.Name=="WorkshopQueueNotice" then notice=item end
                end
                assert(notice and notice.Parent==playerGui and notice.Visible~=false,
                    "queue notice must be visible before leaderstats wait")
                queueSeen=true
                self._children.leaderstats=stats -- simulate a plot becoming available
                queued=false
            end
            return assert(self._children[name],"fixture missing "..name)
        end
        return o
    end
    player=object("Player")
    stats,status,playerGui=object("Folder"),object("Folder"),object("PlayerGui")
    player._children={PlayerGui=playerGui,ToyWarsStatus=status}
    if not queued then player._children.leaderstats=stats end
    for name,value in pairs({Coins=50,Wave=1,Defeated=0}) do
        stats._children[name]=object("IntValue",value)
    end
    for name,value in pairs({BaseHP=100,FactoryLevel=1,Allies=0,Enemies=0,SelectedToy="PON"}) do
        status._children[name]=object("Value",value)
    end
    local module=object("ModuleScript")
    local storage=object("ReplicatedStorage")
    storage._children={ToyWarsBalance=module,ToyWarsSelectUnit={FireServer=function() end}}
    local services={Players={LocalPlayer=player},ReplicatedStorage=storage}
    local function tuple(...) return {...} end
    local env=setmetatable({
        game={GetService=function(_,name) return assert(services[name]) end},
        Instance={new=function(class) local o=object(class);created[#created+1]=o;return o end},
        Color3={fromRGB=tuple},UDim={new=tuple},UDim2={new=tuple},
        Enum={Font={GothamBold="GothamBold"}},
        require=function(x) assert(x==module);return assert(loadfile("src/ToyWarsBalance.lua"))() end,
        print=function() end,
    },{__index=_G})
    assert(loadfile(file,"t",env))()
    local notice,buttons
    buttons=0
    for _,item in ipairs(created) do
        if item.Name=="WorkshopQueueNotice" then notice=item end
        if item.ClassName=="TextButton" then buttons=buttons+1 end
    end
    assert(notice and notice.Visible==false,"queue notice must disappear after assignment")
    assert(buttons==3,"all three toy selectors must load after assignment")
    return queueSeen
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
check("queued player sees waiting notice before workshop assignment",function()
    assert(fixture(hud,true),"fixture did not simulate the queue")
end)
check("assigned player reaches normal three-choice HUD",function()
    assert(fixture(hud,false)==false,"unexpected queue wait")
end)
local old=".qa/server-before/src/ToyWarsHUD.client.lua"
local fh=io.open(old,"rb")
if fh then
    fh:close()
    check("pinned old HUD has no visible waiting notice",function()
        local ok,err=pcall(function() fixture(old,true) end)
        assert(not ok and tostring(err):find("queue notice must be visible",1,true),
            "old HUD should block before creating the queue notice")
    end)
end
print(string.format("AUTO_WORKSHOP_QUEUE_HUD_SUMMARY %d passed / %d failed; canonical HUD Lua mock",passed,failed))
if failed>0 then os.exit(1) end
