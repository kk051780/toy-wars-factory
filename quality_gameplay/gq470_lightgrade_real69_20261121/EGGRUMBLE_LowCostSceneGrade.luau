--!strict
-- GQ470_FB015_LOW_COST_SCENE_GRADE_REAL69_20261121
-- Isolated art-source candidate. Explicit install only; not in the selected REAL69
-- runtime until the authenticated B writer chooses a source-exact integration.
-- Adapted from the art-direction/palette intent of existing FB015 PR #377.
-- Purely cosmetic: 0 Parts, 0 event loops, 0 gameplay authority/Remotes/GUI.
local RunService = game:GetService("RunService")

local SceneGrade = {}
local GRADE_NAME = "EGGRUMBLE_GQ470_LowCostSceneGrade"
local ATMOSPHERE_NAME = "EGGRUMBLE_GQ470_OwnedAtmosphere"

-- Restrained art direction: preserve readable silhouettes and bright egg/team
-- cues. Post effects stay within a mobile-conscious grade range.
local MOODS = {
    CLEAR = {
        contrast = 0.06, saturation = 0.07, brightness = 0.00,
        tint = Color3.fromRGB(249, 245, 235),
        density = 0.23, haze = 0.85, glare = 0.06,
        sky = Color3.fromRGB(215, 227, 235),
        decay = Color3.fromRGB(134, 151, 164),
    },
    GOLDEN = {
        contrast = 0.075, saturation = 0.08, brightness = 0.01,
        tint = Color3.fromRGB(255, 237, 214),
        density = 0.25, haze = 1.00, glare = 0.08,
        sky = Color3.fromRGB(247, 221, 193),
        decay = Color3.fromRGB(157, 136, 139),
    },
    OVERCAST = {
        contrast = 0.07, saturation = -0.035, brightness = 0.00,
        tint = Color3.fromRGB(224, 232, 240),
        density = 0.27, haze = 1.10, glare = 0.03,
        sky = Color3.fromRGB(188, 208, 223),
        decay = Color3.fromRGB(119, 142, 159),
    },
    STORM = {
        contrast = 0.09, saturation = -0.075, brightness = -0.02,
        tint = Color3.fromRGB(208, 221, 238),
        density = 0.30, haze = 1.25, glare = 0.02,
        sky = Color3.fromRGB(169, 194, 220),
        decay = Color3.fromRGB(104, 129, 157),
    },
}

-- One install per Lighting instance. Another art lane's Atmosphere is never
-- overwritten, and named effect collisions are rejected rather than adopted.
function SceneGrade.install(lighting: Lighting)
    if not RunService:IsStudio() then
        return nil, "STUDIO_ONLY"
    end
    if lighting:FindFirstChild(GRADE_NAME) then
        return nil, "ALREADY_INSTALLED"
    end

    local existingAtmosphere = lighting:FindFirstChildOfClass("Atmosphere")
    local atmosphere = existingAtmosphere
    local ownsAtmosphere = false
    if atmosphere == nil then
        atmosphere = Instance.new("Atmosphere")
        atmosphere.Name = ATMOSPHERE_NAME
        atmosphere.Parent = lighting
        ownsAtmosphere = true
    end

    local grade = Instance.new("ColorCorrectionEffect")
    grade.Name = GRADE_NAME
    grade.Enabled = true
    grade.Parent = lighting

    local active = true
    local currentMood = ""

    local function setMood(mood: string)
        if not active then
            return false, "DISPOSED"
        end
        local palette = MOODS[mood]
        if palette == nil then
            return false, "UNKNOWN_MOOD"
        end
        if mood == currentMood then
            return true, "UNCHANGED"
        end
        grade.Contrast = palette.contrast
        grade.Saturation = palette.saturation
        grade.Brightness = palette.brightness
        grade.TintColor = palette.tint
        -- Never modify a previously existing environment owned by another lane.
        if ownsAtmosphere and atmosphere ~= nil then
            atmosphere.Density = palette.density
            atmosphere.Haze = palette.haze
            atmosphere.Glare = palette.glare
            atmosphere.Color = palette.sky
            atmosphere.Decay = palette.decay
        end
        currentMood = mood
        return true, "APPLIED"
    end

    local function destroy()
        if not active then
            return false
        end
        active = false
        grade:Destroy()
        if ownsAtmosphere and atmosphere ~= nil then
            atmosphere:Destroy()
        end
        return true
    end

    setMood("CLEAR")
    local controller = {
        setMood = setMood,
        destroy = destroy,
        getMood = function()
            return currentMood
        end,
    }
    return controller, "INSTALLED"
end

return SceneGrade
