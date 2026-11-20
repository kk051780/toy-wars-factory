--!strict
-- P0D FB-015 / ART-BEAST: Gorogan-only cosmetic rig for private Studio QA.
-- #374 owns Musou neutral minion silhouettes; this file must not decorate them.
-- Damage / HP / egg / AI / drops / event ownership stay with original server Game.
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")
local TweenService = game:GetService("TweenService")
if not RunService:IsStudio() then return end

local MAX_BEASTS = 2
local MAX_DECOR_PARTS = 64
local activeBeasts = 0
local partCount = 0
local seen: {[Model]: boolean} = {}

local function color(r: number, g: number, b: number): Color3
    return Color3.fromRGB(r, g, b)
end

local BASALT = color(64, 73, 83)
local BASALT_LIGHT = color(103, 119, 128)
local RUNE = color(110, 236, 221)
local BRASS = color(191, 153, 91)
local EYES = color(255, 176, 112)

-- Every decorative part is locally welded to the pre-existing server-owned rig.
local function adorn(folder: Instance, root: BasePart, name: string,
    size: Vector3, offset: CFrame, tint: Color3,
    material: Enum.Material, shape: string): BasePart?
    if partCount >= MAX_DECOR_PARTS then return nil end
    local p: BasePart
    if shape == "WEDGE" then
        p = Instance.new("WedgePart")
    else
        local v = Instance.new("Part")
        if shape == "BALL" then v.Shape = Enum.PartType.Ball end
        p = v
    end
    partCount += 1
    p.Name = name
    p.Size = size
    p.CFrame = root.CFrame * offset
    p.Color = tint
    p.Material = material
    p.Anchored = false
    p.Massless = true
    p.CanCollide = false
    p.CanTouch = false
    p.CanQuery = false
    p.CastShadow = true
    p.Parent = folder
    local w = Instance.new("WeldConstraint")
    w.Part0 = root
    w.Part1 = p
    w.Parent = p
    return p
end

local function attachBeast(model: Model): boolean
    if model:FindFirstChild("FB015_BEAST_ART_V2") then return false end
    local torso = model:FindFirstChild("Torso")
    local head = model:FindFirstChild("Head")
    local humanoid = model:FindFirstChildOfClass("Humanoid")
    if not torso or not torso:IsA("BasePart")
        or not head or not head:IsA("BasePart")
        or not humanoid then return false end

    local partCountBefore = partCount
    local art = Instance.new("Folder")
    art.Name = "FB015_BEAST_ART_V2"
    art.Parent = model
    art:SetAttribute("VisualOnly", true)
    art:SetAttribute("OwnerFeedback", "FB-015")
    art:SetAttribute("GameAuthorityUnchanged", true)

    -- An asymmetrical 3D stone titan silhouette; no new collision/Hitbox parts.
    adorn(art, torso, "ObsidianChestPlate", Vector3.new(5.45,4.0,.64),
        CFrame.new(0,.5,-1.55), BASALT, Enum.Material.Slate, "BLOCK")
    adorn(art, torso, "HeartCarving", Vector3.new(1.8,2.15,.18),
        CFrame.new(0,.65,-1.92), RUNE, Enum.Material.Neon, "BALL")
    adorn(art, torso, "Gorget", Vector3.new(5.85,.72,4.05),
        CFrame.new(0,3.0,0), BASALT_LIGHT, Enum.Material.Slate, "BLOCK")
    for _, side in ipairs({-1,1}) do
        adorn(art, torso, "BoulderPauldron_"..side, Vector3.new(2.65,2.3,2.9),
            CFrame.new(side*3.42,1.8,.1)*CFrame.Angles(0,0,side*.17),
            BASALT, Enum.Material.Slate, "BALL")
        adorn(art, torso, "JaggedShoulderSpire_"..side,
            Vector3.new(1.15,2.85,1.3),
            CFrame.new(side*3.77,3.4,.12)*CFrame.Angles(0,0,side*.35),
            BASALT_LIGHT, Enum.Material.Slate, "WEDGE")
        adorn(art, head, "CrownHorn_"..side, Vector3.new(1.12,3.65,1.1),
            CFrame.new(side*1.5,2.55,.13)*CFrame.Angles(0,0,side*.28),
            BASALT, Enum.Material.Slate, "WEDGE")
        adorn(art, head, "RuneEye_"..side, Vector3.new(.66,.55,.22),
            CFrame.new(side*.69,.45,-1.52), EYES, Enum.Material.Neon, "BALL")
        adorn(art, torso, "FlankArmor_"..side, Vector3.new(.95,2.9,2.6),
            CFrame.new(side*2.9,-1.5,.15), BASALT_LIGHT,
            Enum.Material.Rock, "BLOCK")
    end
    adorn(art, head, "ForeheadMask", Vector3.new(3.35,.7,.5),
        CFrame.new(0,.85,-1.4), BRASS, Enum.Material.Metal, "BLOCK")
    adorn(art, head, "JawMask", Vector3.new(2.5,.55,.5),
        CFrame.new(0,-.88,-1.38), BASALT, Enum.Material.Slate, "BLOCK")

    -- Spine and back silhouette, visible in pursuit/retreat over third-person camera.
    for i = 1, 5 do
        adorn(art, torso, "ObsidianBackSpike_"..i,
            Vector3.new(1.05,1.15+(6-i)*.48,.95),
            CFrame.new(0,2.55-(i-1)*1.06,1.86)*CFrame.Angles(.5,0,0),
            BASALT_LIGHT, Enum.Material.Slate, "WEDGE")
    end
    adorn(art, torso, "ShoulderSigil", Vector3.new(1.15,1.15,.2),
        CFrame.new(1.58,1.3,-1.94), BRASS, Enum.Material.Metal, "BALL")

    -- Lightweight glow pulsing in the same rig; no server ability or damage changes.
    local glow = Instance.new("PointLight")
    glow.Name = "FB015RunicHeartGlow"
    glow.Brightness = .7
    glow.Range = 12
    glow.Color = RUNE
    glow.Shadows = false
    glow.Parent = torso
    local pulse = TweenService:Create(glow,
        TweenInfo.new(1.4, Enum.EasingStyle.Sine,
            Enum.EasingDirection.InOut, -1, true),
        {Brightness = 1.3, Range = 15})
    pulse:Play()

    local burst = Instance.new("ParticleEmitter")
    burst.Name = "FB015GoroganDamageSparks"
    burst.Enabled = false
    burst.Rate = 0
    burst.Lifetime = NumberRange.new(.1,.24)
    burst.Speed = NumberRange.new(3.5,7.0)
    burst.Drag = 11
    burst.SpreadAngle = Vector2.new(70,70)
    burst.LightEmission = .35
    burst.Color = ColorSequence.new(EYES,RUNE)
    burst.Size = NumberSequence.new({
        NumberSequenceKeypoint.new(0,.43),
        NumberSequenceKeypoint.new(1,0),
    })
    burst.Parent = torso

    -- Existing server-owned Humanoid health is observed, NEVER modified.
    local oldHealth = humanoid.Health
    local damaged = humanoid.HealthChanged:Connect(function(value)
        if value < oldHealth then
            burst:Emit(if value <= 0 then 22 else 8)
        end
        oldHealth = value
    end)
    local ownParts = partCount - partCountBefore
    model.Destroying:Connect(function()
        damaged:Disconnect()
        pulse:Cancel()
        -- Release only this beast's visual budget, not the other active beast.
        partCount = math.max(0, partCount - ownParts)
        activeBeasts = math.max(0, activeBeasts - 1)
        seen[model] = nil
    end)

    art:SetAttribute("DecorPartCount", partCount - partCountBefore)
    art:SetAttribute("VisualQA", "NOT_TESTED")
    model:SetAttribute("FB015_ArtSilhouette", "RUNESTONE_TITAN")
    return true
