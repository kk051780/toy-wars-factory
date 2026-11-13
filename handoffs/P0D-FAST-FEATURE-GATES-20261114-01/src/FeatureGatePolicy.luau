-- P0D-FAST-FEATURE-GATES-001 / Luau pure policy.
-- This module cannot switch any gameplay on its own. The sole #220 integrator
-- must add explicit Game/assembler hooks; otherwise flags are UI-less proposals.
local Gate = {}

local order = {
    "CORE_S1", "EGG_DUAL_MODE", "H1_SKYV5", "H1_MUSOU_V7",
    "H1_AUTO_DOJO_2", "V4_SIX_SKILL_SESSION",
}
local featureExists = {}
for _, feature in ipairs(order) do
    featureExists[feature] = true
end
local profile = {
    legacy21 = { CORE_S1 = true },
    rich47 = {
        CORE_S1 = true, EGG_DUAL_MODE = true, H1_SKYV5 = true,
        H1_MUSOU_V7 = true, H1_AUTO_DOJO_2 = true,
    },
    rich51 = {
        CORE_S1 = true, EGG_DUAL_MODE = true, H1_SKYV5 = true,
        H1_MUSOU_V7 = true, H1_AUTO_DOJO_2 = true,
        V4_SIX_SKILL_SESSION = true,
    },
}

-- Resolve is all-or-nothing and fail-closed; no authority or side-effects.
function Gate.resolve(profileId, overrides)
    local selected = profile[profileId]
    if selected == nil then return nil, "UNKNOWN_PROFILE" end
    if overrides ~= nil and type(overrides) ~= "table" then
        return nil, "INVALID_OVERRIDES"
    end
    overrides = overrides or {}
    for id, value in pairs(overrides) do
        if not featureExists[id] then return nil, "UNKNOWN_FEATURE" end
        if type(value) ~= "boolean" then return nil, "NON_BOOLEAN" end
        if value == true and selected[id] ~= true then
            return nil, "FEATURE_NOT_IN_PROFILE"
        end
    end
    if overrides.CORE_S1 == false then return nil, "CORE_REQUIRED" end
    local enabled = {}
    for _, id in ipairs(order) do
        enabled[id] = selected[id] == true and overrides[id] ~= false
    end
    if enabled.V4_SIX_SKILL_SESSION and not enabled.H1_AUTO_DOJO_2 then
        return nil, "V4_REQUIRES_H1_DOJO"
    end
    return table.freeze(enabled), nil
end

-- Caller must still check that an actual approved integration hook exists.
function Gate.isEnabled(snapshot, featureId)
    return type(snapshot) == "table"
        and featureExists[featureId] == true
        and snapshot[featureId] == true
end

return table.freeze(Gate)
