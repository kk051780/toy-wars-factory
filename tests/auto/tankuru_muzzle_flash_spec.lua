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
local function countFlash(model)
    local count=0
    for _,child in ipairs(model:GetChildren()) do
        if child.Name=="MuzzleFlash" then count=count+1 end
    end
    return count
end
local function facesIncomingLane(model)
    local core=assert(model:FindFirstChild("Core"))
    local cannon=assert(model:FindFirstChild("Cannon"))
    local face=assert(model:FindFirstChild("Face"))
    local flash=assert(model:FindFirstChild("MuzzleFlash"))
    local tracks=assert(model:FindFirstChild("Tracks"))
    -- Test +Z orientation, full face bounds and all front-facing occluders.
    local cf,ff=cannon.CFrame,face.CFrame
    return cf.LookVector and ff.LookVector
        and cf.LookVector.Z>0.99 and ff.LookVector.Z>0.99
        and ff.Position.Z-face.Size.Z/2>core.CFrame.Position.Z+core.Size.Z/2
        and flash.CFrame.Position.Z>cf.Position.Z+cannon.Size.Z/2
        and ff.Position.Y+face.Size.Y/2<cf.Position.Y-cannon.Size.Y/2
        and ff.Position.Y+face.Size.Y/2<flash.CFrame.Position.Y-flash.Size.Y/2
        and ff.Position.Y-face.Size.Y/2>tracks.CFrame.Position.Y+tracks.Size.Y/2
end
check("tankuru owns one initially hidden 3D neon flash",function()
    local _,_,entity=fixture()
    local tank=entity("tankuru","ally",0,0)
    local flash=assert(tank.model:FindFirstChild("MuzzleFlash"))
    assert(countFlash(tank.model)==1,"exactly one pooled flash")
    assert(flash:IsA("BasePart") and flash.Shape=="PartType.Ball")
    assert(flash.Material=="Material.Neon")
    assert(flash.Anchored and not flash.CanCollide and flash.CanTouch==false)
    assert(flash.Transparency==1)
    assert(flash.CFrame.Position.Z>0)
end)
check("cannon and face point toward the approaching positive-Z JUNK lane",function()
    local _,_,entity=fixture()
    local tank=entity("tankuru","ally",0,0)
    assert(facesIncomingLane(tank.model),"visible face and +Z orientation")
end)
check("reversed cannon orientation is rejected by the facing predicate",function()
    local _,_,entity=fixture()
    local model=entity("tankuru","ally",0,0).model
    local cannon=model:FindFirstChild("Cannon")
    local old=cannon.CFrame
    cannon.CFrame={Position=old.Position,LookVector={X=0,Y=0,Z=-1}}
    assert(not facesIncomingLane(model))
end)
check("occluded face is rejected by the visibility predicate",function()
    local _,_,entity=fixture()
    local model=entity("tankuru","ally",0,0).model
    local face=model:FindFirstChild("Face")
    local old=face.CFrame
    face.CFrame={Position={X=0,Y=2.1,Z=1.28},LookVector=old.LookVector}
    assert(not facesIncomingLane(model))
end)
check("forward face hidden by cannon is rejected",function()
    local _,_,entity=fixture()
    local model=entity("tankuru","ally",0,0).model
    local face=assert(model:FindFirstChild("Face"))
    local old=face.CFrame
    face.CFrame={Position={X=0,Y=2.1,Z=2.65},LookVector=old.LookVector}
    assert(not facesIncomingLane(model),"previous face Y must be occluded")
end)
check("forward face hidden by a moved muzzle flash is rejected",function()
    local _,_,entity=fixture()
    local model=entity("tankuru","ally",0,0).model
    local flash=assert(model:FindFirstChild("MuzzleFlash"))
    flash.CFrame={Position={X=0,Y=1.3,Z=5.7}}
    assert(not facesIncomingLane(model),"flash front projection must be rejected")
end)
check("duplicate flash object is detected by exact child count",function()
    local _,_,entity=fixture()
    local model=entity("tankuru","ally",0,0).model
    assert(countFlash(model)==1)
    local children=model._children -- mock backing list; not a Roblox instance API
    children[#children+1]={Name="MuzzleFlash"}
    assert(countFlash(model)==2)
    table.remove(children)
    assert(countFlash(model)==1)
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
    assert(countFlash(tank.model)==1)
    update(s,tank,0.1)
    s.combatTime=0.3;tank.cooldown=10
    update(s,tank,0.1)
    assert(flash.Transparency==1)
    tank.cooldown=0
    update(s,tank,0.1)
    assert(flash.Transparency==0.08 and tank.model:FindFirstChild("MuzzleFlash")==flash)
    assert(#tank.model:GetChildren()==count)
    assert(countFlash(tank.model)==1,"no duplicate flashes after reuse")
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
