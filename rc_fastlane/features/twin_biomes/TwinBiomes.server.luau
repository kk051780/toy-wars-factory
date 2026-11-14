--!nocheck
-- P0D S2+ PRIVATE63 / F03-F04: Twin Biomes + 4 neutral NPC species.
-- Coral Reef Lab (tidal screen, route lantern) and Thunder Cloud Lookout
-- (scenic flash, signal tower), mirrored for BOTH teams.
-- One optional Studio server Script, NO Game/Remote/Store/HP/score/XP/currency owner.
-- All NPCs are temporary event guides, NOT capturable or saved collectibles.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then
    return
end
local ServerStorage = game:GetService("ServerStorage")
local Workspace = game:GetService("Workspace")
local Players = game:GetService("Players")
local FLAG = "P0D_ENABLE_TWIN_BIOMES_V1"
local value = ServerStorage:FindFirstChild(FLAG)
if not value or not value:IsA("BoolValue") or value.Value ~= true then
    return -- Missing/false = OFF; Studio explicit opt-in only.
end
if ServerStorage:GetAttribute("P0D_RC_ENABLE_WCS_F01_C01") ~= true then
    return
end
if Workspace:FindFirstChild("P0D_TwinBiomes") then
    return -- Never create a duplicate world if hot-reloaded.
end

-- WCS itself is installed by a different server script, after up to 102s of
-- bounded canonical SkyV5 boot. A strict bounded wait avoids random boot-order
-- failures. Do not construct scenery when WCS did not initialize.
local canyon = Workspace:FindFirstChild("P0D_WCS_CrystalCanyon")
    or Workspace:WaitForChild("P0D_WCS_CrystalCanyon", 145)
local anchor = Workspace:FindFirstChild("P0D_CrystalCanyonAnchor")
    or Workspace:WaitForChild("P0D_CrystalCanyonAnchor", 15)
if not canyon or not canyon:IsA("Model")
    or not anchor or not anchor:IsA("BasePart")
    or anchor:GetAttribute("P0DWorldOptIn") ~= true then
    warn("[P0D/TWIN] WCS prerequisite missing; worlds not created")
    return
end
local west = canyon:WaitForChild("WestBank", 12)
local east = canyon:WaitForChild("EastBank", 12)
local safe = canyon:WaitForChild("AlwaysOpenSafeRoute", 12)
if not west or not east or not safe
    or not west:IsA("BasePart") or not east:IsA("BasePart")
    or not safe:IsA("BasePart") then
    warn("[P0D/TWIN] no real WCS banks or permanent crossing")
    return
end
if not west.Anchored or not east.Anchored
    or not west.CanCollide or not east.CanCollide or not safe.CanCollide then
    return
end
-- Original WCS bank centers: anchor local (-50,0,0) and (+50,0,0).
-- X bounds on each site never exceed 75; Z within local [-42.5,42.5].
-- Real Game recovers players when abs(X)>130 or abs(Z)>76.
if (west.Position - anchor.CFrame:PointToWorldSpace(Vector3.new(-50, -2, 0))).Magnitude > 2
    or (east.Position - anchor.CFrame:PointToWorldSpace(Vector3.new(50, -2, 0))).Magnitude > 2
    or west.Size.X < 49 or east.Size.X < 49
    or west.Size.Z < 84 or east.Size.Z < 84 then
    warn("[P0D/TWIN] WCS map geometry changed; fail closed")
    return
end

local world = Instance.new("Model")
world.Name = "P0D_TwinBiomes"
world:SetAttribute("FeatureId", "TWIN_BIOMES_4NPC_V1")
world:SetAttribute("StudioOptInOnly", true)
world:SetAttribute("NoDamageXpScoreSave", true)
world:SetAttribute("BothTeamsAccess", true)
world:SetAttribute("Biomes", 2)
world:SetAttribute("Species", 4)
world:SetAttribute("CharacterInstances", 8)
world:SetAttribute("PersistedCollection", false)
world:SetAttribute("SessionCodexOnly", true)
world:SetAttribute("FourUniqueCreatureSilhouettes", true)
world.Parent = Workspace

