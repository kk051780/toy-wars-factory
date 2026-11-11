--!strict
-- Optional S1 client-only lobby practice. Never FireServer, no match reward or damage.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local player = Players.LocalPlayer
local remote = ReplicatedStorage:WaitForChild("TrapRaidersS1Remote") :: RemoteEvent
local Practice = require(script.Parent:WaitForChild("LobbyPracticeModel"))
local state = Practice.new()
local dummy: Model? = nil
local head: BasePart? = nil
local retired = false
local characterEpoch = 0

local gui = Instance.new("ScreenGui")
gui.Name = "S1SoloLobbyPractice"
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = false
gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
gui.Parent = player:WaitForChild("PlayerGui")

local button = Instance.new("TextButton")
button.Name = "LocalPracticeAttack"
button.Size = UDim2.fromOffset(134, 70)
button.Position = UDim2.new(1, -148, 1, -14)
button.AnchorPoint = Vector2.new(0, 1)
button.Text = "🪵 れんしゅう\nたたく！"
button.TextScaled = true
button.TextWrapped = true
button.Font = Enum.Font.GothamBold
button.TextColor3 = Color3.new(1, 1, 1)
button.BackgroundColor3 = Color3.fromRGB(133, 95, 44)
button.Visible = false
button.Parent = gui
local corner = Instance.new("UICorner")
corner.CornerRadius = UDim.new(0, 12)
corner.Parent = button

local counter = Instance.new("TextLabel")
counter.Name = "LocalOnlyHitCounter"
counter.Size = UDim2.fromOffset(178, 43)
counter.Position = UDim2.new(1, -187, 1, -92)
counter.TextWrapped = true
counter.TextScaled = true
counter.Font = Enum.Font.GothamBold
counter.TextColor3 = Color3.fromRGB(255, 235, 169)
counter.BackgroundColor3 = Color3.fromRGB(26, 34, 45)
counter.BackgroundTransparency = 0.2
counter.Visible = false
counter.Parent = gui
local cc = Instance.new("UICorner")
cc.CornerRadius = UDim.new(0, 10)
cc.Parent = counter

local function part(parent: Instance, name: string, size: Vector3, cf: CFrame,
    color: Color3): Part
    local p = Instance.new("Part")
    p.Name = name
    p.Size = size
    p.CFrame = cf
    p.Color = color
    p.Material = Enum.Material.SmoothPlastic
    p.Anchored = true
    p.CanCollide = false
    p.CanTouch = false
    p.CanQuery = false
    p.Parent = parent
    return p
end

local function clearDummy()
    head = nil
    if dummy then dummy:Destroy() end
    dummy = nil
end

local function hide()
    button.Visible = false
    counter.Visible = false
    clearDummy()
end

local function getRoot(): BasePart?
    local character = player.Character
    if not character then return nil end
    local root = character:FindFirstChild("HumanoidRootPart")
    local humanoid = character:FindFirstChildOfClass("Humanoid")
    if root and root:IsA("BasePart") and humanoid and humanoid.Health > 0 then
        return root
    end
    return nil
end

local function createDummy(root: BasePart)
    if dummy or not state.eligible or retired then return end
    local origin = root.Position + root.CFrame.LookVector * 8
    local base = Vector3.new(origin.X, root.Position.Y - 2.8, origin.Z)
    local model = Instance.new("Model")
    model.Name = "S1_LOCAL_ONLY_PRACTICE_DUMMY"
    -- Only this client's Workspace sees these parts. No server-side damage or touched events.
    local wood = Color3.fromRGB(167, 122, 77)
    local pale = Color3.fromRGB(244, 207, 113)
    part(model, "Base", Vector3.new(4, 0.4, 4), CFrame.new(base), wood)
    part(model, "Post", Vector3.new(1.2, 4.2, 1.2), CFrame.new(base + Vector3.new(0, 2.1, 0)), wood)
    local target = part(model, "Target", Vector3.new(3.6, 3.6, 0.5),
        CFrame.new(base + Vector3.new(0, 3.5, 0)), pale)
    target.Shape = Enum.PartType.Cylinder
    local board = Instance.new("BillboardGui")
    board.Name = "PracticeLabel"
    board.Size = UDim2.fromOffset(154, 38)
    board.StudsOffsetWorldSpace = Vector3.new(0, 3.3, 0)
    board.AlwaysOnTop = false
    board.Parent = target
    local label = Instance.new("TextLabel")
    label.Size = UDim2.fromScale(1, 1)
    label.BackgroundColor3 = Color3.fromRGB(38, 48, 60)
    label.BackgroundTransparency = 0.2
    label.TextColor3 = Color3.fromRGB(255, 255, 255)
    label.TextScaled = true
    label.Font = Enum.Font.GothamBold
    label.Text = "れんしゅうのまと"
    label.Parent = board
    model.Parent = workspace
    dummy = model
    head = target
end

local function refresh()
    if retired or not state.eligible then hide(); return end
    local root = getRoot()
    if root == nil then hide(); return end
    if not dummy then createDummy(root) end
    local visible = dummy ~= nil
    button.Visible = visible
    counter.Visible = visible
    counter.Text = Practice.status(state)
end

button.MouseButton1Click:Connect(function()
    if retired or not state.eligible then return end
    local root = getRoot()
    local target = head
    if not root or not target then refresh(); return end
    local diff = target.Position - root.Position
    local dist = diff.Magnitude
    local dot = if dist > 0.0001 then root.CFrame.LookVector:Dot(diff.Unit) else 1
    if Practice.hit(state, os.clock(), dist, dot) then
        counter.Text = Practice.status(state)
    end
end)

remote.OnClientEvent:Connect(function(packet)
    if retired then return end
    if type(packet) ~= "table" or packet.kind ~= "SNAPSHOT" then return end
    Practice.consume(state, packet)
    refresh()
end)

player.CharacterAdded:Connect(function(character)
    characterEpoch += 1
    local epoch = characterEpoch
    hide()
    task.spawn(function()
        local root = character:WaitForChild("HumanoidRootPart", 10)
        if root and epoch == characterEpoch and player.Character == character then
            refresh()
        end
    end)
end)
player.CharacterRemoving:Connect(function()
    characterEpoch += 1
    hide()
end)
player.AncestryChanged:Connect(function(_, parent)
    if parent == nil then
        retired = true
        hide()
        gui:Destroy()
    end
end)
