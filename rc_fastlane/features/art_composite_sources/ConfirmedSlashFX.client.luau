--!nocheck
-- P0D #364 FB-008 / #372 ART-COMBAT: real-hit-only 3D slash afterimages.
-- Studio-only LocalScript. Reads the ORIGINAL single Horde server's
-- replicated RealDamagePopup.Enabled and damage/KO text; NEVER invents hits,
-- damage, XP, knockback, coins, egg, score, rewards or any remote request.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end

local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")
local TweenService = game:GetService("TweenService")
local Debris = game:GetService("Debris")
local player = Players.LocalPlayer
if not player then return end

local arena = Workspace:WaitForChild("TRAP_RAIDERS_S1", 45)
if not arena then warn("FB008_NO_GAME_ARENA_FAIL_CLOSED"); return end
local horde = arena:WaitForChild("EGG_RUMBLE_NEUTRAL_MUSOU_EXPERIMENT", 45)
if not horde then warn("FB008_NO_REAL_HORDE_FAIL_CLOSED"); return end

local container = Instance.new("Folder")
container.Name = "FB008_CONFIRMED_SLASH_VFX_CLIENT_ONLY"
container:SetAttribute("PreviewOnly", true)
container:SetAttribute("NoGameplayAuthority", true)
container:SetAttribute("StudioFunAccepted", false)
container.Parent = Workspace

local MAX_ACTIVE_PARTS = 48
local VIEW_DISTANCE = 115
local MIN_PER_TARGET_INTERVAL = .09
local BURST_DURATION = .23
local active = 0
local seen = {}
local alive = true

local function color(r,g,b) return Color3.fromRGB(r,g,b) end
local function makePart(name, size, cf, tint, transparency, shape)
    if not alive or not container.Parent or active >= MAX_ACTIVE_PARTS then return nil end
    active += 1
    local p = Instance.new("Part")
    p.Name = name
    p.Size = size
    p.CFrame = cf
    p.Anchored = true
    p.CanCollide = false
    p.CanTouch = false
    p.CanQuery = false
    p.CastShadow = false
    p.Material = Enum.Material.Neon
    p.Color = tint
    p.Transparency = transparency
    if shape == "Cylinder" then p.Shape = Enum.PartType.Cylinder end
    p.Parent = container
    Debris:AddItem(p, .34)
    -- Count is explicitly released even if Debris removes the part sooner.
    task.delay(.35, function()
        active = math.max(0, active - 1)
    end)
    return p
end

local function localViewBasis(origin)
    local camera = Workspace.CurrentCamera
    local look = if camera then camera.CFrame.LookVector else Vector3.new(0,0,-1)
    local flattened = Vector3.new(look.X,0,look.Z)
    if flattened.Magnitude < .01 then flattened = Vector3.new(0,0,-1) end
    return CFrame.lookAt(origin,origin+flattened.Unit)
end

local function isVisibleNear(core)
    local character = player.Character
    local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
    if not root or not root:IsA("BasePart") then return false end
    return (root.Position - core.Position).Magnitude <= VIEW_DISTANCE
end

