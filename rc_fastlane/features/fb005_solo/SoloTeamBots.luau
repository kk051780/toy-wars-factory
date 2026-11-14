--!nocheck
-- FB-005 / #361: Studio SOLO 2 ally and 3 opponent team raiders.
-- THIS IS A PHYSICAL AGENT/INTENT ENGINE ONLY. The sole original Game still
-- validates and writes every egg, score, player HP and winner transaction.
-- No RemoteEvent, DataStore, TouchPrompt impersonation or fake Player.
local RunService=game:GetService("RunService")
local Players=game:GetService("Players")
local PathfindingService=game:GetService("PathfindingService")
local Bot={}
local active=false
local epoch=0
local map=nil
local callbacks=nil
local folder=nil
local bots={}
local REPATH_SECONDS=3.1
local TARGET_REFRESH=.6
local MAX_BOTS=5
local TICK_MIN=.35
local lastTick=-math.huge

local function tagPart(model,name,sz,pos,col,mat)
    local p=Instance.new("Part")
    p.Name=name;p.Size=sz;p.CFrame=pos
    p.Material=mat;p.Color=col
    p.CanTouch=false
    p.CanCollide=name=="Torso"
    p.CanQuery=p.CanCollide
    p.Parent=model
    return p
end
local function motor(parent,name,p0,p1,c0,c1)
    local j=Instance.new("Motor6D")
    j.Name=name;j.Part0=p0;j.Part1=p1;j.C0=c0;j.C1=c1;j.Parent=parent
    return j
end
local function makeActor(id,team,style,spawn)
    local m=Instance.new("Model")
    m.Name="SOLO_TEAM_"..team.."_"..style.."_"..id
    m:SetAttribute("P0D_StudioSoloBot",true)
    m:SetAttribute("P0D_BotTeam",team)
    m:SetAttribute("P0D_BotRole",style)
    local tone=if team=="RED" then Color3.fromRGB(174,56,73)
        else Color3.fromRGB(56,113,190)
    local armor=if style=="GUARD" then Color3.fromRGB(75,88,104)
        else Color3.fromRGB(80,133,110)
    local root=tagPart(m,"HumanoidRootPart",Vector3.new(2,2,1),
        spawn,Color3.new(0,0,0),Enum.Material.SmoothPlastic)
    root.Transparency=1;root.CanCollide=false
    local torso=tagPart(m,"Torso",Vector3.new(2.2,2.1,1.2),
        spawn,armor,Enum.Material.Metal)
    local head=tagPart(m,"Head",Vector3.new(1.3,1.3,1.3),
        spawn*CFrame.new(0,1.65,0),Color3.fromRGB(226,195,149),
        Enum.Material.SmoothPlastic)
    head.Shape=Enum.PartType.Ball
    local leftArm=tagPart(m,"Left Arm",Vector3.new(.85,2,.85),
        spawn*CFrame.new(-1.6,0,0),tone,Enum.Material.Metal)
    local rightArm=tagPart(m,"Right Arm",Vector3.new(.85,2,.85),
        spawn*CFrame.new(1.6,0,0),tone,Enum.Material.Metal)
    local leftLeg=tagPart(m,"Left Leg",Vector3.new(.9,1.9,.9),
        spawn*CFrame.new(-.57,-1.95,0),armor,Enum.Material.Metal)
    local rightLeg=tagPart(m,"Right Leg",Vector3.new(.9,1.9,.9),
        spawn*CFrame.new(.57,-1.95,0),armor,Enum.Material.Metal)
    motor(root,"RootJoint",root,torso,CFrame.new(),CFrame.new())
    motor(torso,"Neck",torso,head,CFrame.new(0,1.13,0),CFrame.new(0,-.57,0))
    motor(torso,"Left Shoulder",torso,leftArm,
        CFrame.new(-1.1,.55,0),CFrame.new(.45,.55,0))
    motor(torso,"Right Shoulder",torso,rightArm,
        CFrame.new(1.1,.55,0),CFrame.new(-.45,.55,0))
    motor(torso,"Left Hip",torso,leftLeg,
        CFrame.new(-.53,-1,0),CFrame.new(0,.95,0))
    motor(torso,"Right Hip",torso,rightLeg,
        CFrame.new(.53,-1,0),CFrame.new(0,.95,0))
    local hum=Instance.new("Humanoid")
    hum.RigType=Enum.HumanoidRigType.R6
    hum.MaxHealth=if style=="GUARD" then 105 else 78
    hum.Health=hum.MaxHealth
    hum.WalkSpeed=if style=="GUARD" then 13 else 17
    hum.DisplayDistanceType=Enum.HumanoidDisplayDistanceType.None
    hum.Parent=m
    local helmet=tagPart(m,"Helmet",Vector3.new(1.46,.48,1.45),
        head.CFrame*CFrame.new(0,.45,0),tone,Enum.Material.Metal)
    helmet.CanCollide=false
    local shield=nil
    if style=="GUARD" then
        shield=tagPart(m,"GuardianShield",Vector3.new(.35,2.1,1.7),
            leftArm.CFrame*CFrame.new(-.55,-.4,-.6),tone,Enum.Material.Metal)
        shield.Shape=Enum.PartType.Ball
        shield.CanCollide=false
        local w=Instance.new("WeldConstraint")
        w.Part0=leftArm;w.Part1=shield;w.Parent=shield
    else
        local weapon=tagPart(m,"RaiderSword",Vector3.new(.28,2.9,.44),
            rightArm.CFrame*CFrame.new(.25,-1.3,-.6),Color3.fromRGB(212,213,208),
            Enum.Material.Metal)
        weapon.CanCollide=false
        local w=Instance.new("WeldConstraint")
        w.Part0=rightArm;w.Part1=weapon;w.Parent=weapon
    end
    local wh=Instance.new("WeldConstraint")
    wh.Part0=head;wh.Part1=helmet;wh.Parent=helmet
    m.PrimaryPart=root
    m.Parent=folder
    -- Network physics stays server-owned.  No player input controls these bots.
    for _,part in ipairs(m:GetDescendants()) do
        if part:IsA("BasePart") then
            part.Anchored=false
            pcall(function() part:SetNetworkOwner(nil) end)
        end
    end
    local state={id=id,team=team,style=style,
        model=m,hum=hum,root=root,spawn=spawn,carry=nil,deadUntil=0,
        nextRepath=0,path={},pathIndex=1,planning=false,
        lastAttack=0,lastGoal=nil,pathGeneration=0}
    return state
