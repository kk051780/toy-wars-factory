-- D18 lightweight ViewportFrame stand-ins. Not a canonical full 3D model import.
-- Works entirely in a WorldModel owned by the caller's ViewportFrame.
local Preview = {}
local SHAPE = { Ball = Enum.PartType.Ball, Cylinder = Enum.PartType.Cylinder, Block = Enum.PartType.Block }

function Preview.render(viewport, entry, yawDegrees)
    assert(viewport and viewport:IsA("ViewportFrame"), "viewport must be a ViewportFrame")
    assert(entry and type(entry.parts) == "table", "known catalog entry required")
    viewport:ClearAllChildren()
    viewport.BackgroundColor3 = Color3.fromRGB(19, 24, 43)
    viewport.Ambient = Color3.fromRGB(190, 195, 212)
    viewport.LightColor = Color3.fromRGB(255, 248, 218)
    viewport.LightDirection = Vector3.new(-1, -1, -1)
    local world = Instance.new("WorldModel")
    world.Name = "LocalPreviewOnly"
    world.Parent = viewport
    local model = Instance.new("Model")
    model.Name = entry.id
    model.Parent = world
    assert(#entry.parts <= 18, "preview part budget exceeded")
    for i, def in ipairs(entry.parts) do
        local part = Instance.new("Part")
        part.Name = def.name
        part.Size = Vector3.new(def.size[1], def.size[2], def.size[3])
        part.CFrame = CFrame.new(def.pos[1], def.pos[2], def.pos[3]) *
            CFrame.Angles(math.rad(def.rot[1]), math.rad(def.rot[2]), math.rad(def.rot[3]))
        part.Shape = SHAPE[def.shape] or Enum.PartType.Block
        part.Material = Enum.Material.SmoothPlastic
        part.Color = Color3.fromRGB(def.color[1], def.color[2], def.color[3])
        part.Anchored = true
        part.CanCollide = false
        part.CanTouch = false
        part.CanQuery = false
        part.CastShadow = false
        part.Parent = model
        if not def.far then
            part.Transparency = 0
        end
    end
    -- Camera frames the actual 3D bounding box; no Workspace parts ever appear.
    local _, bounds = model:GetBoundingBox()
    local center = select(1, model:GetBoundingBox()).Position
    model:PivotTo(CFrame.new(center) * CFrame.Angles(0, math.rad(yawDegrees or 0), 0) * CFrame.new(-center))
    local camera = Instance.new("Camera")
    camera.Name = "PreviewCamera"
    camera.FieldOfView = 36
    local extent = math.max(bounds.X, bounds.Y, bounds.Z)
    local distance = math.max(6, extent * 2.4 + 2)
    camera.CFrame = CFrame.lookAt(center + Vector3.new(distance * 0.42, distance * 0.22, distance), center)
    camera.Parent = viewport
    viewport.CurrentCamera = camera
    return model
end
return Preview
