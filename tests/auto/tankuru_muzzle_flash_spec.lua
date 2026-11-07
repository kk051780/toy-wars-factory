-- Canonical server, no Studio/engine/rendering claim. Test a bounded,
-- pooled tank-cannon neon muzzle flash and preservation of combat authority.
local H=dofile("tests/roblox_server_harness.lua")
local B=dofile("src/ToyWarsBalance.lua")
local passed,failed=0,0
local function up(fn,name)
    for i=1,80 do
        local k,v=debug.getupvalue(fn,i)
        if not k then break end
        if k==name then return v end
    end
    error("missing canonical upvalue "..name)
end
local function fixture()
    local h=H.new(os.getenv("TWF_SERVER_FILE") or "src/ToyWarsServer.server.lua")
    local p=h:addPlayer(h:newPlayer())
    local beat=assert(h.runService.Heartbeat.listeners[1]).fn
    local simulate=up(beat,"simulate")
    local s=assert(up(beat,"sessions")[p])
    local add=up(simulate,"addEntity")
    local update=up(simulate,"updateEntity")
    s.productionTimer=100;s.waveBreak=100
    local function entity(id,side,x,z)
        local e=assert(add(s,id,side))
        e.x=s.x+(x or 0);e.z=z or 0;e.cooldown=0
        return e
    end
    local function boss(x,z)
        s.wave.Value=10;s.enemyTarget=B.waveSize(10)
        s.enemiesMade=s.enemyTarget-1
        local b=entity("junk","enemy",x,z)
        assert(b.boss)
        return b
    end
    return h,s,entity,update,boss
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then passed=passed+1;print("PASS "..name)
    else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
check("tankuru owns one initially hidden 3D neon flash",function()
    local _,_,entity=fixture()
    local tank=entity("tankuru","ally",0,0)
    local flash=assert(tank.model:FindFirstChild("MuzzleFlash"))
    assert(flash:IsA("BasePart") and flash.Shape==Enum.PartType.Ball)
    assert(flash.Material==Enum.Material.Neon)
    assert(flash.Anchored and not flash.CanCollide and flash.CanTouch==false)
    assert(flash.Transparency==1)
    assert(flash.CFrame.Position.Z>0)
end)
check("cannon and face point toward the approaching positive-Z JUNK lane",function()
    local _,_,entity=fixture()
    local tank=entity("tankuru","ally",0,0)
    assert(tank.model:FindFirstChild("Cannon").CFrame.Position.Z>0)
    assert(tank.model:FindFirstChild("Face").CFrame.Position.Z>0)
end)
check("valid tankuru hit illuminates flash and deals normal 19 damage",function()
    local _,s,entity,update=fixture()
    local tank=entity("tankuru","ally",0,0)
    local junk=entity("junk","enemy",0,4)
    update(s,tank,0.3)
    assert(junk.health==19)
    assert(tank.model:FindFirstChild("MuzzleFlash").Transparency==0.08)
    assert(tank.muzzleFlashUntil==0.18 and tank.cooldown>0)
end)
check("flash expires on server time without creating another shot",function()
    local _,s,entity,update=fixture()
    local tank=entity("tankuru","ally",0,0)
    local junk=entity("junk","enemy",0,4)
    update(s,tank,0.1)
    local flash=tank.model:FindFirstChild("MuzzleFlash")
    s.combatTime=0.2;tank.cooldown=10
    update(s,tank,0.01)
    assert(flash.Transparency==1 and tank.muzzleFlashUntil==nil)
    assert(junk.health==19)
end)
check("no target or out-of-range target cannot flash",function()
    local _,s,entity,update=fixture()
    local tank=entity("tankuru","ally",0,0)
    local flash=tank.model:FindFirstChild("MuzzleFlash")
    update(s,tank,0.1)
    assert(flash.Transparency==1)
    entity("junk","enemy",0,30)
    update(s,tank,0.1)
    assert(flash.Transparency==1 and tank.muzzleFlashUntil==nil)
end)
check("cooldown cannot produce extra light or damage",function()
    local _,s,entity,update=fixture()
    local tank=entity("tankuru","ally",0,0)
    local junk=entity("junk","enemy",0,4)
    tank.cooldown=3
    update(s,tank,0.01)
    assert(junk.health==38 and tank.muzzleFlashUntil==nil)
    assert(tank.model:FindFirstChild("MuzzleFlash").Transparency==1)
end)
check("same flash instance reused, no per-shot growth",function()
    local _,s,entity,update=fixture()
    local tank=entity("tankuru","ally",0,0)
    entity("junk","enemy",0,4)
    local flash=tank.model:FindFirstChild("MuzzleFlash")
    local count=#tank.model:GetChildren()
    update(s,tank,0.1)
    s.combatTime=0.3;tank.cooldown=10
    update(s,tank,0.1)
    assert(flash.Transparency==1)
    tank.cooldown=0
    update(s,tank,0.1)
    assert(flash.Transparency==0.08 and tank.model:FindFirstChild("MuzzleFlash")==flash)
    assert(#tank.model:GetChildren()==count)
end)
check("boss focus still applies with the cannon flash",function()
    local _,s,entity,update,boss=fixture()
    local tank=entity("tankuru","ally",0,0)
    local junk=entity("junk","enemy",0,0)
    local captain=boss(0,12)
    update(s,tank,0.1)
    assert(captain.health==captain.maxHealth-19 and junk.health==38)
    assert(tank.model:FindFirstChild("MuzzleFlash").Transparency==0.08)
end)
check("no muzzle flash part is allocated to other playable toys",function()
    local _,s,entity,update=fixture()
    for _,id in ipairs({"pon","guardon","curebo"}) do
        local ally=entity(id,"ally",0,0)
        assert(ally.model:FindFirstChild("MuzzleFlash")==nil)
    end
    entity("junk","enemy",0,0)
    for _,ally in ipairs(s.entities) do
        if ally.side=="ally" then
            update(s,ally,0.1)
            assert(ally.muzzleFlashUntil==nil)
        end
    end
end)
check("destroying tankuru also destroys its pooled flash",function()
    local _,s,entity,update=fixture()
    local tank=entity("tankuru","ally",0,0)
    entity("junk","enemy",0,0)
    update(s,tank,0.1)
    local flash=tank.model:FindFirstChild("MuzzleFlash")
    assert(flash.Transparency==0.08)
    tank.model:Destroy()
    assert(flash.Parent==nil)
end)
print(string.format("TANKURU_3D_MUZZLE_SUMMARY %d passed / %d failed; canonical-server Lua mocks ONLY",passed,failed))
if failed>0 then os.exit(1) end
