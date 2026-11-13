--!strict
-- P0D-FUN-H1-001: a short RAIDER-only flank burst, countered by existing GUARDIAN traps.
-- PURE server policy: no target, coordinates, damage, reward, or second Remote.
local Wind = {}
Wind.COOLDOWN = 18
Wind.DURATION = 2.5
Wind.SPEED = 27

local function finite(n)
    return type(n) == "number" and n == n and math.abs(n) < 1e7
end

function Wind.canActivate(s)
    if type(s) ~= "table" or s.phase ~= "ACTIVE"
        or (s.team ~= "RED" and s.team ~= "BLUE")
        or s.role ~= "RAIDER" or s.alive ~= true
        or s.carrying == true or s.slowed == true or s.active == true then
        return false
    end
    if not finite(s.now) or (s.lastAt ~= -math.huge and not finite(s.lastAt))
        or not finite(s.x) or not finite(s.y) or not finite(s.z) then
        return false
    end
    if s.now - s.lastAt < Wind.COOLDOWN then return false end
    -- Only ordinary walkable ground in current S1 arena; no sky-flight speed exploit.
    if math.abs(s.x) > 120 or math.abs(s.z) > 65 or s.y < 1 or s.y > 12 then
        return false
    end
    return true
end

return Wind
