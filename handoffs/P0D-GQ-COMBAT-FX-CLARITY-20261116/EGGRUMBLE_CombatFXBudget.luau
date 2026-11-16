--!strict
-- Pure, client-only cosmetic policy for #482 secondary skill decorations.
-- Core FLASH/RING, ULTIMATE cues, confirmed KO and HIT are ALWAYS preserved.
-- Does not touch gameplay cooldown, damage, NPC movement, egg or score state.
local Budget = {}
local NEAR_PROTECTION = 40
local HYSTERESIS = 9
local TOUCH_FAR = 85
local DESKTOP_FAR = 130

function Budget.shouldHide(kind:string, distance:number, touch:boolean, reduced:boolean, active:number, wasHidden:boolean?):boolean
    -- Safety by default: all unknown/critical FX remain visible at any distance/load.
    if kind ~= "SECONDARY" then return false end
    if type(distance) ~= "number" or distance ~= distance or distance == math.huge or distance < 0 then
        return false
    end
    if distance <= NEAR_PROTECTION then return false end
    local far = if touch then TOUCH_FAR else DESKTOP_FAR
    if reduced then
        far = if touch then 48 else 70
    elseif active >= 96 then
        far *= if touch then 0.68 else 0.8
    elseif active >= 60 then
        far *= if touch then 0.84 else 0.9
    end
    -- Keep secondary VFX stable near a moving camera instead of flashing at one threshold.
    local threshold = if wasHidden then far - HYSTERESIS else far + HYSTERESIS
    return distance > math.max(NEAR_PROTECTION, threshold)
end

return Budget
