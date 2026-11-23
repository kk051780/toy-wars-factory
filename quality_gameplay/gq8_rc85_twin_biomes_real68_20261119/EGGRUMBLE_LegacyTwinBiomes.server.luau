--!nocheck
-- EGGRUMBLE source-selected twin biomes from original RC85 artifact 14158848286.
-- Studio-only; current V3 WCS canyon is the only stage parent, and old Game is NOT installed.
-- Training/Bond are ORIGINAL pure local policy modules inlined below into one 68th Script.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Workspace=game:GetService("Workspace")
local Players=game:GetService("Players")
local HttpService=game:GetService("HttpService")
local Training=(function()
--!nocheck
-- P0D twin creatures: session-only field practice; does not touch DataStore,
-- Game, rewards, HP, PvP, currency, paid items, gacha or purchase ownership.
-- Pure Luau module so policy can run through the actual native Luau CLI.
local Training = {}

local SPECIES = {
    AWARIN = true,
    SANGORU = true,
    RAIKO = true,
    KUMONON = true,
}
local MAX_PRACTICE = 7
local REPEAT_WAIT_SECONDS = 20

local function safeCount(previous)
    if type(previous) ~= "table" then
        return 0
    end
    local n = previous.xp
    if type(n) ~= "number" or n ~= n or n == math.huge or n == -math.huge then
        return 0
    end
    if n < 0 then
        return 0
    end
    return math.min(MAX_PRACTICE, math.floor(n))
end

function Training.levelFor(xp)
    if type(xp) ~= "number" or xp ~= xp then
        return 1
    end
    if xp >= 7 then return 3 end
    if xp >= 3 then return 2 end
    return 1
end

function Training.effectSeconds(level)
    if level == 3 then return 24 end
    if level == 2 then return 20 end
    return 16
end

function Training.advance(previous, speciesId, now)
    if not SPECIES[speciesId] or type(now) ~= "number" or now ~= now
        or now < 0 or now == math.huge or now == -math.huge then
        return previous, false, false
    end
    local xp = safeCount(previous)
    local waitUntil = (type(previous) == "table" and previous.nextAt) or 0
    if type(waitUntil) ~= "number" or waitUntil ~= waitUntil
        or waitUntil < 0 or waitUntil == math.huge
        or waitUntil == -math.huge then
        waitUntil = 0
    end
    if now < waitUntil or xp >= MAX_PRACTICE then
        return {xp=xp,level=Training.levelFor(xp),nextAt=waitUntil}, false, false
    end
    local nextXP = xp + 1
    local before = Training.levelFor(xp)
    local after = Training.levelFor(nextXP)
    return {
        xp=nextXP,
        level=after,
        nextAt=now+REPEAT_WAIT_SECONDS,
    }, true, after>before
end

function Training.speciesCount()
    return 4
end

return Training

end)()
local Bond=(function()
--!nocheck
-- P0D Twin Bond V1 — server-only, session-only PvE helper.
-- The ONE original Game owns ALL horde health, egg, scores and rewards.
-- This ModuleScript never attacks, damages, stores, purchases or creates Remotes.
local Bond = {}
local MAX_DURATION = 180
local SWITCH_WAIT = 20
local SPECIES = {AWARIN=true,SANGORU=true,RAIKO=true,KUMONON=true}
local state = setmetatable({}, {__mode="k"})

local function finite(n)
    return type(n)=="number" and n==n and n>=0
        and n~=math.huge and n~=-math.huge
end

function Bond.select(player, speciesId, level, now)
    if not player or not SPECIES[speciesId]
        or type(level)~="number" or level~=math.floor(level)
        or level<2 or level>3 or not finite(now) then
        return false, "INVALID"
    end
    local old=state[player]
    if old and old.untilAt>now and old.species~=speciesId
        and now<old.switchAt then
        return false, "SWITCH_COOLDOWN"
    end
    local same = old and old.untilAt>now and old.species==speciesId
    state[player]={
        species=speciesId,level=level,
        -- A re-selection may upgrade Lv2->Lv3, never extend the 180s lease.
        untilAt=(if same then old.untilAt else now+MAX_DURATION),
        switchAt=(if same then old.switchAt else now+SWITCH_WAIT),
    }
    return true,speciesId
end

function Bond.snapshot(player, now)
    if not player or not finite(now) then return nil end
    local current=state[player]
    if not current or now>=current.untilAt then
        state[player]=nil
        return nil
    end
    return {species=current.species,level=current.level,endsAt=current.untilAt}
end

function Bond.pveMultiplier(player, now)
    local current=Bond.snapshot(player,now)
    if not current then return 1 end
    -- hard cap: 20% neutral monster damage bonus, no multiplier for players
    if current.level==3 then return 1.2 end
    return 1.1
end

function Bond.forget(player)
    if player then state[player]=nil end
end

function Bond.speciesCount() return 4 end
return Bond

end)()
local FEATURE="GQ8_RC85_TWIN_BIOMES_TRAINING_BOND_REAL68_20261119"
local LOBBY="EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW"
local setupDone=setmetatable({}, {__mode="k"})
local boundLobby=setmetatable({}, {__mode="k"})