local function renderConfirmedHit(model,core,popup)
    if not model.Parent or not core.Parent or not popup.Parent then return end
    if not isVisibleNear(core) then return end
    local elite = model.Name == "MUSOU_ELITE_TELEGRAPH"
    local marker = popup:FindFirstChildWhichIsA("TextLabel")
    local cueGui = core:FindFirstChild("CombatCue")
    local cue = if cueGui and cueGui:IsA("BillboardGui")
        then cueGui:FindFirstChildWhichIsA("TextLabel") else nil
    local markerText = if marker then marker.Text else ""
    local cueText = if cue then cue.Text else ""
    local isKO = string.find(markerText,"撃破",1,true) ~= nil
        or string.find(cueText,"撃破",1,true) ~= nil
    local gold = color(255,212,116)
    local cyan = color(127,224,255)
    local primary = if elite then gold else cyan
    local basis = localViewBasis(core.Position)
    local initialDistance = if elite then 3.4 else 2.2
    -- Three staggered slashes fanning through real server-hit enemy position.
    -- Cinematic local afterimages only; no extra Hitbox, AoE or damage.
    for i=1,3 do
        local arcX = (i-2)*.42
        local arcY = (i-2)*.52
        local roll = (i-2)*29 + (if elite then 14 else -7)
        local start = basis * CFrame.new(arcX,arcY,-initialDistance)
            * CFrame.Angles(0,0,math.rad(roll))
        local endCF = basis * CFrame.new(arcX*.9,arcY+.28,-initialDistance-.12)
            * CFrame.Angles(0,0,math.rad(roll+15))
        local trail = makePart("CONFIRMED_HIT_SLASH_"..i,
            Vector3.new(if elite then 3.15 else 2.05,.22,.14),
            start,primary,.12,nil)
        if trail then
            local tween=TweenService:Create(trail,
                TweenInfo.new(BURST_DURATION,Enum.EasingStyle.Quad,Enum.EasingDirection.Out),
                {Size=Vector3.new(if elite then 6.5 else 4.7,.075,.12),
                    Transparency=1, CFrame=endCF})
            tween:Play()
        end
    end
    if isKO then
        -- A horizontal, expanding KO ground shock-ring: server KO text first.
        local ringPos = Vector3.new(core.Position.X,core.Position.Y -
            (if elite then 2.40 else 1.55),core.Position.Z)
        local ring = makePart("CONFIRMED_KO_GROUND_RIPPLE",
            Vector3.new(.09,1.65,1.65),
            CFrame.new(ringPos) * CFrame.Angles(0,0,math.rad(90)),
            gold,.30,"Cylinder")
        if ring then
            TweenService:Create(ring,
                TweenInfo.new(.27,Enum.EasingStyle.Quad,Enum.EasingDirection.Out),
                {Size=Vector3.new(.055,if elite then 10 else 6,if elite then 10 else 6),
                    Transparency=1}):Play()
        end
    end
end

local function attach(model)
    if not alive or not model:IsA("Model") or seen[model] then return end
    local good = model.Name:match("^MUSOU_MINION_%d+$")
        or model.Name == "MUSOU_ELITE_TELEGRAPH"
    if not good then return end
    local core = model:FindFirstChild("Core") or model:WaitForChild("Core",5)
    if not core or not core:IsA("BasePart") then return end
    local popup = core:FindFirstChild("RealDamagePopup")
        or core:WaitForChild("RealDamagePopup",5)
    if not popup or not popup:IsA("BillboardGui") then return end
    if seen[model] then return end
    seen[model] = true
    local last = -100000
    local enabledConn
    enabledConn = popup:GetPropertyChangedSignal("Enabled"):Connect(function()
        if not alive or not popup.Enabled or not model.Parent then return end
        local now = os.clock()
        if now-last < MIN_PER_TARGET_INTERVAL then return end
        last = now
        -- Let the replicated server-written popup text settle before querying
        -- its KO variant; the visual is delayed by only 30ms.
        task.delay(.03,function()
            if alive and model.Parent and popup.Parent then
                renderConfirmedHit(model,core,popup)
            end
        end)
    end)
    local destroyingConn
    destroyingConn = model.Destroying:Connect(function()
        if enabledConn then enabledConn:Disconnect() end
        if destroyingConn then destroyingConn:Disconnect() end
        seen[model] = nil
    end)
end

for _,model in ipairs(horde:GetChildren()) do
    task.defer(attach,model)
end
local addConn = horde.ChildAdded:Connect(function(child)
    task.defer(attach,child)
end)
local destroyConn
destroyConn = horde.Destroying:Connect(function()
    alive = false
    addConn:Disconnect()
    if destroyConn then destroyConn:Disconnect() end
    container:Destroy()
end)
script.Destroying:Connect(function()
    alive = false
    addConn:Disconnect()
    if destroyConn then destroyConn:Disconnect() end
    if container.Parent then container:Destroy() end
end)
print("FB008_CONFIRMED_HIT_SLASH_VFX_ATTACHED_STUDIO_ART_NO_GO")