local function part(name, size, x, y, z, color, material, collide, parent)
    local p = Instance.new("Part")
    p.Name = name
    p.Size = size
    p.CFrame = anchor.CFrame * CFrame.new(x, y, z)
    p.Anchored = true
    p.CanCollide = collide == true
    p.CanTouch = false
    p.CanQuery = collide == true
    p.Material = material or Enum.Material.SmoothPlastic
    p.Color = color
    p.TopSurface = Enum.SurfaceType.Smooth
    p.BottomSurface = Enum.SurfaceType.Smooth
    p.Parent = parent or world
    return p
end

local coral = Color3.fromRGB(255, 135, 167)
local aqua = Color3.fromRGB(61, 234, 227)
local pearl = Color3.fromRGB(234, 251, 255)
local storm = Color3.fromRGB(84, 108, 161)
local gold = Color3.fromRGB(250, 210, 94)
local blue = Color3.fromRGB(95, 154, 255)
local dark = Color3.fromRGB(31, 49, 93)

local curtains = {}
local routeLamps = {}
local stormLamps = {}
local watchLamps = {}
local routeTexts = {}
local animate = {}
local seenByPlayer = {}
local sessionSpecies = {"AWARIN", "SANGORU", "RAIKO", "KUMONON"}
Players.PlayerRemoving:Connect(function(p) seenByPlayer[p] = nil end)

local function addSign(target, name, initial, offsetY)
    local gui = Instance.new("BillboardGui")
    gui.Name = name
    gui.AlwaysOnTop = true
    gui.MaxDistance = 100
    gui.Size = UDim2.fromOffset(200, 62)
    gui.StudsOffsetWorldSpace = Vector3.new(0, offsetY or 5, 0)
    gui.Parent = target
    local txt = Instance.new("TextLabel")
    txt.Name = "Readout"
    txt.Size = UDim2.fromScale(1, 1)
    txt.BackgroundTransparency = 0.26
    txt.BackgroundColor3 = dark
    txt.BorderSizePixel = 0
    txt.Text = initial
    txt.TextColor3 = pearl
    txt.TextStrokeTransparency = 0.3
    txt.TextScaled = true
    txt.Font = Enum.Font.GothamBold
    txt.Parent = gui
    return txt
end

-- Both shores get ALL content: no class restriction, no team-exclusive reward.
for _, spec in ipairs({
    {side = "West", sign = -1, x = -50},
    {side = "East", sign = 1, x = 50},
}) do
    -- FIELD F03: the coral garden is a shallow, fixed hiding alcove on the
    -- outer half of a WCS bank; timed water curtain is VISUAL ONLY, not a
    -- misleading invulnerability or permanent wall across an egg route.
    local reef = Instance.new("Model")
    reef.Name = "CoralGarden_" .. spec.side
    reef:SetAttribute("Biotope", "TIDAL_CORAL_GARDEN")
    reef.Parent = world
    part("PearlFloor", Vector3.new(19, 0.45, 14),
        spec.x, 0.23, -24, pearl, Enum.Material.Sand, true, reef)
    for i = 1, 4 do
        local x = spec.x + (i - 2.5) * 4
        local reefStem = part("CoralBranch_" .. i, Vector3.new(1.6, 3.8 + i % 2, 1.6),
            x, 2.1, -29, i % 2 == 0 and coral or aqua, Enum.Material.Neon, false, reef)
        reefStem.Shape = Enum.PartType.Ball
    end
    local veil = part("TidalCurtain_" .. spec.side, Vector3.new(17, 8, 0.35),
        spec.x, 4.5, -31.3, aqua, Enum.Material.Glass, false, reef)
    veil.Transparency = 0.93
    table.insert(curtains, veil)
    local lamp = part("ReefRouteLamp_" .. spec.side, Vector3.new(2.4, 8, 2.4),
        spec.x + spec.sign * 7, 4, -18.8, coral, Enum.Material.Neon, false, reef)
    lamp.Transparency = 0.7
    table.insert(routeLamps, lamp)
    table.insert(routeTexts, addSign(lamp, "RouteStatus", "サンゴの灯台\n橋を見渡そう", 7))

    -- FIELD F04: a permanent 5-stud observation platform, reached by six
    -- fixed shallow stairs. Never disappears while anyone stands on it.
    local lookout = Instance.new("Model")
    lookout.Name = "ThunderLookout_" .. spec.side
    lookout:SetAttribute("Biotope", "STORM_CLOUD_LOOKOUT")
    lookout.Parent = world
    part("ThunderEntry", Vector3.new(18, 0.45, 12),
        spec.x, 0.23, 16, dark, Enum.Material.Slate, true, lookout)
    for i = 1, 6 do
        part("AlwaysOpenStair_" .. string.format("%02d", i), Vector3.new(9, 0.85, 2.55),
            spec.x, 0.7 + i * 0.75, 13 - i * 2.4,
            storm, Enum.Material.Slate, true, lookout)
    end
    local deck = part("AlwaysOpenObservationDeck", Vector3.new(17, 1, 15),
        spec.x, 5.5, -5, dark, Enum.Material.Slate, true, lookout)
    deck:SetAttribute("AlwaysOpen", true)
    for _, edge in ipairs({-1, 1}) do
        part("SafetyRail_" .. (edge < 0 and "Left" or "Right"),
            Vector3.new(0.6, 3.2, 15), spec.x + edge * 8.2, 7.5, -5,
            blue, Enum.Material.Glass, true, lookout)
    end
    part("RearGuard", Vector3.new(17, 3.2, 0.6),
        spec.x, 7.5, -12.2, blue, Enum.Material.Glass, true, lookout)
    local lightning = part("LightningBeacon_" .. spec.side, Vector3.new(2, 8, 2),
        spec.x + spec.sign * 5, 10.6, -9, gold, Enum.Material.Neon, false, lookout)
    lightning.Transparency = 0.8
    local light = Instance.new("PointLight")
    light.Brightness = 0
    light.Range = 18
    light.Color = gold
    light.Parent = lightning
    table.insert(stormLamps, {part = lightning, light = light})
    local cloud = part("CloudCompass_" .. spec.side, Vector3.new(5, 0.7, 5),
        spec.x - spec.sign * 5, 6.4, -5, aqua, Enum.Material.Neon, false, lookout)
    cloud.Shape = Enum.PartType.Ball
    cloud.Transparency = 0.85
    table.insert(watchLamps, cloud)