end

-- Models replicate to clients asynchronously. The first DescendantAdded
-- for the Model can arrive BEFORE Head/Torso/Humanoid, even though the
-- server completed construction before parenting it. A one-shot attach
-- silently leaves the boss looking like the old gray block for this spawn.
local pending: {[Model]: boolean} = {}
local MAX_REPLICATION_WAIT_STEPS = 40
local REPLICATION_WAIT_SECONDS = .15

local function prepare(instance: Instance)
    if not instance:IsA("Model") or instance.Name ~= "Gorogan_ServerRig" then
        return
    end
    local model = instance :: Model
    if seen[model] or pending[model] then return end
    pending[model] = true
    task.spawn(function()
        local done = false
        for _ = 1, MAX_REPLICATION_WAIT_STEPS do
            if not model.Parent or seen[model] then break end
            if activeBeasts < MAX_BEASTS then
                local ok, result = pcall(attachBeast, model)
                if ok and result == true then
                    seen[model] = true
                    activeBeasts += 1
                    model:SetAttribute("FB015_BeastArtClientAttached", true)
                    done = true
                    break
                elseif not ok then
                    warn("FB015_GOROGAN_ART_ATTACH_FAIL_CLOSED", result)
                    break
                end
            end
            task.wait(REPLICATION_WAIT_SECONDS)
        end
        pending[model] = nil
        if not done and not seen[model] and model.Parent then
            model:SetAttribute("FB015_BeastArtClientPendingExpired", true)
            warn("FB015_GOROGAN_ART_REPLICATION_WAIT_EXPIRED")
        end
    end)
end

for _,item in ipairs(Workspace:GetDescendants()) do
    prepare(item)
end
local added = Workspace.DescendantAdded:Connect(function(obj)
    if obj:IsA("Model") and obj.Name == "Gorogan_ServerRig" then
        prepare(obj)
    end
end)
script.Destroying:Connect(function()
    added:Disconnect()
end)
print("FB015_GOROGAN_BEAST_ART_SOURCE_ONLY_NOT_STUDIO_VERIFIED")