local function install(arena:Instance,mode:string,lobby:Instance)
 if arena.Parent~=lobby or setupDone[arena] or arena:FindFirstChild("EGGRUMBLE_TwinBiomes") then return end
 local canyon=arena:FindFirstChild("GQ8_RC85_WCS_Canyon")
 if not canyon or not canyon:IsA("Model") or not canyon.Parent then return end
 local west=canyon:FindFirstChild("WestBank")
 local east=canyon:FindFirstChild("EastBank")
 local safe=canyon:FindFirstChild("AlwaysOpenSafeRoute")
 if not (west and east and safe and west:IsA("BasePart") and east:IsA("BasePart")
    and safe:IsA("BasePart") and west.Anchored and east.Anchored
    and west.CanCollide and east.CanCollide and safe.CanCollide
    and west.Size.X>=49 and east.Size.X>=49 and west.Size.Z>=84 and east.Size.Z>=84) then return end
 local origin=west.CFrame*CFrame.new(50,2,0)
 if (east.Position-origin:PointToWorldSpace(Vector3.new(50,-2,0))).Magnitude>2 then return end
 -- Exact original WCS bank-local origin; no second canyon/Starfall/Meteor route.
 local anchor={CFrame=origin}
 local world=Instance.new("Model")
 world.Name="EGGRUMBLE_TwinBiomes"
 world:SetAttribute("FeatureId",FEATURE)
 world:SetAttribute("OriginalTwinSourceSHA256","c54cf6c8284e2f57a5b9fdb440317afcd363f4db83343c9b33e5783c488ef8f4")
 world:SetAttribute("OriginalTrainingSHA256","c59c6c3873f42f0c850ffc77beb20479ecb209250d2635294f89b61cfd00ac89")
 world:SetAttribute("OriginalBondSHA256","4c02c1933714ff0af09344b490f35f71db5d41534659e8b11ca4bed1d7235d09")
 world:SetAttribute("WorldKey",HttpService:GenerateGUID(false))
 world:SetAttribute("StudioOptInOnly",true)
 world:SetAttribute("NoNewDamageOrGameOwner",true)
 world:SetAttribute("Species",4)
 world:SetAttribute("CharacterInstances",8)
 world:SetAttribute("SessionOnlyPracticeAndBond",true)
 world:SetAttribute("SourceProfile","REAL68")
 world.Parent=arena
 setupDone[arena]=true
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
local practiceByPlayer = {}
local companionsByPlayer = {}
local sessionSpecies = {"AWARIN", "SANGORU", "RAIKO", "KUMONON"}
local removeConnection=Players.PlayerRemoving:Connect(function(p)
    seenByPlayer[p] = nil
    practiceByPlayer[p] = nil
    Bond.forget(p)
    local buddy=companionsByPlayer[p]
    if buddy and buddy.part.Parent then buddy.part:Destroy() end
    companionsByPlayer[p]=nil
end)

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

