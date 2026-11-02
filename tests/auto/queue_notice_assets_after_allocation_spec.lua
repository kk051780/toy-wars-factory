-- Execute the full canonical HUD; allocation must update the notice before remote/balance waits.
-- Lua mocks exercise WaitForChild order, not actual replication timing or Roblox visuals.
local hud=os.getenv("TWF_HUD_FILE") or "src/ToyWarsHUD.client.lua"
local passed,failed=0,0
local function signal()
    local s={listeners={}}
    function s:Connect(fn) self.listeners[#self.listeners+1]=fn end
    function s:Fire(...) for _,fn in ipairs(self.listeners) do fn(...) end end
    return s
end
local function fixture(file,queued,oldOrder)
    local created,commands={},{}
    local player,storage,stats,status,gui
    local sawQueue,sawRemote,sawBalance,sawRequire,sawStatus=false,false,false,false,false
    local function find(name)
        for _,item in ipairs(created) do if item.Name==name then return item end end
    end
    local function notice(expected)
        local n=find("WorkshopQueueNotice")
        assert(n and n.Visible~=false,"notice missing before HUD ready")
        assert(n.Text==expected,"preparing notice missing at asset wait: "..tostring(n.Text))
        assert(not find("QuickStart"),"guide appeared before HUD ready")
    end
    local function object(class,value)
        local o={ClassName=class,Value=value,_children={},Changed=signal(),Activated=signal()}
        function o:WaitForChild(name)
            if self==player and name=="leaderstats" and queued then
                notice("Waiting for a free workshop slot...")
                sawQueue=true
                self._children.leaderstats=stats
            elseif self==storage and name=="ToyWarsSelectUnit" then
                notice("Preparing your workshop...")
                sawRemote=true
            elseif self==storage and name=="ToyWarsBalance" then
                notice("Preparing your workshop...")
                sawBalance=true
            elseif self==player and name=="ToyWarsStatus" then
                notice("Preparing your workshop...")
                sawStatus=true
            end
            return assert(self._children[name],"missing child "..name)
        end
        return o
    end
    player,storage,stats,status,gui=object("Player"),object("ReplicatedStorage"),
        object("Folder"),object("Folder"),object("PlayerGui")
    player._children={PlayerGui=gui,ToyWarsStatus=status}
    if not queued then player._children.leaderstats=stats end
    for name,value in pairs({Coins=50,Wave=1,Defeated=0}) do
        stats._children[name]=object("IntValue",value)
    end
    for name,value in pairs({BaseHP=100,FactoryLevel=1,Allies=0,Enemies=0,RoundOutcome="",SelectedToy="PON"}) do
        status._children[name]=object("Value",value)
    end
    local module=object("ModuleScript")
    storage._children={ToyWarsSelectUnit={FireServer=function(_,id) commands[#commands+1]=id end},
        ToyWarsBalance=module}
    local balance=assert(loadfile("src/ToyWarsBalance.lua"))()
    local function tuple(...) return {...} end
    local env=setmetatable({
        game={GetService=function(_,name)
            if name=="Players" then return {LocalPlayer=player} end
            if name=="ReplicatedStorage" then return storage end
            error("unexpected service "..name)
        end},
        Instance={new=function(class)
            local o=object(class);created[#created+1]=o;return o
        end},
        Color3={fromRGB=tuple},UDim={new=tuple},UDim2={new=tuple},
        Enum={Font={GothamBold="GothamBold"}},
        require=function(value)
            assert(value==module,"unexpected balance module")
            notice("Preparing your workshop...")
            sawRequire=true
            return balance
        end,
        print=function() end,
    },{__index=_G})
    if oldOrder then
        local f=assert(io.open(file,"rb"))
        local source=f:read("*a");f:close()
        local newBlock='local stats=player:WaitForChild("leaderstats")\n-- Allocation is known; keep feedback accurate while status values replicate.\nwaiting.Text="Preparing your workshop..."\nlocal event=ReplicatedStorage:WaitForChild("ToyWarsSelectUnit")\nlocal B=require(ReplicatedStorage:WaitForChild("ToyWarsBalance"))'
        local oldBlock='local event=ReplicatedStorage:WaitForChild("ToyWarsSelectUnit")\nlocal B=require(ReplicatedStorage:WaitForChild("ToyWarsBalance"))\nlocal stats=player:WaitForChild("leaderstats")\n-- Allocation is known; keep feedback accurate while status values replicate.\nwaiting.Text="Preparing your workshop..."'
        local first,last=source:find(newBlock,1,true)
        assert(first and last,"canonical fix block missing")
        source=source:sub(1,first-1)..oldBlock..source:sub(last+1)
        assert(load(source,"@whole-HUD-old-order","t",env))()
    else
        assert(loadfile(file,"t",env))()
    end
    assert(sawRemote and sawBalance and sawRequire and sawStatus,
        "not all replicated-asset/status boundaries were tested")
    assert(not queued or sawQueue,"waiting boundary not tested")
    assert(find("WorkshopQueueNotice").Visible==false,"notice not hidden at readiness")
    assert(find("QuickStart").Visible==true,"guide not shown after readiness")
    local buttons=0
    for _,item in ipairs(created) do if item.ClassName=="TextButton" then buttons=buttons+1 end end
    assert(buttons==3,"three selectors must remain")
    assert(#commands==0,"HUD initialization sent a gameplay command")
    find("GuideNext").Activated:Fire()
    find("GuideSkip").Activated:Fire()
    assert(#commands==0 and find("QuickStart").Visible==false,
        "guide controls must dismiss without gameplay commands")
    find("pon").Activated:Fire()
    assert(commands[1]=="pon","toy selector must still work")
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
check("queued player switches to preparing before remote and balance waits",function()
    fixture(hud,true,false)
end)
check("already allocated player shows preparing while remote and balance load",function()
    fixture(hud,false,false)
end)
check("whole-HUD old order reproduces stale waiting at remote wait",function()
    local ok,err=pcall(function() fixture(hud,false,true) end)
    assert(not ok and tostring(err):find("preparing notice missing at asset wait",1,true),
        "old order must reproduce misleading waiting text")
end)
print(string.format("AUTO_QUEUE_ASSET_ORDER_SUMMARY %d passed / %d failed; canonical whole-HUD Lua mock",passed,failed))
if failed>0 then os.exit(1) end