end

local EFFECT_SECONDS = 16
local REARM_SECONDS = 4
local activeUntil = {}
local nextUse = {}

local species = {
    -- New collectible candidates are only biome NPCs for now. No save/gacha.
    {id = "AWARIN", name = "アワリン", rarity = "COMMON",
        effect = "TIDE_VEIL", action = "泡のカーテン", biome = "REEF",
        localZ = -24, dx = -5, y = 2.5, tint = aqua},
    {id = "SANGORU", name = "サンゴル", rarity = "RARE",
        effect = "ROUTE_LANTERN", action = "橋を見わたす", biome = "REEF",
        localZ = -24, dx = 5, y = 2.5, tint = coral},
    {id = "RAIKO", name = "ライコ", rarity = "EPIC",
        effect = "THUNDER_SIGNAL", action = "雷の灯をともす", biome = "STORM",
        localZ = -5, dx = -5, y = 8, tint = gold},
    {id = "KUMONON", name = "クモノン", rarity = "LEGENDARY",
        effect = "CLOUD_COMPASS", action = "雲の方位を示す", biome = "STORM",
        localZ = -5, dx = 5, y = 8, tint = pearl},
}

local function activate(effect)
    local now = os.clock()
    if now < (nextUse[effect] or 0) then
        return
    end
    activeUntil[effect] = now + EFFECT_SECONDS
    nextUse[effect] = now + EFFECT_SECONDS + REARM_SECONDS
    world:SetAttribute(effect .. "_EndsAt", activeUntil[effect])
    world:SetAttribute(effect .. "_SharedByBothTeams", true)
end