local function activate(effect, level)
    local now = os.clock()
    if now < (nextUse[effect] or 0) then
        return
    end
    local duration = Training.effectSeconds(level)
    activeUntil[effect] = now + duration
    nextUse[effect] = now + duration + REARM_SECONDS
    world:SetAttribute(effect .. "_Level", level)
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

local function awardPractice(player, info, npc, crest)
    -- Per-player practice, capped and cooldown-guarded server-side; no Remote
    -- and no DataStore. Discovery still works even when practice is cooling.
    local state = practiceByPlayer[player]
    if not state then
        state={}
        practiceByPlayer[player]=state
    end
    local previous=state[info.id]
    local updated, earned, promoted=Training.advance(previous,info.id,os.clock())
    if not earned then
        return updated and updated.level or 1
    end
    state[info.id]=updated
    player:SetAttribute("P0D_TwinPractice_"..info.id,updated.xp)
    player:SetAttribute("P0D_TwinLevel_"..info.id,updated.level)
    if updated.level==3 then
        player:SetAttribute("P0D_TwinEvolved_"..info.id,true)
    end
    -- A creature changes visually in THIS Studio server once a participant
    -- reaches stage 3; everyone's interactions stay equally available.
    local maxLevel=math.max(npc:GetAttribute("MaxTrainingLevel") or 1,updated.level)
    npc:SetAttribute("MaxTrainingLevel",maxLevel)
    if promoted and updated.level==3 and not crest:FindFirstChild("P0D_TwinEvolutionGlow") then
        npc:SetAttribute("EvolutionStage",3)
        crest.Color=gold
        crest.Size=Vector3.new(2.1,2.2,2.1)
        local evo=Instance.new("PointLight")
        evo.Name="P0D_TwinEvolutionGlow"
        evo.Color=gold
        evo.Brightness=0.8
        evo.Range=10
        evo.Parent=crest
    end
    local sign=crest:FindFirstChild("SpeciesLevelSign")
    local label=sign and sign:FindFirstChild("Readout")
    if not label then
        label=addSign(crest,"SpeciesLevelSign",
            info.name.." Lv"..tostring(maxLevel),5.4)
    end
    if label and label:IsA("TextLabel") then
        label.Text=info.name.." Lv"..tostring(maxLevel)
            ..(maxLevel==3 and " ✦進化" or "")
    end
    return updated.level
end

