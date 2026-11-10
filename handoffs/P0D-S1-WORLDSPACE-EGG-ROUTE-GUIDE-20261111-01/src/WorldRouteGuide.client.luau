--!strict
-- P0D S1 optional client-only world-space route hint.
-- The current Game.server.luau remains sole authority over egg, scoring and match.
-- Mount this ONCE as a separate LocalScript; the existing HUD is unchanged.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local player = Players.LocalPlayer
local shared = ReplicatedStorage:WaitForChild("TrapRaidersShared")
local model = require(shared:WaitForChild("WorldRouteModel"))
local remote = ReplicatedStorage:WaitForChild("TrapRaidersS1Remote") :: RemoteEvent

-- Parent directly under PlayerGui; target lives in the replicated world.
-- The GUI and its single text label are reused across all snapshots and respawns.
local billboard = Instance.new("BillboardGui")
billboard.Name = "S1WorldRouteHintLocal"
billboard.Adornee = nil
billboard.Enabled = false
billboard.Active = false
billboard.ResetOnSpawn = false
billboard.AlwaysOnTop = true
billboard.MaxDistance = 220
billboard.Size = UDim2.fromOffset(172, 46)
billboard.StudsOffsetWorldSpace = Vector3.new(0, 8, 0)
billboard.Parent = player:WaitForChild("PlayerGui")

local text = Instance.new("TextLabel")
text.Name = "RouteLabel"
text.Size = UDim2.fromScale(1, 1)
text.BackgroundColor3 = Color3.fromRGB(25, 35, 47)
text.BackgroundTransparency = 0.15
text.BorderSizePixel = 0
text.Font = Enum.Font.GothamBold
text.TextColor3 = Color3.fromRGB(255, 233, 144)
text.TextSize = 17
text.TextScaled = false
text.TextWrapped = true
text.Text = ""
text.Parent = billboard
local corner = Instance.new("UICorner")
corner.CornerRadius = UDim.new(0, 10)
corner.Parent = text

local lastSerial = -1
local selected = nil
local lastTarget: Instance? = nil

local function resolveWorldPart(folderName: string?, partName: string?): BasePart?
    if folderName == nil or partName == nil then return nil end
    local map = workspace:FindFirstChild("TRAP_RAIDERS_S1")
    if map == nil then return nil end
    local teamFolder = map:FindFirstChild(folderName)
    if teamFolder == nil then return nil end
    local part = teamFolder:FindFirstChild(partName)
    if part and part:IsA("BasePart") then return part end
    return nil
end

local function draw()
    if selected == nil or selected.kind == "NONE" then
        billboard.Enabled = false
        billboard.Adornee = nil
        lastTarget = nil
        return
    end
    -- Map replication may arrive after first SNAPSHOT. The next snapshot retries.
    local target = resolveWorldPart(selected.folderName, selected.partName)
    if target == nil then
        billboard.Enabled = false
        billboard.Adornee = nil
        lastTarget = nil
        return
    end
    if target ~= lastTarget then
        billboard.Adornee = target
        lastTarget = target
    end
    if text.Text ~= selected.label then text.Text = selected.label end
    billboard.Enabled = true
end

remote.OnClientEvent:Connect(function(snapshot: any)
    local nextRoute = model.resolve(snapshot, lastSerial)
    if nextRoute == nil then return end
    lastSerial = nextRoute.serial
    selected = nextRoute
    draw()
end)