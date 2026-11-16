-- EGGRUMBLE V3: isolated client-only post-elimination viewing aid.
-- References ONLY existing #482 replicated preview state. No server/score/game authority.
-- Integrator: map this LocalScript under StarterPlayerScripts; do not copy existing lobby.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local player = Players.LocalPlayer
local WORLD_NAME = "EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW"
local FALLEN_CORE = Color3.fromRGB(59, 54, 55)
local CAMERA_OFFSET = Vector3.new(0, 48, -75)

local active = false
local dismissed = false
local overview = false
local selected = 1
local elapsed = 0
local savedCameraType = nil
local savedCameraSubject = nil
local ownedCamera = nil
local gui = nil
local label = nil
local overviewButton = nil

local function currentArena()
    local mode = player:GetAttribute("EGGRUMBLE_QueuedMode")
    if mode ~= "TEAM" and mode ~= "BATTLE_ROYALE" then return nil end
    local root = workspace:FindFirstChild(WORLD_NAME)
    local arena = root and root:FindFirstChild(mode .. "_Arena")
    if not arena or not arena:IsA("Folder") then return nil end
    -- The eliminated player must belong to THIS world, not the other mode.
    if not arena:FindFirstChild("Castle_" .. tostring(player.UserId)) then return nil end
    return arena
end

local function aliveCastles(arena)
    local castles = {}
    for _, child in ipairs(arena:GetChildren()) do
        if child:IsA("Model") and string.sub(child.Name, 1, 7) == "Castle_" then
            local core = child:FindFirstChild("StandardCore")
            -- Server colors a fallen core dark gray. Never follow a destroyed one.
            if core and core:IsA("BasePart") and core.Color ~= FALLEN_CORE then
                table.insert(castles, core)
            end
        end
    end
    table.sort(castles, function(a, b) return a.Parent.Name < b.Parent.Name end)
    return castles
end

local function restoreCamera()
    local camera = ownedCamera
    if not camera or workspace.CurrentCamera ~= camera then return end
    if camera.CameraType == Enum.CameraType.Scriptable then
        camera.CameraType = savedCameraType or Enum.CameraType.Custom
        local subject = savedCameraSubject
        if not subject or not subject.Parent then
            local character = player.Character
            subject = character and character:FindFirstChildOfClass("Humanoid")
        end
        if subject then camera.CameraSubject = subject end
    end
end

local function stop()
    if not active then return end
    active = false
    restoreCamera()
    if gui then gui:Destroy() end
    gui = nil
    label = nil
    overviewButton = nil
    savedCameraType = nil
    savedCameraSubject = nil
    ownedCamera = nil
end

local function makeButton(parent, text, x, width)
    local button = Instance.new("TextButton")
    button.Name = "Spectator_" .. text
    button.Size = UDim2.fromOffset(width, 28)
    button.Position = UDim2.fromOffset(x, 35)
    button.BackgroundColor3 = Color3.fromRGB(35, 44, 51)
    button.BackgroundTransparency = 0.08
    button.TextColor3 = Color3.fromRGB(255, 255, 255)
    button.TextScaled = false
    button.TextSize = 13
    button.Font = Enum.Font.GothamMedium
    button.Text = text
    button.AutoButtonColor = true
    button.Parent = parent
    return button
end

