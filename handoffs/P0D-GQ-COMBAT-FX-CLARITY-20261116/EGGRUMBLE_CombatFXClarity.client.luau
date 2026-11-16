--!strict
-- Optional Studio V3 CLIENT cosmetic shedding: only original seven-job secondary FX.
-- Protected at every distance: FLASH/RING, ULTIMATE, server-confirmed KO/HIT.
-- Does not modify original game, server FX, Remote, NPCs, castle, egg, item or HUD.
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
local records:{[BasePart]:{original:number,hidden:boolean}} = {}
local secondaryPrefixes = {
    "WarGod_", "Mage_", "Assassin_", "Esper_", "MadScientist_",
    "Beast_", "CurseMaster_",
}

local function secondary(name:string):boolean
    for _,prefix in ipairs(secondaryPrefixes) do
        if name:sub(1,#prefix) == prefix then return true end
    end
    return false
end

-- Only original #482 session.world ("TEAM_Arena" / "BATTLE_ROYALE_Arena")
-- inside #482's arena host. Prevent a similarly named lobby, gear or map Part
-- from being accidentally culled.
local function isOriginalArenaFX(part:BasePart):boolean
    local current:Instance? = part.Parent
    while current and current ~= workspace do
        if (current.Name == "TEAM_Arena" or current.Name == "BATTLE_ROYALE_Arena")
            and current.Parent and current.Parent.Name == "EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW" then
            return true
        end
        current = current.Parent
    end
    return false
end

local function forget(part:BasePart)
    local record = records[part]
    if record == nil then return end
    if part.Parent then part.LocalTransparencyModifier = record.original end
    records[part] = nil
    active = math.max(0,active-1)
end

local function watch(inst:Instance)
    if active >= MAX_TRACKED or not inst:IsA("BasePart") then return end
    if records[inst] ~= nil or not secondary(inst.Name) then return end
    if not isOriginalArenaFX(inst) then return end
    records[inst] = {original=inst.LocalTransparencyModifier,hidden=false}
    active += 1
end

-- Server-created VFX is always short-lived; no global Workspace GetDescendants
-- enumeration and never a separate Game/replicated damage or server effect loop.
local addedConnection = workspace.DescendantAdded:Connect(watch)
local removingConnection = workspace.DescendantRemoving:Connect(function(inst)
    if inst:IsA("BasePart") then forget(inst) end
end)
local heartbeatConnection = RunService.Heartbeat:Connect(function(dt:number)
    elapsed += math.min(dt,0.5)
    if elapsed < UPDATE_SECONDS then return end
    elapsed = 0
    local camera = workspace.CurrentCamera
    if not camera then return end
    local origin = camera.CFrame.Position
    local touch = UserInputService.TouchEnabled
    local reduced = player:GetAttribute("EGGRUMBLE_ReducedEffects") == true
    for part,record in pairs(records) do
        if not part.Parent or not isOriginalArenaFX(part) then
            forget(part)
        else
            local distance = (part.Position-origin).Magnitude
            local hidden = Budget.shouldHide("SECONDARY",distance,touch,reduced,active,record.hidden)
            if record.hidden ~= hidden then
                record.hidden = hidden
                part.LocalTransparencyModifier = if hidden then 1 else record.original
            end
        end
    end
end)

player.AncestryChanged:Connect(function(_,parent)
    if parent ~= nil then return end
    addedConnection:Disconnect()
    removingConnection:Disconnect()
    heartbeatConnection:Disconnect()
    for part in pairs(records) do forget(part) end
end)
