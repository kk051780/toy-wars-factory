--!nocheck
-- P0D FB-STAGE-LOOT V1: real world-placed usable temporary weapons.
-- Existing original Game still owns attack cooldown, damage, Horde KO, egg, score.
-- Private Studio preview / explicit private server opt-in only; public disabled.
local StageLoot={}
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
local active=setmetatable({},{__mode="k"})
local pickups={}
local folder=nil
local validation=nil
local epoch=0
local DURATION=18
local RESPAWN=15
local LOOT={
    SUN_BLADE={name="炎の大剣",color=Color3.fromRGB(255,131,57),damage=1.35,reach=0},
    WIND_SPEAR={name="疾風の槍",color=Color3.fromRGB(77,237,190),damage=1.08,reach=3.5},
    THUNDER_BOW={name="雷光の弩",color=Color3.fromRGB(177,139,255),damage=1.22,reach=1.7},
}
local SPAWNS={
    {-52,-26,"SUN_BLADE"},{0,43,"SUN_BLADE"},
    {52,-26,"WIND_SPEAR"},{-52,26,"WIND_SPEAR"},
    {0,-43,"THUNDER_BOW"},{52,26,"THUNDER_BOW"},
}
local function allowed()
    return RunService:IsStudio() or (game.PrivateServerId~=""
        and workspace:GetAttribute("P0D_PRIVATE_STAGE_WEAPON_LOOT")==true)
end
local function part(parent,name,size,at,color,material)
    local p=Instance.new("Part")
    p.Name=name
    p.Size=size
    p.CFrame=at
    p.Color=color
    p.Material=material or Enum.Material.Metal
    p.Anchored=true
    p.CanCollide=false
    p.CanTouch=false
    p.CanQuery=false
    p.CastShadow=false
    p.Parent=parent
    return p
end
local function setVisible(pick,show)
    pick.visible=show
    local displayed=show and allowed()
    for _,p in ipairs(pick.parts) do
        p.Transparency=if displayed then (if p.Name=="WeaponLootGlow" then .18 else .03) else 1
    end
    pick.prompt.Enabled=displayed
end
local function clearVisual(player)
    local char=player.Character
    local held=char and char:FindFirstChild("P0D_STAGE_WEAPON_LOOT_HELD")
    if held then held:Destroy() end
end
function StageLoot.clearPlayer(player)
    active[player]=nil
    clearVisual(player)
    if player.Parent==Players then
        player:SetAttribute("P0D_StageLootKind",nil)
        player:SetAttribute("P0D_StageLootUntil",nil)
    end
end
function StageLoot.clearAll()
    for player in pairs(active) do StageLoot.clearPlayer(player) end
end
local function addHeldGlow(player,kind)
    clearVisual(player)
    local char=player.Character
    local hand=char and (char:FindFirstChild("RightHand") or char:FindFirstChild("Right Arm"))
    if not hand or not hand:IsA("BasePart") then return end
    local aura=Instance.new("Model")
    aura.Name="P0D_STAGE_WEAPON_LOOT_HELD"
    local flame=Instance.new("Part")
    flame.Name="LootWeaponRune"
    flame.Shape=Enum.PartType.Ball
    flame.Size=Vector3.new(.6,.6,.6)
    flame.Material=Enum.Material.Neon
    flame.Color=LOOT[kind].color
    flame.Transparency=.18
    flame.Massless=true
    flame.CanCollide=false;flame.CanTouch=false;flame.CanQuery=false
    flame.CastShadow=false
    flame.Anchored=false
    flame.CFrame=hand.CFrame*CFrame.new(0,-1.3,-.35)
    flame.Parent=aura
    local weld=Instance.new("WeldConstraint")
    weld.Part0=hand;weld.Part1=flame;weld.Parent=flame
    aura.Parent=char