end

local function invalidatePath(bot)
    -- PathfindingService:ComputeAsync yields; old callbacks must never claim
    -- authority over an agent that just stole an egg, respawned or changed goal.
    bot.pathGeneration+=1
    bot.lastGoal=nil
    bot.path={}
    bot.pathIndex=1
    bot.nextRepath=0
    bot.planning=false
end
local function respawn(bot)
    local nextGeneration=bot.pathGeneration+1
    if bot.model and bot.model.Parent then bot.model:Destroy() end
    local fresh=makeActor(bot.id,bot.team,bot.style,bot.spawn)
    for key,value in pairs(fresh) do bot[key]=value end
    bot.pathGeneration=nextGeneration
    bot.deadUntil=0
    bot.carry=nil
    bot.carryVisual=nil
end
local function showCarriedEgg(bot, yes)
    if bot.carryVisual then bot.carryVisual:Destroy();bot.carryVisual=nil end
    if not yes or not bot.model or not bot.model.Parent then return end
    local shell=Instance.new("Part")
    shell.Name="VISUAL_CARRIED_ENEMY_EGG"
    shell.Shape=Enum.PartType.Ball
    shell.Size=Vector3.new(1.3,1.7,1.3)
    shell.Color=Color3.fromRGB(255,219,125)
    shell.Material=Enum.Material.Glass
    shell.CFrame=bot.model.Torso.CFrame*CFrame.new(0,1.1,-1.3)
    shell.CanCollide=false;shell.CanTouch=false;shell.CanQuery=false
    shell.Massless=true
    shell.Parent=bot.model
    local weld=Instance.new("WeldConstraint")
    weld.Part0=bot.model.Torso;weld.Part1=shell;weld.Parent=shell
    bot.carryVisual=shell
end
local function clearCarry(bot)
    showCarriedEgg(bot,false)
    if bot.carry then
        if callbacks then callbacks.drop(bot,bot.carry) end
        bot.carry=nil
    end