local function markDiscovery(player,info)
    -- Session-only owner-scoped species discovery. No Game/Remote/Store writes.
    if not player or player.Parent~=Players then return end
    local seen=seenByPlayer[player]
    if not seen then
        seen={}
        seenByPlayer[player]=seen
    end
    if seen[info.id] then return end
    seen[info.id]=true
    local count=0
    for _,id in ipairs(sessionSpecies) do
        if seen[id] then count+=1 end
    end
    player:SetAttribute("P0D_TwinCodexCount",count)
    player:SetAttribute("P0D_TwinSeen_"..info.id,true)
    player:SetAttribute("P0D_TwinCodexComplete",count==4)
    local head=player.Character and player.Character:FindFirstChild("Head")
    if not head or not head:IsA("BasePart") then return end
    local toast=head:FindFirstChild("P0D_TwinCodexToast")
    if not toast then
        toast=Instance.new("BillboardGui")
        toast.Name="P0D_TwinCodexToast"
        toast.Size=UDim2.fromOffset(215,55)
        toast.StudsOffsetWorldSpace=Vector3.new(0,5.8,0)
        toast.MaxDistance=80
        toast.AlwaysOnTop=true
        toast.Parent=head
        local label=Instance.new("TextLabel")
        label.Name="Message"
        label.Size=UDim2.fromScale(1,1)
        label.BackgroundColor3=dark
        label.BackgroundTransparency=0.2
        label.TextColor3=gold
        label.TextScaled=true
        label.Font=Enum.Font.GothamBold
        label.Parent=toast
    end
    local label=toast:FindFirstChild("Message")
    if label and label:IsA("TextLabel") then
        label.Text=(count==4 and "幻の生き物 4/4 発見！"
            or ("新発見！ "..info.name.."\nいきもの図鑑 "..count.."/4"))
    end
    local expires=os.clock()+5
    toast:SetAttribute("ExpiresAt",expires)
    task.delay(5.2,function()
        if toast.Parent and (toast:GetAttribute("ExpiresAt") or 0)<=os.clock() then
            toast:Destroy()
        end
    end)
end

