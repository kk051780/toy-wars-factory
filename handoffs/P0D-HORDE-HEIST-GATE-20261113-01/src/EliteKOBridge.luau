--!strict
-- Read-only server-side death edge detector for original #288 MusouHorde.
-- A full Game/Horde callback is NOT added; this observes only a genuine
-- before/after server-owned Horde:hit() call within the same synchronous action.
-- The owner of each combat callsite must opt in after source-lock review.
local EliteKOBridge = {}

local function isFiniteNumber(n)
    return type(n) == "number" and n == n and n > -math.huge and n < math.huge
end

function EliteKOBridge.capture(horde)
    if type(horde) ~= "table" or type(horde.mobs) ~= "table"
        or not isFiniteNumber(horde.round) or horde.round < 0 then
        return nil
    end

    local elite = nil
    -- A malformed horde with two elites is NOT eligible to open a shared route.
    for _, mob in ipairs(horde.mobs) do
        if type(mob) ~= "table" then return nil end
        if mob.elite == true then
            if elite ~= nil or not isFiniteNumber(mob.hp)
                or not isFiniteNumber(mob.id) then
                return nil
            end
            elite = mob
        end
    end

    if elite == nil or elite.hp <= 0 then return nil end
    return { round = horde.round, elite = elite, id = elite.id, hp = elite.hp }
end

function EliteKOBridge.didConfirmEliteKO(horde, receipt)
    if type(horde) ~= "table" or type(receipt) ~= "table"
        or type(horde.mobs) ~= "table" or horde.round ~= receipt.round
        or not isFiniteNumber(receipt.hp) or receipt.hp <= 0 then
        return false
    end
    -- Same exact object: no stale egg-mode, round, or elite respawn substitution.
    local found = 0
    for _, mob in ipairs(horde.mobs) do
        if mob == receipt.elite then
            found += 1
            if mob.elite ~= true or mob.id ~= receipt.id
                or not isFiniteNumber(mob.hp) or mob.hp ~= 0
                or not isFiniteNumber(mob.deadUntil) or mob.deadUntil <= 0 then
                return false
            end
        end
    end
    return found == 1
end

return EliteKOBridge
