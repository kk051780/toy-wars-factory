--!strict
-- GQ470 FB-015: distant matte cloud silhouettes for the flagship arena.
-- A-PREP only. This file does not modify Game/Host/Combat/Weather/Lighting.
-- Local geometry, fixed finite budget, no replication or per-frame work.
local Workspace = game:GetService("Workspace")
local UserInputService = game:GetService("UserInputService")

local FOLDER_NAME = "EGGRUMBLE_FarSkyFacets_Local"
local MAX_DESKTOP_BANKS = 6
local MAX_TOUCH_BANKS = 4
local FACETS_PER_BANK = 3
local MAX_PARTS = MAX_DESKTOP_BANKS * FACETS_PER_BANK
local ENABLED = true

if not ENABLED then
    return
end

-- A LocalScript runs once per player session. Re-entry cannot duplicate art.
if Workspace:FindFirstChild(FOLDER_NAME) then
    return
end

local folder = Instance.new("Folder")
folder.Name = FOLDER_NAME
folder:SetAttribute("FeatureID", "GQ470_FB015_FAR_SKY_MATTE_CLOUD_BANKS_20261121")
folder:SetAttribute("SourceStage", "A_PREP_NOT_OFFICIAL_RC")
folder.Parent = Workspace

local isTouch = UserInputService.TouchEnabled
local bankCount = if isTouch then MAX_TOUCH_BANKS else MAX_DESKTOP_BANKS
local colorTop = {
    Color3.fromRGB(212, 228, 231),
    Color3.fromRGB(226, 223, 216),
    Color3.fromRGB(202, 222, 230),
    Color3.fromRGB(231, 220, 208),
}
local colorShadow = {
    Color3.fromRGB(158, 187, 198),
    Color3.fromRGB(194, 181, 174),
    Color3.fromRGB(157, 190, 201),
    Color3.fromRGB(196, 180, 176),
}

local made = 0
local function facet(
    label: string,
    center: Vector3,
    size: Vector3,
    yaw: number,
    roll: number,
    tint: Color3,
    alpha: number
): ()
    if made >= MAX_PARTS then
        return
    end

    local part = Instance.new("WedgePart")
    part.Name = label
    part.Size = size
    part.CFrame = CFrame.new(center)
        * CFrame.Angles(0, yaw, 0)
        * CFrame.Angles(0, 0, roll)
    part.Color = tint
    part.Transparency = alpha
    part.Material = Enum.Material.SmoothPlastic
    part.Anchored = true
    part.CanCollide = false
    part.CanTouch = false
    part.CanQuery = false
    part.CastShadow = false
    part.Parent = folder
    made += 1
end

for i = 1, bankCount do
    -- Distant horizon, beyond the main castle approaches. No physical route impact.
    local theta = ((i - 1) / bankCount) * math.pi * 2 + math.rad(-18)
    local distance = 625 + (i % 3) * 55
    local altitude = 158 + (i % 3) * 12
    local origin = Vector3.new(math.cos(theta) * distance, altitude, math.sin(theta) * distance)
    local tangent = Vector3.new(-math.sin(theta), 0, math.cos(theta))
    local angle = theta + math.pi / 2
    local palette = ((i - 1) % #colorTop) + 1

    -- Three overlapping, shallow wedge silhouettes: no spheres, Neon or billboards.
    facet("Cloud" .. i .. "_Base", origin, Vector3.new(146, 16, 20),
        angle, math.rad(-2), colorShadow[palette], 0.52)
    facet("Cloud" .. i .. "_CrestA", origin - tangent * 39 + Vector3.new(0, 12, 0),
        Vector3.new(100, 25, 14), angle, math.rad(5), colorTop[palette], 0.36)
    facet("Cloud" .. i .. "_CrestB", origin + tangent * 43 + Vector3.new(0, 9, 0),
        Vector3.new(91, 19, 14), angle, math.rad(-5), colorTop[palette], 0.42)
end

folder:SetAttribute("PartBudgetActual", made)
folder:SetAttribute("PartBudgetMaximum", MAX_PARTS)
folder:SetAttribute("TouchReduced", isTouch)
