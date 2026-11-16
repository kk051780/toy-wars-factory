--!strict
-- Pure authoritative target rule: an egg carrier can never hide from AI with WIND.
-- TEAM/BR, HP, LOS, range and cooldown remain owned by original BotActors.
local Targeting = {}

function Targeting.canStrike(carriedEggs:any, stealthUntil:any, now:number):boolean
    -- Fail safe for malformed server state: do not grant permanent immunity.
    if type(carriedEggs) ~= "number" or carriedEggs ~= carriedEggs then
        return true
    end
    if carriedEggs > 0 then
        return true
    end
    if type(stealthUntil) ~= "number" or stealthUntil ~= stealthUntil
        or stealthUntil == math.huge or stealthUntil == -math.huge then
        return true
    end
    return now >= stealthUntil
end

return Targeting
