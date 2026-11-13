--!strict
-- P0D S1 official RC / FIRST90 Classic target admission PREVIEW ONLY.
-- Server-side pure policy. This is NOT mounted in the official RC Game.
-- Existing original Game remains sole egg, score, damage, round and Remote owner.
local Rules = {}
Rules.WINDOW_SECONDS = 90

local function finite(v: any, lo: number, hi: number): boolean
    return type(v) == "number" and v == v and v >= lo and v <= hi
end

local function point(p: any): boolean
    return type(p) == "table"
        and finite(p.x, -200, 200)
        and finite(p.y, -50, 100)
        and finite(p.z, -120, 120)
end

local function coords(kind: string, p: any)
    return {kind = kind, x = p.x, y = p.y, z = p.z}
end

-- All input fields MUST be assembled by the existing authoritative server
-- from original match/map/player state. Never accept client-provided coordinates.
-- "RECOVER" has no location: revealing the hostile carrier would leak hidden state.
function Rules.select(snapshot: any): any?
    if type(snapshot) ~= "table" then return nil end
    if snapshot.phase ~= "ACTIVE" or snapshot.alive ~= true then return nil end
    if snapshot.team ~= "RED" and snapshot.team ~= "BLUE" then return nil end
    if not finite(snapshot.serial, 1, 100000000)
        or snapshot.serial % 1 ~= 0 then return nil end
    if not finite(snapshot.elapsedSeconds, 0, Rules.WINDOW_SECONDS)
        or snapshot.elapsedSeconds >= Rules.WINDOW_SECONDS then return nil end

    if snapshot.carryingEgg == true then
        if snapshot.ownEggHome == false then
            return {kind = "RECOVER"}
        end
        if snapshot.ownEggHome ~= true or not point(snapshot.ownScorePad) then
            return nil
        end
        return coords("HOME", snapshot.ownScorePad)
    end
    if snapshot.carryingEgg ~= false then return nil end

    -- Original CLASSIC allows theft only of opponent egg, if its original
    -- Prompt is truly enabled, egg visible and server ownership free.
    if snapshot.enemyEggFree ~= true or snapshot.enemyPromptEnabled ~= true
        or snapshot.enemyEggVisible ~= true or not point(snapshot.enemyEgg) then
        return nil
    end
    return coords("EGG", snapshot.enemyEgg)
end

return Rules