local function summonBoundCompanion(player, info, level)
    -- Server-only, one anchored noncolliding sphere per player. This is
    -- visual representation; the ONLY actual PvE damage authority is Game.
    if level < 2 or player.Parent ~= Players then return end
    if not RunService:IsStudio() or not world.Parent then return end
    local now=os.clock()
    local granted=Bond.select(player,info.id,level,now)
    if not granted then return end
    local prior=companionsByPlayer[player]
    if prior and prior.part.Parent and prior.species==info.id and prior.level==level then
        return -- no duplicate instance churn on repeated same-species prompt
    end
    if prior and prior.part.Parent then prior.part:Destroy() end
    local buddy=Instance.new("Part")
    buddy.Name="P0D_BOND_"..info.id
    buddy.Shape=Enum.PartType.Ball
    buddy.Size=Vector3.new(1.45,1.45,1.45)
    buddy.Anchored=true
    buddy.CanCollide=false
    buddy.CanTouch=false
    buddy.CanQuery=false
    buddy.Material=Enum.Material.Neon
    buddy.Color=info.tint
    buddy:SetAttribute("SpeciesId",info.id)
    buddy:SetAttribute("BoundUserId",player.UserId)
    buddy:SetAttribute("NoDamageAuthority",true)
    buddy.Parent=world
    addSign(buddy,"BoundCompanionLabel",info.name.." 相棒 Lv"..tostring(level),2.4)
    companionsByPlayer[player]={part=buddy,species=info.id,level=level}
    player:SetAttribute("P0D_TwinBondSpecies",info.id)
    player:SetAttribute("P0D_TwinBondLevel",level)
    local active=Bond.snapshot(player,now)
    if active then
        player:SetAttribute("EGGRUMBLE_TwinBondServerGranted",true)
        player:SetAttribute("EGGRUMBLE_TwinBondWorldKey",world:GetAttribute("WorldKey"))
        player:SetAttribute("EGGRUMBLE_TwinBondEndsAt",active.endsAt)
        player:SetAttribute("EGGRUMBLE_TwinBondLevel",active.level)
        player:SetAttribute("EGGRUMBLE_TwinBondMode",mode)
    end
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
        if player.Parent~=Players or player:GetAttribute("EGGRUMBLE_QueuedMode")~=mode
            or player:GetAttribute("EGGRUMBLE_Eliminated")==true
            or not root or not hum or hum.Health <= 0 or hum.Sit
            or char:GetAttribute("EGGRUMBLE_Downed")==true or root.Anchored then
            return
        end
        if (root.Position - body.Position).Magnitude > 12 then
            return
        end
        local ray=RaycastParams.new()
        ray.FilterType=Enum.RaycastFilterType.Exclude
        ray.FilterDescendantsInstances={char,npc}
        ray.RespectCanCollide=true
        local origin=root.Position+Vector3.new(0,1.2,0)
        if Workspace:Raycast(origin,body.Position-origin,ray)~=nil then return end
        local level=awardPractice(player,info,npc,crest)
        summonBoundCompanion(player,info,level)
        activate(info.effect,level)
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
    local realm=arena:FindFirstChild("EGGRUMBLE_REALM_BATTLE_CORE")
    local star=realm and realm:FindFirstChild("GQ8_RC86_StarfallPath")
    local gateActive = canyon:GetAttribute("MoguronGateOpen") == true
    local starActive = star and star:GetAttribute("PathOpen") == true
    return "モグロン " .. (gateActive and "開" or "閉")
        .. "\n星の橋 " .. (starActive and "開" or "閉")
end

