--!strict
-- EGGRUMBLE V3 / FB-PQG-SPECTATE: client-only observation after castle defeat.
-- Private Studio candidate. Zero Game/HP/egg/score/Remote/Store authority.
-- Keep ordinary ACTIVE gameplay HUD and camera untouched.
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")
local UserInputService = game:GetService("UserInputService")
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end

local player = Players.LocalPlayer
local previousSubject: Instance? = nil
local previousType: Enum.CameraType? = nil
local active = false
local arena: Instance? = nil
local viewIndex = 1
local targets: {Model} = {}
local elapsed = 0

local gui = Instance.new("ScreenGui")
gui.Name = "EGGRUMBLE_EliminatedSpectate"
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = false
gui.DisplayOrder = 12
gui.Enabled = false
gui.Parent = player:WaitForChild("PlayerGui")

local panel = Instance.new("Frame")
panel.Name = "SpectateControls"
panel.AnchorPoint = Vector2.new(1, 0)
panel.Position = UDim2.new(1, -12, 0, 78)
panel.Size = UDim2.fromOffset(204, 38)
panel.BackgroundColor3 = Color3.fromRGB(21, 27, 37)
panel.BackgroundTransparency = .16
panel.BorderSizePixel = 0
panel.Parent = gui
Instance.new("UICorner", panel).CornerRadius = UDim.new(0, 8)

local function control(text: string, x: number): TextButton
    local button = Instance.new("TextButton")
    button.Size = UDim2.fromOffset(34, 30)
    button.Position = UDim2.fromOffset(x, 4)
    button.Text = text
    button.TextScaled = true
    button.Font = Enum.Font.GothamBold
    button.TextColor3 = Color3.new(1, 1, 1)
    button.BackgroundColor3 = Color3.fromRGB(57, 77, 105)
    button.BorderSizePixel = 0
    button.Parent = panel
    Instance.new("UICorner", button).CornerRadius = UDim.new(0, 6)
    return button
end
local left = control("◀", 4)
local right = control("▶", 166)
local label = Instance.new("TextLabel")
label.Position = UDim2.fromOffset(40, 3)
label.Size = UDim2.fromOffset(124, 32)
label.BackgroundTransparency = 1
label.TextColor3 = Color3.fromRGB(243, 245, 249)
label.Font = Enum.Font.GothamMedium
label.TextScaled = true
label.Text = "城を観戦"
label.Parent = panel

local function getOwnArena(): Instance?
    local lobby = Workspace:FindFirstChild("EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW")
    if not lobby then return nil end
    for _, mode in ipairs({"TEAM", "BATTLE_ROYALE"}) do
        local candidate = lobby:FindFirstChild(mode .. "_Arena")
        if candidate and candidate:FindFirstChild("Castle_" .. tostring(player.UserId)) then
            return candidate
        end
    end
    return nil
end

local function gatherCastles(inArena: Instance): {Model}
    local result: {Model} = {}
    for _, instance in ipairs(inArena:GetChildren()) do
        if instance:IsA("Model") and string.sub(instance.Name, 1, 7) == "Castle_"
            and instance:FindFirstChild("StandardCore") then
            table.insert(result, instance)
        end
    end
    table.sort(result, function(a: Model, b: Model): boolean
        return a.Name < b.Name
    end)
    return result
end

local function restoreCamera()
    local camera = Workspace.CurrentCamera
    if camera then
        camera.CameraType = previousType or Enum.CameraType.Custom
        local character = player.Character
        local humanoid = character and character:FindFirstChildOfClass("Humanoid")
        if humanoid then
            camera.CameraSubject = humanoid
        elseif previousSubject and previousSubject.Parent then
            camera.CameraSubject = previousSubject :: Instance
        end
    end
    previousSubject = nil
    previousType = nil
end

local function exitSpectate()
    if not active then return end
    active = false
    arena = nil
    targets = {}
    viewIndex = 1
    gui.Enabled = false
    restoreCamera()
end

local function frameTarget()
    if not active then return end
    local camera = Workspace.CurrentCamera
    local target = targets[viewIndex]
    if not camera or not target or not target.Parent or not arena or not arena.Parent then
        exitSpectate()
        return
    end
    local focus = target:GetPivot().Position + Vector3.new(0, 9, 0)
    -- A fixed high third-person view; no per-frame shake or forced player movement.
    local eye = focus + Vector3.new(62, 67, 93)
    camera.CameraType = Enum.CameraType.Scriptable
    camera.CFrame = CFrame.lookAt(eye, focus)
    label.Text = string.format("観戦 %d/%d", viewIndex, #targets)
end

local function refresh()
    if player:GetAttribute("EGGRUMBLE_Eliminated") ~= true then
        exitSpectate()
        return
    end
    local ownArena = getOwnArena()
    if not ownArena then
        exitSpectate()
        return
    end
    local found = gatherCastles(ownArena)
    if #found == 0 then
        exitSpectate()
        return
    end
    if not active then
        local camera = Workspace.CurrentCamera
        if not camera then return end
        previousType = camera.CameraType
        previousSubject = camera.CameraSubject
        active = true
        viewIndex = 1
    elseif arena ~= ownArena then
        viewIndex = 1
    else
        local current = targets[viewIndex]
        if current then
            for i, castle in ipairs(found) do
                if castle == current then viewIndex = i; break end
            end
        end
    end
    arena = ownArena
    targets = found
    viewIndex = math.clamp(viewIndex, 1, #targets)
    gui.Enabled = true
    frameTarget()
end

local function cycle(offset: number)
    if not active or #targets == 0 then return end
    viewIndex = ((viewIndex - 1 + offset) % #targets) + 1
    frameTarget()
end

left.Activated:Connect(function() cycle(-1) end)
right.Activated:Connect(function() cycle(1) end)
UserInputService.InputBegan:Connect(function(input: InputObject, consumed: boolean)
    if consumed or not active then return end
    if input.KeyCode == Enum.KeyCode.Left then cycle(-1) end
    if input.KeyCode == Enum.KeyCode.Right then cycle(1) end
end)
player:GetAttributeChangedSignal("EGGRUMBLE_Eliminated"):Connect(refresh)
Workspace:GetPropertyChangedSignal("CurrentCamera"):Connect(function()
    if active then frameTarget() end
end)
RunService.Heartbeat:Connect(function(dt: number)
    elapsed += dt
    if elapsed < .5 then return end
    elapsed = 0
    -- Respawn/camera takeover, removed arenas and match end are recoverable.
    refresh()
end)
refresh()
