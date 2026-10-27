--!strict
-- TOY WARS FACTORY v1.2 / PLAYABLE PVE VERTICAL SLICE.
-- Server-authoritative solo factory arenas, wave combat and upgrades.
-- Session only: no DataStore, no purchasable content, no PvP yet.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local B = require(ReplicatedStorage:WaitForChild("ToyWarsBalance"))

local oldWorld = workspace:FindFirstChild("ToyWarsWorld")
if oldWorld then oldWorld:Destroy() end
local world = Instance.new("Folder")
world.Name = "ToyWarsWorld"
world.Parent = workspace
local MAX_PLOTS = 4
local SPACING = 108
local sessions = {}
local occupied = {}
local SLOT_COLORS = {Color3.fromRGB(33, 187, 193), Color3.fromRGB(250, 147, 76), Color3.fromRGB(157, 127, 237), Color3.fromRGB(109, 200, 112)}
local UNIT_COLORS = {
    pon = Color3.fromRGB(45, 209, 210),
    guardon = Color3.fromRGB(72, 130, 239),
    tankuru = Color3.fromRGB(255, 166, 83),
    junk = Color3.fromRGB(173, 83, 118),
}
local selectEvent = ReplicatedStorage:WaitForChild("ToyWarsSelectUnit")

local function part(parent, name, size, cf, color, material)
    local p = Instance.new("Part")
    p.Name = name
    p.Anchored = true
    p.CanCollide = false
    p.TopSurface = Enum.SurfaceType.Smooth
    p.BottomSurface = Enum.SurfaceType.Smooth
    p.Size = size
    p.CFrame = cf
    p.Color = color
    p.Material = material or Enum.Material.SmoothPlastic
    p.Parent = parent
    return p
end

local function label(adornee, contents, width, height, offset)
    local bb = Instance.new("BillboardGui")
    bb.Name = "Caption"
    bb.Adornee = adornee
    bb.AlwaysOnTop = true
    bb.MaxDistance = 130
    bb.Size = UDim2.fromOffset(width or 175, height or 60)
    bb.StudsOffsetWorldSpace = Vector3.new(0, offset or 4, 0)
    bb.Parent = adornee
    local txt = Instance.new("TextLabel")
    txt.BackgroundColor3 = Color3.fromRGB(19, 29, 48)
    txt.BackgroundTransparency = 0.18
    txt.TextColor3 = Color3.fromRGB(246, 250, 255)
    txt.Text = contents
    txt.TextScaled = true
    txt.TextWrapped = true
    txt.Font = Enum.Font.GothamBold
    txt.Size = UDim2.fromScale(1,1)
    txt.Parent = bb
    local corner = Instance.new("UICorner")
    corner.CornerRadius = UDim.new(0, 9)
    corner.Parent = txt
    return txt
end

local function chooseSlot()
    for i=1,MAX_PLOTS do
        if not occupied[i] then return i end
    end
    return nil
end

local function plotCenter(slot)
    return (slot - (MAX_PLOTS+1)/2) * SPACING
end

local function setInt(parent, name, value)
    local v = Instance.new("IntValue")
    v.Name = name
    v.Value = value
    v.Parent = parent
    return v
end

local function modelPart(parent, name, offset, size, col, ball)
    local p = part(parent, name, size, CFrame.new(offset), col)
    if ball then p.Shape = Enum.PartType.Ball end
    return p
end

