-- Execute the canonical whole server; offline Lua 5.4, not Roblox rendering.
local H=dofile("tests/roblox_server_harness.lua")
local server=os.getenv("TWF_SERVER_FILE") or "src/ToyWarsServer.server.lua"
local passed,failed=0,0
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
local function up(fn,name)
    for i=1,60 do local k,v=debug.getupvalue(fn,i);if not k then break end;if k==name then return v end end
    error("missing canonical upvalue "..name)
end
local function fixture(file)
    local h=H.new(file or server)
    local p=h:addPlayer(h:newPlayer())
    local heartbeat=h.runService.Heartbeat.listeners[1].fn
    local sessions=up(heartbeat,"sessions")
    local simulate=up(heartbeat,"simulate")
    local add=up(simulate,"addEntity")
    local s=sessions[p];s.productionTimer=100;s.waveBreak=100
    local function entity(id,side,health)
        local e=assert(add(s,id,side or "ally"));e.x=s.x;e.z=0;e.cooldown=100
        if health then e.health=health end
        return e
    end
    local target=entity("guardon","ally",50)
    local healer=entity("curebo")
    local enemy=entity("junk","enemy");enemy.z=1
    return h,p,s,target,healer,enemy,entity,sessions
end
local function beat(h,n) for _=1,n or 1 do h.runService.Heartbeat:Fire(0.12) end end
check("remote selection and production charge the actual CUREBO price",function()
    local h=H.new(server);local p=h:addPlayer(h:newPlayer())
    h.remote.OnServerEvent:Fire(p,"curebo")
    assert(h:status(p,"SelectedToy").Value=="CUREBO")
    for _=1,4 do h.runService.Heartbeat:Fire(0.3) end
    assert(p:FindFirstChild("leaderstats"):FindFirstChild("Coins").Value==25)
    assert(h:status(p,"Allies").Value==1)
end)
check("CUREBO is not free when the wallet is insufficient",function()
    local h=H.new(server);local p=h:addPlayer(h:newPlayer())
    p:FindFirstChild("leaderstats"):FindFirstChild("Coins").Value=0
    h.remote.OnServerEvent:Fire(p,"curebo")
    for _=1,4 do h.runService.Heartbeat:Fire(0.3) end
    assert(h:status(p,"Allies").Value==0)
end)
check("repair heals one ally and refreshes its HP bar immediately",function()
    local h,p,s,target=fixture();beat(h)
    assert(target.health==58)
    assert(math.abs(target.model:FindFirstChild("HealthBar").Size.X-3.2*58/108)<1e-8)
    assert(s.kills.Value==0 and s.baseHP.Value==100 and s.coins.Value==50)
end)
check("repair caps at max HP",function()
    local h,p,s,target=fixture();target.health=104;beat(h);assert(target.health==108)
end)
check("repair prefers the lowest health ratio",function()
    local h,p,s,target,healer,enemy,add=fixture();target.health=70
    local pon=add("pon","ally",10);beat(h)
    assert(pon.health==18 and target.health==70)
end)
check("multiple repair toys share the target cooldown",function()
    local h,p,s,target,healer,enemy,add=fixture();add("curebo")
    beat(h);assert(target.health==58)
    beat(h,20);assert(target.health==58)
    beat(h,7);assert(target.health==66)
end)
check("repair cannot heal itself or an enemy",function()
    local h,p,s,target,healer,enemy=fixture();target.health=target.maxHealth
    healer.health=20;enemy.health=10;beat(h)
    assert(healer.health==20 and enemy.health==10)
end)
check("repair cannot resurrect a defeated toy",function()
    local h,p,s,target=fixture();target.health=0;target.alive=false;beat(h)
    assert(target.health==0 and target.alive==false)
end)
check("repair does not reach an out-of-range ally",function()
    local h,p,s,target=fixture();target.z=20;beat(h);assert(target.health==50)
end)
check("another workshop cannot receive the repair even at the same coordinates",function()
    local h,p,s,target,healer,enemy,add,sessions=fixture();target.health=target.maxHealth
    local other=h:addPlayer(h:newPlayer());local t=sessions[other]
    t.productionTimer=100;t.waveBreak=100
    local heartbeat=h.runService.Heartbeat.listeners[1].fn
    local foreign=up(up(heartbeat,"simulate"),"addEntity")(t,"guardon","ally")
    foreign.health=40;foreign.x=healer.x;foreign.z=healer.z;foreign.cooldown=100
    beat(h);assert(foreign.health==40)
end)
check("primitive model keeps its heart, eyes and winder within budget",function()
    local h,p,s,target,healer=fixture();local n=0
    for _,part in ipairs(healer.model:GetChildren()) do
        if part:IsA("BasePart") then n=n+1;assert(part.Anchored and part.CanCollide==false) end
    end
    assert(n==17 and n<=18)
    for _,name in ipairs({"HeartLobe","HeartMiddle","HeartTip","RepairEye","WinderBar","ToolBag"}) do
        assert(healer.model:FindFirstChild(name),"missing low-detail signature "..name)
    end
end)
check("CUREBO stays in repair reach instead of rushing distant JUNK",function()
    local h,p,s,target,healer,enemy=fixture()
    enemy.z=28
    local initial=healer.z
    beat(h)
    assert(target.health==58,"actual support repair still fires")
    assert(healer.z==initial,"healer should hold position beside its injured ally")
end)
check("CUREBO pursues injured ally instead of enemy when out of repair reach",function()
    local h,p,s,target,healer,enemy=fixture()
    target.z=-18
    enemy.z=28
    beat(h)
    assert(target.health==50,"no repair outside the real range")
    assert(healer.z < -0.4,"healer must move toward injured ally, not distant enemy")
end)
check("CUREBO without a patient retains normal enemy pursuit",function()
    local h,p,s,target,healer,enemy=fixture()
    target.health=target.maxHealth
    enemy.z=28
    beat(h)
    assert(healer.z > 0.4,"no injured ally: preserve the existing combat route")
end)
check("negative control: the same healing assertion detects a disabled repair call",function()
    local f=assert(io.open(server,"rb"));local src=f:read("*a");f:close()
    local mutant,n=src:gsub('if data%.repairAmount and e%.side=="ally" then repairAlly%(state,e,dt%) end','')
    assert(n==1,"mutation must affect exactly one real call")
    local path=os.tmpname();local out=assert(io.open(path,"wb"));out:write(mutant);out:close()
    local ok,err=pcall(function()
        local h,p,s,target=fixture(path);beat(h)
        assert(target.health==50,"disabled repair still changed HP")
        local positive=pcall(function() assert(target.health==58,"repair missing") end)
        assert(not positive,"positive repair assertion accepted disabled code")
    end)
    os.remove(path);assert(ok,err)
end)
print(string.format("AUTO_CUREBO_SUMMARY %d passed / %d failed; native Lua mocks only",passed,failed))
if failed>0 then os.exit(1) end
