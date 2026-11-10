-- Client-only 3D decorative electric wyrm. No Humanoid, AI, collisions, damage or replicated boss.
local M = {}
local function newPart(model, name, size, color, material, shape)
    local p = Instance.new("Part")
    p.Name = name
    p.Anchored = true
    p.CanCollide = false
    p.CanTouch = false
    p.CanQuery = false
    p.CastShadow = false
    p.Size = size
    p.Material = material
    p.Color = color
    if shape then p.Shape = shape end
    p.Parent = model
    return p
end
local CYAN = Color3.fromRGB(30, 215, 245)
local DEEP = Color3.fromRGB(32, 58, 134)
local ICE = Color3.fromRGB(180, 242, 255)
local YELLOW = Color3.fromRGB(255, 241, 80)
function M.build(parent, lowDetail)
    local m = Instance.new("Model")
    m.Name = "LIGARDO_CLIENT_VISUAL_ONLY"
    local segments = lowDetail and 4 or 6
    local arcs = lowDetail and 2 or 4
    local parts = {}
    for i = 1, segments do
        parts[#parts + 1] = newPart(m, "WyrmBody_" .. i,
            Vector3.new(3.8 - i * 0.32, 2.1 - i * 0.13, 2.1 - i * 0.13),
            i % 2 == 0 and CYAN or DEEP, Enum.Material.SmoothPlastic, Enum.PartType.Ball)
    end
    local head = newPart(m, "ThunderCrown", Vector3.new(3.9, 2.7, 3.2), ICE, Enum.Material.Neon, Enum.PartType.Ball)
    local jaw = newPart(m, "ThunderJaw", Vector3.new(3.1, 1.2, 2.6), DEEP, Enum.Material.SmoothPlastic)
    local horns = {}
    for i = 1, 2 do
        horns[i] = newPart(m, "StormHorn_" .. i, Vector3.new(0.7, 2.8, 0.7), YELLOW, Enum.Material.Neon)
    end
    local fins = {}
    for i = 1, 4 do
        fins[i] = newPart(m, "StormFin_" .. i, Vector3.new(1.25, 1.8, 0.35), CYAN, Enum.Material.Neon)
    end
    local lightning = {}
    for i = 1, arcs do
        local p = newPart(m, "WARNING_ONLY_Lightning_" .. i, Vector3.new(0.23, 5, 0.23), YELLOW, Enum.Material.Neon)
        p.Transparency = 1
        lightning[i] = p
    end
    m.Parent = parent
    -- Max 18 parts full detail; 14 on low detail, no physics objects.
    return {model = m, body = parts, head = head, jaw = jaw, horns = horns,
        fins = fins, lightning = lightning, lowDetail = lowDetail == true}
end
function M.update(view, center, phase, elapsed, reducedMotion)
    if not view or not view.model or not view.model.Parent then return end
    if typeof(center) ~= "Vector3" then return end
    if math.abs(center.X) > 4096 or math.abs(center.Y) > 4096 or math.abs(center.Z) > 4096 then return end
    local bob = reducedMotion and 0 or math.sin(elapsed * 1.5) * 0.45
    local root = CFrame.new(center + Vector3.new(0, 5 + bob, 0))
    for i, p in ipairs(view.body) do
        local bend = reducedMotion and 0 or math.sin(elapsed * 1.3 - i * 0.5) * 0.45
        p.CFrame = root * CFrame.new(0, bend, i * 2.4)
    end
    view.head.CFrame = root * CFrame.new(0, 0.1, -2.4)
    view.jaw.CFrame = root * CFrame.new(0, -1.0, -2.8)
    for i, horn in ipairs(view.horns) do
        local sign = i == 1 and -1 or 1
        horn.CFrame = root * CFrame.new(sign * 1.35, 2.0, -3.1) * CFrame.Angles(0, 0, sign * 0.3)
    end
    for i, fin in ipairs(view.fins) do
        local sign = i % 2 == 1 and -1 or 1
        local offset = math.ceil(i / 2)
        fin.CFrame = root * CFrame.new(sign * 1.5, 1.1, offset * 2.5) * CFrame.Angles(0, 0, sign * 0.65)
    end
    for i, spark in ipairs(view.lightning) do
        local warning = phase == "TELEGRAPH" or phase == "ACTIVE"
        spark.Transparency = warning and (reducedMotion and 0.7 or 0.25) or 1
        -- Telegraph in place; this decorative effect has no corresponding client damage area.
        spark.CFrame = root * CFrame.new((i - 2.5) * 1.5, -2, -1.2) * CFrame.Angles(0.25 * i, 0, 0)
    end
end
function M.destroy(view)
    if view and view.model then view.model:Destroy() end
end
return M