local function makeGuide(info, side)
    local x = side.x + info.dx
    local npc = Instance.new("Model")
    npc.Name = info.id .. "_" .. side.name
    npc:SetAttribute("SpeciesId", info.id)
    npc:SetAttribute("Rarity", info.rarity)
    npc:SetAttribute("Region", info.biome)
    npc:SetAttribute("PotentialCodexCharacter", true)
    npc:SetAttribute("CapturableOrOwned", false)
    npc:SetAttribute("EffectId", info.effect)
    npc.Parent = world
    local body = part("Body", Vector3.new(3.5, 3.5, 3.5), x, info.y,
        info.localZ, info.tint, Enum.Material.SmoothPlastic, false, npc)
    body.Shape = Enum.PartType.Ball
    for _, d in ipairs({-0.9,0.9}) do
        local eye = part("Eye", Vector3.new(0.45, 0.55, 0.45),
            x + d, info.y + 0.4, info.localZ - 1.65, dark,
            Enum.Material.Neon, false, npc)
        eye.Shape = Enum.PartType.Ball
    end
    local crest = part("Crest", Vector3.new(1.1, 1.3, 1.1), x,
        info.y + 2, info.localZ, info.tint, Enum.Material.Neon, false, npc)
    crest.Shape = Enum.PartType.Ball

    -- Visual silhouette is deliberately different for EACH species, not a
    -- recolor of one template. All decorative pieces are anchored, non-solid
    -- and belong to the one neutral NPC model (no extra enemies/spawns).
    local function decor(name,size,dx,dy,dz,tint,shape,alpha)
        local p = part(name,size,x+dx,info.y+dy,info.localZ+dz,
            tint,Enum.Material.Neon,false,npc)
        if shape=="Ball" then p.Shape=Enum.PartType.Ball end
        p.Transparency=alpha or 0
        return p
    end
    if info.id=="AWARIN" then
        -- Bubble creature: translucent halo and floating foam bubbles.
        decor("BubbleHalo",Vector3.new(5,5,5),0,0.1,0,aqua,"Ball",0.67)
        for i=1,4 do
            local offset=(i-2.5)*1.25
            decor("Foam_"..i,Vector3.new(0.85,0.85,0.85),
                offset,1.9+math.abs(offset)*0.32,0.3,pearl,"Ball",0.24)
        end
    elseif info.id=="SANGORU" then
        -- Coral creature: upward branching coral antlers and asymmetric crest.
        for side=-1,1,2 do
            decor("CoralAntler_"..side,Vector3.new(0.85,3.3,0.85),
                side*1.15,2.65,0,coral,nil,0)
            decor("CoralFork_"..side,Vector3.new(1.7,0.75,0.85),
                side*1.85,3.75,0,pearl,nil,0)
        end
    elseif info.id=="RAIKO" then
        -- Lightning creature: bright gold pointed vertical energy horns.
        for side=-1,1,2 do
            decor("ThunderHorn_"..side,Vector3.new(0.8,3.1,0.75),
                side*1.1,2.6,0,gold,nil,0)
            decor("ThunderBolt_"..side,Vector3.new(1.85,0.65,0.75),
                side*1.65,3.9,0,aqua,nil,0)
        end
    elseif info.id=="KUMONON" then
        -- Cloud creature: soft four-puff wings on both shoulders.
        for side=-1,1,2 do
            for i=1,2 do
                decor("CloudWing_"..side.."_"..i,
                    Vector3.new(2.7,2.0,2.2),side*(2+i*1.05),
                    i*0.75,-0.15,pearl,"Ball",0.14)
            end
        end
    end
    -- Moving anchored models with PivotTo keeps eyes, crest, and hitless
    -- ornaments together. No movement touches the real player or live map.
    npc.PrimaryPart=body
    table.insert(animate,{model=npc,base=npc:GetPivot(),phase=#animate*1.37})

    local prompt = Instance.new("ProximityPrompt")
    prompt.Name = "P0D_" .. info.effect
    prompt.ActionText = info.action
    prompt.ObjectText = info.name
    prompt.HoldDuration = 0.55
    prompt.MaxActivationDistance = 11
    prompt.RequiresLineOfSight = false
    prompt.Parent = body
    prompt.Triggered:Connect(function(player)
        local char = player and player.Character
        local root = char and char:FindFirstChild("HumanoidRootPart")
        local hum = char and char:FindFirstChildOfClass("Humanoid")
        if not root or not hum or hum.Health <= 0 or hum.Sit or root.Anchored then
            return
        end
        if (root.Position - body.Position).Magnitude > 12 then
            return
        end
        activate(info.effect)
        markDiscovery(player,info)
    end)
    addSign(body,"NPCLabel",info.name .. "\n" .. info.rarity, 4.3)
end

for _, side in ipairs({
    {name = "West", x = -50},
    {name = "East", x = 50},
}) do
    for _, info in ipairs(species) do
        makeGuide(info, side)
    end
end

local function visible(effect)
    return os.clock() < (activeUntil[effect] or 0)
end

local function currentRouteText()
    -- An informative beacon, NOT a wallhack: shows only public world routes.
    local gate = canyon:FindFirstChild("ShortcutGate")
    local star = Workspace:FindFirstChild("P0D_STARRY_PATH")
    local gateActive = gate and gate:GetAttribute("WCS_GateOpen") == true
    local starActive = star and star:GetAttribute("PathOpen") == true
    return "モグロン " .. (gateActive and "開" or "閉")
        .. "\n星の橋 " .. (starActive and "開" or "閉")
end

task.spawn(function()
    -- One 1s loop for ALL eight characters. No Heartbeat per NPC and no
    -- unbounded clones, physics, damage or per-player persistent data.
    while world.Parent do
        local timeNow=os.clock()
        for _,entry in ipairs(animate) do
            local bob=math.sin(timeNow*2+entry.phase)*0.28
            local turn=math.sin(timeNow*0.7+entry.phase)*0.12
            entry.model:PivotTo(entry.base*CFrame.new(0,bob,0)*CFrame.Angles(0,turn,0))
        end
        local veil = visible("TIDE_VEIL")
        for _, p in ipairs(curtains) do
            p.Transparency = veil and 0.32 or 0.93
        end
        local route = visible("ROUTE_LANTERN")
        for _, p in ipairs(routeLamps) do
            p.Transparency = route and 0.06 or 0.7
        end
        for _, txt in ipairs(routeTexts) do
            txt.Text = route and currentRouteText() or "サンゴの灯台\n橋を見渡そう"
        end
        local flash = visible("THUNDER_SIGNAL")
        for _, obj in ipairs(stormLamps) do
            obj.part.Transparency = flash and 0.05 or 0.8
            obj.light.Brightness = flash and 1.8 or 0
        end
        local compass = visible("CLOUD_COMPASS")
        for _, p in ipairs(watchLamps) do
            p.Transparency = compass and 0.1 or 0.85
        end
        task.wait(0.25)
    end
end)

world:SetAttribute("Status", "PRIVATE64_POLISH_WITH_SESSION_CODEX_STUDIO_UNTESTED")
world:SetAttribute("NoRemoteStoreScoreXpDamage", true)