local function createToyModel(id, x, z)
    local m = Instance.new("Model")
    m.Name = id:upper()
    local c = UNIT_COLORS[id]
    local core = modelPart(m,"Core",Vector3.new(0,1.7,0),Vector3.new(3,3,2.4),c,false)
    m.PrimaryPart = core
    modelPart(m,"Face",Vector3.new(0,2.1,-1.28),Vector3.new(2,1.3,0.12),Color3.fromRGB(250,251,255),false)
    if id == "pon" then
        modelPart(m,"Antenna",Vector3.new(0,3.5,0),Vector3.new(0.5,1.0,0.5),Color3.fromRGB(250,210,76),true)
        modelPart(m,"Feet",Vector3.new(0,0.25,0),Vector3.new(3.5,0.5,2.8),Color3.fromRGB(30,100,140),false)
    elseif id == "guardon" then
        modelPart(m,"Shield",Vector3.new(-2.0,1.7,-0.5),Vector3.new(1.2,3.7,2.8),Color3.fromRGB(255,234,130),false)
        modelPart(m,"Feet",Vector3.new(0,0.2,0),Vector3.new(3.6,0.5,2.9),Color3.fromRGB(39,69,137),false)
    elseif id == "tankuru" then
        core.Size = Vector3.new(4.5,2,5)
        core.CFrame = CFrame.new(0,1.45,0)
        modelPart(m,"Cannon",Vector3.new(0,2.8,-3),Vector3.new(1.0,1.0,5),Color3.fromRGB(55,70,92),false)
        modelPart(m,"Tracks",Vector3.new(0,0.3,0),Vector3.new(5.5,0.6,6),Color3.fromRGB(60,65,85),false)
    else
        modelPart(m,"ScrapHat",Vector3.new(0,3.8,0),Vector3.new(3.8,0.7,3.0),Color3.fromRGB(91,59,78),false)
        modelPart(m,"Feet",Vector3.new(0,0.2,0),Vector3.new(3.3,0.5,2.5),Color3.fromRGB(120,66,90),false)
    end
    local hp = part(m,"HealthBar",Vector3.new(3.2,0.33,0.4),CFrame.new(0,4.7,0), id=="junk" and Color3.fromRGB(255,95,102) or Color3.fromRGB(107,255,147),Enum.Material.Neon)
    hp.Transparency = 0.12
    m.Parent = world
    m:PivotTo(CFrame.new(x,2.5,z))
    return m
end

local function refreshStatus(state)
    -- Publish a stable snapshot once per changed field, not zero then count
    -- on every Heartbeat (which generates redundant client value changes).
    local selected = string.upper(state.selected)
    local allies, enemies = 0, 0
    for _, e in ipairs(state.entities) do
        if e.alive then
            if e.side == "ally" then allies = allies + 1
            else enemies = enemies + 1 end
        end
    end
    if state.selectedValue.Value ~= selected then state.selectedValue.Value = selected end
    if state.unitsValue.Value ~= allies then state.unitsValue.Value = allies end
    if state.enemiesValue.Value ~= enemies then state.enemiesValue.Value = enemies end
end

local function makePlot(player, state)
    local x = state.x
    local map = Instance.new("Folder")
    map.Name = "Workshop_" .. tostring(player.UserId)
    map.Parent = world
    state.map = map
    local battlefield = part(map,"FeltBattlefield",Vector3.new(92,1,92),CFrame.new(x,0,0),Color3.fromRGB(90,152,119),Enum.Material.Grass)
    battlefield.CanCollide = true
    for z = -30,30,12 do
        part(map,"BattleStripe",Vector3.new(78,0.08,0.55),CFrame.new(x,0.55,z),Color3.fromRGB(216,228,184))
    end
    local factoryFloor = part(map,"FactoryFloor",Vector3.new(38,1.2,23),CFrame.new(x,0.7,-35),Color3.fromRGB(214,225,237))
    factoryFloor.CanCollide = true
    part(map,"Conveyor",Vector3.new(7,0.6,20),CFrame.new(x-8,1.5,-34),Color3.fromRGB(49,64,83),Enum.Material.Metal)
    for z = -43,-26,3 do
        part(map,"BeltStripe",Vector3.new(7.2,0.12,0.7),CFrame.new(x-8,1.85,z),Color3.fromRGB(85,108,133))
    end
    local machine = part(map,"ToyPrinter",Vector3.new(11,7,7),CFrame.new(x-8,4.2,-46),SLOT_COLORS[state.slot])
    label(machine,"TOY PRINTER\nAuto-production",220,74,6)
    local enemyDoor = part(map,"JunkPortal",Vector3.new(19,9,4),CFrame.new(x,4.7,45),Color3.fromRGB(135,66,105),Enum.Material.Neon)
    label(enemyDoor,"JUNK PIRATES\nIncoming!",220,65,7)
    local base = part(map,"BlueprintVault",Vector3.new(14,7,5),CFrame.new(x,4.0,-45),Color3.fromRGB(75,118,238),Enum.Material.Metal)
    label(base, player.DisplayName.."'s\nBLUEPRINT VAULT",235,77,7)

    local choices = {{"pon", x+8}, {"guardon", x+20},{"tankuru",x+32}}
    for _, entry in ipairs(choices) do
        local id = entry[1]
        local px = entry[2]
        local pad = part(map,id.."Selector",Vector3.new(9,1.4,8),CFrame.new(px,1.2,-40),UNIT_COLORS[id],Enum.Material.Neon)
        label(pad,string.upper(id).."\n"..B.UNITS[id].cost.." coins",150,65,3.3)
        local prompt=Instance.new("ProximityPrompt")
        prompt.ObjectText="Toy printer"
        prompt.ActionText="Select "..string.upper(id)
        prompt.MaxActivationDistance=12
        prompt.HoldDuration=0
        prompt.RequiresLineOfSight=false
        prompt.Parent=pad
        prompt.Triggered:Connect(function(actor)
            if actor ~= player or not state.active then return end
            -- Never trust a client-triggered prompt without checking server-side proximity.
            local character=actor.Character
            local root=character and character:FindFirstChild("HumanoidRootPart")
            if not root or not ((root.Position-pad.Position).Magnitude <= 13) then return end
            state.selected=id
            refreshStatus(state)
        end)
    end
    local station = part(map,"UpgradeStation",Vector3.new(10,2,8),CFrame.new(x+18,1.5,-23),Color3.fromRGB(255,217,96),Enum.Material.Neon)
    local upgradeLabel=label(station,"UPGRADE",205,80,3.7)
    local upgradePrompt=Instance.new("ProximityPrompt")
    upgradePrompt.Name="UpgradePrompt"
    upgradePrompt.ObjectText="Factory generator"
    upgradePrompt.ActionText="Upgrade"
    upgradePrompt.MaxActivationDistance=12
    upgradePrompt.HoldDuration=0
    upgradePrompt.RequiresLineOfSight=false
    upgradePrompt.Parent=station
    local function refreshUpgrade()
        local price=B.upgradePrice(state.level.Value)
        if price then
            upgradeLabel.Text=string.format("UPGRADE Lv.%d to %d\n%d coins",state.level.Value,state.level.Value+1,price)
            upgradePrompt.ActionText="Upgrade - "..price
        else
            upgradeLabel.Text="MAX LEVEL"
            upgradePrompt.Enabled=false
        end
    end
    refreshUpgrade()
    upgradePrompt.Triggered:Connect(function(actor)
        if actor ~= player or not state.active then return end
        -- A forged proximity event must not upgrade from across the map.
        local character=actor.Character
        local root=character and character:FindFirstChild("HumanoidRootPart")
        if not root or not ((root.Position-station.Position).Magnitude <= 13) then return end
        local price=B.upgradePrice(state.level.Value)
        if not price or state.coins.Value<price then return end
        state.coins.Value = state.coins.Value-price
        state.level.Value = state.level.Value+1
        refreshUpgrade()
    end)
