--!nocheck
-- #388 / #372 FB-015 ART-MOTION: first client-only cosmetic motion slice.
-- This is SOURCE_WIP, not PREP_READY, not official RC and not Studio accepted.
-- Parent candidate #387 supplies the original #374 ART_* silhouettes. No new
-- damage, AI, hitbox, score, XP, Remote, store, or authoritative animation.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")

local localPlayer = Players.LocalPlayer
if not localPlayer then return end
local arena = Workspace:WaitForChild("TRAP_RAIDERS_S1", 50)
if not arena then warn("ART_MOTION_NO_ARENA"); return end
local horde = arena:WaitForChild("EGG_RUMBLE_NEUTRAL_MUSOU_EXPERIMENT", 50)
if not horde then warn("ART_MOTION_NO_HORDE"); return end

local FEATURE = "P0D_ART_MOTION_CLIENT_V1"
local MAX_MODELS = 16
local MAX_ACTIVE_COSMETIC_PARTS = 56
local VIEW_RANGE_STUDS = 105
local ANIM_STEP = 1 / 25
local connected = {}
local records = {}
local isRunning = true
local elapsed = 0
local activeParts = 0

-- These names refer to the original #374 generated art. We DO NOT recreate
-- geometry or overlap #379/#381 slash particles or #374's hit sparks.
local watchedParts = {
    KNIGHT = {"ART_KNIGHT_CAPE","ART_KNIGHT_SPEAR_SHAFT",
              "ART_KNIGHT_SPEAR_TIP","ART_KNIGHT_SHIELD"},
    WRAITH = {"ART_WRAITH_SHROUD","ART_WRAITH_ORB",
              "ART_WRAITH_SHOULDER_FIN_-1","ART_WRAITH_SHOULDER_FIN_1"},
    BRUTE = {"ART_BRUTE_BACK_FUR","ART_BRUTE_MAUL_HANDLE",
             "ART_BRUTE_MAUL_HEAD","ART_BRUTE_SHOULDER_-1",
             "ART_BRUTE_SHOULDER_1"},
    ELITE = {"ART_ELITE_BACK_BANNER","ART_ELITE_GAUNTLET_-1",
             "ART_ELITE_GAUNTLET_1"},
}

local function isMinion(model)
    return model:IsA("Model") and (
        model.Name:match("^MUSOU_MINION_%d+$") ~= nil
        or model.Name == "MUSOU_ELITE_TELEGRAPH")
end

local function typeOf(model)
    if model.Name == "MUSOU_ELITE_TELEGRAPH" then return "ELITE" end
    local id = tonumber(model.Name:match("(%d+)$"))
    if not id then return nil end
    return ({"KNIGHT","WRAITH","BRUTE"})[((id - 1) % 3) + 1]
end