end
function Bot.stop()
    epoch+=1
    active=false
    for _,bot in ipairs(bots) do
        clearCarry(bot)
        if bot.model then bot.model:Destroy() end
    end
    table.clear(bots)
    if folder then folder:Destroy();folder=nil end
    map=nil;callbacks=nil
    lastTick=-math.huge
end

function Bot.start(world,humanTeam,authority)
    Bot.stop()
    if not RunService:IsStudio() or #Players:GetPlayers()~=1 then return false end
    if humanTeam~="RED" and humanTeam~="BLUE" then return false end
    if type(authority)~="table" or type(authority.steal)~="function"
        or type(authority.deposit)~="function" or type(authority.drop)~="function"
        or type(authority.attackHuman)~="function"
        or type(authority.attackBot)~="function" then return false end
    if type(world)~="table" or not world.model or not world.teams then return false end
    folder=Instance.new("Folder")
    folder.Name="FB005_STUDIO_REAL_TEAM_BOTS"
    folder.Parent=world.model
    folder:SetAttribute("StudioBotPreview",true)
    folder:SetAttribute("OneOriginalGameOwnsScoreEggHP",true)
    folder:SetAttribute("HumanFUN","NOT_TESTED")
    map=world;callbacks=authority
    local enemy=if humanTeam=="RED" then "BLUE" else "RED"
    local formation={
        {team=humanTeam,style="RAIDER",index=1},
        {team=humanTeam,style="GUARD",index=2},
        {team=enemy,style="RAIDER",index=1},
        {team=enemy,style="RAIDER",index=2},
        {team=enemy,style="GUARD",index=3},
    }
    for i,def in ipairs(formation) do
        local start=world.teams[def.team].spawn
            *CFrame.new(0,3,def.index*6-12)
        table.insert(bots,makeActor(tostring(i),def.team,def.style,start))
    end
    assert(#bots==MAX_BOTS)
    active=true
    return true
end

local function alive(bot)
    return bot.hum and bot.hum.Health>0 and bot.model and bot.model.Parent~=nil
end
local function pathTo(bot,goal,now)
    if bot.planning or now<bot.nextRepath then return end
    bot.nextRepath=now+REPATH_SECONDS
    local token=epoch
    local generation=bot.pathGeneration
    local planningRoot=bot.root
    bot.planning=true
    task.spawn(function()
        local ok,path=pcall(function()
            local p=PathfindingService:CreatePath({
                AgentRadius=2,AgentHeight=5,AgentCanJump=true,WaypointSpacing=7})
            p:ComputeAsync(planningRoot.Position,goal)
            return p
        end)
        -- Both the global match and this particular bot/goal must still be
        -- current. A respawn can happen while ComputeAsync is yielding.
        local current=active and epoch==token and bot.pathGeneration==generation
            and bot.root==planningRoot and alive(bot)
            and bot.lastGoal~=nil and (bot.lastGoal-goal).Magnitude<=8
        if current then
            if ok and path and path.Status==Enum.PathStatus.Success then
                bot.path=path:GetWaypoints()
                bot.pathIndex=math.min(2,#bot.path)
            else
                bot.path={}
                bot.pathIndex=1
            end
        end
        -- Old asynchronous planners must not release a newer planner's lock.
        if bot.pathGeneration==generation and bot.root==planningRoot then
            bot.planning=false
        end
    end)
end
local function move(bot,goal,now)
    -- Rival positions and the raid objective can change WHILE ComputeAsync
    -- yields. Revoke any path planned for a materially different destination.
    if bot.lastGoal==nil or (bot.lastGoal-goal).Magnitude>8 then
        invalidatePath(bot)
    end
    bot.lastGoal=goal
    pathTo(bot,goal,now)
    local actual=goal
    if bot.pathIndex<=#bot.path then
        local waypoint=bot.path[bot.pathIndex]
        if (bot.root.Position-waypoint.Position).Magnitude<5 then
            bot.pathIndex+=1
            waypoint=bot.path[bot.pathIndex]
        end
        if waypoint then
            actual=waypoint.Position
            if waypoint.Action==Enum.PathWaypointAction.Jump then
                bot.hum.Jump=true
            end
        end
    end
    bot.hum:MoveTo(actual)
end
local function nearestEnemyBot(bot,maxDistance)
    local result=nil
    local nearest=maxDistance
    for _,other in ipairs(bots) do
        if other~=bot and other.team~=bot.team and alive(other) then
            local d=(bot.root.Position-other.root.Position).Magnitude
            if d<nearest then result=other;nearest=d end
        end
    end
    return result,nearest
end
local function nearestHuman(bot,maxDistance)
    local result=nil
    local nearest=maxDistance
    for _,p in ipairs(Players:GetPlayers()) do
        local team=p.Team and p.Team.Name
        local ch=p.Character
        local root=ch and ch:FindFirstChild("HumanoidRootPart")
        local hum=ch and ch:FindFirstChildOfClass("Humanoid")
        if team~=bot.team and root and hum and hum.Health>0 then
            local d=(bot.root.Position-root.Position).Magnitude
            if d<nearest then result=p;nearest=d end
        end
    end
    return result,nearest
end
function Bot.tick(now)
    if not active or type(now)~="number" or now-lastTick<TICK_MIN then return end
    lastTick=now
    if #Players:GetPlayers()~=1 then Bot.stop();return end
    for _,bot in ipairs(bots) do
        if not alive(bot) then
            if bot.deadUntil==0 then
                clearCarry(bot)
                bot.deadUntil=now+8
            elseif now>=bot.deadUntil then respawn(bot) end
        else
            local enemy=if bot.team=="RED" then "BLUE" else "RED"
            local target=if bot.carry then map.teams[bot.team].scorePad.Position
                elseif bot.style=="GUARD" then map.teams[bot.team].egg.Position
                else map.teams[enemy].egg.Position
            local player,dp=nearestHuman(bot,8)
            local rival,db=nearestEnemyBot(bot,8)
            local combatTarget=if player and dp<=db then player else rival
            if combatTarget and now>=bot.lastAttack+2.1 then
                bot.lastAttack=now
                if combatTarget==player then callbacks.attackHuman(bot,player,6)
                else callbacks.attackBot(bot,rival,6) end
            end
            if not bot.carry and bot.style=="RAIDER"
                and (bot.root.Position-map.teams[enemy].egg.Position).Magnitude<=7 then
                if callbacks.steal(bot,enemy) then
                    bot.carry=enemy
                    showCarriedEgg(bot,true)
                    invalidatePath(bot)
                end
            elseif bot.carry and
                (bot.root.Position-map.teams[bot.team].scorePad.Position).Magnitude<=7 then
                if callbacks.deposit(bot,bot.team,bot.carry) then
                    if not active then return end
                    bot.carry=nil
                    showCarriedEgg(bot,false)
                    invalidatePath(bot)
                end
            end
            -- Steal/deposit may change bot.carry above. Do NOT reuse the
            -- pre-transaction target for the same-tick MoveTo.
            local waypoint=if bot.carry then map.teams[bot.team].scorePad.Position
                elseif bot.style=="GUARD" then map.teams[bot.team].egg.Position
                else map.teams[enemy].egg.Position
            if bot.style=="GUARD" then
                if rival and db<14 then waypoint=rival.root.Position
                elseif player and dp<14 and player.Character then
                    local r=player.Character:FindFirstChild("HumanoidRootPart")
                    if r then waypoint=r.Position end
                end
            end
            if (bot.root.Position-waypoint).Magnitude>=4.5 then
                move(bot,waypoint,now)
            else
                bot.hum:MoveTo(bot.root.Position)
            end
        end
    end
end
function Bot.tryHumanHit(team,origin,look,reach,attackerCharacter)
    if not active then return nil end
    local best=nil
    local closest=reach+.001
    for _,bot in ipairs(bots) do
        if alive(bot) and bot.team~=team then
            local delta=bot.root.Position-origin
            local d=delta.Magnitude
            local dot=if d>.001 then look:Dot(delta.Unit) else 1
            if d<=reach and dot>=.25 and d<closest then
                local params=RaycastParams.new()
                params.FilterType=Enum.RaycastFilterType.Exclude
                params.FilterDescendantsInstances={bot.model,folder,attackerCharacter}
                local hit=workspace:Raycast(origin,delta,params)
                if not hit then
                    best=bot
                    closest=d
                end
            end
        end
    end
    return best
end
function Bot.isActive() return active end
function Bot.botCount() return #bots end
function Bot.models() return bots end
return Bot