local function start()
    if active or dismissed or player:GetAttribute("EGGRUMBLE_Eliminated") ~= true then return end
    if not currentArena() then return end
    local camera = workspace.CurrentCamera
    local playerGui = player:FindFirstChildOfClass("PlayerGui")
    if not camera or not playerGui then return end
    savedCameraType = camera.CameraType
    savedCameraSubject = camera.CameraSubject
    ownedCamera = camera
    active = true
    overview = false
    selected = 1

    gui = Instance.new("ScreenGui")
    gui.Name = "EGGRUMBLE_EliminationSpectator"
    gui.ResetOnSpawn = false
    gui.IgnoreGuiInset = false
    gui.DisplayOrder = 10
    gui.Parent = playerGui

    local panel = Instance.new("Frame")
    panel.Name = "SpectatorCompactPanel"
    panel.AnchorPoint = Vector2.new(1, 0)
    panel.Position = UDim2.new(1, -10, 0, 10)
    panel.Size = UDim2.fromOffset(266, 71)
    panel.BackgroundColor3 = Color3.fromRGB(18, 24, 32)
    panel.BackgroundTransparency = 0.12
    panel.BorderSizePixel = 0
    panel.Parent = gui

    label = Instance.new("TextLabel")
    label.Name = "ViewState"
    label.Position = UDim2.fromOffset(6, 3)
    label.Size = UDim2.fromOffset(254, 27)
    label.BackgroundTransparency = 1
    label.TextColor3 = Color3.fromRGB(255, 239, 190)
    label.TextXAlignment = Enum.TextXAlignment.Left
    label.TextSize = 13
    label.Font = Enum.Font.GothamBold
    label.Text = "城が陥落｜観戦中"
    label.Parent = panel

    local nextButton = makeButton(panel, "次の城", 5, 78)
    overviewButton = makeButton(panel, "戦場", 91, 78)
    local exitButton = makeButton(panel, "観戦終了", 177, 84)
    nextButton.Activated:Connect(function()
        if not active then return end
        local arena = currentArena()
        if not arena then return end
        local castles = aliveCastles(arena)
        if #castles == 0 then return end
        selected = selected % #castles + 1
        overview = false
    end)
    overviewButton.Activated:Connect(function()
        if not active then return end
        overview = not overview
    end)
    exitButton.Activated:Connect(function()
        dismissed = true -- Do not immediately reopen while the same castle is fallen.
        stop()
    end)
    camera.CameraType = Enum.CameraType.Scriptable
end

local function refresh(dt)
    elapsed += dt
    if elapsed < 0.25 then return end
    elapsed = 0
    if player:GetAttribute("EGGRUMBLE_Eliminated") ~= true then
        dismissed = false
        stop()
        return
    end
    local arena = currentArena()
    if not arena then
        stop()
        return
    end
    if not active then start() end
    if not active then return end
    local camera = workspace.CurrentCamera
    if camera ~= ownedCamera then
        -- Another camera took ownership: don't fight its controller.
        dismissed = true
        stop()
        return
    end
    local castles = aliveCastles(arena)
    if selected > #castles then selected = 1 end
    local field = arena:FindFirstChild("TacticalBattlefield")
    if overview and field and field:IsA("BasePart") then
        label.Text = "城が陥落｜戦場全景"
        local focus = field.Position + Vector3.new(0, 25, 0)
        camera.CFrame = CFrame.lookAt(focus + Vector3.new(0, 330, -390), focus)
    elseif #castles > 0 then
        local core = castles[selected]
        if core then
            label.Text = "城が陥落｜生存城 " .. tostring(selected) .. "/" .. tostring(#castles)
            local focus = core.Position + Vector3.new(0, 6, 0)
            camera.CFrame = CFrame.lookAt(focus + CAMERA_OFFSET, focus)
        end
    elseif field and field:IsA("BasePart") then
        label.Text = "決着間近｜戦場全景"
        local focus = field.Position + Vector3.new(0, 25, 0)
        camera.CFrame = CFrame.lookAt(focus + Vector3.new(0, 330, -390), focus)
    else
        stop()
    end
end

player:GetAttributeChangedSignal("EGGRUMBLE_Eliminated"):Connect(function()
    if player:GetAttribute("EGGRUMBLE_Eliminated") ~= true then
        dismissed = false
        stop()
    else
        start()
    end
end)
player:GetAttributeChangedSignal("EGGRUMBLE_QueuedMode"):Connect(function()
    if active and not currentArena() then stop() end
end)
RunService.RenderStepped:Connect(refresh)
start()
