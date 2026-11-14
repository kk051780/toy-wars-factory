--!nocheck
-- P0D twin creatures: session-only field practice; does not touch DataStore,
-- Game, rewards, HP, PvP, currency, paid items, gacha or purchase ownership.
-- Pure Luau module so policy can run through the actual native Luau CLI.
local Training = {}

local SPECIES = {
    AWARIN = true,
    SANGORU = true,
    RAIKO = true,
    KUMONON = true,
}
local MAX_PRACTICE = 7
local REPEAT_WAIT_SECONDS = 20

local function safeCount(previous)
    if type(previous) ~= "table" then
        return 0
    end
    local n = previous.xp
    if type(n) ~= "number" or n ~= n or n == math.huge or n == -math.huge then
        return 0
    end
    if n < 0 then
        return 0
    end
    return math.min(MAX_PRACTICE, math.floor(n))
end

function Training.levelFor(xp)
    if type(xp) ~= "number" or xp ~= xp then
        return 1
    end
    if xp >= 7 then return 3 end
    if xp >= 3 then return 2 end
    return 1
end

function Training.effectSeconds(level)
    if level == 3 then return 24 end
    if level == 2 then return 20 end
    return 16
end

function Training.advance(previous, speciesId, now)
    if not SPECIES[speciesId] or type(now) ~= "number" or now ~= now
        or now < 0 or now == math.huge or now == -math.huge then
        return previous, false, false
    end
    local xp = safeCount(previous)
    local waitUntil = (type(previous) == "table" and previous.nextAt) or 0
    if type(waitUntil) ~= "number" or waitUntil ~= waitUntil
        or waitUntil < 0 or waitUntil == math.huge
        or waitUntil == -math.huge then
        waitUntil = 0
    end
    if now < waitUntil or xp >= MAX_PRACTICE then
        return {xp=xp,level=Training.levelFor(xp),nextAt=waitUntil}, false, false
    end
    local nextXP = xp + 1
    local before = Training.levelFor(xp)
    local after = Training.levelFor(nextXP)
    return {
        xp=nextXP,
        level=after,
        nextAt=now+REPEAT_WAIT_SECONDS,
    }, true, after>before
end

function Training.speciesCount()
    return 4
end

return Training
