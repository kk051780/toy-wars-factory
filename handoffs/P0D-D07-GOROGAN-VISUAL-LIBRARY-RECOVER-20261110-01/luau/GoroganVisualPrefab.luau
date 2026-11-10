--!strict
-- TRAP RAIDERS D07: entirely LOCAL 3D cosmetic. No Humanoid, Touch, Raycast, Damage, Sound asset or AI.
-- Server authority and gameplay remain exclusively with existing RoundCoordinator / ChaosEventCore.
local Prefab = {}
local ROCK = Color3.fromRGB(102, 112, 109)
local DARK = Color3.fromRGB(61, 70, 69)
local MOSS = Color3.fromRGB(75, 132, 82)
local GOLD = Color3.fromRGB(248, 198, 64)
local GLOW = Color3.fromRGB(255, 238, 125)
local DANGER = Color3.fromRGB(255, 75, 67)

local function block(parent, name, size, offset, color, material, shape)
    local part = Instance.new("Part")
    part.Name = name
    part.Size = size
    part.Anchored = true
    part.CanCollide = false
    part.CanTouch = false
    part.CanQuery = false
    part.CastShadow = false
    part.Locked = true
    part.Material = material or Enum.Material.Slate
    part.Color = color
    part.Shape = shape or Enum.PartType.Block
    part.CFrame = CFrame.new(offset)
    part.Parent = parent
    return part
end

function Prefab.create(parent: Instance, rootPosition: Vector3, lowDetail: boolean)
    -- Max 29 body parts in low detail, 37 with 8 stomp-ring segments.
    -- All assets use stock Roblox primitives/colors: no third-party intellectual property.
    assert(typeof(rootPosition) == "Vector3")
    local model = Instance.new("Model")
    model.Name = "Gorogan_ClientVisualOnly"
    local root = block(model, "VisualRoot", Vector3.new(.2,.2,.2), Vector3.zero, DARK)
    root.Transparency = 1
    model.PrimaryPart = root
    local count = 1
    local function add(name, size, offset, color, material, shape)
        count += 1
        return block(model, name, size, offset, color, material, shape)
    end

    -- Main body: bulky uneven rock silhouette, about 20 studs high.
    add("Torso", Vector3.new(7,7,4.5), Vector3.new(0,11.2,0), ROCK)
    add("BellyRidge", Vector3.new(5.8,2,5.1), Vector3.new(0,9.7,-.3), DARK)
    add("Head", Vector3.new(4.3,3.8,3.9), Vector3.new(0,16.8,-.4), ROCK)
    add("BrowLeft", Vector3.new(2.4,.8,1.7), Vector3.new(-1.3,17.7,-2), DARK)
    add("BrowRight", Vector3.new(2.4,.8,1.7), Vector3.new(1.3,17.7,-2), DARK)
    add("EyeLeft", Vector3.new(.46,.48,.23), Vector3.new(-.95,16.9,-2.48), GLOW, Enum.Material.Neon)
    add("EyeRight", Vector3.new(.46,.48,.23), Vector3.new(.95,16.9,-2.48), GLOW, Enum.Material.Neon)
    add("LeftShoulder", Vector3.new(3.5,3.5,4), Vector3.new(-4.2,14.2,0), ROCK)
    add("RightShoulder", Vector3.new(4.3,4.1,4.5), Vector3.new(4.4,14,0), ROCK)
    add("LeftArm", Vector3.new(2.5,5.7,3.0), Vector3.new(-5,10.4,0), DARK)
    add("RightArm", Vector3.new(3.2,5.4,3.2), Vector3.new(5.2,10.2,0), DARK)
    add("LeftFist", Vector3.new(3.7,3,3.7), Vector3.new(-5.0,6.9,-.4), ROCK)
    add("RightFist", Vector3.new(4.1,3.7,3.9), Vector3.new(5.4,6.9,-.4), ROCK)
    add("LeftThigh", Vector3.new(3.1,6.3,3.2), Vector3.new(-2.0,5.1,0), ROCK)
    add("RightThigh", Vector3.new(3.4,6.4,3.3), Vector3.new(2.1,5.1,0), ROCK)
    add("LeftFoot", Vector3.new(3.6,2,5), Vector3.new(-2,1.1,-.9), DARK)
    add("RightFoot", Vector3.new(3.7,2,5), Vector3.new(2.1,1.1,-.9), DARK)
    -- Chest weak-point is VISUAL only: never grants or changes damage without server gameplay review.
    local core = add("GlowingChestRune", Vector3.new(1.8,1.8,.33), Vector3.new(0,12.1,-2.43), GOLD, Enum.Material.Neon)
    add("CoreStripe", Vector3.new(.42,2.2,.35), Vector3.new(0,12.1,-2.67), GLOW, Enum.Material.Neon)
    add("MossCrown", Vector3.new(4.4,.85,3.7), Vector3.new(-.1,18.9,.1), MOSS, Enum.Material.Grass)
    add("LeftMoss", Vector3.new(2.9,.65,3.0), Vector3.new(-4.4,16.1,.1), MOSS, Enum.Material.Grass)
    add("RightMoss", Vector3.new(3.1,.65,3.7), Vector3.new(4.5,16.2,.1), MOSS, Enum.Material.Grass)
    if not lowDetail then
        add("BackRune1", Vector3.new(.5,3,.25), Vector3.new(-1,11.8,2.4), GOLD, Enum.Material.Neon)
        add("BackRune2", Vector3.new(.5,3,.25), Vector3.new(1,11.8,2.4), GOLD, Enum.Material.Neon)
        add("HornLeft", Vector3.new(1,2,1.1), Vector3.new(-1.7,20,0), ROCK)
        add("HornRight", Vector3.new(1,1.6,1.1), Vector3.new(1.7,19.8,0), ROCK)
    end
    local circle = {}
    local segments = if lowDetail then 4 else 8
    for index = 1, segments do
        local angle = (index-1) * (2*math.pi/segments)
        local x,z = math.sin(angle)*7, math.cos(angle)*7
        local chord = 2*7*math.sin(math.pi/segments)
        local segment = add("StompWarning"..index, Vector3.new(chord*.96,.2,.42), Vector3.new(x,.2,z), DANGER, Enum.Material.Neon)
        segment.CFrame = CFrame.new(x,.2,z) * CFrame.Angles(0,angle,0)
        segment.Transparency = 1
        table.insert(circle, segment)
    end
    model.Parent = parent
    model:PivotTo(CFrame.new(rootPosition))
    return {model=model, core=core, circle=circle, partCount=count, rootPosition=rootPosition, lowDetail=lowDetail}
end

function Prefab.render(handle, phase: string, now: number, reducedMotion: boolean)
    if not handle or not handle.model or not handle.model.Parent then return end
    local warning = phase == "STOMP" or phase == "WARNING"
    for _,segment in ipairs(handle.circle) do
        segment.Transparency = if warning then .28 else 1
    end
    handle.core.Color = if warning then DANGER else GOLD
    -- Throttle caller to 10Hz or lower. No forced camera shake or flashing screen.
    local bob = if reducedMotion then 0 else math.sin(now*2.2) * .13
    handle.model:PivotTo(CFrame.new(handle.rootPosition + Vector3.new(0,bob,0)))
end

function Prefab.destroy(handle)
    if handle and handle.model then
        handle.model:Destroy()
        handle.model = nil
    end
end
return Prefab