end
local function spawnPickup(parent,index,x,z,kind)
    local spec=LOOT[kind]
    local model=Instance.new("Model")
    model.Name="P0D_STAGE_WEAPON_PICKUP_"..tostring(index).."_"..kind
    model:SetAttribute("LootKind",kind)
    model.Parent=parent
    local center=Vector3.new(x,1.6,z)
    local base=part(model,"WeaponLootPedestal",Vector3.new(4,.5,4),
        CFrame.new(x,.3,z),Color3.fromRGB(61,76,99),Enum.Material.Slate)
    local glow=part(model,"WeaponLootGlow",Vector3.new(3,.12,3),
        CFrame.new(x,.65,z),spec.color,Enum.Material.Neon)
    local h=part(model,"WeaponLootGrip",Vector3.new(.25,2.4,.25),
        CFrame.new(center),Color3.fromRGB(215,229,245))
    local head=part(model,"WeaponLootHead",Vector3.new(
            if kind=="THUNDER_BOW" then 2.3 elseif kind=="SUN_BLADE" then .65 else .4,
            if kind=="SUN_BLADE" then 2.6 elseif kind=="WIND_SPEAR" then 3.2 else .45,
            .28),CFrame.new(center+Vector3.new(0,1.75,0)),spec.color,Enum.Material.Neon)
    if kind=="THUNDER_BOW" then
        part(model,"WeaponLootBolt",Vector3.new(.2,1.5,.32),
            CFrame.new(center+Vector3.new(0,1.5,-.38)),Color3.fromRGB(229,221,255),Enum.Material.Neon)
    elseif kind=="SUN_BLADE" then
        part(model,"WeaponLootCrossguard",Vector3.new(1.35,.22,.34),
            CFrame.new(center+Vector3.new(0,.7,0)),Color3.fromRGB(246,217,94))
    else
        part(model,"WeaponLootSpearTip",Vector3.new(.65,.8,.65),
            CFrame.new(center+Vector3.new(0,3.35,0)),Color3.fromRGB(246,245,211),Enum.Material.Neon)
    end
    local pickup={model=model,parts={},visible=true,prompt=nil,kind=kind}
    for _,desc in ipairs(model:GetChildren()) do
        if desc:IsA("BasePart") then table.insert(pickup.parts,desc) end
    end
    local prompt=Instance.new("ProximityPrompt")
    prompt.Name="P0D_STAGE_WEAPON_PICKUP_PROMPT"
    prompt.ActionText="拾って使う"
    prompt.ObjectText=spec.name.."・18秒"
    prompt.HoldDuration=.3
    prompt.MaxActivationDistance=9
    prompt.RequiresLineOfSight=false
    prompt.Enabled=allowed()
    prompt.Parent=base
    pickup.prompt=prompt
    prompt.Triggered:Connect(function(player)
        if not allowed() or not pickup.visible or not validation then return end
        local ok,roundId,root=validation(player)
        if not ok or type(roundId)~="number" or not root then return end
        if (root.Position-base.Position).Magnitude>10 then return end
        local now=workspace:GetServerTimeNow()
        -- Server-owned short-duration boost: no permanent weapon, no purchase.
        StageLoot.clearPlayer(player)
        active[player]={kind=kind,expires=now+DURATION,roundId=roundId}
        player:SetAttribute("P0D_StageLootKind",kind)
        player:SetAttribute("P0D_StageLootUntil",now+DURATION)
        addHeldGlow(player,kind)
        setVisible(pickup,false)
        local capture=epoch
        task.delay(DURATION,function()
            local current=active[player]
            if capture==epoch and current and current.kind==kind
                and current.roundId==roundId and current.expires<=workspace:GetServerTimeNow()+.05 then
                StageLoot.clearPlayer(player)
            end
        end)
        task.delay(RESPAWN,function()
            if capture==epoch and model.Parent then setVisible(pickup,true) end
        end)
    end)
    return pickup
end
function StageLoot.start(parent,canClaim)
    if folder then return false end
    if not parent or not parent.Parent or type(canClaim)~="function" then return false end
    epoch+=1
    validation=canClaim
    folder=Instance.new("Folder")
    folder.Name="P0D_STAGE_USABLE_WEAPON_LOOT"
    folder.Parent=parent
    for index,d in ipairs(SPAWNS) do
        table.insert(pickups,spawnPickup(folder,index,d[1],d[2],d[3]))
    end
    -- Private flags may have been disabled before module initialization.
    for _,pickup in ipairs(pickups) do setVisible(pickup,true) end
    workspace:GetAttributeChangedSignal("P0D_PRIVATE_STAGE_WEAPON_LOOT"):Connect(function()
        if not allowed() then StageLoot.clearAll() end
        for _,pickup in ipairs(pickups) do
            if pickup.visible then setVisible(pickup,true) end
        end
    end)
    return true
end
function StageLoot.endRound()
    epoch+=1
    StageLoot.clearAll()
    -- All six floor pickups respawn clean for next match; no delayed callback
    -- from the previous match is permitted to alter the next match state.
    for _,pickup in ipairs(pickups) do
        if pickup.model.Parent then setVisible(pickup,true) end
    end
end
local function validActive(player,now,roundId)
    if not allowed() or type(roundId)~="number" then return nil end
    local claim=active[player]
    if not claim or claim.roundId~=roundId or now>=claim.expires then return nil end
    if not validation then return nil end
    local ok,currentRound=validation(player)
    if not ok or currentRound~=roundId then return nil end
    return LOOT[claim.kind]
end
function StageLoot.damageMultiplier(player,now,roundId)
    local buff=validActive(player,now,roundId)
    return if buff then buff.damage else 1
end
function StageLoot.hitOrigin(player,origin,direction,now,roundId)
    local buff=validActive(player,now,roundId)
    if not buff or buff.reach<=0 then return origin end
    local v=Vector3.new(direction.X,0,direction.Z)
    return if v.Magnitude>.01 then origin+v.Unit*buff.reach else origin
end
Players.PlayerRemoving:Connect(function(player)
    StageLoot.clearPlayer(player)
end)
return StageLoot
