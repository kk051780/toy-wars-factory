-- Execute the full canonical HUD through the queue -> allocated -> ready transition.
-- Native Lua UI mocks only: not Roblox replication, phone or visual evidence.
local hud=os.getenv("TWF_HUD_FILE") or "src/ToyWarsHUD.client.lua"
local passed,failed=0,0
local function signal()
    local s={listeners={}}
    function s:Connect(fn) self.listeners[#self.listeners+1]=fn end
    function s:Fire(...) for _,fn in ipairs(self.listeners) do fn(...) end end
    return s
end
local function fixture(file,queued,withoutFix)
    local created,commands={},{}
    local player,stats,status,gui,storage
    local sawQueue,sawPreparing=false,false
    local function find(name)
        for _,item in ipairs(created) do if item.Name==name then return item end end
    end
    local function object(class,value)
        local o={ClassName=class,Value=value,_children={},Changed=signal(),Activated=signal()}
        function o:WaitForChild(name)
            if self==player and name=="leaderstats" and queued then
                local notice=find("WorkshopQueueNotice")
                assert(notice and notice.Visible~=false and
                    notice.Text=="Waiting for a free workshop slot...","queue text missing before allocation")
                assert(not find("QuickStart"),"guide appeared before allocation")
                sawQueue=true
                self._children.leaderstats=stats
            elseif self==player and name=="ToyWarsStatus" then
                local notice=find("WorkshopQueueNotice")
                assert(notice and notice.Visible~=false,"notice vanished before status replication")
                assert(notice.Text=="Preparing your workshop...","preparing text missing after allocation")
                assert(not find("QuickStart"),"guide appeared before status replication")
                sawPreparing=true
            end
            return assert(self._children[name],"missing fixture child "..name)
        end
        return o
    end
    player,stats,status,gui,storage=object("Player"),object("Folder"),object("Folder"),
        object("PlayerGui"),object("ReplicatedStorage")
    player._children={PlayerGui=gui,ToyWarsStatus=status}
    if not queued then player._children.leaderstats=stats end
    for name,value in pairs({Coins=50,Wave=1,Defeated=0}) do
        stats._children[name]=object("IntValue",value)
    end
    for name,value in pairs({BaseHP=100,FactoryLevel=1,Allies=0,Enemies=0,SelectedToy="PON"}) do
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
        require=function(value) assert(value==module);return balance end,
        print=function() end,
    },{__index=_G})
    if withoutFix then
        -- Negative control removes only the fix line from the complete HUD source.
        local f=assert(io.open(file,"rb"))
        local source=f:read("*a");f:close()
        local marker='waiting.Text="Preparing your workshop..."'
        local first,last=assert(source:find(marker,1,true),"missing fix marker")
        source=source:sub(1,first-1)..source:sub(last+1)
        assert(load(source,"@whole-HUD-before-fix","t",env))()
    else
        assert(loadfile(file,"t",env))()
    end
    assert(sawPreparing,"status replication boundary not reached")
    assert(not queued or sawQueue,"queue transition not observed")
    assert(find("WorkshopQueueNotice").Visible==false,"notice not cleared at HUD readiness")
    assert(find("QuickStart").Visible==true,"guide missing after readiness")
    assert(#commands==0,"HUD bootstrap sent gameplay command")
    return find,commands
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
check("queued player sees waiting then preparing without premature guide",function()
    local find,commands=fixture(hud,true,false)
    find("GuideNext").Activated:Fire()
    find("GuideSkip").Activated:Fire()
    assert(#commands==0,"guide navigation sent gameplay command")
    assert(find("QuickStart").Visible==false,"SKIP did not dismiss guide")
    find("pon").Activated:Fire()
    assert(commands[1]=="pon","toy selection stopped working")
end)
check("already allocated player sees preparing during status wait",function()
    local find,commands=fixture(hud,false,false)
    assert(find("guardon").ClassName=="TextButton","selector missing")
    assert(#commands==0,"bootstrap sent gameplay command")
end)
check("whole-HUD negative control reproduces stale queue message",function()
    local ok,err=pcall(function() fixture(hud,true,true) end)
    assert(not ok and tostring(err):find("preparing text missing after allocation",1,true),
        "removing the transition must reproduce the misleading queue message")
end)
print(string.format("AUTO_QUEUE_ALLOCATION_SUMMARY %d passed / %d failed; canonical whole-HUD Lua mock",passed,failed))
if failed>0 then os.exit(1) end
