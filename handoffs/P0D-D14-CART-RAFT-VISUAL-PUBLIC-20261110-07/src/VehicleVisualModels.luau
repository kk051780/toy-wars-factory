-- Local visual props only: only anchored cosmetics, no seat or motion primitives.
local M = {}

local BLUE = Color3.fromRGB(75, 158, 240)
local RED = Color3.fromRGB(224, 91, 91)
local WOOD = Color3.fromRGB(124, 79, 47)
local METAL = Color3.fromRGB(86, 91, 103)
local ROPE = Color3.fromRGB(184, 153, 93)

local function part(model, name, dimensions, at, color, material, shape)
    local p = Instance.new("Part")
    p.Name = name
    p.Size = dimensions
    p.Color = color
    p.Material = material or Enum.Material.SmoothPlastic
    p.Shape = shape or Enum.PartType.Block
    p.Anchored = true
    p.CanCollide = false
    p.CanTouch = false
    p.CanQuery = false
    p.CastShadow = false
    p.Massless = true
    p.CFrame = CFrame.new(at)
    p.Parent = model
    return p
end

local function riderMarker(model, anchor, typeName)
    local gui = Instance.new("BillboardGui")
    gui.Name = "OccupancyBadge"
    gui.Size = UDim2.fromOffset(86, 24)
    gui.StudsOffsetWorldSpace = Vector3.new(0, 2.8, 0)
    gui.MaxDistance = 90
    gui.AlwaysOnTop = false
    gui.Adornee = anchor
    local text = Instance.new("TextLabel")
    text.Name = "OccupancyText"
    text.Size = UDim2.fromScale(1, 1)
    text.BackgroundTransparency = 0.25
    text.BackgroundColor3 = Color3.fromRGB(25, 33, 43)
    text.TextColor3 = Color3.fromRGB(255, 255, 255)
    text.TextScaled = true
    text.Font = Enum.Font.GothamBold
    text.Text = typeName .. "  0/2"
    text.Parent = gui
    gui.Parent = anchor
    return text
end

function M.create(vehicleId, vehicleType, team, lowDetail, root)
    assert(vehicleType == "CART" or vehicleType == "RAFT")
    assert(team == "BLUE" or team == "RED")
    local model = Instance.new("Model")
    model.Name = "VehicleFX_" .. vehicleId
    local accent = team == "BLUE" and BLUE or RED
    local center = part(model, "HullVisual", Vector3.new(5.5, 0.55, 8), Vector3.new(0, 1, 0), WOOD, Enum.Material.Wood)
    model.PrimaryPart = center
    if vehicleType == "CART" then
        part(model, "CargoBed", Vector3.new(4.5, 0.38, 5.7), Vector3.new(0, 1.5, 0), accent)
        part(model, "FrontGuard", Vector3.new(5.0, 0.9, 0.32), Vector3.new(0, 1.95, -2.85), WOOD, Enum.Material.Wood)
        part(model, "RearGuard", Vector3.new(5.0, 0.9, 0.32), Vector3.new(0, 1.95, 2.85), WOOD, Enum.Material.Wood)
        for side = -1, 1, 2 do
            for front = -1, 1, 2 do
                local wheel = part(model, "WheelVisual", Vector3.new(1.45, 1.45, 0.5),
                    Vector3.new(side * 2.8, 0.8, front * 2.5), METAL, Enum.Material.Metal, Enum.PartType.Cylinder)
                wheel.CFrame = wheel.CFrame * CFrame.Angles(0, 0, math.pi * 0.5)
            end
        end
        if not lowDetail then
            part(model, "Lantern", Vector3.new(0.6, 0.8, 0.6), Vector3.new(-1.9, 2.3, -2.6), accent, Enum.Material.Neon)
            part(model, "Lantern", Vector3.new(0.6, 0.8, 0.6), Vector3.new(1.9, 2.3, -2.6), accent, Enum.Material.Neon)
            part(model, "CenterBrace", Vector3.new(0.35, 0.3, 5.4), Vector3.new(0, 1.8, 0), METAL, Enum.Material.Metal)
        end
    else
        for side = -1, 1, 2 do
            part(model, "FloatVisual", Vector3.new(1.2, 0.9, 7.6), Vector3.new(side * 2.1, 0.6, 0), WOOD, Enum.Material.Wood)
            part(model, "RailVisual", Vector3.new(0.26, 0.7, 7.2), Vector3.new(side * 2.65, 1.65, 0), ROPE)
        end
        part(model, "MastVisual", Vector3.new(0.3, 4.5, 0.3), Vector3.new(0, 3.0, -1.4), METAL, Enum.Material.Metal)
        part(model, "FlagVisual", Vector3.new(1.9, 1.1, 0.14), Vector3.new(0.9, 4.3, -1.4), accent)
        if not lowDetail then
            for n = -1, 1, 2 do
                part(model, "Crossbeam", Vector3.new(5.0, 0.28, 0.42), Vector3.new(0, 1.55, n * 2.2), ROPE)
            end
        end
    end
    local text = riderMarker(model, center, vehicleType)
    model.Parent = root
    return { model = model, badge = text }
end

function M.update(view, presentation)
    if not view or not view.model or not view.model.Parent then return end
    local p = presentation
    view.model:PivotTo(CFrame.new(p.x, p.y, p.z) * CFrame.Angles(0, math.rad(p.yawDeg), 0))
    local occupied = (p.driverOccupied and 1 or 0) + (p.passengerOccupied and 1 or 0)
    view.badge.Text = p.vehicleType .. "  " .. tostring(occupied) .. "/2"
end

function M.destroy(view)
    if view and view.model then view.model:Destroy() end
end
return M
