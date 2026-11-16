--!strict
-- Cosmetic-only client VFX admission policy. No damage, skills, HP, physics or remote.
local Budget = {}
local TOUCH_LIMITS = {CORE=100, SECONDARY=70, ULTIMATE=200, KO=100}
local DESKTOP_LIMITS = {CORE=165, SECONDARY=115, ULTIMATE=285, KO=165}

function Budget.shouldHide(kind:string, distance:number, touch:boolean, reduced:boolean, active:number):boolean
    local limits = if touch then TOUCH_LIMITS else DESKTOP_LIMITS
    local limit = limits[kind]
    if not limit then return false end
    if distance ~= distance or distance < 0 then return false end
    if reduced then
        limit = if kind == "ULTIMATE" then 90 elseif kind == "KO" then 55 else 35
    elseif active >= 72 and kind ~= "ULTIMATE" then
        limit *= if touch then 0.66 else 0.82
    elseif active >= 44 and kind == "SECONDARY" then
        limit *= if touch then 0.78 else 0.9
    end
    -- The close-range hit identity / ultimate remains visible even on busy touch devices.
    if kind == "ULTIMATE" and distance <= 85 then return false end
    if kind == "KO" and distance <= 40 then return false end
    if kind == "CORE" and distance <= 40 then return false end
    return distance > limit
end

return Budget
