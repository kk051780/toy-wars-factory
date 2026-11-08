-- P0-D route A: original non-production one-minute sorting prototype.
-- Install only as a Script in ServerScriptService of a backed-up isolated Studio place.
-- Never install in the Toy Wars production place.
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")

local ROOT_NAME = "P0D_RobotPostOffice_TrialOnly"
if Workspace:FindFirstChild(ROOT_NAME) then
    error("P0-D demo already exists; refusing a duplicate world")
end

local world = Instance.new("Model")
world.Name = ROOT_NAME
world.Parent = Workspace
local sessions = {}

local colors = {
    {id = "RED", rgb = Color3.fromRGB(234, 82, 87), x = -12},
    {id = "BLUE", rgb = Color3.fromRGB(75, 155, 238), x = 0},
    {id = "YELLOW", rgb = Color3.fromRGB(242, 204, 78), x = 12},
}

local function makePart(name, size, position, tint, parent)
    local p = Instance.new("Part")
    p.Name = name
    p.Anchored = true
    p.Size = size
    p.Position = position
    p.Color = tint
    p.Material = Enum.Material.SmoothPlastic
    p.Parent = parent
    return p
end

local function addSign(part, text, size)
    local gui = Instance.new("BillboardGui")
    gui.Name = "VisibleLabel"
    gui.Size = UDim2.fromOffset(size, 52)
    gui.StudsOffset = Vector3.new(0, part.Size.Y / 2 + 2.5, 0)
    gui.AlwaysOnTop = true
    gui.MaxDistance = 90
    gui.Parent = part
    local label = Instance.new("TextLabel")
    label.Size = UDim2.fromScale(1, 1)
    label.BackgroundColor3 = Color3.fromRGB(27, 34, 49)
    label.BackgroundTransparency = 0.15
    label.TextColor3 = Color3.new(1, 1, 1)
    label.TextScaled = true
    label.Font = Enum.Font.GothamBold
    label.Text = text
    label.Parent = gui
end

local function addClick(part, onClick)
    local detector = Instance.new("ClickDetector")
    detector.MaxActivationDistance = 42
    detector.Parent = part
    detector.MouseClick:Connect(onClick)
end

local function ensureHUD(player)
    local playerGui = player:WaitForChild("PlayerGui")
    local old = playerGui:FindFirstChild("P0D_RobotPostOfficeHUD")
    if old then return old:FindFirstChild("Objective") end
    local gui = Instance.new("ScreenGui")
    gui.Name = "P0D_RobotPostOfficeHUD"
    gui.ResetOnSpawn = false
    gui.IgnoreGuiInset = false
    gui.Parent = playerGui
    local objective = Instance.new("TextLabel")
    objective.Name = "Objective"
    objective.Size = UDim2.new(0.8, 0, 0, 96)
    objective.Position = UDim2.new(0.1, 0, 0, 30)
    objective.BackgroundColor3 = Color3.fromRGB(24, 39, 58)
    objective.BackgroundTransparency = 0.12
    objective.TextColor3 = Color3.new(1, 1, 1)
    objective.Font = Enum.Font.GothamBold
    objective.TextScaled = true
    objective.TextWrapped = true
    objective.Text = "ROBOT POST OFFICE / SORT 3 PARCELS"
    objective.Parent = gui
    local corner = Instance.new("UICorner")
    corner.CornerRadius = UDim.new(0, 12)
    corner.Parent = objective
    return objective
end

local function show(player, message)
    local session = sessions[player]
    if not session then return end
    local ui = session.objective
    if ui and ui.Parent then
        ui.Text = "ROBOT POST OFFICE | " .. tostring(session.count) .. "/3\n" .. message
    end
end

local function selectParcel(player, colorId)
    local state = sessions[player]
    if not state then return end
    if state.count >= 3 then
        show(player, "Finished! Click green REPLAY pillar.")
        return
    end
    state.selected = colorId
    show(player, "Selected " .. colorId .. ". Click the MATCHING bin.")
end

local function deliver(player, binId)
    local state = sessions[player]
    if not state then return end
    if state.count >= 3 then
        show(player, "Finished! Click green REPLAY pillar.")
    elseif not state.selected then
        show(player, "Click a parcel first, then its matching bin.")
    elseif state.selected ~= binId then
        show(player, "Wrong bin: try again. Your parcel is still selected.")
    else
        state.count = state.count + 1
        state.selected = nil
        if state.count == 3 then
            show(player, "Delivered 3/3! Click green REPLAY pillar.")
        else
            show(player, "Delivered! Choose the next parcel.")
        end
    end
end

local function replay(player)
    local state = sessions[player]
    if not state then return end
    state.count = 0
    state.selected = nil
    show(player, "New round: click parcel, then same-color bin.")
end

makePart("TrialFloor", Vector3.new(48, 1, 36), Vector3.new(0, -0.5, -26),
    Color3.fromRGB(194, 202, 216), world)
makePart("BackWall", Vector3.new(48, 10, 1), Vector3.new(0, 5, -43),
    Color3.fromRGB(133, 175, 194), world)
makePart("LeftWall", Vector3.new(1, 10, 36), Vector3.new(-24, 5, -26),
    Color3.fromRGB(133, 175, 194), world)
makePart("RightWall", Vector3.new(1, 10, 36), Vector3.new(24, 5, -26),
    Color3.fromRGB(133, 175, 194), world)

for _, color in ipairs(colors) do
    local parcelId = color.id
    local parcel = makePart("Parcel_" .. parcelId, Vector3.new(4, 3, 4),
        Vector3.new(color.x, 1.5, -15), color.rgb, world)
    addSign(parcel, "PICK " .. parcelId, 180)
    addClick(parcel, function(player)
        selectParcel(player, parcelId)
    end)

    local bin = makePart("DeliveryBin_" .. parcelId, Vector3.new(7, 4, 6),
        Vector3.new(color.x, 2, -33), color.rgb, world)
    addSign(bin, "DELIVER " .. parcelId, 190)
    addClick(bin, function(player)
        deliver(player, parcelId)
    end)
end

local replayPillar = makePart("ReplayPillar", Vector3.new(4, 7, 4),
    Vector3.new(19, 3.5, -16), Color3.fromRGB(55, 178, 116), world)
addSign(replayPillar, "REPLAY", 160)
addClick(replayPillar, replay)

local function join(player)
    local state = {count = 0, selected = nil, objective = nil}
    sessions[player] = state
    state.objective = ensureHUD(player)
    show(player, "Click a parcel, then a same-color delivery bin.")
end

Players.PlayerAdded:Connect(join)
Players.PlayerRemoving:Connect(function(player)
    sessions[player] = nil
end)
for _, player in ipairs(Players:GetPlayers()) do
    task.spawn(join, player)
end
print("P0D_SORTING_POSTOFFICE_TRIAL_READY | no save/publish/purchases/persistence")