end

local function aliveCount(state, side)
    local count=0
    for _,e in ipairs(state.entities) do
        if e.alive and e.side==side then count=count+1 end
    end
    return count
end

local function addEntity(state, id, side)
    local data=B.getUnit(id)
    if not data then return nil end
    local z=side=="ally" and -24 or 26
    local offset=(state.spawnOrdinal % 5 - 2) * 4
    state.spawnOrdinal=state.spawnOrdinal+1
    local e={
        id=id, side=side, health=data.hp, maxHealth=data.hp, cooldown=0,
        x=state.x+offset, z=z, alive=true, model=createToyModel(id,state.x+offset,z),
        renderedX=state.x+offset, renderedZ=z,
    }
    state.entities[#state.entities+1]=e
    return e
end

local function removeEntity(e)
    if not e.alive then return end
    e.alive=false
    if e.model and e.model.Parent then e.model:Destroy() end
end

local function killEntity(state, e, attacker)
    if not e.alive then return end
    removeEntity(e)
    if e.side=="enemy" and attacker and attacker.side=="ally" then
        local new=B.awardCoins(state.coins.Value,B.UNITS[e.id].reward)
        if new then state.coins.Value=new end
        state.kills.Value=state.kills.Value+1
    end
end

local function closestOpponent(state, entity)
    local best=nil
    local bestDistSquared=math.huge
    for _,target in ipairs(state.entities) do
        if target.alive and target.side~=entity.side then
            local dx=target.x-entity.x
            local dz=target.z-entity.z
            local dSquared=dx*dx+dz*dz
            if dSquared<bestDistSquared then
                bestDistSquared=dSquared
                best=target
            end
        end
    end
    return best,best and math.sqrt(bestDistSquared) or math.huge
end

local function refreshHealthBar(e)
    if not e.alive or not e.model or not e.model.Parent then return end
    local bar=e.model:FindFirstChild("HealthBar")
    if bar and bar:IsA("BasePart") then
        local width=3.2*math.max(.01,e.health/e.maxHealth)
        local size=bar.Size
        if size.X~=width or size.Y~=0.33 or size.Z~=0.4 then
            bar.Size=Vector3.new(width,0.33,0.4)
        end
    end
end

local function updateEntity(state,e,dt)
    if not e.alive then return end
    local data=B.UNITS[e.id]
    local remaining=e.cooldown>0 and e.cooldown-dt or 0
    e.cooldown=math.max(0,remaining)
    local target, dist=closestOpponent(state,e)
    if target and dist <= data.range then
        if e.cooldown<=0 then
            local remain=B.nextHP(target.health,target.maxHealth,data.damage)
            if remain then
                target.health=remain
                -- Refresh the damaged victim now, even if its turn already passed.
                if remain<=0 then killEntity(state,target,e) else refreshHealthBar(target) end
            end
            e.cooldown=data.cooldown+math.min(0,remaining)
        end
    else
        local tx= e.x
        local tz= e.side=="ally" and 40 or -41
        if target then tx=target.x;tz=target.z end
        local dx=tx-e.x
        local dz=tz-e.z
        local distance=math.sqrt(dx*dx+dz*dz)
        if distance>0.001 then
            local travel=math.min(distance,data.speed*dt)
            e.x=e.x+dx/distance*travel
            e.z=e.z+dz/distance*travel
        end
    end
    if e.side=="enemy" and e.z <= -40 then
        state.baseHP.Value=math.max(0,state.baseHP.Value-12)
        removeEntity(e)
    elseif e.side=="ally" and e.z >= 39 then
        local coins=B.awardCoins(state.coins.Value,4)
        if coins then state.coins.Value=coins end
        removeEntity(e)
    end
    if e.alive and e.model.Parent then
        -- Anchored models already occupy their last rendered position.
        -- Avoid redundant PivotTo calls for stationary combat units.
        if e.x~=e.renderedX or e.z~=e.renderedZ then
            e.model:PivotTo(CFrame.new(e.x,2.5,e.z))
            e.renderedX=e.x
            e.renderedZ=e.z
        end
    end
end

local function sweepEntities(state)
    for i=#state.entities,1,-1 do
        if not state.entities[i].alive then table.remove(state.entities,i) end
    end
end

local function resetAfterLoss(state)
    for _,e in ipairs(state.entities) do removeEntity(e) end
    state.entities={}
    state.baseHP.Value=100
    state.wave.Value=1
    state.coins.Value=math.max(40,state.coins.Value)
    state.enemiesMade=0
    state.enemyTarget=B.waveSize(1)
    state.enemyTimer=0.1
    state.waveBreak=4
    state.productionTimer=1
end

local function simulate(state,dt)
    if not state.active then return end
    local income=B.incomePerSecond(state.level.Value)
    if not income then income=6 end
    state.incomeCarry=state.incomeCarry+income*dt
    if state.incomeCarry>=1 then
        local whole=math.floor(state.incomeCarry)
        state.incomeCarry=state.incomeCarry-whole
        local new=B.awardCoins(state.coins.Value,whole)
        if new then state.coins.Value=new end
    end

    state.productionTimer=state.productionTimer-dt
    if state.productionTimer<=0 then
        state.productionTimer=state.productionTimer+3.0
        if aliveCount(state,"ally")<B.MAX_FIELD_UNITS then
            local new=B.buy(state.selected,state.coins.Value,aliveCount(state,"ally"))
            if new then
                state.coins.Value=new
                addEntity(state,state.selected,"ally")
            end
        end
    end

    if state.waveBreak>0 then
        state.waveBreak=math.max(0,state.waveBreak-dt)
    else
        state.enemyTimer=state.enemyTimer-dt
        if state.enemyTimer<=0 and state.enemiesMade<state.enemyTarget then
            state.enemyTimer=state.enemyTimer+2.3
            addEntity(state,"junk","enemy")
            state.enemiesMade=state.enemiesMade+1
        end
    end
    for _,e in ipairs(state.entities) do updateEntity(state,e,dt) end
    sweepEntities(state)
    if state.baseHP.Value<=0 then
        resetAfterLoss(state)
    elseif state.waveBreak<=0 and state.enemiesMade>=state.enemyTarget and aliveCount(state,"enemy")==0 then
        local reward=B.waveReward(state.wave.Value)
        local new=B.awardCoins(state.coins.Value,reward or 0)
        if new then state.coins.Value=new end
        state.baseHP.Value=math.min(100,state.baseHP.Value+18)
        if state.wave.Value>=B.MAX_WAVE then
            state.wave.Value=1
        else
            state.wave.Value=state.wave.Value+1
        end
        state.enemyTarget=B.waveSize(state.wave.Value)
        state.enemiesMade=0
        state.enemyTimer=0.1
        state.waveBreak=5
    end
    refreshStatus(state)
end

local spawn=Instance.new("SpawnLocation")
spawn.Name="ToyWarsLobbySpawn"
spawn.Anchored=true
spawn.Neutral=true
spawn.Size=Vector3.new(16,1,16)
spawn.Position=Vector3.new(0,3,-75)
spawn.Color=Color3.fromRGB(250,205,91)
spawn.Material=Enum.Material.Neon
spawn.Parent=world
local lobbyGround = part(world,"LobbyGround",Vector3.new(930,1,200),CFrame.new(0,-2,0),Color3.fromRGB(112,169,144),Enum.Material.Grass)
lobbyGround.CanCollide = true

local function join(player)
    if player.Parent ~= Players or sessions[player] then return end
    local slot=chooseSlot()
    if not slot then
        warn("TWF v1.2: no free workshop plots for",player.UserId)
        return
    end
    occupied[slot]=player
    local stats=Instance.new("Folder")
    stats.Name="leaderstats"
    stats.Parent=player
    local coins=setInt(stats,"Coins",50)
    local wave=setInt(stats,"Wave",1)
    local kills=setInt(stats,"Defeated",0)
    local status=Instance.new("Folder")
    status.Name="ToyWarsStatus"
    status.Parent=player
    local level=setInt(status,"FactoryLevel",1)
    local hp=setInt(status,"BaseHP",100)
    local units=setInt(status,"Allies",0)
    local enemies=setInt(status,"Enemies",0)
    local selected=Instance.new("StringValue")
    selected.Name="SelectedToy"
    selected.Value="PON"
    selected.Parent=status
    local state={
        slot=slot,x=plotCenter(slot),active=true,map=nil,
        coins=coins,wave=wave,kills=kills,baseHP=hp,level=level,
        unitsValue=units,enemiesValue=enemies,selectedValue=selected,selected="pon",
        entities={},spawnOrdinal=0,enemyTarget=B.waveSize(1),enemiesMade=0,
        productionTimer=1.2,enemyTimer=0.1,waveBreak=4,incomeCarry=0,
    }
    sessions[player]=state
    makePlot(player,state)
    local function characterReady(character)
        -- Retry bounded waits for a slow HumanoidRootPart, not a replaced character.
        local root
        for _=1,3 do
            root=character:WaitForChild("HumanoidRootPart",8)
            if root then break end
        end
        if root then
            task.wait(0.1)
            -- Character or session may have changed while the callback yielded.
            if not state.active or sessions[player] ~= state or player.Parent ~= Players or player.Character ~= character then return end
            character:PivotTo(CFrame.new(state.x+17,6,-37))
        end
    end
    player.CharacterAdded:Connect(characterReady)
    if player.Character then task.spawn(characterReady,player.Character) end
end

selectEvent.OnServerEvent:Connect(function(player,selected)
    local state=sessions[player]
    if not state or not state.active then return end
    if not B.isUnit(selected) then return end
    if os.clock() - (state.lastSelection or -100) < 0.12 then return end
    state.lastSelection=os.clock()
    state.selected=selected
    state.selectedValue.Value=string.upper(selected)
end)
Players.PlayerAdded:Connect(join)
Players.PlayerRemoving:Connect(function(player)
    local state=sessions[player]
    if not state then return end
    state.active=false
    occupied[state.slot]=nil
    for _,e in ipairs(state.entities) do removeEntity(e) end
    if state.map and state.map.Parent then state.map:Destroy() end
    sessions[player]=nil
    -- Assign a newly freed plot to one player who was waiting at capacity.
    for _,waiting in ipairs(Players:GetPlayers()) do
        if waiting ~= player and waiting.Parent == Players and not sessions[waiting] then
            join(waiting)
            break
        end
    end
end)
for _,player in ipairs(Players:GetPlayers()) do task.spawn(join,player) end

local accumulated=0
RunService.Heartbeat:Connect(function(dt)
    accumulated=accumulated+dt
    if accumulated<0.12 then return end
    local delta=math.min(accumulated,0.3)
    accumulated=accumulated-delta
    for _,state in pairs(sessions) do simulate(state,delta) end
end)
print("TWF_BOOT_OK v1.2: server PVE auto factory and toy battle arena loaded")
