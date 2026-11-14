--!strict
-- FB-015 / ART-MINION + ART-BEAST, owner #372.
-- Studio-only visual-first candidate, never a damage/HP/egg/Remote owner.
-- Builds distinct silhouettes and hit spark accents onto existing characters,
-- not new creatures. All parts noncolliding, unqueryable and client-local.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end
local Workspace = game:GetService("Workspace")
local MAX_MODELS = 28
local MAX_PARTS = 280
local prepared = 0
local parts = 0
local seen: {[Model]: boolean} = {}

local function color(r: number,g: number,b: number): Color3
    return Color3.fromRGB(r,g,b)
end

local function addPart(parent: Instance, core: BasePart, name: string,
    size: Vector3, offset: CFrame, tint: Color3,
    material: Enum.Material, style: string): BasePart?
    if parts >= MAX_PARTS then return nil end
    local p: BasePart
    if style == "WEDGE" then
        p = Instance.new("WedgePart")
    else
        local b = Instance.new("Part")
        if style == "BALL" then b.Shape = Enum.PartType.Ball end
        if style == "CYLINDER" then b.Shape = Enum.PartType.Cylinder end
        p = b
    end
    parts += 1
    p.Name = name
    p.Size = size
    p.Color = tint
    p.Material = material
    p.CFrame = core.CFrame * offset
    p.Anchored = false
    p.Massless = true
    p.CanCollide = false
    p.CanTouch = false
    p.CanQuery = false
    p.CastShadow = false
    p.Parent = parent
    local weld = Instance.new("WeldConstraint")
    weld.Part0 = core
    weld.Part1 = p
    weld.Parent = p
    return p
end

local function labelLimit(model: Model)
    for _,child in ipairs(model:GetDescendants()) do
        if child:IsA("BillboardGui") then
            -- Keep elite danger readable nearby, never draw 100px text over
            -- the world from the far side of the battlefield.
            child.MaxDistance = if child.Name == "RealDamagePopup" then 44 else 30
            child.AlwaysOnTop = false
            if child.Name == "CombatCue" then
                child.Size = UDim2.fromOffset(74, 25)
            end
        end
    end
end

local function addImpactSpark(model: Model, core: BasePart, elite: boolean)
    local emitter = Instance.new("ParticleEmitter")
    emitter.Name = "FB015_ImpactSparks"
    emitter.Enabled = false
    emitter.Rate = 0
    emitter.Lifetime = NumberRange.new(.12, .24)
    emitter.Speed = NumberRange.new(4, 9)
    emitter.SpreadAngle = Vector2.new(65,65)
    emitter.Drag = 10
    emitter.LightEmission = .35
    emitter.Size = NumberSequence.new({
        NumberSequenceKeypoint.new(0,.35),
        NumberSequenceKeypoint.new(1,0),
    })
    emitter.Color = ColorSequence.new(if elite then color(255,172,84) else color(255,234,165))
    emitter.Parent = core
    local previous = core.Color
    core:GetPropertyChangedSignal("Color"):Connect(function()
        local now = core.Color
        -- The existing single authoritative Horde already flashes golden
        -- or red when taking damage / warning; we only mirror visual signals.
        if (now.R > .8 and now.G > .65 and previous ~= now) then
            emitter:Emit(if elite then 10 else 5)
        end
        previous = now
    end)
    model:SetAttribute("FB015_SparkVisualOnly", true)
end

local function buildMinion(model: Model)
    local core = model:FindFirstChild("Core")
    local head = model:FindFirstChild("Head")
    if not core or not core:IsA("BasePart")
        or not head or not head:IsA("BasePart") then return end
    local art = Instance.new("Folder")
    art.Name = "FB015_CHARACTER_ART_V1"
    art.Parent = model
    local num = tonumber(model.Name:match("(%d+)$")) or 1
    local kind = (num-1)%3
    -- Three DIFFERENT silhouettes: scout (cape/crest), guardian (shield/armor),
    -- storm-caster (double horns/staff); not three color swaps of one cuboid.
    local primary = if kind == 0 then color(32,120,123)
        elseif kind == 1 then color(92,106,148)
        else color(127,79,144)
    local accent = if kind == 0 then color(249,191,92)
        elseif kind == 1 then color(173,210,237)
        else color(227,157,245)
    local armor = color(63,69,89)
    addPart(art,head,"HelmetBand",Vector3.new(2.55,.46,2.40),
        CFrame.new(0,.38,0),armor,Enum.Material.Metal,"BLOCK")
    addPart(art,core,"ChestPlate",Vector3.new(2.75,2,.45),
        CFrame.new(0,.30,-1.11),primary,Enum.Material.Metal,"BLOCK")
    addPart(art,core,"ChestCrest",Vector3.new(.65,.80,.16),
        CFrame.new(0,.55,-1.40),accent,Enum.Material.Neon,"BALL")
    for _,side in ipairs({-1,1}) do
        addPart(art,core,"Shoulder_"..side,Vector3.new(1.35,.75,1.8),
            CFrame.new(side*1.68,1.05,0)*CFrame.Angles(0,0,side*-.25),
            armor,Enum.Material.Metal,"BALL")
        addPart(art,core,"Bracer_"..side,Vector3.new(.6,1.0,.85),
            CFrame.new(side*1.62,-.45,-.2),primary,Enum.Material.Metal,"BLOCK")
    end
    if kind == 0 then
        addPart(art,head,"ScoutCrest",Vector3.new(.55,1.45,1.8),
            CFrame.new(0,1.20,.15)*CFrame.Angles(.3,0,0),
            accent,Enum.Material.Fabric,"WEDGE")
        addPart(art,core,"ScoutCape",Vector3.new(2.3,3.45,.35),
            CFrame.new(0,-.10,1.12)*CFrame.Angles(-.14,0,0),
            primary,Enum.Material.Fabric,"WEDGE")
    elseif kind == 1 then
        addPart(art,core,"GuardianShield",Vector3.new(2.25,3.1,.42),
            CFrame.new(-2.24,-.2,-.86)*CFrame.Angles(0,.15,-.12),
            primary,Enum.Material.Metal,"BLOCK")
        addPart(art,core,"ShieldSigil",Vector3.new(.8,1,.16),
            CFrame.new(-2.24,-.05,-1.12),
            accent,Enum.Material.Metal,"BALL")
    else
        for _,side in ipairs({-1,1}) do
            addPart(art,head,"StormHorn_"..side,Vector3.new(.6,1.85,.7),
                CFrame.new(side*.84,1.46,.1)*CFrame.Angles(0,0,side*.25),
                accent,Enum.Material.Metal,"WEDGE")
        end
        addPart(art,core,"StormMantle",Vector3.new(2.9,.55,1.8),
            CFrame.new(0,1.43,0),primary,Enum.Material.Fabric,"BLOCK")
    end
    labelLimit(model)
    addImpactSpark(model,core,false)
    model:SetAttribute("FB015_ArtSilhouette",if kind==0 then "SCOUT"
        elseif kind==1 then "GUARDIAN" else "STORMCASTER")
