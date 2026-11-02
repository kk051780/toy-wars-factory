-- Execute the canonical HUD while replicated assets and workshop allocation are delayed.
-- The old source blocked on ReplicatedStorage before it drew any queue notice.
-- Lua UI mocks only: no Roblox replication, device or touch runtime is claimed.
local hud=os.getenv("TWF_HUD_FILE") or "src/ToyWarsHUD.client.lua"
local passed,failed=0,0
local function signal()
    local s={listeners={}}
    function s:Connect(fn) self.listeners[#self.listeners+1]=fn end
    function s:Fire(...) for _,fn in ipairs(self.listeners) do fn(...) end end
    return s
end
local function fixture(file)
    local created,calls={},{}
    local player,storage,stats,status,playerGui
    local checks=0
    local function find(name)
        for _,item in ipairs(created) do if item.Name==name then return item end end
    end
    local function queueVisible()
        local notice=find("WorkshopQueueNotice")
        assert(notice and notice.Parent and notice.Parent.Parent==playerGui
            and notice.Visible~=false,"queue notice absent before replicated asset wait")
        assert(find("QuickStart")==nil,"first-play guide appeared before workshop assignment")
        checks=checks+1
    end
    local function object(class,value)
        local o={ClassName=class,Value=value,_children={},Changed=signal(),Activated=signal()}
        function o:WaitForChild(name)
            if self==storage and (name=="ToyWarsSelectUnit" or name=="ToyWarsBalance") then
                queueVisible() -- a real WaitForChild could yield at either boundary
            end
            if self==player and name=="leaderstats" then
                queueVisible()
                self._children.leaderstats=stats -- a workshop becomes available
            end
            return assert(self._children[name],"missing mock child "..name)
        end
        return o
    end
    player,storage,stats,status,playerGui=object("Player"),object("ReplicatedStorage"),
        object("Folder"),object("Folder"),object("PlayerGui")
    player._children={PlayerGui=playerGui,ToyWarsStatus=status}
    for name,value in pairs({Coins=50,Wave=1,Defeated=0}) do
        stats._children[name]=object("IntValue",value)
    end
    for name,value in pairs({BaseHP=100,FactoryLevel=1,Allies=0,Enemies=0,RoundOutcome="",SelectedToy="PON"}) do
        status._children[name]=object("Value",value)
    end
    local module=object("ModuleScript")
    local remote={FireServer=function(_,id) calls[#calls+1]=id end}
    storage._children={ToyWarsBalance=module,ToyWarsSelectUnit=remote}
    local balance=assert(loadfile("src/ToyWarsBalance.lua"))()
    local function tuple(...) return {...} end
    local env=setmetatable({
        game={GetService=function(_,name)
            if name=="Players" then return {LocalPlayer=player} end
            if name=="ReplicatedStorage" then return storage end
            error("unexpected service "..name)
        end},
        Instance={new=function(class)
            local item=object(class)
            created[#created+1]=item
            return item
        end},
        Color3={fromRGB=tuple},UDim={new=tuple},UDim2={new=tuple,fromScale=tuple},
        Enum={Font={GothamBold="GothamBold"}},
        require=function(value)
            assert(value==module,"unexpected module")
            queueVisible() -- loading balance may also yield
            return balance
        end,
        print=function() end,
    },{__index=_G})
    assert(loadfile(file,"t",env))()
    return find,calls,checks
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
check("queue is visible before remote, balance, require and workshop waits",function()
    local find,calls,checks=fixture(hud)
    assert(checks==4,"expected four independently guarded wait boundaries")
    assert(find("WorkshopQueueNotice").Visible==false,"notice not cleared after assignment")
    assert(find("QuickStart").Visible==true,"guide not shown after assignment")
    assert(#calls==0,"HUD bootstrap sent a gameplay command")
end)
check("three selectors and guide controls survive the earlier notice",function()
    local find,calls=fixture(hud)
    for _,id in ipairs({"pon","guardon","tankuru"}) do
        assert(find(id) and find(id).ClassName=="TextButton","missing selector "..id)
        assert(find(id).Text:find(tostring(assert(loadfile("src/ToyWarsBalance.lua"))().UNITS[id].cost),1,true),
            "price missing for "..id)
    end
    find("GuideNext").Activated:Fire()
    find("GuideSkip").Activated:Fire()
    assert(#calls==0,"guide must not send gameplay commands")
    assert(find("QuickStart").Visible==false,"SKIP did not close guide")
    find("pon").Activated:Fire()
    assert(calls[1]=="pon","real selector stopped sending selection")
end)
local old=".qa/server-before/src/ToyWarsHUD.client.lua"
local fh=io.open(old,"rb")
if fh then
    fh:close()
    check("pinned pre-queue HUD cannot display notice at replication wait",function()
        local ok,err=pcall(function() fixture(old) end)
        assert(not ok and tostring(err):find("queue notice absent before replicated asset wait",1,true),
            "old HUD should fail before drawing the queue notice")
    end)
end
print(string.format("AUTO_QUEUE_REPLICATION_SUMMARY %d passed / %d failed; canonical HUD Lua mock",passed,failed))
if failed>0 then os.exit(1) end
