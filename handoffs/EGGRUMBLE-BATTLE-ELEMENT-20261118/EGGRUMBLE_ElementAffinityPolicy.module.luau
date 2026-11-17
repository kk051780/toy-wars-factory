-- P0D BATTLE-ELEMENT-RULES / 2026-11-18
-- Pure policy only. Caller owns valid session, hit authority, HP and damage application.
-- "NONE"/nil preserve the old non-elemental attack path. Unknown strings fail closed.
local Policy = {}

Policy.VERSION = "GQ8_ELEMENT_POLICY_V1"
Policy.ELEMENTS = {
    "FIRE", "WATER", "LIGHTNING", "WIND", "EARTH", "ICE", "DIVINE", "CURSE",
}

local KNOWN = {
    NONE = true,
    FIRE = true, WATER = true, LIGHTNING = true,
    WIND = true, EARTH = true, ICE = true,
    DIVINE = true, CURSE = true,
}
-- Six-element cycle, one offensive advantage and one defensive weakness per element.
local CYCLE = {
    FIRE = "ICE",
    ICE = "WIND",
    WIND = "EARTH",
    EARTH = "LIGHTNING",
    LIGHTNING = "WATER",
    WATER = "FIRE",
}

local function normalize(element)
    if element == nil then
        return "NONE"
    end
    if type(element) ~= "string" or KNOWN[element] ~= true then
        return nil
    end
    return element
end

function Policy.isKnown(element)
    return type(element) == "string" and KNOWN[element] == true
end

-- Returns multiplier, semantic result. No side effects or Roblox services.
-- Results are text/icon contracts for HUD and VFX owners; never a client damage grant.
function Policy.resolve(attackElement, defenseElement)
    local attack = normalize(attackElement)
    if attack == nil then
        return nil, "INVALID_ATTACK_ELEMENT"
    end
    local defend = normalize(defenseElement)
    if defend == nil then
        return nil, "INVALID_DEFENSE_ELEMENT"
    end
    if attack == "NONE" or defend == "NONE" then
        return 1.00, "NEUTRAL"
    end
    -- Same-element protection is strong but not immunity.
    if attack == defend then
        return 0.65, "STRONG_RESISTANCE"
    end
    -- Both mythic elements counter one another, never the six-element base cycle.
    if (attack == "DIVINE" and defend == "CURSE")
        or (attack == "CURSE" and defend == "DIVINE") then
        return 1.25, "MUTUAL_COUNTER"
    end
    if CYCLE[attack] == defend then
        return 1.25, "ADVANTAGE"
    end
    if CYCLE[defend] == attack then
        return 0.80, "RESISTED"
    end
    return 1.00, "NEUTRAL"
end

-- Deterministic rounding; callers MUST apply resulting damage through their ONE server
-- Game/Combat/Host owner. Do not attach to Remotes or directly change Humanoid health.
function Policy.scaleDamage(baseDamage, attackElement, defenseElement)
    if type(baseDamage) ~= "number" or baseDamage ~= baseDamage
        or baseDamage < 0 or baseDamage > 100000 then
        return nil, "INVALID_BASE_DAMAGE"
    end
    local multiplier, outcome = Policy.resolve(attackElement, defenseElement)
    if multiplier == nil then
        return nil, outcome
    end
    return math.floor(baseDamage * multiplier + 0.5), outcome
end

return Policy