task.spawn(function()
    -- One 1s loop for ALL eight characters. No Heartbeat per NPC and no
    -- unbounded clones, physics, damage or per-player persistent data.
    while world.Parent do
        local timeNow=os.clock()
        local bondEnabled=RunService:IsStudio() and arena.Parent==lobby
        for player,companion in pairs(companionsByPlayer) do
            local active=Bond.snapshot(player,timeNow)
            local char=player.Character
            local root=char and char:FindFirstChild("HumanoidRootPart")
            local hum=char and char:FindFirstChildOfClass("Humanoid")
            if not bondEnabled or player:GetAttribute("EGGRUMBLE_QueuedMode")~=mode
                or not active or not companion.part.Parent then
                if companion.part.Parent then companion.part:Destroy() end
                companionsByPlayer[player]=nil
                Bond.forget(player)
                if player.Parent==Players then
                    player:SetAttribute("P0D_TwinBondSpecies",nil)
                    player:SetAttribute("P0D_TwinBondLevel",nil)
                    if player:GetAttribute("EGGRUMBLE_TwinBondWorldKey")==world:GetAttribute("WorldKey") then
                        player:SetAttribute("EGGRUMBLE_TwinBondServerGranted",nil)
                        player:SetAttribute("EGGRUMBLE_TwinBondWorldKey",nil)
                        player:SetAttribute("EGGRUMBLE_TwinBondEndsAt",nil)
                        player:SetAttribute("EGGRUMBLE_TwinBondLevel",nil)
                        player:SetAttribute("EGGRUMBLE_TwinBondMode",nil)
                    end
                end
            elseif not root or not hum or hum.Health<=0 then
                -- Hide visuals during death/respawn but retain the original
                -- server-only 180s lease. On respawn this same part returns.
                companion.part.Transparency=1
            else
                companion.part.Transparency=0
                local behind=root.Position-root.CFrame.LookVector*2.4
                    +root.CFrame.RightVector*2.2
                companion.part.CFrame=CFrame.new(behind+Vector3.new(0,2.7+math.sin(timeNow*2)*0.25,0))
            end
        end
        for _,entry in ipairs(animate) do
            local bob=math.sin(timeNow*2+entry.phase)*0.28
            local turn=math.sin(timeNow*0.7+entry.phase)*0.12
            entry.model:PivotTo(entry.base*CFrame.new(0,bob,0)*CFrame.Angles(0,turn,0))
        end
        local veil = visible("TIDE_VEIL")
        local tidePower=world:GetAttribute("TIDE_VEIL_Level") or 1
        for _, p in ipairs(curtains) do
            p.Transparency = veil and (tidePower==3 and 0.14 or 0.32) or 0.93
        end
        local route = visible("ROUTE_LANTERN")
        local routePower=world:GetAttribute("ROUTE_LANTERN_Level") or 1
        for _, p in ipairs(routeLamps) do
            p.Transparency = route and (routePower==3 and 0 or 0.06) or 0.7
        end
        for _, txt in ipairs(routeTexts) do
            txt.Text = route and currentRouteText() or "サンゴの灯台\n橋を見渡そう"
        end
        local flash = visible("THUNDER_SIGNAL")
        for _, obj in ipairs(stormLamps) do
            obj.part.Transparency = flash and 0.05 or 0.8
            obj.light.Brightness = flash and ((world:GetAttribute("THUNDER_SIGNAL_Level") or 1)==3 and 2.2 or 1.8) or 0
        end
        local compass = visible("CLOUD_COMPASS")
        local compassPower=world:GetAttribute("CLOUD_COMPASS_Level") or 1
        for _, p in ipairs(watchLamps) do
            p.Transparency = compass and (compassPower==3 and 0.02 or 0.1) or 0.85
        end
        task.wait(0.25)
    end
end)

world:SetAttribute("Status", "V3_REAL68_SOURCE_ADOPTED_ENGINE_NOT_TESTED")
world:SetAttribute("NoRemoteStoreScoreXpDamage", true)

world.Destroying:Connect(function()
    removeConnection:Disconnect()
    setupDone[arena]=nil
    for player,companion in pairs(companionsByPlayer) do
        if companion.part and companion.part.Parent then companion.part:Destroy() end
        Bond.forget(player)
        if player.Parent==Players and player:GetAttribute("EGGRUMBLE_TwinBondWorldKey")==world:GetAttribute("WorldKey") then
            for _,a in ipairs({"EGGRUMBLE_TwinBondServerGranted","EGGRUMBLE_TwinBondWorldKey",
                "EGGRUMBLE_TwinBondEndsAt","EGGRUMBLE_TwinBondLevel","EGGRUMBLE_TwinBondMode"}) do
                player:SetAttribute(a,nil)
            end
        end
    end
end)
end

local function attachToLobby(lobby:Instance)
 if lobby.Name~=LOBBY or lobby.Parent~=Workspace or boundLobby[lobby] then return end
 boundLobby[lobby]=true
 local function watch(arena:Instance)
    local mode=if arena.Name=="TEAM_Arena" then "TEAM"
        elseif arena.Name=="BATTLE_ROYALE_Arena" then "BATTLE_ROYALE" else nil
    if not mode then return end
    task.spawn(function()
        while arena.Parent==lobby do
            if not setupDone[arena] and arena:FindFirstChild("GQ8_RC85_WCS_Canyon") then
                install(arena,mode,lobby)
            end
            task.wait(.5)
        end
    end)
 end
 for _,arena in ipairs(lobby:GetChildren()) do watch(arena) end
 lobby.ChildAdded:Connect(watch)
 lobby.Destroying:Connect(function()boundLobby[lobby]=nil end)
end
for _,instance in ipairs(Workspace:GetChildren()) do attachToLobby(instance) end
Workspace.ChildAdded:Connect(attachToLobby)