end

local function buildElite(model: Model)
    local core = model:FindFirstChild("Core")
    local head = model:FindFirstChild("Head")
    if not core or not core:IsA("BasePart")
        or not head or not head:IsA("BasePart") then return end
    local art=Instance.new("Folder")
    art.Name="FB015_CHARACTER_ART_V1"
    art.Parent=model
    local obsidian=color(65,57,83)
    local gold=color(225,172,85)
    addPart(art,core,"EliteThorax",Vector3.new(5.2,3.4,3.65),
        CFrame.new(0,.25,0),obsidian,Enum.Material.Slate,"BALL")
    addPart(art,core,"AncientRune",Vector3.new(1.55,1.7,.22),
        CFrame.new(0,.60,-1.98),gold,Enum.Material.Neon,"BALL")
    for _,side in ipairs({-1,1}) do
        addPart(art,head,"GuardianHorn_"..side,Vector3.new(.9,2.9,1.05),
            CFrame.new(side*1.42,2.0,.25)*CFrame.Angles(0,0,side*.35),
            gold,Enum.Material.Metal,"WEDGE")
        addPart(art,core,"ArmorSpaulder_"..side,Vector3.new(2.5,1.9,2.55),
            CFrame.new(side*3.05,1.15,0),obsidian,Enum.Material.Slate,"BALL")
    end
    labelLimit(model)
    addImpactSpark(model,core,true)
    model:SetAttribute("FB015_ArtSilhouette","CROWNED_ELITE")
end

local function buildGorogan(model: Model)
    local head=model:FindFirstChild("Head")
    local torso=model:FindFirstChild("Torso")
    if not head or not head:IsA("BasePart")
        or not torso or not torso:IsA("BasePart") then return end
    local art=Instance.new("Folder")
    art.Name="FB015_BEAST_ART_V1"
    art.Parent=model
    local stone=color(74,84,94)
    local luminous=color(105,221,215)
    for _,side in ipairs({-1,1}) do
        addPart(art,head,"StoneCrownHorn_"..side,Vector3.new(1.1,3.4,1.3),
            CFrame.new(side*1.35,2.45,.2)*CFrame.Angles(0,0,side*.32),
            stone,Enum.Material.Slate,"WEDGE")
        addPart(art,torso,"TectonicShoulder_"..side,Vector3.new(2.8,2.35,3.3),
            CFrame.new(side*3.65,1.95,.12)*CFrame.Angles(0,0,side*.13),
            stone,Enum.Material.Slate,"BALL")
    end
    addPart(art,torso,"GoroganCoreRune",Vector3.new(1.85,2.2,.24),
        CFrame.new(0,1.25,-1.7),luminous,Enum.Material.Neon,"BALL")
    addPart(art,head,"HornCrownRidge",Vector3.new(2.2,.8,2.7),
        CFrame.new(0,1.1,.2),stone,Enum.Material.Slate,"BLOCK")
    labelLimit(model)
    model:SetAttribute("FB015_ArtSilhouette","TITAN_STONE_BEAST")
end

local function prepare(instance: Instance)
    if not instance:IsA("Model") then return end
    local model=instance :: Model
    if seen[model] or prepared >= MAX_MODELS then return end
    local name=model.Name
    local kind = if name:match("^MUSOU_MINION_%d+$") then "MINION"
        elseif name=="MUSOU_ELITE_TELEGRAPH" then "ELITE"
        elseif name=="Gorogan_ServerRig" then "GOROGAN"
        else nil
    if kind == nil then return end
    seen[model] = true
    local ok,err=pcall(function()
        if kind=="MINION" then buildMinion(model)
        elseif kind=="ELITE" then buildElite(model)
        else buildGorogan(model) end
    end)
    if ok then prepared += 1 else warn("FB015_ART_SAFE_SKIP",err) end
end

for _,obj in ipairs(Workspace:GetDescendants()) do
    prepare(obj)
end
Workspace.DescendantAdded:Connect(function(obj)
    if obj:IsA("Model") then
        task.defer(prepare,obj)
    end
end)
print("P0D_FB015_CHARACTER_ART_STUDIO_CANDIDATE_NOT_OWNER_ACCEPTED")