local function drop(model)
    local entry = records[model]
    if not entry then return end
    activeParts = math.max(0, activeParts - #entry.attachments)
    records[model] = nil
end

local function tryEquip(model)
    if not isRunning or records[model] or not isMinion(model) then return false end
    if model:GetAttribute("P0D_ART_MINION_V1") ~= true then return false end
    local kind = typeOf(model)
    local core = model:FindFirstChild("Core")
    if not kind or not core or not core:IsA("BasePart") then return false end
    local count = 0
    for _ in pairs(records) do count += 1 end
    if count >= MAX_MODELS then return false end

    local attachments = {}
    for _,name in ipairs(watchedParts[kind]) do
        local art = model:FindFirstChild(name)
        if art and art:IsA("BasePart") and art:GetAttribute(FEATURE) ~= true
            and #attachments + activeParts < MAX_ACTIVE_COSMETIC_PARTS then
            -- Preserve the author-created 3D geometry and its initial exact
            -- attachment offset. Re-evaluating relative CFrame from an already
            -- modified part would accumulate drift across frames.
            table.insert(attachments,{
                part=art, offset=core.CFrame:ToObjectSpace(art.CFrame), name=name
            })
        end
    end
    -- The server author marks P0D_ART_MINION_V1 before creating the art.
    -- Do not lock the observer to an incomplete first child attachment.
    -- Wait for all expected accessory parts before taking a fixed offset.
    if #attachments ~= #watchedParts[kind] then return false end
    records[model] = {
        core=core, model=model, kind=kind, attachments=attachments,
        prevPos=core.Position, speed=0, hitAt=-100, koAt=-100,
        lastHit=false, phase=(count * 1.19) + (#model.Name * .17),
    }
    activeParts += #attachments
    return true
end

local function watch(model)
    if not isMinion(model) or connected[model] then return end
    local leases = {}
    connected[model] = leases
    -- #374 marks the model BEFORE creating art children. ChildAdded retries
    -- ensure this observer does not race the visual model's construction.
    local function attempt()
        if not isRunning or not model.Parent then return end
        if tryEquip(model) then
            for _,c in ipairs(leases) do c:Disconnect() end
            connected[model] = nil
        end
    end
    table.insert(leases,model:GetAttributeChangedSignal("P0D_ART_MINION_V1"):Connect(attempt))
    table.insert(leases,model.ChildAdded:Connect(function(child)
        if child.Name:sub(1,4) == "ART_" then task.defer(attempt) end
    end))
    table.insert(leases,model.Destroying:Connect(function()
        for _,c in ipairs(leases) do c:Disconnect() end
        connected[model] = nil
        drop(model)
    end))
    task.defer(attempt)
end

local function movementFor(kind, name, speed, t, hitAge, koAge)
    local walking = math.clamp(speed / 12, 0, 1)
    local step = math.sin(t * (3.0 + walking * 6.0))
    local breathe = math.sin(t * 2.3) * (1 - walking * .45)
    local hit = if hitAge >= 0 and hitAge < .27 then (1 - hitAge / .27) else 0
    local dying = if koAge >= 0 and koAge < .7 then (koAge / .7) else 0
    local sway = .04 * breathe + .12 * walking * step
    local tilt = -.26 * hit + .45 * dying
    if kind == "KNIGHT" then
        if name:find("SPEAR",1,true) then
            return CFrame.new(0,.06*step,0)*CFrame.Angles(sway+tilt,0,-.08*walking*step)
        elseif name:find("SHIELD",1,true) then
            return CFrame.Angles(.06*walking*step - .16*hit,0,.06*breathe)
        end
        return CFrame.Angles(-.1*walking*step+tilt,0,.08*step)
    elseif kind == "WRAITH" then
        if name:find("ORB",1,true) then
            return CFrame.new(0,.19*math.sin(t*2.7),-.12*walking*step)
        end
        return CFrame.new(0,.11*math.sin(t*2.7),0)*CFrame.Angles(.06*step+tilt,0,.1*breathe)
    elseif kind == "BRUTE" then
        if name:find("MAUL",1,true) then
            return CFrame.Angles(.16*walking*step - .22*hit + tilt,0,.05*step)
        end
        return CFrame.Angles(.04*breathe+tilt,0,.08*step)
    else
        if name:find("GAUNTLET",1,true) then
            return CFrame.new(0,.04*walking*step,0)*CFrame.Angles(.08*step + tilt,0,0)
        end
        return CFrame.Angles(-.08*walking*step+tilt,0,.07*step)
    end
end

for _,child in ipairs(horde:GetChildren()) do task.defer(watch,child) end
local added = horde.ChildAdded:Connect(function(child) task.defer(watch,child) end)

local pulse
pulse = RunService.Heartbeat:Connect(function(dt)
    if not isRunning then return end
    if not horde.Parent then
        -- Match the original Horde's teardown semantics. Do not leave a
        -- live client animation loop running after world destruction.
        isRunning = false
        added:Disconnect()
        if pulse then pulse:Disconnect() end
        for _,leases in pairs(connected) do
            for _,connection in ipairs(leases) do connection:Disconnect() end
        end
        table.clear(connected)
        table.clear(records)
        return
    end
    if dt <= 0 or dt > .5 then return end
    elapsed += dt
    if elapsed < ANIM_STEP then return end
    local stepDt = elapsed
    elapsed = 0
    local character = localPlayer.Character
    local root = character and character:FindFirstChild("HumanoidRootPart")
    local now = os.clock()
    for model,entry in pairs(records) do
        local core = entry.core
        if not model.Parent or not core.Parent then
            drop(model)
        else
            local delta = core.Position - entry.prevPos
            entry.prevPos = core.Position
            entry.speed = (entry.speed * .7) + (.3 * (delta.Magnitude / stepDt))
            if root and root:IsA("BasePart")
                and (root.Position-core.Position).Magnitude <= VIEW_RANGE_STUDS then
                local popup = core:FindFirstChild("RealDamagePopup")
                local hit = popup and popup:IsA("BillboardGui") and popup.Enabled == true
                if hit and not entry.lastHit then entry.hitAt = now end
                entry.lastHit = hit == true
                local cue = core:FindFirstChild("CombatCue")
                local label = cue and cue:FindFirstChildWhichIsA("TextLabel")
                local ko = label and label.Text:find("撃破",1,true) ~= nil
                if ko and entry.koAt < entry.hitAt then entry.koAt = now end
                local t = now + entry.phase
                for _,visual in ipairs(entry.attachments) do
                    if visual.part.Parent then
                        local localMotion = movementFor(entry.kind, visual.name,
                            entry.speed, t, now-entry.hitAt, now-entry.koAt)
                        -- Cosmetic CFrame edits on this client only: server-owned
                        -- Horde Core, actual hits and reward authority untouched.
                        visual.part.CFrame = core.CFrame * visual.offset * localMotion
                    end
                end
            end
        end
    end
end)

script.Destroying:Connect(function()
    isRunning = false
    added:Disconnect()
    pulse:Disconnect()
    for _,leases in pairs(connected) do
        for _,c in ipairs(leases) do c:Disconnect() end
    end
    table.clear(connected)
    table.clear(records)
end)
print("ART_MOTION_SOURCE_WIP_CLIENT_COSMETIC_ONLY_NOT_STUDIO_VERIFIED")
