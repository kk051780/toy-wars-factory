--!strict
-- Optional Studio V3 client cosmetic culling. The authored SkillFX and hit gameplay
-- remain untouched. Only known, short-lived visual Parts are locally hidden.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
if not RunService:IsStudio() then return end

local player = Players.LocalPlayer
local Budget = require(script.Parent:WaitForChild("EGGRUMBLE_CombatFXBudget"))
local MAX_TRACKED = 128
local UPDATE_SECONDS = 0.22
local active = 0
local elapsed = 0
local records:{[BasePart]:{kind:string, original:number}} = {}
local secondaryPrefixes = {
    "WarGod_", "Mage_", "Assassin_", "Esper_", "MadScientist_",
    "Beast_", "CurseMaster_"
}

local function classify(name:string):string?
    if name:sub(1,9) == "ULTIMATE_" then return "ULTIMATE" end
    if name == "EGGRUMBLE_KO_BURST" then return "KO" end
    if name:sub(1,3) == "FX_" then return "CORE" end
    for _, prefix in ipairs(secondaryPrefixes) do
        if name:sub(1,#prefix) == prefix then return "SECONDARY" end
    end
    return nil
end

local function forget(part:BasePart)
    local record = records[part]
    if not record then return end
    if part.Parent then part.LocalTransparencyModifier = record.original end
    records[part] = nil
    active = math.max(0, active - 1)
end

local function watch(inst:Instance)
    if active >= MAX_TRACKED or not inst:IsA("BasePart") then return end
    if records[inst] ~= nil then return end
    local kind = classify(inst.Name)
    if not kind then return end
    -- Do not touch actual NPC rigs, permanent battlefield, held weapons or pickups.
    records[inst] = {kind=kind, original=inst.LocalTransparencyModifier}
    active += 1
end

-- DescendantAdded receives the existing SkillFX-created short-lived pieces.
-- No repeated Workspace:GetDescendants() scans and no per-frame part enumeration.
local addedConnection = workspace.DescendantAdded:Connect(watch)
local removingConnection = workspace.DescendantRemoving:Connect(function(inst)
    if inst:IsA("BasePart") then forget(inst) end
end)
local heartbeatConnection = RunService.Heartbeat:Connect(function(dt:number)
    elapsed += math.min(dt, 0.5)
    if elapsed < UPDATE_SECONDS then return end
    elapsed = 0
    local camera = workspace.CurrentCamera
    if not camera then return end
    local origin = camera.CFrame.Position
    local touch = UserInputService.TouchEnabled
    local reduced = player:GetAttribute("EGGRUMBLE_ReducedEffects") == true
    for part, record in pairs(records) do
        if not part.Parent then
            forget(part)
        else
            local distance = (part.Position-origin).Magnitude
            local hidden = Budget.shouldHide(record.kind, distance, touch, reduced, active)
            part.LocalTransparencyModifier = if hidden then 1 else record.original
        end
    end
end)

player.AncestryChanged:Connect(function(_, parent)
    if parent ~= nil then return end
    addedConnection:Disconnect()
    removingConnection:Disconnect()
    heartbeatConnection:Disconnect()
    for part in pairs(records) do forget(part) end
end)
