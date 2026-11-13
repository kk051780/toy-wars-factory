--!strict
-- Optional physical presentation adapter; never auto-runs, creates no Remote.
-- Original MapBuilder owner must select collision-safe CFrame.
local GateVisual = {}

function GateVisual.create(parent: Instance, transform: CFrame, corridorWidth: number): Model
    assert(typeof(transform) == "CFrame", "CFrame required")
    assert(type(corridorWidth) == "number" and corridorWidth == corridorWidth
        and corridorWidth >= 6 and corridorWidth <= 24, "valid corridorWidth required")
    local model = Instance.new("Model")
    model.Name = "NeutralEliteSharedRouteGate"

    local door = Instance.new("Part")
    door.Name = "PhysicalDoor"
    door.Anchored = true
    door.Size = Vector3.new(corridorWidth, 12, 1.2)
    door.CFrame = transform
    door.Material = Enum.Material.Neon
    door.Color = Color3.fromRGB(64, 163, 241)
    door.Transparency = 0.12
    door.CanCollide = true
    door.CanTouch = false
    door.CanQuery = true
    door.Parent = model

    local textGui = Instance.new("BillboardGui")
    textGui.Name = "Status"
    textGui.AlwaysOnTop = false
    textGui.Size = UDim2.fromOffset(150, 38)
    textGui.StudsOffsetWorldSpace = Vector3.new(0, 8, 0)
    textGui.Parent = door

    local text = Instance.new("TextLabel")
    text.Name = "Label"
    text.BackgroundTransparency = 0.3
    text.Size = UDim2.fromScale(1, 1)
    text.TextScaled = true
    text.Text = "TOY GATE"
    text.Parent = textGui
    model.PrimaryPart = door
    model.Parent = parent
    return model
end

-- No tweens/physics changes: this adapter is intended for a single existing
-- authoritative Game server tick. Visual red warning is not a damage event.
function GateVisual.render(model: Model, snapshot)
    local door = model:FindFirstChild("PhysicalDoor")
    assert(door and door:IsA("BasePart"), "PhysicalDoor missing")
    local open = snapshot.passable == true
    -- Roblox property invariant: CanQuery=false requires CanCollide=false.
    -- On reopening query restore BEFORE collision; on opening collision first.
    -- A passable door must not invisibly block original Game raycast attacks.
    if open then
        door.CanCollide = false
        door.CanQuery = false
    else
        door.CanQuery = true
        door.CanCollide = true
    end
    door.Transparency = open and 0.82 or 0.12
    door.Color = snapshot.phase == "WARNING" and Color3.fromRGB(255, 191, 71)
        or (open and Color3.fromRGB(93, 241, 172) or Color3.fromRGB(64, 163, 241))
    local board = door:FindFirstChild("Status")
    local label = board and board:FindFirstChild("Label")
    if label and label:IsA("TextLabel") then
        label.Text = snapshot.phase == "WARNING" and "OPENING!"
            or (open and "BOTH TEAMS: GO!" or "CLOSED")
    end
end

return GateVisual
